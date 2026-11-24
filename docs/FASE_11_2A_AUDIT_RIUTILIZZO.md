# FASE 11.2A — Audit e Riutilizzo del Lavoro Esistente

> **Stato documento**: Analisi completa eseguita sul repository senza installazioni, senza modifiche a firmware/container e senza chiamate cloud.
> **Nota trasparenza**: prima dell'invio della FASE 11.2A è stata avviata una bozza parziale in `05-Voice-AI/voice_bridge/` (non collegata né completata); l'audit seguente distingue chiaramente il codice stabile preesistente da quanto manca per completare la FASE 11.2B.

---

## 1. Inventario dei Componenti Esistenti

### 1.1 Simulatori e Progetti Hardware (`04-Firmware/`)
- `04-Firmware/jarvis-desk-buddy/`: firmware stabile C++ Eyes 3.0 (`14` espressioni, `StateMachine`, `GPIO47`, `SH1106`/`SSD1306`, `TouchManager` isolato sotto `#ifdef JARVIS_ENABLE_TOUCH`).
- `04-Firmware/jarvis-desk-buddy-sim/`: simulatore Python desktop (`eye_engine.py`, `eye_engine_v2_baseline.py`, `eye_engine_v3_preview.py`, `compare_eyes_v2_v3.py`, `behavior_engine.py`, `sensor_manager.py`) con **44 test unitari** verificati.
- `04-Firmware/wokwi-simulation/`, `04-Firmware/wokwi-web/`, `04-Firmware/wokwi-touch/`, `04-Firmware/wokwi-gpio1-diag/`: varianti Wokwi isolate (ESP32-S3 + `board-ssd1306` `0x3C` + `GPIO47` + `GPIO1` in `wokwi-touch` / `wokwi-gpio1-diag`). I progetti compilano localmente; il collaudo interattivo nel browser dipende dall'esecuzione manuale su `wokwi.com`.
- `04-Firmware/esp32s3-diag-test/`: diagnostica hardware FASE 10.1.
- `04-Firmware/arduino-hw-test/`:
  - `jarvis_eyes3_hw_test/` (collaudo reale Eyes 3.0 su SH1106, commit `53f1bce`)
  - `inmp441_hw_test/`, `max98357a_hw_test/`, `jarvis_voice_hw_test/` (FASE 10.5 collaudata)
  - `jarvis_duplex_hw_test/`, `jarvis_audio_diag_hw_test/`, `jarvis_duplex_rtos_hw_test/` (FASE 10.8 con FreeRTOS RX+TX)

### 1.2 Backend Voice AI (`05-Voice-AI/`)
- `ai_providers.py`: `DemoAIProvider`, `OllamaProvider` (con `/api/tags` + `/api/chat`), `OpenAIProvider` (con conferma esplicita e gestione 401/429/timeout).
- `stt_providers.py`: `FasterWhisperSTTProvider` (`device="cpu"`, `compute_type="int8"`, `local_files_only=(not allow_download)`).
- `tts_providers.py`: `WindowsSapiTTSProvider` (PowerShell SAPI, solo Windows) e `PiperTTSProvider` + `voice_dsp.py` (`shape_piper_wav`, pensato per riproduzione locale tramite `winsound` / file).
- `conversation_engine.py`, `conversation_naturalizer.py`, `memory_engine.py`, `voice_controller.py`, `eye_bridge.py`, `config.py`, `control_center_panels.py`, `jarvis_app.py`: stack desktop Tkinter per PC Windows.
- **Server HTTP/FastAPI/WebSocket**: **assente** nello stack `05-Voice-AI/*.py` preesistente (`fastapi`, `uvicorn`, `python-multipart` non presenti in `05-Voice-AI/requirements.txt` né installati in `05-Voice-AI/.venv`).

---

## 2. Confronto con la FASE 11.1 (`docs/FASE_11_1_PROGETTAZIONE_ASSISTENTE_VOCALE.md`)

| Funzionalità | File Esistente | Stato Verificato | Test Disponibili | Riutilizzabilità | Modifiche / Adapter Necessari |
|---|---|---|---|---|---|
| **STT italiano (`faster-whisper`)** | `05-Voice-AI/stt_providers.py` (`FasterWhisperSTTProvider`) | **PARZIALE** | Test errore/mock in `test_voice_ai.py`; modello `base`/`tiny` non pre-verificato su Pi 5 arm64 | Alta (adapter diretto) | Cache singleton per processo, timeout esplicito, gestione silenzio/trascrizione vuota |
| **AI Router (`Ollama → Cloud → Offline`)** | `05-Voice-AI/ai_providers.py` (`OllamaProvider`, `OpenAIProvider`, `DemoAIProvider`) | **PARZIALE** | `test_voice_ai.py` (Ollama assente / OpenAI non confermato) | Alta (wrapping) | In `OllamaProvider` manca fallback automatico `Ollama → Cloud → Offline` e timeout separati probe (`1.5s`) vs generazione (`20s`) |
| **Fallback offline deterministico** | `05-Voice-AI/ai_providers.py` (`DemoAIProvider`) | **PARZIALE** | `test_voice_ai.py` | Media-Alta | Adattare i messaggi affinché dichiarino onestamente l'assenza del motore AI |
| **TTS Piper → WAV 16 kHz mono PCM16** | `05-Voice-AI/tts_providers.py` (`PiperTTSProvider`) + `voice_dsp.py` | **PARZIALE** | `test_11`, `test_12` in `test_voice_ai.py` | Media (wrapper headless) | `tts_providers.py` usa `winsound` per riproduzione locale; serve sintesi headless verso `bytes` WAV con lettura SR da `.onnx.json`/header e ricampionamento reale a `16 kHz` |
| **Gestione contesto conversazionale** | `05-Voice-AI/conversation_engine.py`, `memory_engine.py` | **PRONTA** (desktop) / **PARZIALE** (bridge HTTP) | `test_conversation_engine.py`, `test_memory_engine.py` | Media | Per l'MVP bridge serve contesto leggero configurabile senza persistenza forzata |
| **API HTTP FastAPI (`/health`, `/ready`, `/api/v1/voice/process`)** | Nessuno nello stack preesistente (`voice_bridge/` in bozza) | **MANCANTE** (non ancora completata/testata con FastAPI) | Nessuno eseguibile finché `fastapi` non è in `.venv` | Nuova implementazione | Completare `voice_bridge/` + installazione autorizzata `fastapi`/`uvicorn`/`python-multipart` in `.venv` |
| **Validazione WAV, sicurezza token, SSRF, cleanup temp** | Nessuno nello stack desktop | **MANCANTE** | Da aggiungere | Nuova implementazione | Validazione header RIFF/WAVE, limiti byte/durata, auth Bearer, redazione log, TTL cleanup |
| **Docker & Compose per Raspberry Pi 5 (arm64)** | Nessuno in `05-Voice-AI/` | **MANCANTE** | Da preparare | Nuova implementazione | `Dockerfile` arm64-compatibile, `.dockerignore`, `docker-compose.example.yml`, `.env.bridge.example` |
| **Comunicazione ESP32 ↔ Pi 5 (Wi-Fi/WebSocket/RingBuffer)** | `04-Firmware/arduino-hw-test/jarvis_duplex_rtos_hw_test/` (audio locale) | **DA VERIFICARE** (solo offline RTOS) | Solo hardware locale FASE 10.8 | Alta (FASE 11.3/11.4) | Fuori perimetro FASE 11.2 (prevista in FASE 11.3–11.4) |

---

## 3. Test Verificati in Questa Sessione (Eseguiti Isolatamente)

- **`05-Voice-AI/tests/`**: `05-Voice-AI\.venv\Scripts\python.exe -m unittest discover -s "05-Voice-AI\tests" -p "test_*.py" -v`
  - **Esito**: **`Ran 50 tests in 15.380s` → `OK`** (0 fallimenti, 0 skip).
- **`04-Firmware/jarvis-desk-buddy-sim/`**: `05-Voice-AI\.venv\Scripts\python.exe -m unittest discover -s "04-Firmware\jarvis-desk-buddy-sim" -p "test_*.py" -v`
  - **Esito**: **`Ran 44 tests in 3.844s` → `OK`** (0 fallimenti, 0 skip).

---

## 4. Problemi di Compatibilità e Dipendenze Mancanti

1. **Dipendenze assenti in `05-Voice-AI\.venv`**: `fastapi`, `uvicorn`, `python-multipart` (necessarie per avviare FastAPI e `TestClient` su Windows).
2. **`tts_providers.py` accoppiato a Windows**: importa `winsound` e orienta `PiperTTSProvider` al playback locale su PC, non alla restituzione di buffer WAV HTTP per Linux arm64 / ESP32.
3. **Comportamento di `OllamaProvider`**: nella versione attuale solleva `AIProviderError` senza passare al cloud o al fallback offline (`"Non passo al cloud automaticamente"`).

---

## 5. Architettura di Integrazione Proposta e Piano Minimo FASE 11.2B

1. **Riutilizzo tramite adapter senza duplicare logica**:
   - `voice_bridge/stt_engine.py` → avvolge `stt_providers.FasterWhisperSTTProvider`.
   - `voice_bridge/ai_router.py` → avvolge `ai_providers.OpenAIProvider` + client Ollama con timeout separati (`probe 1.5s`, `connect 2s`, `generate 20s`) + `OfflineFallbackProvider`.
   - `voice_bridge/tts_engine.py` → esegue `piper` headless e normalizza via `audio.py` a `16.000 Hz` mono PCM16 (leggendo `.onnx.json` e header WAV).
2. **Piano minimo FASE 11.2B (in attesa di autorizzazione)**:
   - Completare `voice_bridge/pipeline.py`, `voice_bridge/api.py`, file Docker (`Dockerfile`, `.dockerignore`, `docker-compose.example.yml`, `.env.bridge.example`, `README.md`) e `05-Voice-AI/tests/test_voice_bridge.py` (tutti i 20 test richiesti).
   - Eseguire tutti i test isolati con `05-Voice-AI\.venv\Scripts\python.exe` (e richiedere eventuale autorizzazione per installare `fastapi`/`uvicorn`/`python-multipart` in `.venv` se si vuole testare `TestClient` e server HTTP locale).
   - Redigere `docs/FASE_11_2_REPORT_IMPLEMENTAZIONE.md`.
