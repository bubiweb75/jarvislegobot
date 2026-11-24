# FASE 12.19 — Attivazione profilo vocale B (`1.10x`) e verifica integrità audio

## 1. Diagnostica comparativa WAV A / B / C (prima e dopo DSP)

Analisi dei campioni della FASE 12.18 (`profilo_A_1_21x.wav`, `profilo_B_1_10x.wav`, `profilo_C_1_00x.wav`) e confronto diretto **raw Piper vs post-DSP `shape_piper_wav`** su `"Dodici per otto fa novantasei."` e sulla frase finale (`"Certo, ascolta bene: prima osserviamo i dati; poi, con calma, decidiamo insieme il passo successivo."`):

- **Campioni salvati (`16000 Hz`, mono, 16-bit PCM)**:
  - `profilo_A_1_21x.wav` (`864,658 B`, `27.019s`): coda di silenzio finale `375.8 ms` (`last50ms_rms=0`, `last50ms_peak=0`).
  - `profilo_B_1_10x.wav` (`908,768 B`, `28.398s`): coda di silenzio finale `342.8 ms` (`last50ms_rms=0`, `last50ms_peak=0`).
  - `profilo_C_1_00x.wav` (`930,630 B`, `29.081s`): coda di silenzio finale `345.7 ms` (`last50ms_rms=0`, `last50ms_peak=0`).
- **Confronto prima/dopo DSP su `"Dodici per otto fa novantasei."` (`B_1.10x`)**:
  - Raw Piper: `dur=1.912s`, `last_active=1.483s`, coda silenzio `428.6 ms` (`last50ms_peak=0`).
  - Post-DSP (`shape_piper_wav`): `dur=1.894s`, `last_active=1.513s`, coda silenzio `380.6 ms` (`last50ms_peak=0`).
- **Conclusione sull'integrità**: né `shape_piper_wav` né il salvataggio/concatenazione WAV hanno tagliato la fine delle frasi (`322–428 ms` di silenzio pulito in coda su tutti i profili). Non è stata necessaria alcuna coda artificiale di silenzio.
- **WAV di controllo isolato (`B 1.10x`, `"Dodici per otto fa novantasei."`)**:
  - `05-Voice-AI/tts-lab/samples_fase12_18/controllo_B_1_10x_novantasei.wav` (`65,250 B`, `2.038s`, `tail_sil=422.6ms`, `last50ms_peak=0`, `clipped=0`).

## 2. Configurazione vocale finale attiva (Profilo B)

- `JARVIS_TTS_PIPER_SPEED=1.10` (`length_scale=0.909`)
- `JARVIS_TTS_PIPER_NOISE_SCALE=1.10`
- `JARVIS_TTS_PIPER_PITCH_SEMITONES=5.0`
- `JARVIS_TTS_PIPER_ROBOT_MIX=0.0`
- `JARVIS_TTS_PIPER_DSP_ENABLED=true` (`RMS maximizer + soft-limiter tanh`)
- `JARVIS_TTS_MAX_CHARS=300`, limite PCM ESP32 `640,000 B` (`20.0s`) invariato.
- Parametri AI/STT invariati: `LOCAL_ONLY`, `qwen2.5:3b`, `keep_alive=30m`, pre-warm attivo, `120`/`180` token, `4` turni, `beam_size=1`, Cloud disabilitato.

## 3. Risultati test automatici

Suite (`test_fase12_15b_tts_amichetto.py`, `test_hybrid_ai_fase12.py`, `test_esp32_ws_protocol.py`, `test_voice_bridge.py`, `test_voice_lab.py`):
- **`Ran 43 tests in 4.249s — OK`** (inclusa verifica `speed=1.10x`, `pitch=+5.0st`, `"Dodici per otto fa novantasei."` con `0` clipping e coda di silenzio pulita negli ultimi `50ms`, limite `640,000 B` e `TTS_TOO_LONG`).

## 4. Stato dei servizi post-riavvio

- **Voice Bridge**: `PID 15444` (`task-3886`) su `https://<PC_LAN_IP>:8765`, `Ollama prewarm ok model=qwen2.5:3b keep_alive=30m ms=43.9`.
  - `/health`: `200 OK`
  - `/ready`: `200 OK`, `tts`: `Piper pronto (it_IT-riccardo-x_low.onnx, 16000 Hz, speed=1.10x, pitch=+5.0st, dsp=on)`
- **Ollama**: `PID 18024` (`task-3574`) attivo su `127.0.0.1:11434` (non riavviato).
- **ESP32-S3 (`<ESP32_LAN_IP>`)**: riconnesso automaticamente via WSS.

## 5. Istruzioni per il collaudo fisico (`GPIO47`)

Eseguire sul robot le tre prove richieste:
- **A**: *"Jarvis, quanto fa dodici per otto?"* — verificare che *"novantasei"* sia completa.
- **B**: *"Jarvis, chi era Leonardo da Vinci?"* — valutare naturalezza e velocità a `1.10x`.
- **C**: *"Jarvis, spiegami come funziona un vulcano."* — verificare fluidità e assenza di interruzioni.
