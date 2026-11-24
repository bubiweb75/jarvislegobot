# FASE 12.15B — Ripristino voce JARVIS Amichetto + correzione TTS_TOO_LONG

## 1. File modificati (backup in `scratch/backup_fase12_15b/`)

- `05-Voice-AI/voice_bridge/config.py`: aggiunti `tts_piper_speed=1.21`, `tts_piper_noise_scale=1.10`, `tts_piper_pitch_semitones=5.0`, `tts_piper_robot_mix=0.0`, `tts_piper_dsp_enabled=True`; `tts_max_chars=300`.
- `05-Voice-AI/voice_bridge/tts_engine.py`: `PiperTTSEngine` passa `--length_scale 0.826` (`1.0 / 1.21`) e `--noise_scale 1.10` a Piper CLI, riutilizza `shape_piper_wav()` da `05-Voice-AI/voice_dsp.py` (pitch `+5.0` semitoni, `robot_mix=0.0`, RMS maximizer + soft-limiter `tanh`, `volume=100`, applicato una sola volta) e normalizza a `16000 Hz` mono PCM16.
- `05-Voice-AI/voice_bridge/pipeline.py`: verifica effettiva dei byte PCM (`_measure_wav_pcm`), riduzione testuale su frasi complete (`_reduce_tts_text_for_limit`, max 2 tentativi di risintesi senza chiamate AI aggiuntive), fallback vocale breve (`"La risposta è troppo lunga. Chiedimi una versione più breve."`), logging strutturato (`TTS_PCM_LIMIT_EXCEEDED`, `TTS_TEXT_REDUCED_RESYNTHESIS`, `TTS_FALLBACK_SHORT`, `TTS_FINAL_ERROR`, `TTS_READY`).
- `05-Voice-AI/voice_bridge/esp_protocol.py`: aggiunti log strutturati `WSS TTS_TOO_LONG` e `WSS TTS_SENT` (distinguendo invio WebSocket da riproduzione su dispositivo).
- `05-Voice-AI/voice_bridge/.env.bridge.example`: documentati tutti i nuovi parametri `JARVIS_TTS_*`.
- `05-Voice-AI/tests/test_fase12_15b_tts_amichetto.py`: nuovi test dedicati.

## 2. Parametri vocali definitivi ("JARVIS Amichetto")

| Parametro | Valore attivo |
|---|---|
| Modello Piper | `it_IT-riccardo-x_low.onnx` |
| Velocità (`JARVIS_TTS_PIPER_SPEED`) | `1.21x` (`--length_scale 0.826`) |
| `JARVIS_TTS_PIPER_NOISE_SCALE` | `1.10` |
| Pitch DSP (`JARVIS_TTS_PIPER_PITCH_SEMITONES`) | `+5.0` semitoni (`voice_dsp.shape_piper_wav`) |
| `JARVIS_TTS_PIPER_ROBOT_MIX` | `0.0` |
| Normalizzazione (`JARVIS_TTS_PIPER_DSP_ENABLED=true`) | RMS maximizer + soft-limiter `tanh` |
| Formato finale ESP32 | `16000 Hz`, mono, signed 16-bit PCM |
| `JARVIS_TTS_MAX_CHARS` | `300` |
| Limite hardware/WSS ESP32 (`esp_max_tts_bytes`) | `640,000` byte (`20.0s`, invariato) |

Configurazione AI invariata: `JARVIS_AI_MODE=LOCAL_ONLY`, `qwen2.5:3b`, `120` token standard / `180` approfondimenti, `4` turni, `num_ctx=2048`, `keep_alive=10m`, Cloud e fallback disabilitati.

## 3. Test automatici eseguiti

Suite (`test_fase12_15b_tts_amichetto.py`, `test_hybrid_ai_fase12.py`, `test_esp32_ws_protocol.py`, `test_voice_bridge.py`, `test_voice_lab.py`):
- **`Ran 42 tests in 4.566s — OK`** (0 errori, 0 fallimenti).
- Verificati: parametri Piper + DSP reali su testo breve italiano (`16000 Hz`, mono, 16-bit, `0` clipping), limite esatto `640,000` B, audio vuoto (`TTS_FAILED`), riduzione su frasi complete e testo senza punteggiatura, fallback vocale breve senza retry infiniti, `TTS_TOO_LONG` esplicito se anche il fallback supera il limite, compatibilità WSS, memoria conversazionale, comandi locali e `LOCAL_ONLY` senza Cloud.

## 4. Benchmark audio isolato (prima/dopo su 436 caratteri e su testo breve)

| Configurazione | Tempo sintesi+DSP | Durata | Dimensione PCM | RMS / Picco | Clipping |
|---|---|---|---|---|---|
| **Piper originale senza DSP** (436 char) | `1878.5 ms` | `25.72 s` | `823,040 B` | `6797` / `32767` | `3` |
| **JARVIS Amichetto integrato** (436 char) | `2188.4 ms` | `23.69 s` | `757,928 B` | `11330` / `31455` | `0` |
| **JARVIS Amichetto testo breve** (51 char) | `796.5 ms` | `3.74 s` | `119,672 B` | `6268` / `31456` | `0` |

## 5. Stato finale post-riavvio

- **Voice Bridge**: `PID 4864` (`task-3792`), singola istanza su `<PC_LAN_IP>:8765`, `/health` `200 OK`, `/ready` `200 OK` (`stt=True`, `tts=Piper pronto (it_IT-riccardo-x_low.onnx, 16000 Hz, speed=1.21x, pitch=+5.0st, dsp=on)`, `ollama=True`, `cloud=False`).
- **Ollama**: `PID 18024` (`task-3574`) attivo su `127.0.0.1:11434` con `qwen2.5:3b` (non riavviato).
- **ESP32-S3 (`<ESP32_LAN_IP>`)**: riconnesso automaticamente via WSS (`<ESP32_LAN_IP>:50429 - "WebSocket /ws/v1/esp32" [accepted]`, `connection open`).

## 6. Problemi residui / note per il collaudo

- La normalizzazione `tanh` aumenta il livello RMS (`11330` vs `6797`); il volume percepito sullo speaker ESP32 (`10%` al boot / `13%` via seriale) andrà verificato acusticamente dall'utente.
- La correzione di `TTS_TOO_LONG` è verificata dai test automatici, ma la conferma definitiva sul robot richiede il collaudo fisico dell'utente.

## 7. Procedura di rollback

1. Arrestare `task-3792` (`PID 4864`).
2. Ripristinare i 5 file da `scratch/backup_fase12_15b/` in `05-Voice-AI/voice_bridge/` (oppure impostare `JARVIS_TTS_PIPER_DSP_ENABLED=false`, `JARVIS_TTS_PIPER_SPEED=1.0`, `JARVIS_TTS_PIPER_NOISE_SCALE=0.667`, `JARVIS_TTS_MAX_CHARS=550`).
3. Riavviare il Voice Bridge e verificare `/ready` e la riconnessione WSS dell'ESP32.

## 8. Istruzioni per il collaudo fisico (`GPIO47`)

Eseguire le 5 prove reali:
1. *"Jarvis, che ore sono?"* (verifica comando locale + nuova voce Amichetto)
2. *"Jarvis, chi era Leonardo da Vinci?"*
3. *"Quando è nato?"*
4. *"Jarvis, spiegami come funziona un vulcano."* (verifica risoluzione `TTS_TOO_LONG`)
5. *"Jarvis, quanto fa dodici per otto?"*
