# GITHUB_REPOS_ANALYSIS — Analisi Tecnica e Riutilizzo Repository di Riferimento (FASE 6)

> **Stato:** Analisi completata in preparazione alla FASE 6. **Nessuna modifica al codice** è stata ancora applicata (in attesa dei componenti hardware).
> **Riferimenti:** [HARDWARE_PINOUT.md](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/06-Hardware-Integration/HARDWARE_PINOUT.md) | [AUDIO_ARCHITECTURE.md](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/06-Hardware-Integration/AUDIO_ARCHITECTURE.md) | [THIRD_PARTY_LICENSES.md](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/04-Firmware/jarvis-desk-buddy/THIRD_PARTY_LICENSES.md)

---

## 1. Censimento Licenze, Stato e Compatibilità Hardware

| Repository | Licenza | Ultimo Push | Target Hardware Principale | Compatibilità con JARVIS (ESP32-S3 N16R8 + SH1106 128×64) |
|---|---|---|---|---|
| [`78/xiaozhi-esp32`](https://github.com/78/xiaozhi-esp32) | **MIT** | `2026-11-14` | ESP32-S3 (`bread-compact-wifi`: INMP441 + MAX98357A + OLED SH1106/SSD1306 + GPIO47) | ✅ **Alta** per driver I²S (`NoAudioCodecSimplex`) e board config; ❌ non sostituire tutto il firmware (accoppiato a Wi-Fi/Opus/XiaoZhi cloud). |
| [`xinnan-tech/xiaozhi-esp32-server`](https://github.com/xinnan-tech/xiaozhi-esp32-server) | **MIT** | `2026-11-13` | Server Python 3.10 (`torch==2.2.2`, `funasr`, `sherpa_onnx`, `vosk`, `edge_tts`, `websockets`) | ⚠️ **Solo riferimento futuro (RPi 5)** se si passasse a Wi-Fi+Opus; superfluo rispetto al nostro stack italiano (`faster-whisper` + `Ollama` + `Piper Riccardo`). |
| [`Carmoruda/Jarvis`](https://github.com/Carmoruda/Jarvis) | **MIT** | `2026-07-26` | ESP32 / OLED monocromatico | ✅ **Già integrato e attribuito** in `04-Firmware/jarvis-desk-buddy/` (`eye_engine.h/.cpp` e `THIRD_PARTY_LICENSES.md`). |
| [`FamousWolf/deskbuddy`](https://github.com/FamousWolf/deskbuddy) | **MIT** | `2026-09-01` | ESPHome + ESP32-S3-Box-3 (LCD a colori 2,4") | ❌ **Incompatibile** come codice (ESPHome + display a colori); ✅ utile solo l'idea di micro-animazioni/easing. |
| [`StefanRiese/blinky-desk-companion`](https://github.com/StefanRiese/blinky-desk-companion) | **Nessuna (All Rights Reserved)** | `2026-11-06` | ESP-IDF + AMOLED/LCD rotondi (`amoled175`, `ws146`) | ⛔ **Divieto di copia codice** (nessuna licenza). Già ispirata in modo 100% originale la separazione Host-Link. |

---

## 2. Analisi Approfondita del Codice Esaminato

### A. `78/xiaozhi-esp32` — Punti Chiave sul Codice Reale
1. **`main/boards/bread-compact-wifi/config.h`:**
   - Usa `AUDIO_I2S_METHOD_SIMPLEX` con **gli stessi identici GPIO** già pianificati per JARVIS:
     - `INMP441`: `WS=GPIO4`, `SCK=GPIO5`, `DIN=GPIO6` (`16000 Hz`).
     - `MAX98357A`: `DOUT=GPIO7`, `BCLK=GPIO15`, `LRCK=GPIO16` (`24000 Hz`).
     - `OLED`: `SDA=GPIO41`, `SCL=GPIO42` (`CONFIG_OLED_SH1106_128X64` / `SSD1306`).
     - `Pulsante`: `GPIO47`.
2. **`main/audio/codecs/no_audio_codec.cc` (`NoAudioCodecSimplex`):**
   - **Due controller I²S distinti** (`XIAOZHI_I2S_PORT(0)` TX e `XIAOZHI_I2S_PORT(1)` RX) con `I2S_DATA_BIT_WIDTH_32BIT`, `I2S_SLOT_MODE_MONO`, `I2S_STD_SLOT_LEFT` e `auto_clear_after_cb = true`.
   - **Acquisizione `INMP441` (`NoAudioCodec::Read`):** legge campioni 32-bit dal DMA e applica `bit32_buffer[i] >> 12` con clamp a `±INT16_MAX`. Questo risolve il problema tipico dell'INMP441 (24-bit MSB-aligned), che con `>> 16` suona troppo debole e senza saturazione distorce ai picchi.
   - **Riproduzione `MAX98357A` (`NoAudioCodec::Write`):** applica una curva di volume percettiva quadratica (`pow(volume / 100.0, 2) * 65536`) su `int64_t` con saturazione `INT32_MIN..INT32_MAX`.
   - **`EnableInput(bool)` / `EnableOutput(bool)`:** abilita/disabilita i canali I²S solo quando servono, riducendo traffico DMA e prevenendo eco acustico durante `SPEAKING`.
3. **`main/audio/audio_service.h`:**
   - Gestione asincrona con eventi FreeRTOS (`on_playback_drained`, `on_vad_change`) e code separate per ingresso/uscita. La parte `esp_opus` e `wake_word` non serve nella nostra v1 USB (usiamo PCM 16 kHz su USB-CDC).

### B. Confronto con `04-Firmware/jarvis-desk-buddy/`
- `jarvis-desk-buddy` possiede già un motore grafico **superiore** per OLED 128×64 (`EyeEngine` a 50 FPS, interpolazione esponenziale FPS-indipendente, 7 espressioni, blink naturale e simulatore Python 1:1) rispetto al semplice display LVGL testuale di `xiaozhi-esp32`.
- Quello che **manca** in `jarvis-desk-buddy` (e che aggiungeremo dopo i Test 1–4) è proprio la parte **I²S (`INMP441` + `MAX98357A`)**, il **framing binario USB-CDC** e l'eventuale **reattività occhi al livello audio** durante `SPEAKING`.

---

## 3. Tabella Comparativa e Classificazione Riutilizzo

| Funzionalità | Repository Sorgente | Tipo | Vantaggio per JARVIS | Difficoltà Integrazione | Rischi / Vincoli | Raccomandazione |
|---|---|---|---|---|---|---|
| **Driver I²S Simplex (`INMP441` + `MAX98357A`) + scaling `>> 12` e volume quadratico** | `78/xiaozhi-esp32` (`no_audio_codec.cc`) | **Codice riutilizzabile** (MIT) | Evita bug classici di gain basso INMP441, clipping MAX98357A e conflitti di clock I²S | **Media** (adattamento da ESP-IDF puro ad Arduino/PlatformIO ESP32) | Conservare avviso licenza MIT in `THIRD_PARTY_LICENSES.md` | ✅ **Adottare** in FASE 6/7 dopo Test 1 |
| **`EnableInput` / `EnableOutput` I²S dinamico** | `78/xiaozhi-esp32` (`no_audio_codec.cc`) | **Idea / Pattern** (MIT) | Elimina eco speaker→mic durante `SPEAKING` e riduce carico DMA | **Bassa** | Nessuno | ✅ **Adottare** |
| **Callback `on_playback_drained` e coda audio separata** | `78/xiaozhi-esp32` (`audio_service.h`) | **Idea da reimplementare** | Sincronizzazione precisa tra fine riproduzione speaker e ritorno `SPEAKING` → `IDLE` | **Media** | Evitare dipendenza da `esp_opus` | ✅ **Reimplementare** con ring buffer PCM + frame `SPK_DONE` |
| **Modello animazione occhi OLED 128×64** | `Carmoruda/Jarvis` | **Già integrato** (MIT) | Già attivo e migliorato in `eye_engine.cpp` | — | Non duplicare | ➖ **Già coperto** |
| **Reattività occhi al livello audio (`SPEAKING`)** | `FamousWolf/deskbuddy` (concetto animazione) + `eye_bridge.py` | **Idea da reimplementare** | Rende gli occhi più espressivi (micro-pulsazione altezza/pupille sincronizzata alla voce Piper) | **Bassa** | Non importare codice ESPHome/LCD | ✅ **Reimplementare** su `EyeEngine` |
| **Parser seriale tollerante a log di boot** | `StefanRiese/blinky-desk-companion` (`protocol.h`) | **Solo concetto** (No licenza) | Evita errori di parsing quando l'ESP32 stampa log di sistema | **Bassa** | **Vietato copiare codice** (All Rights Reserved) | ✅ **Già coperto** dal framing binario `0xAA 0x55` |
| **Stack completo `xiaozhi-esp32` (Wi-Fi/Opus) + `xiaozhi-esp32-server`** | `78/xiaozhi-esp32` + `xinnan-tech/xiaozhi-esp32-server` | **Non adatto ora** (MIT) | Porterebbe firmware pronto per cloud/WeChat/ASR cinese | **Alta** | Sostituirebbe OLED, Piper Riccardo, Ollama e faster-whisper | ❌ **Scartare per v1 USB** (tenere solo come riferimento futuro RPi) |

---

## 4. Aggiornamento al Piano Tecnico FASE 6 (Miglioramenti da Applicare dopo l'Arrivo Hardware)

1. **Audio I²S (`no_audio_codec.cc` MIT):** nei Test 3 e 4 (`HARDWARE_TEST_PLAN.md`), usare **due controller I²S separati** (`I2S0` e `I2S1`) con slot a **32 bit mono Left**, scaling `>> 12` con clamp per `INMP441`, e curva di volume quadratica per `MAX98357A`, aggiungendo la relativa attribuzione MIT in `04-Firmware/jarvis-desk-buddy/THIRD_PARTY_LICENSES.md`.
2. **Anti-eco hardware/software:** disabilitare/scartare lo stream `INMP441` mentre l'ESP32-S3 è in `SPEAKING`, riattivandolo solo su `SPK_DONE` o `SPK_STOP`.
3. **Animazione OLED `SPEAKING` reattiva:** invece di duplicare motori grafici esterni, sfruttare l'RMS dei chunk PCM inviati dal PC (o calcolati sull'ESP32-S3) per modulare leggermente l'espressione `kSpeaking` di `EyeEngine` (già predisposto in `eye_bridge.py` con `on_audio_level`).
