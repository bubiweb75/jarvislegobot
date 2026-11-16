// =============================================================================
// JARVIS AI Desk Buddy — Display-Independent 128x64 Monochrome Framebuffer
// =============================================================================
#include "monochrome_fb.h"

#include <string.h>

namespace jarvis::gfx {

namespace {

void SwapInt(int& a, int& b) {
    const int tmp = a;
    a = b;
    b = tmp;
}

}  // namespace

void MonochromeFramebuffer::Clear() {
    memset(buf_, 0, sizeof(buf_));
}

void MonochromeFramebuffer::SetPixel(int x, int y, uint8_t color) {
    if (x < 0 || x >= kWidth || y < 0 || y >= kHeight) return;
    const int idx = y * kStrideBytes + (x >> 3);
    const uint8_t mask = static_cast<uint8_t>(1U << (x & 7));  // XBM LSB-first
    if (color != 0) {
        buf_[idx] |= mask;
    } else {
        buf_[idx] &= static_cast<uint8_t>(~mask);
    }
}

uint8_t MonochromeFramebuffer::GetPixel(int x, int y) const {
    if (x < 0 || x >= kWidth || y < 0 || y >= kHeight) return 0;
    const int idx = y * kStrideBytes + (x >> 3);
    return (buf_[idx] >> (x & 7)) & 1U;
}

void MonochromeFramebuffer::DrawHLine(int x0, int x1, int y, uint8_t color) {
    if (y < 0 || y >= kHeight) return;
    if (x0 > x1) SwapInt(x0, x1);
    if (x1 < 0 || x0 >= kWidth) return;
    if (x0 < 0) x0 = 0;
    if (x1 >= kWidth) x1 = kWidth - 1;
    for (int x = x0; x <= x1; ++x) {
        SetPixel(x, y, color);
    }
}

void MonochromeFramebuffer::FillRect(int x, int y, int w, int h, uint8_t color) {
    if (w <= 0 || h <= 0) return;
    for (int row = y; row < y + h; ++row) {
        DrawHLine(x, x + w - 1, row, color);
    }
}

void MonochromeFramebuffer::FillRoundRect(int x, int y, int w, int h, int r, uint8_t color) {
    if (w <= 0 || h <= 0) return;
    if (r <= 0) {
        FillRect(x, y, w, h, color);
        return;
    }
    const int max_r = (w < h ? w : h) / 2;
    if (r > max_r) r = max_r;

    for (int dy = 0; dy < h; ++dy) {
        int inset = 0;
        if (dy < r) {
            const int cy = r - 1 - dy;
            int dx = 0;
            while ((dx + 1) * (dx + 1) + cy * cy <= r * r) {
                ++dx;
            }
            inset = r - dx;
        } else if (dy >= h - r) {
            const int cy = dy - (h - r);
            int dx = 0;
            while ((dx + 1) * (dx + 1) + cy * cy <= r * r) {
                ++dx;
            }
            inset = r - dx;
        }
        DrawHLine(x + inset, x + w - 1 - inset, y + dy, color);
    }
}

void MonochromeFramebuffer::FillTriangle(int x0, int y0, int x1, int y1, int x2, int y2, uint8_t color) {
    if (y0 > y1) { SwapInt(y0, y1); SwapInt(x0, x1); }
    if (y1 > y2) { SwapInt(y1, y2); SwapInt(x1, x2); }
    if (y0 > y1) { SwapInt(y0, y1); SwapInt(x0, x1); }

    if (y0 == y2) {
        int a = x0;
        int b = x0;
        if (x1 < a) a = x1; else if (x1 > b) b = x1;
        if (x2 < a) a = x2; else if (x2 > b) b = x2;
        DrawHLine(a, b, y0, color);
        return;
    }

    const int total_h = y2 - y0;
    for (int y = y0; y <= y2; ++y) {
        const bool second_half = (y > y1) || (y1 == y0);
        const int seg_h = second_half ? (y2 - y1) : (y1 - y0);
        const float alpha = static_cast<float>(y - y0) / static_cast<float>(total_h);
        const float beta = (seg_h != 0)
            ? static_cast<float>(y - (second_half ? y1 : y0)) / static_cast<float>(seg_h)
            : 0.0f;
        const int ax = x0 + static_cast<int>((x2 - x0) * alpha);
        const int bx = second_half
            ? (x1 + static_cast<int>((x2 - x1) * beta))
            : (x0 + static_cast<int>((x1 - x0) * beta));
        DrawHLine(ax, bx, y, color);
    }
}

void MonochromeFramebuffer::FillCircle(int cx, int cy, int r, uint8_t color) {
    if (r < 0) return;
    for (int dy = -r; dy <= r; ++dy) {
        int dx = 0;
        while ((dx + 1) * (dx + 1) + dy * dy <= r * r) {
            ++dx;
        }
        DrawHLine(cx - dx, cx + dx, cy + dy, color);
    }
}

void MonochromeFramebuffer::DrawCircle(int cx, int cy, int r, uint8_t color) {
    if (r < 0) return;
    int x = r;
    int y = 0;
    int err = 1 - x;
    while (x >= y) {
        SetPixel(cx + x, cy + y, color);
        SetPixel(cx + y, cy + x, color);
        SetPixel(cx - y, cy + x, color);
        SetPixel(cx - x, cy + y, color);
        SetPixel(cx - x, cy - y, color);
        SetPixel(cx - y, cy - x, color);
        SetPixel(cx + y, cy - x, color);
        SetPixel(cx + x, cy - y, color);
        ++y;
        if (err < 0) {
            err += 2 * y + 1;
        } else {
            --x;
            err += 2 * (y - x + 1);
        }
    }
}

}  // namespace jarvis::gfx
