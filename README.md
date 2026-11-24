# JARVIS LEGO BOT

Assistente vocale da scrivania in italiano costruito con mattoncini LEGO, basato su **ESP32-S3-DevKitC-1 N16R8**, riconoscimento wake word locale continuo **«Hey Jarvis»**, animazioni **Eyes 3.0** su OLED I²C e pipeline AI locale su PC Windows 11 (**faster-whisper** + **Ollama `qwen2.5:3b`** + **Piper Riccardo Profilo 08**) via **Voice Bridge** (`WSS` TLS).

---

## Stato del Progetto (FASE 13.8)

| Categoria | Stato | Dettagli |
|---|---|---|
| **Firmware stabile (`FASE 13.8`)** | ✅ Implementato e collaudato | [jarvis_wifi_voice_client](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/README.md): wake word locale continuo «Hey Jarvis», `Eyes 3.0`, VAD adattivo, anti-ri-trigger, speaker silenzioso in `IDLE`, `GPIO47`, diagnostica `STAT`, Wi-Fi/WSS. |
| **Voice Bridge & AI locale** | ✅ Implementato e collaudato | `05-Voice-AI/`: server FastAPI/WSS (`faster-whisper small` + `Ollama qwen2.5:3b` + `Piper it_IT-riccardo-x_low` WSOLA Profilo 08 + Control Center). |
| **Meccanica LEGO (`Companion Hybrid v2`)** | ✅ Progettata / in costruzione | `03-Mechanical-Design/`: modelli `.mpd`/`.ldr` e istruzioni di montaggio. |
| **Prototipi & Simulazioni** | 🧪 Sperimentali | `04-Firmware/experiments/` (storici/sperimentali FASE 13.1–13.7), `04-Firmware/wokwi-*`, `04-Firmware/arduino-hw-test/*_hw_test/`. |
| **PCB Carrier Board v1 & Sensori futuri** | 📋 Progettazione / da collaudare | `JARVIS_CARRIER_BOARD_V1_PRODUZIONE/` (Gerber/BOM di progetto non ancora fabbricati/collaudati), sensori `VL53L0X`/`MPU6050`/`BH1750`/`TTP223`, Base Mobile B2 (`03-Mechanical-Design/05-Mobile-Electronics/`). |
| **JARVIS Robotics Platform** | 📋 Evoluzione futura | `JARVIS-Robotics-Platform/`: architettura, contratti, profili e frontend in evoluzione (non ancora integrata sul robot). |

### Limiti tecnici attuali
- La partizione applicativa `app0` su ESP32-S3 (`1.310.720` B) è occupata al **99%** (`1.299.328` B, margine residuo `11.392` B); future espansioni richiederanno una tabella partizioni `Huge APP` (`3 MB` su Flash `16 MB`).
- I servizi STT, LLM e TTS girano localmente su PC Windows 11 collegato sulla stessa LAN dell'ESP32-S3.

---

## Architettura Hardware e Software

```text
[INMP441 I2S0] ──► Core 0 (AudioCapture: microWakeWord "Hey Jarvis" + Pre-Roll 500ms + VAD)
                        │
                        ▼ (WSS TLS /ws/v1/esp32)
              [PC Windows 11: Voice Bridge]
               ├── STT: faster-whisper (small)
               ├── AI : Local Intent / Ollama (qwen2.5:3b)
               └── TTS: Piper Riccardo (WSOLA Profilo 08)
                        │
                        ▼ (PCM16 16kHz → PSRAM)
[MAX98357A I2S1] ◄── Core 0 (AudioPlayback + zero-flush silenzioso in IDLE)
[OLED SH1106 I2C] ◄── Core 1 (Eyes 3.0: IDLE / LISTENING / THINKING / SPEAKING)
[Pulsante GPIO47] ──► Core 1 (Push-to-Talk alternativo + STOP/CANCEL)
```

### Componenti elettronici attivi (`ESP32-S3-DevKitC-1 N16R8`)
- **MCU**: ESP32-S3 N16R8 (`16 MB` Flash, `8 MB` Octal PSRAM)
- **Display**: OLED 1,3" `128×64` I²C (`SH1106`, `SDA=GPIO41`, `SCL=GPIO42`)
- **Microfono**: `INMP441` I²S (`I2S_NUM_0`: `WS=GPIO4`, `SCK=GPIO5`, `SD=GPIO6`, `L/R=GND`)
- **Amplificatore & Speaker**: `MAX98357A` (`I2S_NUM_1`: `BCLK=GPIO15`, `LRC=GPIO16`, `DIN=GPIO7`) + Speaker `4 Ω / 3 W`
- **Pulsante**: tattile su `GPIO47` (attivo LOW verso GND)

---

## Struttura del Repository

- `03-Mechanical-Design/` — Progettazione meccanica LEGO (`Companion Hybrid v2`), istruzioni e studi elettrici Base Mobile B2.
- `04-Firmware/`
  - `arduino-hw-test/jarvis_wifi_voice_client/` — **Firmware stabile FASE 13.8** (con `tests/test_fase13_4_logic.py`).
  - `archive/fase12_27_jarvis_wifi_voice_client/` — Archivio integrale della precedente versione stabile FASE 12.27.
  - `experiments/` — Prototipi isolati FASE 13 (`fase13-wakeword`, `fase13_3-integrated`).
  - `jarvis-desk-buddy/` & `jarvis-desk-buddy-sim/` — Firmware OLED/USB storico e simulatore Python `Eyes 2.0/3.0`.
  - `wokwi-*` — Configurazioni di simulazione Wokwi.
- `05-Voice-AI/` — **Voice Bridge**, pipeline Whisper/Ollama/Piper, Control Center e test automatici (`backups/` locali esclusi da Git).
- `06-Hardware-Integration/` — Pinout definitivo, schemi SVG, guida al montaggio e specifiche sensori FASE 8.
- `JARVIS_CARRIER_BOARD_V1_PRODUZIONE/` — File Gerber, BOM e documentazione PCB Carrier Board v1 (progettazione non ancora prodotta).
- `JARVIS-Robotics-Platform/` — Documentazione, contratti, profili e frontend per l'evoluzione futura della piattaforma.
- `docs/` — Manuali PDF illustrati (`docs/manuals/`) e report tecnici di fase (`FASE_1` → `FASE_14`).
- `archive/` — Elaborati storici archiviati.

---

## Compilazione Firmware Stabile (`FASE 13.8`)

1. Copiare `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/wifi_secrets.example.h` in `wifi_secrets.h` (escluso da Git) e configurare SSID, password, IP/porta LAN del Voice Bridge e token dispositivo.
2. Dipendenze: core `esp32:esp32` `3.3.13`, `U8g2` (`2.36.19`), `WebSockets` (`2.7.2`), `Chirale_TensorFLowLite-2.0.0` (in `04-Firmware/experiments/fase13-wakeword/libs`).
3. Compilazione con `arduino-cli`:
```powershell
arduino-cli compile --fqbn "esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M,DebugLevel=none" `
  --libraries "04-Firmware\experiments\fase13-wakeword\libs" `
  --libraries "$env:USERPROFILE\Documents\Arduino\libraries" `
  "04-Firmware\arduino-hw-test\jarvis_wifi_voice_client"
```
4. Test logici host:
```powershell
python 04-Firmware\arduino-hw-test\jarvis_wifi_voice_client\tests\test_fase13_4_logic.py
```

---

## Manuali PDF e Documentazione Tecnica

- **Manuali A4 illustrati (`docs/manuals/`)**: [01 Presentazione](docs/manuals/01_Presentazione_Generale_JARVIS.pdf) · [02 Elettronica](docs/manuals/02_Elettronica_e_Collegamenti.pdf) · [03 LEGO](docs/manuals/03_Costruzione_LEGO_Companion_v2.pdf) · [04 Software](docs/manuals/04_Software_e_Utilizzo_Windows.pdf) · [05 Collaudo](docs/manuals/05_Collaudo_e_Manutenzione.pdf) · [06 Personalità](docs/manuals/06_Personalita_Emozioni_e_Reazioni.pdf).
- **Documenti chiave recenti**:
  - [FASE 13.8 — Versione Stabile](docs/FASE_13_8_VERSIONE_STABILE.md)
  - [FASE 13.7 — Collaudo Consolidamento](docs/FASE_13_7_COLLAUDO_CONSOLIDAMENTO.md)
  - [FASE 14.1 — Audit Repository](docs/FASE_14_1_AUDIT_REPOSITORY.md)

---

## Licenze e Attribuzioni

Vedere [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) per l'elenco completo delle librerie e dei modelli di terze parti (`microWakeWord` / `hey_jarvis` Apache-2.0, `TFLite Micro` Apache-2.0, `arduinoWebSockets` LGPL-2.1, `U8g2` BSD-2-Clause, `faster-whisper` MIT, `Piper` MIT, `Ollama` MIT/Apache-2.0).

---

## Roadmap Futura
1. Eventuale migrazione tabella partizioni `Huge APP` (`3 MB`) su Flash `16 MB` per superare il limite attuale del `99%` di `app0`.
2. Produzione e collaudo fisico della Carrier Board PCB v1 e integrazione sensori (`VL53L0X`, `MPU6050`, `BH1750`, `TTP223`).
3. Evoluzione modulare verso `JARVIS-Robotics-Platform` e Base Mobile B2.
