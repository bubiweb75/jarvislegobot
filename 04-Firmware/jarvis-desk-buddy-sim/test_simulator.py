"""Automated regression & verification tests for JARVIS AI Desk Buddy Windows Simulator."""

import unittest

from emotion_engine import EmotionConfig, EmotionEngine, StimulusType, detect_text_stimulus
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

    def test_all_14_serial_state_commands(self) -> None:
        self.assertEqual(len(ALL_EXPRESSIONS), 14)
        eyes = EyeEngine(fps=50, spacing_px=16)
        sm = SimulatorStateMachine(eyes, auto_demo=False)
        for idx, expr in enumerate(ALL_EXPRESSIONS):
            resp = sm.handle_command(f"STATE:{expr.value}", (idx + 1) * 50)
            self.assertEqual(resp, f"EVENT:STATE={expr.value}")
            self.assertEqual(eyes.expr, expr)


class TestEmotionEngine(unittest.TestCase):
    def test_priority_preemption_and_return_to_idle(self) -> None:
        eng = EmotionEngine(seed=101)
        d1 = eng.push_stimulus(StimulusType.GREETING, now_ms=100)
        self.assertIsNotNone(d1)
        self.assertIn(d1.expression, (Expression.HAPPY, Expression.WINK))

        # Higher-priority SUDDEN_NOISE must preempt active GREETING immediately
        d2 = eng.push_stimulus(StimulusType.SUDDEN_NOISE, now_ms=300)
        self.assertIsNotNone(d2)
        self.assertEqual(d2.expression, Expression.SURPRISED)
        self.assertEqual(eng.current_expression, Expression.SURPRISED)

        # After duration expires, engine returns to IDLE
        eng.tick(now_ms=300 + d2.duration_ms + 50)
        self.assertEqual(eng.current_expression, Expression.IDLE)

    def test_cooldown_prevents_spam(self) -> None:
        eng = EmotionEngine(seed=102)
        first = eng.push_stimulus(StimulusType.SUDDEN_NOISE, now_ms=1000)
        self.assertIsNotNone(first)
        second = eng.push_stimulus(StimulusType.SUDDEN_NOISE, now_ms=2000)
        self.assertIsNone(second)
        # After cooldown (6000ms), stimulus works again
        third = eng.push_stimulus(StimulusType.SUDDEN_NOISE, now_ms=7200)
        self.assertIsNotNone(third)

    def test_conversation_busy_suppresses_spontaneous(self) -> None:
        cfg = EmotionConfig(spontaneous_interval_ms=1000)
        eng = EmotionEngine(config=cfg, seed=103)
        eng.set_conversation_busy(True, now_ms=100, phase_expr=Expression.LISTENING)
        self.assertEqual(eng.current_expression, Expression.LISTENING)
        self.assertIsNone(eng.tick(now_ms=5000))
        self.assertEqual(eng.current_expression, Expression.LISTENING)
        eng.set_conversation_busy(False, now_ms=5100)
        self.assertEqual(eng.current_expression, Expression.IDLE)

    def test_inactivity_sleepy_sleeping_and_wakeup(self) -> None:
        cfg = EmotionConfig(
            spontaneous_enabled=False,
            inactivity_sleepy_ms=5000,
            inactivity_sleeping_ms=12000,
        )
        eng = EmotionEngine(config=cfg, seed=104)
        eng.tick(now_ms=5200)
        self.assertEqual(eng.current_expression, Expression.SLEEPY)
        eng.tick(now_ms=16000)
        self.assertTrue(eng.is_sleeping)
        self.assertEqual(eng.current_expression, Expression.SLEEPING)

        wake = eng.touch_activity(now_ms=17000)
        self.assertIsNotNone(wake)
        self.assertFalse(eng.is_sleeping)
        self.assertEqual(eng.current_expression, Expression.HAPPY)

    def test_silent_mode_and_reproducible_seed(self) -> None:
        cfg = EmotionConfig(silent_mode=True)
        eng = EmotionEngine(config=cfg, seed=2026)
        dec = eng.push_stimulus(StimulusType.COMPLIMENT, now_ms=100)
        self.assertIsNotNone(dec)
        self.assertIn(dec.expression, (Expression.LOVE, Expression.SHY))
        self.assertIsNone(dec.voice_line)

        a = EmotionEngine(seed=999)
        b = EmotionEngine(seed=999)
        da = a.push_stimulus(StimulusType.JOKE, now_ms=100)
        db = b.push_stimulus(StimulusType.JOKE, now_ms=100)
        self.assertEqual(da.expression, db.expression)
        self.assertEqual(da.voice_line, db.voice_line)

    def test_text_stimulus_detection_and_error(self) -> None:
        self.assertEqual(detect_text_stimulus("Ciao Jarvis!"), StimulusType.GREETING)
        self.assertEqual(detect_text_stimulus("Sei bravissimo, grazie!"), StimulusType.COMPLIMENT)
        self.assertEqual(detect_text_stimulus("Ahah che battuta!"), StimulusType.JOKE)
        self.assertEqual(detect_text_stimulus("Come funziona il motore?"), StimulusType.QUESTION)

        eng = EmotionEngine(seed=55)
        err = eng.push_stimulus(StimulusType.TEMP_ERROR, now_ms=500)
        self.assertIsNotNone(err)
        self.assertEqual(err.expression, Expression.CONFUSED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
