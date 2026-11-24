# FASE 11.3B.1 — Installazione dipendenze e compilazione completa

> **Stato**: Dipendenze di sviluppo installate secondo autorizzazione e compilazione isolata completata con successo (`exit status 0`). Nessun flash hardware eseguito, nessuna modifica al firmware stabile FASE 10.8 (`jarvis_duplex_rtos_hw_test/`), nessuna modifica a firewall/LAN/router.

---

## 1. Dipendenze installate e versioni verificate

1. **Arduino (`Documents\Arduino\libraries`)**:
   - `WebSockets` (`Links2004/arduinoWebSockets`): versione **`2.7.2`** (installata tramite `arduino-cli lib install "WebSockets"`).
   - Compatibilità verificata con core **`esp32:esp32 3.3.13`** e librerie `ESP_I2S 3.3.13`, `WiFi 3.3.13`, `Networking 3.3.13`, `NetworkClientSecure 3.3.13`, `Wire 3.3.13`, `SPI 3.3.13`, `U8g2 2.36.19`.
2. **Python (`05-Voice-AI/.venv`)**:
   - `websockets`: versione **`17.4`** (installata esclusivamente in `05-Voice-AI/.venv`, nessuna modifica al Python globale).

## 2. Correzioni effettuate nella sola variante isolata

- [jarvis_wifi_voice_client.ino](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/jarvis_wifi_voice_client.ino): aggiornate le chiamate a `ButtonController` (`g_button.Begin()` void, `g_button.Update(now_ms)`, `g_button.ConsumePressedEdge()`, `g_button.ConsumeReleasedEdge()`) per allinearsi all'API reale di `button_controller.h`.
- Il firmware stabile della FASE 10.8 (`jarvis_duplex_rtos_hw_test/`) non è stato modificato.

## 3. Risultato compilazione reale (`arduino-cli`)

- **Target**: `esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M`
- **Sketch**: `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client`
- **Esito**: **COMPILATO CON SUCCESSO (`exit status 0`)**
- **Occupazione Flash**: **`1.153.001` byte (`87%`)** su partizione programma predefinita da `1.310.720` byte.
- **Occupazione RAM (variabili globali)**: **`54.980` byte (`16%`)** su `327.680` byte (`272.700` byte liberi).
- **PSRAM e buffer**:
  - `g_rx_buffer`: `160.000` byte (`5 s` @ `16 kHz` PCM16 mono) in PSRAM.
  - `g_tx_buffer`: `640.000` byte (`20 s` @ `16 kHz` PCM16 mono) in PSRAM.
  - `NetworkBridgeClient::tts_buf_`: `640.000` byte in PSRAM (totale buffer audio PSRAM ~`1,44 MB` su `8 MB` OPI disponibili).
- **Driver I²S e FreeRTOS**: `AudioCapture` (`I2S_NUM_0`, Core 0, prio 3), `AudioPlayback` (`I2S_NUM_1`, Core 0, prio 3), `jarvis_net` (Core 1, prio 1), `EyeController` + `ButtonController` in `loop()` (Core 1, non bloccante).

## 4. Test di regressione Python (`05-Voice-AI/.venv/Scripts/python.exe`)

- `tests/test_esp32_ws_protocol.py` + `tests/test_voice_bridge.py` + `tests/test_voice_lab.py`: **26 test OK**.
- `04-Firmware/jarvis-desk-buddy-sim`: **44 test OK**.
- Test preesistenti `05-Voice-AI` (`test_control_center.py`, `test_conversation_engine.py`, `test_conversation_naturalizer.py`, `test_memory_engine.py`, `test_voice_ai.py`): **50 test OK**.

## 5. Problemi residui / note prima della FASE 11.3C

- **Margine partizione app predefinita (`87%`)**: con lo schema partizioni standard (`1,31 MB` per app) restano ~`157 KB` di margine Flash; per futuri ampliamenti su 16 MB conviene valutare `PartitionScheme=app3M_fat9M_16MB` (o `huge_app`).
- **Compilazione riuscita ≠ collaudo hardware**: nessun flash o test Wi-Fi reale su scheda ESP32-S3 è stato ancora eseguito.
- Restano da autorizzare per la **FASE 11.3C**: creazione di `wifi_secrets.h` locale, scelta TLS/WSS vs `ws://` LAN, regola firewall porta `8765`, avvio server su `0.0.0.0:8765` e flash hardware.
