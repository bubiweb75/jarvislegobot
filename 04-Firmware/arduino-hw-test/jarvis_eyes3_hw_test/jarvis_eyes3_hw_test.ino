// =============================================================================
// JARVIS AI Desk Buddy — Main Firmware Entry Point
// Target: ESP32-S3-DevKitC-1 N16R8 + OLED 1.3" I2C (SH1106 / SSD1306)
// =============================================================================
#ifndef OLED_DRIVER_SH1106
#define OLED_DRIVER_SH1106 1
#endif

#include <Arduino.h>

#include "display_driver.h"
#include "eye_engine.h"
#include "pinout_config.h"
#include "sensor_stub.h"
#include "state_machine.h"

namespace {

jarvis::eyes::EyeEngine g_eyes;
jarvis::state::StateMachine g_state_machine;
jarvis::sensors::SensorBridgeStub g_sensor_stub;

}  // namespace

void setup() {
    Serial.begin(115200);
    const uint32_t wait_start = millis();
    while (!Serial && (millis() - wait_start) < 1200U) {
        // Brief non-blocking wait for USB-CDC enumeration
    }

    Serial.println();
    Serial.println(F("=== JARVIS AI Desk Buddy — Firmware v0.1 ==="));
    Serial.print(F("OLED Driver Build: "));
    Serial.println(kOledDriverName);
    Serial.printf("I2C Pins: SDA=GPIO%u, SCL=GPIO%u | Button=GPIO%u\n",
                  jarvis::pins::kOledSda,
                  jarvis::pins::kOledScl,
                  jarvis::pins::kButtonActivate);

    const auto scan = jarvis::display::Begin();
    if (scan.detected_addr != 0) {
        Serial.printf("I2C OLED detected at 0x%02X\n", scan.detected_addr);
    } else {
        Serial.println(F("WARN: No OLED ACK at 0x3C/0x3D (check wiring/VCC/GND). Continuing anyway."));
    }

#ifdef WOKWI_SIM
    // Brief startup splash screen for Wokwi hardware simulation demo
    jarvis::display::u8g2.clearBuffer();
    jarvis::display::u8g2.setFont(u8g2_font_ncenB14_tr);
    jarvis::display::u8g2.drawStr(24, 30, "JARVIS");
    jarvis::display::u8g2.setFont(u8g2_font_6x10_tr);
    jarvis::display::u8g2.drawStr(16, 48, "ESP32-S3 WOKWI SIM");
    jarvis::display::u8g2.sendBuffer();
    delay(900);
#endif

    g_sensor_stub.Begin();
    g_eyes.Begin(30, 12);
    g_state_machine.Begin(g_eyes, true);
    g_state_machine.SetOledDetectedAddr(scan.detected_addr);
    Serial.println(F("Ready. Type HELP on Serial or press GPIO47 button."));
}

void loop() {
    const uint32_t now_ms = millis();
    g_sensor_stub.Poll(now_ms);
    g_state_machine.Update(now_ms);
    g_eyes.Update(now_ms);
}
