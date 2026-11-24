# FASE 11.3C.13 — Aggiornamento firmware ESP32-S3 e collaudo volume

## 1. Backup e verifiche preliminari hardware

- **Backup integrale Flash 16 MB**: `%USERPROFILE%\Desktop\jarvis_flash_backups\jarvis_fase10_8_flash_backup.bin`
  - Dimensione: `16,777,216` byte
  - SHA-256: `43B9A85F6E1B9D3BCB32D25A58C179DA384AF6F7C379EA2315E9690F9A9015A9`
  - Esito verifica: `BACKUP_OK=True`
- **Porta seriale e target identificato** (`esptool v5.3.1`):
  - Porta: `COM6` (`USB-Enhanced-SERIAL CH343`, `USB\VID_1A86&PID_55D3\5C83027497`)
  - Chip: `ESP32-S3 (QFN56) (revision v0.2)`
  - Flash: `16MB` (`Detected flash size: 16MB`)
  - PSRAM: `Embedded PSRAM 8MB (AP_3v3)`
  - MAC: `<ESP32_MAC_ADDRESS>`
- **Firmware stabile FASE 10.8**: `04-Firmware/arduino-hw-test/jarvis_duplex_rtos_hw_test/` non modificato.

## 2. Modifiche applicate (`jarvis_wifi_voice_client`)

Intervento limitato al firmware isolato `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` (nessuna modifica a pinout, Wi-Fi, TLS/WSS, Voice Bridge, Piper o Whisper):

- `audio_playback.h`:
  - `kDefaultVolumePct`: `3` → `10`
  - `kMaxVolumePct`: `15` → `25`
- `audio_playback.cpp`:
  - `RunTaskLoop()` legge `const uint8_t vol = volume_pct_;` all'interno della sezione critica `portENTER_CRITICAL(&mux_)` per ogni chunk audio, così un cambio volume tramite `VOL <val>` ha effetto immediato anche durante la riproduzione TTS senza alterare I²S o WSS.
- `jarvis_wifi_voice_client.ino`:
  - Aggiunti `HandleSerialLine()` e `PollSerialCommands()` per supportare il comando seriale runtime `VOL <1..25>` (115200 baud) con validazione intera rigorosa e senza persistenza su NVS/Flash.

## 3. Compilazione e test automatici

- **Compilazione Arduino CLI** (`esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M`, `PartitionScheme=default`, nessuna cancellazione Flash):
  - Esito: `exit code 0`
  - Program storage: `1155485` byte (`88%` di `1310720` byte)
  - Variabili globali: `55036` byte (`16%` di `327680` byte, `272644` byte liberi)
- **Test unitari Python (`05-Voice-AI`)**:
  - Comando: `.\.venv\Scripts\python.exe -m unittest tests/test_esp32_ws_protocol.py tests/test_voice_bridge.py tests/test_voice_lab.py -v`
  - Esito: `Ran 29 tests in 7.337s — OK`

## 4. Flash su `COM6` e verifica seriale

- **Upload** (`arduino-cli upload -p COM6 --fqbn esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M`):
  - Esito: `exit code 0` (`1159168` byte, `769496` compressi, `Hash of data verified`, `Hard resetting via RTS pin...`)
- **Log di avvio verificato su `COM6` (`115200` baud)**:
  - `[MEM] AudioBuffer PSRAM alloc=160000 bytes (80000 samples @ 16000 Hz)`
  - `[MEM] AudioBuffer PSRAM alloc=640000 bytes (320000 samples @ 16000 Hz)`
  - `[OLED] Ready addr=0x3C SDA=GPIO41 SCL=GPIO42 driver=SH1106 (132x64 RAM, +2px col offset)`
  - `[MIC] I2S0 RX ready (RTOS task Core=0 Prio=3, WS=GPIO4 SCK=GPIO5 SD=GPIO6, 16kHz, shift=6)`
  - `[AUDIO] I2S1 TX ready (RTOS task Core=0 Prio=3, BCLK=GPIO15 LRC=GPIO16 DIN=GPIO7, 16kHz, vol=10%)`
  - `[STATE] -> WIFI_CONNECTED`
  - `[STATE] -> IDLE`
- **Verifica comando seriale `VOL` (senza salvataggio su Flash)**:
  - `VOL 0` → `[AUDIO] ERR: valore volume non valido (1..25, corrente=10%)`
  - `VOL 3` → `[AUDIO] Volume impostato a 3%`
  - `VOL 10` → `[AUDIO] Volume impostato a 10%`

## 5. Riconnessione WSS al Voice Bridge

- Voice Bridge attivo (`task-3456`, `<PC_LAN_IP>:8765`, Whisper `small/int8`, `JARVIS_LOG_STT_DIAG_TEXT=false`) confermato `RUNNING`.
- Dopo il riavvio dell'ESP32-S3, il dispositivo (`<ESP32_LAN_IP>`) si è riconnesso regolarmente via WSS:
  - `INFO:     <ESP32_LAN_IP>:52122 - "WebSocket /ws/v1/esp32" [accepted]`
  - `INFO:     connection open`

## 6. Procedura di rollback

- **Immediato (runtime via seriale `115200` baud su `COM6`)**: inviare `VOL 3` per riportare subito il volume al precedente valore `3%`.
- **Permanente via codice**: ripristinare `kDefaultVolumePct = 3` (e opzionalmente `kMaxVolumePct = 15`) in `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_playback.h`, ricompilare e riflashare su `COM6`.
- **Ripristino integrale Flash**: riflashare `%USERPROFILE%\Desktop\jarvis_flash_backups\jarvis_fase10_8_flash_backup.bin` con `esptool` su `COM6`.
