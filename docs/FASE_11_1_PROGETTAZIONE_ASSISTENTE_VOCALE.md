# FASE 11.1 — Progettazione dell'Assistente Vocale Intelligente (ESP32-S3 ↔ Raspberry Pi 5 ↔ AI)

> **Stato documento**: Solo analisi e progettazione architetturale. Nessuna modifica a firmware stabili, container o server è stata eseguita in questa fase.

---

## 1. Analisi del Sistema Attuale e Componenti Riutilizzabili

### 1.1 Firmware ESP32-S3 (`04-Firmware/arduino-hw-test/jarvis_duplex_rtos_hw_test/` — FASE 10.8)
Componenti già sviluppati e riutilizzabili nella futura evoluzione:
- **`AudioCapture`** (`jarvis_audio_rx`, FreeRTOS Core `0`, Priorità `3`): acquisizione `I2S_NUM_0` da **INMP441** (`GPIO4/5/6`, `16 kHz`, PCM16 mono con rimozione DC).
- **`AudioPlayback`** (`jarvis_audio_tx`, FreeRTOS Core `0`, Priorità `3`): riproduzione `I2S_NUM_1` su **MAX98357A** (`GPIO15/16/7`, `16 kHz`, PCM16 stereo L=R, fade `20 ms`, volume `3–15%`).
- **`AudioBuffer`** (PSRAM `160.000` byte = `5 s` @ `16 kHz` mono PCM16): riutilizzabile direttamente per la registrazione Push-to-Talk dell'utente.
- **`EyeController`**: wrapper **Eyes 3.0** su OLED SH1106 (`0x3C`, `GPIO41/42`) con stati `IDLE` (`NEUTRAL`), `LISTENING`, `PROCESSING`/`THINKING`, `PLAYING`/`SPEAKING`, `ERROR` (`CONFUSED`).
- **`ButtonController`** (`GPIO47`, `INPUT_PULLUP`, debounce `40 ms`).

### 1.2 Backend Python Esistente (`05-Voice-AI/`)
Il repository dispone già di moduli Python riutilizzabili come base logica sul Raspberry Pi 5:
- `ai_providers.py` (supporto `demo`, `ollama`, `openai`)
- `stt_providers.py` (`faster-whisper`)
- `tts_providers.py` (`Piper`)
- `conversation_engine.py`, `conversation_naturalizer.py`, `memory_engine.py`, `config.py`

---

## 2. Architettura Proposta (Solo LAN, Zero Dipendenza Home Assistant)

```text
[ESP32-S3 N16R8] <-- WebSocket LAN (ws://raspi:8765/ws/voice) --> [Raspberry Pi 5 - Docker: jarvis-voice-bridge]
  - INMP441 (I2S0 RX)                                                   |-- STT: faster-whisper (Pi 5 tiny/base o PC)
  - MAX98357A (I2S1 TX)                                                 |-- AI Router: Ollama (PC Win11) -> Fallback
  - SH1106 Eyes 3.0                                                     |-- TTS: Piper it_IT (16 kHz PCM16 mono)
  - GPIO47 Push-to-Talk                                                 +-- Memory / Log (Appdata persistente)
```

- **Server domestico (Raspberry Pi 5, 8 GB, Debian 13 arm64, Docker/Portainer)**:
  - Un nuovo container isolato `jarvis-voice-bridge` (Python **FastAPI + Uvicorn**), configurato tramite `.env` e volume `/opt/docker/appdata/jarvis-voice-bridge/`.
  - Nessuna modifica ai container esistenti né a Home Assistant.

---

## 3. Valutazione STT e TTS Realistici

### 3.1 Speech-to-Text (STT Italiano)
| Opzione | Dove gira | Pro | Contro / Limiti |
|---|---|---|---|
| **`faster-whisper` (`tiny` / `base`, `int8`)** | Raspberry Pi 5 (CPU arm64) | Sempre disponibile (anche a PC spento), 100% offline, gratuito | `tiny` meno preciso su frasi lunghe; `base` richiede ~1–2,5 s per 3–5 s di audio |
| **`faster-whisper` (`small`)** | PC Windows 11 (Ryzen 7 5700U) | Alta accuratezza in italiano | Non disponibile quando il PC è spento |
| **API STT Cloud (opzionale)** | Esterno | Bassa latenza | Richiede Internet e API key a pagamento/quota |

**Strategia consigliata**: STT primario **`faster-whisper` (`base` `int8`) locale sul Raspberry Pi 5** (garantisce funzionamento autonomo h24 senza PC), con opzione futura di offload sul PC se acceso.

### 3.2 Text-to-Speech (TTS Italiano)
- **Piper TTS** locale su Raspberry Pi 5:
  - Modello leggero nativo `16 kHz`: `it_IT-riccardo-x_low.onnx` (già testato nel repo, nessuna conversione di sample rate necessaria, uscita diretta PCM16 mono `16.000 Hz`).
  - Modello qualità media: `it_IT-paola-medium.onnx` (`22.050 Hz` → richiede ricampionamento `22050 → 16000 Hz` lato Raspberry Pi prima dell'invio all'ESP32).
  - Latenza su Pi 5: ~`0,2–0,6 s` per frasi brevi, 100% offline e open source.

---

## 4. Protocollo ESP32 ↔ Raspberry Pi (Motivazione Scelta)

### Confronto HTTP vs WebSocket
- **HTTP (`POST /v1/voice-turn`)**: semplice, ma richiede nuovo handshake TCP per ogni turno, rende difficile aggiornare gli stati `THINKING`/`SPEAKING` in tempo reale, non permette facilmente la cancellazione immediata (`STOP`) e complica lo streaming audio per risposte `> 5 s`.
- **WebSocket LAN (`ws://<RASPI_IP>:8765/ws/voice`)** *(Scelta consigliata)*:
  - Connessione persistente a bassa latenza con frame **testo JSON** (controllo/stato) e frame **binari** (audio PCM16 mono `16 kHz` grezzo).
  - Permette cancellazione istantanea (`CANCEL`), eventi sincronizzati per `EyeController` e streaming continuo della risposta TTS verso l'ESP32.
  - Affiancato da `GET /health` HTTP per monitoraggio/Portainer.

### Flusso completo di una richiesta vocale
1. `IDLE` (`NEUTRAL`): connessione WebSocket attiva (heartbeat ping/pong ogni `15 s`).
2. Pressione `GPIO47` → `LISTENING` (`LISTENING`): `AudioCapture` registra in `AudioBuffer` (max `5 s`).
3. Rilascio `GPIO47` → `UPLOADING` / `THINKING` (`THINKING`): l'ESP32 invia JSON `{"type":"audio_start","sr":16000,"ch":1,"bits":16}`, poi i chunk binari PCM16 da `2.048 B` (`64 ms`), poi `{"type":"audio_end","samples":N}`.
4. Raspberry Pi: esegue **STT** → **AI Router** → **TTS Piper** (`16 kHz`, PCM16 mono).
5. Raspberry Pi invia `{"type":"tts_start","sr":16000,"total_bytes":M}` seguito da chunk binari PCM16 da `2.048 B` e `{"type":"tts_end"}`.
6. ESP32 entra in `SPEAKING` (`SPEAKING`) dopo pre-buffering iniziale (`~320 ms`) e riproduce tramite `AudioPlayback` (FreeRTOS TX).
7. Al termine di `tts_end` e svuotamento del ring buffer → `IDLE` (`NEUTRAL`).

---

## 5. Gestione Risposte Audio Lunghe (> 5 s / > 160 KB)

Il buffer lineare attuale (`160.000` byte = `5 s`) non può contenere risposte TTS da `10–25 s`.
*(Nota: lo streaming non è ancora implementato né verificato.)*
- **Soluzione progettata per la FASE 11.4**:
  - Sostituire/affiancare in riproduzione un **Ring Buffer circolare in PSRAM** da **`128 KB`** (`4 s` @ `16 kHz` PCM16 mono) con puntatori `write_idx` / `read_idx` protetti da `portMUX_TYPE` / FreeRTOS.
  - **Pre-buffering**: avviare `I2S_NUM_1` TX solo dopo aver accumulato `~12–16 KB` (`375–500 ms`) per assorbire jitter Wi-Fi.
  - **Flow control**: invio lato Pi 5 a chunk da `2.048 B` (`64 ms`) con leggero pacing o `ACK` applicativo per evitare overflow del ring buffer PSRAM.

---

## 6. Configurazione AI e Fallback (PC Spento)

Configurazione tramite `.env` / `config.json` montato sul Raspberry Pi (nessun LLM pesante sul Pi 5):
1. **Primary (`JARVIS_AI_PRIMARY=ollama`)**: `http://<PC_LAN_IP>:11434`, probe rapido (`connect_timeout = 1,5 s`), generazione (`read_timeout = 20 s`).
2. **Fallback automatico se PC spento/irraggiungibile**:
   - Se configurato (`JARVIS_AI_FALLBACK=cloud` + API key in `.env`): instrada su API esterna (es. Gemini / OpenAI-compatible).
   - Altrimenti (`JARVIS_AI_FALLBACK=offline`): risposta locale predefinita cortese generata da Piper (*"Il mio motore AI sul PC è spento al momento, posso rispondere solo in modalità base."*).

---

## 7. Macchina a Stati Completa ESP32-S3

- `BOOT_CONNECTING` → `IDLE` (`NEUTRAL`)
- `IDLE` → `LISTENING` (`LISTENING`, su pressione `GPIO47`)
- `LISTENING` → `THINKING` (`THINKING`, su rilascio `GPIO47` o timeout `5 s`; se `< 300 ms` torna a `IDLE`)
- `THINKING` → `SPEAKING` (`SPEAKING`, su `tts_start` + pre-buffer pronto)
- `SPEAKING` → `IDLE` (`NEUTRAL`, a fine riproduzione)
- **Cancellazione**: pressione `GPIO47` durante `THINKING` o `SPEAKING` invia `{"type":"cancel"}`, svuota il buffer TX con fade-out/flush e torna a `IDLE`.
- **Errori (`ERROR` → `CONFUSED` per `2 s`)**: timeout `STT/AI` (`25 s`), disconnessione WebSocket, errori I²S o ring buffer → ritorno sicuro a `IDLE` e riconnessione Wi-Fi/WS con backoff (`2s → 5s → 15s`).

---

## 8. Sicurezza, Logging e Protezione Credenziali

- Comunicazione confinata alla **LAN domestica** (`ws://` interno; nessuna esposizione su Internet).
- **Autenticazione dispositivo**: header `Authorization: Bearer <DEVICE_TOKEN>` in fase di handshake WebSocket, salvato su Raspberry in `.env` (escluso da Git) e su ESP32 in `secrets.h` (escluso da `.gitignore`) o NVS `Preferences`.
- **Limiti difensivi**: dimensione massima upload vocale `200 KB`, validazione JSON schema, nessun segreto nei log.

---

## 9. Valutazione Prestazioni, Limiti Hardware e Rischi

- **Latenza attesa end-to-end (stima)**:
  - Upload LAN `3 s` audio (`96 KB`): `~50–150 ms`.
  - STT `faster-whisper base` su Pi 5: `~1,0–2,5 s`.
  - LLM Ollama su Ryzen 7 5700U (CPU/iGPU, modello 3B–7B quantizzato): `~1,5–5,0 s` (primo token/risposta breve).
  - TTS Piper su Pi 5: `~0,3–0,6 s`.
  - **Totale stimato**: `~3–8 s` in stato `THINKING` (con Eyes 3.0 animati).
- **Rischi principali e mitigazioni**:
  1. **Contesa Wi-Fi + I²S + I²C su ESP32-S3**: mantenere i task audio `I2S0/I2S1` isolati dalle chiamate di rete (Core `0` audio, Core `1` Wi-Fi/WS/OLED) e verificare sperimentalmente con test dedicati.
  2. **Assorbimento picchi `5 V` con Wi-Fi TX + Speaker attivi**: Wi-Fi TX aggiunge picchi `~250–350 mA`; mantenere volume `≤ 15%` finché non saranno installati i condensatori `470 µF` + `100 nF` e/o alimentazione esterna adeguata.

---

## 10. Piano di Sviluppo Incrementale

- **FASE 11.2 — Bridge Python sul Raspberry Pi 5 (test su PC/Docker senza ESP32)**:
  - Server FastAPI WebSocket + `/health`, integrazione `faster-whisper` + `Ollama`/fallback + `Piper 16 kHz`, test automatici con file WAV.
- **FASE 11.3 — Connettività Wi-Fi + WebSocket ESP32-S3 (solo testo/stati, senza streaming audio)**:
  - Connessione LAN sicura (`secrets.h`), heartbeat, transizioni `IDLE ↔ THINKING ↔ ERROR`, riconnessione automatica.
- **FASE 11.4 — Trasporto Audio Push-to-Talk & Ring Buffer Streaming**:
  - Upload PCM16 PSRAM su WS, ring buffer PSRAM `128 KB` per TTS lungo, test di coesistenza Wi-Fi + FreeRTOS RX/TX + OLED.
- **FASE 11.5 — Integrazione Completa, Cancellazione & Collaudo Endurance**:
  - `STOP`/`CANCEL` durante `THINKING` e `SPEAKING`, test multi-ciclo e fallback PC spento.

---

## 11. Decisioni Ancora da Prendere (Prima della FASE 11.2)

1. **Modello STT predefinito su Pi 5**: `faster-whisper tiny` (più veloce, ~`0,6–1,2 s`) vs `base` (più preciso in italiano, ~`1,5–2,5 s`).
2. **Voce TTS predefinita**: `it_IT-riccardo-x_low` (`16 kHz` nativo, zero ricampionamento) vs `it_IT-paola-medium` (`22,05 kHz` ricampionato).
3. **Modello Ollama sul PC Windows 11** (es. `qwen2.5:7b` / `llama3.1:8b` / `gemma2:9b` in base ai `16 GB` RAM) e scelta del **fallback** quando il PC è spento (offline fisso vs API cloud esterna).
4. **Alimentazione definitiva**: conferma installazione condensatori `470 µF` + `100 nF` (o alimentatore `5 V` dedicato) prima di attivare Wi-Fi + audio insieme.
