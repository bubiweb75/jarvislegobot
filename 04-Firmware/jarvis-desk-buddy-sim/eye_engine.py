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
from typing import Optional

from monochrome_fb import HEIGHT, WIDTH, MonochromeFramebuffer


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

    width: float = 30.0
    height: float = 32.0
    target_width: float = 30.0
    target_height: float = 32.0

    corner_radius: float = 10.0
    target_corner_radius: float = 10.0

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

    blink_squeeze: float = 0.0


class EyeEngine:
    DEFAULT_EYE_WIDTH = 30
    DEFAULT_EYE_HEIGHT = 32
    DEFAULT_CORNER_RADIUS = 10

    def __init__(self, fps: int = 50, spacing_px: int = 16, seed: int = 0xA511E9B3) -> None:
        self.fb = MonochromeFramebuffer()
        self.left = EyeState()
        self.right = EyeState()
        self.expr = Expression.IDLE
        self.spacing_px = spacing_px
        self.frame_interval_ms = (1000 // fps) if fps > 0 else 20
        self.last_frame_ms = 0

        self.blink_phase = "OPEN"
        self.next_blink_ms = 2200
        self.blink_hold_until_ms = 0
        self.double_blink_pending = False

        self.auto_idle_gaze = True
        self.next_gaze_ms = 2400
        self.gaze_override_until_ms = 0
        self.expr_start_ms = 0

        self._rng_state = seed & 0xFFFFFFFF or 0xA511E9B3

        self._recalculate_base_positions()
        self._apply_expression_targets()
        self.render_frame(0)

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
        self.left.base_y = HEIGHT // 2
        self.right.base_y = HEIGHT // 2

        self.left.x = self.left.target_x = float(self.left.base_x)
        self.right.x = self.right.target_x = float(self.right.base_x)
        self.left.y = self.left.target_y = float(self.left.base_y)
        self.right.y = self.right.target_y = float(self.right.base_y)

    def set_expression(self, expr: Expression, now_ms: int = 0) -> None:
        if self.expr == expr:
            return
        self.expr = expr
        self.expr_start_ms = now_ms
        self._apply_expression_targets()

    def _apply_expression_targets(self) -> None:
        for eye in (self.left, self.right):
            eye.target_width = float(self.DEFAULT_EYE_WIDTH)
            eye.target_height = float(self.DEFAULT_EYE_HEIGHT)
            eye.target_corner_radius = float(self.DEFAULT_CORNER_RADIUS)
            eye.target_lower_lid = 0.0
            eye.target_lower_arch = 0.0
            eye.target_upper_lid_l = 0.0
            eye.target_upper_lid_r = 0.0
            eye.target_upper_arch = 0.0
            eye.target_x = float(eye.base_x)
            eye.target_y = float(eye.base_y)

        if self.expr == Expression.IDLE:
            pass
        elif self.expr == Expression.HAPPY:
            self.left.target_width = self.right.target_width = 33.0
            self.left.target_height = self.right.target_height = 30.0
            self.left.target_corner_radius = self.right.target_corner_radius = 12.0
            self.left.target_lower_lid = self.right.target_lower_lid = 6.0
            self.left.target_lower_arch = self.right.target_lower_arch = 12.0
            self.left.target_y = self.right.target_y = float(self.left.base_y - 2)
        elif self.expr == Expression.CURIOUS:
            self.left.target_width = 27.0
            self.left.target_height = 26.0
            self.left.target_corner_radius = 9.0
            self.left.target_upper_lid_l = 1.0
            self.left.target_upper_lid_r = 6.0
            self.left.target_x = float(self.left.base_x + 4)
            self.left.target_y = float(self.left.base_y + 2)

            self.right.target_width = 34.0
            self.right.target_height = 36.0
            self.right.target_corner_radius = 12.0
            self.right.target_x = float(self.right.base_x + 4)
            self.right.target_y = float(self.right.base_y - 3)
        elif self.expr == Expression.SLEEPY:
            self.left.target_width = self.right.target_width = 31.0
            self.left.target_height = self.right.target_height = 28.0
            self.left.target_corner_radius = self.right.target_corner_radius = 10.0
            self.left.target_upper_lid_l = self.left.target_upper_lid_r = 12.0
            self.right.target_upper_lid_l = self.right.target_upper_lid_r = 12.0
            self.left.target_upper_arch = self.right.target_upper_arch = 2.5
            self.left.target_y = self.right.target_y = float(self.left.base_y + 4)
        elif self.expr == Expression.LISTENING:
            self.left.target_width = self.right.target_width = 32.0
            self.left.target_height = self.right.target_height = 36.0
            self.left.target_corner_radius = self.right.target_corner_radius = 11.0
        elif self.expr == Expression.THINKING:
            self.left.target_width = self.right.target_width = 29.0
            self.left.target_height = self.right.target_height = 29.0
            self.left.target_corner_radius = self.right.target_corner_radius = 10.0
            self.left.target_x = float(self.left.base_x + 7)
            self.right.target_x = float(self.right.base_x + 7)
            self.left.target_y = float(self.left.base_y - 5)
            self.right.target_y = float(self.right.base_y - 5)
            self.left.target_upper_lid_l = 4.0
            self.left.target_upper_lid_r = 2.0
            self.right.target_lower_lid = 3.0
            self.right.target_lower_arch = 3.0
        elif self.expr == Expression.SPEAKING:
            self.left.target_width = self.right.target_width = 31.0
            self.left.target_height = self.right.target_height = 31.0
            self.left.target_corner_radius = self.right.target_corner_radius = 10.0
            self.left.target_lower_lid = self.right.target_lower_lid = 3.0
            self.left.target_lower_arch = self.right.target_lower_arch = 5.0
        elif self.expr == Expression.SURPRISED:
            self.left.target_width = self.right.target_width = 34.0
            self.left.target_height = self.right.target_height = 40.0
            self.left.target_corner_radius = self.right.target_corner_radius = 15.0
            self.left.target_y = self.right.target_y = float(self.left.base_y - 3)
        elif self.expr == Expression.SHY:
            self.left.target_width = self.right.target_width = 25.0
            self.left.target_height = self.right.target_height = 24.0
            self.left.target_corner_radius = self.right.target_corner_radius = 10.0
            self.left.target_upper_lid_l = self.left.target_upper_lid_r = 4.0
            self.right.target_upper_lid_l = self.right.target_upper_lid_r = 4.0
            self.left.target_x = float(self.left.base_x + 4)
            self.right.target_x = float(self.right.base_x + 4)
            self.left.target_y = self.right.target_y = float(self.left.base_y + 4)
        elif self.expr == Expression.LOVE:
            self.left.target_width = self.right.target_width = 30.0
            self.left.target_height = self.right.target_height = 28.0
            self.left.target_corner_radius = self.right.target_corner_radius = 10.0
        elif self.expr == Expression.WINK:
            self.left.target_width = 32.0
            self.left.target_height = 32.0
            self.left.target_corner_radius = 12.0
            self.left.target_lower_lid = 4.0
            self.left.target_lower_arch = 9.0
            self.right.target_width = 32.0
            self.right.target_height = 28.0
            self.right.target_y = float(self.right.base_y + 2)
        elif self.expr == Expression.CONFUSED:
            self.left.target_width = 28.0
            self.left.target_height = 24.0
            self.left.target_corner_radius = 8.0
            self.left.target_upper_lid_l = 7.0
            self.left.target_upper_lid_r = 2.0
            self.left.target_y = float(self.left.base_y + 2)
            self.right.target_width = 32.0
            self.right.target_height = 36.0
            self.right.target_corner_radius = 12.0
            self.right.target_upper_lid_l = 0.0
            self.right.target_upper_lid_r = 5.0
            self.right.target_y = float(self.right.base_y - 3)
        elif self.expr == Expression.MISCHIEVOUS:
            self.left.target_width = self.right.target_width = 32.0
            self.left.target_height = self.right.target_height = 28.0
            self.left.target_corner_radius = self.right.target_corner_radius = 10.0
            self.left.target_upper_lid_l = 2.0
            self.left.target_upper_lid_r = 10.0
            self.right.target_upper_lid_l = 10.0
            self.right.target_upper_lid_r = 2.0
            self.left.target_lower_lid = self.right.target_lower_lid = 4.0
            self.left.target_lower_arch = self.right.target_lower_arch = 7.0
            self.left.target_x = float(self.left.base_x - 3)
            self.right.target_x = float(self.right.base_x - 3)
        elif self.expr == Expression.SLEEPING:
            self.left.target_width = self.right.target_width = 30.0
            self.left.target_height = self.right.target_height = 10.0
            self.left.target_y = self.right.target_y = float(self.left.base_y + 4)

    def trigger_blink(self, now_ms: int) -> None:
        if self.blink_phase == "OPEN":
            self.blink_phase = "CLOSING"
            self.next_blink_ms = now_ms + 3200

    def set_gaze_offset(self, dx: int, dy: int, hold_ms: int, now_ms: int) -> None:
        dx = _clamp_int(dx, -11, 11)
        dy = _clamp_int(dy, -6, 6)
        self.left.target_x = float(self.left.base_x + dx)
        self.right.target_x = float(self.right.base_x + dx)
        self.left.target_y = float(self.left.base_y + dy)
        self.right.target_y = float(self.right.base_y + dy)
        self.gaze_override_until_ms = now_ms + hold_ms

    def _update_blinker(self, now_ms: int, dt_sec: float) -> None:
        if self.expr in (Expression.WINK, Expression.SLEEPING):
            self.blink_phase = "OPEN"
            self.left.blink_squeeze = 0.0
            self.right.blink_squeeze = 0.0
            return

        close_rate = 6.5 if self.expr == Expression.SLEEPY else 18.0
        open_rate = 4.5 if self.expr == Expression.SLEEPY else 14.0

        if self.blink_phase == "OPEN":
            if now_ms >= self.next_blink_ms:
                self.blink_phase = "CLOSING"
                if self.expr == Expression.IDLE and not self.double_blink_pending:
                    self.double_blink_pending = self._rand_range(0, 99) < 20
        elif self.blink_phase == "CLOSING":
            self.left.blink_squeeze += close_rate * dt_sec
            self.right.blink_squeeze += close_rate * dt_sec
            if self.left.blink_squeeze >= 1.0:
                self.left.blink_squeeze = self.right.blink_squeeze = 1.0
                self.blink_phase = "HOLD_CLOSED"
                self.blink_hold_until_ms = now_ms + (140 if self.expr == Expression.SLEEPY else 45)
        elif self.blink_phase == "HOLD_CLOSED":
            if now_ms >= self.blink_hold_until_ms:
                self.blink_phase = "OPENING"
        elif self.blink_phase == "OPENING":
            self.left.blink_squeeze -= open_rate * dt_sec
            self.right.blink_squeeze -= open_rate * dt_sec
            if self.left.blink_squeeze <= 0.0:
                self.left.blink_squeeze = self.right.blink_squeeze = 0.0
                self.blink_phase = "OPEN"
                if self.double_blink_pending:
                    self.double_blink_pending = False
                    self.next_blink_ms = now_ms + 130
                else:
                    lo, hi = (1900, 3600) if self.expr == Expression.SLEEPY else (2600, 5400)
                    self.next_blink_ms = now_ms + self._rand_range(lo, hi)

    def _update_gaze(self, now_ms: int) -> None:
        if not self.auto_idle_gaze:
            return
        if now_ms < self.gaze_override_until_ms:
            return
        if self.expr in (
            Expression.THINKING,
            Expression.LISTENING,
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
        if now_ms >= self.next_gaze_ms:
            return_center = self._rand_range(0, 99) < 35
            dx = 0
            dy = 0
            if not return_center:
                max_dx = 3 if self.expr == Expression.SLEEPY else 9
                max_dy = 2 if self.expr == Expression.SLEEPY else 4
                dx = self._rand_range(-max_dx, max_dx)
                dy = self._rand_range(-max_dy, max_dy)
            y_bias = -2 if self.expr == Expression.HAPPY else (4 if self.expr == Expression.SLEEPY else 0)
            self.left.target_x = float(self.left.base_x + dx)
            self.right.target_x = float(self.right.base_x + dx)
            self.left.target_y = float(self.left.base_y + dy + y_bias)
            self.right.target_y = float(self.right.base_y + dy + y_bias)
            self.next_gaze_ms = now_ms + self._rand_range(1700, 3900)

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
        eye.x = _smooth_exp(eye.x, eye.target_x, 12.0, dt_sec)
        eye.y = _smooth_exp(eye.y, eye.target_y, 12.0, dt_sec)
        eye.width = _smooth_exp(eye.width, eye.target_width, 10.0, dt_sec)
        eye.height = _smooth_exp(eye.height, eye.target_height, 10.0, dt_sec)
        eye.corner_radius = _smooth_exp(eye.corner_radius, eye.target_corner_radius, 10.0, dt_sec)
        eye.lower_lid = _smooth_exp(eye.lower_lid, eye.target_lower_lid, 12.0, dt_sec)
        eye.lower_arch = _smooth_exp(eye.lower_arch, eye.target_lower_arch, 12.0, dt_sec)
        eye.upper_lid_l = _smooth_exp(eye.upper_lid_l, eye.target_upper_lid_l, 12.0, dt_sec)
        eye.upper_lid_r = _smooth_exp(eye.upper_lid_r, eye.target_upper_lid_r, 12.0, dt_sec)
        eye.upper_arch = _smooth_exp(eye.upper_arch, eye.target_upper_arch, 12.0, dt_sec)

    def update(self, now_ms: int, force: bool = False) -> bool:
        if not force and (now_ms - self.last_frame_ms) < self.frame_interval_ms:
            return False
        self.update_step(now_ms)
        return True

    def update_step(self, now_ms: int) -> None:
        dt_ms = (now_ms - self.last_frame_ms) if now_ms >= self.last_frame_ms else self.frame_interval_ms
        dt_ms = _clamp_int(dt_ms, 1, 100)
        dt_sec = dt_ms * 0.001
        self.last_frame_ms = now_ms

        self._update_blinker(now_ms, dt_sec)
        self._update_gaze(now_ms)
        self._update_expression_motion(now_ms)
        self._interpolate_eye(self.left, dt_sec)
        self._interpolate_eye(self.right, dt_sec)
        self.render_frame(now_ms)

    def _draw_single_eye(self, eye: EyeState) -> None:
        w = _clamp_int(_round_half_away(eye.width), 8, 44)
        raw_h = _clamp_int(_round_half_away(eye.height), 8, 44)

        if eye.blink_squeeze >= 0.85:
            cx = _clamp_int(_round_half_away(eye.x), w // 2 + 4, WIDTH - w // 2 - 4)
            cy = _clamp_int(_round_half_away(eye.y) + 2, 4, HEIGHT - 5)
            self.fb.fill_round_rect(cx - w // 2, cy - 1, w, 2, 1, 1)
            return

        h = _clamp_int(_round_half_away(raw_h * (1.0 - 0.88 * eye.blink_squeeze)), 3, 44)
        x = _clamp_int(_round_half_away(eye.x) - w // 2, 4, WIDTH - w - 4)
        y = _clamp_int(_round_half_away(eye.y) - h // 2, 4, HEIGHT - h - 4)
        r = _clamp_int(_round_half_away(eye.corner_radius), 1, min(w, h) // 2)

        self.fb.fill_round_rect(x, y, w, h, r, 1)

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
                for col in range(w):
                    frac = (col / float(w - 1)) if w > 1 else 0.5
                    u = ((col - half_w) / half_w) if half_w > 0.0 else 0.0
                    curve = 1.0 - u * u
                    lid_y = eye.upper_lid_l + (eye.upper_lid_r - eye.upper_lid_l) * frac
                    mask_bot = _round_half_away(y + lid_y + eye.upper_arch * curve)
                    for py in range(y - 1, mask_bot + 1):
                        self.fb.set_pixel(x + col, py, 0)

    def _draw_heart(self, cx: int, cy: int, scale: int = 2) -> None:
        pattern = [
            ".111...111.",
            "11111.11111",
            "11111111111",
            "11111111111",
            "11111111111",
            ".111111111.",
            "..1111111..",
            "...11111...",
            "....111....",
            ".....1.....",
        ]
        ph = len(pattern) * scale
        pw = len(pattern[0]) * scale
        ox = _clamp_int(cx - pw // 2, 4, WIDTH - pw - 4)
        oy = _clamp_int(cy - ph // 2, 4, HEIGHT - ph - 4)
        for r_idx, row in enumerate(pattern):
            for c_idx, ch in enumerate(row):
                if ch == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            self.fb.set_pixel(ox + c_idx * scale + sx, oy + r_idx * scale + sy, 1)

    def _draw_glyph(self, ox: int, oy: int, pattern: list[str], scale: int = 1) -> None:
        for r_idx, row in enumerate(pattern):
            for c_idx, ch in enumerate(row):
                if ch == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            px = _clamp_int(ox + c_idx * scale + sx, 4, WIDTH - 5)
                            py = _clamp_int(oy + r_idx * scale + sy, 4, HEIGHT - 5)
                            self.fb.set_pixel(px, py, 1)

    def _draw_wink_eye(self, eye: EyeState) -> None:
        cx = _clamp_int(_round_half_away(eye.x), 20, WIDTH - 20)
        cy = _clamp_int(_round_half_away(eye.y), 14, HEIGHT - 14)
        w = 26
        half = w // 2
        for dx in range(-half, half + 1):
            u = dx / float(half)
            arch = _round_half_away(4.0 * (1.0 - u * u))
            py = cy + 2 - arch
            for thick in range(3):
                self.fb.set_pixel(cx + dx, py + thick, 1)

    def _draw_sleeping_eye(self, eye: EyeState) -> None:
        cx = _clamp_int(_round_half_away(eye.x), 20, WIDTH - 20)
        cy = _clamp_int(_round_half_away(eye.y), 14, HEIGHT - 14)
        w = 28
        half = w // 2
        for dx in range(-half, half + 1):
            u = dx / float(half)
            sag = _round_half_away(3.5 * (1.0 - u * u))
            py = cy + sag
            for thick in range(4):
                self.fb.set_pixel(cx + dx, py + thick, 1)

    def render_frame(self, now_ms: int) -> None:
        self.fb.clear()
        if self.expr == Expression.LOVE:
            beat = 1 if ((now_ms // 260) % 2 == 0) else 0
            self._draw_heart(_round_half_away(self.left.x), _round_half_away(self.left.y) - beat, scale=2)
            self._draw_heart(_round_half_away(self.right.x), _round_half_away(self.right.y) - beat, scale=2)
            return

        if self.expr == Expression.WINK:
            self._draw_single_eye(self.left)
            self._draw_wink_eye(self.right)
            return

        if self.expr == Expression.SLEEPING:
            self._draw_sleeping_eye(self.left)
            self._draw_sleeping_eye(self.right)
            phase = (now_ms // 450) % 3
            z_small = ["1111", "..1.", ".1..", "1111"]
            z_big = ["11111", "...1.", "..1..", ".1...", "11111"]
            self._draw_glyph(98, 16 - phase, z_small, scale=1)
            self._draw_glyph(106, 9 - phase, z_big, scale=1)
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
                    self.fb.set_pixel(cx + offset, 52, 1)
                    self.fb.set_pixel(cx + offset + 1, 51, 1)
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
            self._draw_glyph(112, 6, q_mark, scale=1)
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
        if arg == "PING":
            return "PONG"
        if arg == "STATUS":
            return f"OK:STATE={self.eyes.expr.value};AUTO={'ON' if self.auto_demo else 'OFF'};RES=128x64"
        return f"ERR:UNKNOWN_CMD={cmd}"

    def update(self, now_ms: int) -> Optional[Expression]:
        if self.auto_demo and (now_ms - self.last_demo_switch_ms) >= self.DEMO_INTERVAL_MS:
            self.last_demo_switch_ms = now_ms
            self.demo_idx = (self.demo_idx + 1) % len(self.CYCLE_ORDER)
            nxt = self.CYCLE_ORDER[self.demo_idx]
            self.eyes.set_expression(nxt, now_ms=now_ms)
            return nxt
        return None
