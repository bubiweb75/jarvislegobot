# Controllo Motori, Pinout ESP32-C3, Anticollisione e Matrice Fail-Safe – B2

> [!IMPORTANT]
> **Stato documento:** Verifica conclusiva pinout `ESP32-C3 SuperMini` e bus I²C. Le variazioni tra schede commerciali SuperMini vanno verificate fisicamente prima della saldatura (**`[PROVA NON ESEGUITA]`**).

---

## 1. Verifica `ESP32-C3 SuperMini`, Strapping Pin e Riassegnazione I²C

### 1.1 Analisi strapping pin e LED su `GPIO 8 / 9`
- **`[DATASHEET]`** `ESP32-C3` ha tre pin di strapping campionati al reset: **`GPIO 2`** (flottante), **`GPIO 8`** (flottante) e **`GPIO 9`** (pull-up interno debole, `1` = SPI Boot normale, `0` = Download Boot). La combinazione `GPIO 8 = 0` e `GPIO 9 = 0` durante il reset è **invalida/riservata** e può bloccare il boot.
- **Criticità specifiche della scheda `ESP32-C3 SuperMini`:**
  1. Non esiste un layout unico standardizzato tra i produttori terzi di `SuperMini`.
  2. Nella maggior parte delle varianti, **`GPIO 8`** è collegato al **LED di stato blu integrato** (attivo basso verso `3,3 V`, o LED RGB WS2812 su varianti *Plus*), e **`GPIO 9`** è collegato al pulsante fisico **`BOOT`**.
  3. Usare `GPIO 8/9` come bus I²C introduce il rischio che il LED integrato carichi la linea, lampeggi durante il traffico I²C, o che uno slave I²C (`INA3221` / `VL53L0X`) trattenga `SDA/SCL` basso al reset impedendo l'avvio o la programmazione.

### 1.2 Soluzione adottata: I²C su `GPIO 4 / 5` (non-strapping)
**`[DATASHEET]`** Il controller I²C dell'ESP32-C3 supporta la rimappatura completa tramite **GPIO Matrix** (`Wire.begin(SDA, SCL)`). Per eliminare ogni interferenza con boot, `BOOT` button e LED di bordo senza modificare l'architettura generale:
- **Bus I²C (`INA3221` `0x40` + `VL53L0X` `0x29`):** spostato su **`GPIO 4 (SDA)`** e **`GPIO 5 (SCL)`** (entrambi **non-strapping**, pull-up `4,7 kΩ` a `3,3 V`).
- **`GPIO 9`:** lasciato **completamente libero** per il solo pulsante `BOOT`.
- **`GPIO 8`:** usato come **`VL53L0X XSHUT`** con **pull-up `10 kΩ` a `3,3 V`** (garantisce `GPIO 8 = HIGH` al reset/download boot e controlla il reset hardware del `VL53L0X` a `3,3 V`).
- **`V_BAT` ADC:** spostato su **`GPIO 0` (`ADC1_CH0`, non-strapping)** per evitare che il partitore batteria mantenga `GPIO 2 = 0` durante il Download Boot a base spenta.

| Pin ESP32-C3 | Funzione definitiva | Tipo / Strapping | Note di sicurezza |
| :--- | :--- | :--- | :--- |
| **`GPIO 20 / 21`** | `UART RX / TX` | Non-strapping | `3,3 V` verso `ESP32-S3 GPIO 17/18` (`220–330 Ω` serie) |
| **`GPIO 4 / 5`** | **`I²C SDA / SCL`** | **Non-strapping** | `Wire.begin(4, 5)` esplicito (`400 kHz`); zero conflitti al boot |
| **`GPIO 0`** | `ADC1_CH0` (`V_BAT`) | **Non-strapping** | Partitore `100 kΩ + 47 kΩ` verso batteria 2S |
| **`GPIO 1, 2, 3`** | `AIN1, AIN2, PWMA` | `GPIO 2` strapping (output post-boot) | Pilota ponte A su `TB6612FNG` |
| **`GPIO 6, 7`** | `BIN1, BIN2` | Non-strapping | Direzione ponte B su `TB6612FNG` |
| **`GPIO 10`** | `PWMB` o `STBY`? → **`STBY`** | Non-strapping | **Pull-down `10 kΩ` a GND** (`STBY = LOW` al reset) |
| **`GPIO 8`** | `VL53L0X XSHUT` (o `PWMB`?) | Strapping + LED | **Pull-up `10 kΩ` a `3,3 V`** (`HIGH` al boot); `3,3 V` only |
| **`GPIO 9`** | Solo `BOOT` | Strapping | Nessun collegamento esterno |

> [!WARNING]
> **Nota su `PWMB`:** Contando i pin (`GPIO 0,1,2,3,4,5,6,7,8,9,10,20,21` = 13 pin), se `GPIO 9` resta libero per `BOOT`, restano **12 pin**: `UART` (2) + `I2C` (2) + `V_BAT` (1) + `TB6612` (`AIN1, AIN2, PWMA, BIN1, BIN2, PWMB, STBY` = 7) = **12 pin esatti** (`GPIO 8` assegna `PWMB` con pull-up `10 kΩ` — inoffensivo perché `STBY` ha pull-down `10 kΩ` al boot — oppure si collega `VL53L0X XSHUT` a `3,3 V` tramite `10 kΩ` rinunciando al reset hardware di `XSHUT`). **Scelta definitiva:** **`GPIO 8 = PWMB`** (con `STBY = LOW` hardware al boot, `PWMB` alto al boot non muove il motore; dopo il boot diventa PWM) e **`VL53L0X XSHUT` legato a `3,3 V` via `10 kΩ`**.

---

## 2. Sicurezza anticollisione (`VL53L0X` frontale)
- **Limiti documentati:** copertura solo frontale (`~25°`), angolo cieco posteriore e laterale, nessun anti-caduta (`cliff`), sensibilità ridotta su nero opaco/vetro.
- **Retromarcia:** **vietate retromarce automatiche non sorvegliate**. Consentita solo retromarcia manuale diretta `≤ 35%` PWM sotto controllo visivo.
- **Arresto:** **Short Brake (`150 ms`)** su ostacolo/emergenza controllata, poi **`STBY = LOW` (`High-Z`)**.

---

## 3. Matrice Fail-Safe completa

| Evento / Guasto | Rilevamento | Azione immediata su `TB6612FNG` | Stato motori | Ripristino |
| :--- | :--- | :--- | :--- | :--- |
| **1. Perdita UART** | Timeout da S3 `> 300 ms` **`[REQUISITO]`** | `PWM=0`, `INx=L`, **`STBY = LOW`** | **High-Z** | Nuovo handshake valido |
| **2. Reset ESP32-C3** | `TWDT 500 ms` + pull-down `10 kΩ` su `STBY` | `STBY = LOW` in hardware | **High-Z** | Comando `ARM` da S3 |
| **3. Batteria scarica** | `V_BAT < 6,4 V` (`GPIO 0 ADC1`) **`[REQUISITO]`** | **`STBY = LOW`** permanente | **High-Z** | Ricarica batteria |
| **4. Stallo / sovracorrente** | `INA3221` `≥ 0,48 A` (`≥ 350 ms`) / `≥ 0,85 A` (`≥ 60 ms`) + PTC | **Spegnimento singolo canale** / `STBY=L` | **Canale OFF / High-Z** | Reset comando da S3 |
| **5. Ostacolo frontale** | `VL53L0X < 150 mm` **`[STIMA]`** | **Short Brake `150 ms` → `STBY = LOW`** | **Frenata → High-Z** | Solo rotazione sul posto |
| **6. Guasto sensore I²C** | NACK / timeout `VL53L0X` o `INA3221` (`> 3` letture) | **Short Brake `150 ms` → `STBY = LOW`** | **Frenata → High-Z** | Stop marcia autonoma |
