# FASE 12.26 — Estensione registrazione microfono a 8 secondi (ESP32-S3 + Voice Bridge)

**Data**: 2026-11-19  
**Stato**: **FASE 12.26 preparata e verificata — firmware compilato con successo, NON ancora installato (nessun flash eseguito sull'ESP32)**

---

## 1. Analisi tecnica e limiti individuati

La scansione completa di `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` e `05-Voice-AI/voice_bridge/` ha individuato tutti i punti vincolati al limite precedente di `5` secondi / `160.000` byte:

| Componente | File | Limite precedente | Nuovo limite (FASE 12.26) | Note |
| :--- | :--- | :--- | :--- | :--- |
| Firmware RX buffer | `audio_buffer.h` | `kDefaultMaxSeconds = 5U` (`80.000` campioni = `160.000` B) | **`8U`** (`128.000` campioni = `256.000` B) | Calcolato come `kSampleRateHz * kDefaultMaxSeconds` |
| Firmware loop RX | `jarvis_wifi_voice_client.ino` | `kMaxRecordMs = 5000U` | **`8000U`** + `static_assert` | Garantisce coerenza a compile-time con `AudioBuffer` |
| Firmware capture default | `audio_capture.h` | `max_duration_ms_ = 5000U` | **`8000U`** | Valore di default membro coerente |
| Firmware WS fallback | `ws_protocol.h` | `max_audio_bytes = 160000` | **`256000`** | `max_tts_bytes = 640000` **invariato** |
| Voice Bridge config | `voice_bridge/config.py` | `esp_max_input_bytes = 160000` | **`256000`** (`JARVIS_ESP_MAX_INPUT_BYTES`) | `esp_max_tts_bytes = 640000` **invariato** |
| Voice Bridge diagnostica | `voice_bridge/esp_protocol.py` | Nessun log su `limit_reached` | Log `ESP_AUDIO_RX` (`pcm_bytes`, `dur_s`, `max_bytes`, `limit_reached`) | Zero testo privato nei log |

- **Limiti già compatibili e non modificati**:
  - `max_wav_bytes = 524288` (`512 KB` > `256.044` B WAV da 8 s)
  - `max_audio_duration_s = 15.0` (`> 8.0` s)
  - `esp_ws_idle_timeout_s = 60.0` (upload da `256.000` B in chunk da `2048` B = `125` frame in ~`125 ms`)
  - `esp_max_tts_bytes = 640000` (`20 s` TTS in uscita — **rigorosamente invariato**)
  - **Profilo vocale 08** (`it_IT-riccardo-x_low`, `speed=1.00`, `noise_scale=0.60`, `pitch=+5.0st`, `wsola`, `limiter_enabled=False`, `MAX_CHARS=270`): **rigorosamente invariato**.

---

## 2. Calcolo dei buffer e verifica memoria ESP32-S3 (N16R8)

- **Audio in ingresso (`16000 Hz`, mono, `PCM16`)**: `16000 * 2 = 32.000` byte/s -> per `8 s`: **`256.000` byte** (`128.000` campioni `int16_t`).
- **Allocazione PSRAM (`8 MB` disponibili su N16R8)**:
  - `g_rx_buffer` (PSRAM `ps_malloc`): `256.000` B (`+96.000` B rispetto ai `160.000` B precedenti)
  - `g_tx_buffer` (PSRAM `ps_malloc`): `640.000` B (invariato)
  - `NetworkBridgeClient::tts_buf_` (PSRAM `heap_caps_malloc` SPIRAM): `640.000` B (invariato)
  - **Totale buffer audio PSRAM**: `1.536.000` B (`1.46 MB` su `8 MB` disponibili -> ~`6.5 MB` residui).
- **RAM interna / DMA**: invariata (`AudioCapture::task_pcm_buf_` = `512` B, `AudioPlayback::stereo_buf_` = `1024` B). Nessuna copia aggiuntiva in upload (`network_task.cpp` trasmette a chunk da `2048` B direttamente da `g_rx_buffer`).
- **Comportamento pulsante GPIO47**: invariato; se l'utente rilascia prima degli 8 s, la registrazione termina immediatamente e invia solo i campioni acquisiti.

---

## 3. Compilazione firmware ESP32-S3 (senza flash)

Comando eseguito con `C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe`:
```powershell
arduino-cli compile --fqbn "esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M,PartitionScheme=app3M_fat9M_16MB" "04-Firmware\arduino-hw-test\jarvis_wifi_voice_client"
```
- **Esito**: **COMPILAZIONE RIUSCITA (`exit code 0`)** — `static_assert` superato.
- **Flash programma**: `1.155.517` byte (`36%` di `3.145.728` byte).
- **RAM dinamica globale**: `55.036` byte (`16%` di `327.680` byte), `272.644` byte liberi per variabili locali.
- **Flash eseguito?**: **NO** (blocco obbligatorio rispettato).

---

## 4. Test automatici Voice Bridge

- Nuovo test suite [05-Voice-AI/tests/test_fase12_26_esp_input_8s.py](05-Voice-AI/tests/test_fase12_26_esp_input_8s.py):
  - Default `BridgeConfig.from_env()` (`esp_max_input_bytes == 256000`, `esp_max_tts_bytes == 640000`, Profilo 08 invariato).
  - `auth_ok` con `max_audio_bytes: 256000` e `max_tts_bytes: 640000`.
  - Upload WebSocket validi da **`1 s`, `3 s`, `5 s`, `7 s`, `8 s` esatti (`256.000` B)**.
  - Superamento degli `8 s` (`258.048` B) rifiutato con `PAYLOAD_TOO_LARGE`.
  - Buffer vuoto (`0` B) e byte dispari (`101` B) rifiutati con `INVALID_AUDIO_PAYLOAD`.
  - Disconnessione anticipata a metà upload gestita senza errori residui.
  - Log diagnostico `ESP_AUDIO_RX pcm_bytes=256000 dur_s=8.00 max_bytes=256000 limit_reached=True`.
- **Suite completa (`python -m unittest discover -s tests -q`)**: **`Ran 104 tests in 42.211s — OK`** (`0` errori, `0` fallimenti).

*(Nota: i test hardware reali su microfono INMP441 e PSRAM fisica dell'ESP32 non sono stati eseguiti perché il firmware non è stato ancora flashato.)*

---

## 5. Backup e procedura di rollback

- **Backup FASE 12.26 creati in `05-Voice-AI/backups/fase12_26/`**:
  - `audio_buffer.h.bak`, `audio_capture.h.bak`, `ws_protocol.h.bak`, `jarvis_wifi_voice_client.ino.bak`, `config.py.bak`, `esp_protocol.py.bak`, `previous_limits.json`.
- **Backup flash FASE 10.8 preservato (non modificato)**:
  - `%USERPROFILE%\Desktop\jarvis_flash_backups\jarvis_fase10_8_flash_backup.bin` (`16.777.216` B, `.sha256` presente; nota: rappresenta il backup di FASE 10.8, non include il firmware Wi-Fi client della FASE 11.3B).
- **Rollback**:
  - **Voice Bridge**: impostare `JARVIS_ESP_MAX_INPUT_BYTES=160000` oppure ripristinare `config.py.bak` ed `esp_protocol.py.bak`.
  - **Firmware**: ripristinare i 4 file `.bak` in `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` e ricompilare.

---

## 6. Stato dei processi Windows e autorizzazione flash

- **Processi attivi verificati**: `python`, `uvicorn` e `ollama` risultano **non in esecuzione** (terminati al riavvio precedente dell'IDE; nessun servizio è stato riavviato automaticamente).
- **Autorizzazione flash**: **NON autorizzato in questa fase**. Nessun caricamento, reset o scrittura su Flash/NVS è stato effettuato. Prima di un eventuale futuro flash su `COM6`, verificare la porta seriale effettivamente collegata.
