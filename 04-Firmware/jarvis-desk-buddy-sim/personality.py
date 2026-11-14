"""JARVIS LEGO BOT — PersonalityProfile (FASE 9.1).

Preserves Personality C (giocosa, affettuosa, curiosa, leggermente birichina)
with configurable expressiveness, initiative limits, and non-repetitive cue selection.
Simulated mood states only — no claims of real consciousness or persistence.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import math
import random
from typing import Deque, Dict, Optional, Sequence


def _clamp(value: float, lo: float, hi: float, default: float = 0.75) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return default
    return max(lo, min(hi, float(value)))


@dataclass
class PersonalityConfig:
    """Configurable Personality C parameters (JSON-ready for future FASE 9.2)."""

    # Character traits (Personality C baseline)
    playfulness_bias: float = 0.75
    affection_bias: float = 0.75
    curiosity_bias: float = 0.80
    mischief_bias: float = 0.45

    # User-tunable behavior controls
    expressive_intensity: float = 1.0  # [0.3 .. 1.5]
    initiative_frequency: float = 1.0  # [0.0 .. 1.5] (0.0 disables spontaneous)
    behavior_variation: float = 1.0    # [0.0 .. 1.0]

    # Approved FASE 9.0 spontaneous voice initiative limits
    initiatives_enabled: bool = True
    max_voice_initiatives_per_hour: int = 2
    min_voice_initiative_interval_ms: int = 20 * 60 * 1000  # 20 minutes

    def normalized(self) -> "PersonalityConfig":
        return PersonalityConfig(
            playfulness_bias=_clamp(self.playfulness_bias, 0.0, 1.0),
            affection_bias=_clamp(self.affection_bias, 0.0, 1.0),
            curiosity_bias=_clamp(self.curiosity_bias, 0.0, 1.0),
            mischief_bias=_clamp(self.mischief_bias, 0.0, 1.0),
            expressive_intensity=_clamp(self.expressive_intensity, 0.3, 1.5),
            initiative_frequency=_clamp(self.initiative_frequency, 0.0, 1.5),
            behavior_variation=_clamp(self.behavior_variation, 0.0, 1.0),
            initiatives_enabled=bool(self.initiatives_enabled),
            max_voice_initiatives_per_hour=max(0, int(self.max_voice_initiatives_per_hour)),
            min_voice_initiative_interval_ms=max(0, int(self.min_voice_initiative_interval_ms)),
        )


@dataclass
class MoodState:
    """Bounded simulated mood state (in-memory only, decays toward baseline)."""

    energy: float = 0.70
    playfulness: float = 0.70
    affection: float = 0.70

    def clamp_all(self) -> None:
        self.energy = _clamp(self.energy, 0.1, 1.0)
        self.playfulness = _clamp(self.playfulness, 0.1, 1.0)
        self.affection = _clamp(self.affection, 0.1, 1.0)


DEFAULT_SPONTANEOUS_CUES: Dict[str, tuple[str, ...]] = {
    "IDLE_CHECKIN": (
        "Ehi, ci sei? Io sono qui pronto!",
        "Tutto tranquillo qui sulla scrivania.",
        "Se hai bisogno, premi pure o parlami!",
    ),
    "PROXIMITY_GREET": (
        "Ciao! Ti ho visto avvicinarti!",
        "Ehi, eccoti qui!",
        "Ciao! Tutto bene?",
    ),
    "AFFECTION_PET": (
        "Che bello, grazie!",
        "Hehe, così mi fai contento!",
        "Sempre pronto per te!",
    ),
    "CURIOUS_LOOK": (
        "Hmm, cosa succede da quella parte?",
        "Mi guardo un po' intorno...",
    ),
}


class PersonalityProfile:
    """Manages Personality C traits, simulated mood dynamics, and non-repetitive cues."""

    def __init__(self, config: Optional[PersonalityConfig] = None, seed: int = 2026) -> None:
        self.config = (config or PersonalityConfig()).normalized()
        self._rng = random.Random(seed)
        self.mood = MoodState(
            energy=0.70,
            playfulness=self.config.playfulness_bias,
            affection=self.config.affection_bias,
        )
        self._recent_cues: Dict[str, Deque[str]] = {}
        self._last_decay_ms: int = 0

    def update_config(self, config: PersonalityConfig) -> None:
        self.config = config.normalized()

    def apply_interaction(self, kind: str) -> None:
        """Adjust simulated mood gently in response to an interaction kind."""
        if kind == "AFFECTION":
            self.mood.affection += 0.10
            self.mood.playfulness += 0.05
        elif kind == "PLAYFUL":
            self.mood.playfulness += 0.12
            self.mood.energy += 0.05
        elif kind == "CURIOUS":
            self.mood.energy += 0.06
        elif kind == "TIRED":
            self.mood.energy -= 0.15
        elif kind == "WAKE":
            self.mood.energy = max(self.mood.energy, 0.65)
        self.mood.clamp_all()

    def tick_decay(self, now_ms: int) -> None:
        """Slowly decay mood back toward Personality C baseline."""
        if now_ms <= self._last_decay_ms:
            return
        if self._last_decay_ms == 0:
            self._last_decay_ms = now_ms
            return
        dt_sec = (now_ms - self._last_decay_ms) / 1000.0
        self._last_decay_ms = now_ms
        rate = min(0.25, dt_sec * 0.01)
        self.mood.energy += (0.70 - self.mood.energy) * rate
        self.mood.playfulness += (self.config.playfulness_bias - self.mood.playfulness) * rate
        self.mood.affection += (self.config.affection_bias - self.mood.affection) * rate
        self.mood.clamp_all()

    def pick_cue(self, category: str, candidates: Optional[Sequence[str]] = None) -> Optional[str]:
        """Select a cue avoiding recent repetitions when variation is enabled."""
        pool = list(candidates if candidates is not None else DEFAULT_SPONTANEOUS_CUES.get(category, ()))
        if not pool:
            return None
        if len(pool) == 1 or self.config.behavior_variation <= 0.05:
            return pool[0]

        history = self._recent_cues.setdefault(category, deque(maxlen=min(3, len(pool) - 1)))
        fresh = [c for c in pool if c not in history]
        choice = self._rng.choice(fresh if fresh else pool)
        history.append(choice)
        return choice
