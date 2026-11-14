"""Automated regression & verification tests for JARVIS AI Desk Buddy Windows Simulator."""

import unittest

from eye_engine import ALL_EXPRESSIONS, EyeEngine, Expression, SimulatorStateMachine
from monochrome_fb import BUFFER_SIZE, HEIGHT, WIDTH


class TestJarvisSimulator(unittest.TestCase):
    def test_framebuffer_resolution_128x64(self) -> None:
        eyes = EyeEngine(fps=50, spacing_px=16)
        self.assertEqual(WIDTH, 128)
        self.assertEqual(HEIGHT, 64)
        self.assertEqual(len(eyes.fb.buf), BUFFER_SIZE)
        self.assertGreater(eyes.fb.count_lit_pixels(), 400)

    def test_safe_margins_no_edge_clipping(self) -> None:
        """Verify eyes never touch extreme screen edges across all expressions."""
        eyes = EyeEngine(fps=50, spacing_px=16, seed=12345)
        eyes.auto_idle_gaze = False
        now = 0
        for expr in ALL_EXPRESSIONS:
            eyes.set_expression(expr, now_ms=now)
            for _ in range(45):
                now += 20
                eyes.update(now, force=True)
            # Extreme columns x=0..2 and x=125..127 must remain black
            for y in range(HEIGHT):
                for x in (0, 1, 2, WIDTH - 3, WIDTH - 2, WIDTH - 1):
                    self.assertEqual(
                        eyes.fb.get_pixel(x, y),
                        0,
                        f"Pixel clipped at ({x},{y}) in {expr}",
                    )
            # Top rows y=0..2 must remain black
            for y in (0, 1, 2):
                for x in range(WIDTH):
                    self.assertEqual(
                        eyes.fb.get_pixel(x, y),
                        0,
                        f"Top pixel clipped at ({x},{y}) in {expr}",
                    )

    def test_all_expressions_selectable_and_distinct(self) -> None:
        eyes = EyeEngine(fps=50, spacing_px=16, seed=42)
        eyes.auto_idle_gaze = False
        sm = SimulatorStateMachine(eyes, auto_demo=False)
        snapshots = {}
        now = 0
        max_allowed_lit = int(WIDTH * HEIGHT * 0.40)  # Avoid giant static white blocks
        for expr in ALL_EXPRESSIONS:
            sm.set_expression(expr, now_ms=now, disable_auto=True)
            for _ in range(40):
                now += 20
                eyes.update(now, force=True)
            lit = eyes.fb.count_lit_pixels()
            self.assertGreater(lit, 200, f"Expression {expr} rendered too few pixels")
            self.assertLess(lit, max_allowed_lit, f"Expression {expr} rendered too many pixels")
            snapshots[expr] = bytes(eyes.fb.buf)
        self.assertEqual(len(set(snapshots.values())), len(ALL_EXPRESSIONS))

    def test_blink_cycle_closes_to_thin_line_and_reopens(self) -> None:
        eyes = EyeEngine(fps=50, spacing_px=16, seed=99)
        eyes.auto_idle_gaze = False
        open_pixels = eyes.fb.count_lit_pixels()
        eyes.trigger_blink(100)
        min_pixels = open_pixels
        now = 100
        for _ in range(15):
            now += 20
            eyes.update(now, force=True)
            min_pixels = min(min_pixels, eyes.fb.count_lit_pixels())
        # Closed line ~60*2 = ~120 px, well below 25% of open eyes
        self.assertLess(min_pixels, open_pixels * 0.25, "Eyes did not close to thin line during blink")
        for _ in range(20):
            now += 20
            eyes.update(now, force=True)
        self.assertGreater(eyes.fb.count_lit_pixels(), open_pixels * 0.85, "Eyes did not reopen")

    def test_fps_independent_interpolation(self) -> None:
        """25 FPS (40ms steps) and 50 FPS (20ms steps) must converge to nearly identical states."""
        e_50 = EyeEngine(fps=50, spacing_px=16, seed=777)
        e_25 = EyeEngine(fps=25, spacing_px=16, seed=777)
        e_50.auto_idle_gaze = False
        e_25.auto_idle_gaze = False

        e_50.set_expression(Expression.HAPPY, now_ms=0)
        e_25.set_expression(Expression.HAPPY, now_ms=0)

        for t in range(20, 420, 20):
            e_50.update_step(t)
        for t in range(40, 440, 40):
            e_25.update_step(t)

        self.assertAlmostEqual(e_50.left.y, e_25.left.y, delta=0.8)
        self.assertAlmostEqual(e_50.left.lower_arch, e_25.left.lower_arch, delta=0.8)
        self.assertAlmostEqual(e_50.left.width, e_25.left.width, delta=0.8)

    def test_deterministic_seed_reproducibility(self) -> None:
        a = EyeEngine(fps=50, spacing_px=16, seed=2026)
        b = EyeEngine(fps=50, spacing_px=16, seed=2026)
        for t in range(20, 4000, 20):
            a.update_step(t)
            b.update_step(t)
        self.assertEqual(bytes(a.fb.buf), bytes(b.fb.buf))

    def test_serial_commands(self) -> None:
        eyes = EyeEngine(fps=50, spacing_px=16)
        sm = SimulatorStateMachine(eyes, auto_demo=True)
        self.assertEqual(sm.handle_command("PING", 10), "PONG")
        self.assertEqual(sm.handle_command("STATE:THINKING", 20), "EVENT:STATE=THINKING")
        self.assertEqual(eyes.expr, Expression.THINKING)
        self.assertFalse(sm.auto_demo)
        self.assertEqual(sm.handle_command("LOOK:10,-4", 30), "OK:LOOK")
        self.assertEqual(sm.handle_command("AUTO:ON", 40), "OK:AUTO=ON")
        self.assertTrue(sm.auto_demo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
