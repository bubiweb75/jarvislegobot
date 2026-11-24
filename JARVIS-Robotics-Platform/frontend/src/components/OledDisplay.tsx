import React, { useRef, useEffect } from 'react';
import { MonochromeFramebuffer, FB_WIDTH, FB_HEIGHT } from '../engine/framebuffer/MonochromeFramebuffer';
import { Download, Copy, Check } from 'lucide-react';

export interface OledDisplayProps {
  framebuffer: MonochromeFramebuffer;
  zoom?: 2 | 3 | 4 | 5 | 6 | 8 | number;
  showPixelGrid?: boolean;
  showGrid?: boolean;
  showGlow?: boolean;
  glow?: boolean;
  invert?: boolean;
  color?: string;
  phosphorColor?: string;
  scanlines?: boolean;
  onFrameExport?: () => void;
  className?: string;
}

export const OledDisplay: React.FC<OledDisplayProps> = ({
  framebuffer,
  zoom = 4,
  showPixelGrid,
  showGrid,
  showGlow,
  glow,
  invert = false,
  color,
  phosphorColor = '#00e5ff',
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [copied, setCopied] = React.useState(false);

  const effectiveGrid = showPixelGrid ?? showGrid ?? false;
  const effectiveGlow = showGlow ?? glow ?? true;
  const effectiveColor = color ?? phosphorColor;
  const effectiveZoom = Math.max(1, Math.floor(zoom));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = FB_WIDTH * effectiveZoom;
    const height = FB_HEIGHT * effectiveZoom;

    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }

    // Disabilita anti-aliasing per resa pixel-perfect
    ctx.imageSmoothingEnabled = false;

    // Sfondo OLED (nero assoluto)
    ctx.fillStyle = invert ? effectiveColor : '#05080c';
    ctx.fillRect(0, 0, width, height);

    const onColor = invert ? '#05080c' : effectiveColor;
    ctx.fillStyle = onColor;

    // Disegna pixel attivi
    for (let y = 0; y < FB_HEIGHT; ++y) {
      for (let x = 0; x < FB_WIDTH; ++x) {
        if (framebuffer.getPixel(x, y) === 1) {
          ctx.fillRect(x * effectiveZoom, y * effectiveZoom, effectiveZoom, effectiveZoom);
        }
      }
    }

    // Griglia pixel opzionale per ispezione
    if (effectiveGrid && effectiveZoom >= 4) {
      ctx.strokeStyle = invert ? '#ffffff22' : '#00e5ff18';
      ctx.lineWidth = 1;
      for (let x = 0; x <= FB_WIDTH; ++x) {
        ctx.beginPath();
        ctx.moveTo(x * effectiveZoom + 0.5, 0);
        ctx.lineTo(x * effectiveZoom + 0.5, height);
        ctx.stroke();
      }
      for (let y = 0; y <= FB_HEIGHT; ++y) {
        ctx.beginPath();
        ctx.moveTo(0, y * effectiveZoom + 0.5);
        ctx.lineTo(width, y * effectiveZoom + 0.5);
        ctx.stroke();
      }
    }
  }, [framebuffer, effectiveZoom, effectiveGrid, invert, effectiveColor]);

  const handleDownloadPng = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `jarvis_eyes_frame_${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  const handleCopyXbm = () => {
    const xbmCode = framebuffer.toXBM('jarvis_snapshot');
    navigator.clipboard.writeText(xbmCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`relative flex flex-col items-center select-none ${className}`}>
      {/* Cornice display OLED */}
      <div
        className={`relative p-3 rounded-xl bg-black border border-jarvis-border transition-all duration-300 ${
          effectiveGlow ? 'shadow-[0_0_35px_rgba(0,229,255,0.25)]' : 'shadow-lg'
        }`}
      >
        {/* Label Serigrafia SH1106 */}
        <div className="flex justify-between items-center mb-2 px-1 text-[10px] font-mono tracking-wider text-jarvis-muted/70">
          <span>OLED 1.3" 128x64 MONO</span>
          <span className="text-jarvis-cyan">I2C: 0x3C (GPIO 41/42)</span>
        </div>

        {/* Canvas Display */}
        <div className="overflow-hidden rounded border border-jarvis-border/60 bg-black">
          <canvas
            ref={canvasRef}
            className="block"
            style={{
              imageRendering: 'pixelated'
            }}
          />
        </div>

        {/* Barra di stato inferiore del display */}
        <div className="mt-2 flex items-center justify-between text-[11px] font-mono text-jarvis-muted px-1">
          <span>1024 BYTES (XBM RAW)</span>
          <div className="flex gap-2">
            <button
              onClick={handleCopyXbm}
              className="hover:text-jarvis-cyan transition flex items-center gap-1"
              title="Copia sorgente C++ XBM negli appunti"
            >
              {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
              <span>{copied ? 'Copiato' : 'XBM'}</span>
            </button>
            <button
              onClick={handleDownloadPng}
              className="hover:text-jarvis-cyan transition flex items-center gap-1"
              title="Salva frame come PNG"
            >
              <Download size={12} />
              <span>PNG</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
