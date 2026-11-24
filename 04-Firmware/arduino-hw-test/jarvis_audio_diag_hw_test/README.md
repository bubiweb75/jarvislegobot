# JARVIS LEGO BOT — FASE 10.6.1: Diagnostica Distorsione Audio

Versione diagnostica isolata di `jarvis_duplex_hw_test` per identificare la causa della distorsione vocale rilevata in FASE 10.6, senza modificare i firmware delle FASI 10.5 e 10.6 né `jarvis-desk-buddy`.

---

## 1. Analisi Statica: Fatti Dimostrati vs Ipotesi

- **Fatti verificati nel codice**:
  - `INMP441` (`I2S_NUM_0` RX): `I2S_MODE_STD`, `16 kHz`, `I2S_DATA_BIT_WIDTH_32BIT`, `I2S_SLOT_MODE_MONO`, `I2S_STD_SLOT_LEFT` (`L/R=GND`). I dati 24-bit signed sono allineati nei bit `[31:8]`; `raw_buf_[i] >> 8` estrae il campione 24-bit, `dc_mean` rimuove l'offset DC di blocco e `>> 6` applica uno scaling `4×` con saturazione a `[-32767, +32767]`.
  - `MAX98357A` (`I2S_NUM_1` TX): `I2S_MODE_STD`, `16 kHz`, `I2S_DATA_BIT_WIDTH_16BIT`, `I2S_SLOT_MODE_STEREO`, `I2S_STD_SLOT_BOTH` con duplicazione L=R, volume `3%`..`15%`, fade `20 ms`.
  - In `MIC_TEST` della FASE 10.6 (`RMS=2049`, `PEAK=11195 < 32767`), i campioni non risultavano in clipping digitale.
- **Ipotesi da verificare con i test diagnostici** (non ancora dimostrate):
  1. **Timing `loop()` / I²C OLED vs DMA I²S (`MAX_GAP_MS`)**: ogni iterazione legge/scrive `256` frame (`16 ms`) mentre l'aggiornamento `OLED SH1106` su I²C `400 kHz` può richiedere `~25–30 ms`. Se `MAX_GAP` supera la capacità del buffer DMA (`90 ms` = `6 × 240` frame) o fa accumulare ritardi, si possono verificare **underrun TX / overrun RX** a `~30 Hz`.
  2. **Clipping su sillabe forti durante registrazione reale**: in `LOOPBACK_TEST`, `[DIAG_RX]` verifica `MIN`, `MAX`, `SAT%` (`|pcm16| >= 32000`) e `CLIP`.
  3. **Calo di tensione su `5 V` USB** senza condensatori `470 µF` / `100 nF` all'aumentare del volume: verificabile confrontando `TONE_TEST` a `VOLUME:3`, `VOLUME:5`, `VOLUME:10`.

---

## 2. Nuovi Test Diagnostici (`115200 baud`)

- **`TONE_TEST`**: genera `1,5 s` di sinusoide pura a `440 Hz` direttamente nel buffer e la riproduce su `I2S1` TX **con OLED attivo**.
- **`TONE_TEST_NO_OLED`**: genera esattamente lo stesso tono (`440 Hz`, `1,5 s`, stesso volume/percorso), ma **sospende gli aggiornamenti I²C OLED durante `PLAYING`** (senza disinizializzare il display e ripristinando l'OLED al termine o su errore/STOP).
  Entrambi stampano: `[DIAG_TX] BYTES=... | PARTIAL=... | TX_ERR=... | MAX_GAP=...ms | MAX_WRITE=...ms | MAX_INTER_WRITE=...ms | INTER>30ms=... | INTER>90ms=... | MAX_OLED=...ms`
- **`LOOPBACK_TEST`**: registra `3,0 s` dal microfono, stampa `[DIAG_RX] ...`, poi riproduce la voce e stampa `[DIAG_TX] ...`.

### Confronto A/B (`TONE_TEST` vs `TONE_TEST_NO_OLED`)
1. Esegui `TONE_TEST` a volume `3%`, ascolta e salva la riga `[DIAG_TX]`.
2. Esegui `TONE_TEST_NO_OLED` a volume `3%`, ascolta e salva la riga `[DIAG_TX]`.
- Se `TONE_TEST_NO_OLED` è **pulito** (con `MAX_INTER_WRITE < 5 ms` e `INTER>30ms=0`) mentre `TONE_TEST` è distorto → l'interferenza I²C OLED sul ciclo singolo è dimostrata.
- Se anche `TONE_TEST_NO_OLED` è **distorto** → la causa risiede altrove (es. PSRAM, DMA, alimentazione o amplificatore).

### Significato delle nuove metriche timing (`micros()`)
- **`MAX_WRITE`**: durata massima della singola chiamata `i2s_tx_.write()` (attesa interna del driver DMA).
- **`MAX_INTER_WRITE`**: intervallo massimo dalla **fine** di una `i2s_tx_.write()` all'**inizio** della successiva (tempo esterno fuori da `write()`).
- **`INTER>30ms` / `INTER>90ms`**: numero di pause tra scritture oltre `30 ms` e oltre `90 ms` (dimensione del ring buffer DMA `ESP_I2S`: `6 × 240 = 1440` frame = `90 ms` @ `16 kHz`).
- **`MAX_OLED`**: durata massima di `eyes_->Update()` durante `PLAYING`.
- **`MAX_GAP`**: intervallo massimo complessivo tra due tick di `UpdatePlaying()` (mantenuto per confronto).
- **Nota API**: `ESP_I2S.h` non espone un contatore diretto di underrun DMA hardware; `MAX_INTER_WRITE` e `INTER>90ms` forniscono la misura oggettiva della continuità di alimentazione del buffer TX.

---

## 3. Procedura di Collaudo Manuale (Arduino IDE 2)

1. Apri `04-Firmware\arduino-hw-test\jarvis_audio_diag_hw_test\jarvis_audio_diag_hw_test.ino`.
2. Imposta: `ESP32S3 Dev Module`, `Flash Size: 16MB`, `Flash Mode: QIO 80MHz`, `PSRAM: OPI PSRAM`, `USB CDC On Boot: Disabled` (UART) o `Enabled` (USB nativa).
3. Carica e apri il **Monitor Seriale** a **`115200 baud`**.
4. Esegui nell'ordine:
   - `TONE_TEST` (volume `3%`): se la sinusoide è **distorta** → problema sul percorso TX / DMA / alimentazione speaker; se è **pulita** → TX e speaker sono OK.
   - `VOLUME:8` poi `TONE_TEST`: verifica se la distorsione compare aumentando il volume su tono puro.
   - `VOLUME:3` poi `LOOPBACK_TEST`: parla normalmente e verifica su `[DIAG_RX]` se `SAT% > 0%` / `CLIP > 0` oppure se `MAX_GAP` è elevato (`>= 30 ms`).
5. Riporta l'output completo del Monitor Seriale prima di applicare qualsiasi correzione al guadagno o al timing.
