# FASE 12.27 — Flash controllato ESP32-S3 + collaudo fisico + rollback

**Data**: 2026-11-19  
**Stato**: **COMPLETATA — Flash controllato, verifica avvio/servizi, collaudo fisico (5/5 test superati) e verifica log/backup completati senza alterare il sistema stabile**

---

## 1. FASE A — Preflight e identificazione dispositivo

- **Porta seriale verificata**: `COM6` (`USB-Enhanced-SERIAL CH343`, `USB\VID_1A86&PID_55D3\5C83027497`, unico dispositivo seriale collegato).
- **Chip rilevato via `esptool v5.3.1`**: `ESP32-S3 (QFN56) (revision v0.2)`, Flash `16 MB`, Embedded PSRAM `8 MB (AP_3v3)`, MAC `<ESP32_MAC_ADDRESS>`.
- **Tabella partizioni letta da `0x8000` (`preflash_partitions.bin`)**:
  - `nvs`: `0x009000` (`20.480` B)
  - `otadata`: `0x00E000` (`8.192` B)
  - `app0`: `0x010000` (`1.310.720` B)
  - `app1`: `0x150000` (`1.310.720` B)
  - `spiffs`: `0x290000` (`1.441.792` B)
  - `coredump`: `0x3F0000` (`65.536` B)
- **Compatibilità verificata**: il binario compilato della FASE 12.26 (`1.155.664` B) rientra nella partizione `app0` esistente (`1.310.720` B) senza modificare partizioni o NVS.

---

## 2. Backup pre-flash (`05-Voice-AI/backups/fase12_27_preflash/`)

- **Backup completo 16 MB della Flash precedente**: `05-Voice-AI/backups/fase12_27_preflash/esp32_preflash_full_16mb_backup.bin` (`16.777.216` B, `SHA256 = 34D8C031F74E3227766757645881442574B59201C99CA8580ADDE5C940FC3CC6`).
- **Tabella partizioni pre-flash**: `preflash_partitions.bin`.
- **Copia sorgenti e config**: `*.h`, `*.cpp`, `*.ino` (escluso `wifi_secrets.h`), `config.py.preflash`, `esp_protocol.py.preflash`.
- **Backup storico FASE 10.8 (leggibile, non modificato)**: `%USERPROFILE%\Desktop\jarvis_flash_backups\jarvis_fase10_8_flash_backup.bin` (`SHA256 = 43B9A85F6E1B9D3BCB32D25A58C179DA384AF6F7C379EA2315E9690F9A9015A9`).
- **Binario FASE 12.26 caricato**: `jarvis_wifi_voice_client.ino.bin` (`1.155.664` B, `SHA256 = AED27D18E64FE65DFBD007D31CE40944607A7182880A8B02B347EE7F0EF57E14`).

---

## 3. FASE B — Flash controllato

Comando eseguito (senza `erase-flash`, senza modifica partizioni/bootloader/NVS):
```powershell
esptool.exe --chip esp32s3 --port COM6 --baud 921600 --before default-reset --after hard-reset write-flash -z --flash-mode dio --flash-freq 80m --flash-size 16MB 0x10000 "...\jarvis_wifi_voice_client.ino.bin"
```
- **Esito**: `exit code 0` — `Wrote 1155664 bytes (769503 compressed) at 0x00010000 in 10.6 seconds (873.4 kbit/s). Hash of data verified.`

---

## 4. FASE C & D — Primo avvio ESP32-S3, Voice Bridge e Ollama

- **Log seriale `COM6` (`115200` baud)**:
  - `[FASE 11.3B] JARVIS Wi-Fi Voice Client (isolated)`
  - `[MEM] AudioBuffer PSRAM alloc=256000 bytes (128000 samples @ 16000 Hz)`
  - `[MEM] AudioBuffer PSRAM alloc=640000 bytes (320000 samples @ 16000 Hz)`
  - `[OLED] Ready addr=0x3C SDA=GPIO41 SCL=GPIO42 driver=SH1106 (132x64 RAM, +2px col offset)`
  - `[MIC] I2S0 RX ready (RTOS task Core=0 Prio=3, WS=GPIO4 SCK=GPIO5 SD=GPIO6, 16kHz, shift=6)`
  - `[AUDIO] I2S1 TX ready (RTOS task Core=0 Prio=3, BCLK=GPIO15 LRC=GPIO16 DIN=GPIO7, 16kHz, vol=10%)`
  - `[AUDIO] Volume impostato a 12%` (ripristinato volume operativo 12%)
  - `[STATE] -> WIFI_CONNECTED` -> `[STATE] -> IDLE`
- **Ollama (`task-4206`, `127.0.0.1:11434`)**: attivo, `qwen2.5:3b` caricato in memoria (`keep_alive=30m`).
- **Voice Bridge (`task-4207`, `https://<PC_LAN_IP>:8765`)**:
  - Startup TTS: `Piper pronto (it_IT-riccardo-x_low.onnx, 16000 Hz, speed=1.00x, noise_scale=0.60, pitch=+5.0st, dsp=on, method=wsola, tanh=off)`
  - Prewarm Ollama: `ms=5754.2`
  - `/health`: `200 OK`
  - `/ready`: `200 OK` (`ready: true`)
  - ESP32 WSS: `<ESP32_LAN_IP>:61400 - "WebSocket /ws/v1/esp32" [accepted]`, `connection open`.

---

## 5. FASE E — Collaudo fisico ed evidenze log Voice Bridge (`task-4207.log`)

Tutte e 5 le prove fisiche sono state eseguite e confermate dall'utente senza errori, warning, reset o disconnessioni WebSocket:

| Test | Seq / Request ID | `ESP_AUDIO_RX` (`pcm_bytes` / `dur_s`) | `limit_reached` (`max=256000`) | `stt_ms` | `ai_ms` (`qwen2.5:3b`) | `tts_ms` | `TTS_READY` (`pcm_bytes` / `dur_s`) | `WSS TTS_SENT` | Esito utente |
| :--- | :--- | :--- | :---: | ---: | ---: | ---: | :--- | :--- | :--- |
| **A** (7+5) | `esp-1` / `req_980dadf12d04` | `87.040` B / `2.72 s` | `False` | 5960.6 | 1986.8 | 724.7 | `65.792` B / `2.06 s` | `65.792` B | **SUPERATO** |
| **B** (Marte) | `esp-2` / `req_d90d731b5c00` | `162.304` B / **`5.07 s`** | `False` | 2932.4 | 3968.4 | 1363.5 | `464.384` B / `14.51 s` | `464.384` B | **SUPERATO** |
| **C** (3 piccoli robot...) | `esp-3` / `req_bf829e1a3862` | `200.704` B / **`6.27 s`** | `False` | 2896.2 | 1851.2 | 854.4 | `186.880` B / `5.84 s` | `186.880` B | **SUPERATO (senza tagli)** |
| **D** (7–8 s) | `esp-4` / `req_6d901e1dc1f4` | `228.864` B / **`7.15 s`** | `False` | 3155.3 | 5212.3 | 1499.4 | `504.320` B / `15.76 s` | `504.320` B | **SUPERATO (nessun blocco)** |
| **E** (25+17) | `esp-5` / `req_4b07330377f7` | `137.216` B / `4.29 s` | `False` | 2802.8 | 1069.8 | 840.4 | `87.808` B / `2.74 s` | `87.808` B | **SUPERATO** |

### Analisi tecnica delle evidenze
- **Superamento effettivo del vecchio limite di `5.00 s` (`160.000` B)**: dimostrato oggettivamente dai test **B (`5.07 s` / `162.304` B)**, **C (`6.27 s` / `200.704` B)** e **D (`7.15 s` / `228.864` B)**, tutti accettati senza errori `PAYLOAD_TOO_LARGE`.
- **Risoluzione del taglio nel Test C**: la frase *"Tre piccoli robot preparano trenta programmi"* ha richiesto `6.27 s` di cattura vocale (`200.704` B) ed è stata ripetuta integralmente senza tagli.
- **Test D (`7.15 s`)**: ha verificato una registrazione lunga prossima agli `8 s` (`228.864` B, `limit_reached=False`); il comportamento al tetto esatto `256.000` B (`limit_reached=True`) è stato verificato nella suite automatica WebSocket della FASE 12.26 (`104/104 OK`).
- **Stabilità post-lunga (Test E)**: `esp-5` (`4.29 s`) elaborato regolarmente subito dopo `esp-4`, senza disconnessioni, errori o riavvii (nota: i valori di heap libero ESP32 post-Test D non erano monitorati su seriale perché `COM6` era chiusa durante i test vocali).
- **Limiti di osservabilità**: con `JARVIS_LOG_STT_DIAG_TEXT=False` e `JARVIS_LOG_CONVERSATION_TEXT=False`, i testi trascritti e generati non sono salvati nei log per privacy.

---

## 6. Verifica finale configurazione e integrità backup (`FASE 12.27F`)

- **`/ready` (`200 OK`)**: `Piper pronto (it_IT-riccardo-x_low.onnx, 16000 Hz, speed=1.00x, noise_scale=0.60, pitch=+5.0st, dsp=on, method=wsola, tanh=off)`, `Ollama attivo (1 modelli, selezionato qwen2.5:3b)`, `faster-whisper pronto (modello 'small', CPU int8)`.
- **Limiti confermati**: `kMaxRecordMs = 8000U`, `AudioBuffer` RX = `256.000` B, `esp_max_input_bytes = 256.000`, `esp_max_tts_bytes = 640.000`, `MAX_CHARS = 270`, volume ESP32 = `12%`.
- **Backup pre-flash verificato in sola lettura**: `05-Voice-AI/backups/fase12_27_preflash/esp32_preflash_full_16mb_backup.bin` — **`16.777.216` B**, **`SHA256 = 34D8C031F74E3227766757645881442574B59201C99CA8580ADDE5C940FC3CC6`** (integro e identico al pre-flash), insieme a `preflash_partitions.bin` e ai sorgenti/configurazione.

---

## 7. Piano di rollback

### Rollback A — Voice Bridge
Impostare `JARVIS_ESP_MAX_INPUT_BYTES=160000` oppure ripristinare `05-Voice-AI/backups/fase12_26/config.py.bak` ed `esp_protocol.py.bak` mantenendo il Profilo 08 invariato.

### Rollback B — Firmware ESP32-S3
Verificare prima dispositivo e porta seriale, quindi (solo su autorizzazione esplicita) ripristinare la partizione `app0` o l'immagine completa dal backup verificato immediatamente precedente al flash:
- `05-Voice-AI/backups/fase12_27_preflash/esp32_preflash_full_16mb_backup.bin` (`SHA256 = 34D8C031F74E3227766757645881442574B59201C99CA8580ADDE5C940FC3CC6`).
