# JARVIS LEGO BOT – FASE 1 (Integrazione): Decisioni Definitive e Architettura

**Data:** 13 novembre 2026  
**Stato:** Revisione FASE 1 completata (in attesa di approvazione per iniziare la FASE 2)  
**Riferimento precedente:** [FASE_1_Analisi_Tecnica.md](FASE_1_Analisi_Tecnica.md)

---

## 1. Decisioni Definitive sui Punti Revisionati

1. **Microcontrollore confermato:** **ESP32-S3-DevKitC-1 N16R8** (16 MB Flash, 8 MB Octal PSRAM).
   - Configurazione obbligatoria in firmware: `CONFIG_SPIRAM_MODE_OCT=y` (OPI PSRAM).
   - **Gestione revisioni v1.0 vs v1.1:** Sulla `v1.0` il LED RGB integrato (NeoPixel) è su **`GPIO 48`**, mentre sulla `v1.1` è su **`GPIO 38`**. Il pin esatto andrà verificato fisicamente sulla scheda prima della compilazione finale in FASE 4; entrambi i pin vanno comunque esclusi dal cablaggio delle periferiche esterne.
   - **GPIO vietati / riservati:**
     - `GPIO 35, 36, 37`: riservati internamente alla Octal PSRAM (R8) — **non usare**.
     - `GPIO 19, 20`: USB D- / D+ nativo.
     - `GPIO 43, 44`: UART0 TX/RX (console seriale).
     - `GPIO 0, 3, 45, 46`: Strapping pins (non usare per periferiche esterne).
2. **Pulsante fisico di attivazione su GPIO dedicato (NO GPIO 0):**
   - `GPIO 0` è uno strapping pin di boot: un cavo lungo o una pressione accidentale all'accensione bloccherebbe l'ESP32-S3 in *Download Mode*.
   - **Decisione:** `GPIO 0` resta riservato al tasto `BOOT` integrato sulla scheda. Il pulsante fisico esterno di JARVIS verrà collegato a **`GPIO 47`** (già mappato come `TOUCH_BUTTON_GPIO` nel profilo `bread-compact-wifi`, non strapping pin), configurato con pull-up interno (`INPUT_PULLUP`) e chiusura verso `GND`.
3. **Display OLED 1,3" 128x64:**
   - **Decisione:** Adottare un modulo **OLED 1,3" I2C 128x64 a 4 pin con controller SH1106** (indirizzo `0x3C`, supportato nativamente in `78/xiaozhi-esp32` tramite `CONFIG_OLED_SH1106_128X64`), oppure un equivalente **1,3" SSD1306/SSD1315** (`CONFIG_OLED_SSD1306_128X64`).
   - **Verifica fisica obbligatoria pre-cablaggio:** Nei moduli 1,3" SH1106 esistono due disposizioni fisiche dei pin (`GND-VCC-SCL-SDA` e `VCC-GND-SCL-SDA`). Alimentazione a **3,3 V** (anche se il modulo ha regolatore LDO per 5 V, i segnali I2C verso ESP32-S3 devono lavorare a 3,3 V).
4. **Backend Raspberry Pi 5 (Debian 13 ARM64):**
   - **Distinzione dei deployment in `xinnan-tech/xiaozhi-esp32-server`:**
     - `docker-compose.yml` (**Server-Only**): avvia il solo servizio Python `xiaozhi-esp32-server` (`ghcr.io/xinnan-tech/xiaozhi-esp32-server:server_latest`, immagine multi-arch `linux/arm64`), con configurazione via file `data/.config.yaml`, porte `8000` (WebSocket) e `8003` (HTTP/OTA), nessun database esterno.
     - `docker-compose_all.yml` (**Full Deployment**): aggiunge `xiaozhi-esp32-server-web` (Java Manager UI su `8002`), `mysql:latest` e `redis:8.0`.
   - **Decisione per v1:** Adottare il modello **Server-Only** (`server_latest` ARM64) in uno stack Portainer dedicato e isolato, con persistenza in `/opt/docker/appdata/jarvis/` (incluso nel backup notturno), senza MySQL/Redis e senza modificare alcun servizio o porta esistente sul Raspberry Pi 5.
5. **Riconoscimento vocale italiano (ASR):**
   - **Verifica nel codice:** `core/providers/asr/vosk.py` e `vosk==0.3.45` (`requirements.txt`) sono realmente presenti nel backend `xiaozhi-esp32-server`.
   - **Modello italiano:** `vosk-model-small-it-0.22` (48 MB compressi, ~87 MB estratti, 16 kHz, offline). WER dichiarato da Alpha Cephei: 16,88% (Common Voice), 17,01% (mTEDx), 25,87% (MLS).
   - **Confronto alternative nel repo:**
     - `vosk.py` (`vosk-model-small-it-0.22`): gratuito, 100% locale su Raspberry Pi 5, ottima reattività su comandi brevi, minore precisione su frasi complesse/rumore.
     - `openai.py` (Whisper API / endpoint compatibile): massima accuratezza in italiano e punteggiatura, richiede API key e connessione Internet.
     - `fun_local.py` (SenseVoiceSmall) e `sherpa_onnx_local.py`: **non supportano l'italiano** (scartati).
   - **Decisione:** Usare **`Vosk` (`vosk-model-small-it-0.22`)** come baseline locale offline, mantenendo **`OpenAI Whisper` (`openai.py`)** come opzione attivabile da `config.yaml` qualora la qualità di Vosk sul campo non risultasse sufficiente. TTS con **`EdgeTTS` (`edge.py`, voce italiana)** e LLM online (con futura estensione **`OllamaLLM`** su PC Windows 11).
6. **Sicurezza accesso Docker (NO mount diretto `docker.sock:ro`):**
   - Il mount `/var/run/docker.sock:ro` **non impedisce operazioni di scrittura**: il demone Docker accetta comunque richieste HTTP `POST`/`DELETE` sul socket, consentendo potenzialmente l'escalation a `root` sull'host.
   - **Decisione:** Introdurre un **`docker-socket-proxy`** (es. `tecnativa/docker-socket-proxy`) su rete interna isolata (`jarvis_internal`), configurato per bloccare qualsiasi metodo di scrittura (`POST=0`, `EXEC=0`, `IMAGES=0`, `VOLUMES=0`) e consentire esclusivamente `GET` in sola lettura su `CONTAINERS=1` e `INFO=1`. Il microservizio bridge Python (`jarvis-sys-bridge`) interrogherà solo il proxy HTTP interno, senza mai vedere il socket Docker.
7. **Semplificazione v1 (Rimozione MQTT):**
   - Nella prima versione **non verrà installato né usato MQTT** (né `xiaozhi-mqtt-gateway` né Mosquitto). L'ESP32-S3 comunicherà direttamente via **WebSocket** (`ws://<IP_RASPBERRY>:8000/xiaozhi/v1/`) con `xiaozhi-esp32-server`, e i dati Raspberry/Docker passeranno tramite **MCP Endpoint** al bridge sicuro. MQTT resta opzionale per versioni future multi-dispositivo/robotica mobile.

---

## 2. Componenti Hardware Esatti (v1)

| # | Componente | Specifica esatta | Note |
|---|---|---|---|
| 1 | **MCU Board** | **ESP32-S3-DevKitC-1 N16R8** | 16 MB Flash, 8 MB Octal PSRAM (verificare se v1.0 o v1.1 per GPIO LED RGB). |
| 2 | **Display** | **OLED 1,3" 128x64 I2C (SH1106 o SSD1306)** | 4 pin I2C (`0x3C`), alimentazione logica/VCC 3,3 V, colore bianco o azzurro/ciano. |
| 3 | **Microfono** | **INMP441** (modulo breakout I2S) | Digitale I2S MEMS, **solo 3,3 V**, pin `L/R` a `GND`. |
| 4 | **Amplificatore** | **MAX98357A** (modulo breakout I2S) | Classe D mono, `VIN` a **5 V** per erogare fino a 3 W su 4 Ω. |
| 5 | **Altoparlante** | **Speaker 4 Ω / 3 W** | Diametro compatto **36 mm o 40 mm** (spessore ≤ 20 mm per alloggiamento LEGO). |
| 6 | **Pulsante** | **Pulsante tattile / momentaneo NO** | 2 pin (o 4 pin a coppie), chiusura verso `GND`, montabile su pannello/LEGO. |
| 7 | **Disaccoppiamento** | **Condensatore elettrolitico 220 µF – 470 µF (≥ 10 V)** | Da porre tra `5 V` e `GND` vicino al MAX98357A contro i cali di tensione (brownout). |
| 8 | **Alimentazione** | **Alimentatore USB 5 V / ≥ 2 A** + cavo USB-C dati | Per prototipo da scrivania. |

---

## 3. Pinout Aggiornato (ESP32-S3-DevKitC-1 N16R8)

Mappatura pulita, priva di conflitti con Octal PSRAM (`GPIO 35–37`), USB nativo (`19–20`), UART0 (`43–44`) e strapping pins (`0, 3, 45, 46`):

| Periferica | Pin Modulo | Segnale | GPIO ESP32-S3 | Note |
|---|---|---|---|---|
| **INMP441 (Mic I2S)** | `VDD` | Alimentazione | `3V3` | **Mai collegare a 5 V** |
| | `GND` | Massa | `GND` | |
| | `L/R` | Selezione canale | `GND` | Canale Left |
| | `WS` | Word Select | `GPIO 4` | |
| | `SCK` | Bit Clock | `GPIO 5` | |
| | `SD` | Data Out → ESP In | `GPIO 6` | |
| **MAX98357A (Amp I2S)** | `VIN` | Alimentazione | `5V` | Con condensatore 220–470 µF verso GND |
| | `GND` | Massa | `GND` | |
| | `SD` | Shutdown/Mode | `3V3` | Abilitato fisso (oppure GPIO dedicato in seguito) |
| | `GAIN` | Guadagno | Non connesso | Default 9 dB (regolabile se necessario) |
| | `DIN` | Data In ← ESP Out | `GPIO 7` | |
| | `BCLK` | Bit Clock | `GPIO 15` | |
| | `LRC` | Left/Right Clock | `GPIO 16` | |
| **OLED 1,3" (I2C)** | `VCC` | Alimentazione | `3V3` | Verificare ordine pin sul PCB! |
| | `GND` | Massa | `GND` | |
| | `SDA` | I2C Data | `GPIO 41` | |
| | `SCL` | I2C Clock | `GPIO 42` | |
| **Pulsante JARVIS** | Pin A | Segnale | `GPIO 47` | Pull-up interno abilitato (NO strapping pin) |
| | Pin B | Massa | `GND` | |
| **Riservato Onboard** | `BOOT` | Boot / Wi-Fi Config | `GPIO 0` | Solo tasto onboard |
| **Riservato Onboard** | `RGB LED` | NeoPixel | `GPIO 48` (v1.0) / `GPIO 38` (v1.1) | Non collegare periferiche su entrambi in fase di test |

---

## 4. Architettura Software Concreta (v1)

```text
[ ESP32-S3 N16R8 (xiaozhi-esp32) ]
        │
        │  WebSocket (LAN: ws://<LAN_IP>:8000/xiaozhi/v1/)
        ▼
┌────────────────────────────────────────────────────────────────────┐
│ Raspberry Pi 5 (Debian 13 ARM64) – Stack Portainer "jarvis"       │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ xiaozhi-esp32-server (server_latest - linux/arm64)           │  │
│  │  - ASR: Vosk (vosk-model-small-it-0.22) / opz. Whisper API   │  │
│  │  - TTS: EdgeTTS (voce italiana it-IT)                        │  │
│  │  - LLM: API Cloud (.env) -> futuro Ollama su PC Win11        │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
│                             │ MCP WebSocket (rete jarvis_internal) │
│  ┌──────────────────────────▼───────────────────────────────────┐  │
│  │ jarvis-sys-bridge (Python, container non privilegiato)       │  │
│  │  - Espone solo tool read-only (ora, stato RPi, container, IP)│  │
│  └──────────────────────────┬───────────────────────────────────┘  │
│                             │ HTTP GET (solo /containers/json,/info)│
│  ┌──────────────────────────▼───────────────────────────────────┐  │
│  │ docker-socket-proxy (POST=0, EXEC=0, CONTAINERS=1, INFO=1)   │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
└─────────────────────────────┼──────────────────────────────────────┘
                              │ /var/run/docker.sock (isolato nel proxy)
```

- **Persistenza dati:** `/opt/docker/appdata/jarvis/config/` (file `.env`, `config.yaml`) e `/opt/docker/appdata/jarvis/models/` (modello Vosk italiano).
- **Nessuna interferenza:** Stack completamente separato dalla rete `webapps` (o collegabile in seguito solo se si vorrà esporre una dashboard locale su `jarvis.home.arpa` tramite Nginx Proxy Manager).

---

## 5. Criticità Ancora Aperte (da verificare fisicamente)

1. **Revisione hardware effettiva dell'ESP32-S3-DevKitC-1 N16R8** (v1.0 con LED su GPIO 48 vs v1.1 con LED su GPIO 38).
2. **Controller e ordine pin del display OLED 1,3"** che verrà acquistato (SH1106 vs SSD1306; ordine `GND-VCC` vs `VCC-GND`).
3. **Dimensioni fisiche reali dell'altoparlante 4 Ω / 3 W** (necessarie in FASE 3 per progettare il vano acustico LEGO).
4. **Accuratezza pratica di `vosk-model-small-it-0.22` in ambiente domestico:** da valutare in FASE 5 rispetto all'eventuale fallback su OpenAI Whisper API.
5. **Verifica porte libere sul Raspberry Pi 5** (`8000` e `8003`) prima del deploy dello stack in FASE 5.

---

## 6. Distinta Preliminare Aggiornata (v1)

- 1× **ESP32-S3-DevKitC-1 N16R8** (con header saldati)
- 1× **Display OLED 1,3" I2C 128x64** (preferibilmente **SH1106**, 4 pin, colore bianco o azzurro/ciano)
- 1× **Modulo Microfono I2S INMP441**
- 1× **Modulo Amplificatore I2S MAX98357A**
- 1× **Altoparlante 4 Ω / 3 W** (compatto, Ø 36–40 mm)
- 1× **Pulsante momentaneo (Normalmente Aperto)**
- 1× **Condensatore elettrolitico 220 µF – 470 µF (10 V o 16 V)**
- 1× **Breadboard 830 punti** + **kit cavetti DuPont M-M / M-F** (per test su banco)
- 1× **Alimentatore USB 5 V ≥ 2 A** + **cavo USB-C dati/alimentazione**
