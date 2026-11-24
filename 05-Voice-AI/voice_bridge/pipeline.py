"""Core orchestration pipeline: WAV -> STT -> AI Router -> TTS -> WAV."""

from __future__ import annotations

import base64
import io
import logging
import re
import threading
import time
from typing import Optional, Sequence, Tuple
import wave

from .ai_router import AIRouter
from .audio import validate_and_normalize_wav
from .config import BridgeConfig
from .conversation import BridgeConversationContext, wants_detailed_reply
from .diagnostics import BridgeDiagnostics
from .schemas import (
    BridgeError,
    HealthResponse,
    ProviderStatus,
    ReadyResponse,
    TimingBreakdown,
    VoiceProcessResponse,
)
from .security import ConcurrencyLimiter, TempAudioStore
from .stt_engine import (
    ALLOWED_COMPARE_MODELS,
    FasterWhisperEngine,
    STTEngine,
    STTOptions,
    validate_compare_models,
)
from .tts_engine import PiperTTSEngine, TTSEngine


class CancellationToken:
    """Thread-safe cooperative cancellation token for in-flight voice requests."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise BridgeError("REQUEST_CANCELLED", "Richiesta annullata", http_status=499, recoverable=True)


_TTS_FALLBACK_SHORT_IT = "La risposta è troppo lunga. Chiedimi una versione più breve."


def _measure_wav_pcm(wav_bytes: bytes) -> Tuple[int, float]:
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            frames = wf.getnframes()
            sr = wf.getframerate()
            pcm_bytes = frames * wf.getsampwidth() * wf.getnchannels()
            dur_s = (frames / float(sr)) if sr > 0 else 0.0
            return pcm_bytes, dur_s
    except Exception:
        return 0, 0.0


def _reduce_tts_text_for_limit(text: str, pcm_bytes: int, max_pcm_bytes: int) -> str:
    cleaned = " ".join((text or "").split()).strip()
    if len(cleaned) <= 25:
        return ""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
    if len(sentences) >= 2:
        ratio = max(0.25, min(0.85, (max_pcm_bytes / float(max(1, pcm_bytes))) * 0.90))
        keep_n = max(1, min(len(sentences) - 1, int(len(sentences) * ratio)))
        candidate = " ".join(sentences[:keep_n]).strip()
        if candidate and len(candidate) < len(cleaned):
            return candidate
    target_chars = max(20, min(len(cleaned) - 15, int(len(cleaned) * (max_pcm_bytes / float(max(1, pcm_bytes))) * 0.85)))
    cut = cleaned[:target_chars]
    last_space = cut.rfind(" ")
    if last_space > 15:
        cut = cut[:last_space]
    return cut.rstrip(" ,;:") + "."


class VoiceBridgeService:
    """Coordinates WAV validation, STT, AI routing, TTS, diagnostics, and temp storage."""

    def __init__(
        self,
        config: Optional[BridgeConfig] = None,
        stt_engine: Optional[STTEngine] = None,
        ai_router: Optional[AIRouter] = None,
        tts_engine: Optional[TTSEngine] = None,
    ) -> None:
        self.config = config or BridgeConfig.from_env()
        self.stt = stt_engine or FasterWhisperEngine(
            model_size=self.config.stt_model,
            allow_download=self.config.stt_allow_download,
            default_options=STTOptions(
                vad_filter=self.config.stt_vad_filter,
                speech_pad_ms=self.config.stt_speech_pad_ms,
                beam_size=self.config.stt_beam_size,
                condition_on_previous_text=self.config.stt_condition_on_prev_text,
                initial_prompt=self.config.stt_initial_prompt,
            ),
        )
        self.ai_router = ai_router or AIRouter(self.config)
        self.tts = tts_engine or PiperTTSEngine(
            piper_bin=self.config.piper_bin,
            model_path=self.config.piper_model_path,
            target_sr=self.config.target_sample_rate,
            speed=self.config.tts_piper_speed,
            noise_scale=self.config.tts_piper_noise_scale,
            pitch_semitones=self.config.tts_piper_pitch_semitones,
            robot_mix=self.config.tts_piper_robot_mix,
            dsp_enabled=self.config.tts_piper_dsp_enabled,
            dsp_method=self.config.tts_piper_dsp_method,
            limiter_enabled=self.config.tts_piper_limiter_enabled,
        )
        self.conversation = BridgeConversationContext(
            max_turns=self.config.max_history_turns,
            max_messages=self.config.conversation_max_messages,
            max_tokens=self.config.conversation_max_tokens,
        )
        self.temp_store = TempAudioStore(self.config.temp_dir, ttl_s=self.config.audio_ttl_s)
        self.limiter = ConcurrencyLimiter(self.config.max_concurrent_requests)
        self.diagnostics = BridgeDiagnostics(
            extra_secrets=[self.config.device_token, self.config.esp_device_token, self.config.cloud_api_key]
        )
        self._diag_lock = threading.Lock()
        self._last_diag_wav: Optional[bytes] = None
        self._prewarm_thread: Optional[threading.Thread] = None
        self._prewarm_lock = threading.Lock()

    def start_prewarm(self) -> bool:
        """Starts at most one background daemon thread to pre-warm Ollama without blocking startup."""
        if not self.config.ollama_prewarm_on_startup or self.ai_router.ollama is None:
            return False
        with self._prewarm_lock:
            if self._prewarm_thread is not None:
                return False
            ollama_client = self.ai_router.ollama

            def _run() -> None:
                t0 = time.monotonic()
                ok = ollama_client.prewarm()
                elapsed_ms = (time.monotonic() - t0) * 1000.0
                if ok:
                    self.diagnostics.log_event(
                        logging.INFO,
                        "prewarm",
                        f"Ollama prewarm ok model={ollama_client.model} keep_alive={ollama_client.keep_alive} ms={elapsed_ms:.1f}",
                    )
                else:
                    self.diagnostics.log_event(
                        logging.WARNING,
                        "prewarm",
                        f"Ollama prewarm skipped/unavailable model={ollama_client.model} ms={elapsed_ms:.1f}",
                    )

            self._prewarm_thread = threading.Thread(target=_run, name="jarvis-ollama-prewarm", daemon=True)
            self._prewarm_thread.start()
            return True

    def health(self) -> HealthResponse:
        return HealthResponse()

    def close(self) -> None:
        self.ai_router.close()

    def reset_conversation(self) -> dict:
        self.conversation.clear()
        return {"reset": True, "message_count": self.conversation.message_count}

    def ready(self) -> ReadyResponse:
        stt_ok, stt_msg = self.stt.is_available()
        tts_ok, tts_msg = self.tts.is_available()

        if self.ai_router.ollama is not None:
            ol_ok, ol_msg = self.ai_router.ollama.probe()
        else:
            ol_ok, ol_msg = False, "Ollama disabilitato"

        cl_ok, cl_msg = self.ai_router.cloud.is_configured_and_enabled()

        providers = {
            "stt": ProviderStatus(available=stt_ok, detail=stt_msg),
            "tts": ProviderStatus(available=tts_ok, detail=tts_msg),
            "ollama": ProviderStatus(available=ol_ok, detail=ol_msg),
            "cloud": ProviderStatus(available=cl_ok, detail=cl_msg),
            "offline_fallback": ProviderStatus(available=True, detail="Fallback offline sempre pronto"),
        }
        return ReadyResponse(ready=bool(stt_ok and tts_ok), service_ok=True, providers=providers)

    def transcribe_only(self, wav_bytes: bytes, cancel_token: Optional[CancellationToken] = None) -> dict:
        req_id = self.diagnostics.new_request_id()
        if not self.limiter.acquire():
            raise BridgeError("TOO_MANY_REQUESTS", "Troppi task simultanei in corso", http_status=429, recoverable=True)
        try:
            if cancel_token:
                cancel_token.raise_if_cancelled()
            validated = validate_and_normalize_wav(
                wav_bytes,
                max_bytes=self.config.max_wav_bytes,
                max_duration_s=self.config.max_audio_duration_s,
                target_sr=self.config.target_sample_rate,
                silence_rms_threshold=self.config.silence_rms_threshold,
                reject_silence=True,
            )
            if cancel_token:
                cancel_token.raise_if_cancelled()
            t0 = time.monotonic()
            transcript = self.stt.transcribe(
                validated.wav_bytes_16k_mono,
                language=self.config.stt_language,
                timeout_s=self.config.stt_timeout_s,
            )
            stt_ms = (time.monotonic() - t0) * 1000.0
            self.diagnostics.record_outcome(True)
            return {
                "request_id": req_id,
                "transcript": transcript,
                "stt_ms": round(stt_ms, 2),
                "input_duration_s": round(validated.duration_s, 3),
                "input_sample_rate": validated.input_sample_rate,
                "input_rms_16": validated.rms_16,
                "input_peak_16": validated.peak_16,
                "input_clipped_count": validated.clipped_count,
                "input_wav_bytes_len": validated.input_wav_bytes_len,
            }
        except Exception:
            self.diagnostics.record_outcome(False)
            raise
        finally:
            self.limiter.release()

    def synthesize_only(self, text: str, cancel_token: Optional[CancellationToken] = None) -> bytes:
        if not self.limiter.acquire():
            raise BridgeError("TOO_MANY_REQUESTS", "Troppi task simultanei in corso", http_status=429, recoverable=True)
        try:
            if cancel_token:
                cancel_token.raise_if_cancelled()
            cleaned = self.conversation.clean_for_tts(text)
            wav_out = self.tts.synthesize(cleaned, timeout_s=self.config.tts_timeout_s)
            self.diagnostics.record_outcome(True)
            return wav_out
        except Exception:
            self.diagnostics.record_outcome(False)
            raise
        finally:
            self.limiter.release()

    def process_voice(
        self,
        wav_bytes: bytes,
        include_base64_audio: bool = True,
        cancel_token: Optional[CancellationToken] = None,
    ) -> VoiceProcessResponse:
        req_id = self.diagnostics.new_request_id()
        t_total_0 = time.monotonic()

        if not self.limiter.acquire():
            raise BridgeError("TOO_MANY_REQUESTS", "Troppi task simultanei in corso", http_status=429, recoverable=True)

        try:
            if cancel_token:
                cancel_token.raise_if_cancelled()

            validated = validate_and_normalize_wav(
                wav_bytes,
                max_bytes=self.config.max_wav_bytes,
                max_duration_s=self.config.max_audio_duration_s,
                target_sr=self.config.target_sample_rate,
                silence_rms_threshold=self.config.silence_rms_threshold,
                reject_silence=True,
            )

            if self.config.enable_stt_diag:
                with self._diag_lock:
                    self._last_diag_wav = validated.wav_bytes_16k_mono

            if cancel_token:
                cancel_token.raise_if_cancelled()

            t_stt_0 = time.monotonic()
            transcript = self.stt.transcribe(
                validated.wav_bytes_16k_mono,
                language=self.config.stt_language,
                timeout_s=self.config.stt_timeout_s,
            )
            stt_ms = (time.monotonic() - t_stt_0) * 1000.0

            if cancel_token:
                cancel_token.raise_if_cancelled()

            norm_q = " ".join(transcript.lower().split()).strip(" ?!.,;:")
            if norm_q in {
                "azzera la conversazione",
                "azzera il contesto",
                "nuova conversazione",
                "resetta la conversazione",
                "dimentica la conversazione",
            }:
                self.conversation.clear()
                from .ai_router import AIRouteResult

                ai_res = AIRouteResult(
                    text="Contesto della conversazione azzerato. Dimmi pure.",
                    provider_used="Local Intent",
                    fallback_used=False,
                    reason="local_intent:conversation_reset",
                    latency_ms=0.1,
                )
                ai_ms = 0.1
            else:
                messages = self.conversation.build_messages(transcript)
                max_tok_override = self.config.ollama_detail_max_tokens if wants_detailed_reply(transcript) else None
                t_ai_0 = time.monotonic()
                ai_res = self.ai_router.route(
                    messages,
                    transcript,
                    cancel_check=cancel_token.raise_if_cancelled if cancel_token else None,
                    max_tokens_override=max_tok_override,
                )
                ai_ms = (time.monotonic() - t_ai_0) * 1000.0

            if cancel_token:
                cancel_token.raise_if_cancelled()

            tts_text = self.conversation.clean_for_tts(ai_res.text, max_chars=self.config.tts_max_chars)
            t_tts_0 = time.monotonic()
            max_pcm = self.config.esp_max_tts_bytes
            attempts = 1
            out_wav = self.tts.synthesize(tts_text, timeout_s=self.config.tts_timeout_s)
            pcm_bytes, audio_dur_s = _measure_wav_pcm(out_wav)

            if pcm_bytes <= 0:
                self.diagnostics.log_event(
                    logging.ERROR,
                    req_id,
                    f"TTS_FINAL_ERROR pcm_bytes={pcm_bytes} dur_s={audio_dur_s:.2f} max_bytes={max_pcm} attempts={attempts}",
                )
                raise BridgeError("TTS_FAILED", "Audio TTS vuoto o non valido", http_status=500, recoverable=True)

            used_short_fallback = False
            while pcm_bytes > max_pcm and attempts < 3:
                self.diagnostics.log_event(
                    logging.WARNING,
                    req_id,
                    f"TTS_PCM_LIMIT_EXCEEDED pcm_bytes={pcm_bytes} dur_s={audio_dur_s:.2f} max_bytes={max_pcm} attempts={attempts}",
                )
                reduced = _reduce_tts_text_for_limit(tts_text, pcm_bytes, max_pcm)
                if not reduced or reduced == tts_text:
                    break
                tts_text = reduced
                attempts += 1
                self.diagnostics.log_event(
                    logging.INFO,
                    req_id,
                    f"TTS_TEXT_REDUCED_RESYNTHESIS attempt={attempts} max_bytes={max_pcm}",
                )
                out_wav = self.tts.synthesize(tts_text, timeout_s=self.config.tts_timeout_s)
                pcm_bytes, audio_dur_s = _measure_wav_pcm(out_wav)

            if pcm_bytes > max_pcm or pcm_bytes <= 0:
                self.diagnostics.log_event(
                    logging.WARNING,
                    req_id,
                    f"TTS_FALLBACK_SHORT pcm_bytes={pcm_bytes} dur_s={audio_dur_s:.2f} max_bytes={max_pcm} attempts={attempts}",
                )
                attempts += 1
                used_short_fallback = True
                out_wav = self.tts.synthesize(_TTS_FALLBACK_SHORT_IT, timeout_s=self.config.tts_timeout_s)
                pcm_bytes, audio_dur_s = _measure_wav_pcm(out_wav)
                if pcm_bytes <= 0 or pcm_bytes > max_pcm:
                    self.diagnostics.log_event(
                        logging.ERROR,
                        req_id,
                        f"TTS_FINAL_ERROR pcm_bytes={pcm_bytes} dur_s={audio_dur_s:.2f} max_bytes={max_pcm} attempts={attempts}",
                    )
                    raise BridgeError(
                        "TTS_TOO_LONG",
                        f"Risposta TTS eccede il limite dispositivo ({pcm_bytes} B > {max_pcm} B)",
                        http_status=413,
                        recoverable=True,
                    )

            tts_ms = (time.monotonic() - t_tts_0) * 1000.0
            self.diagnostics.log_event(
                logging.INFO,
                req_id,
                f"TTS_READY pcm_bytes={pcm_bytes} dur_s={audio_dur_s:.2f} max_bytes={max_pcm} attempts={attempts} tts_ms={tts_ms:.1f}",
            )

            if cancel_token:
                cancel_token.raise_if_cancelled()

            if ai_res.provider_used.startswith(("ollama:", "cloud:")) and not used_short_fallback:
                self.conversation.record_turn(transcript, ai_res.text)
            audio_id = self.temp_store.put(out_wav)
            total_ms = (time.monotonic() - t_total_0) * 1000.0

            self.diagnostics.log_event(
                logging.INFO,
                req_id,
                f"Voice turn ok provider={ai_res.provider_used} fallback={ai_res.fallback_used} "
                f"dur={validated.duration_s:.2f}s rms={validated.rms_16} peak={validated.peak_16} "
                f"stt={stt_ms:.1f}ms ai={ai_ms:.1f}ms tts={tts_ms:.1f}ms total={total_ms:.1f}ms",
            )
            if self.config.log_stt_diag_text:
                safe_stt = " ".join(transcript.split())[:200]
                self.diagnostics.log_event(logging.INFO, req_id, f'STT diag text="{safe_stt}"')
            self.diagnostics.record_outcome(True)

            return VoiceProcessResponse(
                request_id=req_id,
                transcript=transcript if self.config.log_conversation_text or True else "",
                reply_text=ai_res.text,
                provider_used=ai_res.provider_used,
                fallback_used=ai_res.fallback_used,
                timings=TimingBreakdown(
                    stt_ms=round(stt_ms, 2),
                    ai_ms=round(ai_ms, 2),
                    tts_ms=round(tts_ms, 2),
                    total_ms=round(total_ms, 2),
                ),
                audio_id=audio_id,
                audio_url=f"/api/v1/voice/audio/{audio_id}",
                audio_sample_rate=self.config.target_sample_rate,
                audio_channels=1,
                audio_bits=16,
                audio_bytes_len=len(out_wav),
                audio_wav_base64=base64.b64encode(out_wav).decode("ascii") if include_base64_audio else None,
                input_duration_s=round(validated.duration_s, 3),
                input_sample_rate=validated.input_sample_rate,
                input_rms_16=validated.rms_16,
                input_peak_16=validated.peak_16,
                input_clipped_count=validated.clipped_count,
                input_wav_bytes_len=validated.input_wav_bytes_len,
                timezone_note=ai_res.timezone_note,
            )
        except BridgeError as exc:
            self.diagnostics.log_event(logging.WARNING, req_id, f"BridgeError code={exc.code}: {exc.message}")
            self.diagnostics.record_outcome(False)
            raise
        except Exception as exc:
            self.diagnostics.log_event(logging.ERROR, req_id, f"Unexpected error: {exc.__class__.__name__}")
            self.diagnostics.record_outcome(False)
            raise BridgeError("INTERNAL_ERROR", "Errore interno inatteso", http_status=500, recoverable=False) from exc
        finally:
            self.limiter.release()

    def compare_stt(self, wav_bytes: Optional[bytes] = None, cancel_token: Optional[CancellationToken] = None) -> dict:
        """Runs A..E STT comparisons on an uploaded WAV or the last in-memory diagnostic WAV."""
        if not self.config.enable_stt_diag:
            raise BridgeError("DIAG_DISABLED", "Diagnostica STT disabilitata", http_status=403, recoverable=False)
        req_id = self.diagnostics.new_request_id()
        if not self.limiter.acquire():
            raise BridgeError("TOO_MANY_REQUESTS", "Troppi task simultanei in corso", http_status=429, recoverable=True)
        try:
            if cancel_token:
                cancel_token.raise_if_cancelled()

            audio_metrics = None
            if wav_bytes:
                validated = validate_and_normalize_wav(
                    wav_bytes,
                    max_bytes=self.config.max_wav_bytes,
                    max_duration_s=self.config.max_audio_duration_s,
                    target_sr=self.config.target_sample_rate,
                    silence_rms_threshold=self.config.silence_rms_threshold,
                    reject_silence=False,
                )
                target_wav = validated.wav_bytes_16k_mono
                with self._diag_lock:
                    self._last_diag_wav = target_wav
                audio_metrics = {
                    "input_duration_s": round(validated.duration_s, 3),
                    "input_sample_rate": validated.input_sample_rate,
                    "input_rms_16": validated.rms_16,
                    "input_peak_16": validated.peak_16,
                    "input_clipped_count": validated.clipped_count,
                    "input_wav_bytes_len": validated.input_wav_bytes_len,
                }
            else:
                with self._diag_lock:
                    target_wav = self._last_diag_wav
                if not target_wav:
                    raise BridgeError(
                        "NO_DIAG_AUDIO",
                        "Nessun audio diagnostico in memoria; registra prima una frase o invia un WAV",
                        http_status=404,
                        recoverable=True,
                    )

            if cancel_token:
                cancel_token.raise_if_cancelled()

            comparisons = self.stt.compare_configs(
                target_wav,
                language=self.config.stt_language,
                timeout_s=self.config.stt_timeout_s,
            )
            self.diagnostics.log_event(logging.INFO, req_id, f"STT compare ok presets={len(comparisons)}")
            return {
                "request_id": req_id,
                "audio_metrics": audio_metrics,
                "comparisons": comparisons,
            }
        finally:
            self.limiter.release()

    def compare_stt_models(
        self,
        wav_bytes: Optional[bytes] = None,
        models: Sequence[str] = ALLOWED_COMPARE_MODELS,
        reference_text: str = "",
        cancel_token: Optional[CancellationToken] = None,
    ) -> dict:
        """Sequentially compares allowed Whisper models (base/small) on the same WAV."""
        if not self.config.enable_stt_diag:
            raise BridgeError("DIAG_DISABLED", "Diagnostica STT disabilitata", http_status=403, recoverable=False)
        validated_models = validate_compare_models(models)
        req_id = self.diagnostics.new_request_id()
        if not self.limiter.acquire():
            raise BridgeError("TOO_MANY_REQUESTS", "Troppi task simultanei in corso", http_status=429, recoverable=True)
        try:
            if cancel_token:
                cancel_token.raise_if_cancelled()

            audio_metrics = None
            if wav_bytes is not None:
                validated = validate_and_normalize_wav(
                    wav_bytes,
                    max_bytes=self.config.max_wav_bytes,
                    max_duration_s=self.config.max_audio_duration_s,
                    target_sr=self.config.target_sample_rate,
                    silence_rms_threshold=self.config.silence_rms_threshold,
                    reject_silence=False,
                )
                target_wav = validated.wav_bytes_16k_mono
                with self._diag_lock:
                    self._last_diag_wav = target_wav
                audio_metrics = {
                    "input_duration_s": round(validated.duration_s, 3),
                    "input_sample_rate": validated.input_sample_rate,
                    "input_rms_16": validated.rms_16,
                    "input_peak_16": validated.peak_16,
                    "input_clipped_count": validated.clipped_count,
                    "input_wav_bytes_len": validated.input_wav_bytes_len,
                }
            else:
                with self._diag_lock:
                    target_wav = self._last_diag_wav
                if not target_wav:
                    raise BridgeError(
                        "NO_DIAG_AUDIO",
                        "Nessun audio diagnostico in memoria; registra prima una frase o invia un WAV",
                        http_status=404,
                        recoverable=True,
                    )
                validated = validate_and_normalize_wav(
                    target_wav,
                    max_bytes=self.config.max_wav_bytes,
                    max_duration_s=self.config.max_audio_duration_s,
                    target_sr=self.config.target_sample_rate,
                    silence_rms_threshold=self.config.silence_rms_threshold,
                    reject_silence=False,
                )
                audio_metrics = {
                    "input_duration_s": round(validated.duration_s, 3),
                    "input_sample_rate": validated.input_sample_rate,
                    "input_rms_16": validated.rms_16,
                    "input_peak_16": validated.peak_16,
                    "input_clipped_count": validated.clipped_count,
                    "input_wav_bytes_len": validated.input_wav_bytes_len,
                }

            if cancel_token:
                cancel_token.raise_if_cancelled()

            opts = STTOptions(
                vad_filter=True,
                speech_pad_ms=self.config.stt_speech_pad_ms,
                beam_size=3,
                condition_on_previous_text=self.config.stt_condition_on_prev_text,
                initial_prompt="",
            )
            comparisons = self.stt.compare_models(
                target_wav,
                models=validated_models,
                language=self.config.stt_language,
                timeout_s=max(self.config.stt_timeout_s, 25.0),
                options=opts,
                reference_text=reference_text,
            )
            self.diagnostics.log_event(logging.INFO, req_id, f"STT model compare ok models={','.join(validated_models)}")
            return {
                "request_id": req_id,
                "default_model": self.config.stt_model,
                "reference_text": reference_text,
                "audio_metrics": audio_metrics,
                "comparisons": comparisons,
            }
        finally:
            self.limiter.release()
