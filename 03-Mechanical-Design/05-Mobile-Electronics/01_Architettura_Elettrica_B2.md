# Architettura Elettrica – Base Mobile B2 (JARVIS LEGO BOT)

> [!IMPORTANT]
> **Stato documento:** Verifica conclusiva `INA3221` e `ESP32-C3 SuperMini` completata a livello documentale. **Nessun acquisto, cablaggio o costruzione è autorizzato** fino alla chiusura delle prove su banco (**`[PROVA NON ESEGUITA]`**).

## 1. Vincoli progettuali invariati `[REQUISITO]`
- **Modulo A (Corpo):** `10 × 10 stud` (`8,0 × 8,0 × 14,4 cm`), **ESP32-S3-DevKitC-1 N16R8**.
- **Modulo B2 (Base mobile):** `16 × 15 stud` (`12,8 × 12,0 × 4,5 cm`), configurazione **2WD + 1 caster**, due motori indipendenti.
- **Controller secondario su B2:** **ESP32-C3 SuperMini** (`GPIO 20/21` UART; I²C spostato su **`GPIO 4/5`** non-strapping).
- **Comunicazione A ↔ B2:** UART `3,3 V` su `GPIO 17/18` dell'ESP32-S3 attraverso connettore **JST-XH a 6 pin** (non hot-plug).
- **Driver motori:** **Toshiba `TB6612FNG`** (con `VM = 6,0 V` regolata, misura corrente `INA3221` + clamp Schottky su `AO1/BO1` e taglio firmware rapido).

---

## 2. Diagramma a blocchi elettrico definitivo

```text
+-----------------------------------------------------------------------------------+
|                              MODULO B2 (Base Mobile)                              |
|                                                                                   |
|  [Caricatore 8,4V CC/CV] ---> (Connettore Ricarica Dedicato, isolato da JST-XH)   |
|                                      |                                            |
|                                      v                                            |
|  [Batteria 2S Piatta 6,0-8,4V con BMS/Bilanciamento]                              |
|         |                                                                         |
|         +---> [Interruttore Generale + Fusibile Principale 3-4A]                  |
|                     |                                                             |
|                     +---> [Partitore ADC V_BAT] ---> ESP32-C3 (GPIO 0 / ADC1)     |
|                     |                                                             |
|                     +---> [Buck 5,09V >= 3A]                                      |
|                     |        |                                                    |
|                     |        +---> [Ideal Diode LM66100 + PTC low-R 2,0A]         |
|                     |        |        |                                           |
|                     |        |        +---> JST-XH Pin 1 (+5V_A: 4,90-5,10V)      |
|                     |        |        +---> ESP32-C3 SuperMini (5V / LDO 3,3V)    |
|                     |                                                             |
|                     +---> [Buck Sincrono 6,0V >= 3A (es. TPS54302)]               |
|                              |                                                    |
|                              +---> [TB6612FNG (VM = 6,0V, VCC = 3,3V)]            |
|                                       |-- AO1 (+BAT54S clamp)->[0,1R + PTC]->N20 SX|
|                                       |-- BO1 (+BAT54S clamp)->[0,1R + PTC]->N20 DX|
|                                                     ^ (RC 10 Ohm + 1 uF)          |
|                                                     | (Sensore I2C 0x40)          |
|  [ESP32-C3 SuperMini] <--- I2C (GPIO 4/5) ---> [INA3221] + [VL53L0X (0x29)]       |
|         ^                   GPIO 8 (+10k PU) -> [VL53L0X XSHUT (3,3V)]            |
|         | UART 3,3V (GPIO 20/21) + GND          GPIO 9: solo BOOT                 |
+---------|-------------------------------------------------------------------------+
          |  Connettore JST-XH 6 pin (NO HOT-PLUG)
          v
+-----------------------------------------------------------------------------------+
|                          MODULO A (Corpo Principale)                              |
|  Pin 1: +5V_A (4,90-5,10V) -> VCC_5V ESP32-S3 (D1/D7 anti-backfeed su DevKitC)    |
|  Pin 2: GND                                                                       |
|  Pin 3/4: UART TX/RX (GPIO 17/18) <-> ESP32-C3 (GPIO 20/21)                       |
|  Pin 5/6: I2C SDA/SCL (GPIO 8/9) - riservati / sensori opzionali                  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Legenda classificazione parametri
- **`[DATASHEET]`**: dato ufficiale del costruttore.
- **`[CALCOLO]`**: grandezza ricavata analiticamente da dati ufficiali o formule fisiche.
- **`[STIMA]`**: assunzione ingegneristica basata su condizioni realistiche di esercizio.
- **`[REQUISITO]`**: vincolo progettuale fissato dal progetto.
- **`[PROVA NON ESEGUITA]`**: verifica sperimentale rimandata alla fase di collaudo su banco.
