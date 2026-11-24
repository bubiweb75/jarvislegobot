# FASE 13.7 — Collaudo Consolidamento Anti-Ri-Trigger e VAD

## 1. Oggetto del Collaudo
- **Build collaudata**: FASE 13.6 (`04-Firmware/experiments/fase13_3-integrated/build/fase13_3-integrated.ino.bin`)
- **Dimensione / SHA-256**: `1.299.328` byte (`<= 1.310.720` B `app0`, margine `11.392` B) | `44A548EDB0A83A318CFE684F6455EFAE71AD3E30B636B2C6FD17ABF7B12BBE32`
- **Target**: `ESP32-S3` (`COM6`, MAC `<ESP32_MAC_ADDRESS>`), sola partizione `app0 @ 0x10000` (`task-4747`, hash verificato).
- **Firmware stabile FASE 12.27**: integro, non sovrascritto; rollback disponibile in [fase12_27_app0_rollback.bin](05-Voice-AI/backups/fase13_2_preflash/fase12_27_app0_rollback.bin).

---

## 2. Risultati dei Checkpoint

### CHECKPOINT A — Avvio e Diagnostica (`task-4751`, `65 s`)
- **Esito**: **SUPERATO** (`panics=0`, `resets=0`).
- **Avvio**: `OLED SH1106 0x3C`, `I2S1 TX`, `microWakeWord hey_jarvis` inizializzati; `WIFI_CONNECTED` (`19:25:04.566`) → `IDLE` (`19:25:05.500`).
- **`STAT` (+12 s / +55 s)**: `heap=129516`, `min_heap=121928`, `psram=6787864`, `rx_hwm=10228` (su `12.288` B), `noise=139–159`, `thr=360–381`.

### CHECKPOINT B — Conversazioni (`task-4755`, `150 s` + Voice Bridge `task-4207`)
- **Esito**: **SUPERATO** (`5/5` prove riuscite, `0` ri-trigger, `0` `EMPTY_TRANSCRIPT`).
- **Prove registrate**:
  1. `19:27:23.228`: domanda breve → `PLAYING` `2.22 s` → `IDLE` (`19:27:38.566`)
  2. `19:27:40.373` (`1.81 s` dopo `IDLE`): seconda domanda → `PLAYING` `3.18 s` → `IDLE` (`19:27:53.723`)
  3. `19:27:58.493`: «Hey Jarvis» senza domanda → chiusura **`no-speech`** a **`2.52 s`** (`19:28:01.024 [STATE] -> IDLE`), zero upload al PC.
  4. `19:28:05.091`: domanda con Ollama (`stt=2.17s, ai=5.44s, tts=1.09s, total=8.71s`) → `PLAYING` `8.49 s` → `IDLE` (`19:28:28.637`).
  5. `19:28:43.042`: domanda successiva (`dur=6.76s, total=16.97s`) → `WSS TTS_SENT` `10.36 s`.
- **`STAT` in `RECORDING`**: `heap=129252, min_heap=121308, psram=6787696, rx_hwm=10036, noise=374, thr=897`.

### CHECKPOINT C — `GPIO47` (`task-4761`, `60 s`)
- **Esito**: **SUPERATO**.
- **Push-to-talk**: attivazioni manuali `19:29:44.729` (`PLAYING` `2.68 s`) e `19:30:02.284` (`PLAYING` `11.34 s`).
- **Cancellazione**: pressione `GPIO47` durante `PLAYING` (`19:30:00.361`) → `[STATE] -> CANCELLED` → `[STATE] -> IDLE`, **zero ri-trigger**.

### CHECKPOINT D — Stabilità (`task-4765`, `611 s` / `> 10 min`)
- **Esito**: **SUPERATO**.
- **Attività**: **15 conversazioni complete consecutive** (risposte Piper da `1.16 s` a `15.40 s`) alternate a periodi di `IDLE` (incluso un tratto continuo di `2 min 23 s` senza falsi positivi).
- **Conteggi**: **`panics=0`**, **`resets=0`**, **`errors=0`**, **`0` `EMPTY_TRANSCRIPT`**, **`0` ri-trigger spontanei**.
- **Memoria su 10 minuti (`STAT` iniziale `19:30:45` vs finale `19:40:40`)**:
  - `heap`: **`129.252` B** → **`129.252` B** (zero memory leak)
  - `min_heap`: **`121.296` B** costante
  - `psram`: **`6.786.092` B** → **`6.787.696` B**
  - `rx_hwm`: **`10.036` B** costante (`81.7%` stack libero su `12.288` B)

---

## 3. Verifica Criteri di Accettazione

| Criterio | Esito |
|---|---|
| Zero crash o reset | **SUPERATO** (`0` su tutti i checkpoint) |
| Zero ri-trigger spontanei dopo la risposta | **SUPERATO** (`0` su oltre 20 turni + `CANCELLED`) |
| Nessuna registrazione vuota causata da coda wake word | **SUPERATO** (`0` `EMPTY_TRANSCRIPT`, `no-speech` chiuso a `2.52 s`) |
| Nessun troncamento delle domande | **SUPERATO** (pre-roll `500 ms` + holdoff VAD `300 ms` non distruttivo) |
| Eyes 3.0 fluido e speaker silenzioso in IDLE | **SUPERATO** (confermato visivamente/acusticamente e da `I2S1 TX` zero-flush) |
| GPIO47 funzionante (PTT + cancel) | **SUPERATO** |
| Memoria e stack senza anomalie | **SUPERATO** (`heap=129252` fisso, `rx_hwm=10036`) |

---

## 4. Anomalie / Note Residue
- **Margine Flash `app0` ridotto (`11.392` B su `1.310.720` B)**: la build corrente funziona stabilmente in `app0`, ma eventuali espansioni future richiederanno una partizione `app0` più ampia (es. `Huge APP` da `3 MB` su Flash `16 MB`).

---

## 5. Raccomandazione sulla Promozione a Versione Stabile
**PROMUOVIBILE A VERSIONE STABILE (FASE 13.x)**: la build FASE 13.6 ha superato tutti i criteri di accettazione su oltre 20 turni vocali reali, `GPIO47`, timeout `no-speech` e più di 10 minuti continui con zero memory leak (`heap=129.252` B invariato), zero ri-trigger e zero errori. Quando autorizzato, sarà sufficiente promuovere i sorgenti da `04-Firmware/experiments/fase13_3-integrated/` al ramo stabile `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` (conservando il backup FASE 12.27).
