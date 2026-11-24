# FASE 12.10 — Diagnostica e ottimizzazione della latenza AI conversazionale

## 1. Diagnosi della lentezza

Dall'analisi congiunta dei log del Voice Bridge attivo (`task-3588`, `PID 21096`) e del server Ollama (`task-3574`, `PID 18024` su `127.0.0.1:11434`) emergono **quattro cause misurate**:

1. **Velocità di generazione CPU (`~16–17 tok/s`)**: su `AMD Ryzen 7 5700U` (senza GPU dedicata attiva in Ollama), ogni 68–110 token generati richiedono `4–6.5s` di solo `eval`, ai quali si sommano `~2.8s` di Whisper `small/int8` e `~0.7–1.2s` di Piper TTS.
2. **Invalidazione della KV cache a finestra piena (`+2.2s` di `prompt_eval`)**: nei turni finali di `task-3574` (`task 159`, `task 170`), raggiunti gli `8` messaggi (`4` turni), l'espulsione del turno più vecchio ha spostato il prefisso subito dopo il prompt di sistema (`163` token), costringendo Ollama a rivalutare `213–219` token (`~2.2s`) anche per risposte da `10–11` token (`ai_ms = 3.33–3.35s`).
3. **Overhead HTTP + probe per singolo turno (`~300–550ms`)**: `OllamaRouterClient` apriva un nuovo `httpx.Client` ed eseguiva `GET /api/tags` + `POST /api/chat` a ogni turno (`req_a6f3489aa5e7`: Ollama `5.61s` vs `ai_ms=6.16s`).
4. **Prompt di sistema ampio (`163` token) e `num_ctx=4096` (`144 MiB` KV cache)**: aumentavano il costo di rivalutazione prompt e l'occupazione KV in RAM.

## 2. Metriche reali osservate nella sessione `task-3588` / `task-3574`

- **Sistema durante la diagnostica**: `CPU_PCT=42`, `RAM_FREE_GB=2.54/15.39`, `VIRT_FREE_GB=1.58`, `C:\pagefile.sys CurUsageMB=321 / PeakMB=399` (nessun paging critico, nessun timeout o richiesta duplicata).
- **Turni reali registrati in `task-3588.log`**:
  - `req_ae4d8068ab18` (`Local Intent`, Test A): `stt=2812.9ms`, `ai=15.1ms`, `tts=633.5ms`, `total=3478.3ms`.
  - `req_edd6f6c11c90` (`ollama:qwen2.5:3b`): `stt=2706.9ms`, `ai=1394.2ms`, `tts=748.4ms`, `total=4862.3ms`.
  - `req_a6f3489aa5e7` (`ollama:qwen2.5:3b`, picco lento riconducibile a spiegazione): `stt=2896.2ms`, `ai=6160.3ms` (`task 90`: `prompt_eval=1635.6ms/158 tok`, `eval=3953.4ms/68 tok`, `16.95 tok/s`), `tts=1193.3ms`, `total=10270.1ms`.
  - `req_6ea722ee9c7f` / `req_4ec00cb8661a`: `ai=3348.4ms` / `3329.4ms` (`prompt_eval=2.21s/219 tok`, `eval=0.57–0.60s/10–11 tok`).

## 3. Limiti della diagnostica

- Con `JARVIS_LOG_STT_DIAG_TEXT=false` e `JARVIS_LOG_CONVERSATION_TEXT=false`, i log del Voice Bridge non salvano i testi delle trascrizioni; l'associazione al Test D si basa su ordine temporale e profilo token/latenza (`68` token, `total=10.27s`), non su testo in chiaro.

## 4. Modifiche implementate in isolamento (non ancora attive sul Voice Bridge reale)

- `05-Voice-AI/voice_bridge/conversation.py`:
  - `SYSTEM_PROMPT_IT` snellito (~80 token stimati rispetto a ~163 precedenti), mantenendo istruzioni su italiano parlato, niente markdown, 1–3 frasi brevi (2–4 per spiegazioni) e protezioni anti-injection.
  - Aggiunta `wants_detailed_reply(text)` per riconoscere richieste esplicite di approfondimento.
- `05-Voice-AI/voice_bridge/ai_router.py`:
  - `OllamaRouterClient` usa un `httpx.Client` persistente (keep-alive HTTP), cache TTL `15s` per `probe()` (disabilitata automaticamente con `MockTransport` nei test) con invalidazione immediata su errore, `num_ctx=2048` (`JARVIS_OLLAMA_NUM_CTX`), `keep_alive="10m"` (`JARVIS_OLLAMA_KEEP_ALIVE`) e supporto `max_tokens_override`.
- `05-Voice-AI/voice_bridge/config.py` e `.env.bridge.example`:
  - `ollama_max_tokens=110` (`JARVIS_OLLAMA_MAX_TOKENS`), `ollama_detail_max_tokens=180` (`JARVIS_OLLAMA_DETAIL_MAX_TOKENS`), `ollama_num_ctx=2048`, `ollama_keep_alive="10m"`, `max_history_turns=3` (`conversation_max_messages=6`), `tts_max_chars=550`.
- `05-Voice-AI/voice_bridge/pipeline.py`:
  - Passaggio di `max_tokens_override=self.config.ollama_detail_max_tokens` solo quando `wants_detailed_reply(transcript)` è vero.

## 5. Benchmark comparativo diretto (`qwen2.5:3b` su `127.0.0.1:11434`)

Eseguito dopo warm-up (`compare_latency_fase12_10.py`, 2 run per domanda):

| Domanda | Originale (`run 1` / `run 2`) | Ottimizzata (`run 1` / `run 2`) | Variazione media |
|---|---|---|---|
| **Q1** (*Chi era Leonardo da Vinci?*) | `3486ms` (39 tok) / `3574ms` (41 tok) | `9141ms`* (83 tok) / `6244ms` (103 tok) | Più lunga per risposta più estesa (con `temp=0.5`); *run 1 include cambio `num_ctx` (`prompt_eval=1287ms`) |
| **Q2** (*Spiegami come funziona un vulcano.*) | `9158ms` (113 tok) / `10374ms` (150 tok) | `6855ms` (110 tok) / `6526ms` (110 tok) | **`-31.5%`** (`9.77s` → `6.69s`) |
| **Q3** (*Quanto fa dodici per otto?*) | `1594ms` (11 tok) / `1142ms` (11 tok) | `861ms` (11 tok) / `906ms` (11 tok) | **`-35.4%`** (`1.37s` → `0.88s`) |
| **Q4** (*Spiegami più approfonditamente...*) | `10970ms` (124 tok) / `7769ms` (118 tok) | `11142ms` (180 tok) / `9497ms` (155 tok) | Più completa grazie a `detail_max_tokens=180` |

**Nota tecnica rilevata**: su Q2 la configurazione ottimizzata ha raggiunto il tetto `110` token in entrambi i run; un limite `110` può talvolta interrompere l'ultima frase se il modello non chiude prima, per cui va valutato eventualmente `120–130` token se durante il collaudo vocale si notassero chiusure brusche.

## 6. Test di regressione

Suite eseguita dopo tutte le modifiche (`test_hybrid_ai_fase12.py`, `test_esp32_ws_protocol.py`, `test_voice_bridge.py`, `test_voice_lab.py`):
- **`Ran 37 tests in 9.556s — OK`** (0 errori, 0 fallimenti; verificati comandi locali prioritari, memoria conversazionale, timeout/fallback, assenza Cloud, compatibilità WSS, troncamento TTS).

## 7. Impatto sulla memoria

- `RAM_FREE_GB` prima del benchmark: `2.02 GB` (`CPU_PCT=25`); al termine: `3.34 GB` (`CPU_PCT=14`).
- La riduzione di `num_ctx` da `4096` a `2048` dimezza la memoria KV allocata per slot (~`144 MiB` → ~`72 MiB`).

## 8. Procedura di rollback

1. Mantenere/ripristinare `JARVIS_OLLAMA_MAX_TOKENS=150`, `JARVIS_OLLAMA_NUM_CTX=4096`, `JARVIS_MAX_HISTORY_TURNS=4`, `JARVIS_TTS_MAX_CHARS=600` oppure `JARVIS_AI_MODE=DISABLED`.
2. Riavviare il Voice Bridge se erano state attivate le nuove impostazioni.

## 9. Raccomandazione finale

- Le modifiche sono pronte e validate dai 37 test automatici.
- Si raccomanda di autorizzare il **riavvio controllato del Voice Bridge** con le nuove impostazioni (eventualmente con `JARVIS_OLLAMA_MAX_TOKENS=120` per evitare tagli di fine frase su spiegazioni brevi) per eseguire la verifica acustica reale su `GPIO47`.
