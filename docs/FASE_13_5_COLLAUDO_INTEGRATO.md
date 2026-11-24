# FASE 13.5 — Collaudo Completo del Firmware Integrato (`fase13_3-integrated`)

## 1. Riepilogo Esecutivo
- **Firmware collaudato**: copia sperimentale FASE 13.5A (`04-Firmware/experiments/fase13_3-integrated/build/fase13_3-integrated.ino.bin`, `1.298.656` B, SHA-256 `342C28A025D5F7239B18263B54E434047B1E08D75747CAA6800326E5E7C5AB17`) flashata esclusivamente su `app0 @ 0x10000` (`ESP32-S3 COM6`, MAC `<ESP32_MAC_ADDRESS>`).
- **Firmware stabile FASE 12.27**: integro, non modificato; immagine di rollback pronta in [fase12_27_app0_rollback.bin](05-Voice-AI/backups/fase13_2_preflash/fase12_27_app0_rollback.bin) (`1.310.720` B, SHA-256 `94E0B14E676E535685F960658C71D7324550A25A88AEB409D10B87A912418E47`).

---

## 2. Cronologia e Risultati dei Checkpoint

### Pre-FASE 13.5A (Primo tentativo, interrotto e risolto)
- **Anomalia**: boot loop con `Guru Meditation Error: Core 0 panic'ed (Interrupt wdt timeout on CPU0)`.
- **Causa**: overflow in `AudioPlayback::WriteZeroFlush(kSilenceFlushFrames)` (`960` frame su buffer da `256` frame) che corrompeva `mux_`.
- **Risoluzione (FASE 13.5A)**: chunking sicuro `<= kChunkFrames` (`256`) + gestione scritture parziali/timeout/errori; `6/6` unit test host OK.

### CHECKPOINT A — Avvio (`task-4658`, `65 s`, `18:58:47`–`18:59:52`)
- **Esito**: **SUPERATO** (`panics=0`, `resets=0`, nessun WDT timeout).
- **Inizializzazioni osservate**:
  - PSRAM RX `256.000` B, TX `640.000` B
  - `[OLED] Ready addr=0x3C SDA=GPIO41 SCL=GPIO42 driver=SH1106 (132x64 RAM, +2px col offset)`
  - `[AUDIO] I2S1 TX ready (RTOS task Core=0 Prio=3, BCLK=GPIO15 LRC=GPIO16 DIN=GPIO7, 16kHz, vol=10%)`
  - `[WAKE_INIT_OK] microWakeWord hey_jarvis ready`
  - `[STATE] -> WIFI_CONNECTED` (`18:58:50.304`) → `[STATE] -> IDLE` (`18:58:53.900`, `~5.3 s` dal boot).

### CHECKPOINT B — Eyes 3.0 e Speaker in `IDLE` (`task-4664`, `45 s`, `19:01:17`–`19:02:02`)
- **Esito**: **SUPERATO**.
- **Log seriali**: `IDLE` stabile per tutta la finestra (`panics=0`, `resets=0`, `wakes=0`).
- **Conferma fisica utente**: occhi **Eyes 3.0** fluidi/naturali e speaker silenzioso in `IDLE` (`ok`).

### CHECKPOINT C — Conversazione Completa E2E (`task-4690` + Voice Bridge `task-4207`)
- **Esito**: **SUPERATO** (con osservazione VAD documentata).
- **Turno E2E completo con Ollama (`esp-3` / `req_c715bb335650`)**:
  - `19:04:57.903 [WAKE_DETECTED] score=0.996 smooth=0.977 noise_rms=199`
  - `19:04:57.904 [STATE] -> RECORDING` (`LISTENING`)
  - `19:05:05.430 [STATE] -> UPLOADING` (`THINKING`, `256.000` B, `dur=8.00 s` con `0.50 s` pre-roll, `rms=1743`, `peak=20261`)
  - Pipeline PC: `stt=2197.7 ms` + `ai=5454.7 ms` (`ollama:qwen2.5:3b`) + `tts=1099.5 ms` (`Piper Profilo 08`, `270.080` B / `8.44 s`) = `total=8790.3 ms`
  - `19:05:20.172 [AUDIO] Playback started (samples=135040, dur=8440ms, vol=10%)` → `PLAYING` (`SPEAKING`)
  - `19:05:28.620 [STATE] -> IDLE` (risposta completa confermata dall'utente, animazioni corrette).
- **Turno breve Local Intent (`req_d1a136acc046`)**: `dur=5.75s`, `stt=2317.5ms`, `ai=2.5ms`, `tts=2600.2ms`, `total=4949.9ms`, risposta `2.06 s`.

### CHECKPOINT D — Funzioni Alternative (`task-4698`, `75 s` + `task-4702`, `30 s`)
- **Esito**: **SUPERATO** (con anomalia minore sul ri-trigger post-guardia documentata).
- **Wake word senza domanda (`no-speech` `2.5 s`)**: **6/6** chiusure automatiche a `~2.50 s` verso `IDLE` senza inviare audio al PC.
- **Pulsante `GPIO47` push-to-talk**: attivazione manuale (`19:07:23.115`), upload al rilascio (`19:07:25.403`), risposta vocale `2.15 s` e ritorno in `IDLE` (`19:07:32.049`).
- **Cancellazione (`GPIO47`)**: verificato `[STATE] -> CANCELLED` → `[STATE] -> IDLE` (`19:08:04.449`).

### CHECKPOINT E — Stabilità (`task-4708`, `610 s`, `19:09:11`–`19:19:21`)
- **Esito**: **SUPERATO**.
- **Log seriali su `610 s` continui**: `panics=0`, `resets=0`, `errors=0`, `wakes=0` (zero falsi positivi/ri-trigger in `IDLE` prolungato), `states=0`.
- **Nota telemetria**: con `JARVIS_DEBUG_VERBOSE=0` il firmware non stampa metriche periodiche di `heap`, `psram`, `stack` o `FPS` OLED durante `IDLE` silenzioso.

---

## 3. Problemi / Anomalie Riscontrate durante il Collaudo
1. **Ri-trigger rapido a `~1.16–1.18 s` dal ritorno in `IDLE`** (osservato in Checkpoint C alle `19:05:29.793` e in Checkpoint D alle `19:07:09.033`, `19:07:12.693`, `19:08:05.611`, `19:08:19.741`): subito allo scadere della guardia `kPostCycleGuardMs = 1000 ms`, residui audio nel buffer DMA `I2S_NUM_0` o eco ambientale possono riattivare la sliding window di `microWakeWord`.
2. **VAD `no-speech` saltato in presenza di eco/coda** (osservato in Checkpoint C `esp-2`/`esp-4` e `task-4702` `19:08:05`): se il pre-roll o la coda post-trigger supera `kMinSpeechRms=360` per 3 chunk, il VAD considera iniziato il parlato e prosegue fino a `8.00 s` producendo poi `EMPTY_TRANSCRIPT` lato Whisper.
3. **Margine Flash ridotto (`12.064` byte liberi su `app0 = 1.310.720` B)**: lascia pochissimo spazio per futuri log o funzionalità senza ripartizionamento.
4. **Mancata esposizione periodica di `heap`/`psram`/`stack`** in `IDLE` con `JARVIS_DEBUG_VERBOSE=0`.

---

## 4. Raccomandazioni per la Successiva Versione Stabile
1. **Flush DMA `I2S_NUM_0` + guardia `1500 ms`**: al ritorno in `kIdle`, drenare/scartare i primi `150–200 ms` di buffer I²S prima di alimentare `MicroWakeWordDetector` e portare `kPostCycleGuardMs` da `1000 ms` a `1500 ms`.
2. **Ignorare i primi `300 ms` post-wake nel VAD** (o escludere il pre-roll dal calcolo `speech_started_`) per evitare che la coda di *"Hey Jarvis"* armi il VAD causando registrazioni vuote da `8.00 s`.
3. **Telemetria leggera su comando seriale (`STAT`)**: aggiungere un comando seriale `STAT` (costo Flash trascurabile) per stampare su richiesta `freeHeap`, `freePsram`, `TaskStackHighWaterMarkBytes()`, `noise_floor_rms` e `FPS` OLED senza inquinare i log `IDLE`.
4. **Tabella partizioni 16 MB (`Huge APP`)**: prima di aggiungere ulteriori feature (es. nuovi comandi o display), valutare in una fase dedicata una partizione `app0` da `3 MB` su Flash `16 MB` per superare il limite del `99%`.
