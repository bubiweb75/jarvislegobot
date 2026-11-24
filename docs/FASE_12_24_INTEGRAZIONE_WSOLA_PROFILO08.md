# FASE 12.24 — Integrazione controllata WSOLA e attivazione del profilo vocale 08

**Data**: 2026-11-18  
**Stato**: **Profilo 08 ATTIVO** sul Voice Bridge live (`https://<PC_LAN_IP>:8765`), in attesa del collaudo fisico dell'utente.

---

## 1. Backup creati

Tutti i file coinvolti prima delle modifiche della FASE 12.24 sono stati salvati senza sovrascrivere i backup delle fasi precedenti in `05-Voice-AI/backups/fase12_24/`:
- `05-Voice-AI/backups/fase12_24/voice_dsp.py.bak`
- `05-Voice-AI/backups/fase12_24/tts_engine.py.bak`
- `05-Voice-AI/backups/fase12_24/config.py.bak`
- `05-Voice-AI/backups/fase12_24/pipeline.py.bak`
- `05-Voice-AI/backups/fase12_24/api.py.bak`
- `05-Voice-AI/backups/fase12_24/previous_live_config.json`

---

## 2. File modificati e aggiunti

- [05-Voice-AI/voice_dsp.py](05-Voice-AI/voice_dsp.py): aggiunti `_wsola_time_stretch()` (vettorizzato pure-NumPy con `sliding_window_view` e `sq_cumsum`), `_safe_linear_level()` (`target_active_rms=0.22`, `max_peak=0.89`), e parametri `method` (`"phase_vocoder"` | `"wsola"`) e `limiter_enabled` in `shape_piper_wav()` con validazione finita.
- [05-Voice-AI/voice_bridge/config.py](05-Voice-AI/voice_bridge/config.py): aggiunti `tts_piper_dsp_method` (`JARVIS_TTS_PIPER_DSP_METHOD`, default `"wsola"`) e `tts_piper_limiter_enabled` (`JARVIS_TTS_PIPER_LIMITER_ENABLED`, default `False`); default `tts_piper_noise_scale` impostato a `0.60`.
- [05-Voice-AI/voice_bridge/tts_engine.py](05-Voice-AI/voice_bridge/tts_engine.py): aggiunti `dsp_method` e `limiter_enabled` in `PiperTTSEngine`, gestione errori `TTS_DSP_FAILED` in `synthesize()` e report esteso in `is_available()`.
- [05-Voice-AI/voice_bridge/pipeline.py](05-Voice-AI/voice_bridge/pipeline.py): passati `dsp_method` e `limiter_enabled` a `PiperTTSEngine`.
- [05-Voice-AI/voice_bridge/api.py](05-Voice-AI/voice_bridge/api.py): log esplicito della configurazione TTS/DSP attiva allo startup (`_startup_event`).
- [05-Voice-AI/tests/test_fase12_24_wsola_profile08.py](05-Voice-AI/tests/test_fase12_24_wsola_profile08.py): nuovi test di integrazione, pitch, assenza `tanh`, clipping, protezioni PCM ESP32 (`640.000` B) e rollback.
- [05-Voice-AI/tests/test_fase12_15b_tts_amichetto.py](05-Voice-AI/tests/test_fase12_15b_tts_amichetto.py): esplicitati in `setUp` i parametri storici della FASE 12.15B (`noise_scale=1.10`, `phase_vocoder`, `limiter_enabled=True`) per mantenere valida la copertura storica.

---

## 3. Configurazione precedente vs nuova (Profilo 08)

| Parametro | Configurazione precedente (FASE 12.21) | Nuova configurazione attiva (FASE 12.24 — Profilo 08) |
| :--- | :--- | :--- |
| Modello Piper | `it_IT-riccardo-x_low.onnx` (`16000 Hz`) | `it_IT-riccardo-x_low.onnx` (`16000 Hz`) |
| `JARVIS_TTS_PIPER_SPEED` | `1.00` | `1.00` |
| `JARVIS_TTS_PIPER_NOISE_SCALE` | `1.10` | **`0.60`** |
| `JARVIS_TTS_PIPER_PITCH_SEMITONES` | `5.0` | `5.0` |
| `JARVIS_TTS_PIPER_ROBOT_MIX` | `0.0` | `0.0` |
| `JARVIS_TTS_PIPER_DSP_ENABLED` | `true` | `true` |
| `JARVIS_TTS_PIPER_DSP_METHOD` | `phase_vocoder` | **`wsola`** |
| `JARVIS_TTS_PIPER_LIMITER_ENABLED` | `true` (`tanh`) | **`false`** (scaling lineare sicura `max_peak=0.89`) |
| `JARVIS_TTS_MAX_CHARS` | `270` | `270` |
| `esp_max_tts_bytes` | `640000` | `640000` |

---

## 4. Test eseguiti

- Suite completa eseguita dopo l'ultima modifica (`python -m unittest discover -s tests -q`): **`Ran 100 tests in 24.528s — OK`** (`0` errori, `0` fallimenti).
- Copertura verificata:
  - Default `BridgeConfig.from_env()` per Profilo 08 e override di rollback via variabili d'ambiente.
  - Pitch shifting `+5` semitoni con WSOLA, durata invariata, formato `16000 Hz` mono PCM16, assenza clipping (`max_peak <= 0.89`), assenza compressione `tanh`.
  - Gestione errori su metodo DSP non valido.
  - Protezioni PCM ESP32 (`640.000` B): risposte brevi, riduzione + risintesi su risposte lunghe, fallback e `BridgeError("TTS_TOO_LONG")`.
  - Sintesi reale con `piper.exe` su più frasi italiane differenti dal benchmark.

---

## 5. Benchmark integrato (`PiperTTSEngine` reale)

| Caso testo | Configurazione | Tempo totale TTS (ms) | PCM (byte) | Durata (s) | Peak (dBFS) | Active RMS (dBFS) | Clipping |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Breve** (31 car.) | Prec. (`phase_vocoder`, `ns=1.10`, `tanh`) | 828.9 | 65.206 | 2.038 | -0.41 | -9.23 | 0 |
| **Breve** (31 car.) | **Profilo 08** (`wsola`, `ns=0.60`, no `tanh`) | **752.9** | 71.424 | 2.232 | -1.06 | -13.08 | 0 |
| **Medio** (102 car.) | Prec. (`phase_vocoder`, `ns=1.10`, `tanh`) | 1081.4 | 209.428 | 6.545 | -0.52 | -8.80 | 0 |
| **Medio** (102 car.) | **Profilo 08** (`wsola`, `ns=0.60`, no `tanh`) | **961.1** | 200.704 | 6.272 | -1.12 | -13.10 | 0 |
| **Lungo** (211 car.) | Prec. (`phase_vocoder`, `ns=1.10`, `tanh`) | 1324.3 | 401.978 | 12.562 | -0.35 | -8.79 | 0 |
| **Lungo** (211 car.) | **Profilo 08** (`wsola`, `ns=0.60`, no `tanh`) | **1561.9** | 462.080 | 14.440 | -1.01 | -14.01 | 0 |

*(Tutti i valori PCM restano ampiamente entro il limite ESP32 di `640.000` byte, con zero clipping.)*

---

## 6. Stato dei servizi e verifiche live

- **Voice Bridge (`task-4096`, `PID 20264`)**: attivo su `https://<PC_LAN_IP>:8765`.
  - Log startup: `TTS startup config | ok=True | Piper pronto (it_IT-riccardo-x_low.onnx, 16000 Hz, speed=1.00x, noise_scale=0.60, pitch=+5.0st, dsp=on, method=wsola, tanh=off)`
  - `/health`: `200 OK` (`{"status": "ok", "service": "jarvis-voice-bridge", "version": "0.1.0"}`)
  - `/ready`: `200 OK` (`ready: true`, `tts` con `method=wsola, noise_scale=0.60, tanh=off`, `stt` `small/int8`, `ollama` `qwen2.5:3b`)
  - Pre-warm Ollama: `Ollama prewarm ok model=qwen2.5:3b keep_alive=30m ms=47.1`
  - ESP32 WSS: riconnesso (`<ESP32_LAN_IP>:58420 - "WebSocket /ws/v1/esp32" [accepted]`, `connection open`)
  - Nessun errore TTS o PCM nei log.
- **Ollama (`task-3574`)**: attivo su `127.0.0.1:11434`, `qwen2.5:3b` caricato in memoria (`api/ps` 200 OK).

---

## 7. Anomalie riscontrate durante l'attivazione

- Al primo tentativo di avvio live, `api.py` aveva sollevato `NameError: name 'logger' is not defined` in `_startup_event`; risolto aggiungendo `import logging` e `logging.getLogger("jarvis.voice_bridge")`, quindi rieseguita l'intera suite (`100/100 OK`) e riavviato il servizio con esito positivo.

---

## 8. Procedura di rollback immediato (senza reinstallazioni o download)

### Opzione A — Rollback rapido via variabili d'ambiente (consigliato)
Riavviare il solo Voice Bridge impostando:
- `JARVIS_TTS_PIPER_NOISE_SCALE=1.10`
- `JARVIS_TTS_PIPER_DSP_METHOD=phase_vocoder`
- `JARVIS_TTS_PIPER_LIMITER_ENABLED=true`

### Opzione B — Ripristino completo dei file originali
Copiare i 5 file da `05-Voice-AI/backups/fase12_24/*.bak` alle rispettive posizioni originali (`voice_dsp.py`, `voice_bridge/tts_engine.py`, `voice_bridge/config.py`, `voice_bridge/pipeline.py`, `voice_bridge/api.py`) e riavviare il solo Voice Bridge.
