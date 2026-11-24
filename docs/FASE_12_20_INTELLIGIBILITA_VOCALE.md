# FASE 12.20 — Miglioramento intelligibilità e naturalezza della voce

## 1. Analisi della catena audio (`Testo → Piper → DSP → PCM → WSS → ESP32 → I²S`)

- **Nessuna accelerazione involontaria**:
  - `it_IT-riccardo-x_low.onnx` genera nativamente a `16000 Hz` mono PCM16.
  - `shape_piper_wav()` (`voice_dsp.py`) applica il phase vocoder per `1/factor` e ricampiona linearmente per `factor`, mantenendo esattamente la durata e la frequenza `16000 Hz`.
  - `validate_and_normalize_wav()` non ricampiona (`16000 Hz == 16000 Hz`).
  - `esp_protocol.py` invia `sr=16000, ch=1, bits=16` e `AudioPlayback` su ESP32 inizializza `I2S_NUM_1` a `16000 Hz`.
- **Cause tecniche dell'effetto *"si mangia le parole"***:
  1. **Modello `x_low` + `speed=1.10x` (`length_scale=0.909`)**: `it_IT-riccardo-x_low` è un modello VITS leggero che già a velocità > `1.00x` tende a fondere le sillabe atone; con `noise_scale=1.10` (rispetto al default `0.667`) aumenta la variabilità prosodica.
  2. **Phase vocoder STFT (`n_fft=1024`, `hop=256`, finestra `64 ms` a `16 kHz`)** per il pitch shifting a `+5.0` semitoni (`factor=1.335`): una finestra da `64 ms` spande leggermente i transienti consonantici rapidi (`t`, `p`, `k`, `d`, `r`), attenuando la nitidezza delle consonanti ravvicinate; riducendo il pitch (`+3` o `0` semitoni) questo *transient smearing* diminuisce o scompare del tutto.
  3. **RMS maximizer + soft-limiter `tanh`**: alza i livelli delle parti più deboli (`rms ~11100`), rendendo il parlato molto denso senza attenuazioni naturali.

## 2. Benchmark comparativo dei quattro profili (testo da 285 caratteri)

Testo identico contenente consonanti ravvicinate, parole lunghe, numeri (`1452`), nome proprio (`Leonardo da Vinci`), pause/punteggiatura e spiegazione scientifica (`noise_scale=1.10`, `robot_mix=0.0`, `tanh` attivo, `16000 Hz` mono PCM16):

| Profilo | Speed / Pitch | Tempo sintesi | Durata | Dimensione PCM | RMS / Picco | Clipping | Silenzio finale | > 640 KB |
|---|---|---|---|---|---|---|---|---|
| **A — Attuale** | `1.10x` / `+5.0 st` | `1648.6 ms` | `18.23 s` | `583,404 B` | `11142` / `31455` | `0` | `314.8 ms` | `False` |
| **B — Più lento** | `1.00x` / `+5.0 st` | `1762.8 ms` | `18.85 s` | `603,350 B` | `11049` / `31456` | `0` | `261.6 ms` | `False` |
| **C — Pitch ridotto** | `1.00x` / `+3.0 st` | `1639.1 ms` | `18.85 s` | `603,186 B` | `7986` / `31456` | `0` | `239.2 ms` | `False` |
| **D — Naturale** | `1.00x` / `0.0 st` | `1602.4 ms` | `19.20 s` | `614,400 B` | `11234` / `30570` | `0` | `336.9 ms` | `False` |

## 3. Percorsi dei WAV di ascolto (FASE 12.20)

- **Profilo A (`1.10x`, pitch `+5`)**: `05-Voice-AI/tts-lab/samples_fase12_20/profilo_A_attuale_1_10x_pitch5.wav`
- **Profilo B (`1.00x`, pitch `+5`)**: `05-Voice-AI/tts-lab/samples_fase12_20/profilo_B_1_00x_pitch5.wav`
- **Profilo C (`1.00x`, pitch `+3`)**: `05-Voice-AI/tts-lab/samples_fase12_20/profilo_C_1_00x_pitch3.wav`
- **Profilo D (`1.00x`, pitch `0`)**: `05-Voice-AI/tts-lab/samples_fase12_20/profilo_D_naturale_1_00x_pitch0.wav`

## 4. Diagnostica della risposta lenta B (collaudo FASE 12.19, `task-3886` + `task-3574`)

Richiesta **Leonardo da Vinci** (`req_497e49c82fbc` / `esp-9`, `task 1240` alle `21:05:05`):
- **STT (`small/int8`, `beam_size=1`)**: `2951.6 ms` (`dur=3.14s`).
- **Caricamento modello Ollama**: **`0 ms`** (modello già caldo grazie al pre-warm + `keep_alive=30m`).
- **Ollama (`qwen2.5:3b`)**: `ai_ms = 5716.6 ms` (`prompt_eval = 295.08 ms` / `18` tok, `eval = 5406.94 ms` / `93` tok @ `17.02 tok/s`).
- **TTS (Piper + DSP)**: `1583.9 ms`.
- **Tempo totale server prima dell'inizio risposta**: **`10270.1 ms`** (`10.27 s`).
- **Durata di ascolto dell'audio prodotto**: **`18.36 s`** (`587,624` byte PCM, `attempts=1`, `WSS TTS_SENT`).

## 5. Rischi relativi al limite PCM (`640,000` byte / `20.0s`)

- A `1.00x` (`B`, `C`, `D`), `285` caratteri producono `603,186–614,400` byte (`18.85–19.20s`), arrivando fino al **96% del limite `640,000 B`**.
- Se l'utente sceglierà `1.00x`, sarà consigliabile abbassare leggermente `JARVIS_TTS_MAX_CHARS` da `300` a **`260–270`** (oltre alla protezione automatica `TTS_TOO_LONG` già attiva su frasi complete).

## 6. Raccomandazione tecnica

- **Profilo C (`1.00x`, pitch `+3.0` semitoni)** o **Profilo D (`1.00x`, pitch `0.0`)** rappresentano il miglior compromesso tecnico per ridurre lo smearing del phase vocoder preservando consonanti nitide (nel caso di C mantenendo comunque una sfumatura più giovanile di Riccardo). La scelta finale spetta all'ascolto umano dell'utente sui quattro WAV.
