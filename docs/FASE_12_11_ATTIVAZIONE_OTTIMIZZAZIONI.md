# FASE 12.11 — Attivazione controllata delle ottimizzazioni AI e verifica del sistema

## 1. Controlli preliminari

- **Voice Bridge precedente**: `PID 21096` (`task-3588`) su `<PC_LAN_IP>:8765`, `/health` `200 OK`, `/ready` `200 OK`.
- **Ollama**: `PID 18024` (`task-3574`) su `127.0.0.1:11434`, modello `qwen2.5:3b` attivo.
- **Risorse iniziali**: `RAM_FREE_GB=3.05/15.39`, `CPU_PCT=30`.
- **Verifiche tecniche pre-riavvio**:
  - `OllamaRouterClient`: `httpx.Client` persistente, `probe_cache_ttl_s=15.0` con invalidazione immediata su errore, `close()` invocato allo shutdown di FastAPI (`VoiceBridgeService.close()` / `AIRouter.close()`).
  - Gestione `done_reason == "length"`: se il limite token (`120` o `180`) interrompe la risposta a metà frase, `OllamaRouterClient.generate()` tronca all'ultima frase completa (`.`, `!`, `?`) prima di Piper TTS.
- **Test automatici pre-riavvio**: `Ran 38 tests in 3.156s — OK`.

## 2. Configurazione precedente vs definitiva (senza segreti)

| Parametro | Precedente (FASE 12.9) | Definitiva (FASE 12.11) |
|---|---|---|
| `JARVIS_AI_MODE` | `LOCAL_ONLY` | `LOCAL_ONLY` |
| `JARVIS_OLLAMA_ENABLED` | `true` | `true` |
| `JARVIS_OLLAMA_MODEL` | `qwen2.5:3b` | `qwen2.5:3b` |
| `JARVIS_OLLAMA_URL` | `http://127.0.0.1:11434` | `http://127.0.0.1:11434` |
| `JARVIS_AI_FALLBACK_ENABLED` | `false` | `false` |
| `JARVIS_CLOUD_ENABLED` | `false` | `false` |
| `JARVIS_OLLAMA_MAX_TOKENS` | `150` | **`120`** |
| `JARVIS_OLLAMA_DETAIL_MAX_TOKENS` | *(non presente)* | **`180`** |
| `JARVIS_MAX_HISTORY_TURNS` / `MAX_MESSAGES` | `4` / `8` | **`3` / `6`** |
| `JARVIS_TTS_MAX_CHARS` | `600` | **`550`** |
| `JARVIS_OLLAMA_NUM_CTX` | `4096` (default Ollama) | **`2048`** |
| `JARVIS_OLLAMA_KEEP_ALIVE` | `5m` (default Ollama) | **`10m`** |
| Prompt di sistema | `163` token stimati | ~`80` token stimati |

## 3. Stato post-riavvio

- **Voice Bridge attivo**: `PID 11452` (`task-3665`), `https://<PC_LAN_IP>:8765`.
  - `/health`: `200 OK`
  - `/ready`: `200 OK`, `stt=True` (`small/int8`), `tts=True` (`it_IT-riccardo-x_low.onnx`), `ollama=True` (`qwen2.5:3b`), `cloud=False`.
- **Ollama**: `PID 18024` (`task-3574`), lasciato attivo senza riavvio su `127.0.0.1:11434`.
- **ESP32-S3 (`<ESP32_LAN_IP>`)**: riconnesso automaticamente via WSS (`<ESP32_LAN_IP>:50421 - "WebSocket /ws/v1/esp32" [accepted]`, `connection open`).

## 4. Test automatici eseguiti

Suite (`test_hybrid_ai_fase12.py`, `test_esp32_ws_protocol.py`, `test_voice_bridge.py`, `test_voice_lab.py`):
- **`38/38` test superati (`OK`, `3.156s`)**, inclusa la verifica esplicita di:
  - limite standard `120` token vs approfondimento `180` token (`test_17`);
  - gestione `done_reason="length"` senza inviare frasi troncate al TTS;
  - cache del probe `/api/tags` con TTL `15s` e chiusura pulita delle risorse;
  - memoria conversazionale, comandi locali prioritari, timeout/fallback, assenza Cloud e protocollo WSS ESP32.

## 5. Benchmark post-attivazione (testuale diretto su `127.0.0.1:11434`, confronto con FASE 12.10)

Nota: i dati seguenti sono misure testuali dirette su Ollama (`bench_fase12_11.py`); `stt_ms` e `tts_ms` saranno rilevati durante il collaudo vocale fisico dell'utente su `GPIO47`.

- **Risorse**: `RAM_FREE_GB` prima `2.78 GB` (`CPU_PCT=18`), dopo `3.10 GB` (`CPU_PCT=20`).
- **Q1 (*"Chi era Leonardo da Vinci?"*, limit `120`)**: `wall=6535ms`, `102` token, `15.8 tok/s`, `done=stop` (FASE 12.10 ott. run 2: `6244ms`, `103` token).
- **Q2 (*"Spiegami come funziona un vulcano."*, limit `120`)**: `wall=8586ms`, `120` token, `14.1 tok/s`, `done=length` (vs FASE 12.10 orig. `9.77s` medi; `done=length` gestito da trim a fine frase completa).
- **Q3 (*"Quanto fa dodici per otto?"*, limit `120`)**: `wall=981ms`, `11` token, `15.9 tok/s`, `done=stop` → `"Dodici per otto fa 96."` (vs FASE 12.10 orig. `1.37s` medi).
- **Q4 (*"Spiegami più approfonditamente come funziona un vulcano."*, limit `180`)**: `wall=12715ms`, `180` token, `14.6 tok/s`, `done=length` (con `14.6 tok/s` sotto carico CPU `18–20%`).

## 6. Problemi e limitazioni note

- Su spiegazioni lunghe (`Q2`/`Q4`), `qwen2.5:3b` su CPU (`~14–16 tok/s`) può comunque richiedere `8.5–12.7s` e raggiungere il tetto di `120` o `180` token (`done=length`), mitigato dal troncamento pulito all'ultima frase completa.
- Il volume `13%` impostato via seriale sull'ESP32 non è persistente al riavvio (default firmware `10%`).
- Il collaudo vocale fisico non è ancora stato eseguito (in attesa dell'utente).

## 7. Procedura di rollback

1. Arrestare `task-3665` (`PID 11452`).
2. Riavviare con la configurazione FASE 12.9 (`JARVIS_OLLAMA_MAX_TOKENS=150`, `JARVIS_MAX_HISTORY_TURNS=4`, `JARVIS_CONVERSATION_MAX_MESSAGES=8`, `JARVIS_TTS_MAX_CHARS=600`, `JARVIS_OLLAMA_NUM_CTX=4096`) oppure con `JARVIS_AI_MODE=DISABLED`.
3. Verificare `/ready` e la riconnessione WSS dell'ESP32 su `<PC_LAN_IP>:8765`.
