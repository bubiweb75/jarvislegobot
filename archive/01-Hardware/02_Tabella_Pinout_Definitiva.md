# Elaborato B – Tabella Pinout Definitiva

**Progetto:** JARVIS LEGO BOT – FASE 2  
**Scheda di riferimento:** Espressif ESP32-S3-DevKitC-1 N16R8 (header 2×22 pin: `J1` sinistro, `J3` destro guardando la scheda con porte USB in basso e antenna in alto)  
**Riferimento firmware:** `78/xiaozhi-esp32` (`bread-compact-wifi`, con variante dedicata in FASE 4)

---

## 1. Mappatura Pinout Definitiva

| GPIO / Pin ESP32-S3 | Header DevKitC-1 | Direzione / Bus | Segnale | Componente Collegato | Pin Modulo | Note Tecniche |
|---|---|---|---|---|---|---|
| **GPIO 4** | `J1-4` | Output (I2S RX) | `I2S_MIC_WS` | Microfono INMP441 | `WS` | Word Select (LRCLK) a 16 kHz |
| **GPIO 5** | `J1-5` | Output (I2S RX) | `I2S_MIC_SCK` | Microfono INMP441 | `SCK` | Bit Clock I2S microfono |
| **GPIO 6** | `J1-6` | Input (I2S RX) | `I2S_MIC_SD` | Microfono INMP441 | `SD` | Dati audio digitali dal microfono |
| **GPIO 7** | `J1-7` | Output (I2S TX) | `I2S_SPK_DIN` | Amplificatore MAX98357A | `DIN` | Dati audio digitali verso amplificatore |
| **GPIO 15** | `J1-8` | Output (I2S TX) | `I2S_SPK_BCLK` | Amplificatore MAX98357A | `BCLK` | Bit Clock I2S amplificatore |
| **GPIO 16** | `J1-9` | Output (I2S TX) | `I2S_SPK_LRC` | Amplificatore MAX98357A | `LRC` | Left/Right Clock a 24 kHz |
| **GPIO 41** | `J3-7` | Bidir. (I2C0) | `I2C_OLED_SDA` | Display OLED 1,3" | `SDA` | Dati I2C (400 kHz) |
| **GPIO 42** | `J3-6` | Output (I2C0) | `I2C_OLED_SCL` | Display OLED 1,3" | `SCL` | Clock I2C (`0x3C` tipico, da verificare) |
| **GPIO 47** | `J3-17` | Input (Digital) | `BTN_ACTIVATE` | Pulsante meccanico NO | Pin A | Pull-up interno abilitato, attivo LOW verso `GND`. Nessun conflitto strapping. |
| **3V3** | `J1-1` o `J1-2` | Alimentazione | `+3.3V` | INMP441 (`VDD`), OLED (`VCC`), MAX98357A (`SD`) | `VDD`/`VCC`/`SD` | Max ~25–30 mA esterni; **non alimentare `VIN` MAX98357A da `3V3`** |
| **5V** | **`J1-21`** | Alimentazione | `+5V` | Stella 5 V (Modalità A) | `5V` | Ingresso 5 V in Modalità A. **Scollegare in Modalità B (USB PC)** |
| **GND** | **`J1-22`**, **`J3-1`**, **`J3-21`**, **`J3-22`** | Massa comune | `GND` | Tutti i moduli + `L/R` INMP441 + Pin B Pulsante | `GND` / `L/R` | Massa comune a stella |

> **Nota pin `J1-3` (`RST` / `EN`):** Sul header sinistro `J1`, il pin **`J1-3` è `RST` (`CHIP_PU` / Enable)** e **NON** è `GND`. Non collegarlo mai a massa fissa, altrimenti l'ESP32-S3 resta in reset permanente.

---

## 2. Verifica Compatibilità `GPIO 47` con Pulsante Meccanico e Firmware

- **Hardware (`GPIO 47`):** GPIO digitale standard (`VDD3P3_CPU`), dotato di resistore di pull-up interno attivabile via software (~45 kΩ) e **non strapping pin**. Non interferisce con il boot né con la PSRAM Octal.
- **Firmware (`78/xiaozhi-esp32`):**
  - La classe `Button` (`main/boards/common/button.cc`) utilizza `iot_button` con `disable_pull = false` e `active_level = 0`: abilita automaticamente il pull-up interno e gestisce il **debouncing** per normali pulsanti meccanici normalmente aperti (NO).
  - In `bread-compact-wifi`, `TOUCH_BUTTON_GPIO` è già mappato su `GPIO_NUM_47` (`StartListening()` / `StopListening()`, oppure adattabile a `OnClick` in FASE 4).

---

## 3. Pin Disabilitati, Riservati o Non Utilizzati

| GPIO / Pin | Stato | Motivazione |
|---|---|---|
| **GPIO 39, GPIO 40** (`J3-9`, `J3-8`) | **DISABILITATI** | Non usati per i tasti volume: in FASE 4 impostati a `GPIO_NUM_NC` e lasciati fisicamente scollegati. |
| **RST / EN** (`J1-3`) | **RISERVATO (Reset)** | Pin `CHIP_PU` (Enable/Reset). Non collegare a `GND`. |
| **GPIO 0** (`J3-14`) | **Solo Onboard `BOOT`** | Strapping pin di avvio (Download Mode se LOW al reset). Resta esclusivamente al tastino `BOOT` sulla scheda. |
| **GPIO 35, 36, 37** (`J3-13`, `J3-12`, `J3-11`) | **VIETATI (PSRAM)** | Riservati internamente alla **Octal PSRAM (R8)**. L'uso provoca crash o corruzione memoria. |
| **GPIO 19, 20** (`J3-20`, `J3-19`) | **RISERVATI (USB)** | USB nativo D- / D+. |
| **GPIO 43, 44** (`J3-2`, `J3-3`) | **RISERVATI (UART0)** | Console seriale TX / RX (`U0TXD`/`U0RXD`). |
| **GPIO 3, 45, 46** (`J1-13`, `J3-15`, `J1-14`) | **VIETATI (Strapping)** | Pin di strapping hardware ESP32-S3. |
| **GPIO 38 / 48** (`J3-10` / `J3-16`) | **RISERVATI (LED RGB)** | LED NeoPixel onboard (`GPIO 48` su v1.0, `GPIO 38` su v1.1). Non collegare periferiche esterne. |
| **GPIO 1, 2, 8–14, 17, 18, 21** | **LIBERI (Espansioni)** | Disponibili per future espansioni (motori/driver, sensori nella versione mobile). |
