"""JARVIS LEGO BOT — EyeEngine 2.0 (FASE 9.1).

Builds on the 14 existing OLED expressions and the ESP32-S3 FASE 8.2A USB-CDC
serial protocol (STATE:*, LOOK:dx,dy, BLINK, AUTO:ON/OFF) without adding any
unsupported firmware commands.

Hardware-compatible features vs simulator-only features are explicitly tagged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from eye_engine import Expression


# Exact ESP32-S3 firmware LOOK bounds (state_machine.cpp: dx -11..11, dy -6..6)
FIRMWARE_LOOK_DX_MIN = -11
FIRMWARE_LOOK_DX_MAX = 11
FIRMWARE_LOOK_DY_MIN = -6
FIRMWARE_LOOK_DY_MAX = 6

ALL_14_EXPRESSIONS: Tuple[Expression, ...] = (
    Expression.IDLE,
    Expression.HAPPY,
    Expression.CURIOUS,
    Expression.SLEEPY,
    Expression.LISTENING,
    Expression.THINKING,
    Expression.SPEAKING,
    Expression.SURPRISED,
    Expression.SHY,
    Expression.LOVE,
    Expression.WINK,
    Expression.CONFUSED,
    Expression.MISCHIEVOUS,
    Expression.SLEEPING,
)


def clamp_firmware_look(dx: int, dy: int) -> Tuple[int, int]:
    """Clamp gaze offsets to the exact range accepted by ESP32-S3 FASE 8.2A."""
    return (
        max(FIRMWARE_LOOK_DX_MIN, min(FIRMWARE_LOOK_DX_MAX, int(dx))),
        max(FIRMWARE_LOOK_DY_MIN, min(FIRMWARE_LOOK_DY_MAX, int(dy))),
    )


@dataclass(frozen=True)
class EyeStep:
    """Single step in a timed eye sequence.

    All fields translate directly to existing ESP32-S3 FASE 8.2A serial commands
    when ``simulator_only=False``.
    """

    expression: Expression
    duration_ms: int
    gaze_dx: Optional[int] = None
    gaze_dy: Optional[int] = None
    trigger_blink: bool = False
    simulator_only: bool = False

    def to_serial_commands(self) -> List[str]:
        """Return FASE 8.2A USB-CDC serial commands for this step."""
        if self.simulator_only:
            return []
        cmds = [f"STATE:{self.expression.value}"]
        if self.gaze_dx is not None and self.gaze_dy is not None:
            dx, dy = clamp_firmware_look(self.gaze_dx, self.gaze_dy)
            cmds.append(f"LOOK:{dx},{dy}")
        if self.trigger_blink:
            cmds.append("BLINK")
        return cmds


BUILTIN_SEQUENCES: Dict[str, Tuple[EyeStep, ...]] = {
    "GREETING": (
        EyeStep(Expression.SURPRISED, 450, gaze_dx=0, gaze_dy=-2),
        EyeStep(Expression.HAPPY, 1400, gaze_dx=0, gaze_dy=0, trigger_blink=True),
        EyeStep(Expression.WINK, 700),
    ),
    "CURIOUS_SCAN": (
        EyeStep(Expression.CURIOUS, 900, gaze_dx=-6, gaze_dy=-1),
        EyeStep(Expression.CURIOUS, 900, gaze_dx=6, gaze_dy=-1),
    ),
    "AFFECTION": (
        EyeStep(Expression.SHY, 900, gaze_dx=-3, gaze_dy=2),
        EyeStep(Expression.LOVE, 1600, gaze_dx=0, gaze_dy=0),
    ),
    "MISCHIEVOUS_PLAY": (
        EyeStep(Expression.MISCHIEVOUS, 1200, gaze_dx=5, gaze_dy=-2),
        EyeStep(Expression.WINK, 650),
    ),
    "WAKE_UP": (
        EyeStep(Expression.SLEEPY, 600, trigger_blink=True),
        EyeStep(Expression.CURIOUS, 800, gaze_dx=0, gaze_dy=-1),
    ),
}


class EyeEngine2:
    """Orchestrates hardware-safe expression sequences and contextual looks."""

    def __init__(self) -> None:
        self._active_sequence: List[EyeStep] = []
        self._step_started_ms: int = 0
        self._current_expr: Expression = Expression.IDLE

    @property
    def is_sequence_active(self) -> bool:
        return len(self._active_sequence) > 0

    def start_sequence(self, name: str, now_ms: int) -> Optional[EyeStep]:
        steps = BUILTIN_SEQUENCES.get(name)
        if not steps:
            return None
        self._active_sequence = list(steps)
        self._step_started_ms = now_ms
        first = self._active_sequence[0]
        self._current_expr = first.expression
        return first

    def cancel_sequence(self) -> None:
        self._active_sequence.clear()

    def tick(self, now_ms: int) -> Optional[EyeStep]:
        """Advance active sequence; returns the new EyeStep when transitioning."""
        if not self._active_sequence:
            return None
        current = self._active_sequence[0]
        if (now_ms - self._step_started_ms) < current.duration_ms:
            return None
        self._active_sequence.pop(0)
        if not self._active_sequence:
            return None
        self._step_started_ms = now_ms
        nxt = self._active_sequence[0]
        self._current_expr = nxt.expression
        return nxt

    @staticmethod
    def contextual_look_for_mode(mode: str) -> Optional[Tuple[int, int]]:
        """Return safe firmware LOOK coordinates for conversation/idle contexts."""
        mapping: Dict[str, Tuple[int, int]] = {
            "LISTENING": (0, 0),
            "THINKING": (6, -3),
            "SPEAKING": (0, 0),
            "SLEEPING": (0, 2),
        }
        coords = mapping.get(mode.upper())
        if coords is None:
            return None
        return clamp_firmware_look(coords[0], coords[1])

    @staticmethod
    def capabilities_summary() -> Dict[str, object]:
        """Explicitly distinguish hardware-compatible vs simulator-only features."""
        return {
            "expressions_count": len(ALL_14_EXPRESSIONS),
            "hardware_compatible": [
                "STATE:<14 expressions>",
                "LOOK:dx,dy (dx:-11..11, dy:-6..6)",
                "BLINK",
                "AUTO:ON/OFF",
                "Timed Python-driven expression sequences",
            ],
            "simulator_only": [
                "Sub-frame procedural interpolation preview",
                "In-app telemetry & Sensor Lab overlay",
            ],
        }
