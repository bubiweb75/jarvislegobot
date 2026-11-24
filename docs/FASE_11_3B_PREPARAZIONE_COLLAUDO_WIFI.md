# FASE 11.3B — Preparazione al primo collaudo Wi-Fi reale

> **Stato**: Verifica tecnica e preparazione completate. Nessun flash eseguito, nessuna dipendenza installata senza autorizzazione, nessuna modifica al firmware stabile FASE 10.8 (`jarvis_duplex_rtos_hw_test/`), nessuna apertura firewall o esposizione LAN.

---

## 1. Disponibilità toolchain ed esito della compilazione reale

- **Toolchain individuata**:
  - `arduino-cli.exe` integrato in Arduino IDE: `C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe`
  - Core ESP32 installato: `esp32:esp32` versione `3.3.13` (`%USERPROFILE%\AppData\Local\Arduino15\packages\esp32\hardware\esp32\3.3.13`)
  - Librerie già presenti e rilevate: `ESP_I2S 3.3.13`, `Wire 3.3.13`, `WiFi 3.3.13`, `Networking 3.3.13`, `U8g2 2.36.19`.
- **Comando eseguito**:
  `arduino-cli.exe compile --fqbn esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M "04-Firmware\arduino-hw-test\jarvis_wifi_voice_client"`
- **Esito compilazione**: **fallita (exit status 1)** esclusivamente per assenza della libreria WebSocket non ancora autorizzata all'installazione:
  `network_task.cpp:5:10: fatal error: WebSocketsClient.h: No such file or directory`

## 2. Problemi rilevati e correzioni effettuate

1. **Collegamento driver audio/display nello sketch isolato (`jarvis_wifi_voice_client`)**:
   - Nella FASE 11.3A lo sketch `jarvis_wifi_voice_client.ino` era uno scheletro privo dei file driver FASE 10.8 e senza collegamento tra `AudioCapture`, `AudioPlayback`, `EyeController` e `ButtonController`.
   - **Correzione effettuata**: copiati nella cartella isolata `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` i 17 file driver riutilizzabili da `jarvis_duplex_rtos_hw_test/` (senza modificare l'originale FASE 10.8) e completato `jarvis_wifi_voice_client.ino` con la macchina a stati completa (`GPIO47` Push-to-Talk + `STOP/CANCEL`, `AudioCapture` → `SubmitVoiceUpload`, `kTtsReady` → `AudioPlayback` e `g_eyes.Update()` non bloccante).
2. **Capacità buffer PSRAM TTS (`640 KB` vs `160 KB`)**:
   - `AudioBuffer` della FASE 10.8 aveva capacità fissa `80.000` campioni (`160 KB` = `5 s`).
   - **Correzione effettuata**: aggiunto `AudioBuffer::AllocateWithCapacity(primary_samples, fallback_samples)` e `Data()` nella copia isolata `jarvis_wifi_voice_client/audio_buffer.*`, allocando `g_rx_buffer` (`160 KB` = `5 s`) e `g_tx_buffer` (`640 KB` = `320.000` campioni = `20 s`).

## 3. Controlli specifici su PSRAM, audio, protocollo, FreeRTOS e sicurezza

- **Buffer TTS da `640 KB`**: sufficiente per risposte fino a `20 s` @ `16 kHz` PCM16 mono. Se Piper genera più di `640.000 B`, il backend restituisce esplicitamente `TTS_TOO_LONG` (nessun overflow o troncamento silenzioso).
- **Coerenza formato audio**: Piper (`it_IT-riccardo-x_low.onnx`) produce WAV `16.000 Hz`, `1 ch`, `16-bit PCM`; `esp_protocol.py` estrae i frame PCM16 grezzi e `AudioPlayback` (Core 0) li converte in stereo L=R per MAX98357A.
- **Timeout, riconnessioni e CANCEL**: timeout idle backend (`60 s`, configurabile), backoff esponenziale `1 s -> 15 s` su ESP32, heartbeat `15 s`, e `STOP/CANCEL` su `GPIO47` che arresta `AudioPlayback` e invia `{"v":"1.0","type":"cancel"}`.
- **FreeRTOS & Eyes 3.0**: Core 0 riservato ai task I²S (`AudioCapture` / `AudioPlayback`, priorità `3`); Core 1 esegue `jarvis_net` (priorità `1`) e `loop()` con `g_eyes.Update(now_ms)` privo di chiamate di rete bloccanti.
- **Sicurezza implementata**:
  - Token dispositivo `JARVIS_ESP_DEVICE_TOKEN` separato da `JARVIS_BRIDGE_TOKEN` (verificato con `hmac.compare_digest` e redatto dai log in `BridgeDiagnostics`).
  - `wifi_secrets.example.h` contiene solo placeholder; `wifi_secrets.h` non è versionato.
  - Il client firmware richiede esplicitamente `JARVIS_WS_USE_TLS=1` (CA cert) oppure l'opt-in `JARVIS_ALLOW_INSECURE_LAN_WS=1`; con entrambi a `0` rifiuta la connessione (`TLS_REQUIRED`).

## 4. Dipendenze necessarie (in attesa di autorizzazione)

1. **`Links2004/arduinoWebSockets`** (libreria Arduino, licenza LGPL-2.1, sorgente `https://github.com/Links2004/arduinoWebSockets`): necessaria per compilare `network_task.cpp` (`WebSocketsClient.h`). Impatto: installazione locale in `Documents\Arduino\libraries\WebSockets`.
2. **`websockets`** (pacchetto Python PyPI) in `05-Voice-AI/.venv`: necessario affinché `uvicorn` possa accettare connessioni WebSocket reali su `/ws/v1/esp32` (non richiesto dai test in-process `TestClient`). Impatto: solo nell'ambiente virtuale `05-Voice-AI/.venv`.

## 5. Risultati dei test automatici

Eseguiti con `05-Voice-AI/.venv/Scripts/python.exe` dopo le modifiche finali:

- `unittest tests/test_esp32_ws_protocol.py tests/test_voice_bridge.py tests/test_voice_lab.py -v`: **26 test OK** (mock STT/AI/TTS).
- Test preesistenti `05-Voice-AI` (ultima esecuzione invariata): **50 test OK**.
- Simulatore `04-Firmware/jarvis-desk-buddy-sim` (ultima esecuzione invariata): **44 test OK**.

## 6. Istruzioni proposte per il collegamento LAN del PC Windows (NON applicate)

Per il successivo collaudo reale sulla sola rete domestica:
1. Creare una regola firewall Windows in ingresso TCP sulla porta `8765` limitata alla sola subnet LAN locale (es. `<LAN_IP>/24`, profilo Privato).
2. Avviare `jarvis-voice-bridge` con `JARVIS_BRIDGE_HOST=0.0.0.0`, `JARVIS_BRIDGE_PORT=8765`, `JARVIS_ESP_DEVICE_TOKEN="<token_dispositivo>"` (separato da `JARVIS_BRIDGE_TOKEN`).
3. Compilare `wifi_secrets.h` con SSID/password locali, IP LAN del PC Windows e `JARVIS_ESP_DEVICE_TOKEN`.

## 7. Elenco delle autorizzazioni ancora necessarie

1. Installazione di `Links2004/arduinoWebSockets` nell'ambiente Arduino locale e nuova compilazione di verifica.
2. Installazione di `websockets` in `05-Voice-AI/.venv`.
3. Creazione `wifi_secrets.h` locale e scelta tra `WSS` con CA locale o `ws://` LAN per il primo test.
4. Apertura porta `8765` sul firewall Windows (solo profilo Privato / subnet LAN) e avvio del server su `0.0.0.0:8765`.
5. Autorizzazione al flash su ESP32-S3-DevKitC-1 e al collaudo hardware reale (FASE 11.3C).
