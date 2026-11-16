# FASE 10.2 — Rapporto Collaudo Hardware Reale Eyes 3.0

## 1. Sintesi del Collaudo

Il primo collaudo su hardware reale del motore grafico **JARVIS Eyes 3.0** su **ESP32-S3-DevKitC-1 N16R8** con display **OLED SH1106 128×64 I²C** è stato completato con successo tramite **Arduino IDE 2**, utilizzando la versione isolata:

- `04-Firmware/arduino-hw-test/jarvis_eyes3_hw_test/`

Il firmware stabile in `04-Firmware/jarvis-desk-buddy/` non è stato modificato durante il collaudo.

---

## 2. Configurazione Hardware Verificata

| Componente | Specifica Verificata | Collegamento / Note |
|---|---|---|
| **MCU** | Espressif `ESP32-S3-DevKitC-1 N16R8` | Flash `16 MB` (QIO), PSRAM `8 MB` (OPI), riconosciuto da Windows via USB |
| **Display OLED** | Monocromatico `1,3"` `128×64`, controller **SH1106** | `U8G2_SH1106_128X64_NONAME_F_HW_I2C` (`+2 px` column offset) |
| **Bus I²C (`Wire`)** | `SDA = GPIO41`, `SCL = GPIO42`, `400 kHz` | Indirizzo I²C rilevato: **`0x3C`** |
| **Pulsante fisico** | `GPIO47` (`INPUT_PULLUP`, attivo `LOW` verso `GND`) | Pressione breve + pressione lunga (`≥ 1500 ms`) verificate |

---

## 3. Dipendenze e Procedura Arduino IDE 2

- **IDE**: Arduino IDE 2 con supporto **Espressif ESP32** (`ESP32S3 Dev Module`).
- **Libreria esterna**: `U8g2` (`olikraus/U8g2`, testata con `2.36.18` in verifica locale e installata in Arduino IDE 2) + `Wire` inclusa nel core ESP32.
- **Sketch**: `04-Firmware/arduino-hw-test/jarvis_eyes3_hw_test/jarvis_eyes3_hw_test.ino` (con `#define OLED_DRIVER_SH1106 1`, `TouchManager` e `JARVIS_ENABLE_TOUCH` esclusi).
- **Impostazioni Board (Tools)**:
  - Flash Size: `16MB (128Mb)` | Flash Mode: `QIO 80MHz` | PSRAM: `OPI PSRAM`
  - Monitor Seriale: `115200 baud`
  - `USB CDC On Boot`: `Disabled` se collegato alla porta UART (`CH343`), `Enabled` se collegato alla porta USB nativa.

---

## 4. Stato dei Test: Superati vs Da Eseguire

### Test Hardware Reale Superati
- [x] Riconoscimento ESP32-S3 da Windows tramite USB.
- [x] Inizializzazione e funzionamento OLED **SH1106 128×64** su I²C indirizzo **`0x3C`**.
- [x] Pinout **`GPIO41` (SDA)** e **`GPIO42` (SCL)** verificato.
- [x] Compilazione e caricamento Eyes 3.0 tramite **Arduino IDE 2**.
- [x] Animazioni automatiche **Eyes 3.0** funzionanti su OLED reale.
- [x] Comandi seriali funzionanti (incluso `STATE:HAPPY`).
- [x] Pressione breve **`GPIO47`** funzionante (cambio espressione).
- [x] Pressione lunga **`GPIO47`** (`≥ 1500 ms`) funzionante: confermato `EVENT:AUTO_DEMO=ON` sul Monitor Seriale.

### Test Ancora da Eseguire
- [ ] Verifica sistematica individuale di tutte le 14 espressioni e dei profili (`PROFILE:CALM|LIVELY|PLAYFUL`) su OLED reale (finora testato ciclo automatico + `STATE:HAPPY`).
- [ ] Collaudo reale del sensore capacitivo tattile **`TTP223B`** su **`GPIO1`** (FASE 11.1, attualmente verificata solo a livello di codice, test unitari Python e progetto Wokwi).
- [ ] Integrazione e collaudo reale del microfono I²S **`INMP441`** (`GPIO4/5/6`).
- [ ] Integrazione e collaudo reale dell'amplificatore/speaker I²S **`MAX98357A`** (`GPIO7/15/16`).
- [ ] Integrazione e collaudo reale dei sensori I²C opzionali (`VL53L0X`, `MPU6050`, `BH1750`).
