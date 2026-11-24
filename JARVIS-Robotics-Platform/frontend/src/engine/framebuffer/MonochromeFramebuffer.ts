/**
 * JARVIS Robotics Platform — 128x64 Monochrome Framebuffer
 * 
 * Corrispondenza 1:1 con 'monochrome_fb.h' e 'monochrome_fb.cpp' del firmware ESP32.
 * 128x64 pixel monocromatici, 1 bit per pixel, 16 byte per riga (stride), 1024 byte totali.
 * Formato LSB-first conforme allo standard XBM / U8g2 drawXBM.
 */

export const FB_WIDTH = 128;
export const FB_HEIGHT = 64;
export const FB_STRIDE_BYTES = FB_WIDTH / 8; // 16 bytes per row
export const FB_BUFFER_SIZE = FB_STRIDE_BYTES * FB_HEIGHT; // 1024 bytes

export class MonochromeFramebuffer {
  readonly width: number = FB_WIDTH;
  readonly height: number = FB_HEIGHT;
  readonly buffer: Uint8Array = new Uint8Array(FB_BUFFER_SIZE);

  getBuffer(): Uint8Array {
    return this.buffer;
  }

  clear(): void {
    this.buffer.fill(0);
  }

  setPixel(x: number, y: number, color: number): void {
    const ix = Math.floor(x);
    const iy = Math.floor(y);
    if (ix < 0 || ix >= FB_WIDTH || iy < 0 || iy >= FB_HEIGHT) return;
    const idx = iy * FB_STRIDE_BYTES + (ix >> 3);
    const mask = 1 << (ix & 7);
    if (color !== 0) {
      this.buffer[idx] |= mask;
    } else {
      this.buffer[idx] &= ~mask;
    }
  }

  getPixel(x: number, y: number): number {
    const ix = Math.floor(x);
    const iy = Math.floor(y);
    if (ix < 0 || ix >= FB_WIDTH || iy < 0 || iy >= FB_HEIGHT) return 0;
    const idx = iy * FB_STRIDE_BYTES + (ix >> 3);
    return (this.buffer[idx] >> (ix & 7)) & 1;
  }

  drawHLine(x0: number, x1: number, y: number, color: number): void {
    const iy = Math.floor(y);
    if (iy < 0 || iy >= FB_HEIGHT) return;
    let startX = Math.floor(Math.min(x0, x1));
    let endX = Math.floor(Math.max(x0, x1));
    if (startX >= FB_WIDTH || endX < 0) return;
    if (startX < 0) startX = 0;
    if (endX >= FB_WIDTH) endX = FB_WIDTH - 1;
    for (let x = startX; x <= endX; ++x) {
      this.setPixel(x, iy, color);
    }
  }

  fillRect(x: number, y: number, w: number, h: number, color: number): void {
    const ix = Math.floor(x);
    const iy = Math.floor(y);
    const iw = Math.floor(w);
    const ih = Math.floor(h);
    for (let r = 0; r < ih; ++r) {
      this.drawHLine(ix, ix + iw - 1, iy + r, color);
    }
  }

  fillCircle(cx: number, cy: number, r: number, color: number): void {
    const icx = Math.floor(cx);
    const icy = Math.floor(cy);
    const ir = Math.floor(r);
    if (ir <= 0) {
      this.setPixel(icx, icy, color);
      return;
    }
    for (let dy = -ir; dy <= ir; ++dy) {
      const dx = Math.floor(Math.sqrt(ir * ir - dy * dy));
      this.drawHLine(icx - dx, icx + dx, icy + dy, color);
    }
  }

  drawCircle(cx: number, cy: number, r: number, color: number): void {
    const icx = Math.floor(cx);
    const icy = Math.floor(cy);
    const ir = Math.floor(r);
    if (ir <= 0) {
      this.setPixel(icx, icy, color);
      return;
    }
    let x = 0;
    let y = ir;
    let d = 1 - ir;
    const draw8 = (px: number, py: number) => {
      this.setPixel(icx + px, icy + py, color);
      this.setPixel(icx - px, icy + py, color);
      this.setPixel(icx + px, icy - py, color);
      this.setPixel(icx - px, icy - py, color);
      this.setPixel(icx + py, icy + px, color);
      this.setPixel(icx - py, icy + px, color);
      this.setPixel(icx + py, icy - px, color);
      this.setPixel(icx - py, icy - px, color);
    };
    draw8(x, y);
    while (x < y) {
      x++;
      if (d < 0) {
        d += 2 * x + 1;
      } else {
        y--;
        d += 2 * (x - y) + 1;
      }
      draw8(x, y);
    }
  }

  fillRoundRect(x: number, y: number, w: number, h: number, r: number, color: number): void {
    const ix = Math.floor(x);
    const iy = Math.floor(y);
    const iw = Math.floor(w);
    const ih = Math.floor(h);
    const ir = Math.floor(Math.min(r, iw / 2, ih / 2));
    this.fillRect(ix + ir, iy, iw - 2 * ir, ih, color);
    for (let dy = 0; dy < ir; ++dy) {
      const dx = Math.floor(Math.sqrt(ir * ir - (ir - dy) * (ir - dy)));
      this.drawHLine(ix + ir - dx, ix + ir, iy + dy, color);
      this.drawHLine(ix + iw - ir, ix + iw - ir + dx, iy + dy, color);
      this.drawHLine(ix + ir - dx, ix + ir, iy + ih - 1 - dy, color);
      this.drawHLine(ix + iw - ir, ix + iw - ir + dx, iy + ih - 1 - dy, color);
    }
    this.fillRect(ix, iy + ir, ir, ih - 2 * ir, color);
    this.fillRect(ix + iw - ir, iy + ir, ir, ih - 2 * ir, color);
  }

  toXBM(variableName: string = "jarvis_eye_bits"): string {
    let out = `// 128x64 XBM Image Data\n`;
    out += `#define ${variableName}_width 128\n`;
    out += `#define ${variableName}_height 64\n`;
    out += `static const unsigned char ${variableName}[] = {\n  `;
    for (let i = 0; i < FB_BUFFER_SIZE; ++i) {
      const hex = this.buffer[i].toString(16).padStart(2, '0');
      out += `0x${hex}`;
      if (i < FB_BUFFER_SIZE - 1) {
        out += `, `;
        if ((i + 1) % 16 === 0) out += `\n  `;
      }
    }
    out += `\n};\n`;
    return out;
  }

  exportRawBytes(): Uint8Array {
    return new Uint8Array(this.buffer);
  }

  loadRawBytes(bytes: Uint8Array): void {
    if (bytes.length === FB_BUFFER_SIZE) {
      this.buffer.set(bytes);
    }
  }
}
