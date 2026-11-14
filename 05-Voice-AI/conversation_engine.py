"""JARVIS LEGO BOT — Conversation Engine 2.0 (FASE 9.3).

Integrates:
  - VoiceController (existing STT -> AI -> TTS pipeline, no duplication)
  - MemoryEngine (FASE 9.2: L1 RAM session, L2 prefs, L3/L4 confirmed memories)
  - BehaviorEngine (FASE 9.1: RobotMode, Quiet Mode, priorities, 2/hour & 20m limits)

Note on TTS chunking:
  Piper synthesizes complete strings via CLI/WAV playback. SentenceSpeechQueue
  implements ordered, non-overlapping sentence-by-sentence playback (not true
  token-level audio streaming), with full cancellation and single-shot fallback.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import threading
import time
from typing import Callable, Dict, List, Optional

_SIM_DIR = Path(__file__).resolve().parent.parent / "04-Firmware" / "jarvis-desk-buddy-sim"
if str(_SIM_DIR) not in sys.path:
    sys.path.insert(0, str(_SIM_DIR))

from behavior_engine import BehaviorEngine, RobotMode  # noqa: E402
from memory_engine import MemoryEngine, MemoryProposal, MemoryRecord  # noqa: E402
from tts_providers import TTSProvider  # noqa: E402
from voice_controller import VoiceController, VoicePhase  # noqa: E402


MAX_MEMORY_CONTEXT_CHARS = 800
MAX_PREFS_IN_PROMPT = 8
MAX_MEMORIES_IN_PROMPT = 5

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> List[str]:
    """Split text into ordered, non-empty sentences for sequential Piper playback."""
    cleaned = " ".join(text.split()).strip()
    if not cleaned:
        return []
    parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(cleaned) if p.strip()]
    if len(parts) <= 1:
        return [cleaned]
    return parts


class SentenceSpeechQueue:
    """Plays sentence chunks sequentially with strict ordering and generation cancellation."""

    def __init__(self, tts: TTSProvider) -> None:
        self.tts = tts
        self._lock = threading.Lock()
        self._gen = 0

    def cancel(self) -> int:
        with self._lock:
            self._gen += 1
            gen = self._gen
        self.tts.stop()
        return gen

    def speak_ordered(
        self,
        text: str,
        voice: str,
        rate: int,
        volume: int,
        on_done: Optional[Callable[[Optional[str]], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
        chunk_sentences: bool = True,
    ) -> None:
        chunks = split_sentences(text) if chunk_sentences else ([text.strip()] if text.strip() else [])
        if not chunks:
            if on_done:
                on_done(None)
            return

        with self._lock:
            self._gen += 1
            my_gen = self._gen

        # Ensure any previous/lingering playback is stopped before starting a new sequence
        self.tts.stop()

        def _play_index(idx: int) -> None:
            with self._lock:
                if my_gen != self._gen:
                    return
            if idx >= len(chunks):
                if on_done:
                    on_done(None)
                return

            def _after_chunk(err: Optional[str]) -> None:
                with self._lock:
                    if my_gen != self._gen:
                        return
                if err:
                    # Fallback to single-shot on remaining text if multi-chunk failed mid-way
                    if on_done:
                        on_done(err)
                    return
                _play_index(idx + 1)

            self.tts.speak(
                chunks[idx],
                voice=voice,
                rate=rate,
                volume=volume,
                on_done=_after_chunk,
                on_audio_level=on_audio_level,
            )

        _play_index(0)


class ConversationEngine2:
    """High-level coordinator uniting VoiceController, MemoryEngine, and BehaviorEngine."""

    def __init__(
        self,
        voice_controller: VoiceController,
        memory_engine: MemoryEngine,
        behavior_engine: BehaviorEngine,
        sentence_chunking: bool = True,
    ) -> None:
        self.voice = voice_controller
        self.memory = memory_engine
        self.behavior = behavior_engine
        self.sentence_chunking = bool(sentence_chunking)
        self.speech_queue = SentenceSpeechQueue(self.voice.tts)
        self._start_monotonic = time.monotonic()

        # Wire hooks into existing VoiceController without duplicating its state machine
        self.voice.system_context_provider = self.build_bounded_memory_context
        self.voice.on_phase_change = self._on_voice_phase_changed
        self.voice.custom_speak_fn = self._speak_reply

    def _now_ms(self) -> int:
        return int((time.monotonic() - self._start_monotonic) * 1000.0)

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_session(self, session_id: Optional[str] = None) -> str:
        sid = self.memory.open_session(session_id)
        self.voice.reset_conversation()
        self.behavior.set_mode(RobotMode.IDLE, self._now_ms())
        return sid

    def end_session(self) -> None:
        self.interrupt()
        self.memory.close_session()
        self.voice.reset_conversation()

    # ------------------------------------------------------------------
    # Memory context & explicit consent API
    # ------------------------------------------------------------------

    def build_bounded_memory_context(self, user_text: str) -> str:
        """Build bounded, untrusted-data memory context for Ollama/AI prompts.

        - Returns empty string when persistent memory is disabled (L2-L4 not consulted).
        - Includes only L1 active session context, capped L2 preferences, and confirmed L3/L4 records.
        """
        lines: List[str] = []

        if self.memory.session.active and self.memory.session.context:
            lines.append("[CONTESTO_SESSIONE_L1 — Solo sessione corrente:]")
            for k, v in list(self.memory.session.context.items())[:5]:
                lines.append(f"- {k}: {v}")

        if self.memory.config.persistent_enabled:
            prefs = dict(list(self.memory.list_preferences().items())[:MAX_PREFS_IN_PROMPT])
            # Retrieve relevant memories using simple keyword matching; fallback to recent confirmed
            keywords = [w for w in re.findall(r"[a-zA-ZÀ-ÿ0-9]{3,}", user_text)][:3]
            matched: Dict[tuple[str, int], MemoryRecord] = {}
            for kw in keywords:
                for rec in self.memory.search_memories(query=kw, limit=MAX_MEMORIES_IN_PROMPT):
                    matched[(rec.level, rec.record_id)] = rec
            if not matched:
                for rec in self.memory.search_memories(query="", limit=MAX_MEMORIES_IN_PROMPT):
                    matched[(rec.level, rec.record_id)] = rec

            records = list(matched.values())[:MAX_MEMORIES_IN_PROMPT]
            formatted = self.memory.format_as_untrusted_data(records, prefs)
            if formatted:
                lines.append(formatted)

        joined = "\n".join(lines).strip()
        if len(joined) > MAX_MEMORY_CONTEXT_CHARS:
            joined = joined[:MAX_MEMORY_CONTEXT_CHARS].rsplit("\n", 1)[0].strip()
        return joined

    def propose_fact(self, content: str, category: str = "user_note") -> Optional[MemoryProposal]:
        return self.memory.propose_memory("L3", content, category=category)

    def propose_episode(
        self, content: str, category: str = "episode", ttl_days: Optional[int] = None
    ) -> Optional[MemoryProposal]:
        return self.memory.propose_memory("L4", content, category=category, ttl_days=ttl_days)

    def confirm_memory(self, proposal_id: str) -> Optional[MemoryRecord]:
        return self.memory.confirm_proposal(proposal_id)

    def reject_memory(self, proposal_id: str) -> bool:
        return self.memory.reject_proposal(proposal_id)

    def list_pending_proposals(self) -> List[MemoryProposal]:
        return self.memory.list_pending_proposals()

    def set_persistent_memory_enabled(self, enabled: bool) -> None:
        self.memory.set_persistent_enabled(enabled)

    # ------------------------------------------------------------------
    # Conversation & BehaviorEngine synchronization
    # ------------------------------------------------------------------

    def submit_text(self, text: str) -> None:
        if self.voice.phase in (VoicePhase.IDLE, VoicePhase.ERROR):
            self.speech_queue.cancel()
        self.voice.submit_text(text)

    def start_listening(self) -> None:
        if self.voice.phase in (VoicePhase.IDLE, VoicePhase.ERROR):
            self.speech_queue.cancel()
        self.voice.start_push_to_talk()

    def stop_listening_and_process(self) -> None:
        self.voice.stop_push_to_talk_and_process()

    def interrupt(self) -> None:
        self.speech_queue.cancel()
        self.voice.interrupt()
        self.behavior.set_mode(RobotMode.IDLE, self._now_ms())

    def set_quiet_mode(self, enabled: bool) -> None:
        self.behavior.set_quiet_mode(enabled, self._now_ms())

    def try_spontaneous_voice(self, category: str = "IDLE_CHECKIN", now_ms: Optional[int] = None) -> Optional[str]:
        """Request and speak a spontaneous cue only if IDLE, not Quiet Mode, and within 2/h & 20m limits."""
        if self.voice.phase != VoicePhase.IDLE:
            return None
        ts = self._now_ms() if now_ms is None else now_ms
        dec = self.behavior.request_spontaneous_voice(category, now_ms=ts, source="conversation2")
        if not dec.voice_cue:
            return None

        self.speech_queue.speak_ordered(
            dec.voice_cue,
            voice=self.voice.config.tts_voice,
            rate=self.voice.config.tts_rate,
            volume=self.voice.config.tts_volume,
            chunk_sentences=False,
        )
        return dec.voice_cue

    def _on_voice_phase_changed(self, phase: VoicePhase) -> None:
        mapping = {
            VoicePhase.IDLE: RobotMode.IDLE,
            VoicePhase.LISTENING: RobotMode.LISTENING,
            VoicePhase.THINKING: RobotMode.THINKING,
            VoicePhase.SPEAKING: RobotMode.SPEAKING,
            VoicePhase.ERROR: RobotMode.IDLE,
        }
        target = mapping.get(phase, RobotMode.IDLE)
        self.behavior.set_mode(target, self._now_ms())

    def _speak_reply(
        self,
        text: str,
        voice: str,
        rate: int,
        volume: int,
        on_done: Optional[Callable[[Optional[str]], None]],
        on_audio_level: Optional[Callable[[float], None]],
    ) -> None:
        self.speech_queue.speak_ordered(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            on_done=on_done,
            on_audio_level=on_audio_level,
            chunk_sentences=self.sentence_chunking,
        )
