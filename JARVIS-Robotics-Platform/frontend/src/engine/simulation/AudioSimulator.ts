/**
 * JARVIS Robotics Platform — Audio Voice Reactivity Simulator
 * 
 * Genera segnali audio sintetici e calcola l'envelope RMS per simulare
 * la reattività vocale esclusivamente oculare di Eyes 3.0 in stato 'SPEAKING'.
 * Supporta inoltre il caricamento locale di file audio WAV reali tramite Web Audio API.
 */

import { EyeEngine } from '../eyes/EyeEngine';

export type AudioSimMode = 'SILENCE' | 'CONSTANT' | 'SINE' | 'SYLLABIC' | 'LOCAL_WAV' | 'silence' | 'constant' | 'sine' | 'syllabic';

export class AudioSimulator {
  private engine?: EyeEngine;
  private mode: AudioSimMode = 'SILENCE';
  private gain: number = 0.75; // 0.0 .. 1.0
  private sineFreqHz: number = 4.5;
  
  // Web Audio per caricamento WAV locale
  private audioCtx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private audioSource: AudioBufferSourceNode | null = null;
  private isWavPlaying: boolean = false;
  private dataArray: Uint8Array | null = null;
  private simTimeMs: number = 0;

  constructor(engine?: EyeEngine) {
    this.engine = engine;
  }

  setMode(mode: AudioSimMode): void {
    this.mode = mode;
    if (mode !== 'LOCAL_WAV' && this.isWavPlaying) {
      this.stopWav();
    }
  }

  getMode(): AudioSimMode {
    return this.mode;
  }

  setGain(gain: number): void {
    this.gain = Math.max(0.0, Math.min(1.0, gain));
  }

  getGain(): number {
    return this.gain;
  }

  setConstantRms(rms: number): void {
    this.setGain(rms);
    this.setMode('CONSTANT');
  }

  setFrequency(freqHz: number): void {
    this.setSineFrequency(freqHz);
  }

  setSineFrequency(freqHz: number): void {
    this.sineFreqHz = Math.max(0.5, Math.min(20.0, freqHz));
  }

  getSineFrequency(): number {
    return this.sineFreqHz;
  }

  /**
   * Aggiorna il livello RMS calcolato in base al clock corrente e alla modalità.
   */
  update(timeOrDt: number): number {
    let nowMs: number;
    if (timeOrDt <= 2.0) {
      // dt in secondi (es. 0.016)
      this.simTimeMs += timeOrDt * 1000;
      nowMs = this.simTimeMs;
    } else {
      nowMs = timeOrDt;
    }

    let currentRms = 0.0;
    const modeUpper = this.mode.toUpperCase();

    switch (modeUpper) {
      case 'SILENCE':
        currentRms = 0.0;
        break;

      case 'CONSTANT':
        currentRms = this.gain;
        break;

      case 'SINE': {
        const tSec = nowMs * 0.001;
        const wave = 0.5 + 0.5 * Math.sin(tSec * 2 * Math.PI * this.sineFreqHz);
        currentRms = wave * this.gain;
        break;
      }

      case 'SYLLABIC': {
        const tSec = nowMs * 0.001;
        // Modulazione pseudo-vocale a due portanti (ritmo sillabico ~ 5-7 Hz)
        const envelope = Math.max(0, 0.4 + 0.35 * Math.sin(tSec * 6.5) + 0.25 * Math.sin(tSec * 11.2));
        const pauseGate = Math.sin(tSec * 0.8) > -0.2 ? 1.0 : 0.05;
        currentRms = Math.min(1.0, envelope * pauseGate * this.gain);
        break;
      }

      case 'LOCAL_WAV': {
        if (this.analyser && this.dataArray && this.isWavPlaying) {
          (this.analyser as any).getByteTimeDomainData(this.dataArray);
          let sumSquares = 0;
          for (let i = 0; i < this.dataArray.length; i++) {
            const norm = (this.dataArray[i] - 128) / 128;
            sumSquares += norm * norm;
          }
          const rawRms = Math.sqrt(sumSquares / this.dataArray.length);
          currentRms = Math.min(1.0, rawRms * 2.5 * this.gain);
        } else {
          currentRms = 0.0;
        }
        break;
      }
    }

    currentRms = Math.max(0.0, Math.min(1.0, currentRms));

    if (this.engine) {
      this.engine.setAudioRms(currentRms);
    }
    return currentRms;
  }

  async loadLocalWav(file: File): Promise<void> {
    this.stopWav();

    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (!this.audioCtx) {
      this.audioCtx = new AudioContextClass();
    }
    if (this.audioCtx.state === 'suspended') {
      await this.audioCtx.resume();
    }

    const arrayBuffer = await file.arrayBuffer();
    const audioBuffer = await this.audioCtx.decodeAudioData(arrayBuffer);

    this.analyser = this.audioCtx.createAnalyser();
    this.analyser.fftSize = 256;
    this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);

    this.audioSource = this.audioCtx.createBufferSource();
    this.audioSource.buffer = audioBuffer;
    this.audioSource.connect(this.analyser);
    this.analyser.connect(this.audioCtx.destination);

    this.audioSource.onended = () => {
      this.isWavPlaying = false;
      this.mode = 'SILENCE';
    };

    this.audioSource.start(0);
    this.isWavPlaying = true;
    this.mode = 'LOCAL_WAV';
  }

  stopWav(): void {
    if (this.audioSource) {
      try {
        this.audioSource.stop();
        this.audioSource.disconnect();
      } catch {}
      this.audioSource = null;
    }
    this.isWavPlaying = false;
  }

  isPlayingWav(): boolean {
    return this.isWavPlaying;
  }
}
