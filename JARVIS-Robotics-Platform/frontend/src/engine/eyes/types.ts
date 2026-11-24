/**
 * JARVIS Robotics Platform — Eyes 3.0 Types & Constants
 * 
 * Definizione tipizzata delle espressioni, micro-espressioni, profili visivi
 * e stati interpolati degli occhi (Eyes 3.0 Baseline: JARVIS Original Premium).
 */

export type Expression =
  | 'NEUTRAL'
  | 'HAPPY'
  | 'CURIOUS'
  | 'SLEEPY'
  | 'LISTENING'
  | 'THINKING'
  | 'SPEAKING'
  | 'SURPRISED'
  | 'SHY'
  | 'LOVE'
  | 'WINK'
  | 'CONFUSED'
  | 'MISCHIEVOUS'
  | 'SLEEPING';

export const ALL_EXPRESSIONS: Expression[] = [
  'NEUTRAL',
  'HAPPY',
  'CURIOUS',
  'SLEEPY',
  'LISTENING',
  'THINKING',
  'SPEAKING',
  'SURPRISED',
  'SHY',
  'LOVE',
  'WINK',
  'CONFUSED',
  'MISCHIEVOUS',
  'SLEEPING'
];

export type VisualProfile = 'CALM' | 'LIVELY' | 'PLAYFUL';

export const ALL_PROFILES: VisualProfile[] = ['CALM', 'LIVELY', 'PLAYFUL'];

export type MicroExpression =
  | 'NONE'
  | 'BrowRaise'
  | 'SideGlance'
  | 'QuickWink'
  | 'EyeSmile'
  | 'PupilPulse';

export const ALL_MICRO_EXPRESSIONS: MicroExpression[] = [
  'NONE',
  'BrowRaise',
  'SideGlance',
  'QuickWink',
  'EyeSmile',
  'PupilPulse'
];

export enum BlinkPhase {
  OPEN = 0,
  CLOSING = 1,
  HOLD_CLOSED = 2,
  OPENING = 3
}

export interface EyeState {
  baseX: number;
  baseY: number;

  x: number;
  y: number;
  targetX: number;
  targetY: number;

  width: number;
  height: number;
  targetWidth: number;
  targetHeight: number;

  shapePower: number;
  targetShapePower: number;
  taper: number;
  targetTaper: number;

  cornerRadius: number;
  targetCornerRadius: number;

  lowerLid: number;
  targetLowerLid: number;
  lowerArch: number;
  targetLowerArch: number;

  upperLidL: number;
  upperLidR: number;
  targetUpperLidL: number;
  targetUpperLidR: number;
  upperArch: number;
  targetUpperArch: number;

  pupilDx: number;
  targetPupilDx: number;
  pupilDy: number;
  targetPupilDy: number;
  pupilRadius: number;
  targetPupilRadius: number;

  browOffset: number;
  targetBrowOffset: number;
  browTilt: number;
  targetBrowTilt: number;
  browArch: number;
  targetBrowArch: number;

  blinkSqueeze: number; // 0.0 = aperto, 1.0 = completamente chiuso
}

export interface EyeParams {
  width: number;
  height: number;
  shapePower: number;
  taper: number;
  cornerRadius: number;
  spacingPx: number;
  pupilRadius: number;
  browOffset: number;
  browArch: number;
  browTilt: number;
}

export interface SkinDefinition {
  skin_id: string;
  schema_version: string;
  name: string;
  description: string;
  author: string;
  skin_version: string;
  target_display: {
    type: 'monochrome_1bit';
    width: number;
    height: number;
  };
  base_geometry: {
    width: number;
    height: number;
    shape_power: number;
    taper: number;
    corner_radius: number;
    spacing_px: number;
    pupil: {
      shape: string;
      radius: number;
      catchlight: string;
    };
    eyebrows?: {
      offset: number;
      arch: number;
      tilt: number;
    };
    eyelashes?: {
      enabled: boolean;
      count: number;
      length_px: number;
      curvature: number;
    };
  };
  visual_behavior_profile_default: VisualProfile;
  expressions: Record<string, any>;
  motion: {
    natural_gaze: {
      enabled: boolean;
      micro_saccades_enabled: boolean;
      max_offset_x: number;
      max_offset_y: number;
      suppress_in_listening: boolean;
    };
    advanced_blink: {
      enabled: boolean;
      close_rate: number;
      open_rate: number;
      hold_closed_ms: number;
      double_blink_chance_pct: number;
    };
    interpolation: {
      algorithm: string;
      base_decay_rate: number;
    };
  };
  voice_reactivity: {
    enabled: boolean;
    target_ocular_element: string;
    max_deviation_px: number;
    smoothing_factor: number;
  };
  fallback?: {
    fallback_skin_id: string;
  };
}
