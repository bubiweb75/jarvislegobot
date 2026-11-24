import React, { useState, useEffect, useRef } from 'react';
import { SkinDefinition, Expression, ALL_EXPRESSIONS } from '../../engine/eyes/types';
import { JARVIS_ORIGINAL_PREMIUM_SKIN, CATALOG_SKINS } from '../../engine/eyes/baseline';
import { EyeEngine } from '../../engine/eyes/EyeEngine';
import { MonochromeFramebuffer } from '../../engine/framebuffer/MonochromeFramebuffer';
import { OledDisplay } from '../../components/OledDisplay';
import { RotateCcw, Download, Upload, Sliders, CheckCircle2, AlertCircle, Copy } from 'lucide-react';

export const SkinEditorView: React.FC = () => {
  // Working copy of skin
  const [skin, setSkin] = useState<SkinDefinition>(() => JSON.parse(JSON.stringify(JARVIS_ORIGINAL_PREMIUM_SKIN)));
  const [selectedExpression, setSelectedExpression] = useState<Expression>('NEUTRAL');
  const [zoom, setZoom] = useState<2 | 3 | 4 | 5 | 6 | 8>(4);
  const [glow, setGlow] = useState<boolean>(true);
  const [pixelGrid, setPixelGrid] = useState<boolean>(false);
  const [importStatus, setImportStatus] = useState<{ success: boolean; msg: string } | null>(null);

  // Engine & Framebuffer refs
  const engineRef = useRef<EyeEngine | null>(null);
  const fbRef = useRef<MonochromeFramebuffer>(new MonochromeFramebuffer());
  const [, setTick] = useState<number>(0);
  const animFrameRef = useRef<number | null>(null);

  // Initialize engine with custom skin
  useEffect(() => {
    engineRef.current = new EyeEngine(skin);
    engineRef.current.setExpression(selectedExpression);
    engineRef.current.setVisualProfile('CALM');
  }, [skin]);

  // Handle expression change
  useEffect(() => {
    if (engineRef.current) {
      engineRef.current.setExpression(selectedExpression);
    }
  }, [selectedExpression]);

  // Animation Loop
  useEffect(() => {
    let lastTime = performance.now();

    const loop = (currentTime: number) => {
      const dt = (currentTime - lastTime) / 1000;
      lastTime = currentTime;

      if (engineRef.current) {
        engineRef.current.update(dt);
        engineRef.current.render(fbRef.current);
        setTick((t) => (t + 1) % 1000000);
      }

      animFrameRef.current = requestAnimationFrame(loop);
    };

    animFrameRef.current = requestAnimationFrame(loop);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, []);

  // Update field helpers
  const updateGeometry = (key: keyof SkinDefinition['base_geometry'], value: any) => {
    setSkin((prev) => ({
      ...prev,
      base_geometry: {
        ...prev.base_geometry,
        [key]: value,
      },
    }));
  };

  const updatePupil = (key: keyof SkinDefinition['base_geometry']['pupil'], value: any) => {
    setSkin((prev) => ({
      ...prev,
      base_geometry: {
        ...prev.base_geometry,
        pupil: {
          ...prev.base_geometry.pupil,
          [key]: value,
        },
      },
    }));
  };

  const updateEyebrows = (key: string, value: any) => {
    setSkin((prev) => ({
      ...prev,
      base_geometry: {
        ...prev.base_geometry,
        eyebrows: {
          offset: prev.base_geometry.eyebrows?.offset ?? 4.0,
          arch: prev.base_geometry.eyebrows?.arch ?? 2.2,
          tilt: prev.base_geometry.eyebrows?.tilt ?? 0.0,
          [key]: value,
        },
      },
    }));
  };

  // Reset to Baseline
  const handleReset = () => {
    setSkin(JSON.parse(JSON.stringify(JARVIS_ORIGINAL_PREMIUM_SKIN)));
    setImportStatus({ success: true, msg: 'Ripristinata Baseline Originale JARVIS' });
  };

  // Export JSON
  const handleExport = () => {
    const exportData = {
      $schema: 'https://jarvis-robotics.io/schemas/skin.schema.json',
      ...skin,
      skin_version: '1.0.0-custom',
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${skin.skin_id || 'custom-skin'}.skin.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Import JSON
  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        if (!json.base_geometry || typeof json.base_geometry.width !== 'number') {
          throw new Error('Formato non conforme: campo base_geometry mancante o errato');
        }
        setSkin(json);
        setImportStatus({ success: true, msg: `Skin caricata con successo: ${json.name || 'Senza nome'}` });
      } catch (err: any) {
        setImportStatus({ success: false, msg: `Errore importazione: ${err.message}` });
      }
    };
    reader.readAsText(file);
  };

  // Copy from Catalog
  const handleLoadPreset = (presetId: string) => {
    const preset = CATALOG_SKINS.find((s) => s.skin_id === presetId);
    if (preset) {
      setSkin(JSON.parse(JSON.stringify(preset)));
      setImportStatus({ success: true, msg: `Caricato preset: ${preset.name}` });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-jarvis-panel border border-jarvis-border p-6 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
              SKIN ENGINE STUDIO
            </span>
            <span className="text-xs text-jarvis-muted font-mono">{skin.skin_id}</span>
          </div>
          <h2 className="text-xl font-bold text-white">Skin Editor Parametrico</h2>
          <p className="text-xs text-jarvis-muted">
            Personalizzazione in tempo reale della geometria e dei dettagli oculari con esportazione conforme a JSON Schema.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleReset}
            className="px-3 py-2 bg-jarvis-card hover:bg-jarvis-border border border-jarvis-border text-jarvis-text rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors"
            title="Ripristina alla Golden Baseline"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Baseline
          </button>

          <label className="px-3 py-2 bg-jarvis-card hover:bg-jarvis-border border border-jarvis-border text-jarvis-text rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer">
            <Upload className="w-3.5 h-3.5" />
            Importa JSON
            <input type="file" accept=".json" onChange={handleImport} className="hidden" />
          </label>

          <button
            onClick={handleExport}
            className="px-3 py-2 bg-jarvis-cyan text-black hover:bg-cyan-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg shadow-jarvis-cyan/10"
          >
            <Download className="w-3.5 h-3.5" />
            Esporta JSON
          </button>
        </div>
      </div>

      {importStatus && (
        <div
          className={`p-3 rounded-lg border text-xs flex items-center gap-2 ${
            importStatus.success
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}
        >
          {importStatus.success ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {importStatus.msg}
        </div>
      )}

      {/* Main Grid: Controls Left + Display Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Parameter Sliders (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Preset Selector */}
          <div className="bg-jarvis-panel border border-jarvis-border p-4 rounded-xl">
            <label className="text-xs font-semibold text-white mb-2 block flex items-center gap-1.5">
              <Copy className="w-3.5 h-3.5 text-jarvis-cyan" />
              Carica da Preset Identità
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {CATALOG_SKINS.map((s) => (
                <button
                  key={s.skin_id}
                  onClick={() => handleLoadPreset(s.skin_id)}
                  className={`p-2 rounded text-xs text-left border transition-all ${
                    skin.skin_id === s.skin_id
                      ? 'bg-jarvis-cyan/10 border-jarvis-cyan text-white'
                      : 'bg-jarvis-card border-jarvis-border text-jarvis-muted hover:border-jarvis-muted'
                  }`}
                >
                  <div className="font-semibold truncate">{s.name}</div>
                  <div className="text-[10px] text-jarvis-cyan-dim font-mono truncate">{s.skin_id}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Geometry Parameters */}
          <div className="bg-jarvis-panel border border-jarvis-border p-4 rounded-xl space-y-4">
            <h3 className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-jarvis-cyan" />
              Geometria Occhio Base
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <div className="flex justify-between text-jarvis-muted mb-1">
                  <span>Larghezza:</span>
                  <span className="font-mono text-white">{skin.base_geometry.width} px</span>
                </div>
                <input
                  type="range"
                  min="16"
                  max="44"
                  value={skin.base_geometry.width}
                  onChange={(e) => updateGeometry('width', parseInt(e.target.value))}
                  className="w-full accent-jarvis-cyan bg-jarvis-card rounded h-1.5"
                />
              </div>

              <div>
                <div className="flex justify-between text-jarvis-muted mb-1">
                  <span>Altezza:</span>
                  <span className="font-mono text-white">{skin.base_geometry.height} px</span>
                </div>
                <input
                  type="range"
                  min="16"
                  max="52"
                  value={skin.base_geometry.height}
                  onChange={(e) => updateGeometry('height', parseInt(e.target.value))}
                  className="w-full accent-jarvis-cyan bg-jarvis-card rounded h-1.5"
                />
              </div>

              <div>
                <div className="flex justify-between text-jarvis-muted mb-1">
                  <span>Spaziatura Interoculare:</span>
                  <span className="font-mono text-white">{skin.base_geometry.spacing_px} px</span>
                </div>
                <input
                  type="range"
                  min="4"
                  max="32"
                  value={skin.base_geometry.spacing_px}
                  onChange={(e) => updateGeometry('spacing_px', parseInt(e.target.value))}
                  className="w-full accent-jarvis-cyan bg-jarvis-card rounded h-1.5"
                />
              </div>

              <div>
                <div className="flex justify-between text-jarvis-muted mb-1">
                  <span>Esponente Superellisse (p):</span>
                  <span className="font-mono text-white">{skin.base_geometry.shape_power.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="5.0"
                  step="0.1"
                  value={skin.base_geometry.shape_power}
                  onChange={(e) => updateGeometry('shape_power', parseFloat(e.target.value))}
                  className="w-full accent-purple-400 bg-jarvis-card rounded h-1.5"
                />
              </div>

              <div>
                <div className="flex justify-between text-jarvis-muted mb-1">
                  <span>Fattore Rastremazione (taper):</span>
                  <span className="font-mono text-white">{skin.base_geometry.taper.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="0.45"
                  step="0.01"
                  value={skin.base_geometry.taper}
                  onChange={(e) => updateGeometry('taper', parseFloat(e.target.value))}
                  className="w-full accent-jarvis-cyan bg-jarvis-card rounded h-1.5"
                />
              </div>

              <div>
                <div className="flex justify-between text-jarvis-muted mb-1">
                  <span>Raggio Angoli Smussati:</span>
                  <span className="font-mono text-white">{skin.base_geometry.corner_radius} px</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="14"
                  value={skin.base_geometry.corner_radius}
                  onChange={(e) => updateGeometry('corner_radius', parseInt(e.target.value))}
                  className="w-full accent-jarvis-cyan bg-jarvis-card rounded h-1.5"
                />
              </div>
            </div>
          </div>

          {/* Features: Pupil & Eyebrows */}
          <div className="bg-jarvis-panel border border-jarvis-border p-4 rounded-xl space-y-4">
            <h3 className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-jarvis-cyan" />
              Caratteristiche Espressive
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              {/* Pupil */}
              <div className="p-3 bg-jarvis-card rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-white">Pupilla Scura</span>
                  <input
                    type="checkbox"
                    checked={skin.base_geometry.pupil.radius > 0}
                    onChange={(e) => updatePupil('radius', e.target.checked ? 7.0 : 0)}
                    className="accent-jarvis-cyan"
                  />
                </div>
                {skin.base_geometry.pupil.radius > 0 && (
                  <>
                    <div className="flex justify-between text-jarvis-muted text-[11px]">
                      <span>Raggio:</span>
                      <span className="font-mono text-white">{skin.base_geometry.pupil.radius} px</span>
                    </div>
                    <input
                      type="range"
                      min="2"
                      max="14"
                      value={skin.base_geometry.pupil.radius}
                      onChange={(e) => updatePupil('radius', parseInt(e.target.value))}
                      className="w-full accent-jarvis-cyan h-1"
                    />
                    <div className="flex items-center justify-between text-[11px] pt-1">
                      <span className="text-jarvis-muted">Catchlight:</span>
                      <span className="font-mono text-jarvis-cyan">{skin.base_geometry.pupil.catchlight}</span>
                    </div>
                  </>
                )}
              </div>

              {/* Eyebrows */}
              <div className="p-3 bg-jarvis-card rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-white">Sopracciglia</span>
                  <input
                    type="checkbox"
                    checked={!!skin.base_geometry.eyebrows}
                    onChange={(e) => {
                      if (e.target.checked) {
                        updateEyebrows('offset', 4.0);
                      } else {
                        setSkin((prev) => ({
                          ...prev,
                          base_geometry: {
                            ...prev.base_geometry,
                            eyebrows: undefined,
                          },
                        }));
                      }
                    }}
                    className="accent-purple-400"
                  />
                </div>
                {skin.base_geometry.eyebrows && (
                  <>
                    <div className="flex justify-between text-jarvis-muted text-[11px]">
                      <span>Offset Verticale:</span>
                      <span className="font-mono text-white">{skin.base_geometry.eyebrows.offset} px</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="8"
                      value={skin.base_geometry.eyebrows.offset}
                      onChange={(e) => updateEyebrows('offset', parseFloat(e.target.value))}
                      className="w-full accent-purple-400 h-1"
                    />
                    <div className="flex justify-between text-jarvis-muted text-[11px]">
                      <span>Arco:</span>
                      <span className="font-mono text-white">{skin.base_geometry.eyebrows.arch}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.2"
                      value={skin.base_geometry.eyebrows.arch}
                      onChange={(e) => updateEyebrows('arch', parseFloat(e.target.value))}
                      className="w-full accent-purple-400 h-1"
                    />
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right: Live OLED Preview + Expressions (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-jarvis-panel border border-jarvis-border p-4 rounded-xl flex flex-col items-center">
            <div className="w-full flex items-center justify-between mb-3 text-xs">
              <span className="font-semibold text-white">Anteprima Live OLED (128x64)</span>
              <div className="flex items-center gap-2">
                <select
                  value={zoom}
                  onChange={(e) => setZoom(parseInt(e.target.value) as 2 | 3 | 4 | 5 | 6 | 8)}
                  className="bg-jarvis-card border border-jarvis-border text-white text-[11px] rounded px-1.5 py-0.5"
                >
                  <option value={2}>Zoom 2x</option>
                  <option value={3}>Zoom 3x</option>
                  <option value={4}>Zoom 4x</option>
                  <option value={5}>Zoom 5x</option>
                </select>
                <button
                  onClick={() => setGlow(!glow)}
                  className={`text-[10px] px-2 py-0.5 rounded border transition-colors ${
                    glow ? 'bg-jarvis-cyan/20 border-jarvis-cyan text-jarvis-cyan' : 'bg-jarvis-card border-jarvis-border text-jarvis-muted'
                  }`}
                >
                  Glow
                </button>
                <button
                  onClick={() => setPixelGrid(!pixelGrid)}
                  className={`text-[10px] px-2 py-0.5 rounded border transition-colors ${
                    pixelGrid ? 'bg-jarvis-cyan/20 border-jarvis-cyan text-jarvis-cyan' : 'bg-jarvis-card border-jarvis-border text-jarvis-muted'
                  }`}
                >
                  Grid
                </button>
              </div>
            </div>

            <OledDisplay
              framebuffer={fbRef.current}
              zoom={zoom}
              color="#00e5ff"
              showGrid={pixelGrid}
              glow={glow}
              scanlines={false}
            />

            <div className="w-full mt-3 pt-3 border-t border-jarvis-border/60 text-center">
              <span className="text-[11px] text-jarvis-muted font-mono">
                Render: Superellisse p={skin.base_geometry.shape_power.toFixed(1)}, Dim: {skin.base_geometry.width}x{skin.base_geometry.height}
              </span>
            </div>
          </div>

          {/* Expression Quick Picker */}
          <div className="bg-jarvis-panel border border-jarvis-border p-4 rounded-xl">
            <h4 className="text-xs font-semibold text-white mb-2">Test su Espressioni</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 max-h-48 overflow-y-auto">
              {ALL_EXPRESSIONS.map((expr) => (
                <button
                  key={expr}
                  onClick={() => setSelectedExpression(expr)}
                  className={`px-2 py-1 rounded text-[11px] font-mono transition-colors text-left ${
                    selectedExpression === expr
                      ? 'bg-jarvis-cyan text-black font-semibold'
                      : 'bg-jarvis-card hover:bg-jarvis-border text-jarvis-text'
                  }`}
                >
                  {expr}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
