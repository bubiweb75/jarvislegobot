# FASE 11.3A — Integrazione Wi-Fi ESP32-S3 ↔ Voice Bridge (Sviluppo e test isolati)

> **Stato fase**: Progettazione, sviluppo isolato e test automatici senza flash hardware. Nessuna modifica al firmware stabile FASE 10.8 (`jarvis_duplex_rtos_hw_test/`), nessun flash su ESP32-S3, nessuna esposizione LAN/firewall attivata.

---

## 1. Architettura proposta e implementata

- **Lato Backend (`05-Voice-AI/voice_bridge/`)**:
  - Aggiunto adapter WebSocket dedicato `WS /ws/v1/esp32` ([esp_protocol.py](05-Voice-AI/voice_bridge/esp_protocol.py), registrato in [api.py](05-Voice-AI/voice_bridge/api.py)), separato dagli endpoint HTTP del browser (`/api/v1/*`).
  - Il server continua a restare in ascolto su `127.0.0.1` nei profili di test locale; l'eventuale binding LAN (`JARVIS_BRIDGE_HOST=0.0.0.0`) è previsto come profilo esplicito da autorizzare in FASE 11.3B.
- **Lato Firmware ESP32-S3 (`04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/`)**:
  - Nuova variante isolata con FreeRTOS dual-core:
    - **Core 0**: `AudioCapture` (`I2S_NUM_0` INMP441, GPIO4/5/6) e `AudioPlayback` (`I2S_NUM_1` MAX98357A, GPIO7/15/16) dalla FASE 10.8.
    - **Core 1**: logica principale, `GPIO47` (`INPUT_PULLUP`, active LOW), `EyeController` (SH1106 `128×64` su GPIO41/42) e `NetworkBridgeClient` (`jarvis_net`, priorità `1`, non bloccante per il loop OLED).

## 2. Inventario dei componenti riutilizzati

- **Backend**: `VoiceBridgeService` (`STT` `FasterWhisperEngine`, `LocalIntentHandler`, `AIRouter` Ollama/Cloud/Offline, `PiperTTSEngine`, `TempAudioStore`, `BridgeDiagnostics`, `CancellationToken`, `encode_wav_mono_16bit`).
- **Firmware FASE 10.8 (`jarvis_duplex_rtos_hw_test/`)**: `pinout_config.h`, `audio_buffer.*`, `audio_capture.*`, `audio_playback.*`, `eye_controller.*`, `eye_engine.*`, `display_driver.*`, `monochrome_fb.*`, `button_controller.*` (non modificati).

## 3. Libreria WebSocket scelta e motivazione

- **Libreria scelta per ESP32-S3**: `Links2004/arduinoWebSockets` (`WebSocketsClient`, licenza LGPL-2.1).
  - Supporta nativamente frame testo JSON e frame binari separati, riconnessione automatica, e connessione cifrata `beginSslWithCA(...)` con certificato CA locale su `WiFiClientSecure` oltre a `begin(...)` per test LAN.
  - **Nota toolchain**: su questo PC non sono installati `arduino-cli`, `pio` né la libreria `Links2004/arduinoWebSockets` in `Documents\Arduino\libraries` (solo `U8g2` presente); la compilazione del firmware isolato non è quindi stata eseguita localmente e non sono state installate librerie automaticamente.

## 4. Protocollo JSON / binario (`v1.0`)

- **Frame JSON (controllo)**:
  - `auth` (`device_id`, `token`) -> `auth_ok` (`session_id`, `max_audio_bytes=160000`, `max_tts_bytes=640000`, `chunk_bytes=2048`)
  - `ping` (`ts`) -> `pong` (`ts`)
  - `audio_start` (`request_id`, `sr=16000`, `ch=1`, `bits=16`) -> `ack` (`stage="audio_start"`)
  - `audio_end` (`request_id`, `samples`) -> avvia `VoiceBridgeService.process_voice(...)` -> `tts_start` (`sr`, `ch`, `bits`, `total_bytes`, `provider_used`, `transcript`) -> chunk binari -> `tts_end` (`total_bytes`, `timings`)
  - `cancel` (`request_id`) -> `cancelled` (`request_id`)
  - `error` (`code`, `message`, `request_id` opzionale): `UNAUTHORIZED`, `SESSION_TIMEOUT`, `MALFORMED_JSON`, `UNEXPECTED_BINARY`, `FRAME_TOO_LARGE`, `PAYLOAD_TOO_LARGE`, `DUPLICATE_REQUEST`, `UNSUPPORTED_AUDIO_FORMAT`, `TTS_TOO_LONG`.
- **Frame binari**: solo PCM16 mono 16 kHz grezzo, chunk nominali `2048 B` (`64 ms`), frame massimo accettato `8192 B`.

## 5. Strategia di autenticazione e sicurezza

- Token dispositivo dedicato `JARVIS_ESP_DEVICE_TOKEN`, separato dal token browser `JARVIS_BRIDGE_TOKEN` (verificato con `hmac.compare_digest` e redatto nei log via `BridgeDiagnostics`).
- Nessuna credenziale o SSID/password nei file versionati (`wifi_secrets.example.h` contiene solo placeholder; `wifi_secrets.h` va escluso da Git).
- **Nota TLS/WSS**: il client firmware supporta `beginSslWithCA` (`JARVIS_WS_USE_TLS=1`). L'uso di `ws://` non cifrato in LAN (`JARVIS_ALLOW_INSECURE_LAN_WS=1`) espone il token dispositivo al traffico LAN locale e richiede autorizzazione esplicita prima dell'uso reale.

## 6. Gestione audio e memoria

- **Upload**: buffer PSRAM fino a `160.000 B` (`5 s` @ `16 kHz` PCM16 mono), inviato al rilascio di `GPIO47` a blocchi da `2048 B`.
- **Risposta TTS**: il backend estrae i frame PCM16 mono 16 kHz dal WAV di Piper e verifica `len(out_pcm) <= 640.000 B` (`20 s`); se eccede, restituisce `TTS_TOO_LONG` evitando overflow o troncamenti silenziosi. L'ESP32 alloca in PSRAM un buffer RX dedicato da `640 KB` (`kMaxTtsPsramBytes`).

## 7. Gestione FreeRTOS e macchina a stati

- Stati definiti in `RobotState` ([ws_protocol.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/ws_protocol.h)): `IDLE`, `WIFI_CONNECTING`, `WIFI_CONNECTED`, `RECORDING`, `UPLOADING`, `PROCESSING`, `RECEIVING`, `PLAYING`, `ERROR`, `CANCELLED`.
- `jarvis_net` gira su **Core 1** con code FreeRTOS (`g_tx_queue`, `g_ev_queue`) non bloccanti per mantenere fluide le animazioni Eyes 3.0 e la risposta `STOP/CANCEL` di `GPIO47`, lasciando il **Core 0** libero per I²S RX/TX.

## 8. File creati e modificati

- Creati:
  - `05-Voice-AI/voice_bridge/esp_protocol.py`
  - `05-Voice-AI/tests/test_esp32_ws_protocol.py`
  - `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/wifi_secrets.example.h`
  - `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/ws_protocol.h`
  - `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/ws_protocol.cpp`
  - `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/network_task.h`
  - `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/network_task.cpp`
  - `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/jarvis_wifi_voice_client.ino`
  - `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/README.md`
  - `docs/FASE_11_3A_INTEGRAZIONE_WIFI_PROTOCOLLO.md`
- Modificati:
  - `05-Voice-AI/voice_bridge/config.py`
  - `05-Voice-AI/voice_bridge/pipeline.py`
  - `05-Voice-AI/voice_bridge/api.py`

## 9. Test eseguiti e risultati (tutti con mock STT/AI/TTS, senza flash hardware)

Eseguiti con `05-Voice-AI/.venv/Scripts/python.exe` dopo le modifiche finali:

1. `unittest tests/test_esp32_ws_protocol.py tests/test_voice_bridge.py tests/test_voice_lab.py -v` -> **26 test OK** (tutti i 15 scenari di protocollo ESP32 WebSocket + compatibilità Voice Bridge/Voice Lab).
2. `unittest tests/test_control_center.py tests/test_conversation_engine.py tests/test_conversation_naturalizer.py tests/test_memory_engine.py tests/test_voice_ai.py -v` -> **50 test OK**.
3. `unittest test_behavior_engine.py test_sensor_manager.py test_simulator.py test_touch_manager.py -v` (in `04-Firmware/jarvis-desk-buddy-sim`) -> **44 test OK**.

## 10. Limitazioni e problemi aperti

- **Hardware non collaudato**: nessun flash o test Wi-Fi reale sull'ESP32-S3 è stato ancora eseguito.
- **Librerie mancanti (non installate per vincolo)**:
  - In `05-Voice-AI/.venv` mancano `websockets`/`wsproto` per servire WebSocket reali con `uvicorn` (i test in-process con `TestClient` funzionano già).
  - Su Windows mancano `arduino-cli` e `Links2004/arduinoWebSockets` per la compilazione da riga di comando.

## 11. Requisiti per il primo collegamento reale

1. Installare `websockets` in `05-Voice-AI/.venv` (per `uvicorn` WebSocket reale).
2. Installare `Links2004/arduinoWebSockets` nell'ambiente Arduino IDE/CLI e creare `wifi_secrets.h` locale (non versionato).
3. Scegliere il canale di trasporto (TLS/WSS con CA locale oppure `ws://` LAN esplicitamente autorizzato per test).
4. Autorizzare il binding LAN (`0.0.0.0:8765`) e la regola firewall locale per la sola subnet domestica sul PC Windows.

## 12. Piano della FASE 11.3B (in attesa di autorizzazione)

1. Richiedere autorizzazione per installare `websockets` in `.venv` e `Links2004/arduinoWebSockets` su Arduino.
2. Configurare `wifi_secrets.h`, compilare e flashare `jarvis_wifi_voice_client` sull'ESP32-S3.
3. Avviare `jarvis-voice-bridge` sul profilo LAN autorizzato con `JARVIS_ESP_DEVICE_TOKEN`.
4. Eseguire il collaudo reale end-to-end con `GPIO47` → `INMP441` → Wi-Fi → `Whisper` → `AI Router` → `Piper` → `MAX98357A` + `Eyes 3.0`.
