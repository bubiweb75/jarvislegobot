"""JARVIS LEGO BOT — Emotion & Reaction Engine (Personalità C: Molto espressivo).

Independent, deterministic, testable emotion engine that maps internal and external
stimuli to OLED eye expressions, micro-behaviors, and optional brief voice cues.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import random
import re
from typing import Dict, List, Optional, Set, Tuple

from eye_engine import Expression


class StimulusType(str, Enum):
    GREETING = "GREETING"
    COMPLIMENT = "COMPLIMENT"
    QUESTION = "QUESTION"
    HARD_ANSWER = "HARD_ANSWER"
    JOKE = "JOKE"
    SUDDEN_NOISE = "SUDDEN_NOISE"
    BUTTON_PRESS = "BUTTON_PRESS"
    INACTIVITY = "INACTIVITY"
    WAKE_UP = "WAKE_UP"
    TEMP_ERROR = "TEMP_ERROR"
    REPLY_DONE = "REPLY_DONE"


DEFAULT_STIMULUS_PRIORITIES: Dict[StimulusType, int] = {
    StimulusType.TEMP_ERROR: 95,
    StimulusType.WAKE_UP: 90,
    StimulusType.SUDDEN_NOISE: 85,
    StimulusType.BUTTON_PRESS: 80,
    StimulusType.COMPLIMENT: 70,
    StimulusType.JOKE: 68,
    StimulusType.GREETING: 65,
    StimulusType.REPLY_DONE: 55,
    StimulusType.QUESTION: 45,
    StimulusType.HARD_ANSWER: 40,
    StimulusType.INACTIVITY: 20,
}

DEFAULT_COOLDOWNS_MS: Dict[StimulusType, int] = {
    StimulusType.TEMP_ERROR: 2500,
    StimulusType.WAKE_UP: 1500,
    StimulusType.SUDDEN_NOISE: 6000,
    StimulusType.BUTTON_PRESS: 700,
    StimulusType.COMPLIMENT: 4000,
    StimulusType.JOKE: 4000,
    StimulusType.GREETING: 5000,
    StimulusType.REPLY_DONE: 1200,
    StimulusType.QUESTION: 1800,
    StimulusType.HARD_ANSWER: 2500,
    StimulusType.INACTIVITY: 10000,
}


@dataclass
class EmotionConfig:
    """User-configurable parameters for Personality C."""

    expressiveness: float = 1.0
    spontaneous_enabled: bool = True
    spontaneous_interval_ms: int = 7500
    inactivity_sleepy_ms: int = 35000
    inactivity_sleeping_ms: int = 75000
    voice_reactions_enabled: bool = True
    silent_mode: bool = False
    enabled_stimuli: Set[StimulusType] = field(default_factory=lambda: set(StimulusType))

    def reset_defaults(self) -> None:
        self.expressiveness = 1.0
        self.spontaneous_enabled = True
        self.spontaneous_interval_ms = 7500
        self.inactivity_sleepy_ms = 35000
        self.inactivity_sleeping_ms = 75000
        self.voice_reactions_enabled = True
        self.silent_mode = False
        self.enabled_stimuli = set(StimulusType)


@dataclass
class StimulusEvent:
    stimulus: StimulusType
    now_ms: int
    priority: int
    source: str = "system"
    payload: str = ""
    seq: int = 0


@dataclass
class ReactionDecision:
    expression: Expression
    duration_ms: int
    priority: int
    stimulus: Optional[StimulusType]
    return_to: Expression
    voice_line: Optional[str] = None
    gaze_dx: Optional[int] = None
    gaze_dy: Optional[int] = None
    trigger_blink: bool = False
    reason: str = ""


_GREETING_RE = re.compile(
    r"\b(ciao|salve|buongiorno|buonasera|buonanotte|ehi|hey|hola|eccomi)\b",
    re.IGNORECASE,
)
_COMPLIMENT_RE = re.compile(
    r"\b(bravo|bravissimo|grande|grazie|fantastico|mitico|adoro|simpatico|carino|genio|ottimo|perfetto)\b|ti voglio bene",
    re.IGNORECASE,
)
_JOKE_RE = re.compile(
    r"\b(ahah+|haha+|hehe+|battuta|barzelletta|scherzo|divertente|ridere|buffo|birichino)\b",
    re.IGNORECASE,
)
_QUESTION_RE = re.compile(
    r"\?|\b(come|perch[eé]|cosa|quando|chi|quale|quanto|dove|spiegami|dimmi)\b",
    re.IGNORECASE,
)


def detect_text_stimulus(text: str) -> Optional[StimulusType]:
    """Rule-based Italian stimulus detector for user/assistant text."""
    cleaned = (text or "").strip()
    if not cleaned:
        return None
    if _COMPLIMENT_RE.search(cleaned):
        return StimulusType.COMPLIMENT
    if _JOKE_RE.search(cleaned):
        return StimulusType.JOKE
    if _GREETING_RE.search(cleaned):
        return StimulusType.GREETING
    if _QUESTION_RE.search(cleaned):
        return StimulusType.QUESTION
    return None


class EmotionEngine:
    """Personality C (Molto espressivo) state, priority queue, cooldown & micro-behavior engine."""

    def __init__(self, config: Optional[EmotionConfig] = None, seed: int = 2026) -> None:
        self.config = config if config is not None else EmotionConfig()
        self.rng = random.Random(seed)
        self._seq = 0

        self.base_expression: Expression = Expression.IDLE
        self.current_expression: Expression = Expression.IDLE
        self.conversation_busy: bool = False
        self.is_sleeping: bool = False

        self.active_reaction: Optional[ReactionDecision] = None
        self.active_until_ms: int = 0
        self.pending_queue: List[StimulusEvent] = []
        self.cooldown_until: Dict[StimulusType, int] = {}

        self.last_activity_ms: int = 0
        self.next_spontaneous_ms: int = self.config.spontaneous_interval_ms
        self.last_event_label: str = "Nessuno"
        self.last_voice_line: Optional[str] = None
        self._button_cycle_idx: int = 0

    def reset_defaults(self, now_ms: int = 0) -> None:
        self.config.reset_defaults()
        self.pending_queue.clear()
        self.cooldown_until.clear()
        self.active_reaction = None
        self.active_until_ms = 0
        self.is_sleeping = False
        self.conversation_busy = False
        self.base_expression = Expression.IDLE
        self.current_expression = Expression.IDLE
        self.last_activity_ms = now_ms
        self.next_spontaneous_ms = now_ms + self.config.spontaneous_interval_ms
        self.last_event_label = "Default ripristinati"
        self.last_voice_line = None

    def touch_activity(self, now_ms: int) -> Optional[ReactionDecision]:
        """Register user/system activity; wakes JARVIS if sleeping or sleepy."""
        self.last_activity_ms = now_ms
        if self.is_sleeping or self.base_expression in (Expression.SLEEPY, Expression.SLEEPING):
            self.is_sleeping = False
            self.base_expression = Expression.IDLE
            return self.push_stimulus(StimulusType.WAKE_UP, now_ms, source="activity")
        return None

    def set_conversation_busy(
        self,
        busy: bool,
        now_ms: int,
        phase_expr: Optional[Expression] = None,
    ) -> None:
        """Pause spontaneous micro-behaviors during LISTENING / THINKING / SPEAKING."""
        self.conversation_busy = busy
        self.last_activity_ms = now_ms
        if busy:
            self.is_sleeping = False
            if phase_expr is not None:
                self.base_expression = phase_expr
                self.current_expression = phase_expr
                self.active_reaction = None
                self.active_until_ms = 0
        else:
            if self.base_expression in (Expression.LISTENING, Expression.THINKING, Expression.SPEAKING):
                self.base_expression = Expression.IDLE
            if self.active_reaction is None:
                self.current_expression = self.base_expression

    def push_stimulus(
        self,
        stimulus: StimulusType,
        now_ms: int,
        source: str = "system",
        payload: str = "",
        priority_override: Optional[int] = None,
    ) -> Optional[ReactionDecision]:
        """Enqueue a stimulus with cooldown and priority preemption checks."""
        if stimulus not in self.config.enabled_stimuli:
            return None

        cooldown_end = self.cooldown_until.get(stimulus, 0)
        if now_ms < cooldown_end:
            return None

        priority = (
            priority_override
            if priority_override is not None
            else DEFAULT_STIMULUS_PRIORITIES.get(stimulus, 50)
        )
        self._seq += 1
        event = StimulusEvent(
            stimulus=stimulus,
            now_ms=now_ms,
            priority=priority,
            source=source,
            payload=payload,
            seq=self._seq,
        )

        # Wake up on direct user stimuli
        if stimulus not in (StimulusType.INACTIVITY, StimulusType.TEMP_ERROR):
            self.last_activity_ms = now_ms
            if self.is_sleeping and stimulus != StimulusType.WAKE_UP:
                self.is_sleeping = False
                self.base_expression = Expression.IDLE

        self.pending_queue.append(event)
        self.pending_queue.sort(key=lambda e: (-e.priority, e.seq))
        return self._dispatch_next_if_ready(now_ms)

    def _scaled_duration(self, base_ms: int) -> int:
        scale = max(0.5, min(1.5, self.config.expressiveness))
        return int(round(base_ms * scale))

    def _pick_voice_line(self, candidates: Tuple[str, ...], chance: float) -> Optional[str]:
        if self.config.silent_mode or not self.config.voice_reactions_enabled:
            return None
        if self.rng.random() <= chance:
            return self.rng.choice(candidates)
        return None

    def _build_reaction(self, event: StimulusEvent) -> ReactionDecision:
        s = event.stimulus
        ret = Expression.IDLE

        if s == StimulusType.GREETING:
            expr = self.rng.choice((Expression.HAPPY, Expression.WINK))
            return ReactionDecision(
                expression=expr,
                duration_ms=self._scaled_duration(2300),
                priority=event.priority,
                stimulus=s,
                return_to=ret,
                voice_line=self._pick_voice_line(("Ehi, ciao!", "Eccomi qui!"), 0.55),
                reason="Saluto amichevole",
            )

        if s == StimulusType.COMPLIMENT:
            expr = self.rng.choice((Expression.LOVE, Expression.SHY))
            return ReactionDecision(
                expression=expr,
                duration_ms=self._scaled_duration(2600),
                priority=event.priority,
                stimulus=s,
                return_to=ret,
                voice_line=self._pick_voice_line(("Oh, grazie!", "Mi fai arrossire!"), 0.60),
                reason="Reazione affettuosa a complimento",
            )

        if s == StimulusType.QUESTION:
            return ReactionDecision(
                expression=Expression.CURIOUS,
                duration_ms=self._scaled_duration(1600),
                priority=event.priority,
                stimulus=s,
                return_to=ret,
                reason="Curiosità su domanda",
            )

        if s == StimulusType.HARD_ANSWER:
            return ReactionDecision(
                expression=Expression.THINKING,
                duration_ms=self._scaled_duration(1800),
                priority=event.priority,
                stimulus=s,
                return_to=ret,
                reason="Elaborazione complessa",
            )

        if s == StimulusType.JOKE:
            expr = self.rng.choice((Expression.MISCHIEVOUS, Expression.WINK, Expression.HAPPY))
            return ReactionDecision(
                expression=expr,
                duration_ms=self._scaled_duration(2400),
                priority=event.priority,
                stimulus=s,
                return_to=ret,
                voice_line=self._pick_voice_line(("Ahah, bella questa!", "Questa me la segno!"), 0.50),
                reason="Reazione scherzosa",
            )

        if s == StimulusType.SUDDEN_NOISE:
            return ReactionDecision(
                expression=Expression.SURPRISED,
                duration_ms=self._scaled_duration(1800),
                priority=event.priority,
                stimulus=s,
                return_to=ret,
                voice_line=self._pick_voice_line(("Oh! Che succede?",), 0.35),
                reason="Sobbalzo per rumore improvviso",
            )

        if s == StimulusType.BUTTON_PRESS:
            cycle = (Expression.HAPPY, Expression.WINK, Expression.CURIOUS, Expression.MISCHIEVOUS)
            expr = cycle[self._button_cycle_idx % len(cycle)]
            self._button_cycle_idx += 1
            return ReactionDecision(
                expression=expr,
                duration_ms=self._scaled_duration(2000),
                priority=event.priority,
                stimulus=s,
                return_to=ret,
                voice_line=self._pick_voice_line(("Eccomi!", "Pronto!"), 0.40),
                reason="Interazione pulsante",
            )

        if s == StimulusType.INACTIVITY:
            if event.payload == "SLEEPING":
                self.is_sleeping = True
                self.base_expression = Expression.SLEEPING
                return ReactionDecision(
                    expression=Expression.SLEEPING,
                    duration_ms=self._scaled_duration(4000),
                    priority=event.priority,
                    stimulus=s,
                    return_to=Expression.SLEEPING,
                    reason="Addormentamento per inattività",
                )
            self.base_expression = Expression.SLEEPY
            return ReactionDecision(
                expression=Expression.SLEEPY,
                duration_ms=self._scaled_duration(3500),
                priority=event.priority,
                stimulus=s,
                return_to=Expression.SLEEPY,
                reason="Sonnolenza per inattività",
            )

        if s == StimulusType.WAKE_UP:
            self.is_sleeping = False
            self.base_expression = Expression.IDLE
            return ReactionDecision(
                expression=Expression.HAPPY,
                duration_ms=self._scaled_duration(2000),
                priority=event.priority,
                stimulus=s,
                return_to=Expression.IDLE,
                voice_line=self._pick_voice_line(("Buongiorno! Eccomi sveglio.",), 0.45),
                trigger_blink=True,
                reason="Risveglio attivo",
            )

        if s == StimulusType.TEMP_ERROR:
            return ReactionDecision(
                expression=Expression.CONFUSED,
                duration_ms=self._scaled_duration(2400),
                priority=event.priority,
                stimulus=s,
                return_to=Expression.IDLE,
                voice_line=self._pick_voice_line(("Ops, qualcosa non torna.",), 0.35),
                reason="Confusione per errore temporaneo",
            )

        # REPLY_DONE
        expr = self.rng.choice((Expression.HAPPY, Expression.WINK))
        return ReactionDecision(
            expression=expr,
            duration_ms=self._scaled_duration(1500),
            priority=event.priority,
            stimulus=s,
            return_to=Expression.IDLE,
            reason="Chiusura espressiva risposta",
        )

    def _dispatch_next_if_ready(self, now_ms: int) -> Optional[ReactionDecision]:
        if not self.pending_queue:
            return None

        top = self.pending_queue[0]
        if self.active_reaction is not None and now_ms < self.active_until_ms:
            if top.priority <= self.active_reaction.priority:
                return None

        self.pending_queue.pop(0)
        # Drop any stale lower-priority duplicates of the same stimulus
        self.pending_queue = [e for e in self.pending_queue if e.stimulus != top.stimulus]

        decision = self._build_reaction(top)
        self.active_reaction = decision
        self.active_until_ms = now_ms + decision.duration_ms
        self.current_expression = decision.expression
        self.last_event_label = f"{top.stimulus.value} -> {decision.expression.value}"
        self.last_voice_line = decision.voice_line
        self.cooldown_until[top.stimulus] = now_ms + DEFAULT_COOLDOWNS_MS.get(top.stimulus, 2000)
        return decision

    def tick(self, now_ms: int) -> Optional[ReactionDecision]:
        """Advance timers, handle timeouts, inactivity transitions, and spontaneous behaviors."""
        # 1. Expire active reaction if finished
        if self.active_reaction is not None and now_ms >= self.active_until_ms:
            ret_expr = self.active_reaction.return_to
            self.active_reaction = None
            self.current_expression = ret_expr if not self.conversation_busy else self.base_expression

        # 2. Dispatch queued higher-priority or waiting event
        dispatched = self._dispatch_next_if_ready(now_ms)
        if dispatched is not None:
            return dispatched

        # 3. Skip inactivity/spontaneous during active conversation or active reaction
        if self.conversation_busy or self.active_reaction is not None:
            return None

        # 4. Inactivity progression (IDLE -> SLEEPY -> SLEEPING)
        idle_elapsed = now_ms - self.last_activity_ms
        if not self.is_sleeping:
            if idle_elapsed >= self.config.inactivity_sleeping_ms:
                return self.push_stimulus(StimulusType.INACTIVITY, now_ms, source="timer", payload="SLEEPING")
            if (
                idle_elapsed >= self.config.inactivity_sleepy_ms
                and self.base_expression == Expression.IDLE
            ):
                return self.push_stimulus(StimulusType.INACTIVITY, now_ms, source="timer", payload="SLEEPY")

        # 5. Spontaneous micro-behaviors only in IDLE
        if (
            self.config.spontaneous_enabled
            and not self.is_sleeping
            and self.base_expression == Expression.IDLE
            and now_ms >= self.next_spontaneous_ms
        ):
            interval = max(2500, int(self.config.spontaneous_interval_ms / max(0.5, self.config.expressiveness)))
            self.next_spontaneous_ms = now_ms + self.rng.randint(int(interval * 0.75), int(interval * 1.35))
            return self._trigger_spontaneous_micro(now_ms)

        return None

    def _trigger_spontaneous_micro(self, now_ms: int) -> ReactionDecision:
        roll = self.rng.random()
        if roll < 0.38:
            # Playful glance + blink
            dx = self.rng.choice((-7, -4, 4, 7))
            dy = self.rng.choice((-2, 0, 2))
            decision = ReactionDecision(
                expression=Expression.IDLE,
                duration_ms=1400,
                priority=10,
                stimulus=None,
                return_to=Expression.IDLE,
                gaze_dx=dx,
                gaze_dy=dy,
                trigger_blink=True,
                reason="Sguardo spontaneo",
            )
        elif roll < 0.65:
            decision = ReactionDecision(
                expression=Expression.CURIOUS,
                duration_ms=self._scaled_duration(1800),
                priority=10,
                stimulus=None,
                return_to=Expression.IDLE,
                reason="Curiosità spontanea",
            )
        elif roll < 0.85:
            decision = ReactionDecision(
                expression=Expression.WINK,
                duration_ms=self._scaled_duration(1300),
                priority=10,
                stimulus=None,
                return_to=Expression.IDLE,
                reason="Occhiolino spontaneo",
            )
        else:
            decision = ReactionDecision(
                expression=Expression.MISCHIEVOUS,
                duration_ms=self._scaled_duration(1600),
                priority=10,
                stimulus=None,
                return_to=Expression.IDLE,
                reason="Espressione birichina spontanea",
            )

        self.active_reaction = decision
        self.active_until_ms = now_ms + decision.duration_ms
        self.current_expression = decision.expression
        self.last_event_label = f"SPONTANEO -> {decision.expression.value}"
        return decision

    def get_telemetry(self, now_ms: int) -> Dict[str, object]:
        rem_ms = max(0, self.active_until_ms - now_ms) if self.active_reaction else 0
        max_cd = max((max(0, v - now_ms) for v in self.cooldown_until.values()), default=0)
        return {
            "last_event": self.last_event_label,
            "active_emotion": self.current_expression.value,
            "base_expression": self.base_expression.value,
            "priority": self.active_reaction.priority if self.active_reaction else 0,
            "remaining_ms": rem_ms,
            "cooldown_ms": max_cd,
            "spontaneous_enabled": self.config.spontaneous_enabled,
            "silent_mode": self.config.silent_mode,
            "conversation_busy": self.conversation_busy,
            "is_sleeping": self.is_sleeping,
            "last_voice_line": self.last_voice_line or "",
        }
