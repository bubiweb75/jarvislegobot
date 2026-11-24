import { describe, it, expect, beforeEach } from 'vitest';
import { AudioSimulator } from '../engine/simulation/AudioSimulator';

describe('AudioSimulator (Envelope Reactivity)', () => {
  let audio: AudioSimulator;

  beforeEach(() => {
    audio = new AudioSimulator();
  });

  it('dovrebbe restituire 0.0 RMS in modalità SILENCE', () => {
    audio.setMode('silence');
    for (let i = 0; i < 10; i++) {
      expect(audio.update(0.016)).toBe(0.0);
    }
  });

  it('dovrebbe restituire il valore fisso in modalità CONSTANT', () => {
    audio.setMode('constant');
    audio.setConstantRms(0.75);
    for (let i = 0; i < 5; i++) {
      expect(audio.update(0.016)).toBe(0.75);
    }
  });

  it('dovrebbe oscillare in modalità SINE e rimanere sempre nell intervallo [0.0, 1.0]', () => {
    audio.setMode('sine');
    audio.setFrequency(2.0);
    for (let i = 0; i < 60; i++) {
      const val = audio.update(0.016);
      expect(val).toBeGreaterThanOrEqual(0.0);
      expect(val).toBeLessThanOrEqual(1.0);
    }
  });

  it('dovrebbe simulare la modulazione sillabica del parlato vocale', () => {
    audio.setMode('syllabic');
    const values: number[] = [];
    for (let i = 0; i < 100; i++) {
      const val = audio.update(0.016);
      values.push(val);
      expect(val).toBeGreaterThanOrEqual(0.0);
      expect(val).toBeLessThanOrEqual(1.0);
    }
    // Verifichiamo che i valori varino nel tempo (modulazione attiva)
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    expect(maxVal).toBeGreaterThan(minVal);
  });
});
