"""Animated eye engine & companion state machine for Windows 11 Simulator (v2 Organic).

Attribution:
    Non-blocking blinker, eyelid masking concept, and idle gaze architecture
    originally inspired by Carmoruda/Jarvis (MIT License, Copyright (c) 2026
    Carmoruda). 1:1 mirror of 04-Firmware/jarvis-desk-buddy/src/eye_engine.cpp
    with organic super-capsule geometry, curved eyelids, FPS-independent
    exponential interpolation, and deterministic xorshift32 PRNG.
"""

from dataclasses import dataclass
from enum import Enum
import math
import time
from typing import Optional

from monochrome_fb import HEIGHT, WIDTH, MonochromeFramebuffer


class VisualProfile(str, Enum):
    CALM = "CALM"
    LIVELY = "LIVELY"
    PLAYFUL = "PLAYFUL"


class MicroExprType(str, Enum):
    NONE = "NONE"
    BROW_RAISE = "BROW_RAISE"
    SIDE_GLANCE = "SIDE_GLANCE"
    QUICK_WINK = "QUICK_WINK"
    EYE_SMILE = "EYE_SMILE"
    PUPIL_PULSE = "PUPIL_PULSE"


class Expression(str, Enum):
    IDLE = "IDLE"
    HAPPY = "HAPPY"
    CURIOUS = "CURIOUS"
    SLEEPY = "SLEEPY"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    SURPRISED = "SURPRISED"
    SHY = "SHY"
    LOVE = "LOVE"
    WINK = "WINK"
    CONFUSED = "CONFUSED"
    MISCHIEVOUS = "MISCHIEVOUS"
    SLEEPING = "SLEEPING"


CORE_EXPRESSIONS = [
    Expression.IDLE,
    Expression.HAPPY,
    Expression.CURIOUS,
    Expression.SLEEPY,
    Expression.LISTENING,
    Expression.THINKING,
    Expression.SPEAKING,
]

ALL_EXPRESSIONS = CORE_EXPRESSIONS + [
    Expression.SURPRISED,
    Expression.SHY,
    Expression.LOVE,
    Expression.WINK,
    Expression.CONFUSED,
    Expression.MISCHIEVOUS,
    Expression.SLEEPING,
]


def _clamp_int(val: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, val))


def _clamp_float(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def _round_half_away(val: float) -> int:
    return int(math.floor(val + 0.5)) if val >= 0.0 else -int(math.floor(-val + 0.5))


def _smooth_exp(current: float, target: float, rate: float, dt_sec: float) -> float:
    diff = target - current
    if abs(diff) < 0.05:
        return target
    alpha = 1.0 - math.exp(-rate * dt_sec)
    return current + diff * alpha


@dataclass
class EyeState:
    base_x: int = 0
    base_y: int = 0
    x: float = 0.0
    y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0

    width: float = 38.0
    height: float = 38.0
    target_width: float = 38.0
    target_height: float = 38.0

    corner_radius: float = 13.0
    target_corner_radius: float = 13.0

    shape_power: float = 3.1
    target_shape_power: float = 3.1
    taper: float = 0.08
    target_taper: float = 0.08

    lower_lid: float = 0.0
    target_lower_lid: float = 0.0
    lower_arch: float = 0.0
    target_lower_arch: float = 0.0

    upper_lid_l: float = 0.0
    upper_lid_r: float = 0.0
    target_upper_lid_l: float = 0.0
    target_upper_lid_r: float = 0.0
    upper_arch: float = 0.0
    target_upper_arch: float = 0.0
    pupil_dx: float = 0.0
    pupil_dy: float = 0.0
    target_pupil_dx: float = 0.0
    target_pupil_dy: float = 0.0
    pupil_radius: float = 7.5
    target_pupil_radius: float = 7.5
    brow_offset: float = 0.0
    target_brow_offset: float = 0.0
    brow_tilt: float = 0.0
    target_brow_tilt: float = 0.0
    brow_arch: float = 2.0
    target_brow_arch: float = 2.0

    blink_squeeze: float = 0.0


class EyeEngine:
    DEFAULT_EYE_WIDTH = 38
    DEFAULT_EYE_HEIGHT = 38
    DEFAULT_CORNER_RADIUS = 13

    def __init__(self, fps: int = 50, spacing_px: int = 12, seed: int = 0xA511E9B3) -> None:
        self.fb = MonochromeFramebuffer()
        self.left = EyeState()
        self.right = EyeState()
        self.expr = Expression.IDLE
        self.spacing_px = spacing_px
        self.frame_interval_ms = (1000 // fps) if fps > 0 else 20
        self.last_frame_ms = 0
        self.last_render_us = 0
        self.actual_fps = float(fps) if fps > 0 else 30.0
        self.dropped_frames = 0

        self.profile = VisualProfile.LIVELY

        self.blink_phase = "OPEN"
        self.next_blink_ms = 2200
        self.blink_hold_until_ms = 0
        self.double_blink_pending = False

        self.auto_idle_gaze = True
        self.next_gaze_ms = 2400
        self.gaze_override_until_ms = 0
        self.gaze_is_micro = False

        self.micro_expressions_enabled = True
        self.micro_expr = MicroExprType.NONE
        self.micro_expr_until_ms = 0
        self.next_micro_expr_ms = 3800
        self.transition_boost = 1.0

        self.expr_start_ms = 0

        self._rng_state = seed & 0xFFFFFFFF or 0xA511E9B3

        self._recalculate_base_positions()
        self._apply_expression_targets()
        self.render_frame(0)

    def set_visual_profile(self, profile: VisualProfile | str) -> None:
        if isinstance(profile, str):
            profile = VisualProfile(profile.strip().upper())
        self.profile = profile

    def get_visual_profile(self) -> VisualProfile:
        return self.profile

    def set_micro_expressions_enabled(self, enabled: bool) -> None:
        self.micro_expressions_enabled = bool(enabled)

    def _profile_speed_scale(self) -> float:
        if self.profile == VisualProfile.CALM:
            return 0.72
        if self.profile == VisualProfile.PLAYFUL:
            return 1.22
        return 1.00

    def _profile_gaze_freq_scale(self) -> float:
        if self.profile == VisualProfile.CALM:
            return 0.65
        if self.profile == VisualProfile.PLAYFUL:
            return 1.35
        return 1.00

    def _profile_micro_freq_scale(self) -> float:
        if self.profile == VisualProfile.CALM:
            return 0.45
        if self.profile == VisualProfile.PLAYFUL:
            return 1.65
        return 1.00

    def _profile_blink_freq_scale(self) -> float:
        if self.profile == VisualProfile.CALM:
            return 0.80
        if self.profile == VisualProfile.PLAYFUL:
            return 1.15
        return 1.00

    def seed_rng(self, seed: int) -> None:
        self._rng_state = (seed & 0xFFFFFFFF) or 0xA511E9B3

    def _next_rand(self) -> int:
        x = self._rng_state
        x = (x ^ ((x << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
        x = (x ^ (x >> 17)) & 0xFFFFFFFF
        x = (x ^ ((x << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
        self._rng_state = x
        return x

    def _rand_range(self, lo: int, hi: int) -> int:
        if hi <= lo:
            return lo
        span = hi - lo + 1
        return lo + (self._next_rand() % span)

    def _recalculate_base_positions(self) -> None:
        total_w = self.DEFAULT_EYE_WIDTH + self.spacing_px + self.DEFAULT_EYE_WIDTH
        start_x = (WIDTH - total_w) // 2
        self.left.base_x = start_x + self.DEFAULT_EYE_WIDTH // 2
        self.right.base_x = start_x + self.DEFAULT_EYE_WIDTH + self.spacing_px + self.DEFAULT_EYE_WIDTH // 2
        self.left.base_y = HEIGHT // 2 + 2
        self.right.base_y = HEIGHT // 2 + 2

        self.left.x = self.left.target_x = float(self.left.base_x)
        self.right.x = self.right.target_x = float(self.right.base_x)
        self.left.y = self.left.target_y = float(self.left.base_y)
        self.right.y = self.right.target_y = float(self.right.base_y)

    def set_expression(self, expr: Expression, now_ms: int = 0) -> None:
        if self.expr == expr:
            return
        self.expr = expr
        self.expr_start_ms = now_ms
        self.micro_expr = MicroExprType.NONE
        self.transition_boost = 1.85 if expr == Expression.SURPRISED else 1.05
        self._apply_expression_targets()

    def _apply_expression_targets(self) -> None:
        for eye in (self.left, self.right):
            eye.target_width = float(self.DEFAULT_EYE_WIDTH)
            eye.target_height = float(self.DEFAULT_EYE_HEIGHT)
            eye.target_corner_radius = float(self.DEFAULT_CORNER_RADIUS)
            eye.target_shape_power = 3.1
            eye.target_taper = 0.08
            eye.target_lower_lid = 0.0
            eye.target_lower_arch = 0.0
            eye.target_upper_lid_l = 0.0
            eye.target_upper_lid_r = 0.0
            eye.target_upper_arch = 0.0
            eye.target_pupil_dx = 0.0
            eye.target_pupil_dy = 0.0
            eye.target_pupil_radius = 7.5
            eye.target_brow_offset = 0.0
            eye.target_brow_tilt = 0.0
            eye.target_brow_arch = 2.0
            eye.target_x = float(eye.base_x)
            eye.target_y = float(eye.base_y)

        if self.expr == Expression.IDLE:
            pass
        elif self.expr == Expression.HAPPY:
            self.left.target_width = self.right.target_width = 38.0
            self.left.target_height = self.right.target_height = 34.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 0.0
            self.left.target_y = self.right.target_y = float(self.left.base_y)
        elif self.expr == Expression.CURIOUS:
            self.left.target_width = 31.0
            self.left.target_height = 29.0
            self.left.target_shape_power = 2.8
            self.left.target_taper = 0.05
            self.left.target_upper_lid_l = 1.0
            self.left.target_upper_lid_r = 5.0
            self.left.target_pupil_dx = 3.0
            self.left.target_pupil_radius = 6.5
            self.left.target_brow_offset = 4.0
            self.left.target_brow_tilt = 2.5
            self.left.target_brow_arch = 1.5
            self.left.target_x = float(self.left.base_x + 3)
            self.left.target_y = float(self.left.base_y + 3)

            self.right.target_width = 41.0
            self.right.target_height = 42.0
            self.right.target_shape_power = 2.5
            self.right.target_taper = 0.11
            self.right.target_pupil_dx = 3.0
            self.right.target_pupil_dy = -1.5
            self.right.target_pupil_radius = 8.0
            self.right.target_brow_offset = 5.0
            self.right.target_brow_tilt = -2.0
            self.right.target_brow_arch = 3.5
            self.right.target_x = float(self.right.base_x + 3)
            self.right.target_y = float(self.right.base_y - 2)
        elif self.expr == Expression.SLEEPY:
            self.left.target_width = self.right.target_width = 36.0
            self.left.target_height = self.right.target_height = 30.0
            self.left.target_shape_power = self.right.target_shape_power = 3.3
            self.left.target_taper = self.right.target_taper = -0.04
            self.left.target_upper_lid_l = self.left.target_upper_lid_r = 14.0
            self.right.target_upper_lid_l = self.right.target_upper_lid_r = 14.0
            self.left.target_upper_arch = self.right.target_upper_arch = 3.5
            self.left.target_pupil_radius = self.right.target_pupil_radius = 5.0
            self.left.target_pupil_dy = self.right.target_pupil_dy = 3.0
            self.left.target_y = self.right.target_y = float(self.left.base_y + 4)
        elif self.expr == Expression.LISTENING:
            self.left.target_width = self.right.target_width = 39.0
            self.left.target_height = self.right.target_height = 41.0
            self.left.target_shape_power = self.right.target_shape_power = 2.8
            self.left.target_taper = self.right.target_taper = 0.10
            self.left.target_pupil_radius = self.right.target_pupil_radius = 8.5
            self.left.target_y = self.right.target_y = float(self.left.base_y - 1)
        elif self.expr == Expression.THINKING:
            self.left.target_width = self.right.target_width = 35.0
            self.left.target_height = self.right.target_height = 32.0
            self.left.target_shape_power = self.right.target_shape_power = 3.1
            self.left.target_taper = self.right.target_taper = 0.05
            self.left.target_x = float(self.left.base_x + 5)
            self.right.target_x = float(self.right.base_x + 5)
            self.left.target_y = float(self.left.base_y - 4)
            self.right.target_y = float(self.right.base_y - 4)
            self.left.target_upper_lid_l = 4.0
            self.left.target_upper_lid_r = 2.0
            self.right.target_lower_lid = 3.0
            self.right.target_lower_arch = 3.0
            self.left.target_pupil_dx = self.right.target_pupil_dx = 5.0
            self.left.target_pupil_dy = self.right.target_pupil_dy = -3.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 6.0
            self.left.target_brow_offset = 4.0
            self.left.target_brow_tilt = 2.5
            self.right.target_brow_offset = 5.0
            self.right.target_brow_tilt = -1.5
            self.right.target_brow_arch = 3.0
        elif self.expr == Expression.SPEAKING:
            self.left.target_width = self.right.target_width = 38.0
            self.left.target_height = self.right.target_height = 36.0
            self.left.target_shape_power = self.right.target_shape_power = 3.0
            self.left.target_taper = self.right.target_taper = 0.08
            self.left.target_lower_lid = self.right.target_lower_lid = 3.0
            self.left.target_lower_arch = self.right.target_lower_arch = 6.5
            self.left.target_pupil_radius = self.right.target_pupil_radius = 7.0
        elif self.expr == Expression.SURPRISED:
            self.left.target_width = self.right.target_width = 41.0
            self.left.target_height = self.right.target_height = 44.0
            self.left.target_shape_power = self.right.target_shape_power = 2.1
            self.left.target_taper = self.right.target_taper = 0.12
            self.left.target_pupil_radius = self.right.target_pupil_radius = 4.5
            self.left.target_brow_offset = self.right.target_brow_offset = 4.0
            self.left.target_brow_arch = self.right.target_brow_arch = 3.5
            self.left.target_y = self.right.target_y = float(self.left.base_y - 1)
        elif self.expr == Expression.SHY:
            self.left.target_width = self.right.target_width = 34.0
            self.left.target_height = self.right.target_height = 29.0
            self.left.target_shape_power = self.right.target_shape_power = 2.7
            self.left.target_taper = self.right.target_taper = -0.06
            self.left.target_upper_lid_l = self.left.target_upper_lid_r = 6.0
            self.right.target_upper_lid_l = self.right.target_upper_lid_r = 6.0
            self.left.target_pupil_dx = self.right.target_pupil_dx = -4.0
            self.left.target_pupil_dy = self.right.target_pupil_dy = 2.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 6.0
            self.left.target_brow_offset = self.right.target_brow_offset = 4.0
            self.left.target_brow_tilt = -2.5
            self.right.target_brow_tilt = 2.5
            self.left.target_x = float(self.left.base_x - 3)
            self.right.target_x = float(self.right.base_x - 3)
            self.left.target_y = self.right.target_y = float(self.left.base_y + 4)
        elif self.expr == Expression.LOVE:
            self.left.target_width = self.right.target_width = 34.0
            self.left.target_height = self.right.target_height = 34.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 0.0
            self.left.target_y = self.right.target_y = float(self.left.base_y - 1)
        elif self.expr == Expression.WINK:
            self.left.target_width = 38.0
            self.left.target_height = 39.0
            self.left.target_shape_power = 2.9
            self.left.target_taper = 0.10
            self.left.target_pupil_radius = 7.5
            self.left.target_brow_offset = 4.0
            self.left.target_brow_arch = 2.5
            self.left.target_y = float(self.left.base_y - 1)
            self.right.target_width = 38.0
            self.right.target_height = 32.0
            self.right.target_pupil_radius = 0.0
            self.right.target_y = float(self.right.base_y + 1)
        elif self.expr == Expression.CONFUSED:
            self.left.target_width = 31.0
            self.left.target_height = 28.0
            self.left.target_shape_power = 3.2
            self.left.target_taper = 0.02
            self.left.target_upper_lid_l = 6.0
            self.left.target_upper_lid_r = 2.0
            self.left.target_pupil_dx = -2.0
            self.left.target_pupil_radius = 5.5
            self.left.target_brow_offset = 4.0
            self.left.target_brow_tilt = 3.0
            self.left.target_brow_arch = 1.0
            self.left.target_y = float(self.left.base_y + 3)
            self.right.target_width = 39.0
            self.right.target_height = 41.0
            self.right.target_shape_power = 2.6
            self.right.target_taper = 0.10
            self.right.target_pupil_dx = 2.0
            self.right.target_pupil_dy = -1.5
            self.right.target_pupil_radius = 7.5
            self.right.target_brow_offset = 5.0
            self.right.target_brow_tilt = -3.0
            self.right.target_brow_arch = 3.5
            self.right.target_y = float(self.right.base_y - 2)
        elif self.expr == Expression.MISCHIEVOUS:
            self.left.target_width = self.right.target_width = 38.0
            self.left.target_height = self.right.target_height = 33.0
            self.left.target_shape_power = self.right.target_shape_power = 3.2
            self.left.target_taper = self.right.target_taper = 0.08
            self.left.target_upper_lid_l = 1.0
            self.left.target_upper_lid_r = 9.0
            self.right.target_upper_lid_l = 9.0
            self.right.target_upper_lid_r = 1.0
            self.left.target_lower_lid = self.right.target_lower_lid = 4.0
            self.left.target_lower_arch = self.right.target_lower_arch = 6.0
            self.left.target_pupil_dx = self.right.target_pupil_dx = 5.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 6.0
            self.left.target_brow_offset = self.right.target_brow_offset = 4.0
            self.left.target_brow_tilt = 3.5
            self.right.target_brow_tilt = -3.5
            self.left.target_brow_arch = self.right.target_brow_arch = 1.0
            self.left.target_x = float(self.left.base_x + 4)
            self.right.target_x = float(self.right.base_x + 4)
        elif self.expr == Expression.SLEEPING:
            self.left.target_width = self.right.target_width = 36.0
            self.left.target_height = self.right.target_height = 28.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 0.0
            self.left.target_y = self.right.target_y = float(self.left.base_y + 3)

    def trigger_blink(self, now_ms: int) -> None:
        if self.blink_phase == "OPEN":
            self.blink_phase = "CLOSING"
            self.next_blink_ms = now_ms + 3200

    def set_gaze_offset(self, dx: int, dy: int, hold_ms: int, now_ms: int) -> None:
        dx = _clamp_int(dx, -11, 11)
        dy = _clamp_int(dy, -6, 6)
        self.micro_expr = MicroExprType.NONE
        self.gaze_is_micro = False
        self.left.target_x = float(self.left.base_x) + float(dx) * 0.45
        self.right.target_x = float(self.right.base_x) + float(dx) * 0.45
        self.left.target_y = float(self.left.base_y) + float(dy) * 0.40
        self.right.target_y = float(self.right.base_y) + float(dy) * 0.40
        self.left.target_pupil_dx = self.right.target_pupil_dx = float(dx) * 0.55
        self.left.target_pupil_dy = self.right.target_pupil_dy = float(dy) * 0.45
        self.gaze_override_until_ms = now_ms + hold_ms

    def _update_blinker(self, now_ms: int, dt_sec: float) -> None:
        if self.expr in (Expression.HAPPY, Expression.WINK, Expression.SLEEPING):
            self.blink_phase = "OPEN"
            self.left.blink_squeeze = 0.0
            self.right.blink_squeeze = 0.0
            return

        speed = self._profile_speed_scale()
        if self.expr == Expression.SLEEPY:
            close_rate = 6.0 * speed
            open_rate = 4.2 * speed
        elif self.expr == Expression.SURPRISED:
            close_rate = 24.0 * speed
            open_rate = 18.0 * speed
        else:
            close_rate = 18.0 * speed
            open_rate = 14.0 * speed

        if self.blink_phase == "OPEN":
            if now_ms >= self.next_blink_ms:
                self.blink_phase = "CLOSING"
                if self.expr in (Expression.IDLE, Expression.HAPPY) and not self.double_blink_pending:
                    dbl_chance = 28 if self.profile == VisualProfile.PLAYFUL else (8 if self.profile == VisualProfile.CALM else 20)
                    self.double_blink_pending = self._rand_range(0, 99) < dbl_chance
        elif self.blink_phase == "CLOSING":
            self.left.blink_squeeze += close_rate * dt_sec
            self.right.blink_squeeze += close_rate * dt_sec
            if self.left.blink_squeeze >= 1.0:
                self.left.blink_squeeze = self.right.blink_squeeze = 1.0
                self.blink_phase = "HOLD_CLOSED"
                self.blink_hold_until_ms = now_ms + (130 if self.expr == Expression.SLEEPY else 42)
        elif self.blink_phase == "HOLD_CLOSED":
            if now_ms >= self.blink_hold_until_ms:
                self.blink_phase = "OPENING"
        elif self.blink_phase == "OPENING":
            ease = 0.45 + 0.55 * self.left.blink_squeeze
            self.left.blink_squeeze -= open_rate * ease * dt_sec
            self.right.blink_squeeze -= open_rate * ease * dt_sec
            if self.left.blink_squeeze <= 0.0:
                self.left.blink_squeeze = self.right.blink_squeeze = 0.0
                self.blink_phase = "OPEN"
                if self.double_blink_pending:
                    self.double_blink_pending = False
                    self.next_blink_ms = now_ms + 130
                else:
                    lo, hi = (1900, 3600) if self.expr == Expression.SLEEPY else (2500, 5400)
                    wait_ms = int(self._rand_range(lo, hi) / self._profile_blink_freq_scale())
                    self.next_blink_ms = now_ms + _clamp_int(wait_ms, 1200, 8000)

    def _update_gaze(self, now_ms: int) -> None:
        if not self.auto_idle_gaze:
            return
        if now_ms < self.gaze_override_until_ms:
            return
        if self.expr in (
            Expression.THINKING,
            Expression.CURIOUS,
            Expression.SURPRISED,
            Expression.SHY,
            Expression.LOVE,
            Expression.WINK,
            Expression.CONFUSED,
            Expression.MISCHIEVOUS,
            Expression.SLEEPING,
        ):
            return
        if now_ms < self.next_gaze_ms:
            return

        if self.expr == Expression.LISTENING:
            micro = self._rand_range(0, 99) < 35
            pdx = self._rand_range(-1, 1) if micro else 0
            pdy = self._rand_range(-1, 0) if micro else 0
            self.left.target_x = float(self.left.base_x)
            self.right.target_x = float(self.right.base_x)
            self.left.target_y = float(self.left.base_y)
            self.right.target_y = float(self.right.base_y)
            self.left.target_pupil_dx = self.right.target_pupil_dx = float(pdx)
            self.left.target_pupil_dy = self.right.target_pupil_dy = float(pdy)
            self.gaze_is_micro = micro
            self.next_gaze_ms = now_ms + self._rand_range(1400, 2800)
            return

        roll = self._rand_range(0, 99)
        return_center = roll < 38
        do_micro = (not return_center) and (roll < 70)
        dx = 0
        dy = 0
        if do_micro:
            dx = self._rand_range(-3, 3)
            dy = self._rand_range(-2, 2)
            self.gaze_is_micro = True
        elif not return_center:
            max_dx = 3 if self.expr == Expression.SLEEPY else 9
            max_dy = 2 if self.expr == Expression.SLEEPY else 4
            dx = self._rand_range(-max_dx, max_dx)
            dy = self._rand_range(-max_dy, max_dy)
            self.gaze_is_micro = False
        else:
            self.gaze_is_micro = False

        y_bias = -1 if self.expr == Expression.HAPPY else (4 if self.expr == Expression.SLEEPY else 0)
        self.left.target_x = float(self.left.base_x) + float(dx) * 0.45
        self.right.target_x = float(self.right.base_x) + float(dx) * 0.45
        self.left.target_y = float(self.left.base_y + y_bias) + float(dy) * 0.40
        self.right.target_y = float(self.right.base_y + y_bias) + float(dy) * 0.40
        self.left.target_pupil_dx = self.right.target_pupil_dx = float(dx) * 0.55
        self.left.target_pupil_dy = self.right.target_pupil_dy = float(dy) * 0.45

        base_wait = self._rand_range(650, 1300) if self.gaze_is_micro else self._rand_range(1600, 3600)
        scaled_wait = int(base_wait / self._profile_gaze_freq_scale())
        self.next_gaze_ms = now_ms + _clamp_int(scaled_wait, 500, 6000)

    def _update_micro_expressions(self, now_ms: int) -> None:
        if self.micro_expr != MicroExprType.NONE and now_ms >= self.micro_expr_until_ms:
            self.micro_expr = MicroExprType.NONE
            self._apply_expression_targets()

        if not self.micro_expressions_enabled:
            return
        if now_ms < self.gaze_override_until_ms or self.blink_phase != "OPEN":
            return
        if self.expr in (Expression.SLEEPING, Expression.LOVE, Expression.SURPRISED, Expression.WINK):
            return

        if self.micro_expr == MicroExprType.NONE and now_ms >= self.next_micro_expr_ms:
            if self.expr == Expression.LISTENING and self._rand_range(0, 99) < 65:
                self.next_micro_expr_ms = now_ms + 3000
                return

            r = self._rand_range(0, 99)
            if r < 28:
                self.micro_expr = MicroExprType.BROW_RAISE
                self.right.target_brow_offset += 3.0
                self.right.target_brow_tilt -= 1.5
                self.micro_expr_until_ms = now_ms + 520
            elif r < 54:
                self.micro_expr = MicroExprType.SIDE_GLANCE
                direction = -3.5 if self._rand_range(0, 1) == 0 else 3.5
                self.left.target_pupil_dx += direction
                self.right.target_pupil_dx += direction
                self.micro_expr_until_ms = now_ms + 460
            elif r < 74:
                self.micro_expr = MicroExprType.EYE_SMILE
                self.left.target_lower_lid += 2.5
                self.right.target_lower_lid += 2.5
                self.left.target_lower_arch += 3.0
                self.right.target_lower_arch += 3.0
                self.micro_expr_until_ms = now_ms + 580
            elif r < 90:
                self.micro_expr = MicroExprType.PUPIL_PULSE
                self.left.target_pupil_radius += 1.0
                self.right.target_pupil_radius += 1.0
                self.micro_expr_until_ms = now_ms + 420
            else:
                wink_thresh = 100 if self.profile == VisualProfile.PLAYFUL else (0 if self.profile == VisualProfile.CALM else 50)
                if self._rand_range(0, 99) < wink_thresh:
                    self.micro_expr = MicroExprType.QUICK_WINK
                    self.right.target_upper_lid_l += 9.0
                    self.right.target_upper_lid_r += 9.0
                    self.micro_expr_until_ms = now_ms + 300

            next_ms = int(self._rand_range(3600, 7400) / self._profile_micro_freq_scale())
            self.next_micro_expr_ms = now_ms + _clamp_int(next_ms, 1800, 14000)

    def _update_expression_motion(self, now_ms: int) -> None:
        t_sec = (now_ms - self.expr_start_ms) * 0.001
        if self.expr == Expression.IDLE:
            breath = math.sin(t_sec * 1.4)
            self.left.target_height = self.right.target_height = 32.0 + 0.8 * breath
        elif self.expr == Expression.HAPPY:
            bounce = math.sin(t_sec * 3.5) * 1.2
            self.left.target_y = self.right.target_y = float(self.left.base_y - 2) + bounce
        elif self.expr == Expression.CURIOUS:
            drift = math.sin(t_sec * 1.9) * 2.0
            self.left.target_x = float(self.left.base_x + 4) + drift
            self.right.target_x = float(self.right.base_x + 4) + drift
        elif self.expr == Expression.SLEEPY:
            drowse = math.sin(t_sec * 1.1) * 1.5
            self.left.target_upper_lid_l = self.left.target_upper_lid_r = 12.0 + drowse
            self.right.target_upper_lid_l = self.right.target_upper_lid_r = 12.0 + drowse
        elif self.expr == Expression.LISTENING:
            breath = math.sin(t_sec * 3.0)
            self.left.target_height = self.right.target_height = 35.5 + 1.2 * breath
        elif self.expr == Expression.THINKING:
            scan = 2.5 * math.sin(t_sec * 1.7) + 1.2 * math.sin(t_sec * 2.9)
            self.left.target_x = float(self.left.base_x + 7) + scan
            self.right.target_x = float(self.right.base_x + 7) + scan
        elif self.expr == Expression.SPEAKING:
            env = _clamp_float(
                0.5 + 0.32 * math.sin(t_sec * 6.8) + 0.18 * math.sin(t_sec * 10.7),
                0.0,
                1.0,
            )
            self.left.target_height = self.right.target_height = 27.0 + 6.0 * env
            self.left.target_lower_lid = self.right.target_lower_lid = 2.0 + 3.5 * (1.0 - env)
            self.left.target_lower_arch = self.right.target_lower_arch = 4.0 + 2.5 * (1.0 - env)
        elif self.expr == Expression.SURPRISED:
            pulse = math.sin(t_sec * 5.0) * 1.0
            self.left.target_width = self.right.target_width = 34.0 + pulse
            self.left.target_height = self.right.target_height = 38.0 + pulse
        elif self.expr == Expression.SHY:
            sway = math.sin(t_sec * 1.6) * 1.5
            self.left.target_x = float(self.left.base_x - 3) + sway
            self.right.target_x = float(self.right.base_x - 3) + sway
        elif self.expr == Expression.LOVE:
            beat = abs(math.sin(t_sec * 3.8)) * 1.8
            self.left.target_y = self.right.target_y = float(self.left.base_y - 1) - beat
        elif self.expr == Expression.WINK:
            self.left.target_y = float(self.left.base_y - 1) + math.sin(t_sec * 2.8) * 0.8
        elif self.expr == Expression.CONFUSED:
            tilt = math.sin(t_sec * 2.2) * 1.5
            self.left.target_x = float(self.left.base_x + 2) + tilt
            self.right.target_x = float(self.right.base_x + 2) + tilt
        elif self.expr == Expression.MISCHIEVOUS:
            sly = math.sin(t_sec * 2.1) * 2.0
            self.left.target_x = float(self.left.base_x + 5) + sly
            self.right.target_x = float(self.right.base_x + 5) + sly
        elif self.expr == Expression.SLEEPING:
            breathe = math.sin(t_sec * 0.9) * 1.0
            self.left.target_y = self.right.target_y = float(self.left.base_y + 3) + breathe

    def _interpolate_eye(self, eye: EyeState, dt_sec: float) -> None:
        mult = self._profile_speed_scale() * self.transition_boost
        eye.x = _smooth_exp(eye.x, eye.target_x, 12.0 * mult, dt_sec)
        eye.y = _smooth_exp(eye.y, eye.target_y, 12.0 * mult, dt_sec)
        eye.width = _smooth_exp(eye.width, eye.target_width, 10.0 * mult, dt_sec)
        eye.height = _smooth_exp(eye.height, eye.target_height, 10.0 * mult, dt_sec)
        eye.corner_radius = _smooth_exp(eye.corner_radius, eye.target_corner_radius, 10.0 * mult, dt_sec)
        eye.lower_lid = _smooth_exp(eye.lower_lid, eye.target_lower_lid, 12.0 * mult, dt_sec)
        eye.lower_arch = _smooth_exp(eye.lower_arch, eye.target_lower_arch, 12.0 * mult, dt_sec)
        eye.upper_lid_l = _smooth_exp(eye.upper_lid_l, eye.target_upper_lid_l, 12.0 * mult, dt_sec)
        eye.upper_lid_r = _smooth_exp(eye.upper_lid_r, eye.target_upper_lid_r, 12.0 * mult, dt_sec)
        eye.upper_arch = _smooth_exp(eye.upper_arch, eye.target_upper_arch, 12.0 * mult, dt_sec)
        eye.pupil_dx = _smooth_exp(eye.pupil_dx, eye.target_pupil_dx, 14.0 * mult, dt_sec)
        eye.pupil_dy = _smooth_exp(eye.pupil_dy, eye.target_pupil_dy, 14.0 * mult, dt_sec)
        eye.pupil_radius = _smooth_exp(eye.pupil_radius, eye.target_pupil_radius, 12.0 * mult, dt_sec)
        eye.brow_offset = _smooth_exp(eye.brow_offset, eye.target_brow_offset, 12.0 * mult, dt_sec)
        eye.brow_tilt = _smooth_exp(eye.brow_tilt, eye.target_brow_tilt, 12.0 * mult, dt_sec)
        eye.brow_arch = _smooth_exp(eye.brow_arch, eye.target_brow_arch, 12.0 * mult, dt_sec)
        eye.shape_power = _smooth_exp(eye.shape_power, eye.target_shape_power, 10.0 * mult, dt_sec)
        eye.taper = _smooth_exp(eye.taper, eye.target_taper, 10.0 * mult, dt_sec)

    def update(self, now_ms: int, force: bool = False) -> bool:
        elapsed = now_ms - self.last_frame_ms
        if not force and elapsed < self.frame_interval_ms:
            return False
        if not force and elapsed >= self.frame_interval_ms * 2 and elapsed < 2000:
            self.dropped_frames += (elapsed // self.frame_interval_ms) - 1
        self.update_step(now_ms)
        return True

    def update_step(self, now_ms: int) -> None:
        dt_ms = (now_ms - self.last_frame_ms) if now_ms >= self.last_frame_ms else self.frame_interval_ms
        dt_ms = _clamp_int(dt_ms, 1, 100)
        dt_sec = dt_ms * 0.001
        self.actual_fps = self.actual_fps * 0.85 + (1000.0 / float(dt_ms)) * 0.15
        self.last_frame_ms = now_ms

        self._update_blinker(now_ms, dt_sec)
        self._update_gaze(now_ms)
        self._update_micro_expressions(now_ms)
        self._update_expression_motion(now_ms)
        self._interpolate_eye(self.left, dt_sec)
        self._interpolate_eye(self.right, dt_sec)
        self.transition_boost = _smooth_exp(self.transition_boost, 1.0, 6.0, dt_sec)
        t0 = time.perf_counter_ns()
        self.render_frame(now_ms)
        self.last_render_us = (time.perf_counter_ns() - t0) // 1000

    def _draw_single_eye(self, eye: EyeState) -> None:
        w = _clamp_int(_round_half_away(eye.width), 12, 46)
        raw_h = _clamp_int(_round_half_away(eye.height), 10, 48)

        if eye.blink_squeeze >= 0.85:
            cx = _clamp_int(_round_half_away(eye.x), w // 2 + 4, WIDTH - w // 2 - 4)
            cy = _clamp_int(_round_half_away(eye.y) + 2, 6, HEIGHT - 6)
            for dx in range(-w // 2, w // 2 + 1):
                u = dx / float(max(1, w // 2))
                sag = _round_half_away(1.5 * (1.0 - u * u))
                self.fb.set_pixel(cx + dx, cy + sag, 1)
                self.fb.set_pixel(cx + dx, cy + sag + 1, 1)
            return

        h = _clamp_int(_round_half_away(raw_h * (1.0 - 0.88 * eye.blink_squeeze)), 4, 48)
        cx = _clamp_int(_round_half_away(eye.x), w // 2 + 4, WIDTH - w // 2 - 4)
        cy = _clamp_int(_round_half_away(eye.y), h // 2 + 6, HEIGHT - h // 2 - 5)
        rx = w * 0.5
        ry = h * 0.5
        p = max(2.0, eye.shape_power)

        # Organic superellipse + vertical taper
        for dy in range(-h // 2, h // 2 + 1):
            v = dy / ry if ry > 0 else 0.0
            av = min(1.0, abs(v))
            taper_scale = 1.0 - eye.taper * v
            span_x = rx * taper_scale * ((max(0.0, 1.0 - (av ** p))) ** (1.0 / p))
            half_x = int(math.floor(span_x))
            py = cy + dy
            if 4 <= py <= HEIGHT - 5:
                for dx in range(-half_x, half_x + 1):
                    px = cx + dx
                    if 4 <= px <= WIDTH - 5:
                        self.fb.set_pixel(px, py, 1)

        x = cx - w // 2
        y = cy - h // 2

        if eye.blink_squeeze < 0.65:
            half_w = (w - 1) * 0.5
            if eye.lower_lid > 0.4 or eye.lower_arch > 0.4:
                for col in range(w):
                    u = ((col - half_w) / half_w) if half_w > 0.0 else 0.0
                    curve = 1.0 - u * u
                    mask_top = _round_half_away((y + h) - eye.lower_lid - eye.lower_arch * curve)
                    for py in range(mask_top, y + h + 2):
                        self.fb.set_pixel(x + col, py, 0)

            if eye.upper_lid_l > 0.4 or eye.upper_lid_r > 0.4 or eye.upper_arch > 0.4:
                max_ul = max(eye.upper_lid_l, eye.upper_lid_r)
                for col in range(w):
                    frac = (col / float(w - 1)) if w > 1 else 0.5
                    u = ((col - half_w) / half_w) if half_w > 0.0 else 0.0
                    curve = 1.0 - u * u
                    lid_y = eye.upper_lid_l + (eye.upper_lid_r - eye.upper_lid_l) * frac
                    mask_bot = _round_half_away(y + lid_y + eye.upper_arch * curve)
                    for py in range(y - 2, mask_bot + 1):
                        self.fb.set_pixel(x + col, py, 0)
                    if max_ul >= 12.0 and 4 <= mask_bot <= HEIGHT - 6:
                        self.fb.set_pixel(x + col, mask_bot + 1, 1)

        # Proportional dark pupil + dual futuristic catchlights
        if eye.blink_squeeze < 0.45 and eye.pupil_radius >= 2.5:
            max_r_fit = min(w, h) // 2 - 4
            pr = _clamp_int(_round_half_away(eye.pupil_radius), 3, max(3, max_r_fit))
            top_mask = _round_half_away(max(eye.upper_lid_l, eye.upper_lid_r) + eye.upper_arch * 0.5)
            bot_mask = _round_half_away(eye.lower_lid + eye.lower_arch * 0.5)
            min_px = x + pr + 4
            max_px = x + w - 1 - pr - 4
            min_py = y + top_mask + pr + 2
            max_py = y + h - 1 - bot_mask - pr - 2
            if min_px <= max_px and min_py <= max_py:
                px = _clamp_int(_round_half_away(cx + eye.pupil_dx), min_px, max_px)
                py = _clamp_int(_round_half_away(cy + eye.pupil_dy), min_py, max_py)
                self.fb.fill_circle(px, py, pr, 0)
                gx = px - (pr // 2) + 1
                gy = py - (pr // 2) + 1
                self.fb.set_pixel(gx, gy, 1)
                self.fb.set_pixel(gx + 1, gy, 1)
                self.fb.set_pixel(gx, gy + 1, 1)
                self.fb.set_pixel(gx + 1, gy + 1, 1)
                if pr >= 5:
                    self.fb.set_pixel(px + (pr // 2) - 1, py + (pr // 2) - 1, 1)

        # Sculpted tapered eyebrow integrated over the eye dome
        if eye.brow_offset >= 1.0 and eye.blink_squeeze < 0.70:
            bw = _clamp_int(w - 6, 14, 34)
            bx0 = _clamp_int(cx - bw // 2, 4, WIDTH - bw - 4)
            by_base = _clamp_int(y - _round_half_away(eye.brow_offset), 4, HEIGHT - 8)
            for col in range(bw):
                frac = (col / float(bw - 1)) if bw > 1 else 0.5
                u = (frac - 0.5) * 2.0
                arch = eye.brow_arch * (1.0 - u * u)
                tilt = eye.brow_tilt * (frac - 0.5)
                py = _clamp_int(_round_half_away(float(by_base) + tilt - arch), 4, HEIGHT - 6)
                thick = 3 if abs(u) < 0.55 else 2
                for t in range(thick):
                    self.fb.set_pixel(bx0 + col, py + t, 1)

    def _draw_happy_crescent(self, eye: EyeState) -> None:
        cx = _clamp_int(_round_half_away(eye.x), 22, WIDTH - 22)
        cy = _clamp_int(_round_half_away(eye.y), 16, HEIGHT - 14)
        half = 16
        for dx in range(-half, half + 1):
            u = dx / float(half)
            arch = _round_half_away(9.0 * (1.0 - u * u))
            py = cy + 3 - arch
            thick = 5 if abs(u) < 0.65 else (4 if abs(u) < 0.85 else 3)
            for t in range(thick):
                self.fb.set_pixel(cx + dx, py + t, 1)
        bw = 26
        bx0 = cx - bw // 2
        by0 = max(5, cy - 15)
        for col in range(bw):
            u = (col / float(bw - 1) - 0.5) * 2.0
            py = max(4, by0 - _round_half_away(3.0 * (1.0 - u * u)))
            self.fb.set_pixel(bx0 + col, py, 1)
            self.fb.set_pixel(bx0 + col, py + 1, 1)

    def _draw_plump_heart(self, cx: int, cy: int) -> None:
        cx = _clamp_int(cx, 18, WIDTH - 18)
        cy = _clamp_int(cy, 18, HEIGHT - 18)
        for dy in range(-14, 14):
            for dx in range(-14, 15):
                nx = dx / 11.5
                ny = -(dy + 1.5) / 10.5
                val = (nx * nx + ny * ny - 1.0) ** 3 - (nx * nx) * (ny ** 3)
                if val <= 0.0:
                    self.fb.set_pixel(cx + dx, cy + dy, 1)
        self.fb.set_pixel(cx - 6, cy - 5, 0)
        self.fb.set_pixel(cx - 5, cy - 5, 0)
        self.fb.set_pixel(cx - 6, cy - 4, 0)

    def _draw_glyph(self, ox: int, oy: int, pattern: list[str], scale: int = 1) -> None:
        for r_idx, row in enumerate(pattern):
            for c_idx, ch in enumerate(row):
                if ch == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            px = _clamp_int(ox + c_idx * scale + sx, 4, WIDTH - 5)
                            py = _clamp_int(oy + r_idx * scale + sy, 4, HEIGHT - 5)
                            self.fb.set_pixel(px, py, 1)

    def _draw_sleeping_lash(self, eye: EyeState) -> None:
        cx = _clamp_int(_round_half_away(eye.x), 22, WIDTH - 22)
        cy = _clamp_int(_round_half_away(eye.y), 16, HEIGHT - 16)
        half = 15
        for dx in range(-half, half + 1):
            u = dx / float(half)
            sag = _round_half_away(5.0 * (1.0 - u * u))
            py = cy - 1 + sag
            thick = 4 if abs(u) < 0.7 else 3
            for t in range(thick):
                self.fb.set_pixel(cx + dx, py + t, 1)

    def render_frame(self, now_ms: int) -> None:
        self.fb.clear()
        if self.expr == Expression.LOVE:
            beat = 1 if ((now_ms // 260) % 2 == 0) else 0
            self._draw_plump_heart(_round_half_away(self.left.x), _round_half_away(self.left.y) - beat)
            self._draw_plump_heart(_round_half_away(self.right.x), _round_half_away(self.right.y) - beat)
            return

        if self.expr == Expression.HAPPY:
            self._draw_happy_crescent(self.left)
            self._draw_happy_crescent(self.right)
            for cx in (_round_half_away(self.left.x) - 14, _round_half_away(self.right.x) + 14):
                self.fb.set_pixel(cx, 48, 1)
                self.fb.set_pixel(cx + 1, 47, 1)
                self.fb.set_pixel(cx + 2, 48, 1)
            return

        if self.expr == Expression.WINK:
            self._draw_single_eye(self.left)
            self._draw_happy_crescent(self.right)
            return

        if self.expr == Expression.SLEEPING:
            self._draw_sleeping_lash(self.left)
            self._draw_sleeping_lash(self.right)
            phase = (now_ms // 450) % 3
            z_small = ["1111", "..1.", ".1..", "1111"]
            z_big = ["11111", "...1.", "..1..", ".1...", "11111"]
            self._draw_glyph(98, 14 - phase, z_small, scale=1)
            self._draw_glyph(106, 7 - phase, z_big, scale=1)
            return

        self._draw_single_eye(self.left)
        self._draw_single_eye(self.right)

        if self.expr == Expression.LISTENING:
            pulse_r = 2 if ((now_ms // 280) % 2 == 0) else 1
            self.fb.fill_circle(WIDTH // 2, HEIGHT - 4, pulse_r, 1)
        elif self.expr == Expression.THINKING:
            active_dot = (now_ms // 300) % 3
            for i in range(3):
                dx = (WIDTH // 2 - 8) + i * 8
                if i == active_dot:
                    self.fb.fill_circle(dx, HEIGHT - 4, 2, 1)
                else:
                    self.fb.draw_circle(dx, HEIGHT - 4, 1, 1)
        elif self.expr == Expression.SHY:
            for cx in (_round_half_away(self.left.x) - 10, _round_half_away(self.right.x) + 10):
                for offset in (-4, 0, 4):
                    self.fb.set_pixel(cx + offset, 53, 1)
                    self.fb.set_pixel(cx + offset + 1, 52, 1)
        elif self.expr == Expression.CONFUSED:
            q_mark = [
                ".111.",
                "1...1",
                "...1.",
                "..1..",
                "..1..",
                ".....",
                "..1..",
            ]
            self._draw_glyph(114, 6, q_mark, scale=1)
        elif self.expr == Expression.SURPRISED:
            bang = ["11", "11", "11", "11", "..", "11"]
            self._draw_glyph(WIDTH // 2 - 1, 6, bang, scale=1)


class SimulatorStateMachine:
    """Mirror of firmware StateMachine for interactive PC & host command testing."""

    CYCLE_ORDER = [
        Expression.IDLE,
        Expression.HAPPY,
        Expression.CURIOUS,
        Expression.LISTENING,
        Expression.THINKING,
        Expression.SPEAKING,
        Expression.SLEEPY,
    ]
    DEMO_INTERVAL_MS = 5000

    def __init__(self, eyes: EyeEngine, auto_demo: bool = True) -> None:
        self.eyes = eyes
        self.auto_demo = auto_demo
        self.demo_idx = 0
        self.last_demo_switch_ms = 0

    def set_expression(self, expr: Expression, now_ms: int, disable_auto: bool = True) -> None:
        if disable_auto:
            self.auto_demo = False
        self.eyes.set_expression(expr, now_ms=now_ms)
        if expr in self.CYCLE_ORDER:
            self.demo_idx = self.CYCLE_ORDER.index(expr)

    def handle_command(self, raw_cmd: str, now_ms: int) -> str:
        cmd = raw_cmd.strip().upper()
        if not cmd:
            return ""
        arg = cmd
        if cmd.startswith("STATE:"):
            arg = cmd[6:]
        elif cmd.startswith("CMD:"):
            arg = cmd[4:]

        if arg in ("IDLE", "NEUTRAL"):
            self.set_expression(Expression.IDLE, now_ms, disable_auto=True)
            return "EVENT:STATE=IDLE"
        for expr in ALL_EXPRESSIONS:
            if arg == expr.value:
                self.set_expression(expr, now_ms, disable_auto=True)
                return f"EVENT:STATE={expr.value}"
        if arg == "BLINK":
            self.eyes.trigger_blink(now_ms)
            return "OK:BLINK"
        if arg.startswith("LOOK:"):
            parts = arg[5:].split(",")
            if len(parts) == 2:
                try:
                    dx, dy = int(parts[0]), int(parts[1])
                    self.eyes.set_gaze_offset(dx, dy, 2000, now_ms)
                    return "OK:LOOK"
                except ValueError:
                    pass
            return "ERR:LOOK_SYNTAX"
        if arg == "AUTO:ON":
            self.auto_demo = True
            self.last_demo_switch_ms = now_ms
            return "OK:AUTO=ON"
        if arg == "AUTO:OFF":
            self.auto_demo = False
            return "OK:AUTO=OFF"
        if arg.startswith("PROFILE:"):
            prof = arg[8:]
            if prof in ("CALM", "LIVELY", "PLAYFUL"):
                self.eyes.set_visual_profile(prof)
                return f"OK:PROFILE={prof}"
            return "ERR:PROFILE_SYNTAX"
        if arg == "PING":
            return "PONG"
        if arg == "STATUS":
            return f"OK:STATE={self.eyes.expr.value};AUTO={'ON' if self.auto_demo else 'OFF'};PROFILE={self.eyes.profile.value};RES=128x64"
        if arg == "DIAG":
            return (
                f"OK:DIAG;STATE={self.eyes.expr.value};UPTIME_MS={now_ms};DRIVER=SIM;"
                f"RENDER_US={self.eyes.last_render_us};FPS={self.eyes.actual_fps:.1f};"
                f"DROPPED={self.eyes.dropped_frames};PROFILE={self.eyes.profile.value};RES=128x64"
            )
        return f"ERR:UNKNOWN_CMD={cmd}"

    def update(self, now_ms: int) -> Optional[Expression]:
        if self.auto_demo and (now_ms - self.last_demo_switch_ms) >= self.DEMO_INTERVAL_MS:
            self.last_demo_switch_ms = now_ms
            self.demo_idx = (self.demo_idx + 1) % len(self.CYCLE_ORDER)
            nxt = self.CYCLE_ORDER[self.demo_idx]
            self.eyes.set_expression(nxt, now_ms=now_ms)
            return nxt
        return None
