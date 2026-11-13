# Procedure di Sicurezza, Collaudo e Tabella Finale di Approvazione – B2

> [!CAUTION]
> **Tutte le prove fisiche descritte di seguito sono `[PROVA NON ESEGUITA]`.** Nessun acquisto, cablaggio o collegamento al Modulo A è autorizzato prima dell'approvazione finale.

---

## 1. Piano di collaudo su banco `[PROVA NON ESEGUITA]`

### Fase A – Verifica preliminare scheda `ESP32-C3 SuperMini` e linea `5 V`
1. Verificare con multimetro sulla scheda `ESP32-C3 SuperMini` effettivamente scelta che **`GPIO 4/5`** non abbiano LED o resistenze parassite e che **`GPIO 9`** risponda al pulsante `BOOT`.
2. Alimentare B2 da alimentatore da banco (`8,4 V / 2 A`, senza Modulo A) e misurare `JST-XH Pin 1`: **`4,90–5,10 V`** sia a `0 A` sia a `1,22 A`, assenza di backfeed e temperatura `LM66100`.

### Fase B – Verifica `INA3221`, clamp `BAT54S`, taratura soglie e termica `TB6612FNG`
1. Verificare `Buck 6,0 V` su `VM` e pull-down `10 kΩ` su `STBY` (`< 0,2 V` a C3 spento).
2. Verificare all'oscilloscopio (o multimetro) su `AO1/BO1` che i diodi **`BAT54S`** limitino eventuali picchi negativi entro `≥ -0,3 V` rispetto a `GND` durante PWM `20 kHz`.
3. **Campagna di taratura corrente `INA3221` (`14,9 ms` / `50 Hz`):** acquisire i profili reali in 6 condizioni:
   - motore a vuoto, avviamento (`soft-start`), marcia normale (liscio/tappeto), curva stretta, contatto ostacolo, ruota bloccata.
   - Tarare le soglie definitive per distinguere spunto (`< 150 ms`) da stallo sostenuto (`≥ 350 ms`) senza falsi interventi.
4. **Test termico (`15 min` marcia + 5 cicli stallo):** arresto immediato se `TB6612FNG > 85 °C` o `N20 > 65 °C`.

### Fase C – Matrice Fail-Safe e anticollisione
1. Verificare `STBY = LOW` su perdita UART (`< 300 ms`), reset C3, `V_BAT < 6,4 V`, guasto I²C.
2. Verificare `Short Brake 150 ms → STBY = LOW` su ostacolo `< 150 mm` e divieto retromarcia autonoma.

---

## 2. Tabella finale di chiusura criticità e approvazione

| Criticità | Soluzione adottata | Componente interessato | Verifica richiesta (`[PROVA NON ESEGUITA]`) | Stato |
| :--- | :--- | :--- | :--- | :--- |
| **PTC `0,75 A` inefficace su stallo `0,67 A`** | `INA3221` su `AO1/BO1` (`0,1 Ω`) + taglio `350 ms`; PTC solo per corto (`≥ 1,50 A`) | `INA3221`, shunt `0,1 Ω`, `PTC`, `N20` | Taratura profili reali (vuoto, spunto, marcia, curva, ostacolo, blocco) | **Approvata su carta** |
| **Picchi negativi PWM su `INA3221` (`-0,3 V`) e `R_F`** | Clamp Schottky **`BAT54S`** verso `GND/VM` + `R_F = 10 Ω` (`≤ 10 Ω` datasheet) + `1 µF` ($\tau = 20\,\mu\text{s}$) | `INA3221`, `BAT54S`, `TB6612FNG` | Verifica transitori su `AO1/BO1` e latenza ciclo `14,9 ms` | **Approvata su carta** |
| **Strapping `GPIO 8/9` e LED su `ESP32-C3 SuperMini`** | I²C spostato su **`GPIO 4/5`** (non-strapping); `GPIO 9` libero per `BOOT`; `V_BAT` su `GPIO 0`; `GPIO 8` con `10 kΩ` PU | `ESP32-C3 SuperMini`, `VL53L0X`, `INA3221` | Verifica pinout/LED sulla scheda fisica prima della saldatura | **Approvata su carta** |
| **Termica `TB6612FNG` in doppio stallo** | `VM = 6,0 V` (`0,45 W` teorici) + taglio `350 ms` + limiti `85 °C`/`65 °C` | `TB6612FNG`, `Buck 6,0 V` | Test termico `15 min` a vano chiuso | **Approvata su carta** |
| **Linea `5 V` (`4,90–5,10 V`) e `LM66100`** | `Buck 5,09 V` + `LM66100` (margine `18,7%`) + `PTC low-R` + cavi `≤ 10 cm` | `Buck 5,09 V`, `LM66100`, `PTC`, `JST-XH` | Misura tensione a `0 A` e `1,22 A` + temperatura | **Approvata su carta** |
| **Retromarcia non sorvegliata** | Divieto retromarcia autonoma; manuale `≤ 35%`; `Short Brake 150 ms → STBY=L` | `VL53L0X`, `TB6612FNG` | Test blocco marcia su guasto I²C e `Short Brake` | **Approvata su carta** |
| **Batteria `2S` commerciale** | Checklist pre-acquisto in 9 punti su datasheet reale | Batteria `2S1P`, caricatore `8,4 V` | Compilazione checklist su prodotto reale | **In attesa verifica commerciale** |
