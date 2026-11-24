# FASE 10.3 — JARVIS Eyes 3.0 (Ultimate Expressive Eye Engine)

## 1. Analisi dello Stato Iniziale (Baseline FASE 10.2)

- **Repository**: `bubiweb75/jarvislegobot` (commit stabile FASE 9.5: `7c33314`, baseline software non committata FASE 10.2).
- **Firmware ESP32-S3 (`04-Firmware/jarvis-desk-buddy`)**:
  - `EyeEngine` (`include/eye_engine.h`, `src/eye_engine.cpp`) con stile ibrido 2.0, 14 espressioni, pupille scure clampate, catchlight `2×2`, sopracciglia curve, target `30 FPS`.
  - `MonochromeFramebuffer` (`128×64`, 1024 byte XBM, zero allocazioni dinamiche).
  - `DisplayDriver` (`U8g2` su Hardware I²C `GPIO41=SDA`, `GPIO42=SCL`, `400 kHz`, `SH1106` default / `SSD1306` alternativo).
  - `StateMachine` (`STATE:*`, `LOOK:dx,dy`, `BLINK`, `AUTO:ON/OFF`, `PING`, `STATUS`, `DIAG`, pulsante `GPIO47`).
- **Simulatore Python (`04-Firmware/jarvis-desk-buddy-sim`)**:
  - `eye_engine.py`, `eye_engine_v2.py`, `simulator_gui.py`, `compare_engines.py`, `test_simulator.py`.
- **Control Center (`05-Voice-AI`)**:
  - `jarvis_app.py`, `eye_bridge.py`, Voice AI (`faster-whisper`, `Ollama`, `Piper`), Memoria L2/L3/L4, Personalità — tutti invariati.

### Matrice di Evoluzione (Baseline 2.0 → Eyes 3.0)

| Funzionalità | Stato FASE 10.2 | Miglioramento Eyes 3.0 |
|---|---|---|
| Geometrie | Super-capsule `32×34`, pupille, sopracciglia | **Organic Visor Companion**: superellissi organiche (`38×38`, `shape_power`, `taper`), mezzelune `HAPPY`/`WINK`, cuori pieni `LOVE`, ciglia `SLEEPING`, sopracciglia scolpite affusolate, doppi catchlight |
| Blink | Blink base + double-blink solo su `NEUTRAL` | Ease-out in riapertura, intervalli scalati per profilo, `SURPRISED` rapido, `SLEEPY` lento |
| Gaze | Sguardo random ogni 1.7–3.9s | Micro-saccadi discrete (`±1..3 px`), esplorazione coordinata, bias ritorno al centro, `LISTENING` stabile |
| Transizioni | Interpolazione esponenziale uniforme | Velocità scalata per profilo + boost rapido su `SURPRISED` (`1.85×`), 100% interrompibili |
| Micro-espressioni | Assenti | Motore contestuale (`BROW_RAISE`, `SIDE_GLANCE`, `EYE_SMILE`, `PUPIL_PULSE`, `QUICK_WINK`) senza alterare `expr_` |
| Rendering / Telemetria | `last_render_us_` mescolava render + I²C | Separazione netta `LastFrameRenderUs()` vs `LastI2cTransferUs()`, `ActualFps()`, `DroppedFrames()` |
| Simulatore | Parità 2.0 + `DIAG` base | Parità 3.0 completa + `PROFILE:*` + demo comparativa `compare_eyes_v2_v3.py` |

---

## 2. Studio dei Repository GitHub e Verifica Licenze

| Repository | Licenza | Punti chiave | Compatibilità / Rischi | Decisione |
|---|---|---|---|---|
| `FluxGarage/RoboEyes` | **GPL-3.0** | Tweening non bloccante, autoblinker/idle con jitter, direzioni cardinali, resizing curioso | Copyleft GPL-3.0 incompatibile con copia diretta in codebase non-GPL | Solo studio concettuale; implementazione originale |
| `playfultechnology/esp32-eyes` | **GPL-3.0** | Geometria procedurale stile Cozmo, coordinamento occhi/palpebre, zero bitmap | Copyleft GPL-3.0 | Solo studio concettuale; implementazione originale |
| `MuffledTech/MOchi` | **Nessuna licenza esplicita** (All Rights Reserved) | ESP32 + touch + OLED SH1106/SSD1306 stile Dasai Mochi | Rischio legale se copiato | Vietato copiare codice/asset |
| `AshishY794/oled-animation-examples` | **MIT** | Esempi OLED e nota tecnica su offset 2 px dell'SH1106 | Compatibile MIT | Riferimento su gestione offset SH1106 |
| `olikraus/u8g2` *(già in uso)* | **2-Clause BSD** (core) | `U8G2_SH1106_128X64` gestisce nativamente i 132×64 col (`+2px` offset), Full Buffer + `drawXBM` | Già integrata in `platformio.ini` | **Mantenuta** |
| `adafruit/Adafruit_SH110X` | **BSD** | Wrapper su `Adafruit_GFX`/`GrayOLED`/`BusIO` | Stack più pesante senza vantaggi rispetto a `U8g2` | **Non adottata** |

### 5 Miglioramenti Prioritari Adottati (100% Originali)
1. **Natural Gaze Engine**: micro-saccadi discrete + sguardo esplorativo + bias di ritorno al centro + stabilità in `LISTENING` + precedenza rigorosa di `LOOK:dx,dy`.
2. **Advanced Blink Engine**: chiusura progressiva, riapertura con ease-out organico, double-blink su `IDLE`/`HAPPY`, blink lento `SLEEPY`, blink rapido `SURPRISED`.
3. **Cinematic Transitions**: transizioni interrompibili con boost su `SURPRISED` e scaling per profilo.
4. **Micro-Expressions Engine**: 5 micro-espressioni contestuali non distruttive (`BROW_RAISE`, `SIDE_GLANCE`, `EYE_SMILE`, `PUPIL_PULSE`, `QUICK_WINK`) con cooldown e soppressione in `SLEEPING`/`LOVE`/`SURPRISED`/`WINK`.
5. **Visual Personality Profiles + Telemetria OLED**: profili visivi `CALM`, `LIVELY` (default), `PLAYFUL` + separazione `RENDER_US` / `PRESENT_US` / `FPS` / `DROPPED`.

---

## 3. Architettura JARVIS Eyes 3.0

Organizzazione modulare all'interno di `EyeEngine` (C++ e Python 1:1):
1. **Expression Geometry** (`ApplyExpressionTargets` / `_apply_expression_targets`): 14 espressioni invariate negli ID.
2. **Visual Personality Controller** (`VisualProfile`: `CALM`, `LIVELY`, `PLAYFUL`): scala velocità di transizione, frequenza sguardo, frequenza micro-espressioni e blink.
3. **Natural Gaze Controller** (`UpdateGaze` / `_update_gaze` + `SetGazeOffset`): micro-saccadi vs esplorazione vs precedenza `LOOK`.
4. **Blink Controller** (`UpdateBlinker` / `_update_blinker`): fasi `OPEN → CLOSING → HOLD_CLOSED → OPENING` con ease-out.
5. **Micro-expression Controller** (`UpdateMicroExpressions` / `_update_micro_expressions`): temporizzate (`300–580 ms`), ripristinano sempre i target dell'espressione attiva.
6. **Transition Controller** (`InterpolateEye` / `_interpolate_eye`): interpolazione esponenziale indipendente dal frame rate con `transition_boost_`.
7. **Frame Renderer & Display Telemetry** (`RenderToFramebuffer` + `display::PresentFramebuffer`): zero allocazioni dinamiche, buffer `128×64` XBM.

---

## 4. Profili Visivi e Parametri

| Profilo | `speed_scale` | `gaze_freq_scale` | `micro_freq_scale` | `blink_freq_scale` | `double_blink` | Uso consigliato |
|---|---|---|---|---|---|---|
| `CALM` | `0.72` | `0.65` | `0.45` | `0.80` | `8%` | Atmosfera rilassata / scrivania silenziosa |
| `LIVELY` *(default)* | `1.00` | `1.00` | `1.00` | `1.00` | `20%` | Personalità "Amichetto Vivace" equilibrata |
| `PLAYFUL` | `1.22` | `1.35` | `1.65` | `1.15` | `28%` | Massima vivacità e ammiccamenti |

Comando seriale retrocompatibile aggiunto: `PROFILE:CALM|LIVELY|PLAYFUL` (risposta `OK:PROFILE=...`), visibile anche in `STATUS` e `DIAG`.

---

## 5. Compatibilità Preservata

- Tutte le 14 espressioni e gli identificatori invariati.
- Tutti i comandi seriali esistenti invariati (`STATE:*`, `LOOK:dx,dy`, `BLINK`, `AUTO:ON`, `AUTO:OFF`, `PING`, `STATUS`, `DIAG`, `HELP`).
- `EyeEngine2`, `EyeBridge`, `StateMachine` e `JARVIS Control Center` compatibili senza modifiche a STT/LLM/TTS/Memoria/Personalità.

---

## 6. Confronto Visivo Eyes 2.0 vs Eyes 3.0

Script dedicato separato dal Control Center: `04-Firmware/jarvis-desk-buddy-sim/compare_eyes_v2_v3.py`
- Confronta `EyeEngineV2Baseline` (`eye_engine_v2_baseline.py`, conservato come baseline 2.0) contro il vero motore unificato `EyeEngine` (`eye_engine.py`, Eyes 3.0 Organic Visor Companion, `spacing_px=12`).
- Modalità CLI deterministica (`--cli`): confronta pixel accesi, pixel differenti (`284–1893 px` su tutte le 14 espressioni + `BLINK` + `LOOK`) e tempo di render.
- Modalità GUI affiancata (`--gui`) e export PNG (`--save-gallery`): rendering rigorosamente monocromatico `128×64` (`#FFFFFF` su `#000000`).

---

## 7. Verifiche Eseguite (Integrazione Definitiva)

- **Compilazione Firmware PlatformIO** (`esp32s3_sh1106` e `esp32s3_ssd1306`, solo compilazione, nessun upload/erase):
  - `esp32s3_sh1106`: `SUCCESS` (`15.39 s`, RAM `8.2%` / `27000 B`, Flash `12.8%` / `427652 B`).
  - `esp32s3_ssd1306`: `SUCCESS` (`15.49 s`, RAM `8.2%` / `27000 B`, Flash `12.8%` / `427668 B`).
- **Test Simulatore (`04-Firmware/jarvis-desk-buddy-sim`)**: `35` test superati (`OK` in `4.020 s`), incluse tutte le 14 espressioni, blink, gaze, transizioni, micro-espressioni, i 3 profili visivi (`CALM`, `LIVELY`, `PLAYFUL`) e i comandi seriali.
- **Test Voice AI & Control Center (`05-Voice-AI/tests`)**: `50` test superati (`OK` in `15.532 s`).
- **Smoke Test GUI (`05-Voice-AI/jarvis_app.py`)**: `--smoke-ms 300` e `--demo --smoke-ms 300` terminati con exit code `0`.
- **Confronto Host C++/Python (`compare_engines.py`)**: `SKIPPED` — nessun compilatore C++ host (`g++`/`clang++`) presente nel `PATH` Windows; la verifica C++ è coperta dalla compilazione PlatformIO `xtensa-esp32s3-elf` e dall'allineamento 1:1 con `eye_engine.py`.

---

## 8. Piano di Collaudo OLED Futuro (Hardware NON ancora collegato)

1. Verificare a scheda spenta regolatore LDO, ponticelli `VDD/GND` e pull-up I²C a `3.3 V` sul PCB V2.2 del display `1.3" SH1106`.
2. Cablare `VCC → 3V3`, `GND → GND`, `SCK → GPIO42`, `SDA → GPIO41`.
3. Solo dopo autorizzazione esplicita dell'utente: compilare/caricare `esp32s3_sh1106`, verificare su seriale `115200` baud il comando `DIAG` (`OLED_ADDR=0x3C`, `RENDER_US`, `PRESENT_US`, `FPS`, `DROPPED`).
4. In caso di shift laterale di 2 pixel, passare a `esp32s3_ssd1306`.
