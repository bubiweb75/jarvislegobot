"""Voice & AI Conversation Controller for JARVIS AI Desk Buddy."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sys
import threading
import time
from typing import Callable, Dict, Optional

_SIM_DIR = Path(__file__).resolve().parent.parent / "04-Firmware" / "jarvis-desk-buddy-sim"
if str(_SIM_DIR) not in sys.path:
    sys.path.insert(0, str(_SIM_DIR))

from emotion_engine import EmotionEngine, StimulusType, detect_text_stimulus  # noqa: E402
from eye_engine import Expression  # noqa: E402

from ai_providers import AIProvider, AIProviderError, DemoAIProvider, OllamaProvider, OpenAIProvider
from audio_input import AudioInputError, WindowsMciAudioRecorder
from config import JarvisConfig
from conversation import ConversationManager
from eye_bridge import EyeBridge
from stt_providers import AutoLocalSTTProvider, STTError, STTProvider
from tts_providers import PiperWithFallbackTTSProvider, TTSProvider


class VoicePhase(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"


@dataclass
class VoiceEvent:
    phase: VoicePhase
    transcript: str = ""
    reply: str = ""
    status_text: str = ""
    provider_label: str = ""
    error_text: str = ""


class VoiceController:
    """Coordinates Push-to-Talk, STT, AI generation, TTS playback, and EyeBridge."""

    def __init__(
        self,
        config: JarvisConfig,
        eye_bridge: EyeBridge,
        recorder: Optional[WindowsMciAudioRecorder] = None,
        stt: Optional[STTProvider] = None,
        tts: Optional[TTSProvider] = None,
        providers: Optional[Dict[str, AIProvider]] = None,
        on_event: Optional[Callable[[VoiceEvent], None]] = None,
        emotion_engine: Optional[EmotionEngine] = None,
    ) -> None:
        self.config = config
        self.eye_bridge = eye_bridge
        self.recorder = recorder or WindowsMciAudioRecorder()
        self.stt = stt or AutoLocalSTTProvider(whisper_model_size=config.whisper_model_size)
        self.tts = tts or PiperWithFallbackTTSProvider(config=config)
        self.on_event = on_event
        self.emotion_engine = emotion_engine or EmotionEngine()
        self._start_monotonic = time.monotonic()

        self.conversation = ConversationManager(
            system_prompt=config.system_prompt,
            max_turns=config.max_history_turns,
        )

        self.providers: Dict[str, AIProvider] = providers or {
            "demo": DemoAIProvider(),
            "ollama": OllamaProvider(base_url=config.ollama_url, timeout_s=config.ollama_timeout_s),
            "openai": OpenAIProvider(
                api_key_getter=config.get_openai_api_key,
                base_url=config.openai_base_url,
                default_model=config.openai_model,
                timeout_s=config.openai_timeout_s,
            ),
        }

        self._active_provider_id = config.ai_provider if config.ai_provider in self.providers else "demo"
        self._active_model = self._default_model_for(self._active_provider_id)
        self._phase = VoicePhase.IDLE
        self._lock = threading.Lock()
        self._cancel_gen = 0
        self._happy_timer: Optional[threading.Timer] = None

    def _now_ms(self) -> int:
        return int((time.monotonic() - self._start_monotonic) * 1000.0)

    @property
    def phase(self) -> VoicePhase:
        with self._lock:
            return self._phase

    @property
    def active_provider_id(self) -> str:
        return self._active_provider_id

    @property
    def active_model(self) -> str:
        return self._active_model

    def _default_model_for(self, provider_id: str) -> str:
        if provider_id == "ollama":
            return self.config.ollama_model
        if provider_id == "openai":
            return self.config.openai_model
        return "jarvis-demo-it"

    def select_provider(self, provider_id: str, model: str = "") -> None:
        if provider_id not in self.providers:
            raise ValueError(f"Provider sconosciuto: {provider_id}")
        self._active_provider_id = provider_id
        self._active_model = model.strip() or self._default_model_for(provider_id)
        self._emit(
            VoiceEvent(
                phase=self.phase,
                provider_label=self.providers[provider_id].display_name,
                status_text=f"Provider attivo: {self.providers[provider_id].display_name}",
            )
        )

    def set_openai_confirmed(self, confirmed: bool) -> None:
        prov = self.providers.get("openai")
        if isinstance(prov, OpenAIProvider):
            prov.set_cloud_confirmed(confirmed)

    def reset_conversation(self) -> None:
        self.conversation.clear()
        self._emit(VoiceEvent(phase=self.phase, status_text="Nuova conversazione avviata"))

    def start_push_to_talk(self) -> None:
        with self._lock:
            if self._phase not in (VoicePhase.IDLE, VoicePhase.ERROR):
                self._emit(
                    VoiceEvent(
                        phase=self._phase,
                        status_text="Attendi la fine dell'operazione corrente o premi Interrompi.",
                    )
                )
                return
            self._cancel_happy_timer()
            self._phase = VoicePhase.LISTENING

        try:
            self.recorder.start_recording()
        except AudioInputError as exc:
            self._recover_with_curious(str(exc))
            return

        self.emotion_engine.set_conversation_busy(True, self._now_ms(), Expression.LISTENING)
        self.eye_bridge.set_state("LISTENING")
        self._emit(VoiceEvent(phase=VoicePhase.LISTENING, status_text="In ascolto (rilascia o premi Ferma)..."))

    def stop_push_to_talk_and_process(self) -> None:
        with self._lock:
            if self._phase != VoicePhase.LISTENING:
                return
            gen = self._cancel_gen
            self._phase = VoicePhase.THINKING

        self.emotion_engine.set_conversation_busy(True, self._now_ms(), Expression.THINKING)
        self.emotion_engine.set_conversation_busy(True, self._now_ms(), Expression.THINKING)
        self.eye_bridge.set_state("THINKING")
        self._emit(VoiceEvent(phase=VoicePhase.THINKING, status_text="Trascrizione ed elaborazione..."))

        def _worker() -> None:
            try:
                wav_bytes = self.recorder.stop_recording()
                if self._is_cancelled(gen):
                    return
                transcript = self.stt.transcribe(
                    wav_bytes,
                    language=self.config.stt_language,
                    timeout_s=self.config.stt_timeout_s,
                )
                if self._is_cancelled(gen):
                    return
                self._emit(
                    VoiceEvent(
                        phase=VoicePhase.THINKING,
                        transcript=transcript,
                        status_text="Elaborazione risposta AI...",
                    )
                )
                self._run_ai_and_speak(transcript, gen)
            except (AudioInputError, STTError) as exc:
                if not self._is_cancelled(gen):
                    self._recover_with_curious(str(exc))
            except Exception as exc:
                if not self._is_cancelled(gen):
                    self._recover_with_curious(f"Errore imprevisto: {exc}")

        threading.Thread(target=_worker, daemon=True, name="jarvis-ptt-worker").start()

    def submit_text(self, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            return
        with self._lock:
            if self._phase not in (VoicePhase.IDLE, VoicePhase.ERROR):
                self._emit(
                    VoiceEvent(
                        phase=self._phase,
                        status_text="Occupato: attendi o premi Interrompi.",
                    )
                )
                return
            self._cancel_happy_timer()
            gen = self._cancel_gen
            self._phase = VoicePhase.THINKING

        self.emotion_engine.set_conversation_busy(True, self._now_ms(), Expression.THINKING)
        self.eye_bridge.set_state("THINKING")
        self._emit(
            VoiceEvent(
                phase=VoicePhase.THINKING,
                transcript=cleaned,
                status_text="Sto pensando...",
            )
        )

        def _worker() -> None:
            self._run_ai_and_speak(cleaned, gen)

        threading.Thread(target=_worker, daemon=True, name="jarvis-ai-worker").start()

    def interrupt(self) -> None:
        with self._lock:
            self._cancel_gen += 1
            self._cancel_happy_timer()
            self._phase = VoicePhase.IDLE
        self.recorder.cancel()
        self.tts.stop()
        self.emotion_engine.set_conversation_busy(False, self._now_ms())
        self.eye_bridge.set_state("IDLE")
        self._emit(VoiceEvent(phase=VoicePhase.IDLE, status_text="Conversazione interrotta"))

    def _is_cancelled(self, gen: int) -> bool:
        with self._lock:
            return gen != self._cancel_gen

    def _run_ai_and_speak(self, user_text: str, gen: int) -> None:
        user_stimulus = detect_text_stimulus(user_text)
        provider = self.providers[self._active_provider_id]
        self.conversation.add_user_message(user_text)
        try:
            resp = provider.generate(self.conversation.get_messages_for_model(), model=self._active_model)
        except AIProviderError as exc:
            if not self._is_cancelled(gen):
                self._recover_with_curious(str(exc))
            return
        except Exception as exc:
            if not self._is_cancelled(gen):
                self._recover_with_curious(f"Errore provider AI: {exc}")
            return

        if self._is_cancelled(gen):
            return

        self.conversation.add_assistant_message(resp.text)

        with self._lock:
            if gen != self._cancel_gen:
                return
            self._phase = VoicePhase.SPEAKING

        self.emotion_engine.set_conversation_busy(True, self._now_ms(), Expression.SPEAKING)
        self.eye_bridge.set_state("SPEAKING")
        self._emit(
            VoiceEvent(
                phase=VoicePhase.SPEAKING,
                transcript=user_text,
                reply=resp.text,
                provider_label=resp.provider_name,
                status_text="JARVIS sta parlando...",
            )
        )

        def _on_tts_done(tts_err: Optional[str]) -> None:
            if self._is_cancelled(gen):
                return
            if tts_err:
                self._recover_with_curious(f"Audio TTS non riuscito: {tts_err}")
                return
            with self._lock:
                self._phase = VoicePhase.IDLE
            now_ms = self._now_ms()
            self.emotion_engine.set_conversation_busy(False, now_ms)

            decision = None
            if user_stimulus in (StimulusType.GREETING, StimulusType.COMPLIMENT, StimulusType.JOKE):
                decision = self.emotion_engine.push_stimulus(user_stimulus, now_ms, source="voice_text")
            elif resp.sentiment == "happy":
                decision = self.emotion_engine.push_stimulus(StimulusType.REPLY_DONE, now_ms, source="ai_reply")

            if decision is not None:
                self.eye_bridge.set_state(decision.expression.value)
                self._schedule_idle_after_happy(gen, delay_s=max(0.8, decision.duration_ms / 1000.0))
            elif resp.sentiment == "happy":
                self.eye_bridge.set_state("HAPPY")
                self._schedule_idle_after_happy(gen, delay_s=1.6)
            else:
                self.eye_bridge.set_state("IDLE")
            self._emit(
                VoiceEvent(
                    phase=VoicePhase.IDLE,
                    reply=resp.text,
                    provider_label=resp.provider_name,
                    status_text="In attesa",
                )
            )

        self.tts.speak(
            resp.text,
            voice=self.config.tts_voice,
            rate=self.config.tts_rate,
            volume=self.config.tts_volume,
            on_done=_on_tts_done,
            on_audio_level=self.eye_bridge.on_audio_level,
        )

    def _schedule_idle_after_happy(self, gen: int, delay_s: float = 1.6) -> None:
        def _back_to_idle() -> None:
            if not self._is_cancelled(gen) and self.phase == VoicePhase.IDLE:
                self.eye_bridge.set_state("IDLE")

        timer = threading.Timer(delay_s, _back_to_idle)
        timer.daemon = True
        with self._lock:
            self._happy_timer = timer
        timer.start()

    def _cancel_happy_timer(self) -> None:
        if self._happy_timer is not None:
            self._happy_timer.cancel()
            self._happy_timer = None

    def _recover_with_curious(self, err_msg: str) -> None:
        with self._lock:
            self._phase = VoicePhase.ERROR
        now_ms = self._now_ms()
        self.emotion_engine.set_conversation_busy(False, now_ms)
        decision = self.emotion_engine.push_stimulus(
            StimulusType.TEMP_ERROR,
            now_ms,
            source="error",
            payload=err_msg,
        )
        err_expr = decision.expression.value if decision is not None else "CONFUSED"
        self.eye_bridge.set_state(err_expr)
        self._emit(
            VoiceEvent(
                phase=VoicePhase.ERROR,
                error_text=err_msg,
                status_text=f"Attenzione: {err_msg}",
            )
        )
        # Return to IDLE cleanly after showing CURIOUS briefly
        gen = self._cancel_gen

        def _reset_idle() -> None:
            with self._lock:
                if gen != self._cancel_gen or self._phase != VoicePhase.ERROR:
                    return
                self._phase = VoicePhase.IDLE
            self.eye_bridge.set_state("IDLE")
            self._emit(VoiceEvent(phase=VoicePhase.IDLE, status_text="Pronto"))

        timer = threading.Timer(1.8, _reset_idle)
        timer.daemon = True
        timer.start()

    def _emit(self, event: VoiceEvent) -> None:
        if self.on_event is not None:
            self.on_event(event)
