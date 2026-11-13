# BOM Elettrica Preliminare – Base Mobile B2

> [!WARNING]
> **Nessun acquisto, cablaggio o costruzione è autorizzato** fino alla verifica fisica della scheda `ESP32-C3 SuperMini` scelta e alla compilazione della checklist batteria 2S.

| # | Componente | Specifiche tecniche minime / riferimento | Q.tà | Origine / Stato |
| :---: | :--- | :--- | :---: | :--- |
| 1 | **Controller secondario B2** | **ESP32-C3 SuperMini** (`3,3 V`, I²C su `GPIO 4/5`, verificare layout pin del venditore) | 1 | Invariato (pinout aggiornato) |
| 2 | **Driver motori** | **Toshiba `TB6612FNG`** (breakout con `470 µF + 100 nF` su `VM`, pull-down `10 kΩ` su `STBY`) | 1 | Confermato (`VM = 6,0 V`) |
| 3 | **Motoriduttori** | **N20 `150:1 MP 6V`** (`150 RPM`, `70 mA` vuoto, `0,67 A` stallo @ `6 V`) | 2 | `[DATASHEET]` Pololu |
| 4 | **Sensore corrente motori** | **`TI INA3221`** modulo I²C (`0–26 V`, `±163,8 mV`, `0x40`) + **2× shunt `0,1 Ω` 1% `≥ 0,5 W`** | 1 | `[DATASHEET]` TI |
| 5 | **Protezione transitori e filtro `INA3221`** | **2× `BAT54S`** (clamp Schottky su `AO1/BO1` verso `GND/VM`) + **4× `10 Ω`** + **2× `1 µF`** + **2× `100 nF`** | 1 set | **Aggiunto** per limite `-0,3 V` e `R_F ≤ 10 Ω` |
| 6 | **Buck Motori (`6,0 V`)** | **Buck sincrono `6,0 V / ≥ 3 A`** (es. `TPS54302`) | 1 | Regolazione `VM` |
| 7 | **Buck Logica (`5,09 V`)** | **Buck `5,09 V / ≥ 3 A`** stabile (`±0,5–1%`) | 1 | Linea `5 V` |
| 8 | **Ideal Diode `5 V`** | **`TI LM66100`** (`1,5–5,5 V`, `1,5 A` max, `79 mΩ` typ) | 1 | `[DATASHEET]` TI |
| 9 | **PTC supplementari motori** | **PTC `0,75 A` hold / `1,50 A` trip** (`1812L075` / `MF-MSMF075`) | 2 | Solo cortocircuito netto |
| 10 | **PTC linea `5 V`** | **PTC low-R `2,0 A` hold** ($R_{\min} \le 25\text{ m}\Omega$) | 1 | In serie a `+5V_A` |
| 11 | **Batteria `2S` piatta** | `2S1P` (`6,0–8,4 V`), `1500–2500 mAh`, `≥ 5 A` cont. / `≥ 8 A` picco, BMS+bilanciamento, max `80×50×20 mm` | 1 | Checklist pre-acquisto obbligatoria |
| 12 | **Caricatore `2S` + presa** | Caricatore **`8,4 V CC/CV`** + connettore ricarica dedicato su B2 | 1 | Separato da `JST-XH` |
| 13 | **Sensore ostacoli frontale** | **`VL53L0X`** (`I²C 0x29`, `XSHUT` a `3,3 V` via `10 kΩ`) | 1 | Copertura solo frontale |
| 14 | **Connettore A ↔ B2** | **JST-XH 6 pin** (`2,50 mm`, cavi corti `≤ 10 cm` `AWG #20/#22`) | 1 set | Non hot-plug |
| 15 | **Protezioni e passivi** | Interruttore `≥ 5 A`, fusibile `3–4 A`, partitore `100 kΩ + 47 kΩ`, resistenze `220–330 Ω`, `4,7 kΩ`, `10 kΩ`, condensatori | 1 kit | Protezione e filtraggio |
