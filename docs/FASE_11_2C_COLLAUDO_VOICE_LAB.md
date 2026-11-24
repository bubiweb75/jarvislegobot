# FASE 11.2C — Collaudo JARVIS Voice Lab (Interfaccia Web Locale)

---

## 1. Architettura della Pagina e File Creati/Modificati

**JARVIS Voice Lab** è servita direttamente dallo stesso processo FastAPI di `jarvis-voice-bridge` su `http://127.0.0.1:8765/` (nessun secondo backend, nessuna risorsa CDN esterna, nessun framework pesante).

### File creati
- `05-Voice-AI/voice_bridge/static/index.html` — Dashboard dark responsive (Header, Auth session, Microfono, Trascrizione, Risposta + Player WAV, Diagnostica).
- `05-Voice-AI/voice_bridge/static/style.css` — Stile dark JARVIS.
- `05-Voice-AI/voice_bridge/static/app.js` — Macchina a stati frontend (`IDLE`, `RECORDING`, `UPLOADING`, `PROCESSING`, `READY`, `PLAYING`, `ERROR`), acquisizione Web Audio API, ricampionamento WAV e `AbortController`.
- `05-Voice-AI/tests/test_voice_lab.py` — Suite automatica Voice Lab (`HttpOnly` cookie, CSRF, sicurezza statici, limiti WAV, errori STT/TTS, timeout).
- `docs/FASE_11_2C_COLLAUDO_VOICE_LAB.md` — Questo documento.

### File modificati (solo in `voice_bridge/`)
- `05-Voice-AI/voice_bridge/security.py` — Aggiunta `BrowserSessionStore` (sessioni in memoria con cookie `HttpOnly` e token CSRF).
- `05-Voice-AI/voice_bridge/api.py` — Aggiunti `GET /`, mount `/static`, `POST /api/v1/auth/session`, `GET /api/v1/auth/session`, `POST /api/v1/auth/logout`, supporto dual-auth (`Authorization: Bearer` oppure cookie `HttpOnly` + `X-CSRF-Token` sulle richieste mutative).

---

## 2. Contratto API Utilizzato

- `GET /health` → stato minimo non sensibile.
- `POST /api/v1/auth/session` (`{"token": "..."}`) → imposta cookie `jarvis_session` (`HttpOnly`, `SameSite=Strict`, `Path=/`) e restituisce `csrf_token`.
- `GET /ready` → disponibilità `stt`, `tts`, `ollama`, `cloud`, `offline_fallback`.
- `POST /api/v1/voice/process?include_base64=true` (multipart `file=voice_lab.wav` + header `X-CSRF-Token`) → restituisce `request_id`, `transcript`, `reply_text`, `provider_used`, `fallback_used`, `timings.{stt_ms,ai_ms,tts_ms,total_ms}`, `audio_sample_rate`, `audio_channels`, `audio_bits`, `audio_bytes_len`, `audio_wav_base64`, `audio_url`.
- **Nota cancellazione**: `AbortController` annulla l'attesa HTTP lato browser, ma l'endpoint sincrono FastAPI non interrompe retroattivamente un'inferenza STT/TTS già avviata nel thread Python.

---

## 3. Registrazione Browser e Conversione WAV

- Acquisizione tramite `navigator.mediaDevices.getUserMedia` + Web Audio API (`AudioContext` + `ScriptProcessorNode` + `AnalyserNode` per livello audio).
- Stop manuale oppure automatico a **`5,0 s`**, con rilascio immediato di `MediaStreamTrack.stop()` e `AudioContext.close()` anche in caso di errore o permesso negato.
- Ricampionamento lineare lato browser da `audioCtx.sampleRate` (es. `44100`/`48000 Hz`) a **`16.000 Hz`**, conversione a **PCM signed 16-bit mono** ed emissione header `RIFF/WAVE` a 44 byte.

---

## 4. Stato Modelli STT e TTS su Questo PC Windows

Verificato localmente senza download:
- **Porta `8765` su `127.0.0.1`**: libera.
- **STT (`faster-whisper` `CPU int8`)**: modello **`base` già presente in cache** (`faster-whisper pronto (modello 'base', CPU int8)`); modello `tiny` non scaricato.
- **TTS (`Piper`)**: presenti `05-Voice-AI\tts-lab\bin\piper\piper.exe`, `05-Voice-AI\tts-lab\models\piper\it_IT-riccardo-x_low.onnx` e `it_IT-riccardo-x_low.onnx.json` (`16.000 Hz` nativi).

---

## 5. Risultati dei Test Automatici (Eseguiti Offline)

- **Voice Bridge + Voice Lab** (`test_voice_bridge.py` + `test_voice_lab.py`): **`10/10` superati** (`Ran 10 tests in 0.661s` → `OK`).
- **Voice AI preesistenti** (`test_control_center.py`, `test_conversation_engine.py`, `test_conversation_naturalizer.py`, `test_memory_engine.py`, `test_voice_ai.py`): **`50/50` superati** (`Ran 50 tests in 14.421s` → `OK`).
  - *Nota tecnica*: eseguendo insieme nello stesso processo `TestClient` (`anyio` threadpool) e i test Tkinter GUI (`test_control_center.py`), la distruzione di oggetti `Tk` sul thread `anyio` può causare `Tcl_AsyncDelete`; i due gruppi di test vanno quindi eseguiti in processi separati come verificato sopra.
- **Simulatore ESP32** (`04-Firmware/jarvis-desk-buddy-sim`): **`44/44` superati** (`Ran 44 tests in 3.843s` → `OK`).
- **Collaudo browser manuale reale (microfono + altoparlanti + Whisper `base` + Piper `it_IT-riccardo-x_low`)**: **non ancora eseguito**, in attesa dell'avvio manuale dell'utente.

---

## 6. Istruzioni Operative per il Collaudo Manuale su Windows

1. Apri PowerShell nella cartella `05-Voice-AI`:
   ```powershell
   cd "05-Voice-AI"
   $env:JARVIS_BRIDGE_TOKEN="jarvis-lab-locale-2026"
   $env:JARVIS_BRIDGE_REQUIRE_AUTH="true"
   $env:JARVIS_STT_MODEL="base"
   $env:JARVIS_OLLAMA_ENABLED="false"
   $env:JARVIS_CLOUD_ENABLED="false"
   $env:JARVIS_PIPER_BIN="tts-lab\bin\piper\piper.exe"
   $env:JARVIS_PIPER_MODEL_PATH="tts-lab\models\piper\it_IT-riccardo-x_low.onnx"
   .\.venv\Scripts\python.exe -m uvicorn voice_bridge.api:app --host 127.0.0.1 --port 8765
   ```
2. Apri nel browser: `http://127.0.0.1:8765/`.
3. Inserisci `jarvis-lab-locale-2026` in **Sessione locale** e clicca **Sblocca sessione**.
4. Verifica in alto `Backend: connesso` e `AI: Offline | STT: OK | TTS: OK`.
5. Clicca **Avvia registrazione**, autorizza il microfono, pronuncia ad esempio *"Ciao Jarvis, che ore sono?"* e clicca **Ferma registrazione** (o attendi il limite di `5 s`).
6. Verifica: trascrizione Whisper, risposta offline, riproduzione WAV Piper (`16 kHz`) e tempi (`STT`, `AI`, `TTS`, `Totale`).
7. Al termine premi `Ctrl+C` nel terminale PowerShell per arrestare il server senza lasciare processi attivi.

---

## 7. Raccomandazioni Prima della FASE 11.3

- Completare il collaudo vocale reale su `127.0.0.1:8765` annotando i tempi effettivi di `faster-whisper base` e `Piper` su questo PC.
- Verificare l'eventuale risposta con `Ollama` locale (`$env:JARVIS_OLLAMA_ENABLED="true"`) in una prova successiva separata.
