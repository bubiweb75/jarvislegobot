// =============================================================================
// JARVIS AI Desk Buddy — Display-Independent 128x64 Monochrome Framebuffer
//
// Provides a 1-bit-per-pixel XBM-compatible framebuffer (1024 bytes) so the
// EyeEngine animation logic has zero direct dependency on U8g2 or hardware.
// =============================================================================
#pragma once

#include <stdint.h>

namespace jarvis::gfx {

constexpr int kWidth = 128;
constexpr int kHeight = 64;
constexpr int kStrideBytes = kWidth / 8;  // 16 bytes per row
constexpr int kBufferSize = kStrideBytes * kHeight;  // 1024 bytes

class MonochromeFramebuffer {
public:
    void Clear();
    void SetPixel(int x, int y, uint8_t color);
    uint8_t GetPixel(int x, int y) const;

    void FillRect(int x, int y, int w, int h, uint8_t color);
    void FillRoundRect(int x, int y, int w, int h, int r, uint8_t color);
    void FillTriangle(int x0, int y0, int x1, int y1, int x2, int y2, uint8_t color);
    void FillCircle(int cx, int cy, int r, uint8_t color);
    void DrawCircle(int cx, int cy, int r, uint8_t color);

    const uint8_t* Data() const { return buf_; }

private:
    uint8_t buf_[kBufferSize] = {};

    void DrawHLine(int x0, int x1, int y, uint8_t color);
};

}  // namespace jarvis::gfx
