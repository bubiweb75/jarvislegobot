import React, { useState } from 'react';
import { 
  Eye, 
  Layers, 
  Sliders, 
  Bot, 
  LayoutDashboard, 
  Sparkles, 
  Volume2, 
  Cpu, 
  CloudUpload, 
  ShieldCheck, 
  Menu,
  X
} from 'lucide-react';

import { DashboardView } from '../features/dashboard/DashboardView';
import { SimulatorView } from '../features/simulator/SimulatorView';
import { SkinEditorView } from '../features/skin-editor/SkinEditorView';
import { CatalogueView } from '../features/profiles/CatalogueView';
import { SkinComparatorView } from '../features/simulator/SkinComparatorView';
import { SkinDefinition } from '../engine/eyes/types';

export type AppView = 'dashboard' | 'simulator' | 'skin-editor' | 'catalogue' | 'comparator';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [customSkinForComparator, setCustomSkinForComparator] = useState<SkinDefinition | undefined>(undefined);

  const navItems = [
    { id: 'dashboard' as AppView, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'simulator' as AppView, label: 'Eyes 3.0 Simulator', icon: Eye },
    { id: 'skin-editor' as AppView, label: 'Skin Studio', icon: Sliders },
    { id: 'catalogue' as AppView, label: 'Catalogo Identità', icon: Bot },
    { id: 'comparator' as AppView, label: 'Comparatore Dual-OLED', icon: Layers },
  ];

  const futureModules = [
    { label: 'Personality Studio', icon: Sparkles, phase: 'RP-05' },
    { label: 'Voice Studio', icon: Volume2, phase: 'RP-06' },
    { label: 'Device Manager', icon: Cpu, phase: 'RP-07' },
    { label: 'Deploy & OTA Engine', icon: CloudUpload, phase: 'RP-08' },
  ];

  const handleSelectSkinToEdit = (skin: SkinDefinition) => {
    setCustomSkinForComparator(skin);
    setCurrentView('skin-editor');
  };

  const handleOpenComparator = () => {
    setCurrentView('comparator');
  };

  return (
    <div className="min-h-screen bg-jarvis-dark text-jarvis-text flex flex-col">
      {/* Top Warning Banner - Safety & Sandbox Indicator */}
      <div className="bg-jarvis-panel/90 border-b border-jarvis-border px-4 py-2 flex items-center justify-between text-xs backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-2 text-jarvis-cyan">
          <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-400" />
          <span className="font-mono font-semibold tracking-wide text-white">
            MODALITÀ SIMULATORE
          </span>
          <span className="text-jarvis-muted hidden sm:inline">
            • Esecuzione Frontend Isolata • Nessuna Connessione o Modifica Firmware ESP32
          </span>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono text-jarvis-muted">
          <span className="hidden md:inline">OLED SH1106: SDA:41 / SCL:42</span>
          <span className="px-2 py-0.5 rounded bg-jarvis-card border border-jarvis-border text-jarvis-cyan">
            RP-03 V1.0
          </span>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Desktop */}
        <aside className="w-64 bg-jarvis-panel border-r border-jarvis-border flex-col justify-between hidden lg:flex shrink-0">
          <div className="p-4 space-y-6">
            {/* Logo */}
            <div className="flex items-center gap-3 px-2">
              <div className="w-8 h-8 rounded-lg bg-jarvis-cyan/10 border border-jarvis-cyan/30 flex items-center justify-center text-jarvis-cyan shadow-sm shadow-jarvis-cyan/20">
                <Eye className="w-5 h-5" />
              </div>
              <div>
                <div className="text-sm font-bold text-white tracking-wide">JARVIS</div>
                <div className="text-[10px] text-jarvis-cyan font-mono tracking-widest uppercase">
                  Identity Studio
                </div>
              </div>
            </div>

            {/* Navigation links */}
            <nav className="space-y-1">
              <div className="text-[10px] font-semibold text-jarvis-muted uppercase tracking-wider px-2.5 py-1">
                Piattaforma Attiva
              </div>
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentView === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentView(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-jarvis-cyan text-black font-semibold shadow-md shadow-jarvis-cyan/20'
                        : 'text-jarvis-muted hover:text-white hover:bg-jarvis-card'
                    }`}
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>

            {/* Future Modules */}
            <div className="space-y-1 pt-4 border-t border-jarvis-border/60">
              <div className="text-[10px] font-semibold text-jarvis-muted uppercase tracking-wider px-2.5 py-1">
                Moduli Futuri
              </div>
              {futureModules.map((item, idx) => {
                const Icon = item.icon;
                return (
                  <div
                    key={idx}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs text-jarvis-muted/60 cursor-not-allowed select-none"
                    title={`Modulo previsto nella fase ${item.phase}`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-4 h-4 shrink-0 opacity-40" />
                      <span>{item.label}</span>
                    </div>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-jarvis-card border border-jarvis-border/40 text-jarvis-muted/50">
                      {item.phase}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-jarvis-border text-[11px] text-jarvis-muted space-y-1 bg-jarvis-card/40">
            <div className="flex items-center justify-between">
              <span>Baseline:</span>
              <span className="font-mono text-emerald-400">Eyes 3.0 (C++)</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Risoluzione:</span>
              <span className="font-mono text-white">128x64 Monochrome</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Framework:</span>
              <span className="font-mono text-jarvis-cyan">React + Vite + Vitest</span>
            </div>
          </div>
        </aside>

        {/* Mobile Navigation Drawer */}
        <div className="lg:hidden">
          <div className="p-3 bg-jarvis-panel border-b border-jarvis-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-jarvis-cyan" />
              <span className="font-bold text-sm text-white">JARVIS Identity Studio</span>
            </div>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 rounded bg-jarvis-card text-jarvis-text"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

          {mobileMenuOpen && (
            <div className="bg-jarvis-panel border-b border-jarvis-border p-4 space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentView === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setCurrentView(item.id);
                      setMobileMenuOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium ${
                      isActive ? 'bg-jarvis-cyan text-black font-semibold' : 'text-jarvis-muted'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Main Workspace Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {currentView === 'dashboard' && <DashboardView onNavigate={(view) => setCurrentView(view)} />}
            {currentView === 'simulator' && <SimulatorView />}
            {currentView === 'skin-editor' && <SkinEditorView />}
            {currentView === 'catalogue' && (
              <CatalogueView
                onSelectSkinToEdit={handleSelectSkinToEdit}
                onOpenComparator={handleOpenComparator}
              />
            )}
            {currentView === 'comparator' && (
              <SkinComparatorView customSkin={customSkinForComparator} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
};
