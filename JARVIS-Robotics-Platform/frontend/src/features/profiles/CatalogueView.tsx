import React, { useState } from 'react';
import { CATALOG_SKINS } from '../../engine/eyes/baseline';
import { MonochromeFramebuffer } from '../../engine/framebuffer/MonochromeFramebuffer';
import { EyeEngine } from '../../engine/eyes/EyeEngine';
import { OledDisplay } from '../../components/OledDisplay';
import { SkinDefinition } from '../../engine/eyes/types';
import { Bot, CheckCircle2, Layers, Sliders } from 'lucide-react';

interface CatalogueViewProps {
  onSelectSkinToEdit?: (skin: SkinDefinition) => void;
  onOpenComparator?: () => void;
}

export const CatalogueView: React.FC<CatalogueViewProps> = ({ onSelectSkinToEdit, onOpenComparator }) => {
  const [selectedSkinId, setSelectedSkinId] = useState<string>('skin-jarvis-original-v3');

  // Preview framebuffers map
  const [previews] = useState(() => {
    const map = new Map<string, MonochromeFramebuffer>();
    CATALOG_SKINS.forEach((skin) => {
      const fb = new MonochromeFramebuffer();
      const engine = new EyeEngine(skin);
      engine.setExpression('NEUTRAL');
      engine.setVisualProfile('CALM');
      // Run a few ticks to settle natural layout
      for (let i = 0; i < 5; i++) {
        engine.update(0.016);
      }
      engine.render(fb);
      map.set(skin.skin_id, fb);
    });
    return map;
  });

  const identitiesMeta = [
    {
      id: 'jarvis',
      skinId: 'skin-jarvis-original-v3',
      name: 'JARVIS Original',
      subtitle: 'Il robot primario originale di riferimento',
      status: 'PRODUZIONE / ATTIVO',
      statusColor: 'emerald',
      voice: 'Maschile formale (TTS Cloud / ElevenLabs)',
      personality: 'Maggiordomo britannico, sobrio, tecnico, ironico',
      wakeWord: 'Ehi Jarvis (Hi-ESP)',
      hardware: 'Carrier Board V1 (ESP32-S3, OLED SH1106 I2C0 41/42, Touch GPIO1)',
      specs: 'Superellisse p=2.6 • Dim: 38x38 • Taper: 0.10 • Catchlight Double',
    },
    {
      id: 'eva',
      skinId: 'skin-eva-elegant-v1',
      name: 'EVA Companion',
      subtitle: 'Assistente empatico e accogliente',
      status: 'PREVIEW / ANTEPRIMA',
      statusColor: 'purple',
      voice: 'Femminile morbido naturale',
      personality: 'Empatica, accogliente, attenta alle sfumature emotive',
      wakeWord: 'Ciao Eva',
      hardware: 'Compatibile Desktop V1',
      specs: 'Superellisse p=2.3 • Dim: 36x40 • Taper: 0.08 • Occhio raccordato',
    },
    {
      id: 'nova',
      skinId: 'skin-nova-hud-v1',
      name: 'NOVA Explorer',
      subtitle: 'Robot dinamico e orientato alla ricerca',
      status: 'PREVIEW / ANTEPRIMA',
      statusColor: 'cyan',
      voice: 'Neutro energico sintetico',
      personality: 'Curiosa, analitica, orientata ai dati e alla scoperta',
      wakeWord: 'Attiva Nova',
      hardware: 'Compatibile Desktop V1 / Mobile V2',
      specs: 'Superellisse p=3.6 • Dim: 32x34 • Taper: 0.22 • Geometria incisiva',
    },
    {
      id: 'tars',
      skinId: 'skin-tars-geometric-v1',
      name: 'TARS Monolith',
      subtitle: 'Design monolitico e geometrico essenziale',
      status: 'PREVIEW / ANTEPRIMA',
      statusColor: 'amber',
      voice: 'Profondo metallico robotico',
      personality: 'Monolitico, pragmatico, 90% onestà, 75% umorismo',
      wakeWord: 'Tars ascolta',
      hardware: 'Compatibile Desktop V1',
      specs: 'Superellisse p=4.8 • Dim: 42x22 • Taper: 0.02 • Feritoia orizzontale',
    },
    {
      id: 'neko',
      skinId: 'skin-neko-feline-v1',
      name: 'NEKO Playful',
      subtitle: 'Compagno giocoso ed espressivo stile anime',
      status: 'PREVIEW / ANTEPRIMA',
      statusColor: 'rose',
      voice: 'Acuto vivace giovanile',
      personality: 'Giocherellone, reattivo al tocco, curioso, allegro',
      wakeWord: 'Ehi Neko',
      hardware: 'Compatibile Desktop V1',
      specs: 'Superellisse p=2.2 • Dim: 36x42 • Taper: 0.12 • Slit verticale',
    },
  ];

  const activeIdentity = identitiesMeta.find((i) => i.skinId === selectedSkinId) || identitiesMeta[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-jarvis-panel border border-jarvis-border p-6 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-jarvis-cyan/10 text-jarvis-cyan border border-jarvis-cyan/20">
              CATALOGO ROBOTICO MULTI-IDENTITÀ
            </span>
            <span className="text-xs text-jarvis-muted font-mono">5 Profili Registrati</span>
          </div>
          <h2 className="text-xl font-bold text-white">Catalogo Identità & Skin Oculari</h2>
          <p className="text-xs text-jarvis-muted">
            Esplora le 5 identità convalidate della piattaforma. JARVIS Original costituisce la Golden Baseline immutabile.
          </p>
        </div>

        {onOpenComparator && (
          <button
            onClick={onOpenComparator}
            className="px-4 py-2 bg-jarvis-card hover:bg-jarvis-border border border-jarvis-border text-jarvis-text rounded-lg text-xs font-medium flex items-center gap-2 transition-colors"
          >
            <Layers className="w-4 h-4 text-jarvis-cyan" />
            Confronta nel Comparatore Dual-OLED
          </button>
        )}
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {identitiesMeta.map((item) => {
          const skin = CATALOG_SKINS.find((s) => s.skin_id === item.skinId)!;
          const fb = previews.get(item.skinId);
          const isSelected = selectedSkinId === item.skinId;

          return (
            <div
              key={item.id}
              onClick={() => setSelectedSkinId(item.skinId)}
              className={`bg-jarvis-panel border rounded-xl p-5 cursor-pointer transition-all flex flex-col justify-between ${
                isSelected
                  ? 'border-jarvis-cyan shadow-lg shadow-jarvis-cyan/10 ring-1 ring-jarvis-cyan'
                  : 'border-jarvis-border hover:border-jarvis-muted'
              }`}
            >
              <div>
                {/* Header status */}
                <div className="flex items-center justify-between mb-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider ${
                      item.statusColor === 'emerald'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : item.statusColor === 'purple'
                        ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
                        : item.statusColor === 'cyan'
                        ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                        : item.statusColor === 'amber'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {item.status}
                  </span>
                  <span className="text-[10px] text-jarvis-muted font-mono">{skin.skin_id}</span>
                </div>

                {/* OLED Mini Preview */}
                <div className="flex justify-center my-3 bg-black/60 p-2 rounded-lg border border-jarvis-border/40">
                  {fb && (
                    <OledDisplay
                      framebuffer={fb}
                      zoom={2}
                      color="#00e5ff"
                      glow={false}
                      showGrid={false}
                    />
                  )}
                </div>

                <h3 className="text-base font-bold text-white mb-0.5">{item.name}</h3>
                <p className="text-xs text-jarvis-muted mb-3">{item.subtitle}</p>

                <div className="space-y-1.5 text-xs border-t border-jarvis-border/60 pt-3">
                  <div className="text-[11px] text-jarvis-muted">
                    <strong className="text-jarvis-text">Personalità:</strong> {item.personality}
                  </div>
                  <div className="text-[11px] text-jarvis-muted">
                    <strong className="text-jarvis-text">Wake Word:</strong> {item.wakeWord}
                  </div>
                  <div className="text-[11px] text-jarvis-muted">
                    <strong className="text-jarvis-text">Specifiche:</strong> {item.specs}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-4 pt-3 border-t border-jarvis-border/60 flex items-center justify-between">
                <span className="text-[10px] text-jarvis-cyan-dim font-mono">
                  {item.id === 'jarvis' ? 'GOLDEN BASELINE' : 'DERIVATO COMPANION'}
                </span>

                {onSelectSkinToEdit && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectSkinToEdit(skin);
                    }}
                    className="px-2.5 py-1 bg-jarvis-card hover:bg-jarvis-border text-white text-xs rounded border border-jarvis-border flex items-center gap-1 transition-colors"
                  >
                    <Sliders className="w-3 h-3 text-jarvis-cyan" />
                    Modifica
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Identity Deep-Dive Panel */}
      <div className="bg-jarvis-panel border border-jarvis-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Bot className="w-5 h-5 text-jarvis-cyan" />
          <h3 className="text-base font-bold text-white">
            Dettagli Profilo Selezionato: {activeIdentity.name} ({activeIdentity.id})
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <span className="text-jarvis-muted block mb-1">Stato Operativo</span>
            <span className="font-semibold text-white">{activeIdentity.status}</span>
          </div>
          <div className="p-3 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <span className="text-jarvis-muted block mb-1">Hardware Target</span>
            <span className="font-semibold text-white">{activeIdentity.hardware}</span>
          </div>
          <div className="p-3 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <span className="text-jarvis-muted block mb-1">Voce & Sintesi</span>
            <span className="font-semibold text-white">{activeIdentity.voice}</span>
          </div>
          <div className="p-3 bg-jarvis-card rounded-lg border border-jarvis-border/60">
            <span className="text-jarvis-muted block mb-1">Algoritmo Occhi</span>
            <span className="font-semibold text-white font-mono">{activeIdentity.specs}</span>
          </div>
        </div>

        {activeIdentity.id === 'jarvis' && (
          <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>
              <strong>Garanzia di Conformità:</strong> Il profilo JARVIS Original è blindato matematicamente per corrispondere esattamente ai file C++ <code>eye_engine.cpp</code> e <code>monochrome_fb.cpp</code> del firmware originale.
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
