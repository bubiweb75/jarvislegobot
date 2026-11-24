# FASE 12.16 — Regolazione volume e diagnostica latenze

## 1. Stato della regolazione volume

- **Verifica firmware**: `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/jarvis_wifi_voice_client.ino` supporta `VOL 1..25` a `115200` baud (non persistente al riavvio).
- **Porta rilevata**: `USB-Enhanced-SERIAL CH343 (COM6)` (`USB\VID_1A86&PID_55D3\5C83027497`, `Status=OK`).
- **Stato invio**: comando `VOL 12` inviato a `115200` baud su `COM6`; risposta firmware verificata: `[AUDIO] Volume impostato a 12%`; porta chiusa (`COM6_CLOSED=True`). Il volume `12%` è **temporaneo** (non persistente su NVS/Flash: al prossimo riavvio tornerà al default firmware `10%`).

## 2. Tabella delle latenze misurate (`task-3792.log` + `task-3574.log`)

*Nota: i tempi seguenti sono latenze lato server (`Voice Bridge` + `Ollama`); il tempo percepito dall'utente include inoltre la fine della pressione su `GPIO47`, il trasferimento audio WSS e l'inizio riproduzione sull'ESP32.*

| Test | `request_id` (`WSS`) | Provider | `dur` audio | `stt_ms` | `ai_ms` (`Ollama tok`) | `tts_ms` (Piper+DSP) | `total_ms` | `PCM` / Durata | Tentativi |
|---|---|---|---|---|---|---|---|---|---|
| **A** | `req_0e583c481f7a` (`esp-24`) | `Local Intent` | `2.56s` | `4366.3` | `0.8` | `607.9` | `4989.2` | `56,384 B` (`1.76s`) | `1` |
| **B** | `req_87c28213d6fd` (`esp-25`) | `ollama:qwen2.5:3b` | `2.99s` | `3050.6` | `9087.4` (`76 tok`, `16.83 tok/s`) | `1467.9` | `13625.6` | `444,938 B` (`13.90s`) | `1` |
| **C** | `req_7eb5de2ed588` (`esp-26`) | `ollama:qwen2.5:3b` | `2.18s` | `2921.4` | `1398.9` (`20 tok`, `17.42 tok/s`) | `768.5` | `5103.4` | `125,810 B` (`3.93s`) | `1` |
| **D** | `req_3e35974b18fb` (`esp-27`) | `ollama:qwen2.5:3b` | `3.82s` | `3081.4` | `7454.5` (`120 tok`, `16.82 tok/s`) | `1335.6` | `11899.9` | `360,170 B` (`11.26s`) | `1` |
| **E** | `req_51fc27b675b4` (`esp-28`) | `ollama:qwen2.5:3b` | `3.38s` | `2989.9` | `1007.8` (`11 tok`, `16.94 tok/s`) | `633.6` | `4652.3` | `60,604 B` (`1.89s`) | `1` |

*(Il tempo interno di DSP `shape_piper_wav` è incluso in `tts_ms`; nel benchmark isolato FASE 12.15B era ~`257ms` su 436 char.)*

## 3. Analisi della prova D e verifica protezione `TTS_TOO_LONG`

- Eventi registrati per `req_3e35974b18fb` (`esp-27`):
  - `TTS_PCM_LIMIT_EXCEEDED`: **non verificato**
  - `TTS_TEXT_REDUCED_RESYNTHESIS`: **non verificato**
  - `TTS_FALLBACK_SHORT`: **non verificato**
  - `TTS_READY`: **`pcm_bytes=360170 dur_s=11.26 max_bytes=640000 attempts=1 tts_ms=1335.6`**
  - `WSS TTS_SENT`: **`esp-27 | WSS TTS_SENT pcm_bytes=360170`**
- **Esito**: la risposta D è stata sintetizzata normalmente al **primo tentativo (`attempts=1`)** e nessun audio superiore a `640,000` byte è stato inviato all'ESP32. La combinazione `JARVIS_TTS_MAX_CHARS=300` + `1.21x` ha mantenuto l'audio a `11.26s` (`360 KB`), eliminando `TTS_TOO_LONG`.
- **Causa della lentezza di D (`11.90s` server)**:
  - `ai_ms = 7454.5ms` (`62.6%` del totale) per generazione di **`120` token** a `16.82 tok/s` (`7075.2ms` eval + `345.9ms` prompt_eval su `24` token).
  - `stt_ms = 3081.4ms` (`25.9%` del totale).
  - `tts_ms = 1335.6ms` (`11.2%` del totale).
- **Causa della lentezza di B (`13.63s` server)**:
  - `task-3574.log` (`20:37:58`) mostra che `qwen2.5:3b` si era scaricato dalla RAM dopo 15 minuti di inattività (`keep_alive=10m` scaduto dalle `20:22:44`), causando **`3.27s` di ricaricamento `llama-server`** + `1.24s` `prompt_eval` (118 token a freddo) + `4.46s` `eval` (76 token) = `9.07s` solo per Ollama (`ai_ms=9087.4ms`).

## 4. Confronto con le fasi precedenti

- **Test A (`Local Intent`)**: `5.12s` (12.13) → `4.99s` (12.15B), stabile (`~4.4s` primo turno freddo Whisper).
- **Test B (`Leonardo da Vinci`)**: `7.15s` (12.13, modello caldo, 46 tok) → `13.63s` (12.15B, modello ricaricato a freddo + 76 tok).
- **Test C (`Quando è nato?`)**: `5.31s` (12.13) → **`5.10s`** (12.15B, hit completo KV cache, `ai=1.40s`).
- **Test D (`Vulcano`)**: `12.09s` + **FAIL** `TTS_TOO_LONG` (12.13) → **`11.90s` + audio consegnato `11.26s`** (12.15B).
- **Test E (`12 × 8`)**: `4.63s` (12.13) → **`4.65s`** (12.15B).

## 5. Classifica delle ottimizzazioni consigliate (senza sacrificare "JARVIS Amichetto")

| Priorità | Intervento | Beneficio stimato / misurato | Complessità / Rischio |
|---|---|---|---|
| **1** | **Pre-warm Ollama allo startup del Voice Bridge + `keep_alive=30m`** (o `15m`) | Elimina i `~4.5s` di ricaricamento a freddo osservati nel Test B (`13.63s` → ~`8.5s` attesi) | Bassa / Rischio minimo (richiede ~1.9 GB RAM tenuti caldi) |
| **2** | **Ridurre `JARVIS_OLLAMA_MAX_TOKENS` da `120` a `85–95`** per risposte ordinarie | Riduce `eval` su spiegazioni tipo D da `~7.1s` (120 tok) a ~`5.0–5.5s` (85–95 tok) → **`-1.5 / -2.0s` attesi** | Bassa / Rischio basso (180 token resta su richiesta esplicita) |
| **3** | **Valutare STT `faster-whisper` `base` vs `small` oppure `compute_type` / `beam_size=1`** | Whisper `small` (`beam_size=3`) pesa fissamente **`~2.9–3.1s`** su ogni turno (`57%` di C, `64%` di E); `beam_size=1` può ridurre STT senza cambiare modello | Media / Da testare per non perdere accuratezza italiana |
| **4** | **Valutare modello Ollama più leggero (es. `qwen2.5:1.5b`)** | Raddoppierebbe ~`tok/s` su CPU (`~30+ tok/s`), dimezzando `ai_ms` | Media / Richiede download e verifica qualità italiano |

## 6. Proposta per la prossima fase

1. Completare la regolazione temporanea **`VOL 12`** su `COM6` appena confermata la connessione USB dall'utente.
2. Nella fase successiva (previa autorizzazione): implementare **Priorità 1 (pre-warm Ollama + `keep_alive=30m`)** e **Priorità 2 (`JARVIS_OLLAMA_MAX_TOKENS=90`)**, mantenendo invariati Whisper `small`, Piper + DSP "JARVIS Amichetto", `num_ctx=2048` e limite `640,000` B.
