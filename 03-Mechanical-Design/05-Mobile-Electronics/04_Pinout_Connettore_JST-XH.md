# Pinout e Regole di Collegamento Connettore JST-XH 6 Pin

> [!CAUTION]
> Il connettore **JST-XH a 6 pin** (`passo 2,50 mm`, portata `3 A AC/DC` con `AWG #22` **[DATASHEET]**) **NON è un connettore hot-plug**. Inserire o scollegare sempre a **base B2 spenta** e con **cavo USB-C scollegato**.

---

## 1. Tabella Pinout Definitiva (Modulo A ↔ Modulo B2)

| Pin | Segnale | Direzione | Tensione / Range | Funzione e Note Elettriche |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **`+5V_A`** | B2 → A | **`4,90 – 5,10 V`** `[REQUISITO]` (`4,92–5,09 V` `[CALCOLO]`) | Uscita da `Buck 5,09 V` + `Ideal Diode LM66100` (`1,5 A` max) + `PTC low-R 2,0 A`. Cablaggio corto `≤ 10 cm` verso `VCC_5V` (`J1-21`) ESP32-S3 |
| **2** | **`GND`** | Comune | `0 V` | Massa comune stella su B2 |
| **3** | **`UART_TX_A`** | A → B2 | `3,3 V` (LVCMOS) | `ESP32-S3 GPIO 17` → `ESP32-C3 GPIO 20 (RX)` (`220–330 Ω` serie) |
| **4** | **`UART_RX_A`** | B2 → A | `3,3 V` (LVCMOS) | `ESP32-C3 GPIO 21 (TX)` → `ESP32-S3 GPIO 18` (`220–330 Ω` serie) |
| **5** | **`I2C_SDA`** | Bidir. | `3,3 V` (pull-up `4,7 kΩ`) | `ESP32-S3 GPIO 8` (riservato / espansioni Modulo A; il bus I²C di B2 usa `ESP32-C3 GPIO 4/5` separati) |
| **6** | **`I2C_SCL`** | A → B2 | `3,3 V` (pull-up `4,7 kΩ`) | `ESP32-S3 GPIO 9` (riservato / espansioni Modulo A) |

---

## 2. Regole di sicurezza su alimentazione e USB-C `[REQUISITO]`
1. **Zero alimentazione simultanea:** È vietato collegare il cavo `USB-C` all'ESP32-S3 mentre il `JST-XH` è inserito o la base B2 è accesa.
2. **Anti-backfeed:** `D1/D7` (`1N5819HW-7-F`) su `ESP32-S3-DevKitC-1` + `LM66100` su B2 **`[DATASHEET]`**.
3. **Ricarica separata:** La ricarica `8,4 V CC/CV` avviene esclusivamente tramite connettore dedicato su B2.
