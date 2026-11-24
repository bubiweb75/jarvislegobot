/**
 * JARVIS Robotics Platform — Eyes 3.0 Rendering Engine (TypeScript Port)
 * 
 * Porting verificato 1:1 di '04-Firmware/jarvis-desk-buddy/src/eye_engine.cpp'.
 * Riproduce in modo bit-exact e matematicamente identico le curve superellittiche,
 * le maschere delle palpebre, i catchlight pupillari, la dinamica temporale esponenziale,
 * le 14 espressioni e le 5 micro-espressioni di JARVIS Original Premium.
 */

import { MonochromeFramebuffer, FB_WIDTH, FB_HEIGHT } from '../framebuffer/MonochromeFramebuffer';
import {
  Expression,
  VisualProfile,
  MicroExpression,
  BlinkPhase,
  EyeState,
  SkinDefinition
} from './types';
import { JARVIS_ORIGINAL_PREMIUM_SKIN } from './baseline';

function clampInt(val: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, Math.floor(val)));
}

function clampFloat(val: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, val));
}

function roundHalfAway(val: number): number {
  return val >= 0 ? Math.floor(val + 0.5) : -Math.floor(-val + 0.5);
}

function smoothExp(current: number, target: number, rate: number, dtSec: number): number {
  const diff = target - current;
  if (Math.abs(diff) < 0.05) return target;
  const alpha = 1.0 - Math.exp(-rate * dtSec);
  return current + diff * alpha;
}

export class EyeEngine {
  readonly fb: MonochromeFramebuffer = new MonochromeFramebuffer();

  private defaultEyeWidth = 38;
  private defaultEyeHeight = 38;
  private defaultCornerRadius = 11;
  private spacingPx = 16;

  left: EyeState = this.createDefaultEyeState();
  right: EyeState = this.createDefaultEyeState();

  private expr: Expression = 'NEUTRAL';
  private visualProfile: VisualProfile = 'LIVELY';

  // Blinker State
  private blinkPhase: BlinkPhase = BlinkPhase.OPEN;
  private nextBlinkMs = 0;
  private blinkHoldUntilMs = 0;
  private doubleBlinkPending = false;

  // Gaze & Saccade State
  private autoIdleGaze = true;
  private nextGazeMs = 0;
  private gazeOverrideUntilMs = 0;
  private gazeIsMicro = false;

  // Micro-Expression State
  private microExpressionsEnabled = true;
  private currentMicroExpr: MicroExpression = 'NONE';
  private microExprUntilMs = 0;
  private nextMicroExprMs = 0;

  // Motion & Animation Phase
  private transitionBoost = 1.0;
  private exprStartMs = 0;
  private rngState = 0xa511e9b3;

  // Timing & Telemetry
  private frameIntervalMs = 33; // 30 FPS default
  private lastFrameMs = 0;
  private actualFps = 30.0;
  private droppedFrames = 0;

  // Audio Voice Reactivity
  private audioRmsLevel = 0.0; // 0.0 .. 1.0

  private currentSkin: SkinDefinition = JARVIS_ORIGINAL_PREMIUM_SKIN;

  constructor(initialSkin?: SkinDefinition) {
    if (initialSkin) {
      this.currentSkin = initialSkin;
      this.applySkinGeometry(initialSkin);
    } else {
      this.recalculateBasePositions();
      this.applyExpressionTargets();
    }
    this.nextBlinkMs = 5000;
  }

  getSkin(): SkinDefinition {
    return this.currentSkin;
  }

  private createDefaultEyeState(): EyeState {
    return {
      baseX: 0,
      baseY: 0,
      x: 0,
      y: 0,
      targetX: 0,
      targetY: 0,
      width: 38,
      height: 38,
      targetWidth: 38,
      targetHeight: 38,
      shapePower: 2.6,
      targetShapePower: 2.6,
      taper: 0.1,
      targetTaper: 0.1,
      cornerRadius: 11,
      targetCornerRadius: 11,
      lowerLid: 0,
      targetLowerLid: 0,
      lowerArch: 0,
      targetLowerArch: 0,
      upperLidL: 0,
      upperLidR: 0,
      targetUpperLidL: 0,
      targetUpperLidR: 0,
      upperArch: 0,
      targetUpperArch: 0,
      pupilDx: 0,
      targetPupilDx: 0,
      pupilDy: 0,
      targetPupilDy: 0,
      pupilRadius: 7,
      targetPupilRadius: 7,
      browOffset: 4,
      targetBrowOffset: 4,
      browTilt: 0,
      targetBrowTilt: 0,
      browArch: 2.2,
      targetBrowArch: 2.2,
      blinkSqueeze: 0
    };
  }

  seedRng(seed: number): void {
    this.rngState = (seed >>> 0) !== 0 ? (seed >>> 0) : 0xa511e9b3;
  }

  nextRand(): number {
    let x = this.rngState >>> 0;
    x ^= (x << 13) >>> 0;
    x ^= x >>> 17;
    x ^= (x << 5) >>> 0;
    this.rngState = x >>> 0;
    return this.rngState;
  }

  randRange(lo: number, hi: number): number {
    if (hi <= lo) return lo;
    const span = (hi - lo + 1) >>> 0;
    return lo + ((this.nextRand() % span) | 0);
  }

  profileSpeedScale(): number {
    switch (this.visualProfile) {
      case 'CALM': return 0.72;
      case 'PLAYFUL': return 1.22;
      case 'LIVELY':
      default: return 1.0;
    }
  }

  profileGazeFreqScale(): number {
    switch (this.visualProfile) {
      case 'CALM': return 0.65;
      case 'PLAYFUL': return 1.35;
      case 'LIVELY':
      default: return 1.0;
    }
  }

  profileMicroFreqScale(): number {
    switch (this.visualProfile) {
      case 'CALM': return 0.45;
      case 'PLAYFUL': return 1.65;
      case 'LIVELY':
      default: return 1.0;
    }
  }

  profileBlinkFreqScale(): number {
    switch (this.visualProfile) {
      case 'CALM': return 0.8;
      case 'PLAYFUL': return 1.15;
      case 'LIVELY':
      default: return 1.0;
    }
  }

  begin(fps = 50, spacingPx = 16, nowMs = 0): void {
    this.frameIntervalMs = fps > 0 ? Math.floor(1000 / fps) : 20;
    this.spacingPx = spacingPx;
    this.recalculateBasePositions();

    this.lastFrameMs = nowMs;
    this.nextBlinkMs = nowMs + 2200;
    this.nextGazeMs = nowMs + 2400;
    this.nextMicroExprMs = nowMs + 3800;
    this.exprStartMs = nowMs;
    this.actualFps = fps > 0 ? fps : 30.0;

    this.expr = 'NEUTRAL';
    this.applyExpressionTargets();
    this.renderFrame(nowMs);
  }

  recalculateBasePositions(): void {
    const totalW = this.defaultEyeWidth + this.spacingPx + this.defaultEyeWidth;
    const startX = Math.floor((FB_WIDTH - totalW) / 2);

    this.left.baseX = startX + Math.floor(this.defaultEyeWidth / 2);
    this.right.baseX = startX + this.defaultEyeWidth + this.spacingPx + Math.floor(this.defaultEyeWidth / 2);
    this.left.baseY = Math.floor(FB_HEIGHT / 2) + 2;
    this.right.baseY = Math.floor(FB_HEIGHT / 2) + 2;

    this.left.x = this.left.targetX = this.left.baseX;
    this.right.x = this.right.targetX = this.right.baseX;
    this.left.y = this.left.targetY = this.left.baseY;
    this.right.y = this.right.targetY = this.right.baseY;
  }

  setExpression(expr: Expression, nowMs = 0): void {
    if (this.expr === expr) return;
    this.expr = expr;
    this.exprStartMs = nowMs;
    this.currentMicroExpr = 'NONE';
    this.transitionBoost = expr === 'SURPRISED' ? 1.85 : 1.05;
    this.applyExpressionTargets();
  }

  getExpression(): Expression {
    return this.expr;
  }

  setVisualProfile(profile: VisualProfile): void {
    this.visualProfile = profile;
  }

  getVisualProfile(): VisualProfile {
    return this.visualProfile;
  }

  setMicroExpressionsEnabled(enabled: boolean): void {
    this.microExpressionsEnabled = enabled;
  }

  setAutoIdleGaze(enabled: boolean): void {
    this.autoIdleGaze = enabled;
  }

  setAudioRms(rms: number): void {
    this.audioRmsLevel = clampFloat(rms, 0.0, 1.0);
  }

  getAudioRms(): number {
    return this.audioRmsLevel;
  }

  getActualFps(): number {
    return this.actualFps;
  }

  getDroppedFrames(): number {
    return this.droppedFrames;
  }

  getCurrentMicroExpression(): MicroExpression {
    return this.currentMicroExpr;
  }

  isBlinking(): boolean {
    return this.blinkPhase !== BlinkPhase.OPEN;
  }

  triggerBlink(nowMs?: number): void {
    const t = nowMs !== undefined ? nowMs : this.lastFrameMs;
    if (this.blinkPhase === BlinkPhase.OPEN) {
      this.doubleBlinkPending = false;
      this.blinkPhase = BlinkPhase.CLOSING;
      this.nextBlinkMs = t + 5000;
    }
  }

  triggerMicroExpression(micro: MicroExpression, nowMs?: number): void {
    const t = nowMs !== undefined ? nowMs : this.lastFrameMs;
    this.currentMicroExpr = micro;
    this.microExprUntilMs = t + 1200;
  }

  getTelemetry() {
    return {
      fps: this.actualFps,
      droppedFrames: this.droppedFrames,
      audioRms: this.audioRmsLevel,
      expression: this.expr,
      profile: this.visualProfile,
      microExpression: this.currentMicroExpr,
      isBlinking: this.isBlinking()
    };
  }

  setGazeOffset(dx: number, dy: number, holdMs: number, nowMs: number): void {
    const clampedDx = clampInt(dx, -11, 11);
    const clampedDy = clampInt(dy, -6, 6);
    this.currentMicroExpr = 'NONE';
    this.gazeIsMicro = false;
    this.left.targetX = this.left.baseX + clampedDx * 0.45;
    this.right.targetX = this.right.baseX + clampedDx * 0.45;
    this.left.targetY = this.left.baseY + clampedDy * 0.4;
    this.right.targetY = this.right.baseY + clampedDy * 0.4;
    this.left.targetPupilDx = this.right.targetPupilDx = clampedDx * 0.55;
    this.left.targetPupilDy = this.right.targetPupilDy = clampedDy * 0.45;
    this.gazeOverrideUntilMs = nowMs + holdMs;
  }

  applySkinGeometry(skin: SkinDefinition): void {
    this.defaultEyeWidth = skin.base_geometry.width;
    this.defaultEyeHeight = skin.base_geometry.height;
    this.defaultCornerRadius = skin.base_geometry.corner_radius;
    this.spacingPx = skin.base_geometry.spacing_px;
    this.visualProfile = skin.visual_behavior_profile_default;
    this.recalculateBasePositions();
    this.applyExpressionTargets();
  }

  resetToDefaultGeometry(): void {
    this.defaultEyeWidth = 38;
    this.defaultEyeHeight = 38;
    this.defaultCornerRadius = 11;
    this.spacingPx = 16;
    this.visualProfile = 'LIVELY';
    this.recalculateBasePositions();
    this.applyExpressionTargets();
  }

  applyExpressionTargets(): void {
    for (const eye of [this.left, this.right]) {
      eye.targetWidth = this.defaultEyeWidth;
      eye.targetHeight = this.defaultEyeHeight;
      eye.targetShapePower = 2.6;
      eye.targetTaper = 0.1;
      eye.targetCornerRadius = this.defaultCornerRadius;
      eye.targetLowerLid = 0;
      eye.targetLowerArch = 0;
      eye.targetUpperLidL = 0;
      eye.targetUpperLidR = 0;
      eye.targetUpperArch = 0;
      eye.targetPupilDx = 0;
      eye.targetPupilDy = 0;
      eye.targetPupilRadius = 7.0;
      eye.targetBrowOffset = 4.0;
      eye.targetBrowTilt = 0;
      eye.targetBrowArch = 2.2;
      eye.targetX = eye.baseX;
      eye.targetY = eye.baseY;
    }

    switch (this.expr) {
      case 'NEUTRAL':
        break;

      case 'HAPPY':
        this.left.targetWidth = this.right.targetWidth = 36.0;
        this.left.targetHeight = this.right.targetHeight = 24.0;
        this.left.targetPupilRadius = this.right.targetPupilRadius = 0.0;
        this.left.targetBrowOffset = this.right.targetBrowOffset = 6.0;
        this.left.targetBrowArch = this.right.targetBrowArch = 3.5;
        this.left.targetY = this.right.targetY = this.left.baseY + 1;
        break;

      case 'CURIOUS':
        this.left.targetWidth = 30.0;
        this.left.targetHeight = 28.0;
        this.left.targetShapePower = 2.4;
        this.left.targetUpperLidL = 2.0;
        this.left.targetUpperLidR = 7.0;
        this.left.targetPupilDx = 3.0;
        this.left.targetPupilRadius = 6.0;
        this.left.targetBrowOffset = 3.5;
        this.left.targetBrowTilt = 2.5;
        this.left.targetBrowArch = 1.0;
        this.left.targetX = this.left.baseX + 2;
        this.left.targetY = this.left.baseY + 3;

        this.right.targetWidth = 42.0;
        this.right.targetHeight = 42.0;
        this.right.targetShapePower = 2.2;
        this.right.targetTaper = -0.06;
        this.right.targetPupilDx = 3.0;
        this.right.targetPupilDy = -2.0;
        this.right.targetPupilRadius = 7.5;
        this.right.targetBrowOffset = 6.5;
        this.right.targetBrowTilt = -2.5;
        this.right.targetBrowArch = 4.0;
        this.right.targetX = this.right.baseX + 2;
        this.right.targetY = this.right.baseY - 2;
        break;

      case 'SLEEPY':
        this.left.targetWidth = this.right.targetWidth = 36.0;
        this.left.targetHeight = this.right.targetHeight = 30.0;
        this.left.targetUpperLidL = this.left.targetUpperLidR = 11.0;
        this.right.targetUpperLidL = this.right.targetUpperLidR = 11.0;
        this.left.targetUpperArch = this.right.targetUpperArch = 2.0;
        this.left.targetPupilRadius = this.right.targetPupilRadius = 5.0;
        this.left.targetPupilDy = this.right.targetPupilDy = 3.0;
        this.left.targetBrowOffset = this.right.targetBrowOffset = 2.0;
        this.left.targetBrowArch = this.right.targetBrowArch = 0.5;
        this.left.targetY = this.right.targetY = this.left.baseY + 3;
        break;

      case 'LISTENING':
        this.left.targetWidth = this.right.targetWidth = 38.0;
        this.left.targetHeight = this.right.targetHeight = 42.0;
        this.left.targetShapePower = this.right.targetShapePower = 2.4;
        this.left.targetPupilRadius = this.right.targetPupilRadius = 8.5;
        this.left.targetBrowOffset = this.right.targetBrowOffset = 5.5;
        this.left.targetBrowArch = this.right.targetBrowArch = 3.0;
        break;

      case 'THINKING':
        this.left.targetWidth = this.right.targetWidth = 35.0;
        this.left.targetHeight = this.right.targetHeight = 31.0;
        this.left.targetX = this.left.baseX + 4;
        this.right.targetX = this.right.baseX + 4;
        this.left.targetY = this.left.baseY - 3;
        this.right.targetY = this.right.baseY - 3;
        this.left.targetUpperLidL = 8.0;
        this.left.targetUpperLidR = 5.0;
        this.right.targetUpperLidL = 4.0;
        this.right.targetUpperLidR = 6.0;
        this.left.targetLowerLid = this.right.targetLowerLid = 3.0;
        this.left.targetPupilDx = this.right.targetPupilDx = 5.5;
        this.left.targetPupilDy = this.right.targetPupilDy = -3.0;
        this.left.targetPupilRadius = this.right.targetPupilRadius = 5.5;
        this.left.targetBrowOffset = 3.5;
        this.left.targetBrowTilt = 3.0;
        this.right.targetBrowOffset = 5.5;
        this.right.targetBrowTilt = -1.5;
        break;

      case 'SPEAKING':
        this.left.targetWidth = this.right.targetWidth = 37.0;
        this.left.targetHeight = this.right.targetHeight = 35.0;
        this.left.targetLowerLid = this.right.targetLowerLid = 4.0;
        this.left.targetLowerArch = this.right.targetLowerArch = 6.0;
        this.left.targetPupilRadius = this.right.targetPupilRadius = 6.5;
        this.left.targetBrowOffset = this.right.targetBrowOffset = 4.5;
        break;

      case 'SURPRISED':
        this.left.targetWidth = this.right.targetWidth = 39.0;
        this.left.targetHeight = this.right.targetHeight = 45.0;
        this.left.targetShapePower = this.right.targetShapePower = 2.1;
        this.left.targetTaper = this.right.targetTaper = 0.0;
        this.left.targetPupilRadius = this.right.targetPupilRadius = 3.5;
        this.left.targetBrowOffset = this.right.targetBrowOffset = 6.0;
        this.left.targetBrowArch = this.right.targetBrowArch = 4.5;
        this.left.targetY = this.right.targetY = this.left.baseY;
        break;

      case 'SHY':
        this.left.targetWidth = this.right.targetWidth = 32.0;
        this.left.targetHeight = this.right.targetHeight = 28.0;
        this.left.targetUpperLidL = this.left.targetUpperLidR = 6.0;
        this.right.targetUpperLidL = this.right.targetUpperLidR = 6.0;
        this.left.targetPupilDx = this.right.targetPupilDx = -4.0;
        this.left.targetPupilDy = this.right.targetPupilDy = 2.5;
        this.left.targetPupilRadius = this.right.targetPupilRadius = 6.0;
        this.left.targetBrowOffset = this.right.targetBrowOffset = 4.5;
        this.left.targetBrowTilt = -3.5;
        this.right.targetBrowTilt = 3.5;
        this.left.targetX = this.left.baseX - 3;
        this.right.targetX = this.right.baseX - 3;
        this.left.targetY = this.right.targetY = this.left.baseY + 4;
        break;

      case 'LOVE':
        this.left.targetWidth = this.right.targetWidth = 34.0;
        this.left.targetHeight = this.right.targetHeight = 34.0;
        this.left.targetPupilRadius = this.right.targetPupilRadius = 0.0;
        this.left.targetBrowOffset = this.right.targetBrowOffset = 0.0;
        this.left.targetY = this.right.targetY = this.left.baseY;
        break;

      case 'WINK':
        this.left.targetWidth = 38.0;
        this.left.targetHeight = 38.0;
        this.left.targetPupilRadius = 7.0;
        this.left.targetBrowOffset = 5.5;
        this.left.targetBrowArch = 3.0;
        this.right.targetWidth = 36.0;
        this.right.targetHeight = 26.0;
        this.right.targetPupilRadius = 0.0;
        this.right.targetBrowOffset = 5.0;
        this.right.targetY = this.right.baseY + 2;
        break;

      case 'CONFUSED':
        this.left.targetWidth = 31.0;
        this.left.targetHeight = 27.0;
        this.left.targetUpperLidL = 8.0;
        this.left.targetUpperLidR = 3.0;
        this.left.targetPupilDx = -3.0;
        this.left.targetPupilRadius = 5.5;
        this.left.targetBrowOffset = 4.0;
        this.left.targetBrowTilt = 3.5;
        this.left.targetY = this.left.baseY + 2;

        this.right.targetWidth = 40.0;
        this.right.targetHeight = 40.0;
        this.right.targetPupilDx = 3.0;
        this.right.targetPupilDy = -2.0;
        this.right.targetPupilRadius = 7.0;
        this.right.targetBrowOffset = 6.0;
        this.right.targetBrowTilt = -3.5;
        this.right.targetBrowArch = 4.0;
        this.right.targetY = this.right.baseY - 2;
        break;

      case 'MISCHIEVOUS':
        this.left.targetWidth = this.right.targetWidth = 37.0;
        this.left.targetHeight = this.right.targetHeight = 32.0;
        this.left.targetUpperLidL = 2.0;
        this.left.targetUpperLidR = 14.0;
        this.right.targetUpperLidL = 14.0;
        this.right.targetUpperLidR = 2.0;
        this.left.targetLowerLid = this.right.targetLowerLid = 4.0;
        this.left.targetLowerArch = this.right.targetLowerArch = 7.0;
        this.left.targetPupilDx = this.right.targetPupilDx = 5.0;
        this.left.targetPupilRadius = this.right.targetPupilRadius = 5.5;
        this.left.targetBrowOffset = this.right.targetBrowOffset = 4.5;
        this.left.targetBrowTilt = 4.5;
        this.right.targetBrowTilt = -4.5;
        this.left.targetX = this.left.baseX + 3;
        this.right.targetX = this.right.baseX + 3;
        break;

      case 'SLEEPING':
        this.left.targetWidth = this.right.targetWidth = 34.0;
        this.left.targetHeight = this.right.targetHeight = 24.0;
        this.left.targetPupilRadius = this.right.targetPupilRadius = 0.0;
        this.left.targetBrowOffset = this.right.targetBrowOffset = 0.0;
        this.left.targetY = this.right.targetY = this.left.baseY + 3;
        break;
    }
  }

  updateBlinker(nowMs: number, dtSec: number): void {
    if (this.expr === 'HAPPY' || this.expr === 'WINK' || this.expr === 'SLEEPING') {
      this.blinkPhase = BlinkPhase.OPEN;
      this.left.blinkSqueeze = 0.0;
      this.right.blinkSqueeze = 0.0;
      return;
    }

    const speed = this.profileSpeedScale();
    const closeRate = (this.expr === 'SLEEPY' ? 6.0 : (this.expr === 'SURPRISED' ? 24.0 : 18.0)) * speed;
    const openRate = (this.expr === 'SLEEPY' ? 4.2 : (this.expr === 'SURPRISED' ? 18.0 : 14.0)) * speed;

    switch (this.blinkPhase) {
      case BlinkPhase.OPEN:
        if (nowMs >= this.nextBlinkMs) {
          this.blinkPhase = BlinkPhase.CLOSING;
          if (this.expr === 'NEUTRAL' && !this.doubleBlinkPending) {
            const dblChance = this.visualProfile === 'PLAYFUL' ? 28 : (this.visualProfile === 'CALM' ? 8 : 20);
            this.doubleBlinkPending = this.randRange(0, 99) < dblChance;
          }
        }
        break;

      case BlinkPhase.CLOSING:
        this.left.blinkSqueeze += closeRate * dtSec;
        this.right.blinkSqueeze += closeRate * dtSec;
        if (this.left.blinkSqueeze >= 1.0) {
          this.left.blinkSqueeze = this.right.blinkSqueeze = 1.0;
          this.blinkPhase = BlinkPhase.HOLD_CLOSED;
          this.blinkHoldUntilMs = nowMs + (this.expr === 'SLEEPY' ? 130 : 42);
        }
        break;

      case BlinkPhase.HOLD_CLOSED:
        if (nowMs >= this.blinkHoldUntilMs) {
          this.blinkPhase = BlinkPhase.OPENING;
        }
        break;

      case BlinkPhase.OPENING:
        this.left.blinkSqueeze -= openRate * dtSec;
        this.right.blinkSqueeze -= openRate * dtSec;
        if (this.left.blinkSqueeze <= 0.0) {
          this.left.blinkSqueeze = this.right.blinkSqueeze = 0.0;
          this.blinkPhase = BlinkPhase.OPEN;
          const bfreq = this.profileBlinkFreqScale();
          if (this.doubleBlinkPending) {
            this.doubleBlinkPending = false;
            this.nextBlinkMs = nowMs + Math.floor(this.randRange(110, 240) / bfreq);
          } else {
            const spanMs = (this.expr === 'SLEEPY' ? this.randRange(1600, 3200) : this.randRange(2400, 6200)) / bfreq;
            this.nextBlinkMs = nowMs + Math.floor(spanMs);
          }
        }
        break;
    }
  }

  updateGaze(nowMs: number): void {
    if (!this.autoIdleGaze) return;

    if (nowMs < this.gazeOverrideUntilMs) {
      return;
    }

    if (this.expr === 'SLEEPING' || this.expr === 'SLEEPY') {
      this.left.targetX = this.left.baseX;
      this.right.targetX = this.right.baseX;
      this.left.targetY = this.left.baseY + 3;
      this.right.targetY = this.right.baseY + 3;
      this.left.targetPupilDx = this.right.targetPupilDx = 0;
      this.left.targetPupilDy = this.right.targetPupilDy = 3.0;
      return;
    }

    if (nowMs >= this.nextGazeMs) {
      const gfreq = this.profileGazeFreqScale();
      const r = this.randRange(0, 99);

      if (r < 62) {
        // Micro-saccade
        const mdx = (this.randRange(-2, 2) | 0);
        const mdy = (this.randRange(-1, 1) | 0);
        this.left.targetPupilDx = mdx;
        this.right.targetPupilDx = mdx;
        this.left.targetPupilDy = mdy;
        this.right.targetPupilDy = mdy;
        this.left.targetX = this.left.baseX + mdx * 0.4;
        this.right.targetX = this.right.baseX + mdx * 0.4;
        this.left.targetY = this.left.baseY + mdy * 0.3;
        this.right.targetY = this.right.baseY + mdy * 0.3;
        this.gazeIsMicro = true;
      } else if (r < 86) {
        // Macro-saccade
        const dx = (this.randRange(-7, 7) | 0);
        const dy = (this.randRange(-4, 4) | 0);
        this.left.targetPupilDx = dx * 0.55;
        this.right.targetPupilDx = dx * 0.55;
        this.left.targetPupilDy = dy * 0.45;
        this.right.targetPupilDy = dy * 0.45;
        this.left.targetX = this.left.baseX + dx * 0.45;
        this.right.targetX = this.right.baseX + dx * 0.45;
        this.left.targetY = this.left.baseY + dy * 0.4;
        this.right.targetY = this.right.baseY + dy * 0.4;
        this.gazeIsMicro = false;
      } else {
        // Centro
        this.left.targetX = this.left.baseX;
        this.right.targetX = this.right.baseX;
        this.left.targetY = this.left.baseY;
        this.right.targetY = this.right.baseY;
        this.left.targetPupilDx = this.right.targetPupilDx = 0;
        this.left.targetPupilDy = this.right.targetPupilDy = 0;
        this.gazeIsMicro = false;
      }

      const nextBase = this.gazeIsMicro ? this.randRange(700, 1900) : this.randRange(2100, 4800);
      this.nextGazeMs = nowMs + Math.floor(nextBase / gfreq);
    }
  }

  updateMicroExpressions(nowMs: number): void {
    if (!this.microExpressionsEnabled) return;

    if (this.currentMicroExpr !== 'NONE') {
      if (nowMs >= this.microExprUntilMs) {
        this.currentMicroExpr = 'NONE';
        this.applyExpressionTargets();
      }
      return;
    }

    if (this.expr === 'SLEEPING' || this.expr === 'SLEEPY' || this.expr === 'LOVE') {
      return;
    }

    if (this.currentMicroExpr === 'NONE' && nowMs >= this.nextMicroExprMs) {
      if (this.expr === 'LISTENING' && this.randRange(0, 99) < 65) {
        this.nextMicroExprMs = nowMs + 3000;
        return;
      }

      const r = this.randRange(0, 99);
      if (r < 28) {
        this.currentMicroExpr = 'BrowRaise';
        this.right.targetBrowOffset += 3.0;
        this.right.targetBrowTilt -= 1.5;
        this.microExprUntilMs = nowMs + 520;
      } else if (r < 54) {
        this.currentMicroExpr = 'SideGlance';
        const dir = this.randRange(0, 1) === 0 ? -3.5 : 3.5;
        this.left.targetPupilDx += dir;
        this.right.targetPupilDx += dir;
        this.microExprUntilMs = nowMs + 460;
      } else if (r < 74) {
        this.currentMicroExpr = 'EyeSmile';
        this.left.targetLowerLid += 2.5;
        this.right.targetLowerLid += 2.5;
        this.left.targetLowerArch += 3.0;
        this.right.targetLowerArch += 3.0;
        this.microExprUntilMs = nowMs + 580;
      } else if (r < 90) {
        this.currentMicroExpr = 'PupilPulse';
        this.left.targetPupilRadius += 1.0;
        this.right.targetPupilRadius += 1.0;
        this.microExprUntilMs = nowMs + 420;
      } else {
        const winkThresh = this.visualProfile === 'PLAYFUL' ? 100 : (this.visualProfile === 'CALM' ? 0 : 50);
        if (this.randRange(0, 99) < winkThresh) {
          this.currentMicroExpr = 'QuickWink';
          this.right.targetUpperLidL += 9.0;
          this.right.targetUpperLidR += 9.0;
          this.microExprUntilMs = nowMs + 300;
        }
      }

      const mfreq = this.profileMicroFreqScale();
      const nextMs = Math.floor(this.randRange(3600, 7400) / mfreq);
      this.nextMicroExprMs = nowMs + clampInt(nextMs, 1800, 14000);
    }
  }

  updateExpressionMotion(nowMs: number): void {
    const tSec = (nowMs - this.exprStartMs) * 0.001;

    switch (this.expr) {
      case 'NEUTRAL': {
        const breath = Math.sin(tSec * 1.4);
        this.left.targetHeight = this.right.targetHeight = 32.0 + 0.8 * breath;
        break;
      }
      case 'HAPPY': {
        const bounce = Math.sin(tSec * 3.5) * 1.2;
        this.left.targetY = this.right.targetY = this.left.baseY - 2 + bounce;
        break;
      }
      case 'CURIOUS': {
        const drift = Math.sin(tSec * 1.9) * 2.0;
        this.left.targetX = this.left.baseX + 4 + drift;
        this.right.targetX = this.right.baseX + 4 + drift;
        break;
      }
      case 'SLEEPY': {
        const drowse = Math.sin(tSec * 1.1) * 1.5;
        this.left.targetUpperLidL = this.left.targetUpperLidR = 12.0 + drowse;
        this.right.targetUpperLidL = this.right.targetUpperLidR = 12.0 + drowse;
        break;
      }
      case 'LISTENING': {
        const breath = Math.sin(tSec * 3.0);
        this.left.targetHeight = this.right.targetHeight = 35.5 + 1.2 * breath;
        break;
      }
      case 'THINKING': {
        const scan = 2.5 * Math.sin(tSec * 1.7) + 1.2 * Math.sin(tSec * 2.9);
        this.left.targetX = this.left.baseX + 7 + scan;
        this.right.targetX = this.right.baseX + 7 + scan;
        break;
      }
      case 'SPEAKING': {
        // Se c'è un segnale audio RMS attivo, utilizzalo per modulare dinamicamente l'apertura
        let env = 0.5 + 0.32 * Math.sin(tSec * 6.8) + 0.18 * Math.sin(tSec * 10.7);
        if (this.audioRmsLevel > 0.01) {
          env = 0.3 + 0.7 * this.audioRmsLevel;
        }
        env = clampFloat(env, 0.0, 1.0);
        this.left.targetHeight = this.right.targetHeight = 27.0 + 6.0 * env;
        this.left.targetLowerLid = this.right.targetLowerLid = 2.0 + 3.5 * (1.0 - env);
        this.left.targetLowerArch = this.right.targetLowerArch = 4.0 + 2.5 * (1.0 - env);
        break;
      }
      case 'SURPRISED': {
        const pulse = Math.sin(tSec * 5.0);
        this.left.targetWidth = this.right.targetWidth = 34.0 + pulse;
        this.left.targetHeight = this.right.targetHeight = 38.0 + pulse;
        break;
      }
      case 'SHY': {
        const sway = Math.sin(tSec * 1.6) * 1.5;
        this.left.targetX = this.left.baseX - 3 + sway;
        this.right.targetX = this.right.baseX - 3 + sway;
        break;
      }
      case 'LOVE': {
        const beat = Math.abs(Math.sin(tSec * 3.8)) * 1.8;
        this.left.targetY = this.right.targetY = this.left.baseY - 1 - beat;
        break;
      }
      case 'WINK': {
        this.left.targetY = this.left.baseY - 1 + Math.sin(tSec * 2.8) * 0.8;
        break;
      }
      case 'CONFUSED': {
        const tilt = Math.sin(tSec * 2.2) * 1.5;
        this.left.targetX = this.left.baseX + 2 + tilt;
        this.right.targetX = this.right.baseX + 2 + tilt;
        break;
      }
      case 'MISCHIEVOUS': {
        const sly = Math.sin(tSec * 2.1) * 2.0;
        this.left.targetX = this.left.baseX + 5 + sly;
        this.right.targetX = this.right.baseX + 5 + sly;
        break;
      }
      case 'SLEEPING': {
        const breathe = Math.sin(tSec * 0.9);
        this.left.targetY = this.right.targetY = this.left.baseY + 3 + breathe;
        break;
      }
    }
  }

  interpolateEye(eye: EyeState, dtSec: number): void {
    const mult = this.profileSpeedScale() * this.transitionBoost;
    eye.x = smoothExp(eye.x, eye.targetX, 12.0 * mult, dtSec);
    eye.y = smoothExp(eye.y, eye.targetY, 12.0 * mult, dtSec);
    eye.width = smoothExp(eye.width, eye.targetWidth, 10.0 * mult, dtSec);
    eye.height = smoothExp(eye.height, eye.targetHeight, 10.0 * mult, dtSec);
    eye.cornerRadius = smoothExp(eye.cornerRadius, eye.targetCornerRadius, 10.0 * mult, dtSec);
    eye.lowerLid = smoothExp(eye.lowerLid, eye.targetLowerLid, 12.0 * mult, dtSec);
    eye.lowerArch = smoothExp(eye.lowerArch, eye.targetLowerArch, 12.0 * mult, dtSec);
    eye.upperLidL = smoothExp(eye.upperLidL, eye.targetUpperLidL, 12.0 * mult, dtSec);
    eye.upperLidR = smoothExp(eye.upperLidR, eye.targetUpperLidR, 12.0 * mult, dtSec);
    eye.upperArch = smoothExp(eye.upperArch, eye.targetUpperArch, 12.0 * mult, dtSec);
    eye.pupilDx = smoothExp(eye.pupilDx, eye.targetPupilDx, 14.0 * mult, dtSec);
    eye.pupilDy = smoothExp(eye.pupilDy, eye.targetPupilDy, 14.0 * mult, dtSec);
    eye.pupilRadius = smoothExp(eye.pupilRadius, eye.targetPupilRadius, 12.0 * mult, dtSec);
    eye.browOffset = smoothExp(eye.browOffset, eye.targetBrowOffset, 12.0 * mult, dtSec);
    eye.browTilt = smoothExp(eye.browTilt, eye.targetBrowTilt, 12.0 * mult, dtSec);
    eye.browArch = smoothExp(eye.browArch, eye.targetBrowArch, 12.0 * mult, dtSec);
    eye.shapePower = smoothExp(eye.shapePower, eye.targetShapePower, 10.0 * mult, dtSec);
    eye.taper = smoothExp(eye.taper, eye.targetTaper, 10.0 * mult, dtSec);
  }

  update(timeOrDt: number): void {
    let nowMs: number;
    if (timeOrDt <= 2.0) {
      // Delta time in secondi (ad es. 0.016) per simulazioni / test
      nowMs = (this.lastFrameMs || 0) + timeOrDt * 1000;
      this.updateStep(nowMs);
    } else {
      // Timestamp assoluto in ms (performance.now() o Date.now())
      nowMs = timeOrDt;
      const elapsed = nowMs - this.lastFrameMs;
      if (elapsed < this.frameIntervalMs) {
        return;
      }
      if (elapsed >= this.frameIntervalMs * 2 && elapsed < 2000) {
        this.droppedFrames += Math.floor(elapsed / this.frameIntervalMs) - 1;
      }
      this.updateStep(nowMs);
    }
  }

  updateStep(nowMs: number): void {
    let dtMs = nowMs >= this.lastFrameMs ? nowMs - this.lastFrameMs : this.frameIntervalMs;
    if (dtMs < 1) dtMs = 1;
    if (dtMs > 100) dtMs = 100;
    const dtSec = dtMs * 0.001;
    const instFps = 1000.0 / dtMs;
    this.actualFps = this.actualFps * 0.85 + instFps * 0.15;

    this.lastFrameMs = nowMs;

    this.updateBlinker(nowMs, dtSec);
    this.updateGaze(nowMs);
    this.updateMicroExpressions(nowMs);
    this.updateExpressionMotion(nowMs);
    this.interpolateEye(this.left, dtSec);
    this.interpolateEye(this.right, dtSec);
    this.transitionBoost = smoothExp(this.transitionBoost, 1.0, 6.0, dtSec);
    this.renderFrame(nowMs);
  }

  render(targetFb?: MonochromeFramebuffer): void {
    this.renderFrame(this.lastFrameMs || Date.now());
    if (targetFb && targetFb !== this.fb) {
      targetFb.loadRawBytes(this.fb.getBuffer());
    }
  }

  renderFrame(nowMs: number): void {
    this.renderToFramebuffer(nowMs);
  }

  drawSingleEye(eye: EyeState): void {
    const w = clampInt(roundHalfAway(eye.width), 12, 46);
    const rawH = clampInt(roundHalfAway(eye.height), 10, 48);

    // Occhio quasi completamente chiuso: linea curva delle ciglia
    if (eye.blinkSqueeze >= 0.85) {
      const cx = clampInt(roundHalfAway(eye.x), Math.floor(w / 2) + 4, FB_WIDTH - Math.floor(w / 2) - 4);
      const cy = clampInt(roundHalfAway(eye.y) + 2, 6, FB_HEIGHT - 6);
      const half = Math.floor(w / 2);
      for (let dx = -half; dx <= half; ++dx) {
        const u = dx / (half > 1 ? half : 1);
        const sag = roundHalfAway(1.5 * (1.0 - u * u));
        this.fb.setPixel(cx + dx, cy + sag, 1);
        this.fb.setPixel(cx + dx, cy + sag + 1, 1);
      }
      return;
    }

    const h = clampInt(roundHalfAway(rawH * (1.0 - 0.88 * eye.blinkSqueeze)), 4, 48);
    const cx = clampInt(roundHalfAway(eye.x), Math.floor(w / 2) + 4, FB_WIDTH - Math.floor(w / 2) - 4);
    const cy = clampInt(roundHalfAway(eye.y), Math.floor(h / 2) + 6, FB_HEIGHT - Math.floor(h / 2) - 5);
    const rx = w * 0.5;
    const ry = h * 0.5;
    const p = eye.shapePower > 2.0 ? eye.shapePower : 2.0;

    // Rasterizzazione Superellisse Organica con Tapering
    const halfH = Math.floor(h / 2);
    for (let dy = -halfH; dy <= halfH; ++dy) {
      const v = ry > 0.0 ? dy / ry : 0.0;
      const av = Math.min(1.0, Math.abs(v));
      const taperScale = 1.0 - eye.taper * v;
      const inner = 1.0 - Math.pow(av, p);
      const spanX = rx * taperScale * Math.pow(inner > 0 ? inner : 0, 1.0 / p);
      const halfX = Math.floor(spanX);
      const py = cy + dy;
      if (py >= 4 && py <= FB_HEIGHT - 5) {
        for (let dx = -halfX; dx <= halfX; ++dx) {
          const px = cx + dx;
          if (px >= 4 && px <= FB_WIDTH - 5) {
            this.fb.setPixel(px, py, 1);
          }
        }
      }
    }

    const x = cx - Math.floor(w / 2);
    const y = cy - Math.floor(h / 2);

    // Maschere Palpebrali
    if (eye.blinkSqueeze < 0.65) {
      const halfW = (w - 1) * 0.5;

      if (eye.lowerLid > 0.4 || eye.lowerArch > 0.4) {
        for (let col = 0; col < w; ++col) {
          const u = halfW > 0 ? (col - halfW) / halfW : 0;
          const curve = 1.0 - u * u;
          const maskTop = roundHalfAway((y + h) - eye.lowerLid - eye.lowerArch * curve);
          for (let py = maskTop; py <= y + h + 1; ++py) {
            this.fb.setPixel(x + col, py, 0);
          }
        }
      }

      if (eye.upperLidL > 0.4 || eye.upperLidR > 0.4 || eye.upperArch > 0.4) {
        const maxUl = Math.max(eye.upperLidL, eye.upperLidR);
        for (let col = 0; col < w; ++col) {
          const frac = w > 1 ? col / (w - 1) : 0.5;
          const u = halfW > 0 ? (col - halfW) / halfW : 0;
          const curve = 1.0 - u * u;
          const lidY = eye.upperLidL + (eye.upperLidR - eye.upperLidL) * frac;
          const maskBot = roundHalfAway(y + lidY + eye.upperArch * curve);
          for (let py = y - 2; py <= maskBot; ++py) {
            this.fb.setPixel(x + col, py, 0);
          }
          if (maxUl >= 12.0 && maskBot >= 4 && maskBot <= FB_HEIGHT - 6) {
            this.fb.setPixel(x + col, maskBot + 1, 1);
          }
        }
      }
    }

    // Pupilla Scura + Riflessi Futuristi (Catchlights)
    if (eye.blinkSqueeze < 0.45 && eye.pupilRadius >= 2.5) {
      const maxRFit = Math.floor(Math.min(w, h) / 2) - 4;
      const pr = clampInt(roundHalfAway(eye.pupilRadius), 3, Math.max(3, maxRFit));
      const topMask = roundHalfAway(Math.max(eye.upperLidL, eye.upperLidR) + eye.upperArch * 0.5);
      const botMask = roundHalfAway(eye.lowerLid + eye.lowerArch * 0.5);
      const minPx = x + pr + 4;
      const maxPx = x + w - 1 - pr - 4;
      const minPy = y + topMask + pr + 2;
      const maxPy = y + h - 1 - botMask - pr - 2;

      if (minPx <= maxPx && minPy <= maxPy) {
        const px = clampInt(roundHalfAway(cx + eye.pupilDx), minPx, maxPx);
        const py = clampInt(roundHalfAway(cy + eye.pupilDy), minPy, maxPy);
        this.fb.fillCircle(px, py, pr, 0);

        // Catchlight primario 2x2
        const gx = px - Math.floor(pr / 2) + 1;
        const gy = py - Math.floor(pr / 2) + 1;
        this.fb.setPixel(gx, gy, 1);
        this.fb.setPixel(gx + 1, gy, 1);
        this.fb.setPixel(gx, gy + 1, 1);
        this.fb.setPixel(gx + 1, gy + 1, 1);

        // Catchlight secondario
        if (pr >= 5) {
          this.fb.setPixel(px + Math.floor(pr / 2) - 1, py + Math.floor(pr / 2) - 1, 1);
        }
      }
    }

    // Sopracciglio Scolpito
    if (eye.browOffset >= 1.0 && eye.blinkSqueeze < 0.7) {
      const bw = clampInt(w - 6, 14, 34);
      const bx0 = clampInt(cx - Math.floor(bw / 2), 4, FB_WIDTH - bw - 4);
      const byBase = clampInt(y - roundHalfAway(eye.browOffset), 4, FB_HEIGHT - 8);

      for (let col = 0; col < bw; ++col) {
        const frac = bw > 1 ? col / (bw - 1) : 0.5;
        const u = (frac - 0.5) * 2.0;
        const arch = eye.browArch * (1.0 - u * u);
        const tilt = eye.browTilt * (frac - 0.5);
        const py = clampInt(roundHalfAway(byBase + tilt - arch), 4, FB_HEIGHT - 6);
        const thick = Math.abs(u) < 0.55 ? 3 : 2;
        for (let t = 0; t < thick; ++t) {
          this.fb.setPixel(bx0 + col, py + t, 1);
        }
      }
    }
  }

  drawHappyCrescent(eye: EyeState): void {
    const cx = clampInt(roundHalfAway(eye.x), 22, FB_WIDTH - 22);
    const cy = clampInt(roundHalfAway(eye.y), 16, FB_HEIGHT - 14);
    const kHalf = 16;
    for (let dx = -kHalf; dx <= kHalf; ++dx) {
      const u = dx / kHalf;
      const arch = roundHalfAway(9.0 * (1.0 - u * u));
      const py = cy + 3 - arch;
      const au = Math.abs(u);
      const thick = au < 0.65 ? 5 : (au < 0.85 ? 4 : 3);
      for (let t = 0; t < thick; ++t) {
        this.fb.setPixel(cx + dx, py + t, 1);
      }
    }
    // Sopracciglio felice superiore
    const kBw = 26;
    const bx0 = cx - Math.floor(kBw / 2);
    const by0 = Math.max(5, cy - 15);
    for (let col = 0; col < kBw; ++col) {
      const u = (col / (kBw - 1) - 0.5) * 2.0;
      const pyRaw = by0 - roundHalfAway(3.0 * (1.0 - u * u));
      const py = Math.max(4, pyRaw);
      this.fb.setPixel(bx0 + col, py, 1);
      this.fb.setPixel(bx0 + col, py + 1, 1);
    }
  }

  drawPlumpHeart(cx: number, cy: number): void {
    const clampedCx = clampInt(cx, 18, FB_WIDTH - 18);
    const clampedCy = clampInt(cy, 18, FB_HEIGHT - 18);
    for (let dy = -14; dy < 14; ++dy) {
      for (let dx = -14; dx <= 14; ++dx) {
        const nx = dx / 11.5;
        const ny = -(dy + 1.5) / 10.5;
        const r2 = nx * nx + ny * ny - 1.0;
        const val = r2 * r2 * r2 - (nx * nx) * (ny * ny * ny);
        if (val <= 0.0) {
          this.fb.setPixel(clampedCx + dx, clampedCy + dy, 1);
        }
      }
    }
    // Riflesso glossy sul lobo sinistro
    this.fb.setPixel(clampedCx - 6, clampedCy - 5, 0);
    this.fb.setPixel(clampedCx - 5, clampedCy - 5, 0);
    this.fb.setPixel(clampedCx - 6, clampedCy - 4, 0);
  }

  drawGlyph(ox: number, oy: number, pattern: string[], rows: number, scale = 1): void {
    for (let r = 0; r < rows; ++r) {
      const row = pattern[r];
      for (let c = 0; c < row.length; ++c) {
        if (row[c] === '1') {
          for (let sy = 0; sy < scale; ++sy) {
            for (let sx = 0; sx < scale; ++sx) {
              const px = clampInt(ox + c * scale + sx, 4, FB_WIDTH - 5);
              const py = clampInt(oy + r * scale + sy, 4, FB_HEIGHT - 5);
              this.fb.setPixel(px, py, 1);
            }
          }
        }
      }
    }
  }

  drawSleepingLash(eye: EyeState): void {
    const cx = clampInt(roundHalfAway(eye.x), 22, FB_WIDTH - 22);
    const cy = clampInt(roundHalfAway(eye.y), 16, FB_HEIGHT - 16);
    const kHalf = 15;
    for (let dx = -kHalf; dx <= kHalf; ++dx) {
      const u = dx / kHalf;
      const sag = roundHalfAway(5.0 * (1.0 - u * u));
      const py = cy - 1 + sag;
      const thick = Math.abs(u) < 0.7 ? 4 : 3;
      for (let t = 0; t < thick; ++t) {
        this.fb.setPixel(cx + dx, py + t, 1);
      }
    }
  }

  renderToFramebuffer(nowMs: number): void {
    this.fb.clear();

    if (this.expr === 'LOVE') {
      const beat = (Math.floor(nowMs / 260) % 2) === 0 ? 1 : 0;
      this.drawPlumpHeart(roundHalfAway(this.left.x), roundHalfAway(this.left.y) - beat);
      this.drawPlumpHeart(roundHalfAway(this.right.x), roundHalfAway(this.right.y) - beat);
      return;
    }

    if (this.expr === 'HAPPY') {
      this.drawHappyCrescent(this.left);
      this.drawHappyCrescent(this.right);
      const cxs = [roundHalfAway(this.left.x) - 14, roundHalfAway(this.right.x) + 14];
      for (const cx of cxs) {
        this.fb.setPixel(cx, 48, 1);
        this.fb.setPixel(cx + 1, 47, 1);
        this.fb.setPixel(cx + 2, 48, 1);
      }
      return;
    }

    if (this.expr === 'WINK') {
      this.drawSingleEye(this.left);
      this.drawHappyCrescent(this.right);
      return;
    }

    if (this.expr === 'SLEEPING') {
      this.drawSleepingLash(this.left);
      this.drawSleepingLash(this.right);
      const phase = Math.floor(nowMs / 450) % 3;
      const kZSmall = ["1111", "..1.", ".1..", "1111"];
      const kZBig = ["11111", "...1.", "..1..", ".1...", "11111"];
      this.drawGlyph(98, 14 - phase, kZSmall, 4, 1);
      this.drawGlyph(106, 7 - phase, kZBig, 5, 1);
      return;
    }

    this.drawSingleEye(this.left);
    this.drawSingleEye(this.right);
  }
}
