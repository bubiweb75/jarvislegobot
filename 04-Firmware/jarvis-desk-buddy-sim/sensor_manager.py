"""JARVIS LEGO BOT — Sensor Manager & Physical Sensor Simulation (FASE 8.1).

Architecture:
    Real/Simulated Sensors (SensorProvider)
        -> SensorManager (filtering, hysteresis, debounce, transitions, cooldowns)
        -> EmotionEngine (Personality C)
        -> EyeEngine / Voice AI
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Deque, Dict, List, Optional

from emotion_engine import EmotionEngine, ReactionDecision, StimulusType


class SensorType(str, Enum):
    VL53L0X = "VL53L0X"
    TTP223 = "TTP223"
    MPU6050 = "MPU6050"
    BH1750 = "BH1750"


@dataclass
class SensorReading:
    sensor: SensorType
    timestamp_ms: int
    valid: bool = True
    distance_cm: Optional[float] = None
    touch_pressed: Optional[bool] = None
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    accel_g: float = 1.0
    shake_detected: bool = False
    lifted_detected: bool = False
    lux: Optional[float] = None
    source: str = "sim"


@dataclass
class SensorEvent:
    sensor: SensorType
    name: str
    stimulus: Optional[StimulusType]
    now_ms: int
    payload: str = ""
    details: str = ""


@dataclass
class SensorConfig:
    """Conservative, calibratable parameters for all 4 physical/simulated sensors."""

    vl53l0x_enabled: bool = True
    ttp223_enabled: bool = True
    mpu6050_enabled: bool = True
    bh1750_enabled: bool = True

    # VL53L0X (provisional defaults pending physical calibration)
    prox_enter_cm: float = 25.0
    prox_exit_cm: float = 35.0
    prox_approach_delta_cm: float = 6.0
    prox_dwell_ms: int = 250
    prox_cooldown_ms: int = 12000
    prox_min_valid_cm: float = 2.0
    prox_max_valid_cm: float = 200.0

    # TTP223 capacitive touch
    touch_debounce_ms: int = 60
    touch_long_ms: int = 900
    touch_multi_window_ms: int = 1200
    touch_multi_count: int = 2
    touch_cooldown_ms: int = 2000

    # MPU6050 IMU (tilt / sudden motion / simulated lift)
    tilt_enter_deg: float = 18.0
    tilt_exit_deg: float = 10.0
    tilt_dwell_ms: int = 220
    shake_threshold_g: float = 1.65
    motion_cooldown_ms: int = 3500

    # BH1750 ambient light
    lux_dark_enter: float = 15.0
    lux_dark_exit: float = 40.0
    lux_bright_threshold: float = 250.0
    lux_dark_dwell_ms: int = 15000
    lux_light_dwell_ms: int = 1500
    lux_cooldown_ms: int = 10000

    def is_enabled(self, sensor: SensorType) -> bool:
        return {
            SensorType.VL53L0X: self.vl53l0x_enabled,
            SensorType.TTP223: self.ttp223_enabled,
            SensorType.MPU6050: self.mpu6050_enabled,
            SensorType.BH1750: self.bh1750_enabled,
        }[sensor]

    def set_enabled(self, sensor: SensorType, enabled: bool) -> None:
        if sensor == SensorType.VL53L0X:
            self.vl53l0x_enabled = enabled
        elif sensor == SensorType.TTP223:
            self.ttp223_enabled = enabled
        elif sensor == SensorType.MPU6050:
            self.mpu6050_enabled = enabled
        elif sensor == SensorType.BH1750:
            self.bh1750_enabled = enabled

    def reset_defaults(self) -> None:
        fresh = SensorConfig()
        for fld in self.__dataclass_fields__:
            setattr(self, fld, getattr(fresh, fld))


class SensorProvider(ABC):
    """Abstract sensor acquisition interface (simulated or future ESP32-S3 bridge)."""

    @abstractmethod
    def read_all(self, now_ms: int) -> Dict[SensorType, SensorReading]:
        raise NotImplementedError


class SimulatedSensorProvider(SensorProvider):
    """In-memory interactive provider used by the Windows Simulator and unit tests."""

    def __init__(self) -> None:
        self.reset_defaults()

    def reset_defaults(self) -> None:
        self.distance_cm: float = 80.0
        self.touch_pressed: bool = False
        self.pitch_deg: float = 0.0
        self.roll_deg: float = 0.0
        self.accel_g: float = 1.0
        self.lux: float = 300.0
        self._pending_shake: bool = False
        self._pending_lift: bool = False
        self.connected: Dict[SensorType, bool] = {s: True for s in SensorType}

    def set_connected(self, sensor: SensorType, is_connected: bool) -> None:
        self.connected[sensor] = is_connected

    def trigger_sudden_motion(self) -> None:
        self._pending_shake = True

    def trigger_lift(self) -> None:
        self._pending_lift = True

    def read_all(self, now_ms: int) -> Dict[SensorType, SensorReading]:
        shake = self._pending_shake
        lift = self._pending_lift
        self._pending_shake = False
        self._pending_lift = False

        return {
            SensorType.VL53L0X: SensorReading(
                sensor=SensorType.VL53L0X,
                timestamp_ms=now_ms,
                valid=self.connected[SensorType.VL53L0X],
                distance_cm=self.distance_cm,
                source="sim",
            ),
            SensorType.TTP223: SensorReading(
                sensor=SensorType.TTP223,
                timestamp_ms=now_ms,
                valid=self.connected[SensorType.TTP223],
                touch_pressed=self.touch_pressed,
                source="sim",
            ),
            SensorType.MPU6050: SensorReading(
                sensor=SensorType.MPU6050,
                timestamp_ms=now_ms,
                valid=self.connected[SensorType.MPU6050],
                pitch_deg=self.pitch_deg,
                roll_deg=self.roll_deg,
                accel_g=2.1 if shake else self.accel_g,
                shake_detected=shake,
                lifted_detected=lift,
                source="sim",
            ),
            SensorType.BH1750: SensorReading(
                sensor=SensorType.BH1750,
                timestamp_ms=now_ms,
                valid=self.connected[SensorType.BH1750],
                lux=self.lux,
                source="sim",
            ),
        }


class HardwareSensorProviderStub(SensorProvider):
    """Placeholder interface for future ESP32-S3 USB-CDC sensor telemetry (FASE 8.2+)."""

    def read_all(self, now_ms: int) -> Dict[SensorType, SensorReading]:
        return {
            s: SensorReading(sensor=s, timestamp_ms=now_ms, valid=False, source="esp32_unconnected")
            for s in SensorType
        }


class SensorManager:
    """Interprets raw sensor readings into semantic events for EmotionEngine."""

    def __init__(
        self,
        provider: Optional[SensorProvider] = None,
        emotion_engine: Optional[EmotionEngine] = None,
        config: Optional[SensorConfig] = None,
    ) -> None:
        self.provider: SensorProvider = provider if provider is not None else SimulatedSensorProvider()
        self.emotion_engine = emotion_engine
        self.config = config if config is not None else SensorConfig()
        self.reset_state()

    def reset_state(self) -> None:
        self.cooldown_until: Dict[SensorType, int] = {}
        self.invalid_counts: Dict[SensorType, int] = {s: 0 for s in SensorType}
        self.disconnected_sensors: Dict[SensorType, bool] = {s: False for s in SensorType}

        # VL53L0X state
        self._dist_hist: Deque[float] = deque(maxlen=4)
        self.proximity_state: str = "NONE"  # NONE | APPROACHING | NEAR | LEAVING
        self._prox_candidate_since_ms: Optional[int] = None
        self._last_dist_cm: Optional[float] = None

        # TTP223 state
        self._touch_raw_last: bool = False
        self._touch_raw_since_ms: int = 0
        self._touch_stable: bool = False
        self._touch_press_start_ms: int = 0
        self._touch_long_fired: bool = False
        self._touch_tap_times: Deque[int] = deque(maxlen=6)

        # MPU6050 state
        self._pitch_filt: float = 0.0
        self._roll_filt: float = 0.0
        self._tilted_active: bool = False
        self._tilt_candidate_since_ms: Optional[int] = None

        # BH1750 state
        self._lux_filt: Optional[float] = None
        self.light_state: str = "BRIGHT"  # BRIGHT | NORMAL | DIM | DARK
        self._dark_since_ms: Optional[int] = None
        self._dark_triggered: bool = False
        self._bright_since_ms: Optional[int] = None

        # Diagnostics
        self.last_event: Optional[SensorEvent] = None
        self.last_decision: Optional[ReactionDecision] = None
        self.last_readings: Dict[SensorType, SensorReading] = {}

    def _in_cooldown(self, sensor: SensorType, now_ms: int) -> bool:
        return now_ms < self.cooldown_until.get(sensor, 0)

    def _emit_event(
        self,
        event: SensorEvent,
        cooldown_ms: int,
    ) -> SensorEvent:
        self.last_event = event
        self.cooldown_until[event.sensor] = event.now_ms + cooldown_ms
        if self.emotion_engine is not None and event.stimulus is not None:
            decision = self.emotion_engine.push_stimulus(
                event.stimulus,
                event.now_ms,
                source=f"sensor:{event.sensor.value}",
                payload=event.payload,
            )
            if decision is not None:
                self.last_decision = decision
        return event

    @staticmethod
    def _is_finite(val: Optional[float]) -> bool:
        return val is not None and math.isfinite(val)

    def _process_vl53l0x(self, r: SensorReading, now_ms: int) -> Optional[SensorEvent]:
        if not self._is_finite(r.distance_cm):
            self.invalid_counts[SensorType.VL53L0X] += 1
            return None
        d = float(r.distance_cm)  # type: ignore[arg-type]
        if d < self.config.prox_min_valid_cm or d > self.config.prox_max_valid_cm:
            self.invalid_counts[SensorType.VL53L0X] += 1
            return None

        self._dist_hist.append(d)
        smoothed = sorted(self._dist_hist)[len(self._dist_hist) // 2]
        prev_d = self._last_dist_cm
        self._last_dist_cm = smoothed

        if self.proximity_state in ("NONE", "LEAVING"):
            if smoothed <= self.config.prox_enter_cm:
                if self._prox_candidate_since_ms is None:
                    self._prox_candidate_since_ms = now_ms
                    self.proximity_state = "APPROACHING"
                elif (now_ms - self._prox_candidate_since_ms) >= self.config.prox_dwell_ms:
                    self.proximity_state = "NEAR"
                    self._prox_candidate_since_ms = None
                    if not self._in_cooldown(SensorType.VL53L0X, now_ms):
                        fast = prev_d is not None and (prev_d - smoothed) >= self.config.prox_approach_delta_cm
                        return self._emit_event(
                            SensorEvent(
                                sensor=SensorType.VL53L0X,
                                name="PROXIMITY_NEAR",
                                stimulus=StimulusType.PROXIMITY_APPROACH,
                                now_ms=now_ms,
                                payload="FAST" if fast else "NORMAL",
                                details=f"{smoothed:.1f} cm",
                            ),
                            self.config.prox_cooldown_ms,
                        )
            else:
                self._prox_candidate_since_ms = None
                self.proximity_state = "NONE"
        elif self.proximity_state == "APPROACHING":
            if smoothed <= self.config.prox_enter_cm:
                if (now_ms - (self._prox_candidate_since_ms or now_ms)) >= self.config.prox_dwell_ms:
                    self.proximity_state = "NEAR"
                    self._prox_candidate_since_ms = None
                    if not self._in_cooldown(SensorType.VL53L0X, now_ms):
                        return self._emit_event(
                            SensorEvent(
                                sensor=SensorType.VL53L0X,
                                name="PROXIMITY_NEAR",
                                stimulus=StimulusType.PROXIMITY_APPROACH,
                                now_ms=now_ms,
                                payload="NORMAL",
                                details=f"{smoothed:.1f} cm",
                            ),
                            self.config.prox_cooldown_ms,
                        )
            else:
                self._prox_candidate_since_ms = None
                self.proximity_state = "NONE"
        elif self.proximity_state == "NEAR":
            # Hysteresis: stay NEAR while inside [0..prox_exit_cm], no repeated greetings
            if smoothed >= self.config.prox_exit_cm:
                self.proximity_state = "LEAVING"
                return self._emit_event(
                    SensorEvent(
                        sensor=SensorType.VL53L0X,
                        name="PROXIMITY_LEFT",
                        stimulus=StimulusType.PROXIMITY_LEAVE,
                        now_ms=now_ms,
                        details=f"{smoothed:.1f} cm",
                    ),
                    2500,
                )
        return None

    def _process_ttp223(self, r: SensorReading, now_ms: int) -> Optional[SensorEvent]:
        if r.touch_pressed is None:
            self.invalid_counts[SensorType.TTP223] += 1
            return None
        raw = bool(r.touch_pressed)
        if raw != self._touch_raw_last:
            self._touch_raw_last = raw
            self._touch_raw_since_ms = now_ms

        if (now_ms - self._touch_raw_since_ms) < self.config.touch_debounce_ms:
            return None

        # Debounced state transition
        if raw and not self._touch_stable:
            self._touch_stable = True
            self._touch_press_start_ms = now_ms
            self._touch_long_fired = False
        elif raw and self._touch_stable:
            # Fire TOUCH_LONG once while held; never spam repeated events
            if not self._touch_long_fired and (now_ms - self._touch_press_start_ms) >= self.config.touch_long_ms:
                self._touch_long_fired = True
                if not self._in_cooldown(SensorType.TTP223, now_ms):
                    return self._emit_event(
                        SensorEvent(
                            sensor=SensorType.TTP223,
                            name="TOUCH_LONG",
                            stimulus=StimulusType.TOUCH_LONG,
                            now_ms=now_ms,
                            details=f">={self.config.touch_long_ms}ms",
                        ),
                        self.config.touch_cooldown_ms,
                    )
        elif not raw and self._touch_stable:
            self._touch_stable = False
            if not self._touch_long_fired:
                self._touch_tap_times.append(now_ms)
                while (
                    self._touch_tap_times
                    and (now_ms - self._touch_tap_times[0]) > self.config.touch_multi_window_ms
                ):
                    self._touch_tap_times.popleft()
                if len(self._touch_tap_times) >= self.config.touch_multi_count:
                    self._touch_tap_times.clear()
                    if not self._in_cooldown(SensorType.TTP223, now_ms):
                        return self._emit_event(
                            SensorEvent(
                                sensor=SensorType.TTP223,
                                name="TOUCH_MULTI",
                                stimulus=StimulusType.TOUCH_MULTI,
                                now_ms=now_ms,
                                details="multi-tap",
                            ),
                            self.config.touch_cooldown_ms,
                        )
                elif not self._in_cooldown(SensorType.TTP223, now_ms):
                    return self._emit_event(
                        SensorEvent(
                            sensor=SensorType.TTP223,
                            name="TOUCH_SHORT",
                            stimulus=StimulusType.TOUCH_SHORT,
                            now_ms=now_ms,
                            details="short-tap",
                        ),
                        self.config.touch_cooldown_ms,
                    )
        return None

    def _process_mpu6050(self, r: SensorReading, now_ms: int) -> Optional[SensorEvent]:
        if not (self._is_finite(r.pitch_deg) and self._is_finite(r.roll_deg) and self._is_finite(r.accel_g)):
            self.invalid_counts[SensorType.MPU6050] += 1
            return None

        # Low-pass filter for tilt angles
        self._pitch_filt = 0.65 * self._pitch_filt + 0.35 * r.pitch_deg
        self._roll_filt = 0.65 * self._roll_filt + 0.35 * r.roll_deg

        if r.lifted_detected and not self._in_cooldown(SensorType.MPU6050, now_ms):
            return self._emit_event(
                SensorEvent(
                    sensor=SensorType.MPU6050,
                    name="SIMULATED_LIFT",
                    stimulus=StimulusType.MOTION_LIFT,
                    now_ms=now_ms,
                    details="lift_event",
                ),
                self.config.motion_cooldown_ms,
            )

        if (r.shake_detected or r.accel_g >= self.config.shake_threshold_g) and not self._in_cooldown(
            SensorType.MPU6050, now_ms
        ):
            return self._emit_event(
                SensorEvent(
                    sensor=SensorType.MPU6050,
                    name="SUDDEN_MOTION",
                    stimulus=StimulusType.MOTION_SHAKE,
                    now_ms=now_ms,
                    details=f"{r.accel_g:.2f}g",
                ),
                self.config.motion_cooldown_ms,
            )

        max_tilt = max(abs(self._pitch_filt), abs(self._roll_filt))
        if not self._tilted_active:
            if max_tilt >= self.config.tilt_enter_deg:
                if self._tilt_candidate_since_ms is None:
                    self._tilt_candidate_since_ms = now_ms
                elif (now_ms - self._tilt_candidate_since_ms) >= self.config.tilt_dwell_ms:
                    self._tilted_active = True
                    self._tilt_candidate_since_ms = None
                    if not self._in_cooldown(SensorType.MPU6050, now_ms):
                        axis = "TILT_LATERAL" if abs(self._roll_filt) >= abs(self._pitch_filt) else "TILT_FORWARD_BACK"
                        return self._emit_event(
                            SensorEvent(
                                sensor=SensorType.MPU6050,
                                name=axis,
                                stimulus=StimulusType.MOTION_TILT,
                                now_ms=now_ms,
                                payload=axis,
                                details=f"pitch={self._pitch_filt:.0f}° roll={self._roll_filt:.0f}°",
                            ),
                            self.config.motion_cooldown_ms,
                        )
            else:
                self._tilt_candidate_since_ms = None
        elif max_tilt <= self.config.tilt_exit_deg:
            self._tilted_active = False
            self._tilt_candidate_since_ms = None
        return None

    def _process_bh1750(self, r: SensorReading, now_ms: int) -> Optional[SensorEvent]:
        if not self._is_finite(r.lux):
            self.invalid_counts[SensorType.BH1750] += 1
            return None
        lux = float(r.lux)  # type: ignore[arg-type]
        if lux < 0.0 or lux > 100000.0:
            self.invalid_counts[SensorType.BH1750] += 1
            return None

        self._lux_filt = lux if self._lux_filt is None else (0.50 * self._lux_filt + 0.50 * lux)
        val = self._lux_filt

        if val < self.config.lux_dark_enter:
            self._bright_since_ms = None
            if self._dark_since_ms is None:
                self._dark_since_ms = now_ms
            self.light_state = "DARK"
            if (
                not self._dark_triggered
                and (now_ms - self._dark_since_ms) >= self.config.lux_dark_dwell_ms
                and not self._in_cooldown(SensorType.BH1750, now_ms)
            ):
                self._dark_triggered = True
                return self._emit_event(
                    SensorEvent(
                        sensor=SensorType.BH1750,
                        name="DARK_PROLONGED",
                        stimulus=StimulusType.LIGHT_DARK,
                        now_ms=now_ms,
                        details=f"{val:.0f} lux",
                    ),
                    self.config.lux_cooldown_ms,
                )
        else:
            # Hysteresis: exit DARK only above lux_dark_exit
            if val >= self.config.lux_dark_exit:
                was_dark = self._dark_triggered or self.light_state == "DARK"
                self._dark_since_ms = None
                self.light_state = "BRIGHT" if val >= self.config.lux_bright_threshold else "NORMAL"
                if was_dark:
                    if self._bright_since_ms is None:
                        self._bright_since_ms = now_ms
                    elif (now_ms - self._bright_since_ms) >= self.config.lux_light_dwell_ms:
                        self._dark_triggered = False
                        self._bright_since_ms = None
                        if not self._in_cooldown(SensorType.BH1750, now_ms):
                            waking = self.emotion_engine is not None and (
                                self.emotion_engine.is_sleeping
                                or self.emotion_engine.base_expression.value in ("SLEEPY", "SLEEPING")
                            )
                            return self._emit_event(
                                SensorEvent(
                                    sensor=SensorType.BH1750,
                                    name="LIGHT_RETURNED",
                                    stimulus=StimulusType.LIGHT_BRIGHT,
                                    now_ms=now_ms,
                                    payload="WAKE" if waking else "BRIGHT",
                                    details=f"{val:.0f} lux",
                                ),
                                self.config.lux_cooldown_ms,
                            )
            else:
                self.light_state = "DIM"
        return None

    def update(self, now_ms: int) -> List[SensorEvent]:
        """Non-blocking poll of all enabled sensors."""
        readings = self.provider.read_all(now_ms)
        self.last_readings = readings
        events: List[SensorEvent] = []

        processors = (
            (SensorType.VL53L0X, self._process_vl53l0x),
            (SensorType.TTP223, self._process_ttp223),
            (SensorType.MPU6050, self._process_mpu6050),
            (SensorType.BH1750, self._process_bh1750),
        )

        for sensor, proc in processors:
            if not self.config.is_enabled(sensor):
                continue
            reading = readings.get(sensor)
            if reading is None or not reading.valid:
                self.disconnected_sensors[sensor] = True
                continue
            self.disconnected_sensors[sensor] = False
            evt = proc(reading, now_ms)
            if evt is not None:
                events.append(evt)
        return events

    def get_diagnostics(self, now_ms: int) -> Dict[str, object]:
        disabled = [s.value for s in SensorType if not self.config.is_enabled(s)]
        disconnected = [s.value for s, disc in self.disconnected_sensors.items() if disc and self.config.is_enabled(s)]
        max_cd = max((max(0, t - now_ms) for t in self.cooldown_until.values()), default=0)
        return {
            "proximity_state": self.proximity_state,
            "light_state": self.light_state,
            "last_event": self.last_event.name if self.last_event else "Nessuno",
            "last_reaction": self.last_decision.expression.value if self.last_decision else "-",
            "disabled_sensors": disabled,
            "disconnected_sensors": disconnected,
            "cooldown_ms": max_cd,
            "invalid_counts": {s.value: c for s, c in self.invalid_counts.items()},
        }
