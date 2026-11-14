"""Display-independent 128x64 monochrome framebuffer (1-bit per pixel).

Exact Python mirror of 04-Firmware/jarvis-desk-buddy/src/monochrome_fb.cpp
for the Windows 11 desktop simulator.
"""

WIDTH = 128
HEIGHT = 64
STRIDE_BYTES = WIDTH // 8  # 16 bytes per row
BUFFER_SIZE = STRIDE_BYTES * HEIGHT  # 1024 bytes


class MonochromeFramebuffer:
    def __init__(self) -> None:
        self.buf = bytearray(BUFFER_SIZE)

    def clear(self) -> None:
        self.buf[:] = b"\x00" * BUFFER_SIZE

    def set_pixel(self, x: int, y: int, color: int) -> None:
        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            return
        idx = y * STRIDE_BYTES + (x >> 3)
        mask = 1 << (x & 7)  # XBM LSB-first
        if color != 0:
            self.buf[idx] |= mask
        else:
            self.buf[idx] &= ~mask & 0xFF

    def get_pixel(self, x: int, y: int) -> int:
        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            return 0
        idx = y * STRIDE_BYTES + (x >> 3)
        return (self.buf[idx] >> (x & 7)) & 1

    def _draw_hline(self, x0: int, x1: int, y: int, color: int) -> None:
        if y < 0 or y >= HEIGHT:
            return
        if x0 > x1:
            x0, x1 = x1, x0
        if x1 < 0 or x0 >= WIDTH:
            return
        x0 = max(0, x0)
        x1 = min(WIDTH - 1, x1)
        for x in range(x0, x1 + 1):
            self.set_pixel(x, y, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        if w <= 0 or h <= 0:
            return
        for row in range(y, y + h):
            self._draw_hline(x, x + w - 1, row, color)

    def fill_round_rect(self, x: int, y: int, w: int, h: int, r: int, color: int) -> None:
        if w <= 0 or h <= 0:
            return
        if r <= 0:
            self.fill_rect(x, y, w, h, color)
            return
        r = min(r, min(w, h) // 2)
        for dy in range(h):
            inset = 0
            if dy < r:
                cy = r - 1 - dy
                dx = 0
                while (dx + 1) * (dx + 1) + cy * cy <= r * r:
                    dx += 1
                inset = r - dx
            elif dy >= h - r:
                cy = dy - (h - r)
                dx = 0
                while (dx + 1) * (dx + 1) + cy * cy <= r * r:
                    dx += 1
                inset = r - dx
            self._draw_hline(x + inset, x + w - 1 - inset, y + dy, color)

    def fill_triangle(
        self, x0: int, y0: int, x1: int, y1: int, x2: int, y2: int, color: int
    ) -> None:
        if y0 > y1:
            y0, y1 = y1, y0
            x0, x1 = x1, x0
        if y1 > y2:
            y1, y2 = y2, y1
            x1, x2 = x2, x1
        if y0 > y1:
            y0, y1 = y1, y0
            x0, x1 = x1, x0

        if y0 == y2:
            a = min(x0, x1, x2)
            b = max(x0, x1, x2)
            self._draw_hline(a, b, y0, color)
            return

        total_h = y2 - y0
        for y in range(y0, y2 + 1):
            second_half = (y > y1) or (y1 == y0)
            seg_h = (y2 - y1) if second_half else (y1 - y0)
            alpha = (y - y0) / float(total_h)
            beta = ((y - (y1 if second_half else y0)) / float(seg_h)) if seg_h != 0 else 0.0
            ax = x0 + int((x2 - x0) * alpha)
            bx = (x1 + int((x2 - x1) * beta)) if second_half else (x0 + int((x1 - x0) * beta))
            self._draw_hline(ax, bx, y, color)

    def fill_circle(self, cx: int, cy: int, r: int, color: int) -> None:
        if r < 0:
            return
        for dy in range(-r, r + 1):
            dx = 0
            while (dx + 1) * (dx + 1) + dy * dy <= r * r:
                dx += 1
            self._draw_hline(cx - dx, cx + dx, cy + dy, color)

    def draw_circle(self, cx: int, cy: int, r: int, color: int) -> None:
        if r < 0:
            return
        x = r
        y = 0
        err = 1 - x
        while x >= y:
            for px, py in (
                (cx + x, cy + y), (cx + y, cy + x),
                (cx - y, cy + x), (cx - x, cy + y),
                (cx - x, cy - y), (cx - y, cy - x),
                (cx + y, cy - x), (cx + x, cy - y),
            ):
                self.set_pixel(px, py, color)
            y += 1
            if err < 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x + 1)

    def count_lit_pixels(self) -> int:
        return sum(bin(b).count("1") for b in self.buf)
