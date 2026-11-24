# FASE 12.21 — Attivazione voce definitiva `1.00x` e protezione integrità TTS

## 1. Configurazione precedente vs nuova (senza segreti)

| Parametro | Precedente (FASE 12.19) | Definitiva (FASE 12.21) |
|---|---|---|
| `JARVIS_TTS_PIPER_SPEED` | `1.10` (`length_scale=0.909`) | **`1.00`** (`length_scale=1.000`) |
| `JARVIS_TTS_PIPER_PITCH_SEMITONES` | `+5.0` | `+5.0` (invariato) |
| `JARVIS_TTS_PIPER_NOISE_SCALE` | `1.10` | `1.10` (invariato) |
| `JARVIS_TTS_PIPER_ROBOT_MIX` | `0.0` | `0.0` (invariato) |
| `JARVIS_TTS_PIPER_DSP_ENABLED` | `true` (`RMS maximizer + tanh`) | `true` (invariato) |
| `JARVIS_TTS_MAX_CHARS` | `300` | **`270`** (margine sotto `640,000 B` a `1.00x`) |
| Limite PCM ESP32 (`esp_max_tts_bytes`) | `640,000 B` (`20.0s`) | `640,000 B` (invariato) |

Parametri AI/STT invariati: `LOCAL_ONLY`, `qwen2.5:3b`, `keep_alive=30m`, pre-warm attivo, `120`/`180` token, `4` turni, `num_ctx=2048`, Whisper `small/int8`, `beam_size=1`, Cloud disabilitato.

## 2. File modificati (backup in `scratch/backup_fase12_21/`)

- `05-Voice-AI/voice_bridge/config.py`: `tts_piper_speed=1.00`, `tts_max_chars=270`.
- `05-Voice-AI/voice_bridge/tts_engine.py`: default `speed=1.00`.
- `05-Voice-AI/voice_bridge/.env.bridge.example`: aggiornati `JARVIS_TTS_PIPER_SPEED=1.00` e `JARVIS_TTS_MAX_CHARS=270`.
- `05-Voice-AI/tests/test_fase12_15b_tts_amichetto.py`: test aggiornati per `1.00x`, `length_scale=1.000`, `270` caratteri e verifica audio lungo `~250` caratteri (`<= 640,000 B`).

## 3. Benchmark TTS isolato a `1.00x` (`pitch=+5.0st`, `noise_scale=1.10`, `tanh`)

| Caso | Caratteri | Tempo sintesi+DSP | Durata | Dimensione PCM | Clipping | `last50ms` peak | > 640 KB |
|---|---|---|---|---|---|---|---|
| **A — Breve** (*Dodici per otto...*) | `30` | `647.2 ms` | `2.03 s` | `64,822 B` | `0` | `0` | `False` |
| **B — Leonardo** | `192` | `1160.1 ms` | `11.40 s` | `364,772 B` | `0` | `0` | `False` |
| **C — Vulcano** | `246` | `1464.8 ms` | `13.94 s` | `446,088 B` | `0` | `0` | `False` |
| **D — Prossimo al limite** | `285` | `1713.1 ms` | `19.03 s` | `609,104 B` | `0` | `0` | `False` |
| **E — Molte pause/lunghe** | `294` | `1529.6 ms` | `17.13 s` | `548,116 B` | `0` | `0` | `False` |

**Motivazione di `JARVIS_TTS_MAX_CHARS=270`**: a `1.00x`, `285` caratteri raggiungono già `609,104 B` (`19.03s`, ~`95%` del limite `640,000 B`); impostare `270` caratteri lascia un margine di sicurezza di ~`1.5–2.0s`, riducendo la necessità di risintesi aggiuntive pur mantenendo intatto il controllo effettivo su `640,000 B` e la riduzione su frasi complete.

## 4. Test automatici

Suite (`test_fase12_15b_tts_amichetto.py`, `test_hybrid_ai_fase12.py`, `test_esp32_ws_protocol.py`, `test_voice_bridge.py`, `test_voice_lab.py`):
- **`Ran 43 tests in 5.737s — OK`** (0 errori, 0 fallimenti).

## 5. Stato dei servizi post-riavvio

- **Voice Bridge**: `PID 21484` (`task-3921`) su `https://<PC_LAN_IP>:8765`, `Ollama prewarm ok model=qwen2.5:3b keep_alive=30m ms=33.0`.
  - `/health`: `200 OK`
  - `/ready`: `200 OK`, `tts`: `Piper pronto (it_IT-riccardo-x_low.onnx, 16000 Hz, speed=1.00x, pitch=+5.0st, dsp=on)`
- **Ollama**: `PID 18024` (`task-3574`) attivo su `127.0.0.1:11434` (`qwen2.5:3b`, non riavviato).
- **ESP32-S3 (`<ESP32_LAN_IP>`)**: riconnesso automaticamente via WSS (`<ESP32_LAN_IP>:58415 - "WebSocket /ws/v1/esp32" [accepted]`, `connection open`).

## 6. Problemi residui / note

- La latenza di generazione CPU di `qwen2.5:3b` (`~16.5–17 tok/s`) resta invariata per scelta progettuale di questa fase.
- Il collaudo fisico su `GPIO47` è in attesa dell'utente.

## 7. Procedura di rollback

1. Arrestare `task-3921` (`PID 21484`).
2. Ripristinare i 3 file da `scratch/backup_fase12_21/` in `05-Voice-AI/voice_bridge/` (oppure impostare `JARVIS_TTS_PIPER_SPEED=1.10`, `JARVIS_TTS_MAX_CHARS=300`).
3. Riavviare il Voice Bridge e verificare `/ready` e la riconnessione WSS dell'ESP32.
