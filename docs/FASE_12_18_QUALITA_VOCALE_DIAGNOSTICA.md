# FASE 12.18 — Diagnostica interruzione audio, naturalezza vocale e latenze residue

## 1. Diagnosi della risposta E (`"Jarvis, quanto fa dodici per otto?"`)

### Fatti verificati dai log (`task-3851.log` + `task-3574.log`)
- **Voice Bridge (`task-3851.log`)**:
  - `req_c3e9db197f81` (`esp-6`): `provider=ollama:qwen2.5:3b`, `fallback=False`, `dur=3.30s`, `stt=2967.5ms`, `ai=923.6ms`, `tts=676.6ms`, `total=4587.2ms`.
  - `TTS_READY pcm_bytes=59452 dur_s=1.86 max_bytes=640000 attempts=1 tts_ms=676.6`.
  - `esp-6 | WSS TTS_SENT pcm_bytes=59452 (invio completato, riproduzione lato dispositivo)`.
  - Nessun errore, nessun timeout, nessuna disconnessione WSS.
- **Ollama (`task-3574.log`, `task 1204`, `20:54:09`)**:
  - `prompt eval time = 315.39 ms / 21 tokens`, `eval time = 562.31 ms / 11 tokens` (`17.78 tok/s`), `stop processing: n_tokens = 405, truncated = 0`, `POST /api/chat 200 OK (892.07ms)`.

### Classificazione esplicita
- **A. Testo generato incompleto**: **ESCLUSO** (`11` token generati con `truncated=0`, coerente con `"Dodici per otto fa 96."`).
- **B. Testo modificato o troncato prima del TTS**: **ESCLUSO** (`attempts=1`, nessun `TTS_TEXT_REDUCED_RESYNTHESIS` né `TTS_FALLBACK_SHORT`).
- **C vs D (Audio generato incompleto vs riproduzione interrotta sull'ESP32)**: **EVIDENZA INSUFFICIENTE dai soli log** per distinguere C da D con certezza assoluta, perché il protocollo WSS v1.0 non invia un ACK di fine riproduzione I²S dall'ESP32.
  - **Ipotesi da verificare**: (1) l'ascolto di `profilo_A_1_21x.wav` (generato sullo stesso `1.21x` + `shape_piper_wav`) verifica subito se Piper+DSP chiude correttamente `"novantasei."` sul PC; (2) lato firmware ESP32 (`audio_playback.cpp`), un eventuale arresto/svuotamento anticipato del DMA I²S prima che gli ultimi frame raggiungano lo speaker può tagliare gli ultimi `~100–200ms` (strumentazione minima futura senza modificare ora il firmware: loggare sul seriale `COM6` i byte effettivamente riprodotti a fine coda rispetto a `total_bytes` di `tts_start`).

## 2. Tabella delle latenze A–E (FASE 12.17, `task-3851.log` + `task-3574.log`)

*Nota: i tempi indicano la latenza lato server (`stt_ms + ai_ms + tts_ms`) e la durata di ascolto dell'audio prodotto (`dur_s`), distinte dal tempo percepito dall'utente.*

| Test | `request_id` (`WSS`) | Provider | `stt_ms` | `ai_ms` (`Ollama tok`, `pe`/`eval`) | `tts_ms` | `total_ms` (server) | `PCM` / Durata ascolto |
|---|---|---|---|---|---|---|---|
| **A** | `req_0fd462bd86a2` (`esp-2`) | `Local Intent` | `4169.8` | `0.5` *(nessuno)* | `664.5` | `4849.7` | `62,522 B` (`1.95s`) |
| **B** | `req_41289cf0f0ae` (`esp-3`) | `ollama:qwen2.5:3b` | `2985.4` | `6385.3` (`101 tok`, `pe=245ms`, `eval=6117ms`) | `1265.9` | `10654.2` | `398,142 B` (`12.44s`) |
| **C** | `req_c41f2c7c4d21` (`esp-4`) | `ollama:qwen2.5:3b` | `2897.1` | `1070.1` (`15 tok`, `pe=282ms`, `eval=773ms`) | `775.7` | `4753.2` | `107,016 B` (`3.34s`) |
| **D** | `req_634fee3b7504` (`esp-5`) | `ollama:qwen2.5:3b` | `2999.7` | `7552.8` (`120 tok`, `pe=355ms`, `eval=7183ms`) | `1410.6` | `11983.4` | `450,690 B` (`14.08s`) |
| **E** | `req_c3e9db197f81` (`esp-6`) | `ollama:qwen2.5:3b` | `2967.5` | `923.6` (`11 tok`, `pe=315ms`, `eval=562ms`) | `676.6` | `4587.2` | `59,452 B` (`1.86s`) |

## 3. Confronto con la FASE 12.16

- **Pre-warm & `keep_alive=30m`**: confermato efficace — **0 ricaricamenti a freddo** in B (`ai_ms` sceso da **`9087.4ms`** in 12.16 a **`6385.3ms`** in 12.17 nonostante `101` token vs `76`; `total_ms` da **`13625.6ms`** a **`10654.2ms`**).
- **STT (`beam_size=1`)**: su audio reale da microfono `stt_ms` è sceso leggermente da `~3050ms` a `~2960–3000ms` (circa `-50 / -100ms`), meno marcato rispetto al benchmark sintetico.
- **Latenze residue B (`10.65s`) e D (`11.98s`)**: dovute principalmente alla velocità CPU di `qwen2.5:3b` (`~16.5 tok/s` su `101–120` token → `6.1–7.2s` di generazione) + `~3.0s` di Whisper `small/int8`.

## 4. Benchmark isolato dei tre profili vocali ("JARVIS Amichetto")

Parametri invariati: `it_IT-riccardo-x_low.onnx`, `pitch=+5.0st`, `noise_scale=1.10`, `robot_mix=0.0`, `shape_piper_wav` (`tanh`), `16000 Hz` mono 16-bit PCM.

| Profilo | Matematica (30 ch) | Conversazionale (76 ch) | Scientifica (227 ch) | Punteggiatura (100 ch) | Clipping | > 640 KB |
|---|---|---|---|---|---|---|
| **A (`1.21x`, `0.826`)** | `1.99s` / `63,672 B` / `663.6ms` | `4.71s` / `150,742 B` / `825.3ms` | `12.85s` / `411,184 B` / `1289.4ms` | `5.97s` / `191,016 B` / `878.7ms` | `0` | `False` |
| **B (`1.10x`, `0.909`)** | `2.22s` / `70,960 B` / `660.0ms` | `5.08s` / `162,632 B` / `846.3ms` | `13.11s` / `419,622 B` / `1312.2ms` | `6.48s` / `207,510 B` / `892.3ms` | `0` | `False` |
| **C (`1.00x`, `1.000`)** | `2.13s` / `68,274 B` / `645.7ms` | `5.53s` / `176,824 B` / `889.7ms` | `13.14s` / `420,390 B` / `1326.7ms` | `6.78s` / `217,098 B` / `1038.2ms` | `0` | `False` |

## 5. Percorsi dei WAV di ascolto generati sul PC

- Profilo A (`1.21x`): `05-Voice-AI/tts-lab/samples_fase12_18/profilo_A_1_21x.wav`
- Profilo B (`1.10x`): `05-Voice-AI/tts-lab/samples_fase12_18/profilo_B_1_10x.wav`
- Profilo C (`1.00x`): `05-Voice-AI/tts-lab/samples_fase12_18/profilo_C_1_00x.wav`

## 6. Rischi sul limite PCM (`640,000` byte / `20.0s`)

- Su tutti e tre i profili (`1.21x`, `1.10x`, `1.00x`), frasi fino a `227` caratteri restano ampiamente sotto il limite (`411–420 KB`, `12.85–13.14s`).
- Il passaggio da `1.21x` a `1.10x` o `1.00x` aumenta la dimensione PCM della frase scientifica solo del `+2.1% / +2.2%`, e la protezione `TTS_TOO_LONG` (`JARVIS_TTS_MAX_CHARS=300` + riduzione su frasi complete + fallback breve) resta pienamente efficace.

## 7. Raccomandazione motivata per il prossimo intervento

1. **Ascolto umano dei tre WAV** per scegliere la velocità preferita (`1.10x` o `1.00x` per maggiore naturalezza, lasciando invariati `pitch=+5.0st` e `tanh`) e verificare contestualmente se su `profilo_A_1_21x.wav` la parola finale `"novantasei."` è integra (distinguendo così causa C vs causa D sull'interruzione della risposta E).
2. Se `profilo_A_1_21x.wav` risulta integro al PC ma sul robot l'ultima sillaba continua a risultare tagliata, prevedere nella fase successiva (solo previa autorizzazione) un breve tail-padding/drain I²S sul firmware ESP32.
