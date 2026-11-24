# JARVIS LEGO BOT — Wokwi Web (Browser Online, FASE 10.2-WEB)

Questa directory permette di eseguire **JARVIS LEGO BOT** direttamente nel browser su **https://wokwi.com/** (Chrome/Edge), senza installare VS Code né l'estensione Wokwi.

---

## Cosa contiene questa cartella

- **`diagram.json`**: circuito virtuale (`board-esp32-s3-devkitc-1`, `board-ssd1306` `128×64` a `0x3C`, `SDA=GPIO41`, `SCL=GPIO42`, pulsante `GPIO47` → `GND`, `$serialMonitor`).
- **`jarvis-esp32s3-wokwi-merged.bin`**: immagine firmware completa pronta per il browser (contiene `bootloader.bin` @ `0x0000`, `partitions.bin` @ `0x8000`, `boot_app0.bin` @ `0xE000`, `firmware.bin` @ `0x10000`).
- **`build_merged_firmware.py`**: rigenera `jarvis-esp32s3-wokwi-merged.bin` dai binari PlatformIO di `../wokwi-simulation/.pio/build/esp32s3_wokwi/`.
- **`web-project/`** e **`jarvis-wokwi-web.zip`**: progetto sorgente completo (Eyes 3.0 con 14 espressioni, `libraries.txt` con `U8g2`, `diagram.json`) per salvare e condividere JARVIS nel proprio account Wokwi.
- **`prepare_web_bundle.py`**: rigenera `web-project/` e `jarvis-wokwi-web.zip` dai sorgenti originali di `../jarvis-desk-buddy/`.

---

## Opzione A (Più veloce — Avvio immediato con firmware precompilato)

Ideale per provare subito JARVIS in 30 secondi senza copiare i file C++:

1. Apri Chrome e vai su:
   **https://wokwi.com/projects/new/esp32-s3**
2. Clicca sulla scheda **`diagram.json`**, seleziona tutto e incolla il contenuto di `04-Firmware/wokwi-web/diagram.json`.
3. Clicca nell'editor di codice (scheda `sketch.ino`), premi **`F1`** e scegli:
   **`Upload Firmware and Start Simulation...`**
4. Seleziona il file:
   `04-Firmware/wokwi-web/jarvis-esp32s3-wokwi-merged.bin`
5. La simulazione parte immediatamente: vedrai la schermata `JARVIS`, gli occhi **Eyes 3.0**, il blink automatico, il movimento dello sguardo e il cambio espressione.

> **Nota**: con *Upload Firmware and Start Simulation* il file `.bin` viene eseguito nella sessione corrente del browser, ma non viene salvato dentro un link condivisibile. Per avere un link permanente salvato nel tuo account Wokwi, usa l'**Opzione B**.

---

## Opzione B (Consigliata per salvare e ottenere un link condivisibile permanente)

1. Accedi al tuo account gratuito su **https://wokwi.com/** e apri **https://wokwi.com/projects/new/esp32-s3**.
2. Carica/incolla i file presenti in `04-Firmware/wokwi-web/web-project/`:
   - Sostituisci `diagram.json` e `sketch.ino`.
   - Nella scheda **Library Manager** (`+`), aggiungi **`U8g2`** (oppure crea la scheda `libraries.txt` con contenuto `U8g2`).
   - Con il pulsante **`+`** accanto ai tab dei file, aggiungi i file `.h` e `.cpp` da `web-project/`:
     `pinout_config.h`, `monochrome_fb.h`, `monochrome_fb.cpp`, `display_driver.h`, `display_driver.cpp`, `eye_engine.h`, `eye_engine.cpp`, `sensor_stub.h`, `state_machine.h`, `state_machine.cpp`.
3. Premi il pulsante verde **Start Simulation** (Play).
4. Clicca **Save** (in alto) per salvare il progetto nel tuo account Wokwi e poi **Share** per ottenere il link condivisibile diretto.

---

## Come controllare JARVIS nel browser

- **Pulsante blu `GPIO47`** (oppure tasto **`Spazio`**):
  - **Clic breve**: passa all'espressione successiva e stampa `EVENT:STATE=...` nel Serial Monitor.
  - **Pressione lunga (≥ 1,5 s)**: attiva/disattiva il ciclo automatico (`EVENT:AUTO_DEMO=ON|OFF`).
- **Comandi Serial Monitor (`115200 baud`)**:
  - Espressioni: `IDLE`, `HAPPY`, `CURIOUS`, `SLEEPY`, `LISTENING`, `THINKING`, `SPEAKING`, `SURPRISED`, `SHY`, `LOVE`, `WINK`, `CONFUSED`, `MISCHIEVOUS`, `SLEEPING`, `ERROR` (o `STATE:<nome>`).
  - Controlli: `BLINK`, `LOOK:6,-2`, `PROFILE:CALM|LIVELY|PLAYFUL`, `AUTO:ON|OFF`, `DIAG`, `STATUS`, `PING`, `HELP`.

---

## Limitazioni note della versione web

- **Display simulato `SSD1306` vs reale `SH1106`**: Wokwi simula `board-ssd1306` (`0 px` offset), mentre il modulo reale da 1,3" è `SH1106` (`+2 px` offset).
- **Piano gratuito Wokwi**: i progetti salvati online nel piano gratuito sono **pubblici**; la compilazione online dei sorgenti (Opzione B) usa le code dei server Wokwi.
- **Sicurezza elettrica**: Wokwi non verifica tensioni, regolatori LDO né pull-up I2C reali. Per la scheda ESP32-S3 reale usare sempre `04-Firmware/jarvis-desk-buddy` (`esp32s3_sh1106`).
