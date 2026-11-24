# JARVIS LEGO BOT — FASE 10.3: Test Hardware Microfono INMP441

Sketch Arduino isolato per verificare la ricezione audio I²S dal microfono **INMP441** su **ESP32-S3-DevKitC-1 N16R8** (senza modificare Eyes 3.0, Wokwi, TouchManager o GPIO1).

---

## 1. Collegamenti Hardware Verificati

| Pin `INMP441` | ESP32-S3 | Note |
|---|---|---|
| `VDD` | `3V3` | Solo 3.3V (mai 5V) |
| `GND` | `GND` | Massa comune |
| `L/R` | `GND` | Canale sinistro (`I2S_STD_SLOT_LEFT`) |
| `WS` | `GPIO4` | Word Select (LRCLK) |
| `SCK` | `GPIO5` | Bit Clock (BCLK) |
| `SD` | `GPIO6` | Data Out → ESP32-S3 DIN |

---

## 2. Configurazione Arduino IDE 2

1. Apri `04-Firmware\arduino-hw-test\inmp441_hw_test\inmp441_hw_test.ino`.
2. **Core richiesto**: **Espressif ESP32 (Arduino-ESP32 v3.x)** — usa `<ESP_I2S.h>` (`I2SClass`) già incluso nel core, nessuna libreria esterna da installare.
3. In **Strumenti (Tools)**:
   - **Board**: `ESP32S3 Dev Module`
   - **Flash Size**: `16MB (128Mb)`
   - **Flash Mode**: `QIO 80MHz`
   - **PSRAM**: `OPI PSRAM`
   - **USB CDC On Boot**: `Disabled` se usi la porta **UART (CH343)**, oppure `Enabled` se usi la porta **USB** nativa
   - **Port**: la porta COM dell'ESP32-S3
4. Premi **Verifica** (`Ctrl+R`), poi **Carica** (`Ctrl+U`).
5. Apri il **Monitor Seriale** a **`115200 baud`**.

---

## 3. Interpretazione dei Valori (24-bit AC, scala `0 .. 8.388.607`)

Ogni `300 ms` lo sketch stampa una riga:
`RMS=<val> | PEAK=<val> | SAMPLES=<~4800> | I2S_ERR=0 (last=0)`

| Condizione acustica | `RMS` indicativo | `PEAK` indicativo | Cosa verifica |
|---|---|---|---|
| **Silenzio ambiente** | Basso e stabile (es. `< 1500`–`5000` in base al rumore stanza) | Basso (es. `< 15000`) | Assenza di saturazione o pin flottanti |
| **Parlato normale (~30–50 cm)** | Chiaramente superiore al silenzio (es. `10.000`–`150.000+`) | Picchi dinamici ben visibili (`50.000`–`600.000+`) | Modulazione vocale continua e `SAMPLES` ~`4800` ogni `300 ms` |
| **Battito delle mani (clap)** | Impulso rapido in aumento nella finestra | Picco molto alto e netto (`> 500.000`–`4.000.000+`) | Risposta ai transienti e assenza di clipping fisso a `0` o `8388607` |

**Segnali di anomalia da controllare:**
- `RMS=0` e `PEAK=0` fissi → controllare saldature su `SD (GPIO6)`, `SCK (GPIO5)`, `WS (GPIO4)` o `VDD/GND`.
- Valori molto alti/casuali costanti anche nel silenzio → verificare `L/R → GND` (non flottante) e `GND` comune.
- `I2S_ERR > 0` → errore driver I²S (controllare `last=<codice>`).
