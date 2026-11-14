"""JARVIS LEGO BOT — BehaviorEngine (FASE 9.1).

Central deterministic event coordinator that reuses EmotionEngine, SensorManager,
PersonalityProfile, and EyeEngine2 without duplicating their internal logic.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Deque, Dict, List, Optional

from emotion_engine import (
    DEFAULT_STIMULUS_PRIORITIES,
    EmotionEngine,
    ReactionDecision,
    StimulusType,
)
from eye_engine import Expression
from eye_engine_v2 import EyeEngine2, EyeStep
from personality import PersonalityProfile
from sensor_manager import SensorEvent, SensorManager


class RobotMode(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    SLEEPING = "SLEEPING"


BUSY_CONVERSATION_MODES = {RobotMode.LISTENING, RobotMode.THINKING, RobotMode.SPEAKING}


@dataclass(order=True)
class BehaviorEvent:
    """Prioritized event submitted to BehaviorEngine (higher priority wins)."""

    sort_key: tuple[int, int] = field(init=False, repr=False)
    priority: int
    timestamp_ms: int
    event_type: str  # "STIMULUS" | "MODE" | "SPONTANEOUS_VOICE" | "ERROR"
    source: str
    stimulus: Optional[StimulusType] = None
    target_mode: Optional[RobotMode] = None
    cue_category: Optional[str] = None
    sequence_name: Optional[str] = None
    cooldown_ms: int = 0

    def __post_init__(self) -> None:
        # Negative priority so min-sort or sorted(..., reverse=False) puts highest priority first;
        # older timestamp breaks ties deterministically.
        self.sort_key = (-int(self.priority), int(self.timestamp_ms))


@dataclass(frozen=True)
class BehaviorDiagnostic:
    """Privacy-safe diagnostic record of a BehaviorEngine decision."""

    timestamp_ms: int
    mode: RobotMode
    source: str
    event_type: str
    outcome: str
    expression: Optional[str] = None
    reason: str = ""


@dataclass
class BehaviorDecision:
    """Result emitted by BehaviorEngine for UI, EyeBridge, or Voice AI."""

    mode: RobotMode
    expression: Optional[Expression] = None
    gaze_dx: Optional[int] = None
    gaze_dy: Optional[int] = None
    trigger_blink: bool = False
    voice_cue: Optional[str] = None
    serial_commands: List[str] = field(default_factory=list)
    suppressed_reason: str = ""


class BehaviorEngine:
    """Central coordinator for modes, sensor events, Quiet Mode, and spontaneous initiatives."""

    def __init__(
        self,
        emotion_engine: Optional[EmotionEngine] = None,
        sensor_manager: Optional[SensorManager] = None,
        personality: Optional[PersonalityProfile] = None,
        eye_v2: Optional[EyeEngine2] = None,
        quiet_mode: bool = False,
        on_voice_cue: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.emotion_engine = emotion_engine or EmotionEngine()
        self.sensor_manager = sensor_manager
        self.personality = personality or PersonalityProfile()
        self.eye_v2 = eye_v2 or EyeEngine2()
        self.on_voice_cue = on_voice_cue

        self.mode: RobotMode = RobotMode.IDLE
        self.quiet_mode: bool = bool(quiet_mode)
        self._last_event_ms: Dict[str, int] = {}
        self._voice_initiative_timestamps_ms: Deque[int] = deque()
        self._pending_events: List[BehaviorEvent] = []
        self._active_sequence_priority: int = 0
        self.diagnostics: Deque[BehaviorDiagnostic] = deque(maxlen=30)

    @property
    def spontaneous_voice_count(self) -> int:
        """Number of spontaneous voice cues recorded in the rolling 1-hour window."""
        return len(self._voice_initiative_timestamps_ms)

    def set_quiet_mode(self, enabled: bool, now_ms: int = 0) -> None:
        self.quiet_mode = bool(enabled)
        self.emotion_engine.config.silent_mode = self.quiet_mode
        self._record(now_ms, "system", "QUIET_MODE", "APPLIED", reason=f"quiet={self.quiet_mode}")

    def set_mode(self, new_mode: RobotMode, now_ms: int) -> BehaviorDecision:
        """Transition robot operational mode and synchronize EmotionEngine/EyeEngine2."""
        if not isinstance(new_mode, RobotMode):
            self._record(now_ms, "system", "MODE", "ERROR", reason="invalid_mode")
            return BehaviorDecision(mode=self.mode, suppressed_reason="invalid_mode")

        self.mode = new_mode
        busy = new_mode in BUSY_CONVERSATION_MODES
        if busy:
            self.eye_v2.cancel_sequence()

        self.emotion_engine.set_conversation_busy(
            busy=busy,
            now_ms=now_ms,
            phase_expr=self._expression_for_mode(new_mode) if busy else None,
        )

        expr = self._expression_for_mode(new_mode)
        if new_mode == RobotMode.SLEEPING:
            self.personality.apply_interaction("TIRED")
        elif new_mode == RobotMode.IDLE:
            self.personality.apply_interaction("WAKE")

        look = self.eye_v2.contextual_look_for_mode(new_mode.value)
        cmds = [f"STATE:{expr.value}"]
        if look is not None:
            cmds.append(f"LOOK:{look[0]},{look[1]}")

        self._record(now_ms, "mode", "MODE", "APPLIED", expression=expr.value)
        return BehaviorDecision(
            mode=self.mode,
            expression=expr,
            gaze_dx=look[0] if look else None,
            gaze_dy=look[1] if look else None,
            serial_commands=cmds,
        )

    def submit_event(self, event: Optional[BehaviorEvent]) -> None:
        if event is None or event.timestamp_ms < 0:
            self._record(0, "unknown", "INVALID", "ERROR", reason="invalid_event")
            return
        self._pending_events.append(event)

    def submit_stimulus(
        self,
        stimulus: StimulusType,
        now_ms: int,
        source: str = "external",
        priority: Optional[int] = None,
        cooldown_ms: int = 0,
        sequence_name: Optional[str] = None,
    ) -> None:
        if not isinstance(stimulus, StimulusType):
            self._record(now_ms, source, "STIMULUS", "ERROR", reason="invalid_stimulus")
            return
        prio = DEFAULT_STIMULUS_PRIORITIES.get(stimulus, 50) if priority is None else int(priority)
        self.submit_event(
            BehaviorEvent(
                priority=prio,
                timestamp_ms=now_ms,
                event_type="STIMULUS",
                source=source,
                stimulus=stimulus,
                sequence_name=sequence_name,
                cooldown_ms=cooldown_ms,
            )
        )

    def can_trigger_spontaneous_voice(self, now_ms: int) -> tuple[bool, str]:
        """Enforce FASE 9.0 approved spontaneous voice limits strictly."""
        cfg = self.personality.config
        if not cfg.initiatives_enabled or cfg.initiative_frequency <= 0.0:
            return False, "initiatives_disabled"
        if self.quiet_mode or self.emotion_engine.config.silent_mode:
            return False, "quiet_mode"
        if self.mode in BUSY_CONVERSATION_MODES or self.mode == RobotMode.SLEEPING:
            return False, f"busy_or_sleeping:{self.mode.value}"

        # Prune timestamps older than 1 hour
        one_hour_ms = 60 * 60 * 1000
        while self._voice_initiative_timestamps_ms and (
            now_ms - self._voice_initiative_timestamps_ms[0] >= one_hour_ms
        ):
            self._voice_initiative_timestamps_ms.popleft()

        if len(self._voice_initiative_timestamps_ms) >= cfg.max_voice_initiatives_per_hour:
            return False, "hourly_limit_reached"

        if self._voice_initiative_timestamps_ms:
            elapsed = now_ms - self._voice_initiative_timestamps_ms[-1]
            if elapsed < cfg.min_voice_initiative_interval_ms:
                return False, "min_interval_active"

        return True, "ok"

    def request_spontaneous_voice(
        self,
        category: str,
        now_ms: int,
        source: str = "spontaneous",
        priority: int = 25,
    ) -> BehaviorDecision:
        """Attempt a spontaneous voice initiative respecting Quiet Mode, busy state, and rate limits."""
        if now_ms < 0:
            self._record(0, source, "SPONTANEOUS_VOICE", "ERROR", reason="negative_timestamp")
            return BehaviorDecision(mode=self.mode, suppressed_reason="negative_timestamp")

        allowed, reason = self.can_trigger_spontaneous_voice(now_ms)
        if not allowed:
            self._record(now_ms, source, "SPONTANEOUS_VOICE", f"SUPPRESSED:{reason}", reason=reason)
            return BehaviorDecision(mode=self.mode, suppressed_reason=reason)

        cue = self.personality.pick_cue(category)
        if not cue:
            self._record(now_ms, source, "SPONTANEOUS_VOICE", "SUPPRESSED:no_cue", reason="no_cue")
            return BehaviorDecision(mode=self.mode, suppressed_reason="no_cue")

        self._voice_initiative_timestamps_ms.append(now_ms)
        if self.on_voice_cue is not None:
            self.on_voice_cue(cue)
        self._record(now_ms, source, "SPONTANEOUS_VOICE", "APPLIED", reason=category)
        return BehaviorDecision(mode=self.mode, voice_cue=cue)

    def handle_sensor_events(self, events: List[SensorEvent], now_ms: int) -> None:
        """Translate SensorManager events into prioritized BehaviorEvents."""
        for ev in events:
            if ev.stimulus is None:
                continue
            seq = None
            if ev.stimulus == StimulusType.PROXIMITY_APPROACH:
                seq = "GREETING"
                self.personality.apply_interaction("CURIOUS")
            elif ev.stimulus in (StimulusType.TOUCH_SHORT, StimulusType.TOUCH_LONG):
                seq = "AFFECTION"
                self.personality.apply_interaction("AFFECTION")
            elif ev.stimulus == StimulusType.TOUCH_MULTI:
                seq = "MISCHIEVOUS_PLAY"
                self.personality.apply_interaction("PLAYFUL")
            elif ev.stimulus == StimulusType.LIGHT_DARK:
                self.personality.apply_interaction("TIRED")
            elif ev.stimulus == StimulusType.LIGHT_BRIGHT:
                self.personality.apply_interaction("WAKE")

            self.submit_stimulus(
                stimulus=ev.stimulus,
                now_ms=now_ms,
                source=f"sensor:{ev.sensor.value}",
                sequence_name=seq,
            )

    def tick(self, now_ms: int) -> Optional[BehaviorDecision]:
        """Advance SensorManager, queued prioritized events, EyeEngine2, and EmotionEngine."""
        if now_ms < 0:
            self._record(0, "system", "TICK", "ERROR", reason="negative_timestamp")
            return None

        self.personality.tick_decay(now_ms)

        if self.sensor_manager is not None and self.mode not in BUSY_CONVERSATION_MODES:
            sensor_events = self.sensor_manager.update(now_ms)
            if sensor_events:
                self.handle_sensor_events(sensor_events, now_ms)

        # Process highest-priority pending event first
        decision_out: Optional[BehaviorDecision] = None
        if self._pending_events:
            ordered = sorted(self._pending_events)
            self._pending_events.clear()
            for idx, ev in enumerate(ordered):
                if idx == 0:
                    decision_out = self._dispatch_event(ev, now_ms)
                else:
                    # Re-queue lower-priority stimulus only if not a duplicate; record preemption
                    self._record(
                        now_ms,
                        ev.source,
                        ev.event_type,
                        "PREEMPTED",
                        reason=f"lower_than:{ordered[0].priority}",
                    )

        # Advance active EyeEngine2 sequence
        seq_step = self.eye_v2.tick(now_ms)
        if not self.eye_v2.is_sequence_active:
            self._active_sequence_priority = 0
        if seq_step is not None and decision_out is None:
            decision_out = self._decision_from_eye_step(seq_step)

        # Advance EmotionEngine
        emo_dec = self.emotion_engine.tick(now_ms)
        if emo_dec is not None and decision_out is None:
            decision_out = self._decision_from_emotion(emo_dec, now_ms)

        return decision_out

    def _dispatch_event(self, ev: BehaviorEvent, now_ms: int) -> Optional[BehaviorDecision]:
        cooldown_key = f"{ev.event_type}:{ev.stimulus.value if ev.stimulus else ev.source}"
        if ev.cooldown_ms > 0 and cooldown_key in self._last_event_ms:
            if (now_ms - self._last_event_ms[cooldown_key]) < ev.cooldown_ms:
                self._record(now_ms, ev.source, ev.event_type, "SUPPRESSED_COOLDOWN")
                return BehaviorDecision(mode=self.mode, suppressed_reason="cooldown")

        if ev.event_type == "MODE" and ev.target_mode is not None:
            self._last_event_ms[cooldown_key] = now_ms
            return self.set_mode(ev.target_mode, now_ms)

        if ev.event_type == "STIMULUS" and ev.stimulus is not None:
            if self.mode in BUSY_CONVERSATION_MODES and ev.stimulus != StimulusType.TEMP_ERROR:
                self._record(now_ms, ev.source, "STIMULUS", "SUPPRESSED_BUSY", reason=self.mode.value)
                return BehaviorDecision(mode=self.mode, suppressed_reason="conversation_busy")

            self._last_event_ms[cooldown_key] = now_ms
            if self.eye_v2.is_sequence_active and ev.priority >= self._active_sequence_priority:
                self.eye_v2.cancel_sequence()
                self._active_sequence_priority = 0

            if ev.sequence_name and not self.eye_v2.is_sequence_active:
                step = self.eye_v2.start_sequence(ev.sequence_name, now_ms)
                if step is not None:
                    self._active_sequence_priority = ev.priority
                    self._record(
                        now_ms,
                        ev.source,
                        "SEQUENCE",
                        "APPLIED",
                        expression=step.expression.value,
                        reason=ev.sequence_name,
                    )
                    return self._decision_from_eye_step(step)

            emo_dec = self.emotion_engine.push_stimulus(ev.stimulus, now_ms, source=ev.source)
            if emo_dec is not None:
                return self._decision_from_emotion(emo_dec, now_ms, source=ev.source)
            self._record(now_ms, ev.source, "STIMULUS", "DEFERRED_TO_EMOTION_ENGINE")
            return None

        if ev.event_type == "SPONTANEOUS_VOICE":
            return self.request_spontaneous_voice(
                ev.cue_category or "IDLE_CHECKIN", now_ms, source=ev.source, priority=ev.priority
            )

        self._record(now_ms, ev.source, ev.event_type, "ERROR", reason="unhandled_event")
        return BehaviorDecision(mode=self.mode, suppressed_reason="unhandled_event")

    def _decision_from_eye_step(self, step: EyeStep) -> BehaviorDecision:
        return BehaviorDecision(
            mode=self.mode,
            expression=step.expression,
            gaze_dx=step.gaze_dx,
            gaze_dy=step.gaze_dy,
            trigger_blink=step.trigger_blink,
            serial_commands=step.to_serial_commands(),
        )

    def _decision_from_emotion(
        self, dec: ReactionDecision, now_ms: int, source: str = "emotion_engine"
    ) -> BehaviorDecision:
        cue: Optional[str] = None
        if dec.voice_line and not self.quiet_mode and self.mode not in BUSY_CONVERSATION_MODES:
            allowed, _ = self.can_trigger_spontaneous_voice(now_ms)
            if allowed:
                cue = dec.voice_line
                self._voice_initiative_timestamps_ms.append(now_ms)

        cmds = [f"STATE:{dec.expression.value}"]
        if dec.gaze_dx is not None and dec.gaze_dy is not None:
            cmds.append(f"LOOK:{dec.gaze_dx},{dec.gaze_dy}")
        if dec.trigger_blink:
            cmds.append("BLINK")

        self._record(now_ms, source, "EMOTION", "APPLIED", expression=dec.expression.value)
        return BehaviorDecision(
            mode=self.mode,
            expression=dec.expression,
            gaze_dx=dec.gaze_dx,
            gaze_dy=dec.gaze_dy,
            trigger_blink=dec.trigger_blink,
            voice_cue=cue,
            serial_commands=cmds,
        )

    @staticmethod
    def _expression_for_mode(mode: RobotMode) -> Expression:
        return {
            RobotMode.IDLE: Expression.IDLE,
            RobotMode.LISTENING: Expression.LISTENING,
            RobotMode.THINKING: Expression.THINKING,
            RobotMode.SPEAKING: Expression.SPEAKING,
            RobotMode.SLEEPING: Expression.SLEEPING,
        }[mode]

    def _record(
        self,
        now_ms: int,
        source: str,
        event_type: str,
        outcome: str,
        expression: Optional[str] = None,
        reason: str = "",
    ) -> None:
        self.diagnostics.append(
            BehaviorDiagnostic(
                timestamp_ms=now_ms,
                mode=self.mode,
                source=source,
                event_type=event_type,
                outcome=outcome,
                expression=expression,
                reason=reason,
            )
        )
