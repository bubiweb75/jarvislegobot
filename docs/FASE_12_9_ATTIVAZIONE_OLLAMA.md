# FASE 12.9 — Attivazione controllata Ollama locale e collaudo conversazionale

## 1. Verifiche iniziali

- **Ollama**: `%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe` (`client version 0.40.16`), inizialmente fermo (`127.0.0.1:11434` chiuso).
- **Modello locale**: `qwen2.5:3b` già presente e integro in cache locale (`~/.ollama/models`).
- **Risorse PC rilevate prima dell'avvio**:
  - CPU: `AMD Ryzen 7 5700U with Radeon Graphics` (`8C/16T`, carico iniziale `9%`)
  - RAM: `15.39 GB` totali, `4.31 GB` liberi
  - Memoria virtuale: `17.42 GB` totali, `1.74 GB` liberi
- **Voice Bridge precedente**: identificato su `<PC_LAN_IP>:8765` (`PID 13276`, `task-3456`, AI disabilitata).
- **Test pre-attivazione (`test_hybrid_ai_fase12.py`)**: `Ran 8 tests in 1.014s — OK`.

## 2. Avvio Ollama e benchmark preliminare diretto (`qwen2.5:3b`)

- **Endpoint**: avviato esclusivamente su `127.0.0.1:11434` (`task-3574`, `OLLAMA_HOST=127.0.0.1:11434`, nessuna esposizione LAN, nessun download, nessun servizio Windows aggiunto).
- **Stato prima del benchmark**: `RAM_FREE_GB=4.25`, `VIRT_FREE_GB=1.57`, `CPU_PCT=4`, `OLLAMA_MB=33.2`.
- **Risultati reali (`num_predict=180`, `temperature=0.5`)**:
  1. `"Chi era Leonardo da Vinci? Rispondi brevemente in italiano."` → `wall=9.59s` (`load=4.42s`, `eval=4.40s`, `77` token, **`17.5 tok/s`**).
  2. `"Spiega cos'è un vulcano in due frasi."` → `wall=6.77s` (`load=0.01s`, `eval=6.24s`, `104` token, **`16.7 tok/s`**).
  3. `"Quanto fa 12 moltiplicato per 8?"` → `wall=1.55s` (`load=0.01s`, `eval=0.93s`, `15` token, **`16.1 tok/s`**) → `"12 moltiplicato per 8 fa 96."`.
- **Stato dopo il benchmark**: `RAM_FREE_GB=2.33`, `VIRT_FREE_GB=0.61`, `CPU_PCT=6` (nessuno swapping sostenuto né instabilità).

## 3. Configurazione effettiva Voice Bridge (senza segreti)

Dopo arresto ordinato del precedente Voice Bridge (`PID 13276`) e verifica porta `8765` libera, è stata avviata la nuova istanza (`PID 21096`, `task-3588`) con:

- `JARVIS_BRIDGE_HOST=<PC_LAN_IP>`
- `JARVIS_BRIDGE_PORT=8765`
- `JARVIS_BRIDGE_REQUIRE_AUTH=true`
- `JARVIS_STT_MODEL=small` (`int8`)
- `JARVIS_TIMEZONE=Europe/Rome`
- `JARVIS_PIPER_BIN=tts-lab\bin\piper\piper.exe`
- `JARVIS_PIPER_MODEL_PATH=tts-lab\models\piper\it_IT-riccardo-x_low.onnx`
- `JARVIS_AI_MODE=LOCAL_ONLY`
- `JARVIS_OLLAMA_ENABLED=true`
- `JARVIS_OLLAMA_MODEL=qwen2.5:3b`
- `JARVIS_OLLAMA_URL=http://127.0.0.1:11434`
- `JARVIS_OLLAMA_MAX_TOKENS=150`
- `JARVIS_OLLAMA_GENERATE_TIMEOUT_S=20.0`
- `JARVIS_AI_TIMEOUT_SECONDS=20.0`
- `JARVIS_AI_FALLBACK_ENABLED=false`
- `JARVIS_CLOUD_ENABLED=false`
- `JARVIS_LOG_STT_DIAG_TEXT=false`

## 4. Verifiche post-attivazione

- **`/health`**: `200 OK` (`{"status": "ok", "service": "jarvis-voice-bridge", "version": "0.1.0"}`).
- **`/ready`**: `200 OK`, `ready=true`, `service_ok=true`:
  - `stt`: `faster-whisper pronto (modello 'small', CPU int8)`
  - `tts`: `Piper pronto (it_IT-riccardo-x_low.onnx, 16000 Hz)`
  - `ollama`: `Ollama attivo (1 modelli, selezionato qwen2.5:3b)`
  - `cloud`: `available=false` (`Cloud disabilitato da configurazione`)
  - `offline_fallback`: `Fallback offline sempre pronto`
- **Connessione ESP32 WSS**: riconnesso automaticamente dopo l'avvio (`<ESP32_LAN_IP>:50417 - "WebSocket /ws/v1/esp32" [accepted]`, `connection open`).
- **Risorse PC post-attivazione**: `RAM_FREE_GB=2.75`, `VIRT_FREE_GB=1.16`, `CPU_PCT=12`.
- **Suite test automatici** (`test_hybrid_ai_fase12.py`, `test_esp32_ws_protocol.py`, `test_voice_bridge.py`, `test_voice_lab.py`): **`Ran 37 tests in 3.062s — OK`**.

## 5. Problemi e limitazioni note

- Con Ollama (`qwen2.5:3b`), Voice Bridge (`Whisper small/int8`) e IDE attivi restano ~`2.75 GB` di RAM libera su `15.39 GB`.
- La prima richiesta dopo lungo inutilizzo può includere ~`4.4s` di caricamento modello se scaricato dalla RAM da Ollama.
- Il volume `13%` impostato via seriale sull'ESP32 non è persistente al riavvio (default firmware `10%`).
- Nessun test vocale fisico eseguito ancora: in attesa dei test A–E da parte dell'utente su `GPIO47`.

## 6. Procedura di rollback

1. Arrestare il Voice Bridge (`PID 21096` / `task-3588`) e, se necessario, il processo Ollama (`task-3574`).
2. Riavviare il Voice Bridge impostando `JARVIS_AI_MODE=DISABLED`, `JARVIS_OLLAMA_ENABLED=false`, `JARVIS_CLOUD_ENABLED=false`, `JARVIS_AI_FALLBACK_ENABLED=false`.
3. Verificare `/ready` e la riconnessione WSS dell'ESP32 su `<PC_LAN_IP>:8765`.
