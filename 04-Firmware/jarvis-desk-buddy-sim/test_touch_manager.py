"""Automated tests for FASE 11.1 TouchManager & StateMachine touch reactions.

Mirrors the exact non-blocking state machine in:
  - 04-Firmware/jarvis-desk-buddy/src/touch_manager.cpp
  - 04-Firmware/jarvis-desk-buddy/src/state_machine.cpp (JARVIS_ENABLE_TOUCH)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import unittest

from eye_engine import Expression, EyeEngine, SimulatorStateMachine


class TouchEvent(str, Enum):
    NONE = "NONE"
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    LONG = "LONG"


@dataclass
class TouchConfig:
    active_high: bool = True
    debounce_ms: int = 40
    double_tap_window_ms: int = 350
    long_press_ms: int = 1200


@dataclass
class TouchUpdateResult:
    event: TouchEvent = TouchEvent.NONE
    released: bool = False
    is_pressed: bool = False


class TouchManagerMirror:
    """1:1 Python mirror of C++ jarvis::touch::TouchManager."""

    def __init__(self, initial_raw_level: bool = False, config: TouchConfig | None = None) -> None:
        self.config = config or TouchConfig()
        self.enabled = True
        active = self.config.active_high if initial_raw_level else (not self.config.active_high)
        if not initial_raw_level and self.config.active_high:
            active = False
        elif initial_raw_level and not self.config.active_high:
            active = False
        else:
            active = True
        self.last_raw_active = active
        self.stable_active = active
        self.last_change_ms = 0
        self.press_start_ms = 0
        self.first_release_ms = 0
        self.long_fired = False
        self.waiting_second_tap = False

    def update(self, raw_level: bool, now_ms: int) -> TouchUpdateResult:
        out = TouchUpdateResult()
        if not self.enabled:
            return out

        raw_active = raw_level if self.config.active_high else (not raw_level)
        if raw_active != self.last_raw_active:
            self.last_raw_active = raw_active
            self.last_change_ms = now_ms

        if (now_ms - self.last_change_ms) >= self.config.debounce_ms and raw_active != self.stable_active:
            self.stable_active = raw_active
            if self.stable_active:
                self.press_start_ms = now_ms
                self.long_fired = False
            else:
                out.released = True
                if not self.long_fired:
                    if self.waiting_second_tap and (now_ms - self.first_release_ms) <= self.config.double_tap_window_ms:
                        self.waiting_second_tap = False
                        out.event = TouchEvent.DOUBLE
                    else:
                        self.waiting_second_tap = True
                        self.first_release_ms = now_ms
                else:
                    self.waiting_second_tap = False

        if self.stable_active and not self.long_fired and (now_ms - self.press_start_ms) >= self.config.long_press_ms:
            self.long_fired = True
            self.waiting_second_tap = False
            out.event = TouchEvent.LONG

        if not self.stable_active and self.waiting_second_tap and (now_ms - self.first_release_ms) > self.config.double_tap_window_ms:
            self.waiting_second_tap = False
            out.event = TouchEvent.SINGLE

        out.is_pressed = self.stable_active
        return out


class TouchReactionHarness:
    """1:1 mirror of StateMachine touch integration + GPIO47 coexistence."""

    def __init__(self, auto_demo: bool = True) -> None:
        self.eyes = EyeEngine(fps=30, spacing_px=12, seed=2026)
        self.sm = SimulatorStateMachine(self.eyes, auto_demo=auto_demo)
        self.touch = TouchManagerMirror(initial_raw_level=False)
        self.touch_reaction_active = False
        self.touch_long_holding = False
        self.touch_reaction_until_ms = 0
        self.saved_expr = Expression.IDLE
        self.saved_auto_demo = auto_demo
        self.events: list[str] = []

    def step(self, raw_touch: bool, now_ms: int) -> None:
        res = self.touch.update(raw_touch, now_ms)
        if res.event == TouchEvent.SINGLE:
            self.events.append("EVENT:TOUCH_SINGLE")
            self._handle_touch(res.event, now_ms)
        elif res.event == TouchEvent.DOUBLE:
            self.events.append("EVENT:TOUCH_DOUBLE")
            self._handle_touch(res.event, now_ms)
        elif res.event == TouchEvent.LONG:
            self.events.append("EVENT:TOUCH_LONG")
            self._handle_touch(res.event, now_ms)
        if res.released:
            self.events.append("EVENT:TOUCH_RELEASE")
            if self.touch_reaction_active and self.touch_long_holding:
                self.touch_long_holding = False
                self.touch_reaction_until_ms = now_ms + 1800

        if self.touch_reaction_active and not self.touch_long_holding and now_ms >= self.touch_reaction_until_ms:
            self.touch_reaction_active = False
            self.sm.auto_demo = self.saved_auto_demo
            self.eyes.set_expression(self.saved_expr, now_ms)
            self.events.append(f"EVENT:TOUCH_RESTORE={self.saved_expr.value}")

    def press_gpio47_short(self, now_ms: int) -> None:
        """Simulates GPIO47 explicit expression cycle cancelling temporary touch reaction."""
        self.touch_reaction_active = False
        self.touch_long_holding = False
        self.sm.auto_demo = False
        self.sm.set_expression(Expression.CURIOUS, now_ms, disable_auto=True)

    def _handle_touch(self, ev: TouchEvent, now_ms: int) -> None:
        cur = self.eyes.expr
        if cur in (Expression.LISTENING, Expression.THINKING, Expression.SPEAKING):
            self.events.append("EVENT:TOUCH_IGNORED=BUSY")
            return
        if not self.touch_reaction_active:
            self.saved_expr = Expression.IDLE if cur in (Expression.SLEEPING, Expression.SLEEPY) else cur
            self.saved_auto_demo = self.sm.auto_demo
            self.sm.auto_demo = False
            self.touch_reaction_active = True

        if ev == TouchEvent.SINGLE:
            self.touch_long_holding = False
            self.touch_reaction_until_ms = now_ms + 2200
            self.eyes.set_expression(Expression.HAPPY, now_ms)
            self.events.append("EVENT:TOUCH_REACTION=HAPPY")
        elif ev == TouchEvent.DOUBLE:
            self.touch_long_holding = False
            self.touch_reaction_until_ms = now_ms + 2600
            self.eyes.set_expression(Expression.MISCHIEVOUS, now_ms)
            self.events.append("EVENT:TOUCH_REACTION=MISCHIEVOUS")
        elif ev == TouchEvent.LONG:
            self.touch_long_holding = True
            self.touch_reaction_until_ms = now_ms + 2500
            self.eyes.set_expression(Expression.LOVE, now_ms)
            self.events.append("EVENT:TOUCH_REACTION=LOVE")


class TestTouchManager(unittest.TestCase):
    def test_01_idle_no_events(self) -> None:
        tm = TouchManagerMirror()
        for t in range(0, 2000, 10):
            res = tm.update(False, t)
            self.assertEqual(res.event, TouchEvent.NONE)
            self.assertFalse(res.released)
            self.assertFalse(res.is_pressed)

    def test_02_bounce_rejected_under_40ms(self) -> None:
        tm = TouchManagerMirror()
        for t in range(0, 35, 5):
            res = tm.update(True, t)
            self.assertEqual(res.event, TouchEvent.NONE)
        # Drop back to False before 40 ms debounce settles
        for t in range(35, 600, 10):
            res = tm.update(False, t)
            self.assertEqual(res.event, TouchEvent.NONE)
            self.assertFalse(res.released)

    def test_03_single_tap_waits_for_double_window_no_duplicate(self) -> None:
        tm = TouchManagerMirror()
        events = []
        releases = 0
        for t in range(0, 1000, 10):
            raw = 50 <= t < 170  # 120 ms press
            res = tm.update(raw, t)
            if res.released:
                releases += 1
            if res.event != TouchEvent.NONE:
                events.append((t, res.event))
        self.assertEqual(releases, 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][1], TouchEvent.SINGLE)
        # Confirmed only after release_settled (210ms) + 350ms
        self.assertGreater(events[0][0], 170 + 40 + 350 - 1)

    def test_04_double_tap_suppresses_single(self) -> None:
        tm = TouchManagerMirror()
        events = []
        releases = 0
        for t in range(0, 1200, 10):
            raw = (50 <= t < 150) or (260 <= t < 360)
            res = tm.update(raw, t)
            if res.released:
                releases += 1
            if res.event != TouchEvent.NONE:
                events.append(res.event)
        self.assertEqual(releases, 2)
        self.assertEqual(events, [TouchEvent.DOUBLE])

    def test_05_long_press_and_release_no_single(self) -> None:
        tm = TouchManagerMirror()
        events = []
        releases = 0
        for t in range(0, 2200, 10):
            raw = 50 <= t < 1600
            res = tm.update(raw, t)
            if res.released:
                releases += 1
            if res.event != TouchEvent.NONE:
                events.append((t, res.event))
        self.assertEqual(releases, 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][1], TouchEvent.LONG)
        self.assertGreaterEqual(events[0][0], 50 + 40 + 1200)

    def test_06_rapid_triple_tap_produces_double_then_single(self) -> None:
        tm = TouchManagerMirror()
        events = []
        for t in range(0, 1800, 10):
            raw = (40 <= t < 120) or (210 <= t < 290) or (420 <= t < 500)
            res = tm.update(raw, t)
            if res.event != TouchEvent.NONE:
                events.append(res.event)
        self.assertEqual(events, [TouchEvent.DOUBLE, TouchEvent.SINGLE])

    def test_07_reactions_happy_mischievous_love_and_restore(self) -> None:
        h = TouchReactionHarness(auto_demo=True)
        # Single tap -> HAPPY -> restore IDLE + auto_demo=True
        for t in range(0, 3200, 10):
            h.step(50 <= t < 150, t)
        self.assertIn("EVENT:TOUCH_REACTION=HAPPY", h.events)
        self.assertIn("EVENT:TOUCH_RESTORE=IDLE", h.events)
        self.assertEqual(h.eyes.expr, Expression.IDLE)
        self.assertTrue(h.sm.auto_demo)

        # Double tap -> MISCHIEVOUS -> restore
        h.events.clear()
        for t in range(3200, 6800, 10):
            h.step((3250 <= t < 3350) or (3450 <= t < 3550), t)
        self.assertIn("EVENT:TOUCH_REACTION=MISCHIEVOUS", h.events)
        self.assertIn("EVENT:TOUCH_RESTORE=IDLE", h.events)

        # Long press -> LOVE while held -> tail 1800ms after release -> restore
        h.events.clear()
        for t in range(7000, 11500, 10):
            h.step(7050 <= t < 8600, t)
        self.assertIn("EVENT:TOUCH_REACTION=LOVE", h.events)
        self.assertIn("EVENT:TOUCH_RELEASE", h.events)
        self.assertIn("EVENT:TOUCH_RESTORE=IDLE", h.events)

    def test_08_priority_busy_conversation_ignored_and_sleep_wakeup(self) -> None:
        h = TouchReactionHarness(auto_demo=False)
        for busy_expr in (Expression.LISTENING, Expression.THINKING, Expression.SPEAKING):
            h.events.clear()
            h.sm.set_expression(busy_expr, 0, disable_auto=True)
            for t in range(0, 700, 10):
                h.step(20 <= t < 110, t)
            self.assertIn("EVENT:TOUCH_IGNORED=BUSY", h.events)
            self.assertEqual(h.eyes.expr, busy_expr)

        # Wakeup from SLEEPING restores to IDLE
        h.events.clear()
        h.sm.set_expression(Expression.SLEEPING, 1000, disable_auto=True)
        for t in range(1000, 4200, 10):
            h.step(1050 <= t < 1150, t)
        self.assertIn("EVENT:TOUCH_REACTION=HAPPY", h.events)
        self.assertIn("EVENT:TOUCH_RESTORE=IDLE", h.events)
        self.assertEqual(h.eyes.expr, Expression.IDLE)

    def test_09_coexistence_with_gpio47_cancels_reaction(self) -> None:
        h = TouchReactionHarness(auto_demo=True)
        for t in range(0, 700, 10):
            h.step(20 <= t < 110, t)
        self.assertEqual(h.eyes.expr, Expression.HAPPY)
        h.press_gpio47_short(750)
        self.assertEqual(h.eyes.expr, Expression.CURIOUS)
        for t in range(760, 3500, 10):
            h.step(False, t)
        # Must stay CURIOUS, NOT revert to IDLE from cancelled touch reaction
        self.assertEqual(h.eyes.expr, Expression.CURIOUS)


if __name__ == "__main__":
    unittest.main()
