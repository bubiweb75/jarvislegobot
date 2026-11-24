// =============================================================================
// JARVIS AI Desk Buddy — Hardware Pinout Configuration
// Board: Espressif ESP32-S3-DevKitC-1 N16R8
// Reference: 01-Hardware/02_Tabella_Pinout_Definitiva.md
// =============================================================================
#pragma once

#include <stdint.h>

namespace jarvis::pins {

// I2C0 Bus — OLED 1.3" 128x64 Monochrome
constexpr uint8_t kOledSda = 41;          // J3-7 (GPIO 41)
constexpr uint8_t kOledScl = 42;          // J3-6 (GPIO 42)
constexpr uint32_t kI2cClockHz = 400000;  // 400 kHz Fast-Mode I2C
constexpr uint8_t kOledI2cAddr = 0x3C;    // Typical 7-bit address (0x3C or 0x3D)

// User Input — Mechanical Pushbutton (Normally Open, Active LOW to GND)
constexpr uint8_t kButtonActivate = 47;   // J3-17 (GPIO 47, internal pull-up)

// -----------------------------------------------------------------------------
// FASE 8.2A — Sensor Pin & I2C Address Reservations (NOT ACTIVE YET — FASE 8.2B)
//   Shared I2C0 Bus: GPIO 41 (SDA) / GPIO 42 (SCL)
//     - OLED SH1106/SSD1306 : 0x3C (or 0x3D)
//     - VL53L0X (ToF)       : 0x29
//     - MPU6050 (IMU)       : 0x68 (AD0 = GND)
//     - BH1750 (Lux)        : 0x23 (ADDR = GND)
// -----------------------------------------------------------------------------
constexpr uint8_t kTouchTtp223 = 8;       // Digital Input (3.3V Active HIGH, FASE 8.2B)
constexpr uint8_t kTofXshut = 9;          // Optional VL53L0X XSHUT (FASE 8.2B)
constexpr uint8_t kImuInt = 10;           // Optional MPU6050 INT (FASE 8.2B)
constexpr uint8_t kVl53l0xI2cAddr = 0x29;
constexpr uint8_t kMpu6050I2cAddr = 0x68;
constexpr uint8_t kBh1750I2cAddr = 0x23;

// -----------------------------------------------------------------------------
// RESERVED / FORBIDDEN PINS ON ESP32-S3-DevKitC-1 N16R8 (DO NOT USE):
//   GPIO 35, 36, 37 : Octal PSRAM (R8) — using these crashes the MCU
//   GPIO 0, 3, 45, 46: Hardware strapping pins
//   GPIO 19, 20     : Native USB D- / D+
//   GPIO 43, 44     : UART0 TX / RX
//   GPIO 38 / 48    : Onboard NeoPixel RGB LED (v1.1 / v1.0)
//   GPIO 4, 5, 6    : Reserved for future INMP441 I2S Microphone
//   GPIO 7, 15, 16  : Reserved for future MAX98357A I2S Amplifier
// -----------------------------------------------------------------------------

}  // namespace jarvis::pins
