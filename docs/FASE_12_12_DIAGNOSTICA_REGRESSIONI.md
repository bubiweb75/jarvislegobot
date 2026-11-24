# FASE 12.12 — Diagnostica delle regressioni dopo l'ottimizzazione AI

## 1. Stato iniziale del sistema (sola lettura)

- **Voice Bridge attivo**: `PID 11452` (`task-3665`) su `<PC_LAN_IP>:8765`, `/health` `200 OK`, `/ready` `200 OK` (`stt=True`, `tts=True`, `ollama=True`, `cloud=False`).
- **Ollama attivo**: `PID 18024` (`task-3574`) su `127.0.0.1:11434`, modello `qwen2.5:3b`.
- **ESP32-S3 (`<ESP32_LAN_IP>`)**: connesso via WSS (`connection open`).

## 2. Correlazione dei turni di collaudo (`task-3665.log` + `task-3574.log`)

Poiché `JARVIS_LOG_STT_DIAG_TEXT=false` e `JARVIS_LOG_CONVERSATION_TEXT=false`, nei log non sono presenti i testi delle trascrizioni né le risposte generate. I **6 turni** registrati in `task-3665.log` si correlano per timestamp e profilo token/latenza con `task-3574.log`:

| # | `request_id` (`task-3665`) | Provider | `stt_ms` | `ai_ms` | `tts_ms` | `total_ms` | Ollama (`task-3574`) |
|---|---|---|---|---|---|---|---|
| 1 | `req_710da33943f7` | `ollama:qwen2.5:3b` | `5561.6` | `2108.3` | `882.4` | `8569.7` | `task 1188` (`20:12:13`): `prompt_eval=11 tok/220ms`, `eval=32 tok/1844ms` |
| 2 | `req_b0cfb80ac394` | `ollama:qwen2.5:3b` | `3018.4` | `2148.0` | `836.6` | `6017.3` | `task 1221` (`20:12:31`): `prompt_eval=15 tok/299ms`, `eval=32 tok/1810ms` |
| 3 | `req_60bacd40bbf8` | `ollama:qwen2.5:3b` | `3074.7` | `4940.3` | `1243.5` | `9273.9` | `task 1254` (`20:12:52`): `prompt_eval=18 tok/268ms`, `eval=80 tok/4607ms` |
| 4 | `req_bc9e283321df` | `ollama:qwen2.5:3b` | `2832.4` | `1140.8` | `745.6` | `4734.5` | `task 1335` (`20:13:19`): `prompt_eval=15 tok/282ms`, `eval=15 tok/835ms` |
| 5 | `req_5b147b6e5370` | `ollama:qwen2.5:3b` | `3072.0` | `9523.8` | `1630.9` | `14246.0` | `task 1351` (`20:13:43`): `prompt_eval=189 tok/2138ms`, `eval=120 tok/7354ms` |
| 6 | `req_d27abfaf6819` | `ollama:qwen2.5:3b` | `3044.3` | `3660.3` | `685.0` | `7410.1` | `task 1472` (`20:14:01`): `prompt_eval=277 tok/3041ms`, `eval=11 tok/581ms` |

Nessun timeout, errore HTTP, eccezione, cancellazione o fallimento TTS/WSS è presente nei log.

## 3. Diagnosi dei due FAIL

### Test A — Comando locale (`"Jarvis, che ore sono?"`) → FAIL
- **Fatto confermato dai log**: **nessuno dei 6 turni** ha attivato `Local Intent` (tutti e 6 hanno usato `ollama:qwen2.5:3b`, incluso il primo turno che ha generato 32 token da Ollama invece dell'ora locale).
- **Causa individuata**: `LocalIntentHandler` usava un match esatto (`q in {...}`) dopo `_PREFIX_RE` (che rimuoveva solo `jarvis`) e `_SUFFIX_RE`. Se Whisper `small/int8` trascrive il wake word con una variante fonetica (es. `gervis`/`giarvis`/`charvis`) o con un prefisso/suffisso extra (es. `"senti Jarvis..."` o `"...oggi"`), il match esatto falliva e instradava la richiesta a Ollama (che non ha accesso all'orologio reale).
- **Non confermabile senza log STT**: la stringa esatta trascritta da Whisper nel turno 1/2.

### Test D — Spiegazione (`"Jarvis, spiegami come funziona un vulcano."`) → FAIL
- **Fatto confermato dai log**: il turno 5 (`req_5b147b6e5370` / `task 1351`) ha impiegato **`14246.0ms` totali** (`ai=9523.8ms`), con **`prompt_eval=2137.8ms` su `189` token** (KV cache invalidata dopo il prompt di sistema) e **`eval=7353.9ms` raggiungendo esattamente il tetto di `120` token** (`tts=1630.9ms`).
- **Causa individuata**:
  1. Con `max_history_turns=3` (`6` messaggi), già al turno 4–5 la finestra scorrevole ha espulso il turno più vecchio, invalidando la KV cache di Ollama dopo il prompt di sistema (`+2.14s` sul turno 5 e `+3.04s` sul turno 6!).
  2. Il tetto `120` token ha fermato la generazione di `qwen2.5:3b` (`eval=120 tok`, `done=length`), e `OllamaRouterClient` usava `rfind(". ")` che non intercetta `.\n` e può tagliare una parte significativa della spiegazione se l'ultima frase supera il limite.
- **Non confermabile senza log testo**: la qualità o completezza semantica esatta della risposta pronunciata nel turno 5.

## 4. Analisi della lentezza (Test B / E)

- **Turni 1–3 (`req_710da33943f7`, `req_60bacd40bbf8`)**: `stt=5561.6ms` al primo turno (rispetto a `~2.8–3.0s` sui successivi) + `ai=4940.3ms` (`80` token sul turno 3) → `total=9273.9ms`.
- **Turno 6 (`req_d27abfaf6819`)**: nonostante solo `11` token generati (`580.7ms`), `ai_ms` è salito a `3660.3ms` perché Ollama ha dovuto rivalutare `277` token di prompt (`3041.2ms`) per via dello scorrimento della cronologia (`max_history_turns=3`).
- Inoltre la cache del probe `/api/tags` aveva `TTL=15s`, inferiore all'intervallo tipico fra i turni (`15–26s`), causando comunque 6 chiamate `GET /api/tags` (`7–23ms` ciascuna).

## 5. Correzioni isolate applicate su disco (non ancora attive sul Voice Bridge)

1. `05-Voice-AI/voice_bridge/local_intents.py`:
   - Esteso `_PREFIX_RE` con `senti` e varianti fonetiche comuni di Jarvis (`jarvis|gervis|giarvis|charvis`).
   - Aggiunto fallback regex sicuro `_TIME_CORE_RE` per frasi brevi (`<= 7` parole) contenenti `"che ore sono"` / `"che ora è"` / `"dimmi l'ora"` / `"mi dici l'ora"`, escludendo contesti non locali (`fuso`, `treno`, `volo`, `ieri`, `domani`, città).
2. `05-Voice-AI/voice_bridge/ai_router.py`:
   - Migliorata la gestione `done_reason == "length"` con regex `[.!?](?=\s|$)` (gestisce anche `.\n`) senza mai restituire testo vuoto.
   - Esteso `probe_cache_ttl_s` di default da `15.0` a `60.0` secondi.

## 6. Test automatici

Aggiunto `test_18_local_intent_variants_and_fase_c_truncation_edge_cases` in `05-Voice-AI/tests/test_hybrid_ai_fase12.py` (copre tutte le varianti `Local Intent` e tutti i 6 casi limite di `done_reason` / troncamento richiesti in FASE C).
Esecuzione dell'intera suite (`test_hybrid_ai_fase12.py`, `test_esp32_ws_protocol.py`, `test_voice_bridge.py`, `test_voice_lab.py`):
- **`Ran 39 tests in 3.299s — OK`**.

## 7. Confronto opzioni di rollback / intervento

- **Opzione A — Correzione mirata (RACCOMANDATA)**: mantenere le ottimizzazioni FASE 12.11 attivando le correzioni isolate in `local_intents.py` e `ai_router.py`, riportando però `JARVIS_MAX_HISTORY_TURNS=4` (`8` messaggi) o `5` (`10` messaggi) per evitare l'invalidazione precoce della KV cache (`+2.1–3.0s`) al turno 4–5, e mantenendo `JARVIS_OLLAMA_MAX_TOKENS=150` (o `140`) per non troncare le spiegazioni come `"vulcano"`.
- **Opzione B — Rollback selettivo**: disabilitare il taglio su `done_reason == "length"` e riportare `JARVIS_OLLAMA_MAX_TOKENS=150` mantenendo il client HTTP persistente. Non risolverebbe però i mancati match di `LocalIntentHandler` su varianti Whisper.
- **Opzione C — Ripristino FASE 12.9**: tornare alla configurazione `LOCAL_ONLY` con `150` token e `4` turni (4/5 OK nella FASE 12.9), perdendo però il client HTTP persistente e la protezione `LocalIntentHandler` su varianti fonetiche.

## 8. Raccomandazione finale

Si raccomanda l'**Opzione A** (riavvio controllato con le correzioni in `local_intents.py` + `ai_router.py`, `JARVIS_MAX_HISTORY_TURNS=4` e `JARVIS_OLLAMA_MAX_TOKENS=150` per non troncare le spiegazioni, mantenendo `httpx.Client` persistente, `num_ctx=2048`, `keep_alive=10m` e `detail_max_tokens=180`).

Voice Bridge `task-3665` (`PID 11452`) lasciato attivo senza interruzioni in attesa di autorizzazione.
