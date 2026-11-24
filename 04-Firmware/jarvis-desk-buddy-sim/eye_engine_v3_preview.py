"""JARVIS Eyes 3.0 Preview Engine — Organic Visor Companion (128x64 Monochrome).

Brand-new visual language for FASE 10.3 evaluation before C++ firmware sync:
- Organic superellipse / tapered eye silhouettes (not boxy rounded rects)
- Sculpted tapered eyebrows integrated above the eye dome
- Proportional dark pupils with crisp dual futuristic catchlights
- Unmistakable cartoon silhouettes for all 14 expressions (even in still frames)
- Full Eyes 3.0 Natural Gaze, Advanced Blink, Micro-Expressions & Visual Profiles
"""

from dataclasses import dataclass
import math
import time
from typing import Optional

from eye_engine import (
    ALL_EXPRESSIONS,
    Expression,
    MicroExprType,
    VisualProfile,
    _clamp_int,
    _round_half_away,
    _smooth_exp,
)
from monochrome_fb import HEIGHT, WIDTH, MonochromeFramebuffer


@dataclass
class EyeState30:
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

    # Superellipse exponent (2.0 = ellipse, 2.7 = organic soft cushion)
    shape_power: float = 2.6
    target_shape_power: float = 2.6
    # Vertical taper (+ = wider top / softer cheek, - = wider bottom)
    taper: float = 0.10
    target_taper: float = 0.10

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
    pupil_radius: float = 7.0
    target_pupil_radius: float = 7.0

    brow_offset: float = 4.0
    target_brow_offset: float = 4.0
    brow_tilt: float = 0.0
    target_brow_tilt: float = 0.0
    brow_arch: float = 2.0
    target_brow_arch: float = 2.0

    blink_squeeze: float = 0.0


class EyeEngineV3:
    """JARVIS Eyes 3.0 — Organic Visor Companion Engine (128x64 monochrome)."""

    DEFAULT_EYE_WIDTH = 38
    DEFAULT_EYE_HEIGHT = 38

    def __init__(self, fps: int = 30, spacing_px: int = 12, seed: int = 2026) -> None:
        self.fb = MonochromeFramebuffer()
        self.left = EyeState30()
        self.right = EyeState30()
        self.expr = Expression.IDLE
        self.spacing_px = spacing_px
        self.frame_interval_ms = (1000 // fps) if fps > 0 else 33
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
        self.next_micro_expr_ms = 3600
        self.transition_boost = 1.0
        self.expr_start_ms = 0
        self._rng_state = seed & 0xFFFFFFFF or 0xA511E9B3

        total_w = self.DEFAULT_EYE_WIDTH + self.spacing_px + self.DEFAULT_EYE_WIDTH
        start_x = (WIDTH - total_w) // 2
        self.left.base_x = start_x + self.DEFAULT_EYE_WIDTH // 2
        self.right.base_x = start_x + self.DEFAULT_EYE_WIDTH + self.spacing_px + self.DEFAULT_EYE_WIDTH // 2
        self.left.base_y = self.right.base_y = HEIGHT // 2 + 2
        self.left.x = self.left.target_x = float(self.left.base_x)
        self.right.x = self.right.target_x = float(self.right.base_x)
        self.left.y = self.left.target_y = float(self.left.base_y)
        self.right.y = self.right.target_y = float(self.right.base_y)

        self._apply_expression_targets()
        self.render_frame(0)

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
        return lo + (self._next_rand() % (hi - lo + 1))

    def set_visual_profile(self, profile: VisualProfile | str) -> None:
        if isinstance(profile, str):
            profile = VisualProfile(profile.strip().upper())
        self.profile = profile

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

    def set_expression(self, expr: Expression, now_ms: int = 0) -> None:
        if self.expr == expr:
            return
        self.expr = expr
        self.expr_start_ms = now_ms
        self.micro_expr = MicroExprType.NONE
        self.transition_boost = 1.85 if expr == Expression.SURPRISED else 1.05
        self._apply_expression_targets()

    def trigger_blink(self, now_ms: int) -> None:
        if self.blink_phase == "OPEN":
            self.blink_phase = "CLOSING"
            self.next_blink_ms = now_ms + 3200

    def set_gaze_offset(self, dx: int, dy: int, hold_ms: int, now_ms: int) -> None:
        dx = _clamp_int(dx, -11, 11)
        dy = _clamp_int(dy, -6, 6)
        self.micro_expr = MicroExprType.NONE
        self.gaze_is_micro = False
        self.left.target_x = float(self.left.base_x) + float(dx) * 0.40
        self.right.target_x = float(self.right.base_x) + float(dx) * 0.40
        self.left.target_y = float(self.left.base_y) + float(dy) * 0.35
        self.right.target_y = float(self.right.base_y) + float(dy) * 0.35
        self.left.target_pupil_dx = self.right.target_pupil_dx = float(dx) * 0.65
        self.left.target_pupil_dy = self.right.target_pupil_dy = float(dy) * 0.55
        self.gaze_override_until_ms = now_ms + hold_ms

    def _apply_expression_targets(self) -> None:
        for eye in (self.left, self.right):
            eye.target_width = float(self.DEFAULT_EYE_WIDTH)
            eye.target_height = float(self.DEFAULT_EYE_HEIGHT)
            eye.target_shape_power = 2.6
            eye.target_taper = 0.10
            eye.target_lower_lid = 0.0
            eye.target_lower_arch = 0.0
            eye.target_upper_lid_l = 0.0
            eye.target_upper_lid_r = 0.0
            eye.target_upper_arch = 0.0
            eye.target_pupil_dx = 0.0
            eye.target_pupil_dy = 0.0
            eye.target_pupil_radius = 7.0
            eye.target_brow_offset = 4.0
            eye.target_brow_tilt = 0.0
            eye.target_brow_arch = 2.2
            eye.target_x = float(eye.base_x)
            eye.target_y = float(eye.base_y)

        e = self.expr
        if e == Expression.IDLE:
            pass
        elif e == Expression.HAPPY:
            # Distinct joyful cartoon smiling crescent arches
            self.left.target_width = self.right.target_width = 36.0
            self.left.target_height = self.right.target_height = 24.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 0.0
            self.left.target_brow_offset = self.right.target_brow_offset = 6.0
            self.left.target_brow_arch = self.right.target_brow_arch = 3.5
            self.left.target_y = self.right.target_y = float(self.left.base_y + 1)
        elif e == Expression.CURIOUS:
            # Strong cartoon asymmetry: left narrowed & tilted, right big & wide
            self.left.target_width, self.left.target_height = 30.0, 28.0
            self.left.target_shape_power = 2.4
            self.left.target_upper_lid_l, self.left.target_upper_lid_r = 2.0, 7.0
            self.left.target_pupil_dx, self.left.target_pupil_radius = 3.0, 6.0
            self.left.target_brow_offset, self.left.target_brow_tilt, self.left.target_brow_arch = 3.5, 2.5, 1.0
            self.left.target_x = float(self.left.base_x + 2)
            self.left.target_y = float(self.left.base_y + 3)

            self.right.target_width, self.right.target_height = 42.0, 42.0
            self.right.target_shape_power = 2.2
            self.right.target_taper = -0.06
            self.right.target_pupil_dx, self.right.target_pupil_dy, self.right.target_pupil_radius = 3.0, -2.0, 7.5
            self.right.target_brow_offset, self.right.target_brow_tilt, self.right.target_brow_arch = 6.5, -2.5, 4.0
            self.right.target_x = float(self.right.base_x + 2)
            self.right.target_y = float(self.right.base_y - 2)
        elif e == Expression.SLEEPY:
            # Heavy half-closed droopy lids with low half-moon pupils peeking underneath
            self.left.target_width = self.right.target_width = 36.0
            self.left.target_height = self.right.target_height = 30.0
            self.left.target_upper_lid_l = self.left.target_upper_lid_r = 11.0
            self.right.target_upper_lid_l = self.right.target_upper_lid_r = 11.0
            self.left.target_upper_arch = self.right.target_upper_arch = 2.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 5.0
            self.left.target_pupil_dy = self.right.target_pupil_dy = 3.0
            self.left.target_brow_offset = self.right.target_brow_offset = 2.0
            self.left.target_brow_arch = self.right.target_brow_arch = 0.5
            self.left.target_y = self.right.target_y = float(self.left.base_y + 3)
        elif e == Expression.LISTENING:
            # Tall attentive eyes with wide receptive pupils
            self.left.target_width = self.right.target_width = 38.0
            self.left.target_height = self.right.target_height = 42.0
            self.left.target_shape_power = self.right.target_shape_power = 2.4
            self.left.target_pupil_radius = self.right.target_pupil_radius = 8.5
            self.left.target_brow_offset = self.right.target_brow_offset = 5.5
            self.left.target_brow_arch = self.right.target_brow_arch = 3.0
        elif e == Expression.THINKING:
            # Concentrated half-lidded squint + up-right focused gaze + furrowed brows
            self.left.target_width = self.right.target_width = 35.0
            self.left.target_height = self.right.target_height = 31.0
            self.left.target_x, self.right.target_x = float(self.left.base_x + 4), float(self.right.base_x + 4)
            self.left.target_y, self.right.target_y = float(self.left.base_y - 3), float(self.right.base_y - 3)
            self.left.target_upper_lid_l, self.left.target_upper_lid_r = 8.0, 5.0
            self.right.target_upper_lid_l, self.right.target_upper_lid_r = 4.0, 6.0
            self.left.target_lower_lid = self.right.target_lower_lid = 3.0
            self.left.target_pupil_dx = self.right.target_pupil_dx = 5.5
            self.left.target_pupil_dy = self.right.target_pupil_dy = -3.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 5.5
            self.left.target_brow_offset, self.left.target_brow_tilt = 3.5, 3.0
            self.right.target_brow_offset, self.right.target_brow_tilt = 5.5, -1.5
        elif e == Expression.SPEAKING:
            # Warm lively companion eyes with gentle lower cheek lift
            self.left.target_width = self.right.target_width = 37.0
            self.left.target_height = self.right.target_height = 35.0
            self.left.target_lower_lid = self.right.target_lower_lid = 4.0
            self.left.target_lower_arch = self.right.target_lower_arch = 6.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 6.5
            self.left.target_brow_offset = self.right.target_brow_offset = 4.5
        elif e == Expression.SURPRISED:
            # Tall wide-open dome + tiny pinprick pupil + high arched brows
            self.left.target_width = self.right.target_width = 39.0
            self.left.target_height = self.right.target_height = 45.0
            self.left.target_shape_power = self.right.target_shape_power = 2.1
            self.left.target_taper = self.right.target_taper = 0.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 3.5
            self.left.target_brow_offset = self.right.target_brow_offset = 6.0
            self.left.target_brow_arch = self.right.target_brow_arch = 4.5
            self.left.target_y = self.right.target_y = float(self.left.base_y)
        elif e == Expression.SHY:
            # Soft downcast eyes + inward-angled shy brows + blush
            self.left.target_width = self.right.target_width = 32.0
            self.left.target_height = self.right.target_height = 28.0
            self.left.target_upper_lid_l = self.left.target_upper_lid_r = 6.0
            self.right.target_upper_lid_l = self.right.target_upper_lid_r = 6.0
            self.left.target_pupil_dx = self.right.target_pupil_dx = -4.0
            self.left.target_pupil_dy = self.right.target_pupil_dy = 2.5
            self.left.target_pupil_radius = self.right.target_pupil_radius = 6.0
            self.left.target_brow_offset = self.right.target_brow_offset = 4.5
            self.left.target_brow_tilt, self.right.target_brow_tilt = -3.5, 3.5
            self.left.target_x, self.right.target_x = float(self.left.base_x - 3), float(self.right.base_x - 3)
            self.left.target_y = self.right.target_y = float(self.left.base_y + 4)
        elif e == Expression.LOVE:
            self.left.target_width = self.right.target_width = 34.0
            self.left.target_height = self.right.target_height = 34.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 0.0
            self.left.target_brow_offset = self.right.target_brow_offset = 0.0
            self.left.target_y = self.right.target_y = float(self.left.base_y)
        elif e == Expression.WINK:
            self.left.target_width, self.left.target_height = 38.0, 38.0
            self.left.target_pupil_radius = 7.0
            self.left.target_brow_offset, self.left.target_brow_arch = 5.5, 3.0
            self.right.target_width, self.right.target_height = 36.0, 26.0
            self.right.target_pupil_radius = 0.0
            self.right.target_brow_offset = 5.0
            self.right.target_y = float(self.right.base_y + 2)
        elif e == Expression.CONFUSED:
            self.left.target_width, self.left.target_height = 31.0, 27.0
            self.left.target_upper_lid_l, self.left.target_upper_lid_r = 8.0, 3.0
            self.left.target_pupil_dx, self.left.target_pupil_radius = -3.0, 5.5
            self.left.target_brow_offset, self.left.target_brow_tilt = 4.0, 3.5
            self.left.target_y = float(self.left.base_y + 2)
            self.right.target_width, self.right.target_height = 40.0, 40.0
            self.right.target_pupil_dx, self.right.target_pupil_dy, self.right.target_pupil_radius = 3.0, -2.0, 7.0
            self.right.target_brow_offset, self.right.target_brow_tilt, self.right.target_brow_arch = 6.0, -3.5, 4.0
            self.right.target_y = float(self.right.base_y - 2)
        elif e == Expression.MISCHIEVOUS:
            # Sharp sly-fox diagonal slant + lower smile + cocked brows
            self.left.target_width = self.right.target_width = 37.0
            self.left.target_height = self.right.target_height = 32.0
            self.left.target_upper_lid_l, self.left.target_upper_lid_r = 2.0, 14.0
            self.right.target_upper_lid_l, self.right.target_upper_lid_r = 14.0, 2.0
            self.left.target_lower_lid = self.right.target_lower_lid = 4.0
            self.left.target_lower_arch = self.right.target_lower_arch = 7.0
            self.left.target_pupil_dx = self.right.target_pupil_dx = 5.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 5.5
            self.left.target_brow_offset = self.right.target_brow_offset = 4.5
            self.left.target_brow_tilt, self.right.target_brow_tilt = 4.5, -4.5
            self.left.target_x, self.right.target_x = float(self.left.base_x + 3), float(self.right.base_x + 3)
        elif e == Expression.SLEEPING:
            self.left.target_width = self.right.target_width = 34.0
            self.left.target_height = self.right.target_height = 24.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 0.0
            self.left.target_brow_offset = self.right.target_brow_offset = 0.0
            self.left.target_y = self.right.target_y = float(self.left.base_y + 3)

    def _update_blinker(self, now_ms: int, dt_sec: float) -> None:
        if self.expr in (Expression.WINK, Expression.SLEEPING, Expression.HAPPY):
            self.blink_phase = "OPEN"
            self.left.blink_squeeze = self.right.blink_squeeze = 0.0
            return
        speed = self._profile_speed_scale()
        close_rate = (6.0 if self.expr == Expression.SLEEPY else (24.0 if self.expr == Expression.SURPRISED else 18.0)) * speed
        open_rate = (4.2 if self.expr == Expression.SLEEPY else (18.0 if self.expr == Expression.SURPRISED else 14.0)) * speed

        if self.blink_phase == "OPEN":
            if now_ms >= self.next_blink_ms:
                self.blink_phase = "CLOSING"
                if self.expr == Expression.IDLE and not self.double_blink_pending:
                    dbl = 28 if self.profile == VisualProfile.PLAYFUL else (8 if self.profile == VisualProfile.CALM else 20)
                    self.double_blink_pending = self._rand_range(0, 99) < dbl
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
                    self.next_blink_ms = now_ms + _clamp_int(int(self._rand_range(lo, hi) / self._profile_blink_freq_scale()), 1200, 8000)

    def _update_gaze(self, now_ms: int) -> None:
        if not self.auto_idle_gaze or now_ms < self.gaze_override_until_ms:
            return
        if self.expr in (Expression.THINKING, Expression.CURIOUS, Expression.SURPRISED, Expression.SHY, Expression.LOVE, Expression.WINK, Expression.CONFUSED, Expression.MISCHIEVOUS, Expression.SLEEPING, Expression.HAPPY):
            return
        if now_ms < self.next_gaze_ms:
            return
        if self.expr == Expression.LISTENING:
            micro = self._rand_range(0, 99) < 35
            pdx = self._rand_range(-1, 1) if micro else 0
            pdy = self._rand_range(-1, 0) if micro else 0
            self.left.target_pupil_dx = self.right.target_pupil_dx = float(pdx)
            self.left.target_pupil_dy = self.right.target_pupil_dy = float(pdy)
            self.next_gaze_ms = now_ms + self._rand_range(1400, 2800)
            return

        roll = self._rand_range(0, 99)
        return_center = roll < 38
        do_micro = (not return_center) and (roll < 70)
        dx = self._rand_range(-3, 3) if do_micro else (0 if return_center else self._rand_range(-8, 8))
        dy = self._rand_range(-2, 2) if do_micro else (0 if return_center else self._rand_range(-4, 4))
        self.gaze_is_micro = do_micro
        self.left.target_x = float(self.left.base_x) + float(dx) * 0.40
        self.right.target_x = float(self.right.base_x) + float(dx) * 0.40
        self.left.target_y = float(self.left.base_y) + float(dy) * 0.35
        self.right.target_y = float(self.right.base_y) + float(dy) * 0.35
        self.left.target_pupil_dx = self.right.target_pupil_dx = float(dx) * 0.65
        self.left.target_pupil_dy = self.right.target_pupil_dy = float(dy) * 0.55
        base_wait = self._rand_range(650, 1300) if do_micro else self._rand_range(1600, 3600)
        self.next_gaze_ms = now_ms + _clamp_int(int(base_wait / self._profile_gaze_freq_scale()), 500, 6000)

    def _update_micro_expressions(self, now_ms: int) -> None:
        if self.micro_expr != MicroExprType.NONE and now_ms >= self.micro_expr_until_ms:
            self.micro_expr = MicroExprType.NONE
            self._apply_expression_targets()
        if not self.micro_expressions_enabled or now_ms < self.gaze_override_until_ms or self.blink_phase != "OPEN":
            return
        if self.expr in (Expression.SLEEPING, Expression.LOVE, Expression.SURPRISED, Expression.WINK, Expression.HAPPY):
            return
        if self.micro_expr == MicroExprType.NONE and now_ms >= self.next_micro_expr_ms:
            r = self._rand_range(0, 99)
            if r < 30:
                self.micro_expr = MicroExprType.BROW_RAISE
                self.right.target_brow_offset += 3.0
                self.right.target_brow_tilt -= 2.0
                self.micro_expr_until_ms = now_ms + 520
            elif r < 60:
                self.micro_expr = MicroExprType.SIDE_GLANCE
                d = -4.0 if self._rand_range(0, 1) == 0 else 4.0
                self.left.target_pupil_dx += d
                self.right.target_pupil_dx += d
                self.micro_expr_until_ms = now_ms + 460
            elif r < 85:
                self.micro_expr = MicroExprType.PUPIL_PULSE
                self.left.target_pupil_radius += 1.2
                self.right.target_pupil_radius += 1.2
                self.micro_expr_until_ms = now_ms + 420
            else:
                self.micro_expr = MicroExprType.EYE_SMILE
                self.left.target_lower_lid += 3.0
                self.right.target_lower_lid += 3.0
                self.left.target_lower_arch += 4.0
                self.right.target_lower_arch += 4.0
                self.micro_expr_until_ms = now_ms + 560
            self.next_micro_expr_ms = now_ms + _clamp_int(int(self._rand_range(3600, 7400) / self._profile_micro_freq_scale()), 1800, 14000)

    def _update_expression_motion(self, now_ms: int) -> None:
        t = (now_ms - self.expr_start_ms) * 0.001
        if self.expr == Expression.IDLE:
            self.left.target_height = self.right.target_height = 38.0 + 0.8 * math.sin(t * 1.4)
        elif self.expr == Expression.HAPPY:
            self.left.target_y = self.right.target_y = float(self.left.base_y + 1) + math.sin(t * 3.5) * 1.2
        elif self.expr == Expression.LISTENING:
            self.left.target_height = self.right.target_height = 41.5 + 1.2 * math.sin(t * 3.0)
        elif self.expr == Expression.SPEAKING:
            env = 0.5 + 0.35 * math.sin(t * 6.8) + 0.15 * math.sin(t * 10.7)
            self.left.target_height = self.right.target_height = 32.0 + 5.0 * env
            self.left.target_lower_lid = self.right.target_lower_lid = 2.0 + 3.5 * (1.0 - env)
        elif self.expr == Expression.LOVE:
            beat = abs(math.sin(t * 3.8)) * 1.8
            self.left.target_y = self.right.target_y = float(self.left.base_y) - beat
        elif self.expr == Expression.SLEEPING:
            self.left.target_y = self.right.target_y = float(self.left.base_y + 3) + math.sin(t * 0.9)

    def update_step(self, now_ms: int) -> None:
        dt_ms = _clamp_int((now_ms - self.last_frame_ms) if now_ms >= self.last_frame_ms else self.frame_interval_ms, 1, 100)
        dt_sec = dt_ms * 0.001
        self.actual_fps = self.actual_fps * 0.85 + (1000.0 / float(dt_ms)) * 0.15
        self.last_frame_ms = now_ms

        self._update_blinker(now_ms, dt_sec)
        self._update_gaze(now_ms)
        self._update_micro_expressions(now_ms)
        self._update_expression_motion(now_ms)

        mult = self._profile_speed_scale() * self.transition_boost
        for eye in (self.left, self.right):
            eye.x = _smooth_exp(eye.x, eye.target_x, 12.0 * mult, dt_sec)
            eye.y = _smooth_exp(eye.y, eye.target_y, 12.0 * mult, dt_sec)
            eye.width = _smooth_exp(eye.width, eye.target_width, 10.0 * mult, dt_sec)
            eye.height = _smooth_exp(eye.height, eye.target_height, 10.0 * mult, dt_sec)
            eye.shape_power = _smooth_exp(eye.shape_power, eye.target_shape_power, 10.0 * mult, dt_sec)
            eye.taper = _smooth_exp(eye.taper, eye.target_taper, 10.0 * mult, dt_sec)
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
        self.transition_boost = _smooth_exp(self.transition_boost, 1.0, 6.0, dt_sec)

        t0 = time.perf_counter_ns()
        self.render_frame(now_ms)
        self.last_render_us = (time.perf_counter_ns() - t0) // 1000

    def _draw_organic_eye(self, eye: EyeState30) -> None:
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

        x0 = cx - w // 2
        y0 = cy - h // 2

        if eye.blink_squeeze < 0.65:
            half_w = (w - 1) * 0.5
            if eye.lower_lid > 0.4 or eye.lower_arch > 0.4:
                for col in range(w):
                    u = ((col - half_w) / half_w) if half_w > 0.0 else 0.0
                    mask_top = _round_half_away((y0 + h) - eye.lower_lid - eye.lower_arch * (1.0 - u * u))
                    for py in range(mask_top, y0 + h + 2):
                        self.fb.set_pixel(x0 + col, py, 0)
            if eye.upper_lid_l > 0.4 or eye.upper_lid_r > 0.4 or eye.upper_arch > 0.4:
                for col in range(w):
                    frac = (col / float(w - 1)) if w > 1 else 0.5
                    u = ((col - half_w) / half_w) if half_w > 0.0 else 0.0
                    lid_y = eye.upper_lid_l + (eye.upper_lid_r - eye.upper_lid_l) * frac
                    mask_bot = _round_half_away(y0 + lid_y + eye.upper_arch * (1.0 - u * u))
                    for py in range(y0 - 2, mask_bot + 1):
                        self.fb.set_pixel(x0 + col, py, 0)
                    # Heavy sleepy/focused lash rim for 3.0 readability
                    if max(eye.upper_lid_l, eye.upper_lid_r) >= 12.0 and 4 <= mask_bot <= HEIGHT - 6:
                        self.fb.set_pixel(x0 + col, mask_bot + 1, 1)

        # Proportional dark pupil + dual futuristic catchlights
        if eye.blink_squeeze < 0.45 and eye.pupil_radius >= 2.5:
            pr = _clamp_int(_round_half_away(eye.pupil_radius), 3, max(3, min(w, h) // 2 - 4))
            top_mask = _round_half_away(max(eye.upper_lid_l, eye.upper_lid_r) + eye.upper_arch * 0.5)
            bot_mask = _round_half_away(eye.lower_lid + eye.lower_arch * 0.5)
            min_px, max_px = x0 + pr + 4, x0 + w - 1 - pr - 4
            min_py, max_py = y0 + top_mask + pr + 2, y0 + h - 1 - bot_mask - pr - 2
            if min_px <= max_px and min_py <= max_py:
                px = _clamp_int(_round_half_away(cx + eye.pupil_dx), min_px, max_px)
                py = _clamp_int(_round_half_away(cy + eye.pupil_dy), min_py, max_py)
                self.fb.fill_circle(px, py, pr, 0)
                # Primary crisp 2x2 catchlight
                gx, gy = px - (pr // 2) + 1, py - (pr // 2) + 1
                self.fb.set_pixel(gx, gy, 1)
                self.fb.set_pixel(gx + 1, gy, 1)
                self.fb.set_pixel(gx, gy + 1, 1)
                self.fb.set_pixel(gx + 1, gy + 1, 1)
                # Secondary futuristic tech glint
                if pr >= 5:
                    self.fb.set_pixel(px + (pr // 2) - 1, py + (pr // 2) - 1, 1)

        # Sculpted tapered eyebrow integrated over the eye dome
        if eye.brow_offset >= 1.0 and eye.blink_squeeze < 0.70:
            bw = _clamp_int(w - 6, 14, 34)
            bx0 = _clamp_int(cx - bw // 2, 4, WIDTH - bw - 4)
            by_base = _clamp_int(y0 - _round_half_away(eye.brow_offset), 4, HEIGHT - 8)
            for col in range(bw):
                frac = (col / float(bw - 1)) if bw > 1 else 0.5
                u = (frac - 0.5) * 2.0
                arch = eye.brow_arch * (1.0 - u * u)
                tilt = eye.brow_tilt * (frac - 0.5)
                py = _clamp_int(_round_half_away(float(by_base) + tilt - arch), 4, HEIGHT - 6)
                thick = 3 if abs(u) < 0.55 else 2
                for t in range(thick):
                    self.fb.set_pixel(bx0 + col, py + t, 1)

    def _draw_happy_crescent(self, eye: EyeState30) -> None:
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
        # Sculpted happy brow above
        bw = 26
        bx0 = cx - bw // 2
        by0 = max(5, cy - 15)
        for col in range(bw):
            u = (col / float(bw - 1) - 0.5) * 2.0
            py = max(4, by0 - _round_half_away(3.0 * (1.0 - u * u)))
            self.fb.set_pixel(bx0 + col, py, 1)
            self.fb.set_pixel(bx0 + col, py + 1, 1)

    def _draw_plump_heart(self, cx: int, cy: int) -> None:
        # Smooth 28x28 heart with full rounded top lobes & glossy catchlight
        cx = _clamp_int(cx, 18, WIDTH - 18)
        cy = _clamp_int(cy, 18, HEIGHT - 18)
        for dy in range(-14, 14):
            for dx in range(-14, 15):
                nx = dx / 11.5
                ny = -(dy + 1.5) / 10.5
                val = (nx * nx + ny * ny - 1.0) ** 3 - (nx * nx) * (ny ** 3)
                if val <= 0.0:
                    self.fb.set_pixel(cx + dx, cy + dy, 1)
        # Glossy catchlight on left lobe
        self.fb.set_pixel(cx - 6, cy - 5, 0)
        self.fb.set_pixel(cx - 5, cy - 5, 0)
        self.fb.set_pixel(cx - 6, cy - 4, 0)

    def _draw_sleeping_lash(self, eye: EyeState30) -> None:
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
            # Cheerful cheek sparkles
            for cx in (_round_half_away(self.left.x) - 14, _round_half_away(self.right.x) + 14):
                self.fb.set_pixel(cx, 48, 1)
                self.fb.set_pixel(cx + 1, 47, 1)
                self.fb.set_pixel(cx + 2, 48, 1)
            return
        if self.expr == Expression.WINK:
            self._draw_organic_eye(self.left)
            self._draw_happy_crescent(self.right)
            return
        if self.expr == Expression.SLEEPING:
            self._draw_sleeping_lash(self.left)
            self._draw_sleeping_lash(self.right)
            phase = (now_ms // 450) % 3
            z_small = ["1111", "..1.", ".1..", "1111"]
            z_big = ["11111", "...1.", "..1..", ".1...", "11111"]
            for r, row in enumerate(z_small):
                for c, ch in enumerate(row):
                    if ch == "1":
                        self.fb.set_pixel(98 + c, 14 - phase + r, 1)
            for r, row in enumerate(z_big):
                for c, ch in enumerate(row):
                    if ch == "1":
                        self.fb.set_pixel(106 + c, 7 - phase + r, 1)
            return

        self._draw_organic_eye(self.left)
        self._draw_organic_eye(self.right)

        if self.expr == Expression.LISTENING:
            r = 2 if ((now_ms // 280) % 2 == 0) else 1
            self.fb.fill_circle(WIDTH // 2, HEIGHT - 4, r, 1)
        elif self.expr == Expression.THINKING:
            act = (now_ms // 300) % 3
            for i in range(3):
                dx = (WIDTH // 2 - 8) + i * 8
                if i == act:
                    self.fb.fill_circle(dx, HEIGHT - 4, 2, 1)
                else:
                    self.fb.draw_circle(dx, HEIGHT - 4, 1, 1)
        elif self.expr == Expression.SHY:
            for cx in (_round_half_away(self.left.x) - 10, _round_half_away(self.right.x) + 10):
                for off in (-4, 0, 4):
                    self.fb.set_pixel(cx + off, 53, 1)
                    self.fb.set_pixel(cx + off + 1, 52, 1)
        elif self.expr == Expression.CONFUSED:
            q = [".111.", "1...1", "...1.", "..1..", "..1..", ".....", "..1.."]
            for r, row in enumerate(q):
                for c, ch in enumerate(row):
                    if ch == "1":
                        self.fb.set_pixel(114 + c, 6 + r, 1)
        elif self.expr == Expression.SURPRISED:
            b = ["11", "11", "11", "11", "..", "11"]
            for r, row in enumerate(b):
                for c, ch in enumerate(row):
                    if ch == "1":
                        self.fb.set_pixel(WIDTH // 2 - 1 + c, 6 + r, 1)
