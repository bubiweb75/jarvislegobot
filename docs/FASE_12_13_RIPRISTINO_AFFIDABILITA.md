# FASE 12.13 — Attivazione correzioni mirate e ripristino affidabilità

## 1. Stato iniziale

- **Voice Bridge precedente**: `PID 11452` (`task-3665`) su `<PC_LAN_IP>:8765`, `/health` `200 OK`, `/ready` `200 OK`.
- **Ollama**: `PID 18024` (`task-3574`) su `127.0.0.1:11434`, modello `qwen2.5:3b` attivo.
- **Test automatici pre-riavvio**: `Ran 39 tests in 3.398s — OK`.

## 2. Modifiche effettivamente attivate

1. **`05-Voice-AI/voice_bridge/local_intents.py`**:
   - Esteso `_PREFIX_RE` con `senti` e varianti fonetiche (`jarvis|gervis|giarvis|charvis`).
   - Aggiunto fallback `_TIME_CORE_RE` per frasi brevi (`<= 7` parole) sull'ora locale, escludendo esplicitamente contesti non locali (`fuso`, `treno`, `volo`, `ieri`, `domani`, città come New York / Tokyo).
2. **`05-Voice-AI/voice_bridge/ai_router.py`**:
   - Gestione `done_reason == "length"` tramite regex `[.!?](?=\s|$)` (supporta `. `, `.\n`, `! `, `? `) troncando alla fine dell'ultima frase completa senza mai restituire testo vuoto.
   - `probe_cache_ttl_s=60.0` (cache `/api/tags` con invalidazione immediata su errore) e `httpx.Client` persistente chiuso allo shutdown (`AIRouter.close()` / `VoiceBridgeService.close()`).
3. **`05-Voice-AI/voice_bridge/config.py` e `.env.bridge.example`**:
   - Impostata cronologia di sessione a **4 turni** (`JARVIS_MAX_HISTORY_TURNS=4`, `JARVIS_CONVERSATION_MAX_MESSAGES=8`).

## 3. Configurazione finale attiva (verificata su processo `PID 12080`, senza segreti)

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
- `JARVIS_OLLAMA_MAX_TOKENS=120`
- `JARVIS_OLLAMA_DETAIL_MAX_TOKENS=180`
- `JARVIS_MAX_HISTORY_TURNS=4` (`JARVIS_CONVERSATION_MAX_MESSAGES=8`)
- `JARVIS_OLLAMA_NUM_CTX=2048`
- `JARVIS_OLLAMA_KEEP_ALIVE=10m`
- `JARVIS_TTS_MAX_CHARS=550`
- `JARVIS_CLOUD_ENABLED=false`
- `JARVIS_AI_FALLBACK_ENABLED=false`
- `JARVIS_LOG_STT_DIAG_TEXT=false`

## 4. Risultati test automatici (`39/39 OK`)

Suite eseguita (`test_hybrid_ai_fase12.py`, `test_esp32_ws_protocol.py`, `test_voice_bridge.py`, `test_voice_lab.py`):
- **`Ran 39 tests in 3.398s — OK`** (0 errori, 0 fallimenti).
- Verificati nello specifico:
  - Comandi locali riconosciuti (`"Jarvis, che ore sono?"`, `"Gervis che ore sono"`, `"Senti Jarvis, che ore sono oggi?"`, `"Dimmi l'ora per favore"`).
  - Falsi positivi rifiutati (`"Che ore sono a New York?"`, `"Che fuso orario ha Tokyo?"`, `"A che ora parte il treno?"`, `"Che ore erano ieri?"`, `"Che ora sarà domani?"`, `"Quando è nato Leonardo?"`).
  - Tutti i 6 casi limite su `done_reason` / troncamento (`test_18`).
  - Limiti token `120` vs `180`, probe cache TTL, memoria conversazionale, Cloud disabilitato, chiusura pulita client HTTP e protocollo WSS ESP32.

## 5. Stato del sistema post-riavvio

- **Voice Bridge**: `PID 12080` (`task-3723`), singola istanza su `<PC_LAN_IP>:8765`, `/health` `200 OK`, `/ready` `200 OK` (`stt=True`, `tts=True`, `ollama=True`, `cloud=False`). Nessuna eccezione nei log.
- **Ollama**: `PID 18024` (`task-3574`), attivo su `127.0.0.1:11434` con `qwen2.5:3b` (non riavviato).
- **ESP32-S3 (`<ESP32_LAN_IP>`)**: riconnesso automaticamente via WSS (`<ESP32_LAN_IP>:50425 - "WebSocket /ws/v1/esp32" [accepted]`, `connection open`).
- **Risorse PC**: `RAM_FREE_GB=2.51/15.39`, `CPU_PCT=18`.

## 6. Note su KV cache, latenza e collaudo fisico

- L'aumento a `JARVIS_MAX_HISTORY_TURNS=4` (`8` messaggi) evita lo scorrimento prematuro della finestra nei primi 4 turni; l'eventuale beneficio sulla KV cache oltre il turno 4 sarà verificato durante il collaudo vocale reale dell'utente (i 5 test fisici su `GPIO47` non sono stati simulati né dichiarati superati).

## 7. Stato del rollback

In caso di anomalie durante il collaudo fisico:
1. Arrestare `task-3723` (`PID 12080`).
2. Riavviare il Voice Bridge con la configurazione FASE 12.9 (`JARVIS_OLLAMA_MAX_TOKENS=150`, `JARVIS_MAX_HISTORY_TURNS=4`, `JARVIS_OLLAMA_NUM_CTX=4096`) oppure con `JARVIS_AI_MODE=DISABLED`.
3. Verificare `/ready` e la riconnessione WSS dell'ESP32 su `<PC_LAN_IP>:8765`.
