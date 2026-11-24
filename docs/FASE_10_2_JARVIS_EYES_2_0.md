# FASE 10.2 — JARVIS Eyes 2.0 (Hybrid Expressive Eye Engine)

## 1. Obiettivo e Architettura

**JARVIS Eyes 2.0** introduce un motore grafico espressivo **ibrido (soft + cartoon + futuristico)** per display OLED monocromatici **128×64** (`SH1106` / `SSD1306`), mantenendo la parità 1:1 tra:

- Firmware ESP32-S3 C++: `04-Firmware/jarvis-desk-buddy/include/eye_engine.h`, `04-Firmware/jarvis-desk-buddy/src/eye_engine.cpp`
- Simulatore Python Desktop: `04-Firmware/jarvis-desk-buddy-sim/eye_engine.py`

Tutti i contratti esistenti sono preservati invariati:
- 14 identificatori `Expression` (`IDLE`/`NEUTRAL`, `HAPPY`, `CURIOUS`, `SLEEPY`, `LISTENING`, `THINKING`, `SPEAKING`, `SURPRISED`, `SHY`, `LOVE`, `WINK`, `CONFUSED`, `MISCHIEVOUS`, `SLEEPING`)
- Protocollo seriale (`STATE:*`, `LOOK:dx,dy`, `BLINK`, `AUTO:ON`, `AUTO:OFF`, `PING`, `STATUS`, `DIAG`, `HELP`)
- Compatibilità completa con `EyeEngine2` (`eye_engine_v2.py`), `EyeBridge` (`eye_bridge.py`) e `JARVIS Control Center` (`jarvis_app.py`).

## 2. Specifica Geometrica (128×64 Monocromatico)

- **Risoluzione framebuffer**: `128 × 64` pixel (buffer XBM da 1024 byte).
- **Margini di sicurezza**: `x >= 4`, `x <= 123`, `y >= 4`, `y <= 59` (le colonne `0..2`, `125..127` e le righe `0..2`, `62..63` restano sempre spente per evitare tagli ai bordi/cornice LEGO).
- **Occhio base (`DEFAULT` / `IDLE`)**:
  - Larghezza: `32 px` (`kDefaultEyeWidth` / `DEFAULT_EYE_WIDTH`)
  - Altezza: `34 px` (`kDefaultEyeHeight` / `DEFAULT_EYE_HEIGHT`)
  - Raggio angoli: `11 px` (`kDefaultCornerRadius` / `DEFAULT_CORNER_RADIUS`)
  - Spaziatura centrale configurata nel firmware: `14 px` (`g_eyes.Begin(30, 14)`)
- **Pupilla mobile**:
  - Cerchio scuro (`color=0`) con raggio nominale `4.0–6.5 px` (disattivato in `LOVE`, `SLEEPING` e sull'occhio chiuso di `WINK`).
  - Clamping rigoroso all'interno della sclera visibile al netto delle palpebre (`min_px..max_px`, `min_py..max_py`) in modo da non toccare mai il bordo esterno dell'occhio.
- **Catchlight futuristico**:
  - Riflesso principale `2×2 px` acceso (`color=1`) nell'quadrante superiore sinistro della pupilla.
  - Secondo micro-glint `1×1 px` diagonale per pupille con raggio `>= 5`.
- **Sopracciglia stilizzate**:
  - Arco parabolico spessore `2 px` con offset verticale (`brow_offset`) e inclinazione (`brow_tilt`), clampato rigorosamente nei margini sicuri (`x >= 4`, `y >= 4`).

## 3. Tabella delle 14 Espressioni

| Espressione | Sclera (W×H, R) | Palpebre / Forma | Pupilla (r, offset) | Sopracciglia (offset, tilt) | Dettagli / Micro-animazioni |
|---|---|---|---|---|---|
| `IDLE` / `NEUTRAL` | 32×34, R11 | Aperte | r=6.0, centro | off=0 | Respiro verticale leggero, blink naturale (20% double-blink) |
| `HAPPY` | 33×31, R12 | Sorriso inferiore (`lower=6, arch=11`) | r=5.0, dy=-1 | off=4.0, tilt=0 | Rimbalzo allegro verticale |
| `CURIOUS` | L:28×27 R9 / R:34×36 R12 | Asimmetrica (`upper_l=1, upper_r=5` su L) | L:r=6 dx=3 / R:r=6.5 dx=3 dy=-1 | L:4,+1.5 / R:5,-1.5 | Micro-inclinazione curiosa |
| `SLEEPY` | 31×28, R10 | Palpebre cadenti (`upper=12, arch=2.5`) | r=4.5, dy=+2 | off=0 | Blink più lento, postura abbassata |
| `LISTENING` | 32×36, R11 | Ben aperte, attente | r=6.5, centro | off=0 | Indicatore inferiore pulsante (`pulse_r` 1/2 px) |
| `THINKING` | 30×29, R10 | Concentrata (`upper_l=4,2` / `lower=3`) | r=5.0, dx=4 dy=-2 | L:4,+2 / R:5,-1 | 3 puntini animati in basso + sguardo in alto a destra |
| `SPEAKING` | 32×32, R11 | Leggero sorriso (`lower=3, arch=5`) | r=5.5 | off=0 | Modulazione ritmica dolce in altezza e guance |
| `SURPRISED` | 34×38, R13 | Spalancate | r=4.0 (contratta) | off=5.0, tilt=0 | Simbolo `!` in alto al centro |
| `SHY` | 29×25, R10 | Palpebre alte (`upper=5`) | r=5.0, dx=-3 dy=+2 | off=4.0, tilt L:-2 R:+2 | Sguardo laterale in basso + rossore sulle guance |
| `LOVE` | 30×30 (cuori) | Cuori pixel-art (`scale=2`) | r=0 (disattiva) | off=0 | Battito cardiaco sincronizzato |
| `WINK` | L:32×34 R11 / R:arco | R chiuso ad arco sorridente | L:r=6.0 / R:r=0 | L:off=4.0 / R:0 | Occhio sinistro vivace con micro-oscillazione |
| `CONFUSED` | L:27×25 / R:33×35 | Asimmetrica (`upper_l=5,2` su L) | L:r=5 dx=-2 / R:r=6 dx=2 dy=-1 | L:4,+2.5 / R:5,-2.5 | Punto interrogativo `?` in alto a destra |
| `MISCHIEVOUS` | 32×28, R9 | Sguardo furbo inclinato (`1↔8`, `lower=4`) | r=5.0, dx=4 | off=4.0, tilt L:+3 R:-3 | Oscillazione laterale sorniona |
| `SLEEPING` | 30×24 (archi) | Occhi chiusi rilassati | r=0 (disattiva) | off=0 | `Z z` fluttuanti + respiro lento |

## 4. Animazioni, Parametri Regolabili e Misurazione Render

- **Frequenza target**: `30 FPS` (`frame_interval_ms_ = 33 ms`, `g_eyes.Begin(30, 14)`).
- **Interpolazione esponenziale indipendente dal frame rate (`SmoothExp`)**:
  - Posizione occhi (`x, y`), palpebre, sopracciglia, `pupil_radius`: fattore `12.0`
  - Dimensioni (`width, height, corner_radius`): fattore `10.0`
  - Sguardo pupille (`pupil_dx, pupil_dy`): fattore `14.0`
- **Sguardo (`LOOK:dx,dy`)**:
  - `dx` clampato a `[-11, 11]`, `dy` a `[-6, 6]`.
  - Suddivisione naturale tra movimento sclera (`0.45 * dx`, `0.40 * dy`) e movimento pupilla (`0.55 * dx`, `0.45 * dy`).
- **Telemetria render (Firmware C++)**:
  - `EyeEngine::LastFrameRenderUs()` misura in microsecondi (`micros()`) il tempo reale di `RenderFrame(now_ms)`.
  - Esposto nel comando seriale `DIAG` come campo `;RENDER_US=<us>`.

## 5. Differenze tra Simulatore PC e Display OLED Reale

- Il simulatore PC renderizza il medesimo framebuffer `128×64` scalato su canvas Tkinter a contrasto ideale.
- Sul display OLED fisico `1.3" 128×64`, la leggibilità dipende da contrasto effettivo (`U8g2`), angolo di visione e velocità del bus I²C (`400 kHz` in `pinout_config.h`: `kI2cClockHz = 400000`).
- La trasmissione I²C completa di 1024 byte tramite `u8g2.sendBuffer()` richiede alcuni millisecondi sul bus I²C (separati dal tempo CPU di `RenderFrame()` misurato da `LastFrameRenderUs()`).

## 6. Procedura Sicura di Collaudo Elettrico / I²C prima di Eyes 2.0

**ATTENZIONE — Verifiche obbligatorie prima di alimentare il display reale (PCB V2.2):**

1. **Controllo visivo ponticelli e regolatore sul PCB V2.2**:
   - Verificare a vista (o con multimetro in continuità a scheda spenta) l'eventuale regolatore LDO sul retro del modulo OLED e i ponticelli `VDD`/`GND` (alcuni moduli 1.3" hanno `VCC/GND` invertibili tramite resistori/ponticelli `0 Ω`!).
   - Confermare l'ordine effettivo dei pin serigrafati (`VCC — GND — SCK — SDA`) rispetto al pinout reale del PCB.
   - Verificare la presenza delle resistenze di pull-up I²C su `SDA`/`SCL` verso `3.3 V` (evitare collegamenti a `5 V`).
2. **Cablaggio previsto su ESP32-S3-N16R8 (a PC scollegato)**:
   - `VCC` → `3V3` ESP32-S3
   - `GND` → `GND` ESP32-S3
   - `SCK` → `GPIO42`
   - `SDA` → `GPIO41`
3. **Nota porta seriale ESP32-S3 (da FASE 10.1)**:
   - Sulla scheda ESP32-S3-N16R8 collegata tramite porta UART CH343 (`COM4`), il monitor seriale lavora a `115200` baud; per ricevere i log su UART0 è necessario `ARDUINO_USB_CDC_ON_BOOT=0` (in `platformio.ini` attuale è `1` per USB CDC nativa).
4. **Test I²C minimo prima del firmware grafico**:
   - Alimentare via USB e verificare l'ACK I²C all'indirizzo `0x3C` (o `0x3D`) tramite comando `DIAG` o scanner I²C minimo prima di valutare le animazioni complete.
5. **Verifica driver SH1106 vs SSD1306**:
   - L'ambiente predefinito è `esp32s3_sh1106`; se lo schermo mostra bande spostate di 2 pixel o artefatti di offset laterale, passare all'ambiente `esp32s3_ssd1306` (o viceversa).

## 7. Limitazioni Note

- Su `128×64` monocromatico senza anti-aliasing, le curve delle sopracciglia e i riflessi `2×2` / `1×1` hanno quantizzazione a pixel interi.
- Il trasferimento fisico `U8g2` su I²C e la resa visiva sul pannello `1.3"` PCB V2.2 non sono ancora stati collaudati su hardware reale in questa fase.
