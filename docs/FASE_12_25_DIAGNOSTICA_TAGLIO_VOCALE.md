# FASE 12.25 — Diagnostica del taglio vocale e verifica end-to-end

**Data**: 2026-11-19  
**Stato**: Diagnostica completata (nessuna modifica applicata a Profilo 08, Piper, WSOLA, firmware ESP32 o altri servizi)  
**Frase di riferimento (Prova D)**:  
> *"Tre piccoli robot preparano trenta programmi."*

---

## 1. Analisi dei log esistenti (`task-4096.log`)

Dai log del Voice Bridge della FASE 12.24 (`task-4096.log`) risultano esattamente 4 turni consecutivi ESP32 (`esp-16`..`esp-19`), corrispondenti alle prove A, B, C e D del collaudo fisico:

| Prova | Request ID | WS Seq | Durata input ESP32 (`dur`) | `stt_ms` | `ai_ms` | `tts_ms` | `TTS_READY pcm_bytes` | `dur_s` | `attempts` | `WSS TTS_SENT` |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| A (Matematica) | `req_b39f904bfba9` | `esp-16` | `3.07s` | 4209.3 | 1008.3 | 840.2 | 105.728 | 3.30 | 1 | `105728 B` |
| B (Leonardo) | `req_26e8b552a059` | `esp-17` | `2.19s` | 2753.5 | 4139.0 | 1449.9 | 456.704 | 14.27 | 1 | `456704 B` |
| C (Vulcano) | `req_d60335174197` | `esp-18` | `3.54s` | 2821.8 | 6345.6 | 1172.2 | 357.888 | 11.18 | 1 | `357888 B` |
| **D (Pronuncia)** | **`req_a1f0d857e6c2`** | **`esp-19`** | **`5.00s`** | **2942.7** | **1458.2** | **720.0** | **90.880** | **2.84** | **1** | **`90880 B`** |

### Trasparenza sui dati non presenti nei log
- Poiché nel servizio live `JARVIS_LOG_STT_DIAG_TEXT` e `JARVIS_LOG_CONVERSATION_TEXT` erano disattivati (`False` per privacy), **il testo riconosciuto da Whisper, il testo prodotto da Ollama e il testo passato a Piper non sono registrati in `task-4096.log`**.
- **Riduzioni / fallback**: `attempts=1`, nessun evento `TTS_PCM_LIMIT_EXCEEDED`, nessuna riduzione testo, nessun fallback (`fallback=False`, `provider=ollama:qwen2.5:3b`).
- **Errori**: `0` errori nei log server.
- **Nota stato servizi**: in seguito a un riavvio del server IDE/host, i processi background della sessione precedente (`task-4096` Voice Bridge e `task-3574` Ollama) risultavano terminati all'avvio di questa fase diagnostica.

---

## 2. Verifica STT e limite cattura ESP32 (`5.00 s`)

- **Evidenza chiave nei log e nel firmware**: nella prova D (`req_a1f0d857e6c2`), la durata dell'audio catturato dal microfono ESP32 è esattamente **`dur=5.00s`**.
- Nel firmware ESP32 ([jarvis_wifi_voice_client.ino](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/jarvis_wifi_voice_client.ino#L29), [audio_buffer.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_buffer.h#L11-L12), [ws_protocol.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/ws_protocol.h#L31)):
  - `kMaxRecordMs = 5000U` (`5` secondi = `80.000` campioni = `160.000` byte @ 16 kHz PCM16).
  - La registrazione viene interrotta automaticamente al raggiungimento dei `5.00 s` (`jarvis_wifi_voice_client.ino#L245-L257`).
- La frase pronunciata dall'utente (*"Jarvis, pronuncia lentamente: tre piccoli robot preparano trenta programmi."*) supera facilmente i 5 secondi se detta con pausa o scandita: **la registrazione in ingresso ha quindi saturato il buffer da `5.00 s`**, potendo troncare la parte finale della richiesta prima dell'invio a Whisper.
- L'accuratezza esatta della trascrizione di Whisper sulla prova D non è verificabile dai soli log perché `JARVIS_LOG_STT_DIAG_TEXT` era disattivo.

---

## 3. Verifica Ollama

- Nei log di `req_a1f0d857e6c2`, Ollama (`qwen2.5:3b`) ha risposto in `1458.2 ms` (`fallback=False`).
- Poiché Ollama risultava fermo dopo il riavvio del server e `JARVIS_LOG_CONVERSATION_TEXT` era disattivo, non è stato possibile ispezionare la stringa esatta generata da Ollama né i token/stop reason di `req_a1f0d857e6c2`.
- Tuttavia, dal confronto quantitativo con il TTS offline (Sezione 4):
  - La frase esatta *"Tre piccoli robot preparano trenta programmi."* sintetizzata con Profilo 08 dura **`2.952 s` (`94.464` byte PCM)**.
  - Nella prova D live, il TTS ha generato **`2.84 s` (`90.880` byte PCM)** — cioè **`3.584` byte (`0.112 s`) in meno** rispetto alla frase esatta, compatibile con una risposta leggermente più corta o riformulata/troncata a monte (input troncato a `5.00 s` o riformulazione breve di `qwen2.5:3b`).

---

## 4. Verifica TTS e test comparativi (`05-Voice-AI/tts-lab/samples_fase12_25/`)

Tutti i 4 campioni richiesti sono stati generati in modo isolato con `it_IT-riccardo-x_low.onnx`, `speed=1.00x`, `noise_scale=0.60`:

| Campione | Testo | Durata (s) | PCM (byte) | `<= 640000` | Peak (dBFS) | Active RMS (dBFS) | Clipping | Silenzio iniziale (ms) | Silenzio finale (ms) | `head_100ms_rms` | `tail_100ms_rms` | Tempo TTS (ms) |
| :--- | :--- | ---: | ---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `A_frase_piper_puro_ns0.60.wav` | Frase originale (Piper puro, no DSP) | 3.016 | 96.512 | Sì | -0.00 | -11.99 | 1 | 52.7 | 395.3 | 0.0946 | 0.0000 | 2585.4 |
| `B_frase_profilo08_wsola.wav` | Frase originale (Profilo 08 WSOLA) | 2.952 | 94.464 | Sì | -1.01 | -13.24 | 0 | **51.6** | **411.3** | 0.1678 | 0.0000 | 651.3 |
| `C_frase_profilo08_silenzio_150ms.wav` | Frase originale + `150 ms` start/end (Profilo 08) | 3.252 | 104.064 | Sì | -1.01 | -13.24 | 0 | 201.6 | 561.3 | 0.0000 | 0.0000 | 651.3 |
| `D_due_frasi_profilo08_wsola.wav` | Due frasi consecutive (Profilo 08) | 6.736 | 215.552 | Sì | -1.01 | -13.23 | 0 | 56.9 | 330.9 | 0.1732 | 0.0000 | 859.7 |

### Osservazioni sul TTS / WSOLA
- Il profilo 08 **non taglia né le consonanti iniziali né le sillabe finali**: preserva **`51.6 ms`** di silenzio iniziale (vs `52.7 ms` in Piper puro) e **`411.3 ms`** di silenzio finale (vs `395.3 ms` in Piper puro), con `0` clipping.
- Anche con due frasi consecutive (`D_due_frasi_profilo08_wsola.wav`), la durata è integra (`6.736 s`, `215.552` B).

---

## 5. Verifica riproduzione ESP32 (sola lettura firmware)

Analisi di [audio_playback.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_playback.cpp), [audio_playback.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_playback.h), [audio_buffer.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_buffer.h) e [jarvis_wifi_voice_client.ino](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/jarvis_wifi_voice_client.ino):

- **Bufferizzazione completa prima del play**: `g_tx_buffer` riceve tutti i frame fino a `tts_end` (`NetEventType::kTtsReady`) prima che `g_playback.Start(g_tx_buffer)` avvii il task FreeRTOS `jarvis_audio_tx`.
- **Fade iniziale/finale**: `kFadeFrames = 320` (`20 ms`). Poiché Piper + Profilo 08 ha già `~52 ms` di silenzio iniziale e `~411 ms` finale, il fade da `20 ms` cade interamente nel silenzio senza attenuare il parlato.
- **Flush I²S finale**: `kSilenceFlushFrames = 960` (`60 ms` di zeri) via `WriteZeroFlush`.
- **Limite osservabilità WebSocket vs Seriale**: in [esp_protocol.py](05-Voice-AI/voice_bridge/esp_protocol.py#L309), `WSS TTS_SENT` attesta soltanto il completamento dell'invio lato server. Il firmware stampa `[AUDIO] Playback started` / `stopped` e i contatori `partial_writes_`, `i2s_errors_` soltanto sulla seriale USB locale, non via WebSocket, quindi i log server da soli non certificano l'esito I²S lato dispositivo (e su `audio_playback.cpp#L303-L316` una eventuale scrittura parziale incrementerebbe `partial_writes_` senza ritentare il residuo del chunk).

---

## 6. Classificazione del problema

Sulla base delle sole evidenze raccolte:

1. **Causa primaria altamente probabile (evidenza diretta nei log): `STT incompleto` / troncamento cattura microfono ESP32 a `5.00 s`**.
   - Nella prova D (`req_a1f0d857e6c2`), `dur=5.00s` indica il raggiungimento del tetto massimo di registrazione lato ESP32 (`kMaxRecordMs = 5000U`, `160.000` byte). Troncando la fine della frase dettata dall'utente, Whisper/Ollama ricevono una richiesta incompleta, spiegando un TTS risultante di `2.84 s` (`90.880` B) anziché `2.952 s` (`94.464` B).
2. **Ipotesi residua non escludibile senza log testuali / seriali**:
   - **Risposta AI abbreviata o riformulata** da `qwen2.5:3b` (non verificabile nei log perché `JARVIS_LOG_CONVERSATION_TEXT=False`).
   - **Esclusi dalle verifiche offline**: `Testo TTS ridotto` (`attempts=1`, `90.880 <= 640.000`), `Difetto della sintesi Piper` e `Artefatto DSP` (i campioni offline A–D con Profilo 08 sono completi e integri con `51.6 ms` di testa e `411.3 ms` di coda).

---

## 7. Percorsi dei campioni WAV generati

- **A — Piper puro (`noise_scale=0.60`, no DSP)**: `05-Voice-AI/tts-lab/samples_fase12_25/A_frase_piper_puro_ns0.60.wav`
- **B — Profilo 08 (WSOLA `+5`, `ns=0.60`, no `tanh`)**: `05-Voice-AI/tts-lab/samples_fase12_25/B_frase_profilo08_wsola.wav`
- **C — Profilo 08 + silenzio `150 ms` start/end**: `05-Voice-AI/tts-lab/samples_fase12_25/C_frase_profilo08_silenzio_150ms.wav`
- **D — Due frasi consecutive (Profilo 08)**: `05-Voice-AI/tts-lab/samples_fase12_25/D_due_frasi_profilo08_wsola.wav`

---

## 8. Correzione minima consigliata, rischi e rollback (non applicati)

- **Prima di modificare il codice**: ripetere una prova D parlando entro `3–4 s` (oppure con `JARVIS_LOG_STT_DIAG_TEXT=true` in test isolato) e ascoltare i campioni `B` e `C` per confermare al 100% che la sintesi offline è integra.
- **Correzione minima consigliata (se confermato il limite dei `5.00 s`)**:
  - Aumentare il buffer massimo di registrazione su ESP32 e Voice Bridge da `5 s` (`160.000` B) a `8 s` (`256.000` B) (`kMaxRecordMs = 8000U`, `AudioBuffer::kDefaultMaxSeconds = 8U`, `JARVIS_ESP_MAX_INPUT_BYTES=256000`).
- **Rischi**: maggior uso PSRAM lato ESP32 (+`96 KB` sul buffer RX, trascurabile su ESP32-S3 con PSRAM) e latenza leggermente superiore per richieste molto lunghe.
- **Rollback**: ripristinare `5000U` / `5U` / `160000`.
