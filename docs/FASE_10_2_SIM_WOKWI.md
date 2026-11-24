# FASE 10.2-SIM — Integrazione Wokwi e Simulazione Hardware ESP32-S3

## 1. Obiettivo e Architettura Adottata

La directory [04-Firmware/wokwi-simulation](04-Firmware/wokwi-simulation/README.md) integra la simulazione **Wokwi** per **JARVIS LEGO BOT** senza duplicare il firmware principale:

- `04-Firmware/wokwi-simulation/platformio.ini` imposta `src_dir = ../jarvis-desk-buddy/src` e `include_dir = ../jarvis-desk-buddy/include` per compilare direttamente i sorgenti condivisi (`EyeEngine` Eyes 3.0, `StateMachine`, `DisplayDriver`, `MonochromeFramebuffer`).
- Environment dedicato `esp32s3_wokwi`:
  - `-DOLED_DRIVER_SSD1306=1` (esclusivamente per Wokwi `board-ssd1306`, lasciando `esp32s3_sh1106` come default per il display reale).
  - `-DARDUINO_USB_CDC_ON_BOOT=0` (serial monitor su `UART0` `TX`/`RX` collegato a `$serialMonitor`).
  - `-DWOKWI_SIM=1` (abilita in `main.cpp` la breve schermata iniziale `"JARVIS / ESP32-S3 WOKWI SIM"` e in `state_machine.cpp` l'alias seriale `ERROR → CONFUSED`, senza alterare il comportamento del firmware reale).
- `04-Firmware/wokwi-simulation/wokwi.toml`: punta ai binari generati `.pio/build/esp32s3_wokwi/firmware.bin` e `.pio/build/esp32s3_wokwi/firmware.elf`.
- `04-Firmware/wokwi-simulation/diagram.json`:
  - `board-esp32-s3-devkitc-1` (`esp`)
  - `board-ssd1306` (`oled1`, I2C `0x3c`, `SDA=GPIO41`, `SCL=GPIO42`, `VCC=3V3`, `GND=GND.1`)
  - `wokwi-pushbutton` (`btn1`, `GPIO47` → `GND.2`, attivo `LOW` con `INPUT_PULLUP`, tasto `Space`)
  - `$serialMonitor` su `esp:TX` / `esp:RX`

---

## 2. Stato delle Verifiche (Distinzione Esplicita)

### Test Compilati e Verificati Localmente
- **Test A — Compilazione Wokwi (`esp32s3_wokwi`)**: `SUCCESS` (`93.80 s`, RAM `8.2%` / `26800 B`, Flash `13.1%` / `438348 B`). Generati `firmware.bin` (`445104 B`) e `firmware.elf` (`8159776 B`).
- **Ricompilazione firmware principale (`jarvis-desk-buddy`)**:
  - `esp32s3_sh1106`: `SUCCESS` (`16.18 s`, RAM `8.2%` / `27000 B`, Flash `12.8%` / `427652 B`) — identico alla baseline reale.
  - `esp32s3_ssd1306`: `SUCCESS` (`14.35 s`, RAM `8.2%` / `27000 B`, Flash `12.8%` / `427668 B`).

### Test Automatici Eseguiti (Isolamento)
- **Simulatore Python (`04-Firmware/jarvis-desk-buddy-sim`)**: `35` test superati (`OK` in `7.525 s`).
- **Voice AI & Control Center (`05-Voice-AI/tests`)**: `50` test superati (`OK` in `28.523 s`).
- Firmware diagnostico `04-Firmware/esp32s3-diag-test`: invariato.

### Test Interattivi Wokwi Ancora da Eseguire Manualmente
Poiché `wokwi-cli` e `code` (VS Code CLI) non sono installati nel `PATH` di sistema, i seguenti test devono essere eseguiti interattivamente dall'utente in **VS Code + Wokwi Simulator**:
- **Test B — Avvio**: avvio della `board-esp32-s3-devkitc-1` virtuale e verifica output a `115200 baud` sul Serial Monitor.
- **Test C — OLED**: verifica schermata iniziale `"JARVIS"`, rilevamento `0x3C`, rendering Eyes 3.0 e ciclo automatico delle espressioni.
- **Test D — Pulsante**: clic su `GPIO47` (o `Spazio`) per cambio espressione (`EVENT:STATE=...`) e pressione lunga (`≥ 1,5 s`) per toggle `EVENT:AUTO_DEMO=ON|OFF`.

---

## 3. Differenze Rispetto all'Hardware Reale

1. Wokwi simula `board-ssd1306` (`0 px` offset) anziché il modulo fisico `1.30'' IIC V2.2` dichiarato `SH1106` (`+2 px` offset).
2. `esp32s3_wokwi` usa `UART0` (`ARDUINO_USB_CDC_ON_BOOT=0`), mentre `jarvis-desk-buddy` usa USB-CDC (`ARDUINO_USB_CDC_ON_BOOT=1`).
3. Wokwi non verifica la sicurezza elettrica reale (regolatore LDO, tolleranza `3.3 V`, resistenze di pull-up I2C reali).
