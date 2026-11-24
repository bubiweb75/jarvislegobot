# FASE 13.8 — Promozione Ufficiale Versione Stabile

## 1. Stato e Percorsi
- **Nuova versione stabile (sorgenti)**: [04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/jarvis_wifi_voice_client.ino)
- **Archivio sorgenti FASE 12.27**: `04-Firmware/archive/fase12_27_jarvis_wifi_voice_client/`
- **Binario applicativo collaudato (`app0`)**: `05-Voice-AI/backups/fase13_8_stable/fase13_8_app0.bin` (`1.299.328` B, SHA-256 `44A548EDB0A83A318CFE684F6455EFAE71AD3E30B636B2C6FD17ABF7B12BBE32`)
- **Backup completo 16 MB FASE 13.8 (ESP32-S3 COM6)**: `05-Voice-AI/backups/fase13_8_stable/esp32_fase13_8_stable_full_16mb.bin` (`16.777.216` B, SHA-256 `2C11FAA2C39175DA3A9BA8B190B23E1FF319BB7262556B8EC6D5293856AD434E`)
- **Backup rollback FASE 12.27 (`app0`)**: `05-Voice-AI/backups/fase13_2_preflash/fase12_27_app0_rollback.bin` (`1.310.720` B, SHA-256 `94E0B14E676E535685F960658C71D7324550A25A88AEB409D10B87A912418E47`)
- **Backup completo 16 MB FASE 12.27**: `05-Voice-AI/backups/fase13_2_preflash/esp32_fase13_2_preflash_full_16mb.bin` (`16.777.216` B, SHA-256 `3206F1933AF561A72C35CC376C45EF162BC543D7351ABE32B58D5AF8FFF22307`)

## 2. Verifica Backup Completo FASE 13.8
- Letti tutti i `16.777.216` byte (`0x000000`–`0x1000000`) da `ESP32-S3 COM6` (`MAC <ESP32_MAC_ADDRESS>`) in `228.4 s`.

## 3. Sicurezza Repository GitHub
- `wifi_secrets.h`, `.env`, certificati `.local_certs/`, database `.db/.sqlite`, backup Flash (`05-Voice-AI/backups/`) e cartelle `build/`/`build_verify/` sono esclusi dal versionamento tramite `.gitignore`.
