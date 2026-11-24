# JARVIS LEGO BOT — FASE 10.5: Prima Voce Italiana (Collaudo Isolato)

Progetto Arduino isolato per pronunciare offline la frase:
**«Ciao, sono Jarvis! Sono pronto ad aiutarti.»**
con animazione vivace **Eyes 3.0** su OLED **SH1106** (`0x3C`, `GPIO41/42`) e uscita audio I²S su **MAX98357A** + speaker `4 Ω / 3 W`.

---

## 1. Alimentazione e Checklist Elettrica Obbligatoria (Prima del Primo Flash!)

### Consumo complessivo stimato
- **ESP32-S3-DevKitC-1 N16R8** (240 MHz, OPI PSRAM, Wi-Fi/BT spenti): `~60–120 mA` (picchi `~200 mA`).
- **OLED SH1106 1.3"**: `~10–25 mA`.
- **INMP441**: `~1,4 mA`.
- **MAX98357A + Speaker `4 Ω / 3 W`** (riproduzione vocale reale):
  - A riposo: `~2,5–3,5 mA`.
  - Durante parlato reale anche a volume moderato (`5–15%` o transitori): picchi fino a **`250–600+ mA`** (e fino a `800 mA` a volume alto su `5 V`).
- **Conclusione**: il regolatore LDO `3,3 V` integrato sull'ESP32-S3 **non** è dimensionato per alimentare contemporaneamente ESP32-S3 + OLED + INMP441 + riproduzione vocale continua sul MAX98357A (rischio di brownout/reset o surriscaldamento dell'LDO).

### Alimentazione consigliata per MAX98357A
- **Linea `5 V` dedicata (o `5V` USB/VBUS con alimentatore `≥ 1 A`) collegata a `VIN` del MAX98357A**, con **`GND` in comune** con ESP32-S3, OLED e INMP441.
- **`SD` del MAX98357A**: collegato a `3V3` (abilitazione / canale Left; i campioni sono comunque duplicati identici su L e R).
- **Disaccoppiamento vicino a `VIN`–`GND` del MAX98357A**:
  - **Condensatore elettrolitico `470 µF`** (tensione nominale **`≥ 10 V` o `16 V`**, rispettando la **polarità**: `+` su `VIN`, `−` su `GND`).
  - **Condensatore ceramico `100 nF`** (`0,1 µF`, non polarizzato) in parallelo vicino ai pin `VIN` e `GND` del modulo.
- **Sicurezza GPIO**: non collegare mai `5 V` ai pin GPIO dell'ESP32-S3 (`BCLK=GPIO15`, `LRC=GPIO16`, `DIN=GPIO7` sono solo segnali logici `3,3 V`).
- **Sicurezza Speaker**: collegare lo speaker `4 Ω / 3 W` **esclusivamente** tra `+` e `−` del MAX98357A (mai verso `GND`).

### Checklist prima dell'accensione
- [ ] `VIN` MAX98357A su linea `5 V` adeguata (`≥ 1 A`) e `GND` in comune con ESP32-S3.
- [ ] Condensatore `470 µF` (`≥ 10 V`, polarità `+` su `VIN`, `−` su `GND`) + `100 nF` montati vicino al MAX98357A.
- [ ] Nessun corto tra `5V`, `3V3` e `GND`.
- [ ] Nessun collegamento `5V` verso GPIO ESP32-S3.
- [ ] Speaker collegato solo a `+` e `−` del MAX98357A, isolato da `GND`.

---

## 2. Origine e Formato della Voce

- **Sorgente**: sintesi vocale locale offline tramite **Piper TTS** (`05-Voice-AI/tts-lab/bin/piper/piper.exe`) con modello italiano maschile **`it_IT-riccardo-x_low.onnx`** (licenza open-source).
- **File WAV sorgente**: `audio/jarvis_intro_it.wav` — **WAV PCM mono, 16 bit signed, 16.000 Hz**, non compresso (`101.932` byte, durata `3,184 s`).
- **Header incorporato in Flash (`PROGMEM`)**: `generated/jarvis_voice_pcm.h` (`50.944` campioni = `101.888` byte, generato da `tools/wav_to_pcm_header.py`).

---

## 3. Architettura e File del Progetto

- `jarvis_voice_hw_test.ino`: orchestrazione non bloccante (`setup()` / `loop()`).
- `audio_player.h` / `audio_player.cpp` (`AudioPlayer`): riproduzione I²S `ESP_I2S.h` a blocchetti da `256` frame (`16 ms`), duplicazione mono→stereo L/R, volume conservativo (`default 5%`, range `1..15%`), fade-in/fade-out `20 ms`, flush `60 ms` e blocco riproduzioni simultanee.
- `eye_controller.h` / `eye_controller.cpp` (`EyeController`): wrapper Eyes 3.0 su OLED SH1106 (`0x3C`, `GPIO41/42`), espressione `SPEAKING` vivace durante l'audio e ritorno a `NEUTRAL` al termine.
- `button_controller.h` / `button_controller.cpp` (`ButtonController`): lettura `GPIO47` (`INPUT_PULLUP`, attivo `LOW`) con debounce `40 ms` sul rilascio (un solo trigger per pressione).
- `serial_command_handler.h` / `serial_command_handler.cpp` (`SerialCommandHandler`): comandi `HELP`, `SPEAK`, `STOP`, `STATUS`, `VOLUME`, `VOLUME:<1..15>` a `115200 baud`.
- `display_driver.*`, `eye_engine.*`, `monochrome_fb.*`, `pinout_config.h`: copia isolata da Eyes 3.0.

---

## 4. Caricamento con Arduino IDE 2 e Test

1. Apri `04-Firmware\arduino-hw-test\jarvis_voice_hw_test\jarvis_voice_hw_test.ino`.
2. **Board**: `ESP32S3 Dev Module` | **Flash Size**: `16MB (128Mb)` | **Flash Mode**: `QIO 80MHz` | **PSRAM**: `OPI PSRAM`.
3. **USB CDC On Boot**: `Disabled` (porta **UART CH343**) oppure `Enabled` (porta **USB** nativa).
4. **Verifica** (`Ctrl+R`) → **Carica** (`Ctrl+U`) → **Monitor Seriale** (`115200 baud`).
5. Verifica:
   - `STATUS`: conferma `AUDIO=READY(IDLE)`, `OLED=0x3C(NEUTRAL)`, `VOL=5%(max=15%)`.
   - `SPEAK`: riproduzione chiara della frase italiana senza clic e occhi animati su `SPEAKING` → ritorno a `NEUTRAL`.
   - Pressione breve `GPIO47`: avvia `SPEAK` una sola volta (nessun rimbalzo multiplo).
   - `STOP` durante la frase: interrompe subito l'audio e riporta gli occhi a `NEUTRAL`.
   - `VOLUME:8` / `VOLUME:10` (opzionale, max `15%`).
