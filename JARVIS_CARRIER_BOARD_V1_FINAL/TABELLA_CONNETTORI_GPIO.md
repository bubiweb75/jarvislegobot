# Tabella Connettori e Mappatura GPIO — JARVIS Carrier Board V1

- **Scheda target:** Espressif **ESP32-S3-DevKitC-1 v1.1** (`WROOM-1-N16R8`, 16 MB Flash QIO + 8 MB Octal PSRAM)
- **Pinout ufficiale verificato:** Documentazione Espressif `ESP32-S3-DevKitC-1 v1.1` (Header `J1` e `J3` da 22 pin, passo `2,54 mm`, interasse `22,86 mm`).
- **Orientamento fisico connettori `JST-XH` / `JST-PH` (`J4..J14`):** Tutti i connettori periferici sono montati verticalmente sul lato superiore (`F.Cu`) con rotazione `270°` (`-90°`):
  - **Vista frontale (lato componenti `F.Cu`):** **Pin 1** (piazzola rettangolare/quadrata) è sempre in **alto**, i pin `2..N` scendono verso il **basso (`+Y`)**, e la fessura di polarizzazione (*keying slot* della sede JST-XH) è rivolta verso **destra (`+X`)**.
  - **Vista posteriore (lato saldature `B.Cu`):** specchiata orizzontalmente (Pin 1 in alto, *keying slot* verso sinistra).
  - Per **`J4` (OLED Binghe SH1106)**: `Pin 1 = GND`, `Pin 2 = +3V3 (VCC)`, `Pin 3 = SCL (GPIO42)`, `Pin 4 = SDA (GPIO41)`.

---

## 1. Connettori Moduli Periferici (Accessibili e Sostituibili)

| Rif. | Modulo / Funzione | Footprint KiCad | Pin 1 | Pin 2 | Pin 3 | Pin 4 | Pin 5 | Pin 6 | Pin 7 | Pin 8 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`J1`** | ESP32-S3 Header SX | `PinSocket_1x22_P2.54mm_Vertical` | `+3V3` | `+3V3` | `NC` (`RST/EN`) | `MIC_WS` (`GPIO4`) | `MIC_SCK` (`GPIO5`) | `MIC_SD` (`GPIO6`) | `AMP_DIN` (`GPIO7`) | `AMP_BCLK` (`GPIO15`) *(continua sotto)* |
| **`J3`** | ESP32-S3 Header DX | `PinSocket_1x22_P2.54mm_Vertical` | `GND` | `NC` (`TX0/43`) | `NC` (`RX0/44`) | `TOUCH_OUT` (`GPIO1`) | `NC` (`GPIO2`) | `I2C_SCL` (`GPIO42`) | `I2C_SDA` (`GPIO41`) | `NC` (`GPIO40`) *(continua sotto)* |
| **`J4`** | **OLED SH1106** (36×34 mm) | `JST_XH_B4B-XH-A_1x04_P2.50mm` | **`GND`** | **`+3V3` (`VCC`)** | `I2C_SCL` (`GPIO42`) | `I2C_SDA` (`GPIO41`) | — | — | — | — |
| **`J5`** | **INMP441** Mic I²S (Ø 13 mm) | `JST_XH_B6B-XH-A_1x06_P2.50mm` | `+3V3` | `GND` | `GND` (`L/R=Left`) | `MIC_WS` (`GPIO4`) | `MIC_SCK` (`GPIO5`) | `MIC_SD` (`GPIO6`) | — | — |
| **`J6`** | **MAX98357A** Amp I²S (18×20 mm) | `JST_XH_B7B-XH-A_1x07_P2.50mm` | `+5V` (`VIN`) | `GND` | `+3V3` (`SD`) | `NC` (`GAIN`) | `AMP_DIN` (`GPIO7`) | `AMP_BCLK` (`GPIO15`) | `AMP_LRC` (`GPIO16`) | — |
| **`J14`** | **Uscita BTL da MAX98357A** | `JST_XH_B2B-XH-A_1x02_P2.50mm` | `SPK_PLUS` | `SPK_MINUS` | — | — | — | — | — | — |
| **`J7`** | **Speaker 4 Ω / 3 W** (2 fili) | `JST_PH_B2B-PH-K_1x02_P2.00mm` | `SPK_PLUS` | `SPK_MINUS` | — | — | — | — | — | — |
| **`J8`** | **Pulsante PTT** (NO) | `JST_XH_B2B-XH-A_1x02_P2.50mm` | `BUTTON` (`GPIO47`) | `GND` | — | — | — | — | — | — |
| **`J9`** | **Touch TTP223B** (24×24 mm) | `JST_XH_B3B-XH-A_1x03_P2.50mm` | `+3V3` | `GND` | `TOUCH_OUT` (`GPIO1`) | — | — | — | — | — |
| **`J10`** | **VL53L0X ToF** (25×12 mm) | `JST_XH_B6B-XH-A_1x06_P2.50mm` | `+3V3` | `GND` | `I2C_SDA` (`GPIO41`) | `I2C_SCL` (`GPIO42`) | `TOF_XSHUT_PU` (`+3V3` via 10k) | `NC` (`GPIO1_TOF`) | — | — |
| **`J11`** | **BH1750 Lux** (32,6×15,1 mm) | `JST_XH_B5B-XH-A_1x05_P2.50mm` | `+3V3` | `GND` | `I2C_SCL` (`GPIO42`) | `I2C_SDA` (`GPIO41`) | `GND` (`ADDR=0x23`) | — | — | — |
| **`J12`** | **MPU6050 GY-521** (20×15 mm) | `JST_XH_B8B-XH-A_1x08_P2.50mm` | `+3V3` | `GND` | `I2C_SCL` (`GPIO42`) | `I2C_SDA` (`GPIO41`) | `NC` (`XDA`) | `NC` (`XCL`) | `GND` (`AD0=0x68`) | `IMU_INT` (`GPIO10`) |
| **`J13`** | **Base Mobile B2** (Predisposizione) | `JST_XH_B6B-XH-A_1x06_P2.50mm` | `B2_5V_ISOLATED` *(isolato via `JP1`)* | `GND` | `B2_UART_TX` (`GPIO17` via 220 Ω) | `B2_UART_RX` (`GPIO18` via 220 Ω) | `B2_I2C_SDA` (`GPIO8`) | `B2_I2C_SCL` (`GPIO9`) | — | — |

---

## 2. Mappatura Completa dei 44 Contatti DevKitC-1 v1.1 (`J1` e `J3`)

### Header `J1` (Sinistra)
| Pin | Nome Espressif | Rete su PCB | Stato / Nota |
| :---: | :--- | :--- | :--- |
| 1 | `3V3` | `+3V3` | Alimentazione sensori e logica 3,3 V |
| 2 | `3V3` | `+3V3` | In parallelo a `J1-1` |
| 3 | `RST` (`EN`) | `NC` | **Mai collegare a GND** |
| 4 | `GPIO4` | `/MIC_WS` | INMP441 Word Select (`I2S0`) |
| 5 | `GPIO5` | `/MIC_SCK` | INMP441 Bit Clock (`I2S0`) |
| 6 | `GPIO6` | `/MIC_SD` | INMP441 Data (`I2S0`) + `R3` 100 kΩ pull-down |
| 7 | `GPIO7` | `/AMP_DIN` | MAX98357A Data (`I2S1`) |
| 8 | `GPIO15` | `/AMP_BCLK` | MAX98357A Bit Clock (`I2S1`) |
| 9 | `GPIO16` | `/AMP_LRC` | MAX98357A LR Clock (`I2S1`) |
| 10 | `GPIO17` | `/B2_TX_RAW` | Verso `J13-3` tramite `R1` 220 Ω |
| 11 | `GPIO18` | `/B2_RX_RAW` | Da `J13-4` tramite `R2` 220 Ω |
| 12 | `GPIO8` | `/B2_I2C_SDA` | Predisposizione `J13-5` |
| 13 | `GPIO3` | `NC` | Strapping pin |
| 14 | `GPIO46` | `NC` | Strapping pin |
| 15 | `GPIO9` | `/B2_I2C_SCL` | Predisposizione `J13-6` (**non usato per XSHUT**) |
| 16 | `GPIO10` | `/IMU_INT` | Interrupt opzionale MPU6050 (`J12-8`) |
| 17 | `GPIO11` | `NC` | Libero |
| 18 | `GPIO12` | `NC` | Libero |
| 19 | `GPIO13` | `NC` | Libero |
| 20 | `GPIO14` | `NC` | Libero |
| 21 | `5V` | `+5V` | Rail 5 V da USB verso `MAX98357A` (`C1` 470 µF + `C2` 100 nF) |
| 22 | `G` (`GND`) | `GND` | Piano di massa comune |

### Header `J3` (Destra)
| Pin | Nome Espressif | Rete su PCB | Stato / Nota |
| :---: | :--- | :--- | :--- |
| 1 | `G` (`GND`) | `GND` | Piano di massa comune |
| 2 | `TX` (`GPIO43`) | `NC` | Riservato UART0 |
| 3 | `RX` (`GPIO44`) | `NC` | Riservato UART0 |
| 4 | `GPIO1` | `/TOUCH_OUT` | Touch TTP223B (`J9-3`) |
| 5 | `GPIO2` | `NC` | Libero |
| 6 | `GPIO42` | `/I2C_SCL` | Bus I²C0 condiviso (`OLED`, `VL53L0X`, `BH1750`, `MPU6050`) |
| 7 | `GPIO41` | `/I2C_SDA` | Bus I²C0 condiviso (`OLED`, `VL53L0X`, `BH1750`, `MPU6050`) |
| 8 | `GPIO40` | `NC` | Libero |
| 9 | `GPIO39` | `NC` | Libero |
| 10 | `GPIO38` | `NC` | Riservato RGB LED v1.1 |
| 11 | `GPIO37` | `NC` | **VIETATO (Octal PSRAM)** |
| 12 | `GPIO36` | `NC` | **VIETATO (Octal PSRAM)** |
| 13 | `GPIO35` | `NC` | **VIETATO (Octal PSRAM)** |
| 14 | `GPIO0` | `NC` | **Riservato BOOT Strapping** |
| 15 | `GPIO45` | `NC` | **VIETATO (`VDD_SPI` Strapping)** |
| 16 | `GPIO48` | `NC` | Riservato RGB LED v1.0 |
| 17 | `GPIO47` | `/BUTTON` | Pulsante fisico PTT (`J8-1`) |
| 18 | `GPIO21` | `NC` | Libero |
| 19 | `GPIO20` (`USB_D+`) | `NC` | Riservato USB nativa |
| 20 | `GPIO19` (`USB_D-`) | `NC` | Riservato USB nativa |
| 21 | `G` (`GND`) | `GND` | Piano di massa comune |
| 22 | `G` (`GND`) | `GND` | Piano di massa comune |
