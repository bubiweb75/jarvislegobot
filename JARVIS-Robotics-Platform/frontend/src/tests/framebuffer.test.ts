import { describe, it, expect, beforeEach } from 'vitest';
import { MonochromeFramebuffer } from '../engine/framebuffer/MonochromeFramebuffer';

describe('MonochromeFramebuffer (128x64 1-bit)', () => {
  let fb: MonochromeFramebuffer;

  beforeEach(() => {
    fb = new MonochromeFramebuffer();
  });

  it('dovrebbe inizializzare un buffer di esattamente 1024 byte azzerati', () => {
    const buf = fb.getBuffer();
    expect(buf.length).toBe(1024);
    for (let i = 0; i < buf.length; i++) {
      expect(buf[i]).toBe(0);
    }
  });

  it('dovrebbe impostare e leggere correttamente i singoli pixel', () => {
    fb.setPixel(0, 0, 1);
    expect(fb.getPixel(0, 0)).toBe(1);
    expect(fb.getPixel(1, 0)).toBe(0);

    fb.setPixel(127, 63, 1);
    expect(fb.getPixel(127, 63)).toBe(1);
    expect(fb.getPixel(126, 63)).toBe(0);

    // Coordinate fuori schermo ignorate senza errori
    fb.setPixel(-1, 0, 1);
    fb.setPixel(128, 0, 1);
    fb.setPixel(0, -1, 1);
    fb.setPixel(0, 64, 1);
    expect(fb.getPixel(-1, 0)).toBe(0);
    expect(fb.getPixel(128, 0)).toBe(0);
  });

  it('dovrebbe azzerare il buffer con clear()', () => {
    fb.setPixel(10, 10, 1);
    fb.setPixel(50, 30, 1);
    fb.clear();
    expect(fb.getPixel(10, 10)).toBe(0);
    expect(fb.getPixel(50, 30)).toBe(0);
  });

  it('dovrebbe tracciare linee orizzontali con drawHLine', () => {
    fb.drawHLine(10, 20, 15, 1);
    for (let x = 10; x <= 20; x++) {
      expect(fb.getPixel(x, 15)).toBe(1);
    }
    expect(fb.getPixel(9, 15)).toBe(0);
    expect(fb.getPixel(21, 15)).toBe(0);
  });

  it('dovrebbe disegnare cerchi pieni con fillCircle', () => {
    fb.fillCircle(64, 32, 5, 1);
    expect(fb.getPixel(64, 32)).toBe(1);
    expect(fb.getPixel(64 + 4, 32)).toBe(1);
    expect(fb.getPixel(64, 32 + 4)).toBe(1);
    expect(fb.getPixel(64 + 7, 32)).toBe(0);
  });

  it('dovrebbe esportare il formato XBM conforme a U8g2 e SH1106', () => {
    fb.setPixel(0, 0, 1);
    const xbm = fb.toXBM('test_xbm');
    expect(xbm).toContain('#define test_xbm_width 128');
    expect(xbm).toContain('#define test_xbm_height 64');
    expect(xbm).toContain('static const unsigned char test_xbm[] = {');
    expect(xbm).toContain('0x01');
  });
});
