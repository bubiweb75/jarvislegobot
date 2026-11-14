# JARVIS AI Desk Buddy — Simulatore Firmware su Windows 11

Simulatore desktop per Windows 11 che riproduce il display OLED monocromatico **128×64** di JARVIS con pixel nitidi (zoom intero `6×` nearest-neighbor, zero sfocatura), tutte le 7 espressioni animate, battito palpebre, movimenti dello sguardo e protocollo seriale compatibile con il futuro collegamento Raspberry Pi.

---

## 1. Avvio Rapido su Windows 11

Da PowerShell / Terminale nella cartella `04-Firmware/jarvis-desk-buddy-sim`:

```powershell
python simulator_gui.py
```

Oppure fai doppio clic su **`run_simulator.bat`**.

Per eseguire i test automatici:

```powershell
python -m unittest test_simulator.py -v
```

---

## 2. Architettura Condivisa & Differenze Documentate (Requisiti 7 e 8)

- **Architettura indipendente dal display fisico:**
  - Nel firmware ESP32-S3 (`04-Firmware/jarvis-desk-buddy/`), `EyeEngine` disegna esclusivamente su **`MonochromeFramebuffer`** (`128×64` pixel = `1024` byte in formato XBM), e solo `display_driver.cpp` invia il buffer a `U8g2` (`SH1106` o `SSD1306/SSD1106`).
- **Rapporto tra Simulatore PC e Firmware ESP32-S3:**
  - Poiché su questo PC Windows non è installato un compilatore C++ nativo desktop (`g++`/`MSVC`/`clang++`), il simulatore (`monochrome_fb.py`, `eye_engine.py`, `simulator_gui.py`) è un **porting 1:1 in Python + `tkinter`** della logica di `MonochromeFramebuffer`, `EyeEngine` e `StateMachine` C++.
  - **Non viene dichiarata equivalenza binaria:** le tempistiche di I²C hardware, l'offset colonna reale del controller **SH1106 vs SSD1106/SSD1306**, il debounce elettrico del pulsante su `GPIO 47` e la memoria/PSRAM dell'ESP32-S3 N16R8 **richiedono comunque il collaudo sull'hardware fisico**.

---

## 3. Cosa è Testato su PC vs Cosa Richiede l'ESP32-S3 Fisico

| Aspetto | Verificato su PC Windows 11 | Richiede ESP32-S3 + OLED Fisici |
| :--- | :---: | :---: |
| Risoluzione virtuale `128×64`, proporzione e centratura occhi | ✅ Sì | Verifica resa visiva dietro la visiera LEGO `27925` |
| Espressioni `IDLE`, `HAPPY`, `CURIOUS`, `SLEEPY`, `LISTENING`, `THINKING`, `SPEAKING` | ✅ Sì | — |
| Battito palpebre, sguardi organici, interpolazione 50 FPS | ✅ Sì | Verifica fluidità reale su bus I²C `400 kHz` |
| Parser comandi seriali (`STATE:...`, `BLINK`, `LOOK:dx,dy`, `PING`, `STATUS`) | ✅ Sì (logica) | Verifica fisica su USB-CDC / UART verso Raspberry Pi |
| Compilazione firmware C++ (`esp32s3_sh1106` e `esp32s3_ssd1306`) | ✅ Sì (`pio run`) | Caricamento flash (`pio run -t upload`) |
| Riconoscimento controller `SH1106` vs `SSD1106` e indirizzo `0x3C`/`0x3D` | ❌ No | ✅ Sì |
| Pinout reale `GPIO 41/42` (I²C) e `GPIO 47` (pulsante NO) | ❌ No | ✅ Sì |
