import React, { useState, useEffect, useRef } from 'react';
import { EyeEngine } from '../../engine/eyes/EyeEngine';
import { EventSimulator, EventLogEntry, SimEvent } from '../../engine/simulation/EventSimulator';
import { AudioSimulator, AudioSimMode } from '../../engine/simulation/AudioSimulator';
import { OledDisplay } from '../../components/OledDisplay';
import {
  ALL_EXPRESSIONS,
  ALL_MICRO_EXPRESSIONS,
  ALL_PROFILES,
  Expression,
  VisualProfile,
  MicroExpression
} from '../../engine/eyes/types';
import {
  Play,
  Pause,
  StepForward,
  RotateCcw,
  Volume2,
  Mic,
  Hand,
  Moon,
  Sun,
  AlertCircle,
  Activity,
  Layers,
  Sparkles,
  Sliders,
  Upload,
  Grid
} from 'lucide-react';

export const SimulatorView: React.FC = () => {
  // Instanza centrale del motore grafico (persiste tra i render)
  const engineRef = useRef<EyeEngine>(new EyeEngine());
  const eventSimRef = useRef<EventSimulator | null>(null);
  const audioSimRef = useRef<AudioSimulator | null>(null);

  // Stato UI e Telemetria
  const [activeExpr, setActiveExpr] = useState<Expression>('NEUTRAL');
  const [activeProfile, setActiveProfile] = useState<VisualProfile>('LIVELY');
  const [activeMicro, setActiveMicro] = useState<MicroExpression>('NONE');
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [zoom, setZoom] = useState<2 | 4 | 6 | 8>(6);
  const [showGrid, setShowGrid] = useState<boolean>(false);
  const [showGlow, setShowGlow] = useState<boolean>(true);
  const [phosphorColor, setPhosphorColor] = useState<string>('#00e5ff');
  const [fpsMeasured, setFpsMeasured] = useState<number>(30.0);
  const [droppedFrames, setDroppedFrames] = useState<number>(0);
  const [eventLogs, setEventLogs] = useState<EventLogEntry[]>([]);
  
  // Audio state
  const [audioMode, setAudioMode] = useState<AudioSimMode>('SILENCE');
  const [audioGain, setAudioGain] = useState<number>(0.75);
  const [audioRms, setAudioRms] = useState<number>(0.0);

  // Frame tick trigger per forzare il re-render del canvas React
  const [, setFrameTick] = useState<number>(0);

  // Inizializzazione motore e loop
  useEffect(() => {
    const engine = engineRef.current;
    engine.begin(30, 16, performance.now());

    const eventSim = new EventSimulator(engine, (logs) => {
      setEventLogs(logs);
      setActiveExpr(engine.getExpression());
    });
    eventSimRef.current = eventSim;

    const audioSim = new AudioSimulator(engine);
    audioSimRef.current = audioSim;

    let animId: number;

    const loop = (currentTime: number) => {
      if (isPlaying) {
        // Avanza audio simulator
        const rms = audioSim.update(currentTime);
        setAudioRms(rms);

        // Avanza rendering motore grafico
        engine.update(currentTime);
        setFpsMeasured(engine.getActualFps());
        setDroppedFrames(engine.getDroppedFrames());
        setActiveMicro(engine.getCurrentMicroExpression());
        setFrameTick((t) => (t + 1) % 1000000);
      }
      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(animId);
      audioSim.stopWav();
    };
  }, [isPlaying]);

  const handleExpressionChange = (expr: Expression) => {
    setActiveExpr(expr);
    engineRef.current.setExpression(expr, performance.now());
  };

  const handleProfileChange = (prof: VisualProfile) => {
    setActiveProfile(prof);
    engineRef.current.setVisualProfile(prof);
  };

  const handleMicroExpressionTrigger = (micro: MicroExpression) => {
    if (micro === 'BrowRaise') {
      engineRef.current.right.targetBrowOffset += 3.0;
      engineRef.current.right.targetBrowTilt -= 1.5;
    } else if (micro === 'SideGlance') {
      engineRef.current.left.targetPupilDx += 3.5;
      engineRef.current.right.targetPupilDx += 3.5;
    } else if (micro === 'EyeSmile') {
      engineRef.current.left.targetLowerLid += 2.5;
      engineRef.current.right.targetLowerLid += 2.5;
      engineRef.current.left.targetLowerArch += 3.0;
      engineRef.current.right.targetLowerArch += 3.0;
    } else if (micro === 'PupilPulse') {
      engineRef.current.left.targetPupilRadius += 1.5;
      engineRef.current.right.targetPupilRadius += 1.5;
    } else if (micro === 'QuickWink') {
      engineRef.current.right.targetUpperLidL += 9.0;
      engineRef.current.right.targetUpperLidR += 9.0;
    }
  };

  const handleStepForward = () => {
    setIsPlaying(false);
    const now = performance.now() + 33;
    audioSimRef.current?.update(now);
    engineRef.current.updateStep(now);
    setFrameTick((t) => t + 1);
  };

  const handleResetBaseline = () => {
    engineRef.current.resetToDefaultGeometry();
    engineRef.current.setExpression('NEUTRAL', performance.now());
    setActiveExpr('NEUTRAL');
    setActiveProfile('LIVELY');
    setAudioMode('SILENCE');
    audioSimRef.current?.setMode('SILENCE');
    eventSimRef.current?.clearLogs();
  };

  const handleAudioModeChange = (mode: AudioSimMode) => {
    setAudioMode(mode);
    audioSimRef.current?.setMode(mode);
  };

  const handleAudioGainChange = (gain: number) => {
    setAudioGain(gain);
    audioSimRef.current?.setGain(gain);
  };

  const handleWavUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && audioSimRef.current) {
      audioSimRef.current.loadLocalWav(file).then(() => {
        setAudioMode('LOCAL_WAV');
        eventSimRef.current?.dispatch('START_SPEAKING');
      });
    }
  };

  const handleEventTrigger = (event: SimEvent) => {
    eventSimRef.current?.dispatch(event, performance.now());
    setActiveExpr(engineRef.current.getExpression());
  };

  return (
    <div className="flex-1 flex flex-col gap-6 p-6 max-w-[1500px] mx-auto w-full">
      {/* Intestazione Titolo & Badge Modalità */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-jarvis-border pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Activity className="text-jarvis-cyan" size={24} />
              Eyes 3.0 Real-Time Simulator
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-mono rounded-full bg-jarvis-cyan/10 text-jarvis-cyan border border-jarvis-cyan/30">
              FASE RP-03
            </span>
            <span className="px-2.5 py-0.5 text-xs font-mono rounded-full bg-green-500/10 text-green-400 border border-green-500/30">
              SH1106 128x64 1-BIT
            </span>
          </div>
          <p className="text-sm text-jarvis-muted mt-1">
            Simulatore indipendente ad alta fedeltà. Baseline: <strong className="text-white">JARVIS Original Premium — Organic Visor Companion</strong>.
          </p>
        </div>

        {/* Pulsanti di Controllo Clock Principale */}
        <div className="flex items-center gap-2 bg-jarvis-panel p-1.5 rounded-lg border border-jarvis-border">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`px-3 py-1.5 rounded flex items-center gap-2 text-xs font-mono transition ${
              isPlaying
                ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 hover:bg-yellow-500/30'
                : 'bg-green-500/20 text-green-300 border border-green-500/30 hover:bg-green-500/30'
            }`}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
            <span>{isPlaying ? 'PAUSA' : 'AVVIA'}</span>
          </button>
          <button
            onClick={handleStepForward}
            className="p-1.5 hover:bg-jarvis-card rounded text-jarvis-muted hover:text-white transition"
            title="Avanza di 1 Frame (33 ms)"
          >
            <StepForward size={16} />
          </button>
          <button
            onClick={handleResetBaseline}
            className="p-1.5 hover:bg-jarvis-card rounded text-jarvis-muted hover:text-jarvis-cyan transition"
            title="Ripristina Baseline Originale"
          >
            <RotateCcw size={16} />
          </button>
        </div>
      </div>

      {/* Area Principale Simulator: OLED al centro + Controlli affiancati */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Colonna Sinistra / Centrale: Display OLED e Telemetria (7 Colonne) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <div className="bg-jarvis-panel rounded-xl p-5 border border-jarvis-border flex flex-col items-center justify-center">
            {/* Opzioni Viewport Display */}
            <div className="w-full flex items-center justify-between text-xs text-jarvis-muted mb-4 px-2">
              <div className="flex items-center gap-2">
                <span>ZOOM:</span>
                {([2, 4, 6, 8] as const).map((z) => (
                  <button
                    key={z}
                    onClick={() => setZoom(z)}
                    className={`px-2 py-0.5 rounded font-mono text-[11px] ${
                      zoom === z ? 'bg-jarvis-cyan text-black font-bold' : 'bg-jarvis-card text-jarvis-muted hover:text-white'
                    }`}
                  >
                    {z}x
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowGrid(!showGrid)}
                  className={`flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded transition ${
                    showGrid ? 'bg-jarvis-cyan/20 text-jarvis-cyan border border-jarvis-cyan/40' : 'text-jarvis-muted'
                  }`}
                >
                  <Grid size={12} />
                  <span>GRIGLIA</span>
                </button>
                <button
                  onClick={() => setShowGlow(!showGlow)}
                  className={`flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded transition ${
                    showGlow ? 'bg-jarvis-cyan/20 text-jarvis-cyan border border-jarvis-cyan/40' : 'text-jarvis-muted'
                  }`}
                >
                  <Sparkles size={12} />
                  <span>GLOW</span>
                </button>
                <div className="flex items-center gap-1">
                  <span className="text-[10px]">TINTA:</span>
                  {[
                    { label: 'Cyan', color: '#00e5ff' },
                    { label: 'White', color: '#f0f4f8' },
                    { label: 'Amber', color: '#ffb300' },
                    { label: 'Blue', color: '#2979ff' }
                  ].map((t) => (
                    <button
                      key={t.label}
                      onClick={() => setPhosphorColor(t.color)}
                      className="w-3.5 h-3.5 rounded-full border border-white/20 transition transform hover:scale-110"
                      style={{ backgroundColor: t.color }}
                      title={t.label}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Componente Display OLED monocromatico bit-exact */}
            <OledDisplay
              framebuffer={engineRef.current.fb}
              zoom={zoom}
              showPixelGrid={showGrid}
              showGlow={showGlow}
              phosphorColor={phosphorColor}
            />

            {/* Barra Telemetria Live */}
            <div className="w-full grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4 pt-3 border-t border-jarvis-border/60 text-xs font-mono">
              <div className="bg-jarvis-card/70 p-2 rounded border border-jarvis-border/40">
                <span className="text-jarvis-muted block text-[10px]">FRAME RATE</span>
                <span className="text-jarvis-cyan font-bold">{fpsMeasured.toFixed(1)} FPS</span>
                <span className="text-[10px] text-jarvis-muted/70 block">Target: 30.0 • Drop: {droppedFrames}</span>
              </div>
              <div className="bg-jarvis-card/70 p-2 rounded border border-jarvis-border/40">
                <span className="text-jarvis-muted block text-[10px]">ESPRESSIONE</span>
                <span className="text-white font-bold">{activeExpr}</span>
                <span className="text-[10px] text-jarvis-cyan block">Micro: {activeMicro}</span>
              </div>
              <div className="bg-jarvis-card/70 p-2 rounded border border-jarvis-border/40">
                <span className="text-jarvis-muted block text-[10px]">PROFILO VISIVO</span>
                <span className="text-emerald-400 font-bold">{activeProfile}</span>
                <span className="text-[10px] text-jarvis-muted block">Speed: {engineRef.current.profileSpeedScale().toFixed(2)}x</span>
              </div>
              <div className="bg-jarvis-card/70 p-2 rounded border border-jarvis-border/40">
                <span className="text-jarvis-muted block text-[10px]">AUDIO RMS LEVEL</span>
                <span className="text-yellow-400 font-bold">{(audioRms * 100).toFixed(0)}%</span>
                <div className="w-full bg-jarvis-dark h-1.5 rounded mt-1 overflow-hidden">
                  <div
                    className="bg-yellow-400 h-full transition-all duration-75"
                    style={{ width: `${Math.min(100, audioRms * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Event Simulator & Voice Reactivity Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Pannello Simulazione Eventi */}
            <div className="bg-jarvis-panel rounded-xl p-4 border border-jarvis-border">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
                  <Hand size={14} className="text-jarvis-cyan" />
                  SIMULATORE EVENTI HARDWARE
                </h3>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <button
                  onClick={() => handleEventTrigger('PTT_PRESS')}
                  className="p-2 bg-jarvis-card hover:bg-jarvis-cyan/20 hover:text-jarvis-cyan border border-jarvis-border rounded transition text-left flex items-center gap-1.5"
                >
                  <Mic size={13} className="text-jarvis-cyan" />
                  <span>PTT Press</span>
                </button>
                <button
                  onClick={() => handleEventTrigger('WAKEWORD_DETECTED')}
                  className="p-2 bg-jarvis-card hover:bg-jarvis-cyan/20 hover:text-jarvis-cyan border border-jarvis-border rounded transition text-left flex items-center gap-1.5"
                >
                  <Activity size={13} className="text-amber-400" />
                  <span>Hey Jarvis</span>
                </button>
                <button
                  onClick={() => handleEventTrigger('AI_PROCESSING')}
                  className="p-2 bg-jarvis-card hover:bg-jarvis-cyan/20 hover:text-jarvis-cyan border border-jarvis-border rounded transition text-left flex items-center gap-1.5"
                >
                  <Sliders size={13} className="text-purple-400" />
                  <span>Elabora AI</span>
                </button>
                <button
                  onClick={() => handleEventTrigger('START_SPEAKING')}
                  className="p-2 bg-jarvis-card hover:bg-jarvis-cyan/20 hover:text-jarvis-cyan border border-jarvis-border rounded transition text-left flex items-center gap-1.5"
                >
                  <Volume2 size={13} className="text-green-400" />
                  <span>Parla TTS</span>
                </button>
                <button
                  onClick={() => handleEventTrigger('TOUCH_SINGLE')}
                  className="p-2 bg-jarvis-card hover:bg-jarvis-cyan/20 hover:text-jarvis-cyan border border-jarvis-border rounded transition text-left flex items-center gap-1.5"
                >
                  <Hand size={13} className="text-pink-400" />
                  <span>Touch Tap</span>
                </button>
                <button
                  onClick={() => handleEventTrigger('TOUCH_LONG')}
                  className="p-2 bg-jarvis-card hover:bg-jarvis-cyan/20 hover:text-jarvis-cyan border border-jarvis-border rounded transition text-left flex items-center gap-1.5"
                >
                  <Hand size={13} className="text-rose-400" />
                  <span>Touch Long</span>
                </button>
                <button
                  onClick={() => handleEventTrigger('SLEEP')}
                  className="p-2 bg-jarvis-card hover:bg-jarvis-cyan/20 hover:text-jarvis-cyan border border-jarvis-border rounded transition text-left flex items-center gap-1.5"
                >
                  <Moon size={13} className="text-blue-400" />
                  <span>Addormenta</span>
                </button>
                <button
                  onClick={() => handleEventTrigger('WAKEUP')}
                  className="p-2 bg-jarvis-card hover:bg-jarvis-cyan/20 hover:text-jarvis-cyan border border-jarvis-border rounded transition text-left flex items-center gap-1.5"
                >
                  <Sun size={13} className="text-yellow-400" />
                  <span>Risveglia</span>
                </button>
              </div>
            </div>

            {/* Pannello Simulazione Audio & Reattività */}
            <div className="bg-jarvis-panel rounded-xl p-4 border border-jarvis-border">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
                  <Volume2 size={14} className="text-jarvis-cyan" />
                  REATTIVITÀ VOCALE (SOLO OCULARE)
                </h3>
              </div>
              <div className="flex flex-col gap-2.5 text-xs font-mono">
                <div className="grid grid-cols-2 gap-1.5">
                  {(['SILENCE', 'CONSTANT', 'SINE', 'SYLLABIC'] as AudioSimMode[]).map((m) => (
                    <button
                      key={m}
                      onClick={() => handleAudioModeChange(m)}
                      className={`py-1 px-2 rounded text-[11px] border transition text-left ${
                        audioMode === m
                          ? 'bg-jarvis-cyan/20 text-jarvis-cyan border-jarvis-cyan'
                          : 'bg-jarvis-card text-jarvis-muted border-jarvis-border hover:text-white'
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>

                <div className="flex flex-col gap-1 mt-1">
                  <div className="flex justify-between text-[11px] text-jarvis-muted">
                    <span>GUADAGNO RMS:</span>
                    <span className="text-white font-mono">{(audioGain * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={audioGain}
                    onChange={(e) => handleAudioGainChange(parseFloat(e.target.value))}
                    className="w-full accent-jarvis-cyan cursor-pointer"
                  />
                </div>

                {/* Caricamento File WAV Locale */}
                <div className="pt-2 border-t border-jarvis-border/60">
                  <label className="flex items-center justify-center gap-2 p-1.5 bg-jarvis-card hover:bg-jarvis-card/80 border border-jarvis-border rounded cursor-pointer text-[11px] text-jarvis-muted hover:text-white transition">
                    <Upload size={12} className="text-jarvis-cyan" />
                    <span>Carica WAV locale per test audio</span>
                    <input
                      type="file"
                      accept=".wav"
                      onChange={handleWavUpload}
                      className="hidden"
                    />
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Colonna Destra: Controlli Espressioni, Micro-Espressioni e Log Eventi (5 Colonne) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          {/* Selettore Espressioni (14 ufficiali) */}
          <div className="bg-jarvis-panel rounded-xl p-4 border border-jarvis-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
                <Layers size={14} className="text-jarvis-cyan" />
                14 ESPRESSIONI UFFICIALI EYES 3.0
              </h3>
              <span className="text-[10px] font-mono text-jarvis-cyan">BASELINE ORIGINALE</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
              {ALL_EXPRESSIONS.map((expr) => {
                const isActive = activeExpr === expr;
                return (
                  <button
                    key={expr}
                    onClick={() => handleExpressionChange(expr)}
                    className={`px-2.5 py-1.5 rounded text-xs font-mono border transition text-left flex items-center justify-between ${
                      isActive
                        ? 'bg-jarvis-cyan text-black font-bold border-jarvis-cyan shadow-[0_0_12px_rgba(0,229,255,0.4)]'
                        : 'bg-jarvis-card text-jarvis-text/90 border-jarvis-border hover:bg-jarvis-card/80 hover:border-jarvis-border/80'
                    }`}
                  >
                    <span>{expr}</span>
                    {isActive && <span className="w-1.5 h-1.5 rounded-full bg-black" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Micro-Espressioni Spontanee */}
          <div className="bg-jarvis-panel rounded-xl p-4 border border-jarvis-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
                <Sparkles size={14} className="text-jarvis-cyan" />
                5 MICRO-ESPRESSIONI (NON DISTRUTTIVE)
              </h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
              {ALL_MICRO_EXPRESSIONS.filter(m => m !== 'NONE').map((micro) => (
                <button
                  key={micro}
                  onClick={() => handleMicroExpressionTrigger(micro)}
                  className="px-2 py-1.5 bg-jarvis-card hover:bg-jarvis-cyan/15 hover:text-jarvis-cyan border border-jarvis-border rounded text-[11px] font-mono text-left transition"
                >
                  {micro}
                </button>
              ))}
            </div>
          </div>

          {/* Profilo Comportamentale Visivo */}
          <div className="bg-jarvis-panel rounded-xl p-4 border border-jarvis-border">
            <h3 className="text-xs font-mono font-bold text-white mb-2 flex items-center gap-1.5">
              <Activity size={14} className="text-jarvis-cyan" />
              PROFILO COMPORTAMENTALE DINAMICO
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {ALL_PROFILES.map((prof) => (
                <button
                  key={prof}
                  onClick={() => handleProfileChange(prof)}
                  className={`py-1.5 px-2 rounded text-xs font-mono border transition text-center ${
                    activeProfile === prof
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500 font-bold'
                      : 'bg-jarvis-card text-jarvis-muted border-jarvis-border hover:text-white'
                  }`}
                >
                  {prof}
                </button>
              ))}
            </div>
          </div>

          {/* Log Eventi Live */}
          <div className="bg-jarvis-panel rounded-xl p-4 border border-jarvis-border flex-1 flex flex-col min-h-[160px]">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-mono font-bold text-white flex items-center gap-1.5">
                <AlertCircle size={14} className="text-jarvis-cyan" />
                LOG EVENTI INTERATTIVI
              </h3>
              <button
                onClick={() => eventSimRef.current?.clearLogs()}
                className="text-[10px] font-mono text-jarvis-muted hover:text-white"
              >
                PULISCI
              </button>
            </div>
            <div className="flex-1 overflow-y-auto max-h-[180px] flex flex-col gap-1 pr-1 font-mono text-[11px]">
              {eventLogs.length === 0 ? (
                <span className="text-jarvis-muted/50 italic py-4 text-center">Nessun evento registrato.</span>
              ) : (
                eventLogs.map((log) => (
                  <div key={log.id} className="p-1.5 bg-jarvis-card/60 rounded border border-jarvis-border/40 flex items-start justify-between">
                    <div>
                      <span className="text-jarvis-cyan font-bold mr-2">[{log.event}]</span>
                      <span className="text-white/80">{log.details}</span>
                    </div>
                    <span className="text-jarvis-muted text-[10px] shrink-0 ml-2">{log.timestamp}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
