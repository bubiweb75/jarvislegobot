# FASE 12.14 — Diagnostica end-to-end del collaudo vocale e analisi del fallimento delle spiegazioni

## 1. Stato iniziale (sola lettura)

- **Voice Bridge attivo**: `PID 12080` (`task-3723`) su `<PC_LAN_IP>:8765`, `/health` `200 OK`, `/ready` `200 OK` (`stt=True`, `tts=True`, `ollama=True`, `cloud=False`).
- **Ollama attivo**: `PID 18024` (`task-3574`) su `127.0.0.1:11434`, modello `qwen2.5:3b`.
- **ESP32-S3 (`<ESP32_LAN_IP>`)**: connesso via WSS (`connection open`).
- **Risorse PC**: `RAM_FREE_GB=2.98/15.39`, `VIRT_FREE_GB=2.10`, `CPU_PCT=17`, `C:\pagefile.sys CurUsageMB=931 / PeakMB=974`.

## 2. Tabella dei cinque turni identificati (`task-3723.log` + `task-3574.log`)

| Test | `request_id` (`task-3723`) | Provider | `dur` | `stt_ms` | `ai_ms` | `tts_ms` | `total_ms` | Ollama (`task-3574`) |
|---|---|---|---|---|---|---|---|---|
| **A** | `req_09eaf1358923` | `Local Intent` | `2.58s` | `4468.4` | `0.7` | `634.3` | `5118.1` | *(non chiamato)* |
| **B** | `req_74115bdb3dd8` | `ollama:qwen2.5:3b` | `3.34s` | `3178.6` | `2949.1` | `1002.1` | `7148.5` | `task 1484` (`20:21:43`): `pe=12 tok/264ms`, `eval=46 tok/2639ms` (`17.05 tok/s`) |
| **C** | `req_cc10ce00334f` | `ollama:qwen2.5:3b` | `1.82s` | `2910.1` | `1450.1` | `937.4` | `5307.7` | `task 1531` (`20:22:04`): `pe=15 tok/272ms`, `eval=20 tok/1148ms` (`16.55 tok/s`) |
| **D** | `req_381e72b0cbe7` | `ollama:qwen2.5:3b` | `3.70s` | `3116.0` | `7372.4` | `1586.7` | `12094.7` | `task 1552` (`20:22:26`): `pe=24 tok/341ms`, `eval=117 tok/7018ms` (`16.53 tok/s`) |
| **E** | `req_a13292a977b6` | `ollama:qwen2.5:3b` | `4.11s` | `2988.8` | `924.4` | `696.9` | `4634.6` | `task 1670` (`20:22:44`): `pe=21 tok/329ms`, `eval=11 tok/557ms` (`17.95 tok/s`) |

## 3. Diagnosi del Test D (`req_381e72b0cbe7` → FAIL)

### Tracciamento passo-passo
1. **Audio ricevuto e STT**: sì (`dur=3.70s`, `stt=3116.0ms`).
2. **Ollama**: sì (`task 1552`, `eval=117` token `< 120`, `7018.0ms`, `POST /api/chat 200 OK`). Non ha raggiunto il cap di 120 token.
3. **Piper TTS**: sì (`tts=1586.7ms`), `process_voice()` ha completato e loggato `Voice turn ok`.
4. **Test diagnostico isolato (`diag_fase12_14_isolated.py`)**:
   - Un testo italiano di `436` caratteri (~`115` token, **sotto** `JARVIS_TTS_MAX_CHARS=550`) sintetizzato da `PiperTTSEngine` (`it_IT-riccardo-x_low.onnx`) ha richiesto `1683.5ms` e prodotto **`825,600` byte PCM (`25.80` secondi @ 16kHz)**!
   - Piper italiano parla a circa **`16.9` caratteri/secondo** (`436 / 25.80`).
5. **Causa tecnica individuata (`esp_protocol.py` + `JARVIS_TTS_MAX_CHARS`)**:
   - Il limite del buffer audio su ESP32-S3 (`esp_max_tts_bytes`) è **`640,000` byte** (**`20.0` secondi**).
   - In `esp_protocol.py` (riga 267), subito dopo `process_voice()`, se `len(out_pcm) > 640000`, l'adattatore invia al client `{"type": "error", "code": "TTS_TOO_LONG", ...}` **senza loggare nulla nel log del Voice Bridge** e **senza inviare audio**.
   - Con `JARVIS_TTS_MAX_CHARS=550` (equivalenti a `~32.5` secondi di audio Piper!), qualunque spiegazione tra `~340` e `550` caratteri supera `640,000` byte PCM e viene bloccata da `TTS_TOO_LONG` prima dell'invio WSS!
   - Questo spiega perfettamente perché D ha fallito sia in FASE 12.11 (`tts=1630.9ms`, `120` tok) sia in FASE 12.13 (`tts=1586.7ms`, `117` tok), mentre in FASE 12.9 (`68` tok, `tts=1193.3ms`) era rimasto sotto i `20s`.

### Limite diagnostico dei log
- `esp_protocol.py` non logga `TTS_TOO_LONG` nel log server e il protocollo WSS v1.0 non prevede un ACK di fine riproduzione dall'ESP32. Inoltre `JARVIS_LOG_CONVERSATION_TEXT=false` impedisce di leggere la lunghezza esatta in caratteri di `req_381e72b0cbe7`.

## 4. Analisi della lentezza di B (`7.15s`) e C (`5.31s`)

- **KV cache 100% preservata**: con `JARVIS_MAX_HISTORY_TURNS=4`, tutti i turni B → C → D → E hanno ottenuto **hit completo della KV cache** (`prompt_eval` solo `12–24` token, `264–341ms`). Nessun ricaricamento modello e nessuna invalidazione KV cache.
- **Scomposizione reale dei tempi**:
  - **Test B (`7148.5ms`)**: `stt=3178.6ms` (`44.5%`), `ai=2949.1ms` (`41.3%`, `46` token), `tts=1002.1ms` (`14.0%`).
  - **Test C (`5307.7ms`)**: `stt=2910.1ms` (`54.8%`), `ai=1450.1ms` (`27.3%`, `20` token), `tts=937.4ms` (`17.7%`).
- **Conclusione su B e C**: in C l'AI impiega solo `1.45s`; oltre la metà della latenza (`2.91s`) è dovuta a Whisper `small/int8` su CPU. In B si sommano `3.18s` di Whisper + `2.64s` di generazione Ollama (46 token a `17 tok/s`) + `1.00s` di Piper.

## 5. Confronto delle soluzioni (non implementate in questa fase)

| Soluzione | Evidenze a favore | Benefici attesi | Rischi | Modifiche necessarie |
|---|---|---|---|---|
| **A — Correzione mirata pipeline (`tts_max_chars` + logging `TTS_TOO_LONG` + `num_predict` coerente)** | `diag_fase12_14_isolated.py` dimostra che `436` char = `825,600 B` (`> 640,000 B`) | Elimina `TTS_TOO_LONG` su spiegazioni come Test D; rende visibili gli errori WSS nei log | Risposte tagliate a ~`310` char (~18s) se il prompt non guida a 2 frasi brevi | `tts_max_chars=300` (o taglio basato su durata PCM <= `20s`), log `WARNING` in `esp_protocol.py`, `ollama_max_tokens=90` |
| **B — Riduzione latenza AI** | Su CPU `17 tok/s` ogni 30 token sono `~1.8s` | Riduce `ai_ms` su B e D | Risposte più sintetiche | `ollama_max_tokens=85–90` + prompt "massimo 2 frasi (~250 caratteri)" |
| **C — Gestione differente spiegazioni** | `esp_max_tts_bytes=640000` (20s) su ESP32 limita il turno singolo | Spiegazioni lunghe non sforano il buffer ESP32 | Richiede chunking/streaming multi-messaggio se si vogliono >20s | Oppure sintesi in 2 frasi brevi + invito ad approfondire |
| **D — Ripristino FASE 12.9** | In FASE 12.9 Test D aveva `68` tok (`tts=1193ms`) | Riduce probabilità di `>20s` ma non garantisce il rispetto di `640,000 B` | Il bug `tts_max_chars=600 > 20s` resterebbe latente | Nessun fix strutturale |

## 6. Raccomandazione tecnica per la FASE 12.15

Applicare una **correzione mirata combinata (A + B)**:
1. Allineare `JARVIS_TTS_MAX_CHARS=300` (~`17.7s` di audio Piper, sicuro sotto `640,000` byte / `20.0s`) **e/o** verificare in `pipeline.py`/`esp_protocol.py` che l'audio TTS non superi `esp_max_tts_bytes`, loggando esplicitamente `TTS_TOO_LONG` in `esp_protocol.py`.
2. Aggiornare `SYSTEM_PROMPT_IT` e `JARVIS_OLLAMA_MAX_TOKENS=90` per risposte ordinarie da **1–2 frasi (~200–280 caratteri)**, riducendo sia `ai_ms` (B e D più veloci di ~1–2s) sia il rischio di superare `20.0s` di audio sull'ESP32.
