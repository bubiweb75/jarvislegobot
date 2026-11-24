// =============================================================================
// JARVIS AI Desk Buddy — OLED Display Driver Abstraction
// Supports explicit build-time selection between SH1106 and SSD1306/SSD1106.
// =============================================================================
#pragma once

#include <U8g2lib.h>
#include <stdint.h>
#include "monochrome_fb.h"

#if defined(OLED_DRIVER_SH1106)
using JarvisU8g2Display = U8G2_SH1106_128X64_NONAME_F_HW_I2C;
constexpr const char* kOledDriverName = "SH1106 (132x64 RAM, +2px col offset)";
#elif defined(OLED_DRIVER_SSD1306)
using JarvisU8g2Display = U8G2_SSD1306_128X64_NONAME_F_HW_I2C;
constexpr const char* kOledDriverName = "SSD1306/SSD1106 (128x64 RAM, 0px offset)";
#else
#error "Select either -DOLED_DRIVER_SH1106=1 or -DOLED_DRIVER_SSD1306=1 in platformio.ini"
#endif

namespace jarvis::display {

constexpr int kScreenWidth = 128;
constexpr int kScreenHeight = 64;

struct I2cScanResult {
    bool found_0x3c = false;
    bool found_0x3d = false;
    uint8_t detected_addr = 0;
};

extern JarvisU8g2Display u8g2;

/// Initializes Wire on ESP32-S3 GPIO 41/42, scans for OLED, and starts U8g2.
I2cScanResult Begin();

/// Blits the 128x64 monochrome framebuffer (XBM format) to the physical OLED.
/// Returns measured I2C transfer duration in microseconds.
uint32_t PresentFramebuffer(const gfx::MonochromeFramebuffer& fb);

/// Last measured OLED I2C transfer duration in microseconds.
uint32_t LastTransferUs();

}  // namespace jarvis::display
