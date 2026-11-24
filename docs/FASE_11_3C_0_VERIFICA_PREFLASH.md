# FASE 11.3C.0 — Verifica finale prima del primo flash hardware

> **Stato**: Revisione pre-flash completata, due bug individuati e corretti nella sola variante isolata `jarvis_wifi_voice_client`, ricompilazione riuscita (`exit status 0`). Nessun flash eseguito, nessuna modifica al firmware stabile FASE 10.8 (`jarvis_duplex_rtos_hw_test/`), nessuna modifica a firewall/LAN/router.

---

## 1. Problemi individuati e correzioni effettuate

1. **Bug critico in `TtsSampleCount()`** ([network_task.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/network_task.h), [network_task.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/network_task.cpp)):
   - `TtsSampleCount()` leggeva il membro `tts_bytes_received_` (sempre `0`), mentre `OnWsEvent` aggiornava la variabile statica `g_tts_received`. Al termine della ricezione TTS, `jarvis_wifi_voice_client.ino` avrebbe copiato `0` campioni in `g_tx_buffer`.
   - **Correzione**: `TtsSampleCount()` ora restituisce `g_tts_received / sizeof(int16_t)`.
2. **Stato `ws_started` su errore `TLS_REQUIRED`** ([network_task.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/network_task.cpp)):
   - Quando né `use_tls` (con `ca_cert`) né `allow_insecure_lan_ws` erano attivi, `ws_started` veniva comunque impostato a `true` chiamando `g_ws.loop()` su un client non inizializzato.
   - **Correzione**: `ws_started = true` viene impostato solo dopo `beginSslWithCA(...)` o `begin(...)`.

## 2. Memoria (PSRAM, RAM e Stack)

- **Allocazioni PSRAM (`8 MB` OPI disponibili)**:
  - `g_rx_buffer` (`AudioBuffer`): `160.000 B` (`5 s` @ `16 kHz` PCM16 mono).
  - `g_tx_buffer` (`AudioBuffer`): `640.000 B` (`20 s` @ `16 kHz` PCM16 mono).
  - `NetworkBridgeClient::tts_buf_`: `640.000 B` (ricezione chunk binari WebSocket).
  - Totale audio PSRAM: **`1.440.000 B` (~`1,37 MiB`)** su `8 MiB` OPI (~`17%`), lasciando oltre `6,5 MiB` liberi.
- **Condivisione `tts_buf_` / `g_tx_buffer`**: sconsigliata in questa fase; mantenerli separati evita race condition tra `OnWsEvent` (Core 1) e `AudioPlayback` (Core 0) durante `STOP/CANCEL` o turni ravvicinati senza introdurre mutex sul percorso I²S real-time.
- **RAM interna e Stack**: variabili globali **`54.980 B` (`16%`)** su `327.680 B` (`272.700 B` liberi per heap Wi-Fi/TLS e stack FreeRTOS: `jarvis_net` `8192 B` su Core 1, `AudioCapture` `4096 B` e `AudioPlayback` `4096 B` su Core 0).
- **Errori di allocazione**: `setup()` controlla `g_rx_buffer.Allocate()` (fallback `32 KB` RAM), `g_tx_buffer.AllocateWithCapacity(...)` e `g_net.Begin(...)`; in caso di fallimento passa a `RobotState::kError`.

## 3. Flash e partizioni

- **Schema partizioni attualmente attivo** (`--show-properties` con `esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M`):
  - `build.partitions=default` (`Default 4MB with spiffs`, `upload.maximum_size=1.310.720 B` = `1,25 MiB` per app).
  - Occupazione attuale dopo le correzioni: **`1.152.989 B` (`87%`)** — margine residuo ~`157 KB`.
- **Valutazione per ESP32-S3 16 MB**: lo schema `default` sfrutta solo 4 MB dei 16 MB disponibili.
  - Per i prossimi sviluppi si consiglia (su autorizzazione al flash) `PartitionScheme=app3M_fat9M_16MB` (`upload.maximum_size=3.145.728 B`, app ~`36%`) oppure `PartitionScheme=huge_app` (`3.145.728 B`). Nessuna modifica automatica è stata applicata.

## 4. Stato funzionale e parti non ancora collaudate fisicamente

- **Verificato a livello di codice e compilazione**:
  - Driver INMP441 (`AudioCapture`, Core 0, GPIO4/5/6), MAX98357A (`AudioPlayback`, Core 0, GPIO7/15/16), SH1106 Eyes 3.0 (`EyeController`, GPIO41/42) e `GPIO47` (`ButtonController`) riusano il codice validato nella FASE 10.8.
  - Ricezione WebSocket binaria, controllo `TTS_TOO_LONG`/`PSRAM_OVERFLOW`, riconnessione con backoff, heartbeat `15 s`, `STOP/CANCEL`, TLS/WSS (`beginSslWithCA`) vs opt-in LAN.
- **Parti NON ancora collaudate fisicamente (compilazione ≠ collaudo hardware)**:
  - Intero ciclo reale su scheda ESP32-S3 (`WiFi.begin`, handshake `WebSocketsClient`, streaming reale verso `uvicorn`, latenza `Eyes 3.0` durante traffico Wi-Fi/TLS, qualità audio end-to-end).
  - Stabilità della regola di fallback `AudioBuffer` se mai mancasse la PSRAM.

## 5. Risultati test e ricompilazione

- **Compilazione `arduino-cli`** (`esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M`): **`exit status 0`** (`1.152.989 B` Flash `87%`, `54.980 B` RAM `16%`).
- **Test backend Python (`05-Voice-AI/.venv/Scripts/python.exe`)**:
  - `tests/test_esp32_ws_protocol.py` + `tests/test_voice_bridge.py` + `tests/test_voice_lab.py`: **26 test OK**.
  - Test preesistenti `05-Voice-AI` (ultima esecuzione invariata, senza modifiche ai moduli testati): **50 test OK**.
  - Simulatore `04-Firmware/jarvis-desk-buddy-sim` (ultima esecuzione invariata): **44 test OK**.

## 6. Rischi residui

- Margine Flash ridotto (`87%`) se si resta su `PartitionScheme=default` (in particolare se si abilita TLS/mbedTLS con certificati aggiuntivi).
- Necessità di test fisico su heap interno libero (`ESP.getFreeHeap()`) durante handshake Wi-Fi + TLS/WebSocket + I²S attivi contemporaneamente.
- Se nel primo test LAN si usasse `ws://` non cifrato (`JARVIS_ALLOW_INSECURE_LAN_WS=1`), il token dispositivo transiterebbe in chiaro sulla sola rete locale.

## 7. Procedura esatta per il primo flash e recupero del firmware stabile

1. **Preparazione credenziali locali**: copiare `wifi_secrets.example.h` in `wifi_secrets.h` (non versionato) con SSID, password, IP LAN del PC Windows, `JARVIS_ESP_DEVICE_TOKEN` e configurazione TLS/WSS (o `JARVIS_ALLOW_INSECURE_LAN_WS=1` esplicitamente autorizzato).
2. **Compilazione e flash su porta COM** (con partizione consigliata `PartitionScheme=app3M_fat9M_16MB` su scheda 16 MB):
   `arduino-cli compile --fqbn esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M,PartitionScheme=app3M_fat9M_16MB "04-Firmware\arduino-hw-test\jarvis_wifi_voice_client"`
   `arduino-cli upload -p COM<N> --fqbn esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M,PartitionScheme=app3M_fat9M_16MB "04-Firmware\arduino-hw-test\jarvis_wifi_voice_client"`
3. **Recupero immediato del firmware stabile FASE 10.8** (intatto e non modificato):
   `arduino-cli compile --upload -p COM<N> --fqbn esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M "04-Firmware\arduino-hw-test\jarvis_duplex_rtos_hw_test"`

## 8. Autorizzazioni necessarie per il collaudo reale (FASE 11.3C)

1. Creazione locale di `wifi_secrets.h` con SSID/password e scelta esplicita tra `WSS` (CA locale) o `ws://` LAN.
2. Apertura regola firewall Windows TCP `8765` per la sola subnet LAN privata.
3. Avvio del backend `jarvis-voice-bridge` su `0.0.0.0:8765` con `JARVIS_ESP_DEVICE_TOKEN` dedicato.
4. Autorizzazione esplicita al flash fisico sull'ESP32-S3-DevKitC-1.
