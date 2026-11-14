"""Automated unit & integration tests for FASE 8.1 SensorManager (simulated clock, no real sleeps)."""

import math
import unittest

from emotion_engine import EmotionConfig, EmotionEngine, StimulusType
from eye_engine import Expression
from sensor_manager import (
    HardwareSensorProviderStub,
    SensorConfig,
    SensorManager,
    SensorReading,
    SensorType,
    SimulatedSensorProvider,
)


class TestSensorManager(unittest.TestCase):
    def _make_setup(self, seed: int = 2026):
        prov = SimulatedSensorProvider()
        emo_cfg = EmotionConfig(silent_mode=True, spontaneous_enabled=False)
        emo = EmotionEngine(config=emo_cfg, seed=seed)
        cfg = SensorConfig()
        mgr = SensorManager(provider=prov, emotion_engine=emo, config=cfg)
        return prov, emo, cfg, mgr

    def test_01_distance_threshold_hysteresis_and_stationary(self) -> None:
        prov, emo, cfg, mgr = self._make_setup()
        prov.distance_cm = 60.0
        self.assertEqual(mgr.update(100), [])

        # Approach into <= 25 cm and dwell >= 250 ms
        prov.distance_cm = 20.0
        self.assertEqual(mgr.update(200), [])
        self.assertEqual(mgr.update(350), [])
        evts = mgr.update(700)
        self.assertEqual(len(evts), 1)
        self.assertEqual(evts[0].name, "PROXIMITY_NEAR")
        self.assertIn(emo.current_expression, (Expression.CURIOUS, Expression.SURPRISED, Expression.HAPPY))

        # Hysteresis: moving to 30 cm (< 35 exit) stays NEAR and does NOT re-trigger
        prov.distance_cm = 30.0
        self.assertEqual(mgr.update(1000), [])
        self.assertEqual(mgr.proximity_state, "NEAR")

        # Stationary at 20 cm even after cooldown must NOT spam greetings
        prov.distance_cm = 20.0
        self.assertEqual(mgr.update(15000), [])

        # Exit above 35 cm triggers PROXIMITY_LEFT (median filter settles in 2-3 samples)
        prov.distance_cm = 42.0
        evts_leave = mgr.update(16000) + mgr.update(16100) + mgr.update(16200)
        self.assertEqual(len(evts_leave), 1)
        self.assertEqual(evts_leave[0].name, "PROXIMITY_LEFT")

    def test_02_touch_short_long_held_and_multi(self) -> None:
        prov, emo, cfg, mgr = self._make_setup()
        # Short tap: press -> debounce -> release before 900ms
        prov.touch_pressed = True
        mgr.update(100)
        mgr.update(170)  # debounced press
        prov.touch_pressed = False
        mgr.update(250)  # raw release
        evts = mgr.update(320)  # debounced release
        self.assertEqual([e.name for e in evts], ["TOUCH_SHORT"])
        self.assertEqual(emo.current_expression, Expression.SHY)

        # Long held touch: fires TOUCH_LONG once, never spams while held
        prov.touch_pressed = True
        mgr.update(3000)
        mgr.update(3070)
        evts_long = mgr.update(4100)
        self.assertEqual([e.name for e in evts_long], ["TOUCH_LONG"])
        self.assertEqual(emo.current_expression, Expression.LOVE)
        # Still held at 7000ms -> no duplicate event
        self.assertEqual(mgr.update(7000), [])
        prov.touch_pressed = False
        mgr.update(7100)
        self.assertEqual(mgr.update(7200), [])

        # Multi-tap within window
        prov.touch_pressed = True
        mgr.update(10000)
        mgr.update(10070)
        prov.touch_pressed = False
        mgr.update(10150)
        mgr.update(10220)  # 1st tap
        prov.touch_pressed = True
        mgr.update(12500)
        mgr.update(12570)
        prov.touch_pressed = False
        mgr.update(12650)
        evts_multi = mgr.update(12720)  # 2nd tap? window is 1200ms -> outside, so short
        self.assertEqual([e.name for e in evts_multi], ["TOUCH_SHORT"])

    def test_03_mpu6050_tilt_oscillation_shake_and_lift(self) -> None:
        prov, emo, cfg, mgr = self._make_setup()
        # Small oscillation below 18 deg -> no reaction
        prov.roll_deg = 8.0
        self.assertEqual(mgr.update(100), [])
        self.assertEqual(mgr.update(500), [])

        # Sustained lateral tilt >= 18 deg
        prov.roll_deg = 32.0
        mgr.update(1000)
        mgr.update(1100)
        evts_tilt = mgr.update(1350)
        self.assertEqual([e.name for e in evts_tilt], ["TILT_LATERAL"])
        self.assertIn(emo.current_expression, (Expression.CURIOUS, Expression.CONFUSED))

        # Return flat
        prov.roll_deg = 0.0
        mgr.update(2000)
        mgr.update(2200)

        # Sudden motion after cooldown
        prov.trigger_sudden_motion()
        evts_shake = mgr.update(6000)
        self.assertEqual([e.name for e in evts_shake], ["SUDDEN_MOTION"])
        self.assertIn(emo.current_expression, (Expression.SURPRISED, Expression.CONFUSED))

        # Simulated lift after cooldown
        prov.trigger_lift()
        evts_lift = mgr.update(10000)
        self.assertEqual([e.name for e in evts_lift], ["SIMULATED_LIFT"])
        self.assertEqual(emo.current_expression, Expression.SURPRISED)

    def test_04_bh1750_temporary_vs_prolonged_dark_and_light_return(self) -> None:
        prov, emo, cfg, mgr = self._make_setup()
        # Temporary dark (5s < 15s dwell) -> must NOT sleep
        prov.lux = 5.0
        mgr.update(1000)
        mgr.update(3000)
        self.assertEqual(mgr.update(5000), [])
        self.assertNotEqual(emo.current_expression, Expression.SLEEPY)

        # Return to normal light
        prov.lux = 300.0
        mgr.update(5500)
        mgr.update(6500)

        # Prolonged dark >= 15s -> SLEEPY
        prov.lux = 2.0
        for ts in (10000, 10200, 10400, 10600, 10800, 11000, 15000):
            mgr.update(ts)
        evts_dark = mgr.update(27000)
        self.assertEqual([e.name for e in evts_dark], ["DARK_PROLONGED"])
        self.assertEqual(emo.current_expression, Expression.SLEEPY)

        # Light returns -> wakes up cleanly
        prov.lux = 350.0
        mgr.update(37000)
        mgr.update(37800)
        evts_light = mgr.update(39000)
        self.assertEqual([e.name for e in evts_light], ["LIGHT_RETURNED"])
        self.assertEqual(emo.current_expression, Expression.SURPRISED)

    def test_05_disabled_sensor_invalid_readings_and_stub(self) -> None:
        prov, emo, cfg, mgr = self._make_setup()
        cfg.set_enabled(SensorType.VL53L0X, False)
        prov.distance_cm = 10.0
        mgr.update(100)
        self.assertEqual(mgr.update(500), [])
        diag = mgr.get_diagnostics(500)
        self.assertIn("VL53L0X", diag["disabled_sensors"])

        # Invalid NaN/out-of-range readings handled gracefully
        prov.lux = float("nan")
        prov.roll_deg = float("inf")
        self.assertEqual(mgr.update(1000), [])
        diag2 = mgr.get_diagnostics(1000)
        self.assertGreater(diag2["invalid_counts"]["BH1750"], 0)
        self.assertGreater(diag2["invalid_counts"]["MPU6050"], 0)

        # Disconnected hardware stub
        stub_mgr = SensorManager(provider=HardwareSensorProviderStub(), emotion_engine=emo)
        self.assertEqual(stub_mgr.update(2000), [])
        self.assertEqual(len(stub_mgr.get_diagnostics(2000)["disconnected_sensors"]), 4)

    def test_06_simultaneous_events_cooldown_and_no_voice_interruption(self) -> None:
        prov, emo, cfg, mgr = self._make_setup()
        # Simultaneous proximity + shake -> higher priority MOTION_SHAKE wins
        prov.distance_cm = 15.0
        mgr.update(100)
        prov.trigger_sudden_motion()
        evts = mgr.update(400)
        self.assertEqual(len(evts), 2)
        self.assertIn(emo.current_expression, (Expression.SURPRISED, Expression.CONFUSED))

        # Cooldown prevents immediate re-trigger of shake
        prov.trigger_sudden_motion()
        self.assertEqual(mgr.update(1000), [])

        # Active voice conversation must NEVER be interrupted and stale events must NOT play late
        emo.set_conversation_busy(True, now_ms=10000, phase_expr=Expression.LISTENING)
        prov.trigger_lift()
        mgr.update(10500)
        self.assertEqual(emo.current_expression, Expression.LISTENING)
        # Long conversation ends 8 seconds later -> stale lift event must NOT replay!
        emo.set_conversation_busy(False, now_ms=18500)
        emo.tick(18600)
        self.assertEqual(emo.current_expression, Expression.IDLE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
