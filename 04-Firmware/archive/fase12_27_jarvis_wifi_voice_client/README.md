# JARVIS LEGO BOT — FASE 11.3A (`jarvis_wifi_voice_client`)

Variante isolata per il collegamento Wi-Fi WebSocket tra ESP32-S3-DevKitC-1 N16R8 e `jarvis-voice-bridge` (`/ws/v1/esp32`).

- **Non modifica** il firmware stabile FASE 10.8 (`jarvis_duplex_rtos_hw_test/`).
- **Dipendenza WebSocket scelta**: `Links2004/arduinoWebSockets` (`WebSocketsClient`, licenza LGPL-2.1, supporto `beginSslWithCA` / `begin`, compatibile ESP32 Arduino core).
- **Credenziali**: copiare `wifi_secrets.example.h` in `wifi_secrets.h` (non versionato) prima della compilazione in FASE 11.3B.
- **Stato**: sviluppo isolato FASE 11.3A — **nessun flash hardware autorizzato in questa fase**.
