# JARVIS LEGO BOT — FASE 10.6: Integrazione Offline Audio Duplex + Eyes 3.0

Firmware diagnostico isolato e completamente offline che integra acquisizione microfono **INMP441** (`I2S0` RX), riproduzione **MAX98357A** (`I2S1` TX), pulsante **Push-to-Talk** (`GPIO47`), buffer audio in **PSRAM** (5 secondi) e animazioni **Eyes 3.0** su OLED **SH1106** (`0x3C`).

- **Preserva integralmente**: `04-Firmware/jarvis-desk-buddy/`, `04-Firmware/arduino-hw-test/jarvis_voice_hw_test/`, `inmp441_hw_test`, `max98357a_hw_test` e i progetti Wokwi.

---

## 1. Pinout Hardware Confermato

| Periferica | Segnale | GPIO / Alimentazione |
|---|---|---|
| **OLED SH1106 (`0x3C`)** | `SDA` / `SCL` | `GPIO41` / `GPIO42` |
| **INMP441 (`I2S0` RX)** | `WS` / `SCK` / `SD` / `L/R` | `GPIO4` / `GPIO5` / `GPIO6` / `GND` |
| **MAX98357A (`I2S1` TX)** | `DIN` / `BCLK` / `LRC` / `SD` / `VIN` | `GPIO7` / `GPIO15` / `GPIO16` / `3V3` / `5V` |
| **Pulsante Push-to-Talk** | `BTN` | `GPIO47` (`INPUT_PULLUP`, verso `GND`) |

---

## 2. Architettura e Macchina a Stati

- **`AudioBuffer`** (`audio_buffer.*`): alloca `160.000` byte (`80.000` campioni = `5 s` @ `16 kHz`, PCM 16-bit) in **PSRAM** tramite `ps_malloc()`; se la PSRAM non è disponibile usa un fallback sicuro da `1 s` (`32.000` byte) in RAM.
- **`AudioCapture`** (`audio_capture.*`): `I2SClass(I2S_NUM_0)` a `16 kHz`, 32-bit mono slot sinistro, rimozione DC per blocco, conversione `24 -> 16 bit` (`>> 6` con saturazione/clamp `[-32767, +32767]`).
- **`AudioPlayback`** (`audio_playback.*`): `I2SClass(I2S_NUM_1)` a `16 kHz`, 16-bit stereo L=R duplicato, volume iniziale **`3%`** (range **`1..15%`**), fade-in/out `20 ms`, flush `60 ms`, blocchi da `16 ms` non bloccanti per mantenere fluido l'OLED.
- **`EyeController`** (`eye_controller.*`): `IDLE → NEUTRAL`, `LISTENING → LISTENING`, `PROCESSING → THINKING`, `PLAYING → SPEAKING`, `ERROR → CONFUSED`.
- **`ButtonController`** (`button_controller.*`): debounce `40 ms`, gestione sicura del rilascio anche dopo timeout di `5 s`.

---

## 3. Comandi Seriali (`115200 baud`)

- `HELP` — Elenco comandi
- `STATUS` — Stato macchina a stati, occhi, I²S RX/TX e registrazione
- `MIC_TEST` — Diagnostica microfono live (`2,5 s`, stampa `RMS`/`PEAK`/`SAMPLES`/`I2S_ERR` ogni `500 ms`)
- `RECORD` — Avvia registrazione (timeout automatico `5 s`, arrestabile con `STOP`)
- `STOP` — Interrompe registrazione, riproduzione o `MIC_TEST`
- `PLAY` — Riproduce l'ultima registrazione valida
- `VOLUME` / `VOLUME:<1..15>` — Legge o imposta il volume digitale (`default 3%`, max `15%`)
- `MEMORY` — Mostra `FREE_HEAP`, `FREE_PSRAM` e allocazione `AudioBuffer`
- `AUDIO_INFO` — Mostra formato, campioni, durata, picco e clipping

---

## 4. Caricamento con Arduino IDE 2 e Piano di Test Hardware

1. Apri `04-Firmware\arduino-hw-test\jarvis_duplex_hw_test\jarvis_duplex_hw_test.ino`.
2. In **Strumenti (Tools)**: `ESP32S3 Dev Module`, `Flash Size: 16MB (128Mb)`, `Flash Mode: QIO 80MHz`, **`PSRAM: OPI PSRAM`**, `USB CDC On Boot: Disabled` (UART CH343) o `Enabled` (USB nativa).
3. Compila (`Ctrl+R`), carica (`Ctrl+U`) e apri il **Monitor Seriale** a **`115200 baud`**.
4. **Piano di collaudo progressivo**:
   - **Avvio & display**: verifica `[MEM] AudioBuffer PSRAM alloc=160000 bytes`, `[MIC] I2S0 RX ready`, `[AUDIO] I2S1 TX ready`, `[OLED] Ready addr=0x3C`, occhi `NEUTRAL`.
   - **Diagnostica microfono**: invia `MIC_TEST` e verifica aumento `RMS`/`PEAK` parlando.
   - **Pressione troppo breve**: premi e rilascia `GPIO47` in `< 300 ms` → nessuna riproduzione vuota, ritorno a `IDLE`.
   - **Push-to-Talk completo (`2–3 s`)**: tieni premuto `GPIO47`, parla, rilascia → osserva `LISTENING → PROCESSING → PLAYING → IDLE` e ascolta la tua voce allo speaker.
   - **Limite 5 secondi**: tieni premuto `GPIO47` per `> 5 s` → arresto automatico sicuro a `5 s`, rilascio successivo ignorato senza riavvio accidentale.
   - **Interruzione (`STOP`) & ripetizione (`PLAY`)**: testa `RECORD` + `STOP`, poi `PLAY`, e ripeti almeno 5 cicli consecutivi verificando `MEMORY` e assenza di riavvii.

### Sicurezza e limiti noti
- `MAX98357A` alimentato a `5 V` da USB ESP32 senza condensatori da `470 µF` / `100 nF`: mantenere volume `≤ 15%` (default `3%`) e interrompere subito in caso di riavvii o distorsioni.
- `I2S0` (RX) e `I2S1` (TX) lavorano in half-duplex logico sequenziale (`LISTENING` → `PLAYING`); l'eco/feedback acustico simultaneo non è attivo.
