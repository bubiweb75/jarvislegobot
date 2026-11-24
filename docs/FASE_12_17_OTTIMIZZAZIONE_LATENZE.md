# FASE 12.17 — Ottimizzazione controllata delle latenze AI e STT

## 1. Configurazione iniziale vs finale (senza segreti)

| Parametro | Iniziale (FASE 12.16) | Finale (FASE 12.17) | Motivazione |
|---|---|---|---|
| `JARVIS_OLLAMA_KEEP_ALIVE` | `10m` | **`30m`** | Evita scaricamenti prematuri tra sessioni vicine |
| `JARVIS_OLLAMA_PREWARM_ON_STARTUP` | *(assente)* | **`true`** (non bloccante) | Precarica `qwen2.5:3b` in background allo startup senza duplicazioni né polling |
| `JARVIS_OLLAMA_MAX_TOKENS` | `120` | **`120`** (invariato) | `95` non ha migliorato la latenza nel benchmark comparativo |
| `JARVIS_OLLAMA_DETAIL_MAX_TOKENS` | `180` | `180` (invariato) | Invariato per approfondimenti |
| `JARVIS_STT_BEAM_SIZE` | `3` | **`1`** | `-46.5%` latenza STT nel benchmark con trascrizione identica |
| `JARVIS_STT_MODEL` / `COMPUTE` | `small` / `int8` | `small` / `int8` | Invariato |
| Piper + DSP "JARVIS Amichetto" | `1.21x`, `+5.0st`, `tanh` | `1.21x`, `+5.0st`, `tanh` | Invariato |
| `JARVIS_TTS_MAX_CHARS` | `300` | `300` (invariato) | Protezione `TTS_TOO_LONG` (`640,000` B) invariata |

## 2. Benchmark comparativi isolati

### A. Limite AI: `120` vs `95` token (`qwen2.5:3b`, `num_ctx=2048`, `keep_alive=30m`)
- **Q1** (*Leonardo da Vinci*): `120` → `6220ms` (`98` tok, `done=stop`) | `95` → `7719ms` (`91` tok, `done=stop`).
- **Q2** (*Come funziona un vulcano*): `120` → `8845ms` (`120` tok, `done=length`) | `95` → `9817ms` (`95` tok, `done=length`, taglio più precoce).
- **Q3** (*Dodici per otto*): `120` → `984ms` (`11` tok) | `95` → `1312ms` (`11` tok).
- **Q4** (*Approfondimento*, cap `180`): `10424ms` (`130` tok) / `14989ms` (`167` tok).
- **Decisione**: mantenuto `120` token (non applicato `95` perché privo di beneficio misurato e più soggetto a troncamenti precoci).

### B. Whisper `small/int8`: `beam_size=3` vs `beam_size=1` (campioni italiani generati con Piper)
- **`beam_size=3`**: `CMD_LOCALE=5340.1ms`, `NOME_PROPRIO=6388.9ms`, `BREVE=5014.1ms`, `LUNGA=5219.4ms` → **media `5490.6 ms`**.
- **`beam_size=1`**: `CMD_LOCALE=3772.7ms`, `NOME_PROPRIO=2305.8ms`, `BREVE=2339.7ms`, `LUNGA=3330.2ms` → **media `2937.1 ms` (`-46.5%`)**, con trascrizioni identiche su tutte le 4 categorie. *(Nota: entrambi i run sono stati eseguiti con CPU condivisa con il benchmark Ollama `task-3823`.)*
- **Decisione**: attivato `JARVIS_STT_BEAM_SIZE=1`.

## 3. Modifiche effettivamente applicate (backup in `scratch/backup_fase12_17/`)

- `05-Voice-AI/voice_bridge/config.py`: `stt_beam_size=1`, `ollama_keep_alive="30m"`, `ollama_prewarm_on_startup=True`.
- `05-Voice-AI/voice_bridge/ai_router.py`: `OllamaRouterClient.prewarm()` (esegue al massimo una volta per istanza, carica il modello con `messages=[]`, `keep_alive`, `num_ctx`, cattura eventuali errori senza bloccare).
- `05-Voice-AI/voice_bridge/pipeline.py`: `VoiceBridgeService.start_prewarm()` in thread daemon singolo.
- `05-Voice-AI/voice_bridge/api.py`: chiamata `svc.start_prewarm()` allo startup FastAPI.
- `05-Voice-AI/voice_bridge/.env.bridge.example`: aggiornati `JARVIS_STT_BEAM_SIZE=1`, `JARVIS_OLLAMA_KEEP_ALIVE=30m`, `JARVIS_OLLAMA_PREWARM_ON_STARTUP=true`.
- `05-Voice-AI/tests/test_hybrid_ai_fase12.py`: aggiunto `test_19_prewarm_non_blocking_no_duplicate_and_beam_size_1`.

## 4. Test automatici

Suite (`test_fase12_15b_tts_amichetto.py`, `test_hybrid_ai_fase12.py`, `test_esp32_ws_protocol.py`, `test_voice_bridge.py`, `test_voice_lab.py`):
- **`Ran 43 tests in 4.589s — OK`** (0 errori, 0 fallimenti).

## 5. Stato dei servizi post-riavvio

- **Voice Bridge**: `PID 11020` (`task-3851`) su `https://<PC_LAN_IP>:8765`, `/health` `200 OK`, `/ready` `200 OK`.
  - Prewarm eseguito allo startup senza bloccare: `Ollama prewarm ok model=qwen2.5:3b keep_alive=30m ms=42.1`.
- **Ollama**: `PID 18024` (`task-3574`) attivo su `127.0.0.1:11434` (`qwen2.5:3b`, non riavviato).
- **ESP32-S3 (`<ESP32_LAN_IP>`)**: riconnesso automaticamente via WSS.

## 6. Problemi residui / note

- Il volume `12%` impostato via seriale nella FASE 12.16 non è persistente al riavvio dell'ESP32 (torna a `10%` se il robot si riavvia).
- Le latenze reali di `stt_ms` con `beam_size=1` e di `ai_ms` a caldo vanno confermate dal collaudo fisico dell'utente su `GPIO47`.

## 7. Istruzioni per il collaudo fisico (`GPIO47`)

Eseguire le 5 prove reali:
1. *"Jarvis, che ore sono?"*
2. *"Jarvis, chi era Leonardo da Vinci?"*
3. *"Quando è nato?"*
4. *"Jarvis, spiegami come funziona un vulcano."*
5. *"Jarvis, quanto fa dodici per otto?"*
