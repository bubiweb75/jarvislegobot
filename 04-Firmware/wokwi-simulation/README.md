# JARVIS LEGO BOT — Simulazione Hardware Wokwi (FASE 10.2-SIM)

Questa directory contiene la configurazione **Wokwi** per simulare l'hardware base di **JARVIS LEGO BOT** prima del montaggio fisico:

- **MCU**: `board-esp32-s3-devkitc-1`
- **Display**: `board-ssd1306` (`128×64`, I2C `0x3C`, `SDA=GPIO41`, `SCL=GPIO42`)
- **Pulsante**: `wokwi-pushbutton` (`GPIO47` → `GND`, `INPUT_PULLUP` attivo `LOW`, anche tasto `Spazio`)
- **Monitor Seriale**: `115200 baud` su `UART0` (`TX`/`RX` collegati a `$serialMonitor`)

> **Zero duplicazione di codice**: [platformio.ini](platformio.ini) compila direttamente i sorgenti di `../jarvis-desk-buddy/src` e gli header di `../jarvis-desk-buddy/include` con `-DOLED_DRIVER_SSD1306=1 -DARDUINO_USB_CDC_ON_BOOT=0 -DWOKWI_SIM=1`.

---

## Differenze tra simulazione Wokwi e hardware reale

| Elemento | Simulazione Wokwi | Hardware reale ESP32-S3 |
|---|---|---|
| Controller OLED | `board-ssd1306` (`0 px` offset, `-DOLED_DRIVER_SSD1306=1`) | Modulo 1,3" `1.30'' IIC V2.2` dichiarato `SH1106` (`+2 px` offset, `-DOLED_DRIVER_SH1106=1`) |
| Serial Monitor | `UART0` (`ARDUINO_USB_CDC_ON_BOOT=0`) | `esp32s3_sh1106` usa USB-CDC (`ARDUINO_USB_CDC_ON_BOOT=1`) |
| Sicurezza elettrica | **Non simulata** | Verificare LDO, `3V3`, pull-up I2C e polarità prima di alimentare il display reale |

---

## Procedura guidata (Windows 11 + VS Code)

### 1. Aprire la simulazione in Wokwi
1. Apri **Visual Studio Code** su Windows 11.
2. Verifica di avere installate le estensioni **PlatformIO IDE** e **Wokwi Simulator** (`wokwi.wokwi-vscode`).
   - Al primo utilizzo, attiva la licenza gratuita Wokwi (rinnovabile ogni 30 giorni dal comando `Wokwi: Request a New License`).
3. Apri la cartella `04-Firmware\wokwi-simulation` come workspace in VS Code (`File → Open Folder...`).

### 2. Compilare e avviare la simulazione
1. Esegui la build PlatformIO dell'environment `esp32s3_wokwi`:
   - Da UI PlatformIO: **Build** (`esp32s3_wokwi`), oppure
   - Da terminale:
     ```powershell
     python -m platformio run -d "04-Firmware\wokwi-simulation" -e esp32s3_wokwi
     ```
2. Apri il file `diagram.json` in VS Code (oppure premi `F1` → **Wokwi: Start Simulator**).
3. Wokwi legge automaticamente `wokwi.toml` e carica `.pio/build/esp32s3_wokwi/firmware.bin` e `.elf`.

### 3. Visualizzare gli occhi animati
All'avvio vedrai:
1. Breve schermata iniziale `JARVIS / ESP32-S3 WOKWI SIM` (~0,9 s).
2. Occhi animati **Eyes 3.0 (Organic Visor Companion)** con battito delle palpebre, sguardo naturale e ciclo automatico delle espressioni ogni 5 secondi.

### 4. Premere il pulsante virtuale (`GPIO47`)
- **Clic breve** sul pulsante blu `GPIO47` (oppure premi **`Spazio`**): interrompe il ciclo automatico e passa subito all'espressione successiva (`EVENT:STATE=...` sul Serial Monitor).
- **Pressione lunga (≥ 1,5 s)**: attiva/disattiva il ciclo automatico (`EVENT:AUTO_DEMO=ON|OFF`).

### 5. Leggere il monitor seriale e comandare le espressioni
Il Serial Monitor di Wokwi si apre automaticamente a `115200 baud` (`newline: lf`). Puoi inviare:

- **Espressioni**:
  `IDLE`, `HAPPY`, `CURIOUS`, `SLEEPY`, `LISTENING`, `THINKING`, `SPEAKING`, `SURPRISED`, `SHY`, `LOVE`, `WINK`, `CONFUSED`, `MISCHIEVOUS`, `SLEEPING`, `ERROR` (mappato a `CONFUSED`), oppure con prefisso `STATE:HAPPY`, `CMD:THINKING`.
- **Controllo occhi e profili**:
  - `BLINK`
  - `LOOK:dx,dy` (`dx: -11..11`, `dy: -6..6`, es. `LOOK:6,-2`)
  - `PROFILE:CALM` | `PROFILE:LIVELY` | `PROFILE:PLAYFUL`
  - `AUTO:ON` | `AUTO:OFF`
- **Diagnostica**:
  - `PING` → `PONG`
  - `STATUS`
  - `DIAG` (`OLED_ADDR=0x3C`, `RENDER_US`, `PRESENT_US`, `FPS`, `DROPPED`, `PROFILE`)
  - `HELP`

### 6. Trasferire il firmware sulla ESP32-S3 reale
Quando il display reale è verificato elettricamente e cablato su `GPIO41` (SDA), `GPIO42` (SCL), `GPIO47` (pulsante), `3V3` e `GND`:
1. Usa il progetto principale **`04-Firmware\jarvis-desk-buddy`**, **non** `wokwi-simulation`.
2. Compila e carica l'environment per display `SH1106`:
   ```powershell
   python -m platformio run -d "04-Firmware\jarvis-desk-buddy" -e esp32s3_sh1106 -t upload --upload-port COM4
   ```
   *(Se il modulo fisico risultasse `SSD1306` con shift di 2 pixel, usa `-e esp32s3_ssd1306`.)*

### 7. Cosa NON può essere verificato in Wokwi
- Compatibilità elettrica reale (`3.3 V` vs `5 V`, LDO sul PCB `1.30'' IIC V2.2`, pull-up I2C fisiche).
- Offset colonne reale del controller `SH1106` (`132×64` RAM vs `128×64` simulato).
- Consumi reali, stabilità alimentazione USB, PSRAM fisica e tempi I2C su cavi reali.
