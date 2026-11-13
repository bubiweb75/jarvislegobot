# JARVIS LEGO BOT – FASE 1: Relazione Tecnica e Validazione Hardware

**Data:** 13 novembre 2026  
**Stato:** FASE 1 completata (in attesa di approvazione per passare alla FASE 2)  
**Repository di riferimento:**
- Firmware: `https://github.com/78/xiaozhi-esp32`
- Backend: `https://github.com/xinnan-tech/xiaozhi-esp32-server`

---

## 1. Analisi dei Repository di Riferimento

### 1.1 Firmware: `78/xiaozhi-esp32`
Dall'ispezione del codice sorgente ufficiale:
- **Profilo scheda compatibile:** È presente la configurazione `main/boards/bread-compact-wifi/`, progettata per prototipi su breadboard/custom con ESP32-S3, microfono I2S, amplificatore I2S e display OLED I2C.
- **Supporto ESP32-S3 N16R8:** Il file `sdkconfig.defaults.esp32s3` abilita nativamente `CONFIG_SPIRAM=y`, `CONFIG_SPIRAM_MODE_OCT=y` e `CONFIG_SPIRAM_SPEED_80M=y` (Octal PSRAM a 80 MHz), configurazione richiesta dal modulo **N16R8** (16 MB Flash, 8 MB Octal PSRAM).
- **Supporto Display OLED 128x64:** `bread-compact-wifi/config.h` e `compact_wifi_board.cc` supportano via `Kconfig` tre varianti I2C (`0x3C`):
  - `CONFIG_OLED_SSD1306_128X32`
  - `CONFIG_OLED_SSD1306_128X64`
  - `CONFIG_OLED_SH1106_128X64` (attiva `esp_lcd_new_panel_sh1106`)
  - La classe `OledDisplay` (basata su LVGL) espone nativamente `SetupUI_128x64()`, `SetEmotion(const char* emotion)` e `SetChatMessage(...)`.
- **Supporto Audio I2S:** Supporta sia la modalità **Simplex** (`AUDIO_I2S_METHOD_SIMPLEX`, due bus I2S separati per microfono e amplificatore, default in `bread-compact-wifi`) sia Duplex.
- **Lingua Italiana:** In `main/assets/locales/` è presente la cartella `it-IT` per le stringhe di sistema dell'interfaccia.
- **Pulsanti fisici:** `compact_wifi_board.cc` gestisce nativamente `BOOT_BUTTON_GPIO` (click per attivare/fermare la conversazione o entrare in configurazione Wi-Fi all'avvio), `TOUCH_BUTTON_GPIO` (pressione continua *Push-to-Talk*), `VOLUME_UP_BUTTON_GPIO` e `VOLUME_DOWN_BUTTON_GPIO`.

### 1.2 Backend: `xinnan-tech/xiaozhi-esp32-server`
Dall'ispezione di `.github/workflows/docker-image.yml`, `Dockerfile-server` e `main/xiaozhi-server/config.yaml`:
- **Compatibilità ARM64 / Docker:** Il workflow CI ufficiale compila e pubblica immagini multi-architettura `linux/amd64,linux/arm64` su GHCR (`ghcr.io/xinnan-tech/xiaozhi-esp32-server:server_latest` e `web_latest`). **Compatibile nativamente con Raspberry Pi 5 ARM64 (Debian 13 Trixie)**.
- **Criticità lingua italiana (ASR):** Il modulo ASR locale di default (`FunASR` con `SenseVoiceSmall` e `SherpaASR`) dichiara il supporto solo per `zh, en, ja, ko, yue` — **non supporta l'italiano**.
  - Nel repository (`core/providers/asr/`) sono però già presenti provider compatibili con l'italiano: **`vosk.py`** (ASR locale offline, leggero su ARM64 con modello italiano es. `vosk-model-small-it-0.22`) e **`openai.py`** (Whisper API online o endpoint compatibile).
- **Sintesi Vocale (TTS) italiana:** In `core/providers/tts/` è presente **`edge.py`** (Microsoft Edge TTS, gratuito, con voci italiane neurali come `it-IT-DiegoNeural`), oltre a `openai.py`.
- **LLM ed Estensibilità:** In `core/providers/llm/` sono già supportati nativamente `gemini`, `openai`, `ollama` (utile per la futura integrazione su PC Windows 11) e `homeassistant`. Inoltre `config.yaml` supporta `mcp_endpoint` (Model Context Protocol via WebSocket) e `plugins` per collegare tool personalizzati.
- **Protocollo di comunicazione e MQTT:** Di default il firmware comunica col server tramite **WebSocket** (`ws://<IP>:8000/xiaozhi/v1/`). Il repo documenta un `xiaozhi-mqtt-gateway` (`docs/mqtt-gateway-integration.md`), ma quest'ultimo è un gateway audio/controllo specifico (MQTT + UDP porta 8884) per l'ESP32, **non** un broker MQTT generico per telemetria Raspberry/Docker.

---

## 2. Validazione Hardware e Compatibilità Componenti

| Componente | Stato | Note tecniche e criticità |
|---|---|---|
| **ESP32-S3 N16R8** | Validato | Verificare l'uso della **Octal PSRAM**: sui moduli N16R8 i pin **GPIO 35, 36, 37** sono riservati internamente alla PSRAM Octal e **non devono essere usati**. Evitare anche GPIO 19/20 (USB D-/D+), 43/44 (UART0) e strapping pin (GPIO 0/3/45/46) se non per funzioni previste (GPIO 0 è ok per BOOT/pulsante). |
| **Display OLED 1,3" 128x64** | Da verificare il controller | Quasi tutti gli OLED da **1,3"** montano il controller **SH1106** (e non SSD1306, tipico degli 0,96"). `xiaozhi-esp32` supporta entrambi, ma va selezionato il driver corretto in compilazione, altrimenti lo schermo resta nero o sfalsato di 2 pixel. **Attenzione al pinout:** alcuni moduli 1,3" hanno ordine `VCC-GND-SCL-SDA`, altri `GND-VCC-SCL-SDA`. Alimentare a **3,3 V**. |
| **Microfono INMP441** | Validato | Microfono MEMS I2S digitale. **Obbligatorio alimentarlo a 3,3 V** (non tollera 5 V). Collegare il pin `L/R` a `GND` per il canale sinistro (standard). Posizionarlo nella testa dietro un piccolo foro acustico, disaccoppiato dalle vibrazioni dello speaker. |
| **Amplificatore MAX98357A** | Validato | Amplificatore Classe D I2S mono. Per ottenere i 3 W su carico 4 Ω va alimentato sul pin **`VIN` a 5 V** (a 3,3 V eroga solo ~1,3 W). Aggiungere un **condensatore elettrolitico (220 µF – 470 µF, 10 V+)** tra 5 V e GND vicino al MAX98357A per assorbire i picchi di corrente ed evitare reset (brownout) dell'ESP32-S3. |
| **Altoparlante 4 Ω / 3 W** | Validato | Compatibile con MAX98357A a 5 V. Verificare le dimensioni fisiche (es. diametro 36–40 mm o ovale compatto) per l'alloggiamento nel corpo LEGO. |
| **Alimentazione USB 5 V** | Attenzione alla corrente | Un alimentatore USB da almeno **5 V / 2 A** (o porta USB-C dedicata con cavo dati+alimentazione adeguato) è necessario per gestire contemporaneamente Wi-Fi ESP32-S3 + picchi audio da 3 W. |
| **Pulsante fisico** | Validato | Usabile su `GPIO 0` (già mappato come `BOOT_BUTTON_GPIO` per avvio/stop conversazione) o su un GPIO dedicato (es. `GPIO 47` configurato come push-button o touch). |

### Mappatura GPIO preliminare (riferimento `bread-compact-wifi`, sicura su N16R8)
- **INMP441 (I2S Mic):** `WS` → GPIO 4 | `SCK` → GPIO 5 | `SD` → GPIO 6 | `L/R` → GND | `VDD` → 3,3 V
- **MAX98357A (I2S Amp):** `DIN` → GPIO 7 | `BCLK` → GPIO 15 | `LRC` → GPIO 16 | `SD_MODE` → 3,3 V (o GPIO controllo) | `VIN` → 5 V
- **OLED 1,3" (I2C):** `SDA` → GPIO 41 | `SCL` → GPIO 42 | `VCC` → 3,3 V
- **Pulsante attivazione:** GPIO 0 (o GPIO dedicato con pull-up interno)

---

## 3. Integrazione Raspberry Pi 5 e Architettura Proposta

In linea con l'infrastruttura esistente del Raspberry Pi 5 (`raspberry-server`: Debian 13 Trixie ARM64, 8 GB RAM, Docker, Portainer, Nginx Proxy Manager su rete `webapps`, AdGuard Home, backup notturno `/opt/docker/appdata/`):

1. **Isolamento totale:** Creare uno stack Docker dedicato (gestito via Portainer) senza toccare i servizi esistenti. Dati e configurazioni persistenti sotto `/opt/docker/appdata/jarvis/`.
2. **Modalità AI leggera su Raspberry Pi 5:**
   - **Opzione consigliata (ibrida/cloud per LLM, leggera su RPi):** `xiaozhi-esp32-server` con **LLM online** (es. Gemini / OpenAI via API key in `.env`), **TTS** con `EdgeTTS` (italiano gratuito) e **ASR** con `Vosk` (locale italiano offline) oppure `OpenAI Whisper` (online, qualità superiore per l'italiano). Consumo RAM stimato sul Pi: < 1–2 GB.
   - **Futura integrazione Ollama (PC Windows 11):** Già prevista nativamente in `config.yaml` (`OllamaLLM` puntando a `http://<IP_PC_WIN11>:11434`).
3. **Bridge MQTT e Telemetria Raspberry/Docker (non nativo in XiaoZhi):**
   - `xiaozhi-esp32-server` non interroga Docker né espone comandi di sistema via MQTT.
   - **Architettura consigliata:** Affiancare nello stesso stack un broker **Eclipse Mosquitto** (autenticato) + un **servizio Python bridge / MCP Server** isolato (con accesso in **sola lettura** a `/var/run/docker.sock` o alle metriche di sistema e al broker MQTT) che espone a `xiaozhi-esp32-server` (via `mcp_endpoint` WebSocket o plugin) i tool per:
     - Stato CPU/RAM/temperatura Raspberry Pi 5
     - Stato container Docker
     - Ora/rete domestica e pubblicazione/ricezione stati via MQTT.
4. **Sicurezza e Rete:**
   - Tutte le API key e credenziali MQTT esclusivamente in variabili d'ambiente (`.env` / Portainer Secrets), mai nei sorgenti.
   - Eventuale UI web di gestione (`xiaozhi-esp32-server-web`) collegata alla rete `webapps` dietro Nginx Proxy Manager (`jarvis.home.arpa`) senza esporre porte HTTP sull'host. La porta WebSocket (`8000`) per l'ESP32 resterà accessibile solo sulla LAN domestica.

---

## 4. Elementi Non Verificati (da confermare prima della FASE 2)

1. **Modello esatto della scheda ESP32-S3 N16R8:** Alcune devboard hanno doppia porta USB-C (una `UART` con chip CH340/CP2102 e una `USB` nativa), altre una sola; inoltre il LED RGB integrato può essere su `GPIO 48` o `GPIO 38`.
2. **Controller e pinout reale del display OLED 1,3":** È necessario verificare sul retro del modulo acquistato se il controller è **SH1106** o **SSD1306** e l'ordine esatto dei pin (`VCC/GND` invertiti su alcuni lotti).
3. **Dimensioni fisiche effettive dell'altoparlante 4 Ω / 3 W:** Necessarie in FASE 3 per dimensionare l'alloggiamento LEGO (idealmente 36 mm o 40 mm di diametro).
4. **Stato attuale delle porte e risorse sul Raspberry Pi 5:** Non avendo accesso diretto al Raspberry in questa fase, in FASE 5 andranno verificate eventuali porte occupate (es. `1883`, `8000`, `8003`) e la RAM libera disponibile.
5. **Livello sonoro del microfono con EdgeTTS/Vosk in italiano:** La qualità di riconoscimento vocale di `vosk-model-small-it-0.22` rispetto a `Whisper API` andrà testata sul campo in FASE 5.

---

## 5. Raccomandazioni e Distinta Preliminare (Prototipo FASE 1/2)

### Raccomandazioni chiave
- **Non riscrivere il firmware:** Partire dalla board `bread-compact-wifi` di `78/xiaozhi-esp32` creando una variante dedicata `jarvis-lego-s3` (in FASE 4) con pinout bloccato e logo/espressioni personalizzate (FASE 6).
- **Attivazione vocale tramite pulsante:** In italiano `WakeNet` (wake-word offline di Espressif) non ha modelli italiani ufficiali gratuiti pronti; il pulsante fisico di attivazione garantisce affidabilità al 100% e zero falsi positivi.
- **Separazione alimentazione:** Inserire almeno un condensatore di livellamento (220–470 µF) sui 5 V del MAX98357A e tenere i cavi audio I2S corti e lontani dall'antenna Wi-Fi dell'ESP32-S3.

### Distinta Preliminare Componenti Elettronici (BOM)
- 1× **ESP32-S3-DevKitC-1 N16R8** (16 MB Flash, 8 MB Octal PSRAM)
- 1× **Display OLED 1,3" I2C 128x64** (preferibilmente bianco o azzurro/ciano, in linea con la palette JARVIS; verificare se SH1106 o SSD1306)
- 1× **Modulo Microfono I2S INMP441**
- 1× **Modulo Amplificatore I2S MAX98357A**
- 1× **Altoparlante 4 Ω / 3 W** (diametro compatto 36–40 mm per corpo LEGO)
- 1× **Pulsante tattile / momentaneo** (per attivazione conversazione)
- 1× **Condensatore elettrolitico 220 µF – 470 µF (10 V o 16 V)** (disaccoppiamento alimentazione audio)
- 1× **Breadboard + cavetti DuPont M-M / M-F** (per test su banco prima dell'assemblaggio definitivo nel telaio LEGO)
- 1× **Alimentatore USB 5 V ≥ 2 A** + cavo USB-C dati/alimentazione
