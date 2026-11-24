# JARVIS LEGO BOT — Firmware Stabile FASE 13.8 (`jarvis_wifi_voice_client`)

Firmware ufficiale su **ESP32-S3-DevKitC-1 N16R8** con riconoscimento vocale locale continuo **«Hey Jarvis»**, animazioni **Eyes 3.0** su OLED I²C, conversazione vocale bidirezionale via Wi-Fi WebSocket (`WSS` TLS) con **Voice Bridge** (`faster-whisper` + `Ollama qwen2.5:3b` + `Piper Profilo 08`), **VAD adattivo**, **protezione anti-ri-trigger**, **speaker silenzioso in IDLE** e **diagnostica `STAT`**.

---

## 1. Architettura Firmware (Core 0 / Core 1)

| Modulo | Responsabilità | Core / Risorse |
|---|---|---|
| `AudioCapture` (`audio_capture.*`) | Unico proprietario di `I2S_NUM_0` (`16 kHz` PCM16, rimozione DC). In `IDLE` esegue wake word + `PreRollRingBuffer` (`500 ms` PSRAM); in `RECORDING` applica `VoiceActivityDetector`. | Core 0 (`jarvis_audio_rx`, prio `3`, stack `12.288` B) |
| `AudioPlayback` (`audio_playback.*`) | Riproduzione `I2S_NUM_1` (`16 kHz` stereo, fade 20 ms) + `WriteZeroFlush(960)` a chunk `<= 256` al boot e a fine playback per mantenere lo speaker silenzioso in `IDLE`. | Core 0 (`jarvis_audio_tx`, prio `3`, stack `4.096` B) |
| `NetworkBridgeClient` (`network_task.*`) | Connessione Wi-Fi + `WebSocketsClient` TLS verso `/ws/v1/esp32`, upload PCM16, ricezione TTS PSRAM (`max 640 KB`). | Core 1 (`network_task`) |
| `EyeController` / `EyeEngine` | Rendering non bloccante **Eyes 3.0** su OLED `SH1106` / `SSD1306` (`I2C 400 kHz`, `30 FPS`). | Core 1 (`loop()`) |
| `ButtonController` | Debounce e fronti di `GPIO47` (push-to-talk e `STOP/CANCEL`). | Core 1 (`loop()`) |

---

## 2. Wake Word, Anti-Ri-Trigger, VAD e Stati Eyes 3.0

- **Modello wake word**: `hey_jarvis_v2_int8` (`52.272` B, `Chirale_TensorFlowLite 2.0.0`, microfrontend 40 bin, soglia `0.970`, sliding window `5`, inferenza `~2.92 ms`).
- **Stati `RobotState` → `Eyes 3.0`**:
  - `IDLE` → `Neutral` (movimenti naturali degli occhi, sguardi e battiti di palpebre; wake word attiva in background; speaker silenzioso; nessun invio audio al PC).
  - `RECORDING` → `Listening`
  - `UPLOADING` / `PROCESSING` / `RECEIVING` → `Thinking` (wake word sospesa)
  - `PLAYING` → `Speaking` (wake word sospesa)
  - `ERROR` → `Confused` (recupero automatico a `IDLE` dopo `2.0 s`)
- **Protezione anti-ri-trigger**: al rientro in `IDLE`, scarto controllato di `200 ms` (`20` frame) dal DMA `I2S_NUM_0` + guardia post-ciclo di `1500 ms` con warm-up continuo (estesa a passi di `150 ms` se `smooth >= 0.30`, senza usare `ResetAll()` sui tensori INT8).
- **VAD adattivo (`vad_controller.h`)**:
  - Stima continua `noise_floor_rms_` in `IDLE` (`clamp 80..1500`), soglia parlato `max(360, 2.4 × noise)` su `4` chunk consecutivi (`~64 ms`).
  - Finestra cieca iniziale `300 ms` post-wake (senza troncare il PCM16 registrato né il `pre-roll` da `500 ms`) per ignorare la coda di *«Hey Jarvis»*.
  - Chiusura automatica dopo `1100 ms` di silenzio post-parlato, timeout `no-speech` a `2500 ms` (nessun upload al PC) e limite massimo `8000 ms`.
- **Pulsante `GPIO47`**: in `IDLE` avvia registrazione push-to-talk; durante `RECORDING` (da wake word), `PROCESSING` o `PLAYING` interrompe subito (`CANCELLED → IDLE`).

---

## 3. Pinout Hardware (`ESP32-S3-DevKitC-1 N16R8`)

| Periferica | Segnale | GPIO |
|---|---|---|
| **OLED `SH1106` `0x3C`** | `SDA` / `SCL` (`I2C 400 kHz`) | `GPIO41` / `GPIO42` |
| **Microfono `INMP441`** (`I2S_NUM_0`) | `WS` / `SCK` / `SD` (`L/R=GND`) | `GPIO4` / `GPIO5` / `GPIO6` |
| **Amplificatore `MAX98357A`** (`I2S_NUM_1`) | `BCLK` / `LRC` / `DIN` | `GPIO15` / `GPIO16` / `GPIO7` |
| **Pulsante** | Attivazione / Cancel (attivo LOW) | `GPIO47` |

*(Pin vietati/riservati: `GPIO35–37` Octal PSRAM, `GPIO0/3/45/46` strapping, `GPIO19/20` USB, `GPIO43/44` UART0).*

---

## 4. Diagnostica Seriale (`115200` baud)

- `STAT`: stampa stato corrente, `heap`, `min_heap`, `psram`, `rx_hwm` (stack libero task audio Core 0), `noise` e `thr` adattivo del VAD.
- `VOL <1..25>`: imposta il volume software di riproduzione (`default 10%`).
- `JARVIS_DEBUG_VERBOSE` (`debug_config.h`, `0` in produzione): abilita/disabilita i log verbosi per risparmiare Flash.

---

## 5. Compilazione e Riproducibilità

1. Copiare `wifi_secrets.example.h` in `wifi_secrets.h` (escluso da Git) e inserire credenziali Wi-Fi / token / CA LAN.
2. Dipendenze richieste:
   - Core Arduino `esp32:esp32` `3.3.13` (`ESP_I2S`, `Wire`, `WiFi`, `NetworkClientSecure`, `SPI`)
   - `U8g2` (`2.36.19`) e `WebSockets` (`2.7.2`) in `Documents\Arduino\libraries`
   - `Chirale_TensorFLowLite-2.0.0` in `04-Firmware/experiments/fase13-wakeword/libs`
3. Comando `arduino-cli`:
```powershell
arduino-cli compile --fqbn "esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M,DebugLevel=none" `
  --libraries "04-Firmware\experiments\fase13-wakeword\libs" `
  --libraries "$env:USERPROFILE\Documents\Arduino\libraries" `
  "04-Firmware\arduino-hw-test\jarvis_wifi_voice_client"
```
4. Test logici host: `python 04-Firmware\arduino-hw-test\jarvis_wifi_voice_client\tests\test_fase13_4_logic.py`.

---

## 6. Limiti Attuali Partizione `app0` e Ripristino FASE 12.27

- **Limite `app0`**: il binario occupa `~1.299.328` B (`99%`) su `1.310.720` B (`~11 KB` liberi). Qualsiasi espansione futura di codice richiederà il passaggio a una tabella partizioni `Huge APP` (`3 MB`) su Flash `16 MB`.
- **Versione precedente archiviata**: i sorgenti FASE 12.27 sono conservati integralmente in `04-Firmware/archive/fase12_27_jarvis_wifi_voice_client/`.
- **Ripristino FASE 12.27 su `COM6`** (sola partizione `app0 @ 0x10000`, senza toccare bootloader/NVS/otadata):
```powershell
esptool --chip esp32s3 --port COM6 --baud 921600 write-flash -z --flash-mode dio --flash-freq 80m --flash-size 16MB `
  0x10000 "05-Voice-AI\backups\fase13_2_preflash\fase12_27_app0_rollback.bin"
```
