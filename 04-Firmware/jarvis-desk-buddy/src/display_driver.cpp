// =============================================================================
// JARVIS AI Desk Buddy — OLED Display Driver Implementation
// =============================================================================
#include "display_driver.h"

#include <Wire.h>
#include "pinout_config.h"

namespace jarvis::display {

JarvisU8g2Display u8g2(U8G2_R0, U8X8_PIN_NONE);

static bool ProbeAddress(uint8_t addr) {
    Wire.beginTransmission(addr);
    return (Wire.endTransmission() == 0);
}

I2cScanResult Begin() {
    Wire.begin(pins::kOledSda, pins::kOledScl, pins::kI2cClockHz);

    I2cScanResult res;
    res.found_0x3c = ProbeAddress(0x3C);
    res.found_0x3d = ProbeAddress(0x3D);
    if (res.found_0x3c) {
        res.detected_addr = 0x3C;
    } else if (res.found_0x3d) {
        res.detected_addr = 0x3D;
    }

    const uint8_t addr_to_use =
        (res.detected_addr != 0) ? res.detected_addr : pins::kOledI2cAddr;
    u8g2.setI2CAddress(addr_to_use << 1);  // U8g2 expects 8-bit I2C address
    u8g2.begin();
    u8g2.setBusClock(pins::kI2cClockHz);
    u8g2.setContrast(220);

    return res;
}

void PresentFramebuffer(const gfx::MonochromeFramebuffer& fb) {
    u8g2.clearBuffer();
    u8g2.drawXBM(0, 0, gfx::kWidth, gfx::kHeight, fb.Data());
    u8g2.sendBuffer();
}

}  // namespace jarvis::display
