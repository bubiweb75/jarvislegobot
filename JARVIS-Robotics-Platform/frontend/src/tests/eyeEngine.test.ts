import { describe, it, expect, beforeEach } from 'vitest';
import { EyeEngine } from '../engine/eyes/EyeEngine';
import { MonochromeFramebuffer } from '../engine/framebuffer/MonochromeFramebuffer';
import { JARVIS_ORIGINAL_PREMIUM_SKIN } from '../engine/eyes/baseline';
import { ALL_EXPRESSIONS, ALL_PROFILES } from '../engine/eyes/types';

describe('EyeEngine (Eyes 3.0 C++ 1:1 Correspondence)', () => {
  let engine: EyeEngine;
  let fb: MonochromeFramebuffer;

  beforeEach(() => {
    engine = new EyeEngine(JARVIS_ORIGINAL_PREMIUM_SKIN);
    fb = new MonochromeFramebuffer();
  });

  it('dovrebbe caricare correttamente i parametri geometrici di JARVIS Original', () => {
    const skin = engine.getSkin();
    expect(skin.skin_id).toBe('skin-jarvis-original-v3');
    expect(skin.base_geometry.width).toBe(38.0);
    expect(skin.base_geometry.height).toBe(38.0);
    expect(skin.base_geometry.spacing_px).toBe(16);
    expect(skin.base_geometry.shape_power).toBe(2.6);
    expect(skin.base_geometry.taper).toBe(0.10);
    expect(skin.base_geometry.pupil.radius).toBe(7.0);
  });

  it('dovrebbe impostare ed aggiornare tutte le 14 espressioni canoniche', () => {
    expect(ALL_EXPRESSIONS.length).toBe(14);

    ALL_EXPRESSIONS.forEach((expr) => {
      engine.setExpression(expr);
      expect(engine.getExpression()).toBe(expr);
      // Step di aggiornamento senza crash
      engine.update(0.016);
    });
  });

  it('dovrebbe applicare ed estinguere le micro-espressioni', () => {
    engine.triggerMicroExpression('BrowRaise');
    expect(engine.getCurrentMicroExpression()).toBe('BrowRaise');

    // Verifichiamo che l'aggiornamento gestisca il decadimento temporale
    for (let i = 0; i < 30; i++) {
      engine.update(0.05);
    }
  });

  it('dovrebbe eseguire un ciclo di ammiccamento completo (Blink)', () => {
    engine.triggerBlink();
    expect(engine.isBlinking()).toBe(true);

    // Avanzamento temporale oltre la durata tipica del blink (0.24s)
    for (let i = 0; i < 20; i++) {
      engine.update(0.02);
    }
    expect(engine.isBlinking()).toBe(false);
  });

  it('dovrebbe supportare i profili comportamentali CALM, LIVELY e PLAYFUL', () => {
    ALL_PROFILES.forEach((profile) => {
      engine.setVisualProfile(profile);
      expect(engine.getVisualProfile()).toBe(profile);
    });
  });

  it('dovrebbe eseguire il rendering nel framebuffer monochrome 128x64 producendo pixel illuminati simmetrici', () => {
    engine.setExpression('NEUTRAL');
    // Lasciamo che la forma si stabilizzi
    for (let i = 0; i < 15; i++) {
      engine.update(0.016);
    }
    engine.render(fb);

    // Controlliamo che siano presenti pixel illuminati
    let litCount = 0;
    const buf = fb.getBuffer();
    for (let i = 0; i < buf.length; i++) {
      let b = buf[i];
      while (b > 0) {
        litCount += b & 1;
        b >>= 1;
      }
    }
    expect(litCount).toBeGreaterThan(100);

    // Verifichiamo che il centro dello schermo sia vuoto (spaziatura interoculare)
    // Con interoculare 16px, attorno a x=63-64 non dovrebbero esserci pixel accesi a y=32
    expect(fb.getPixel(63, 32)).toBe(0);
    expect(fb.getPixel(64, 32)).toBe(0);

    // Verifichiamo che ci siano pixel accesi nell'occhio sinistro e nell'occhio destro
    // Verifichiamo che ci siano pixel accesi nell'occhio sinistro (baseX ~37) e destro (baseX ~91)
    expect(fb.getPixel(25, 34)).toBe(1);
    expect(fb.getPixel(101, 34)).toBe(1);
  });

  it('dovrebbe reagire all inviluppo audio RMS modulando l altezza degli occhi', () => {
    engine.setExpression('SPEAKING');
    engine.setAudioRms(0.8);
    for (let i = 0; i < 10; i++) {
      engine.update(0.016);
    }
    engine.render(fb);
    const telemetry = engine.getTelemetry();
    expect(telemetry.audioRms).toBe(0.8);
  });
});
