import React from 'react';
import { Eye, Layers, Sliders, ShieldCheck, Cpu, HardDrive, Sparkles, CheckCircle2, ArrowRight } from 'lucide-react';

interface DashboardViewProps {
  onNavigate: (view: 'simulator' | 'skin-editor' | 'catalogue' | 'comparator') => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-jarvis-panel via-jarvis-card to-jarvis-panel border border-jarvis-border p-6 rounded-xl relative overflow-hidden shadow-xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-jarvis-cyan/5 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-jarvis-cyan/10 text-jarvis-cyan border border-jarvis-cyan/30">
                FASE RP-03 ATTIVA
              </span>
              <span className="px-2.5 py-0.5 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Baseline C++ Eyes 3.0 Conforme al 100%
              </span>
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold tracking-tight text-white mb-2">
              JARVIS Identity Studio & Eyes 3.0 Simulator
            </h1>
            <p className="text-jarvis-muted text-sm max-w-2xl leading-relaxed">
              Ambiente unificato di simulazione grafica deterministica, collaudo espressivo e gestione profili per la piattaforma robotica multi-identità JARVIS.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate('simulator')}
              className="px-4 py-2.5 bg-jarvis-cyan text-black font-semibold rounded-lg hover:bg-cyan-300 transition-colors flex items-center gap-2 text-sm shadow-lg shadow-jarvis-cyan/20"
            >
              <Eye className="w-4 h-4" />
              Avvia Simulatore Eyes 3.0
            </button>
            <button
              onClick={() => onNavigate('comparator')}
              className="px-4 py-2.5 bg-jarvis-panel border border-jarvis-border hover:border-jarvis-cyan text-jarvis-text font-medium rounded-lg transition-colors flex items-center gap-2 text-sm"
            >
              <Sliders className="w-4 h-4" />
              Comparatore Dual-OLED
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-jarvis-panel border border-jarvis-border p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-jarvis-cyan/10 border border-jarvis-cyan/20 rounded-lg text-jarvis-cyan">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">27</div>
            <div className="text-xs text-jarvis-muted">Profili Formalizzati</div>
            <div className="text-[10px] text-jarvis-cyan-dim font-mono">10 Schemi Draft 2020-12</div>
          </div>
        </div>

        <div className="bg-jarvis-panel border border-jarvis-border p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">ESP32-S3</div>
            <div className="text-xs text-jarvis-muted">I2C0 SDA:41 / SCL:42</div>
            <div className="text-[10px] text-emerald-500 font-mono">SH1106 128x64 400kHz</div>
          </div>
        </div>

        <div className="bg-jarvis-panel border border-jarvis-border p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg text-purple-400">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">14 + 5</div>
            <div className="text-xs text-jarvis-muted">Espressioni & Micro-expr</div>
            <div className="text-[10px] text-purple-400 font-mono">Gaze + Superellissi p=3.0</div>
          </div>
        </div>

        <div className="bg-jarvis-panel border border-jarvis-border p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">Sandbox</div>
            <div className="text-xs text-jarvis-muted">Isolamento Completo</div>
            <div className="text-[10px] text-amber-400 font-mono">Firmware Read-Only</div>
          </div>
        </div>
      </div>

      {/* Main Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Simulator Card */}
        <div 
          onClick={() => onNavigate('simulator')}
          className="bg-jarvis-panel border border-jarvis-border hover:border-jarvis-cyan/50 p-6 rounded-xl cursor-pointer transition-all hover:shadow-lg hover:shadow-jarvis-cyan/5 group"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-jarvis-card rounded-lg text-jarvis-cyan group-hover:scale-110 transition-transform">
              <Eye className="w-6 h-6" />
            </div>
            <ArrowRight className="w-5 h-5 text-jarvis-muted group-hover:text-jarvis-cyan group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Simulatore Grafico Eyes 3.0</h3>
          <p className="text-sm text-jarvis-muted leading-relaxed mb-4">
            Emulazione deterministica a 60 FPS dell'algoritmo visivo C++ originale: palpebre curve, rendering superellittico p=3.0, saccadi xorshift32 e reattività audio.
          </p>
          <div className="text-xs font-mono text-jarvis-cyan-dim">Visualizza OLED • Tracciamento FPS • Saccadi</div>
        </div>

        {/* Skin Editor Card */}
        <div 
          onClick={() => onNavigate('skin-editor')}
          className="bg-jarvis-panel border border-jarvis-border hover:border-jarvis-cyan/50 p-6 rounded-xl cursor-pointer transition-all hover:shadow-lg hover:shadow-jarvis-cyan/5 group"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-jarvis-card rounded-lg text-purple-400 group-hover:scale-110 transition-transform">
              <Sliders className="w-6 h-6" />
            </div>
            <ArrowRight className="w-5 h-5 text-jarvis-muted group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Skin Editor Parametrico</h3>
          <p className="text-sm text-jarvis-muted leading-relaxed mb-4">
            Personalizzazione in tempo reale di raggio occhio, spaziatura, esponente superellisse, rastremazione e catchlight con esportazione conforme a JSON Schema.
          </p>
          <div className="text-xs font-mono text-purple-400/70">Parametri Geometrici • Export JSON • Reset Baseline</div>
        </div>

        {/* Comparator Card */}
        <div 
          onClick={() => onNavigate('comparator')}
          className="bg-jarvis-panel border border-jarvis-border hover:border-jarvis-cyan/50 p-6 rounded-xl cursor-pointer transition-all hover:shadow-lg hover:shadow-jarvis-cyan/5 group"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-jarvis-card rounded-lg text-emerald-400 group-hover:scale-110 transition-transform">
              <Layers className="w-6 h-6" />
            </div>
            <ArrowRight className="w-5 h-5 text-jarvis-muted group-hover:text-emerald-400 group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Comparatore Side-by-Side</h3>
          <p className="text-sm text-jarvis-muted leading-relaxed mb-4">
            Verifica ottica comparata a doppio display tra la Golden Baseline JARVIS e qualsiasi skin sperimentale con sincronizzazione degli stati d'animazione.
          </p>
          <div className="text-xs font-mono text-emerald-400/70">Dual OLED 128x64 • Diff Geometrica • Step Sincrono</div>
        </div>
      </div>

      {/* Hardware & Infrastructure Status Panel */}
      <div className="bg-jarvis-panel border border-jarvis-border rounded-xl p-6">
        <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <HardDrive className="w-5 h-5 text-jarvis-cyan" />
          Stato Reale dell'Infrastruttura Hardware (RP-02 Audit Corretto)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
          <div className="p-3.5 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <div className="font-semibold text-white mb-1">Carrier Board V1 (PCB)</div>
            <div className="text-jarvis-muted">Stato: Progettata & Ordinata in fabbrica.</div>
            <div className="text-amber-400 mt-1 font-mono">In attesa ricezione / Non assemblata</div>
          </div>
          <div className="p-3.5 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <div className="font-semibold text-white mb-1">Pinout ESP32-S3 Verificato</div>
            <div className="text-jarvis-muted">I2C0: SDA GPIO41, SCL GPIO42 | Touch: GPIO1</div>
            <div className="text-emerald-400 mt-1 font-mono">Nessun conflitto con GPIO non esistenti</div>
          </div>
          <div className="p-3.5 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <div className="font-semibold text-white mb-1">Raspberry Pi 5 8GB & NAS Synology</div>
            <div className="text-jarvis-muted">Debian 13 su microSD, Portainer, NPM, AdGuard</div>
            <div className="text-cyan-400 mt-1 font-mono">Ambiente multi-servizio (Risorse condivise)</div>
          </div>
        </div>
      </div>
    </div>
  );
};
