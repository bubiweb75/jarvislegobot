/**
 * JARVIS Robotics Platform — Official Baseline & Catalogue
 * 
 * Contiene la definizione immutabile della Golden Baseline:
 * 'JARVIS Original Premium — Organic Visor Companion' (Eyes 3.0)
 * e i profili dimostrativi del catalogo RP-02 (EVA, NOVA, TARS, NEKO).
 */

import { SkinDefinition } from './types';

export const JARVIS_ORIGINAL_PREMIUM_SKIN: Readonly<SkinDefinition> = Object.freeze({
  skin_id: "skin-jarvis-original-v3",
  schema_version: "1.0.0",
  name: "JARVIS Original Premium — Organic Visor Companion",
  description: "Baseline grafica ufficiale Eyes 3.0. Geometrie superellittiche organiche 38x38 px, 14 espressioni e micro-espressioni.",
  author: "JARVIS Platform Team",
  skin_version: "3.0.0",
  target_display: {
    type: "monochrome_1bit" as const,
    width: 128,
    height: 64
  },
  base_geometry: {
    width: 38.0,
    height: 38.0,
    shape_power: 2.6,
    taper: 0.10,
    corner_radius: 11.0,
    spacing_px: 16,
    pupil: {
      shape: "circle",
      radius: 7.0,
      catchlight: "double_offset"
    },
    eyebrows: {
      offset: 4.0,
      arch: 2.2,
      tilt: 0.0
    }
  },
  visual_behavior_profile_default: "LIVELY",
  expressions: {
    NEUTRAL: { render_mode: "parametric", width: 38.0, height: 38.0, shape_power: 2.6, corner_radius: 11.0, pupil_radius: 7.0 },
    HAPPY: { render_mode: "crescent", width: 36.0, height: 24.0, pupil_radius: 0.0, brow_offset: 6.0, brow_arch: 3.5 },
    CURIOUS: { render_mode: "parametric", width: 38.0, height: 38.0 },
    SLEEPY: { render_mode: "parametric", width: 36.0, height: 30.0 },
    LISTENING: { render_mode: "parametric", width: 38.0, height: 42.0 },
    THINKING: { render_mode: "parametric", width: 35.0, height: 31.0 },
    SPEAKING: { render_mode: "parametric", width: 37.0, height: 35.0 },
    SURPRISED: { render_mode: "parametric", width: 39.0, height: 45.0 },
    SHY: { render_mode: "parametric", width: 32.0, height: 28.0 },
    LOVE: { render_mode: "heart", width: 34.0, height: 34.0 },
    WINK: { render_mode: "parametric", width: 38.0, height: 38.0 },
    CONFUSED: { render_mode: "parametric", width: 36.0, height: 36.0 },
    MISCHIEVOUS: { render_mode: "parametric", width: 37.0, height: 32.0 },
    SLEEPING: { render_mode: "sleeping_lash", width: 34.0, height: 18.0 }
  },
  motion: {
    natural_gaze: { enabled: true, micro_saccades_enabled: true, max_offset_x: 8.0, max_offset_y: 4.0, suppress_in_listening: true },
    advanced_blink: { enabled: true, close_rate: 15.0, open_rate: 10.0, hold_closed_ms: 60, double_blink_chance_pct: 10 },
    interpolation: { algorithm: "exponential_decay", base_decay_rate: 12.0 }
  },
  voice_reactivity: { enabled: true, target_ocular_element: "lower_eyelid_arch", max_deviation_px: 4.0, smoothing_factor: 0.65 },
  fallback: { fallback_skin_id: "skin-jarvis-original-v3" }
});

export const EVA_SKIN: Readonly<SkinDefinition> = Object.freeze({
  skin_id: "skin-eva-elegant-v1",
  schema_version: "1.0.0",
  name: "EVA Elegant Soft Companion",
  description: "Occhi dolci e morbidi, superellisse p=2.4 con raggio di raccordo ampio.",
  author: "JARVIS Platform Team",
  skin_version: "1.0.0",
  target_display: { type: "monochrome_1bit" as const, width: 128, height: 64 },
  base_geometry: {
    width: 36.0,
    height: 40.0,
    shape_power: 2.3,
    taper: 0.08,
    corner_radius: 14.0,
    spacing_px: 18,
    pupil: { shape: "circle", radius: 7.5, catchlight: "single_large" },
    eyebrows: { offset: 5.0, arch: 2.8, tilt: -1.0 }
  },
  visual_behavior_profile_default: "CALM",
  expressions: { ...JARVIS_ORIGINAL_PREMIUM_SKIN.expressions },
  motion: {
    natural_gaze: { enabled: true, micro_saccades_enabled: false, max_offset_x: 6.0, max_offset_y: 3.0, suppress_in_listening: true },
    advanced_blink: { enabled: true, close_rate: 12.0, open_rate: 8.0, hold_closed_ms: 80, double_blink_chance_pct: 5 },
    interpolation: { algorithm: "exponential_decay", base_decay_rate: 9.0 }
  },
  voice_reactivity: { enabled: true, target_ocular_element: "lower_eyelid_arch", max_deviation_px: 3.5, smoothing_factor: 0.70 },
  fallback: { fallback_skin_id: "skin-jarvis-original-v3" }
});

export const NOVA_SKIN: Readonly<SkinDefinition> = Object.freeze({
  skin_id: "skin-nova-hud-v1",
  schema_version: "1.0.0",
  name: "NOVA Futuristic HUD",
  description: "Stile visor tecnologico e squadrato p=3.6 con rastremazione marcata.",
  author: "JARVIS Platform Team",
  skin_version: "1.0.0",
  target_display: { type: "monochrome_1bit" as const, width: 128, height: 64 },
  base_geometry: {
    width: 32.0,
    height: 34.0,
    shape_power: 3.6,
    taper: 0.22,
    corner_radius: 6.0,
    spacing_px: 14,
    pupil: { shape: "circle", radius: 5.5, catchlight: "double_offset" },
    eyebrows: { offset: 4.5, arch: 1.0, tilt: 3.0 }
  },
  visual_behavior_profile_default: "CALM",
  expressions: { ...JARVIS_ORIGINAL_PREMIUM_SKIN.expressions },
  motion: {
    natural_gaze: { enabled: true, micro_saccades_enabled: true, max_offset_x: 10.0, max_offset_y: 5.0, suppress_in_listening: false },
    advanced_blink: { enabled: true, close_rate: 20.0, open_rate: 16.0, hold_closed_ms: 40, double_blink_chance_pct: 15 },
    interpolation: { algorithm: "exponential_decay", base_decay_rate: 16.0 }
  },
  voice_reactivity: { enabled: true, target_ocular_element: "lower_eyelid_arch", max_deviation_px: 5.0, smoothing_factor: 0.50 },
  fallback: { fallback_skin_id: "skin-jarvis-original-v3" }
});

export const TARS_SKIN: Readonly<SkinDefinition> = Object.freeze({
  skin_id: "skin-tars-geometric-v1",
  schema_version: "1.0.0",
  name: "TARS Geometric Monolith",
  description: "Forma monolitica ultra-squadrata p=4.8 a feritoia orizzontale.",
  author: "JARVIS Platform Team",
  skin_version: "1.0.0",
  target_display: { type: "monochrome_1bit" as const, width: 128, height: 64 },
  base_geometry: {
    width: 42.0,
    height: 22.0,
    shape_power: 4.8,
    taper: 0.02,
    corner_radius: 3.0,
    spacing_px: 12,
    pupil: { shape: "slit", radius: 4.0, catchlight: "none" },
    eyebrows: { offset: 3.0, arch: 0.0, tilt: 0.0 }
  },
  visual_behavior_profile_default: "CALM",
  expressions: { ...JARVIS_ORIGINAL_PREMIUM_SKIN.expressions },
  motion: {
    natural_gaze: { enabled: false, micro_saccades_enabled: false, max_offset_x: 4.0, max_offset_y: 0.0, suppress_in_listening: true },
    advanced_blink: { enabled: true, close_rate: 25.0, open_rate: 20.0, hold_closed_ms: 50, double_blink_chance_pct: 0 },
    interpolation: { algorithm: "exponential_decay", base_decay_rate: 20.0 }
  },
  voice_reactivity: { enabled: true, target_ocular_element: "lower_eyelid_arch", max_deviation_px: 2.0, smoothing_factor: 0.80 },
  fallback: { fallback_skin_id: "skin-jarvis-original-v3" }
});

export const NEKO_SKIN: Readonly<SkinDefinition> = Object.freeze({
  skin_id: "skin-neko-feline-v1",
  schema_version: "1.0.0",
  name: "NEKO Feline Companion",
  description: "Occhi verticali stile felino, pupilla a fessura e reattività vivace.",
  author: "JARVIS Platform Team",
  skin_version: "1.0.0",
  target_display: { type: "monochrome_1bit" as const, width: 128, height: 64 },
  base_geometry: {
    width: 36.0,
    height: 42.0,
    shape_power: 2.2,
    taper: 0.12,
    corner_radius: 12.0,
    spacing_px: 16,
    pupil: { shape: "slit_vertical", radius: 8.0, catchlight: "sparkle" },
    eyebrows: { offset: 5.5, arch: 3.0, tilt: -2.0 }
  },
  visual_behavior_profile_default: "PLAYFUL",
  expressions: { ...JARVIS_ORIGINAL_PREMIUM_SKIN.expressions },
  motion: {
    natural_gaze: { enabled: true, micro_saccades_enabled: true, max_offset_x: 9.0, max_offset_y: 5.0, suppress_in_listening: false },
    advanced_blink: { enabled: true, close_rate: 18.0, open_rate: 14.0, hold_closed_ms: 60, double_blink_chance_pct: 25 },
    interpolation: { algorithm: "exponential_decay", base_decay_rate: 14.0 }
  },
  voice_reactivity: { enabled: true, target_ocular_element: "lower_eyelid_arch", max_deviation_px: 4.5, smoothing_factor: 0.60 },
  fallback: { fallback_skin_id: "skin-jarvis-original-v3" }
});

export const CATALOG_SKINS: SkinDefinition[] = [
  JARVIS_ORIGINAL_PREMIUM_SKIN,
  EVA_SKIN,
  NOVA_SKIN,
  TARS_SKIN,
  NEKO_SKIN
];

export const CATALOGUE_IDENTITIES = [
  {
    id: "identity-jarvis-original-v3",
    name: "JARVIS Original",
    subtitle: "Maggiordomo Tecnologico (Golden Baseline)",
    status: "PRODUZIONE / ATTIVO",
    statusType: "active" as const,
    voice: "Riccardo (Piper TTS ONNX)",
    wakeword: "Hey Jarvis (microWakeWord ACTIVE)",
    skin: "JARVIS Original Premium",
    skinId: "skin-jarvis-original-v3",
    profile: "LIVELY" as const,
    description: "Assistente brillante, professionale e cordiale. Riproduzione 1:1 dell'originale."
  },
  {
    id: "identity-eva-elegant-v1",
    name: "EVA",
    subtitle: "Compagna Empatica e Rassicurante",
    status: "ANTEPRIMA SPERIMENTALE (RP-03)",
    statusType: "preview" as const,
    voice: "Paola (Piper TTS ONNX)",
    wakeword: "Hey Eva (Modello DESIRED)",
    skin: "EVA Elegant Soft Companion",
    skinId: "skin-eva-elegant-v1",
    profile: "CALM" as const,
    description: "Sguardo morbido e fluido, ciglia stilizzate e transizioni delicate ad alta empatia."
  },
  {
    id: "identity-nova-hud-v1",
    name: "NOVA",
    subtitle: "Interfaccia Scientifica & Telemetria",
    status: "ANTEPRIMA SPERIMENTALE (RP-03)",
    statusType: "preview" as const,
    voice: "Riccardo / Sintetico (1.10x)",
    wakeword: "Hey Nova (Modello DESIRED)",
    skin: "NOVA Futuristic HUD",
    skinId: "skin-nova-hud-v1",
    profile: "CALM" as const,
    description: "Linee squadrate e precisione geometrica, ottimizzata per visualizzazione telemetrica."
  },
  {
    id: "identity-tars-geometric-v1",
    name: "TARS",
    subtitle: "Robot Tattico Sarcastico",
    status: "ANTEPRIMA SPERIMENTALE (RP-03)",
    statusType: "preview" as const,
    voice: "Corrado (Piper TTS Basso)",
    wakeword: "Hey Tars (Modello DESIRED)",
    skin: "TARS Geometric Monolith",
    skinId: "skin-tars-geometric-v1",
    profile: "CALM" as const,
    description: "Blocchi geometrici essenziali, movimenti asciutti e parametro umorismo al 75%."
  },
  {
    id: "identity-neko-feline-v1",
    name: "NEKO",
    subtitle: "Cucciolo Felino Elettronico",
    status: "ANTEPRIMA SPERIMENTALE (RP-03)",
    statusType: "preview" as const,
    voice: "Paola (Pitch +4.0 st)",
    wakeword: "Hey Neko (Modello DESIRED)",
    skin: "NEKO Feline Companion",
    skinId: "skin-neko-feline-v1",
    profile: "PLAYFUL" as const,
    description: "Pupille a fessura verticale, orecchie e baffi assenti (grafica 100% oculare), reattivo a carezze touch."
  }
];

export function cloneSkin(skin: SkinDefinition): SkinDefinition {
  return JSON.parse(JSON.stringify(skin));
}
