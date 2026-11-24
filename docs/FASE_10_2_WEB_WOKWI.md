# FASE 10.2-WEB — Adattamento Wokwi Online (`https://wokwi.com/`)

## 1. Verifica Preliminare (Documentazione Ufficiale Wokwi)

- **ESP32-S3 online**: supportata (`board-esp32-s3-devkitc-1`, attributi `flashSize: "16"`, `psramType: "octal"`).
- **Caricamento firmware precompilato nel browser**: supportato tramite `F1` → **`Upload Firmware and Start Simulation...`**. Per ESP32-S3 PlatformIO/Arduino è necessaria un'**immagine combinata (`merge-bin`)** con `bootloader.bin` (`0x0000`), `partitions.bin` (`0x8000`), `boot_app0.bin` (`0xE000`) e `firmware.bin` (`0x10000`). Il binario caricato vale per la sessione corrente e non viene salvato nel link condivisibile.
- **Progetto sorgente salvabile e condivisibile online**: supportato tramite `sketch.ino`, `diagram.json`, `libraries.txt` (`U8g2`) e file multipli `.h`/`.cpp`.

---

## 2. File Prodotti in `04-Firmware/wokwi-web/`

- `diagram.json`: circuito web compatibile (`ESP32-S3`, `board-ssd1306` `0x3C`, `SDA=GPIO41`, `SCL=GPIO42`, `GPIO47` → `GND`, `$serialMonitor`).
- `build_merged_firmware.py` → genera `jarvis-esp32s3-wokwi-merged.bin` (`510640 B`) dai binari di `04-Firmware/wokwi-simulation/.pio/build/esp32s3_wokwi/`.
- `prepare_web_bundle.py` → genera `web-project/` e `jarvis-wokwi-web.zip` (`22111 B`) dai sorgenti originali di `04-Firmware/jarvis-desk-buddy/`, aggiungendo i `#define OLED_DRIVER_SSD1306 1` e `#define WOKWI_SIM 1` solo nella copia web esportata.
- `README.md`: guida passo-passo per Windows 11 + Chrome (Opzione A immediata e Opzione B salvabile con link condivisibile).

---

## 3. Stato Verifiche (Distinzione Esplicita)

- **Compatibilità documentata**: verificata su documentazione ufficiale Wokwi (`docs.wokwi.com`).
- **Compilazione e generazione artefatti**:
  - `jarvis-esp32s3-wokwi-merged.bin` generato con `esptool.exe` v5.4.0 (`510640 B`, exit code `0`).
  - `web-project/` e `jarvis-wokwi-web.zip` generati (`22111 B`, exit code `0`).
- **Test automatici Python e firmware reale**: invariati (`35/35` simulatore, `50/50` Voice AI, `esp32s3_sh1106` invariato — nessuna modifica effettuata ai firmware reale, diagnostico o Voice AI).
- **Simulazione nel browser (`wokwi.com`)**: **non ancora eseguita** (richiede interazione manuale in Chrome e accesso account Wokwi per eventuale salvataggio/condivisione).
