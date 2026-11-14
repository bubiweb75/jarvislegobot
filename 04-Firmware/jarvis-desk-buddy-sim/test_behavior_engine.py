"""Automated tests for FASE 9.1: BehaviorEngine, PersonalityProfile, and EyeEngine 2.0."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from behavior_engine import BehaviorEngine, BehaviorEvent, RobotMode
from emotion_engine import EmotionEngine, StimulusType
from eye_engine import Expression
from eye_engine_v2 import ALL_14_EXPRESSIONS, EyeEngine2, clamp_firmware_look
from personality import PersonalityConfig, PersonalityProfile
from sensor_manager import SensorManager, SimulatedSensorProvider


class TestBehaviorAndPersonality(unittest.TestCase):
    def test_01_event_priority_and_concurrent_events(self) -> None:
        be = BehaviorEngine()
        # Submit low priority first, high priority second at same timestamp
        be.submit_stimulus(StimulusType.INACTIVITY, now_ms=1000, source="idle", priority=20)
        be.submit_stimulus(StimulusType.TEMP_ERROR, now_ms=1000, source="sys", priority=95)
        dec = be.tick(1000)
        self.assertIsNotNone(dec)
        self.assertEqual(dec.expression, Expression.CONFUSED)
        self.assertTrue(any(d.outcome == "PREEMPTED" for d in be.diagnostics))

    def test_02_quiet_mode_suppresses_voice_allows_oled(self) -> None:
        cues: list[str] = []
        be = BehaviorEngine(quiet_mode=True, on_voice_cue=cues.append)
        dec_voice = be.request_spontaneous_voice("IDLE_CHECKIN", now_ms=5000)
        self.assertIsNone(dec_voice.voice_cue)
        self.assertEqual(dec_voice.suppressed_reason, "quiet_mode")
        self.assertEqual(cues, [])

        # Silent OLED reaction still works
        be.submit_stimulus(StimulusType.TOUCH_SHORT, now_ms=6000, source="sensor:TTP223", sequence_name="AFFECTION")
        dec_oled = be.tick(6000)
        self.assertIsNotNone(dec_oled)
        self.assertEqual(dec_oled.expression, Expression.SHY)

    def test_03_spontaneous_voice_limits_2_per_hour_and_20_min_interval(self) -> None:
        be = BehaviorEngine()
        # 1st initiative at t = 1_000 ms -> allowed
        d1 = be.request_spontaneous_voice("IDLE_CHECKIN", now_ms=1_000)
        self.assertIsNotNone(d1.voice_cue)

        # 5 minutes later -> blocked by 20 min interval
        d_early = be.request_spontaneous_voice("IDLE_CHECKIN", now_ms=1_000 + 5 * 60 * 1000)
        self.assertIsNone(d_early.voice_cue)
        self.assertEqual(d_early.suppressed_reason, "min_interval_active")

        # 21 minutes later -> 2nd initiative allowed
        d2 = be.request_spontaneous_voice("IDLE_CHECKIN", now_ms=1_000 + 21 * 60 * 1000)
        self.assertIsNotNone(d2.voice_cue)

        # 42 minutes from start (still within 1 hour, 21 min after d2) -> blocked by hourly limit (2/hour)
        d3 = be.request_spontaneous_voice("IDLE_CHECKIN", now_ms=1_000 + 42 * 60 * 1000)
        self.assertIsNone(d3.voice_cue)
        self.assertEqual(d3.suppressed_reason, "hourly_limit_reached")

        # 61 minutes from start -> d1 expired from 1h window, allowed again
        d4 = be.request_spontaneous_voice("IDLE_CHECKIN", now_ms=1_000 + 62 * 60 * 1000)
        self.assertIsNotNone(d4.voice_cue)

    def test_04_disable_all_initiatives_and_no_voice_during_conversation(self) -> None:
        cfg = PersonalityConfig(initiatives_enabled=False)
        be = BehaviorEngine(personality=PersonalityProfile(cfg))
        d_off = be.request_spontaneous_voice("IDLE_CHECKIN", now_ms=1000)
        self.assertEqual(d_off.suppressed_reason, "initiatives_disabled")

        be.personality.update_config(PersonalityConfig(initiatives_enabled=True))
        for busy_mode in (RobotMode.LISTENING, RobotMode.THINKING, RobotMode.SPEAKING, RobotMode.SLEEPING):
            be.set_mode(busy_mode, now_ms=2000)
            d_busy = be.request_spontaneous_voice("IDLE_CHECKIN", now_ms=3000)
            self.assertIsNone(d_busy.voice_cue)
            self.assertTrue(d_busy.suppressed_reason.startswith("busy_or_sleeping:"))

    def test_05_cooldown_and_non_repetitive_cues(self) -> None:
        be = BehaviorEngine()
        ev1 = BehaviorEvent(priority=60, timestamp_ms=1000, event_type="STIMULUS", source="test", stimulus=StimulusType.GREETING, cooldown_ms=5000)
        ev2 = BehaviorEvent(priority=60, timestamp_ms=2000, event_type="STIMULUS", source="test", stimulus=StimulusType.GREETING, cooldown_ms=5000)
        be.submit_event(ev1)
        d1 = be.tick(1000)
        self.assertIsNotNone(d1)
        be.submit_event(ev2)
        d2 = be.tick(2000)
        self.assertIsNotNone(d2)
        self.assertEqual(d2.suppressed_reason, "cooldown")

        # Non-repetitive cue selection
        p = PersonalityProfile(seed=42)
        picks = [p.pick_cue("IDLE_CHECKIN") for _ in range(3)]
        self.assertEqual(len(set(picks)), 3)

    def test_06_eye_engine_v2_14_expressions_and_firmware_protocol_safety(self) -> None:
        self.assertEqual(len(ALL_14_EXPRESSIONS), 14)
        self.assertEqual(clamp_firmware_look(50, -20), (11, -6))

        eye2 = EyeEngine2()
        first = eye2.start_sequence("GREETING", now_ms=1000)
        self.assertIsNotNone(first)
        self.assertEqual(first.expression, Expression.SURPRISED)
        self.assertIn("STATE:SURPRISED", first.to_serial_commands())
        self.assertIn("LOOK:0,-2", first.to_serial_commands())

        # Advance past first step (450ms)
        second = eye2.tick(1500)
        self.assertIsNotNone(second)
        self.assertEqual(second.expression, Expression.HAPPY)
        self.assertIn("BLINK", second.to_serial_commands())

    def test_07_sensor_manager_integration_and_error_handling(self) -> None:
        provider = SimulatedSensorProvider()
        emo = EmotionEngine(seed=123)
        sm = SensorManager(provider=provider, emotion_engine=emo)
        be = BehaviorEngine(emotion_engine=emo, sensor_manager=sm)

        # Simulate approach on VL53L0X
        provider.distance_cm = 18.0
        be.tick(100)
        dec = be.tick(400)  # dwell >= 250ms
        self.assertIsNotNone(dec)
        self.assertEqual(dec.expression, Expression.SURPRISED)  # start of GREETING sequence

        # Error handling: negative timestamp & invalid event
        be.submit_event(None)
        self.assertIsNone(be.tick(-5))
        self.assertTrue(any(d.outcome == "ERROR" for d in be.diagnostics))

    def test_08_sequence_interruption_quiet_mid_sequence_and_config_bounds(self) -> None:
        be = BehaviorEngine()
        # Start low-priority GREETING sequence (priority 48)
        be.submit_stimulus(
            StimulusType.PROXIMITY_APPROACH,
            now_ms=1000,
            source="sensor:VL53L0X",
            priority=48,
            sequence_name="GREETING",
        )
        d1 = be.tick(1000)
        self.assertIsNotNone(d1)
        self.assertEqual(d1.expression, Expression.SURPRISED)
        self.assertTrue(be.eye_v2.is_sequence_active)

        # Activate Quiet Mode mid-sequence: OLED continues silently, voice cue blocked
        be.set_quiet_mode(True, now_ms=1100)
        self.assertTrue(be.eye_v2.is_sequence_active)
        self.assertEqual(be.request_spontaneous_voice("IDLE_CHECKIN", now_ms=1150).suppressed_reason, "quiet_mode")

        # Higher-priority TEMP_ERROR interrupts the active sequence
        be.submit_stimulus(StimulusType.TEMP_ERROR, now_ms=1200, source="sys", priority=95)
        d_err = be.tick(1200)
        self.assertIsNotNone(d_err)
        self.assertEqual(d_err.expression, Expression.CONFUSED)
        self.assertFalse(be.eye_v2.is_sequence_active)

        # PersonalityConfig NaN / negative bounds safety
        bad_cfg = PersonalityConfig(
            expressive_intensity=float("nan"),
            initiative_frequency=99.0,
            max_voice_initiatives_per_hour=-3,
            min_voice_initiative_interval_ms=-500,
        ).normalized()
        self.assertEqual(bad_cfg.expressive_intensity, 0.75)
        self.assertEqual(bad_cfg.initiative_frequency, 1.5)
        self.assertEqual(bad_cfg.max_voice_initiatives_per_hour, 0)
        self.assertEqual(bad_cfg.min_voice_initiative_interval_ms, 0)


if __name__ == "__main__":
    unittest.main()
