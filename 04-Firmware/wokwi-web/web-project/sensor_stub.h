// =============================================================================
// JARVIS AI Desk Buddy — Sensor Architecture Stub (FASE 8.2A)
//
// Prepares the interface for FASE 8.2B physical sensors (VL53L0X, TTP223,
// MPU6050, BH1750) without introducing unverified libraries, active drivers,
// or fake physical readings.
// =============================================================================
#pragma once

#include <stdint.h>

namespace jarvis::sensors {

enum class SensorId : uint8_t {
    kVl53l0x = 0,
    kTtp223,
    kMpu6050,
    kBh1750,
};

struct SensorSnapshot {
    bool initialized = false;
    bool vl53l0x_online = false;
    bool ttp223_online = false;
    bool mpu6050_online = false;
    bool bh1750_online = false;
};

class SensorBridgeStub {
public:
    void Begin() { snapshot_.initialized = false; }

    /// Non-blocking placeholder; returns inactive snapshot until FASE 8.2B.
    void Poll(uint32_t /*now_ms*/) {}

    const SensorSnapshot& Snapshot() const { return snapshot_; }
    static constexpr const char* StatusLabel() { return "STUB_ONLY"; }

private:
    SensorSnapshot snapshot_{};
};

}  // namespace jarvis::sensors
