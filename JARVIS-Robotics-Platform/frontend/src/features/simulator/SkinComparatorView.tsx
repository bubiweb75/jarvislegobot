import React, { useState, useEffect, useRef } from 'react';
import { SkinDefinition, Expression, VisualProfile, ALL_EXPRESSIONS, ALL_PROFILES } from '../../engine/eyes/types';
import { JARVIS_ORIGINAL_PREMIUM_SKIN, CATALOG_SKINS } from '../../engine/eyes/baseline';
import { EyeEngine } from '../../engine/eyes/EyeEngine';
import { MonochromeFramebuffer } from '../../engine/framebuffer/MonochromeFramebuffer';
import { OledDisplay } from '../../components/OledDisplay';
import { Play, Pause, StepForward, RefreshCw, Sliders } from 'lucide-react';

interface SkinComparatorViewProps {
  customSkin?: SkinDefinition;
}

export const SkinComparatorView: React.FC<SkinComparatorViewProps> = ({ customSkin }) => {
  const [candidateSkinId, setCandidateSkinId] = useState<string>(
    customSkin ? customSkin.skin_id : 'skin-eva-elegant-v1'
  );
  const [selectedExpr, setSelectedExpr] = useState<Expression>('NEUTRAL');
  const [selectedProfile, setSelectedProfile] = useState<VisualProfile>('CALM');
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [zoom, setZoom] = useState<2 | 3 | 4 | 5 | 6 | 8>(3);
  const [glow, setGlow] = useState<boolean>(true);

  // Engines
  const baselineEngineRef = useRef<EyeEngine | null>(null);
  const candidateEngineRef = useRef<EyeEngine | null>(null);

  // Framebuffers
  const baselineFbRef = useRef<MonochromeFramebuffer>(new MonochromeFramebuffer());
  const candidateFbRef = useRef<MonochromeFramebuffer>(new MonochromeFramebuffer());

  const [, setTick] = useState<number>(0);
  const animFrameRef = useRef<number | null>(null);

  // Selected Candidate Skin
  const candidateSkin =
    customSkin && customSkin.skin_id === candidateSkinId
      ? customSkin
      : CATALOG_SKINS.find((s) => s.skin_id === candidateSkinId) || CATALOG_SKINS[1];

  // Initialize Engines
  useEffect(() => {
    baselineEngineRef.current = new EyeEngine(JARVIS_ORIGINAL_PREMIUM_SKIN);
    candidateEngineRef.current = new EyeEngine(candidateSkin);

    baselineEngineRef.current.setExpression(selectedExpr);
    candidateEngineRef.current.setExpression(selectedExpr);

    baselineEngineRef.current.setVisualProfile(selectedProfile);
    candidateEngineRef.current.setVisualProfile(selectedProfile);
  }, [candidateSkinId, customSkin]);

  // Sync Expressions & Profiles
  useEffect(() => {
    if (baselineEngineRef.current) baselineEngineRef.current.setExpression(selectedExpr);
    if (candidateEngineRef.current) candidateEngineRef.current.setExpression(selectedExpr);
  }, [selectedExpr]);

  useEffect(() => {
    if (baselineEngineRef.current) baselineEngineRef.current.setVisualProfile(selectedProfile);
    if (candidateEngineRef.current) candidateEngineRef.current.setVisualProfile(selectedProfile);
  }, [selectedProfile]);

  // Sync Blink
  const handleTriggerBlink = () => {
    if (baselineEngineRef.current) baselineEngineRef.current.triggerBlink();
    if (candidateEngineRef.current) candidateEngineRef.current.triggerBlink();
  };

  // Sync Step
  const handleStep = (stepMs = 16) => {
    const dt = stepMs / 1000;
    if (baselineEngineRef.current && candidateEngineRef.current) {
      baselineEngineRef.current.update(dt);
      baselineEngineRef.current.render(baselineFbRef.current);

      candidateEngineRef.current.update(dt);
      candidateEngineRef.current.render(candidateFbRef.current);

      setTick((t) => (t + 1) % 1000000);
    }
  };

  // Synchronous Animation Loop
  useEffect(() => {
    let lastTime = performance.now();

    const loop = (currentTime: number) => {
      const dt = (currentTime - lastTime) / 1000;
      lastTime = currentTime;

      if (isPlaying && baselineEngineRef.current && candidateEngineRef.current) {
        baselineEngineRef.current.update(dt);
        baselineEngineRef.current.render(baselineFbRef.current);

        candidateEngineRef.current.update(dt);
        candidateEngineRef.current.render(candidateFbRef.current);

        setTick((t) => (t + 1) % 1000000);
      }

      animFrameRef.current = requestAnimationFrame(loop);
    };

    animFrameRef.current = requestAnimationFrame(loop);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPlaying]);

  // Calculate Diff Metrics
  const baseGeom = JARVIS_ORIGINAL_PREMIUM_SKIN.base_geometry;
  const candGeom = candidateSkin.base_geometry;

  const deltaW = candGeom.width - baseGeom.width;
  const deltaH = candGeom.height - baseGeom.height;
  const deltaP = candGeom.shape_power - baseGeom.shape_power;
  const deltaS = candGeom.spacing_px - baseGeom.spacing_px;
  const deltaT = candGeom.taper - baseGeom.taper;

  // Calculate Lit Pixels Count
  const countLit = (fb: MonochromeFramebuffer) => {
    let count = 0;
    const buf = fb.getBuffer();
    for (let i = 0; i < buf.length; i++) {
      let b = buf[i];
      while (b > 0) {
        count += b & 1;
        b >>= 1;
      }
    }
    return count;
  };

  const baseLit = countLit(baselineFbRef.current);
  const candLit = countLit(candidateFbRef.current);
  const deltaLit = candLit - baseLit;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-jarvis-panel border border-jarvis-border p-6 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              DUAL-OLED COMPARATOR
            </span>
            <span className="text-xs text-jarvis-muted font-mono">Verifica Ottica Simultanea</span>
          </div>
          <h2 className="text-xl font-bold text-white">Comparatore Side-by-Side: Baseline vs Variante</h2>
          <p className="text-xs text-jarvis-muted">
            Confronto frame-per-frame in sincronia d'orologio tra la Golden Baseline JARVIS e qualsiasi skin candidata.
          </p>
        </div>

        {/* Sync Controls */}
        <div className="flex items-center gap-2 bg-jarvis-card p-1.5 rounded-lg border border-jarvis-border">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              isPlaying
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
            }`}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            {isPlaying ? 'Pausa Sincrona' : 'Riproduci'}
          </button>

          <button
            onClick={() => handleStep(16)}
            disabled={isPlaying}
            className="px-2.5 py-1.5 bg-jarvis-panel hover:bg-jarvis-border disabled:opacity-40 text-jarvis-text text-xs rounded border border-jarvis-border flex items-center gap-1 transition-colors"
            title="Avanza 1 frame (+16ms)"
          >
            <StepForward className="w-3.5 h-3.5" />
            +1F
          </button>

          <button
            onClick={handleTriggerBlink}
            className="px-2.5 py-1.5 bg-jarvis-panel hover:bg-jarvis-border text-jarvis-text text-xs rounded border border-jarvis-border flex items-center gap-1 transition-colors"
            title="Attiva blink sincrono"
          >
            <RefreshCw className="w-3.5 h-3.5 text-jarvis-cyan" />
            Blink Sincrono
          </button>
        </div>
      </div>

      {/* Synchronized Selectors */}
      <div className="bg-jarvis-panel border border-jarvis-border p-4 rounded-xl flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-jarvis-muted font-medium">Variante Candidata:</span>
          <select
            value={candidateSkinId}
            onChange={(e) => setCandidateSkinId(e.target.value)}
            className="bg-jarvis-card border border-jarvis-border text-white text-xs rounded px-2.5 py-1"
          >
            {customSkin && <option value={customSkin.skin_id}>Skin Corrente Editor ({customSkin.name})</option>}
            {CATALOG_SKINS.map((s) => (
              <option key={s.skin_id} value={s.skin_id}>
                {s.name} ({s.skin_id})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-jarvis-muted font-medium">Espressione:</span>
          <select
            value={selectedExpr}
            onChange={(e) => setSelectedExpr(e.target.value as Expression)}
            className="bg-jarvis-card border border-jarvis-border text-white text-xs rounded px-2.5 py-1"
          >
            {ALL_EXPRESSIONS.map((expr) => (
              <option key={expr} value={expr}>
                {expr}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-jarvis-muted font-medium">Profilo Dinamico:</span>
          <div className="flex gap-1">
            {ALL_PROFILES.map((p) => (
              <button
                key={p}
                onClick={() => setSelectedProfile(p)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono border transition-colors ${
                  selectedProfile === p
                    ? 'bg-jarvis-cyan text-black font-semibold border-jarvis-cyan'
                    : 'bg-jarvis-card border-jarvis-border text-jarvis-muted'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={zoom}
            onChange={(e) => setZoom(parseInt(e.target.value) as 2 | 3 | 4 | 5 | 6 | 8)}
            className="bg-jarvis-card border border-jarvis-border text-white text-[11px] rounded px-2.5 py-1"
          >
            <option value={2}>Zoom 2x</option>
            <option value={3}>Zoom 3x</option>
            <option value={4}>Zoom 4x</option>
          </select>
          <button
            onClick={() => setGlow(!glow)}
            className={`text-[10px] px-2 py-0.5 rounded border ${
              glow ? 'bg-jarvis-cyan/20 border-jarvis-cyan text-jarvis-cyan' : 'bg-jarvis-card border-jarvis-border text-jarvis-muted'
            }`}
          >
            Phosphor Glow
          </button>
        </div>
      </div>

      {/* Side-by-Side Dual Displays */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Golden Baseline */}
        <div className="bg-jarvis-panel border border-jarvis-border rounded-xl p-5 flex flex-col items-center">
          <div className="w-full flex items-center justify-between mb-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              <span className="font-bold text-white uppercase tracking-wider">Golden Baseline</span>
            </div>
            <span className="text-[11px] text-emerald-400 font-mono">JARVIS Original (C++ 100%)</span>
          </div>

          <div className="p-3 bg-black/80 rounded-lg border border-jarvis-border/60">
            <OledDisplay
              framebuffer={baselineFbRef.current}
              zoom={zoom}
              color="#00e5ff"
              glow={glow}
              showGrid={false}
            />
          </div>

          <div className="w-full mt-4 pt-3 border-t border-jarvis-border/60 grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2 bg-jarvis-card rounded">
              <div className="text-jarvis-muted text-[10px]">Dimensione</div>
              <div className="font-mono text-white">{baseGeom.width}x{baseGeom.height}</div>
            </div>
            <div className="p-2 bg-jarvis-card rounded">
              <div className="text-jarvis-muted text-[10px]">Power / Taper</div>
              <div className="font-mono text-white">p={baseGeom.shape_power} / {baseGeom.taper}</div>
            </div>
            <div className="p-2 bg-jarvis-card rounded">
              <div className="text-jarvis-muted text-[10px]">Pixel Accesi</div>
              <div className="font-mono text-emerald-400">{baseLit} px</div>
            </div>
          </div>
        </div>

        {/* Right: Candidate Skin */}
        <div className="bg-jarvis-panel border border-jarvis-border rounded-xl p-5 flex flex-col items-center">
          <div className="w-full flex items-center justify-between mb-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-400"></span>
              <span className="font-bold text-white uppercase tracking-wider">Variante Candidata</span>
            </div>
            <span className="text-[11px] text-purple-400 font-mono">{candidateSkin.name}</span>
          </div>

          <div className="p-3 bg-black/80 rounded-lg border border-jarvis-border/60">
            <OledDisplay
              framebuffer={candidateFbRef.current}
              zoom={zoom}
              color="#00e5ff"
              glow={glow}
              showGrid={false}
            />
          </div>

          <div className="w-full mt-4 pt-3 border-t border-jarvis-border/60 grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2 bg-jarvis-card rounded">
              <div className="text-jarvis-muted text-[10px]">Dimensione</div>
              <div className="font-mono text-white">{candGeom.width}x{candGeom.height}</div>
            </div>
            <div className="p-2 bg-jarvis-card rounded">
              <div className="text-jarvis-muted text-[10px]">Power / Taper</div>
              <div className="font-mono text-white">p={candGeom.shape_power} / {candGeom.taper}</div>
            </div>
            <div className="p-2 bg-jarvis-card rounded">
              <div className="text-jarvis-muted text-[10px]">Pixel Accesi</div>
              <div className="font-mono text-purple-400">{candLit} px</div>
            </div>
          </div>
        </div>
      </div>

      {/* Delta Comparison Summary Bar */}
      <div className="bg-jarvis-panel border border-jarvis-border rounded-xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Sliders className="w-4 h-4 text-jarvis-cyan" />
          Delta Geometrico e Ottico Rispetto alla Baseline
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
          <div className="p-3 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <div className="text-jarvis-muted text-[10px]">Δ Larghezza</div>
            <div className={`font-mono font-bold text-sm ${deltaW === 0 ? 'text-white' : deltaW > 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {deltaW > 0 ? `+${deltaW}` : deltaW} px
            </div>
          </div>

          <div className="p-3 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <div className="text-jarvis-muted text-[10px]">Δ Altezza</div>
            <div className={`font-mono font-bold text-sm ${deltaH === 0 ? 'text-white' : deltaH > 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {deltaH > 0 ? `+${deltaH}` : deltaH} px
            </div>
          </div>

          <div className="p-3 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <div className="text-jarvis-muted text-[10px]">Δ Superellisse (p)</div>
            <div className={`font-mono font-bold text-sm ${deltaP === 0 ? 'text-white' : deltaP > 0 ? 'text-purple-400' : 'text-cyan-400'}`}>
              {deltaP > 0 ? `+${deltaP.toFixed(1)}` : deltaP.toFixed(1)}
            </div>
          </div>

          <div className="p-3 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <div className="text-jarvis-muted text-[10px]">Δ Spaziatura</div>
            <div className={`font-mono font-bold text-sm ${deltaS === 0 ? 'text-white' : deltaS > 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {deltaS > 0 ? `+${deltaS}` : deltaS} px
            </div>
          </div>

          <div className="p-3 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <div className="text-jarvis-muted text-[10px]">Δ Taper</div>
            <div className={`font-mono font-bold text-sm ${deltaT === 0 ? 'text-white' : deltaT > 0 ? 'text-purple-400' : 'text-cyan-400'}`}>
              {deltaT > 0 ? `+${deltaT.toFixed(2)}` : deltaT.toFixed(2)}
            </div>
          </div>

          <div className="p-3 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <div className="text-jarvis-muted text-[10px]">Δ Pixel Illuminati</div>
            <div className={`font-mono font-bold text-sm ${deltaLit === 0 ? 'text-white' : deltaLit > 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {deltaLit > 0 ? `+${deltaLit}` : deltaLit} px
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
