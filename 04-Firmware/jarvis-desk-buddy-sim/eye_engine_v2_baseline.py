"""Frozen Eyes 2.0 Baseline for side-by-side visual comparison (128x64 monochrome).

Preserves the exact Eyes 2.0 rounded-rectangle + basic pupil/brow geometry
so Eyes 2.0 vs Eyes 3.0 comparisons use two genuinely distinct implementations.
"""

from dataclasses import dataclass
import math

from eye_engine import Expression, _clamp_int, _round_half_away, _smooth_exp
from monochrome_fb import HEIGHT, WIDTH, MonochromeFramebuffer


@dataclass
class _EyeState20:
    base_x: int = 0
    base_y: int = 0
    x: float = 0.0
    y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    width: float = 32.0
    height: float = 34.0
    target_width: float = 32.0
    target_height: float = 34.0
    corner_radius: float = 11.0
    target_corner_radius: float = 11.0
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
    pupil_radius: float = 6.0
    target_pupil_radius: float = 6.0
    brow_offset: float = 0.0
    target_brow_offset: float = 0.0
    brow_tilt: float = 0.0
    target_brow_tilt: float = 0.0
    blink_squeeze: float = 0.0


class EyeEngineV2Baseline:
    """Authentic Eyes 2.0 baseline engine (32x34 rounded-rect + basic pupil/brow)."""

    DEFAULT_EYE_WIDTH = 32
    DEFAULT_EYE_HEIGHT = 34
    DEFAULT_CORNER_RADIUS = 11

    def __init__(self, fps: int = 30, spacing_px: int = 14, seed: int = 2026) -> None:
        self.fb = MonochromeFramebuffer()
        self.left = _EyeState20()
        self.right = _EyeState20()
        self.expr = Expression.IDLE
        self.spacing_px = spacing_px
        self.frame_interval_ms = (1000 // fps) if fps > 0 else 33
        self.last_frame_ms = 0
        self.blink_phase = "OPEN"
        self.next_blink_ms = 2200
        self.blink_hold_until_ms = 0
        self.auto_idle_gaze = True
        self.next_gaze_ms = 2400
        self.gaze_override_until_ms = 0
        self.expr_start_ms = 0
        self._rng_state = seed & 0xFFFFFFFF or 0xA511E9B3

        total_w = self.DEFAULT_EYE_WIDTH + self.spacing_px + self.DEFAULT_EYE_WIDTH
        start_x = (WIDTH - total_w) // 2
        self.left.base_x = start_x + self.DEFAULT_EYE_WIDTH // 2
        self.right.base_x = start_x + self.DEFAULT_EYE_WIDTH + self.spacing_px + self.DEFAULT_EYE_WIDTH // 2
        self.left.base_y = self.right.base_y = HEIGHT // 2
        self.left.x = self.left.target_x = float(self.left.base_x)
        self.right.x = self.right.target_x = float(self.right.base_x)
        self.left.y = self.left.target_y = float(self.left.base_y)
        self.right.y = self.right.target_y = float(self.right.base_y)

        self._apply_targets()
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

    def set_expression(self, expr: Expression, now_ms: int = 0) -> None:
        if self.expr == expr:
            return
        self.expr = expr
        self.expr_start_ms = now_ms
        self._apply_targets()

    def trigger_blink(self, now_ms: int) -> None:
        if self.blink_phase == "OPEN":
            self.blink_phase = "CLOSING"
            self.next_blink_ms = now_ms + 3200

    def set_gaze_offset(self, dx: int, dy: int, hold_ms: int, now_ms: int) -> None:
        dx = _clamp_int(dx, -11, 11)
        dy = _clamp_int(dy, -6, 6)
        self.left.target_x = float(self.left.base_x) + float(dx) * 0.45
        self.right.target_x = float(self.right.base_x) + float(dx) * 0.45
        self.left.target_y = float(self.left.base_y) + float(dy) * 0.40
        self.right.target_y = float(self.right.base_y) + float(dy) * 0.40
        self.left.target_pupil_dx = self.right.target_pupil_dx = float(dx) * 0.55
        self.left.target_pupil_dy = self.right.target_pupil_dy = float(dy) * 0.45
        self.gaze_override_until_ms = now_ms + hold_ms

    def _apply_targets(self) -> None:
        for eye in (self.left, self.right):
            eye.target_width = float(self.DEFAULT_EYE_WIDTH)
            eye.target_height = float(self.DEFAULT_EYE_HEIGHT)
            eye.target_corner_radius = float(self.DEFAULT_CORNER_RADIUS)
            eye.target_lower_lid = eye.target_lower_arch = 0.0
            eye.target_upper_lid_l = eye.target_upper_lid_r = eye.target_upper_arch = 0.0
            eye.target_pupil_dx = eye.target_pupil_dy = 0.0
            eye.target_pupil_radius = 6.0
            eye.target_brow_offset = eye.target_brow_tilt = 0.0
            eye.target_x = float(eye.base_x)
            eye.target_y = float(eye.base_y)

        e = self.expr
        if e == Expression.HAPPY:
            self.left.target_width = self.right.target_width = 33.0
            self.left.target_height = self.right.target_height = 31.0
            self.left.target_corner_radius = self.right.target_corner_radius = 12.0
            self.left.target_lower_lid = self.right.target_lower_lid = 6.0
            self.left.target_lower_arch = self.right.target_lower_arch = 11.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 5.0
            self.left.target_pupil_dy = self.right.target_pupil_dy = -1.0
            self.left.target_brow_offset = self.right.target_brow_offset = 4.0
            self.left.target_y = self.right.target_y = float(self.left.base_y - 1)
        elif e == Expression.CURIOUS:
            self.left.target_width, self.left.target_height, self.left.target_corner_radius = 28.0, 27.0, 9.0
            self.left.target_upper_lid_l, self.left.target_upper_lid_r = 1.0, 5.0
            self.left.target_pupil_dx, self.left.target_brow_offset, self.left.target_brow_tilt = 3.0, 4.0, 1.5
            self.left.target_x, self.left.target_y = float(self.left.base_x + 3), float(self.left.base_y + 2)
            self.right.target_width, self.right.target_height, self.right.target_corner_radius = 34.0, 36.0, 12.0
            self.right.target_pupil_dx, self.right.target_pupil_dy, self.right.target_pupil_radius = 3.0, -1.0, 6.5
            self.right.target_brow_offset, self.right.target_brow_tilt = 5.0, -1.5
            self.right.target_x, self.right.target_y = float(self.right.base_x + 3), float(self.right.base_y - 2)
        elif e == Expression.SLEEPY:
            self.left.target_width = self.right.target_width = 31.0
            self.left.target_height = self.right.target_height = 28.0
            self.left.target_corner_radius = self.right.target_corner_radius = 10.0
            self.left.target_upper_lid_l = self.left.target_upper_lid_r = 12.0
            self.right.target_upper_lid_l = self.right.target_upper_lid_r = 12.0
            self.left.target_upper_arch = self.right.target_upper_arch = 2.5
            self.left.target_pupil_radius = self.right.target_pupil_radius = 4.5
            self.left.target_pupil_dy = self.right.target_pupil_dy = 2.0
            self.left.target_y = self.right.target_y = float(self.left.base_y + 4)
        elif e == Expression.LISTENING:
            self.left.target_width = self.right.target_width = 32.0
            self.left.target_height = self.right.target_height = 36.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 6.5
        elif e == Expression.THINKING:
            self.left.target_width = self.right.target_width = 30.0
            self.left.target_height = self.right.target_height = 29.0
            self.left.target_corner_radius = self.right.target_corner_radius = 10.0
            self.left.target_x, self.right.target_x = float(self.left.base_x + 5), float(self.right.base_x + 5)
            self.left.target_y, self.right.target_y = float(self.left.base_y - 4), float(self.right.base_y - 4)
            self.left.target_upper_lid_l, self.left.target_upper_lid_r = 4.0, 2.0
            self.right.target_lower_lid, self.right.target_lower_arch = 3.0, 3.0
            self.left.target_pupil_dx = self.right.target_pupil_dx = 4.0
            self.left.target_pupil_dy = self.right.target_pupil_dy = -2.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 5.0
            self.left.target_brow_offset, self.left.target_brow_tilt = 4.0, 2.0
            self.right.target_brow_offset, self.right.target_brow_tilt = 5.0, -1.0
        elif e == Expression.SPEAKING:
            self.left.target_width = self.right.target_width = 32.0
            self.left.target_height = self.right.target_height = 32.0
            self.left.target_lower_lid = self.right.target_lower_lid = 3.0
            self.left.target_lower_arch = self.right.target_lower_arch = 5.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 5.5
        elif e == Expression.SURPRISED:
            self.left.target_width = self.right.target_width = 34.0
            self.left.target_height = self.right.target_height = 38.0
            self.left.target_corner_radius = self.right.target_corner_radius = 13.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 4.0
            self.left.target_brow_offset = self.right.target_brow_offset = 5.0
            self.left.target_y = self.right.target_y = float(self.left.base_y - 1)
        elif e == Expression.SHY:
            self.left.target_width = self.right.target_width = 29.0
            self.left.target_height = self.right.target_height = 25.0
            self.left.target_corner_radius = self.right.target_corner_radius = 10.0
            self.left.target_upper_lid_l = self.left.target_upper_lid_r = 5.0
            self.right.target_upper_lid_l = self.right.target_upper_lid_r = 5.0
            self.left.target_pupil_dx = self.right.target_pupil_dx = -3.0
            self.left.target_pupil_dy = self.right.target_pupil_dy = 2.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 5.0
            self.left.target_brow_offset = self.right.target_brow_offset = 4.0
            self.left.target_brow_tilt, self.right.target_brow_tilt = -2.0, 2.0
            self.left.target_x, self.right.target_x = float(self.left.base_x - 3), float(self.right.base_x - 3)
            self.left.target_y = self.right.target_y = float(self.left.base_y + 4)
        elif e == Expression.LOVE:
            self.left.target_width = self.right.target_width = 30.0
            self.left.target_height = self.right.target_height = 30.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 0.0
            self.left.target_y = self.right.target_y = float(self.left.base_y - 1)
        elif e == Expression.WINK:
            self.left.target_brow_offset = 4.0
            self.left.target_y = float(self.left.base_y - 1)
            self.right.target_height, self.right.target_pupil_radius = 28.0, 0.0
            self.right.target_y = float(self.right.base_y + 1)
        elif e == Expression.CONFUSED:
            self.left.target_width, self.left.target_height = 27.0, 25.0
            self.left.target_upper_lid_l, self.left.target_upper_lid_r = 5.0, 2.0
            self.left.target_pupil_dx, self.left.target_pupil_radius = -2.0, 5.0
            self.left.target_brow_offset, self.left.target_brow_tilt = 4.0, 2.5
            self.left.target_y = float(self.left.base_y + 2)
            self.right.target_width, self.right.target_height, self.right.target_corner_radius = 33.0, 35.0, 12.0
            self.right.target_pupil_dx, self.right.target_pupil_dy = 2.0, -1.0
            self.right.target_brow_offset, self.right.target_brow_tilt = 5.0, -2.5
            self.right.target_y = float(self.right.base_y - 2)
        elif e == Expression.MISCHIEVOUS:
            self.left.target_width = self.right.target_width = 32.0
            self.left.target_height = self.right.target_height = 28.0
            self.left.target_corner_radius = self.right.target_corner_radius = 9.0
            self.left.target_upper_lid_l, self.left.target_upper_lid_r = 1.0, 8.0
            self.right.target_upper_lid_l, self.right.target_upper_lid_r = 8.0, 1.0
            self.left.target_lower_lid = self.right.target_lower_lid = 4.0
            self.left.target_lower_arch = self.right.target_lower_arch = 5.0
            self.left.target_pupil_dx = self.right.target_pupil_dx = 4.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 5.0
            self.left.target_brow_offset = self.right.target_brow_offset = 4.0
            self.left.target_brow_tilt, self.right.target_brow_tilt = 3.0, -3.0
            self.left.target_x, self.right.target_x = float(self.left.base_x + 4), float(self.right.base_x + 4)
        elif e == Expression.SLEEPING:
            self.left.target_width = self.right.target_width = 30.0
            self.left.target_height = self.right.target_height = 24.0
            self.left.target_pupil_radius = self.right.target_pupil_radius = 0.0
            self.left.target_y = self.right.target_y = float(self.left.base_y + 3)

    def update_step(self, now_ms: int) -> None:
        dt_ms = _clamp_int((now_ms - self.last_frame_ms) if now_ms >= self.last_frame_ms else self.frame_interval_ms, 1, 100)
        dt_sec = dt_ms * 0.001
        self.last_frame_ms = now_ms

        if self.expr in (Expression.WINK, Expression.SLEEPING):
            self.blink_phase = "OPEN"
            self.left.blink_squeeze = self.right.blink_squeeze = 0.0
        else:
            cr = 6.5 if self.expr == Expression.SLEEPY else 18.0
            op = 4.5 if self.expr == Expression.SLEEPY else 14.0
            if self.blink_phase == "OPEN" and now_ms >= self.next_blink_ms:
                self.blink_phase = "CLOSING"
            elif self.blink_phase == "CLOSING":
                self.left.blink_squeeze += cr * dt_sec
                self.right.blink_squeeze += cr * dt_sec
                if self.left.blink_squeeze >= 1.0:
                    self.left.blink_squeeze = self.right.blink_squeeze = 1.0
                    self.blink_phase = "HOLD_CLOSED"
                    self.blink_hold_until_ms = now_ms + 45
            elif self.blink_phase == "HOLD_CLOSED" and now_ms >= self.blink_hold_until_ms:
                self.blink_phase = "OPENING"
            elif self.blink_phase == "OPENING":
                self.left.blink_squeeze -= op * dt_sec
                self.right.blink_squeeze -= op * dt_sec
                if self.left.blink_squeeze <= 0.0:
                    self.left.blink_squeeze = self.right.blink_squeeze = 0.0
                    self.blink_phase = "OPEN"
                    self.next_blink_ms = now_ms + self._rand_range(2600, 5200)

        for eye in (self.left, self.right):
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
            eye.pupil_dx = _smooth_exp(eye.pupil_dx, eye.target_pupil_dx, 14.0, dt_sec)
            eye.pupil_dy = _smooth_exp(eye.pupil_dy, eye.target_pupil_dy, 14.0, dt_sec)
            eye.pupil_radius = _smooth_exp(eye.pupil_radius, eye.target_pupil_radius, 12.0, dt_sec)
            eye.brow_offset = _smooth_exp(eye.brow_offset, eye.target_brow_offset, 12.0, dt_sec)
            eye.brow_tilt = _smooth_exp(eye.brow_tilt, eye.target_brow_tilt, 12.0, dt_sec)

        self.render_frame(now_ms)

    def _draw_single_eye(self, eye: _EyeState20) -> None:
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
                    mask_top = _round_half_away((y + h) - eye.lower_lid - eye.lower_arch * (1.0 - u * u))
                    for py in range(mask_top, y + h + 2):
                        self.fb.set_pixel(x + col, py, 0)
            if eye.upper_lid_l > 0.4 or eye.upper_lid_r > 0.4 or eye.upper_arch > 0.4:
                for col in range(w):
                    frac = (col / float(w - 1)) if w > 1 else 0.5
                    u = ((col - half_w) / half_w) if half_w > 0.0 else 0.0
                    lid_y = eye.upper_lid_l + (eye.upper_lid_r - eye.upper_lid_l) * frac
                    mask_bot = _round_half_away(y + lid_y + eye.upper_arch * (1.0 - u * u))
                    for py in range(y - 1, mask_bot + 1):
                        self.fb.set_pixel(x + col, py, 0)

        if eye.blink_squeeze < 0.45 and eye.pupil_radius >= 2.5:
            pr = _clamp_int(_round_half_away(eye.pupil_radius), 2, max(2, min(w, h) // 2 - 3))
            top_mask = _round_half_away(max(eye.upper_lid_l, eye.upper_lid_r) + eye.upper_arch * 0.5)
            bot_mask = _round_half_away(eye.lower_lid + eye.lower_arch * 0.5)
            min_px, max_px = x + pr + 3, x + w - 1 - pr - 3
            min_py, max_py = y + top_mask + pr + 2, y + h - 1 - bot_mask - pr - 2
            if min_px <= max_px and min_py <= max_py:
                px = _clamp_int(_round_half_away(eye.x + eye.pupil_dx), min_px, max_px)
                py = _clamp_int(_round_half_away(eye.y + eye.pupil_dy), min_py, max_py)
                self.fb.fill_circle(px, py, pr, 0)
                gx, gy = px - (pr // 2) + 1, py - (pr // 2) + 1
                self.fb.set_pixel(gx, gy, 1)
                self.fb.set_pixel(gx + 1, gy, 1)
                self.fb.set_pixel(gx, gy + 1, 1)
                self.fb.set_pixel(gx + 1, gy + 1, 1)

        if eye.brow_offset >= 1.0 and eye.blink_squeeze < 0.70:
            bw = _clamp_int(w - 6, 10, 30)
            bx0 = _clamp_int(x + 3, 4, WIDTH - bw - 4)
            by_base = _clamp_int(y - _round_half_away(eye.brow_offset), 4, HEIGHT - 8)
            for col in range(bw):
                frac = (col / float(bw - 1)) if bw > 1 else 0.5
                u = (frac - 0.5) * 2.0
                py = _clamp_int(_round_half_away(float(by_base) + eye.brow_tilt * (frac - 0.5) - 1.5 * (1.0 - u * u)), 4, HEIGHT - 6)
                self.fb.set_pixel(bx0 + col, py, 1)
                self.fb.set_pixel(bx0 + col, py + 1, 1)

    def render_frame(self, now_ms: int) -> None:
        self.fb.clear()
        if self.expr == Expression.LOVE:
            pat = [".111...111.", "11111.11111", "11111111111", "11111111111", "11111111111", ".111111111.", "..1111111..", "...11111...", "....111....", ".....1....."]
            for eye in (self.left, self.right):
                ox = _clamp_int(_round_half_away(eye.x) - 11, 4, WIDTH - 26)
                oy = _clamp_int(_round_half_away(eye.y) - 10, 4, HEIGHT - 24)
                for r, row in enumerate(pat):
                    for c, ch in enumerate(row):
                        if ch == "1":
                            for sy in range(2):
                                for sx in range(2):
                                    self.fb.set_pixel(ox + c * 2 + sx, oy + r * 2 + sy, 1)
            return
        if self.expr == Expression.WINK:
            self._draw_single_eye(self.left)
            cx = _clamp_int(_round_half_away(self.right.x), 20, WIDTH - 20)
            cy = _clamp_int(_round_half_away(self.right.y), 14, HEIGHT - 14)
            for dx in range(-13, 14):
                u = dx / 13.0
                py = cy + 2 - _round_half_away(4.0 * (1.0 - u * u))
                for t in range(3):
                    self.fb.set_pixel(cx + dx, py + t, 1)
            return
        if self.expr == Expression.SLEEPING:
            for eye in (self.left, self.right):
                cx = _clamp_int(_round_half_away(eye.x), 20, WIDTH - 20)
                cy = _clamp_int(_round_half_away(eye.y), 14, HEIGHT - 14)
                for dx in range(-14, 15):
                    u = dx / 14.0
                    py = cy + _round_half_away(3.5 * (1.0 - u * u))
                    for t in range(4):
                        self.fb.set_pixel(cx + dx, py + t, 1)
            return
        self._draw_single_eye(self.left)
        self._draw_single_eye(self.right)
        if self.expr == Expression.LISTENING:
            self.fb.fill_circle(WIDTH // 2, HEIGHT - 4, 2 if ((now_ms // 280) % 2 == 0) else 1, 1)
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
                    self.fb.set_pixel(cx + off, 52, 1)
                    self.fb.set_pixel(cx + off + 1, 51, 1)
        elif self.expr == Expression.CONFUSED:
            q = [".111.", "1...1", "...1.", "..1..", "..1..", ".....", "..1.."]
            for r, row in enumerate(q):
                for c, ch in enumerate(row):
                    if ch == "1":
                        self.fb.set_pixel(112 + c, 6 + r, 1)
        elif self.expr == Expression.SURPRISED:
            b = ["11", "11", "11", "11", "..", "11"]
            for r, row in enumerate(b):
                for c, ch in enumerate(row):
                    if ch == "1":
                        self.fb.set_pixel(WIDTH // 2 - 1 + c, 6 + r, 1)
