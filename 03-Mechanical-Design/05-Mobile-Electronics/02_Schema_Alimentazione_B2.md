# Schema di Alimentazione, Protezione Stallo INA3221, Termica e Batteria – B2

> [!IMPORTANT]
> **Stato documento:** Verifica conclusiva `INA3221` su ponte H `TB6612FNG`, taratura soglie e sicurezza alimentazione. Tutte le verifiche sperimentali sono **`[PROVA NON ESEGUITA]`**.

---

## 1. Collegamento reale `INA3221` sul ponte H `TB6612FNG`

### 1.1 Posizione degli shunt e collegamenti `IN+ / IN−`
Poiché il `TB6612FNG` condivide `VM` e `PGND` tra i due ponti H, la misura indipendente dei due motori avviene sulle uscite di fase:
- **Canale 1 (`CH1`, Motore SX):** shunt **`0,1 Ω` (1%, `≥ 0,5 W`)** in serie tra **`TB6612FNG AO1`** e il morsetto `+` del motore SX (`AO2` diretto al morsetto `−`).
  - `IN1+` collegato al lato `AO1` (tramite `R_F = 10 Ω`).
  - `IN1−` collegato al lato motore SX (tramite `R_F = 10 Ω`).
- **Canale 2 (`CH2`, Motore DX):** shunt **`0,1 Ω` (1%, `≥ 0,5 W`)** in serie tra **`TB6612FNG BO1`** e il morsetto `+` del motore DX (`BO2` diretto al morsetto `−`).
  - `IN2+` collegato al lato `BO1` (tramite `R_F = 10 Ω`).
  - `IN2−` collegato al lato motore DX (tramite `R_F = 10 Ω`).
- **Canale 3 (`CH3`, Monitor `VM`):** `IN3+` collegato a **`VM (+6,0 V)`** (senza shunt o con `IN3−` a `VM`) per telemetria tensione motori.
- **Massa:** `GND` di `INA3221` collegato al punto stella di massa del `TB6612FNG`.

### 1.2 Polarità, PWM, Short Brake e modo comune
- **Polarità marcia avanti / retromarcia:**
  - **Avanti (`AO1 = +6 V, AO2 = 0 V`):** corrente `AO1 → Shunt → Motore → AO2`, tensione differenziale **`V_shunt > 0`** (es. `+67 mV` a `0,67 A` **`[CALCOLO]`**).
  - **Retromarcia (`AO1 = 0 V, AO2 = +6 V`):** corrente `AO2 → Motore → Shunt → AO1`, tensione differenziale **`V_shunt < 0`** (es. `−67 mV` a `0,67 A`). **`[DATASHEET]`** `INA3221` misura bidirezionalmente entro **`±163,8 mV`** (`±1,638 A` con `0,1 Ω`); il firmware usa `|I_meas|`.
- **Compatibilità modo comune e transitori PWM:**
  - **`[DATASHEET]`** Il modo comune ammesso su `IN+ / IN−` è **`0 V – +26 V`**, con **Absolute Maximum Rating `-0,3 V` rispetto a `GND`**.
  - Durante la commutazione PWM (`20 kHz`), `AO1/BO1` oscillano tra `0 V` e `+6,0 V` (dentro `0–26 V`). Tuttavia, nei tempi morti di commutazione induttiva, i diodi parassiti dei MOSFET possono portare brevemente il nodo `AO1/BO1` a **`~ -0,7 V`**, violando il limite `-0,3 V` dell'`INA3221`.
  - **Protezione obbligatoria aggiunta:** diodi Schottky veloci **`BAT54S`** (o equivalenti `V_F ≤ 0,3 V`) tra `AO1/BO1` e `GND` (catodo su `AO1/BO1`, anodo su `GND`) per clampare eventuali picchi negativi a `~ -0,25 V`, più condensatore ceramico `100 nF` ai capi del motore.
- **Comportamento durante `Short Brake` (`IN1=H, IN2=H`):** entrambi i morsetti vengono chiusi a `GND` dai MOSFET inferiori (modo comune `~0 V`, dentro `0–26 V`); la corrente induttiva residua decade a zero entro i `150 ms` di frenata attiva, poi `STBY = LOW` (`High-Z`).

### 1.3 Filtro RC, tempo di conversione e latenza firmware
- **Filtro RC sugli ingressi `INA3221`:** **`[DATASHEET]`** `INA3221` richiede resistenze di filtro **`R_F ≤ 10 Ω`** per evitare errori di offset dovuti alla corrente di bias in ingresso. Si adotta **`R_F = 10 Ω`** per linea + condensatore differenziale ceramico **`C_F = 1 µF`** tra `IN+` e `IN−`:
  - **`[CALCOLO]`** Costante di tempo $\tau = (2 \times 10\,\Omega) \times 1\,\mu\text{F} = \mathbf{20\,\mu\text{s}}$ ($f_c \approx \mathbf{7,96\text{ kHz}}$): **non introduce alcun ritardo significativo** rispetto ai `50 ms` / `350 ms` di intervento.
- **Configurazione conversione `INA3221` (`3` canali attivi):**
  - **`[DATASHEET]`** `T_shunt_conv = 1,1 ms` (integra `22` cicli PWM a `20 kHz`), `T_bus_conv = 140 µs`, averaging **`N_samples = 4`**.
  - **`[CALCOLO]`** Tempo ciclo completo hardware = $3 \times 4 \times (1,1\text{ ms} + 0,14\text{ ms}) = \mathbf{14,9\text{ ms}}$.
  - **Interrogazione I²C (`400 kHz`):** ogni **`20 ms`** (`50 Hz`). Latenza massima per campione: `14,9 ms + ~0,2 ms (I²C) + ≤ 20 ms (loop) ≈` **`35 ms`**.

---

## 2. Taratura delle soglie di corrente e procedura di collaudo

> [!NOTE]
> Le soglie seguenti (`0,48 A` stallo / `0,85 A` sovracorrente) sono **valori iniziali di progetto `[REQUISITO]`**, **NON valori sperimentalmente confermati**.

### 2.1 Soglie iniziali di progetto
| Condizione | Soglia iniziale (`INA3221`) | Tempo / Campioni (`20 ms`/cad.) | Azione |
| :--- | :--- | :--- | :--- |
| **Spunto avviamento** | Fino a `0,67 A` **`[DATASHEET]`** | `< 150 ms` (durante `soft-start`) | Consentito; nessun blocco |
| **Stallo / blocco ruota** | **`≥ 0,48 A`** (dopo `soft-start`) **`[REQUISITO]`** | **`≥ 350 ms`** (`18` campioni) | Spegnimento **singolo canale** (`INx=L, PWM=0`) |
| **Sovracorrente critica** | **`≥ 0,85 A`** **`[REQUISITO]`** | **`≥ 60 ms`** (`3` campioni) | **`STBY = LOW`** immediato |
| **Cortocircuito netto** | **`≥ 1,50 A`** **`[DATASHEET]`** | Intervento hardware PTC | `PTC 0,75 A` limita il circuito |

### 2.2 Procedura di collaudo e distinzione spunto vs stallo `[PROVA NON ESEGUITA]`
1. **Registrazione profili reali (`14,9 ms` / `50 Hz` via log seriale):**
   - **Motore a vuoto** (ruote sollevate): verifica corrente base (`~70 mA` attesi **`[DATASHEET]`**).
   - **Avviamento** da fermo con `soft-start 150 ms`: misura picco massimo e durata reale dello spunto (`τ_meccanica`).
   - **Marcia normale** su pavimento liscio e su tappeto: misura corrente media e varianza.
   - **Curva stretta / rotazione sul posto**: misura squilibrio tra ruota interna ed esterna.
   - **Contatto con ostacolo** (prima che intervenga `VL53L0X`): misura salita corrente.
   - **Ruota bloccata** meccanicamente: misura corrente di stallo reale a `6,0 V` e tempo di intervento.
2. **Criterio anti-falsi interventi:**
   - **Mascheramento `soft-start` (`150 ms`):** la soglia stallo (`0,48 A`) è ignorata durante i primi `150 ms` di rampa (resta attiva solo la soglia critica `0,85 A`).
   - **Filtro di persistenza:** lo spunto reale decade sotto `0,35 A` entro `~50–100 ms` **`[STIMA]`**; solo una corrente `≥ 0,48 A` sostenuta per **`≥ 350 ms`** consecutivi viene classificata come stallo. Le soglie finali verranno tarate al `~75%` della corrente di stallo reale misurata su prototipo.

---

## 3. Verifica termica `TB6612FNG`
- **`[DATASHEET]`** $I_{O(\text{AVE})} = 1,2\text{ A}/\text{ch}$, $I_{O(\text{PEAK})} = 3,2\text{ A}$ (**non continuativa**), $R_{ON} = 0,5\,\Omega$, $P_{D(\max)} = 0,78\text{ W}$ (IC solo, `25 °C`), $0,89\text{ W}$ (`50×50 mm`), $1,36\text{ W}$ (`76,2×114,3 mm`).
- **`[CALCOLO]`** Doppio stallo continuo a `6,0 V` (`0,67 A/ch`): $P_{\text{chip}} = 2 \times 0,67^2 \times 0,5 = \mathbf{0,449\text{ W}}$. Su breakout compatta (`~20 × 20 mm`) in vano chiuso a `45 °C` ($P_{D,\max} \approx 0,655\text{ W}$), un doppio stallo continuo porterebbe $T_j \approx 117\,^\circ\text{C}$ **`[STIMA]`**; con taglio firmware `350 ms` la dissipazione media resta `< 0,10 W`.
- **`[PROVA NON ESEGUITA]`** Test `15 min` a vano chiuso: arresto prova se `TB6612FNG > 85 °C` o carcassa N20 `> 65 °C`.

---

## 4. Linea `5 V` (`4,90–5,10 V` su `JST-XH Pin 1`)
- Modulo A: `0,25–0,40 A` continui **`[STIMA]`**, **`1,22 A` picco** **`[CALCOLO/STIMA]`**.
- **`LM66100`:** $I_{\max} = 1,50\text{ A}$ **`[DATASHEET]`** → margine **`0,28 A` (`18,7%`)**. **Vietato aggiungere carichi futuri.**
- Caduta serie (`LM66100` `79 mΩ` + `PTC` `~30 mΩ` + cavi `≤ 10 cm` / contatti `~31 mΩ` ≈ `140 mΩ` **`[CALCOLO]`**): con **`Buck 5,09 V`**, tensione su `JST-XH Pin 1` = `5,09 V` (`0 A`), `5,04 V` (`0,35 A`), **`4,92 V`** (`1,22 A`) — entro **`4,90–5,10 V`**. Anti-backfeed garantito da `D1/D7` su DevKitC-1 + `LM66100` + divieto uso simultaneo USB-C/B2.

---

## 5. Batteria `2S` piatta e checklist commerciale
- **`[REQUISITO]`** `2S1P` (`6,0–8,4 V`), `≤ 80 × 50 × 20 mm`, `1500–2500 mAh`, `≥ 5 A` cont. / `≥ 8 A` picco, BMS (OVP/UVP/OCP/SCP + bilanciamento), caricatore **`8,4 V CC/CV`** su presa dedicata separata da `JST-XH`.
- **Checklist pre-acquisto:** `[ ]` Celle/chimica · `[ ]` Capacità reale su datasheet · `[ ]` Dimensioni e peso (`≤ 80×50×20 mm`) · `[ ]` Corrente cont./picco · `[ ]` BMS con bilanciamento · `[ ]` Protezioni OVP/UVP/OCP/SCP · `[ ]` Caricatore `8,4 V CC/CV` · `[ ]` Connettore ricarica separato · `[ ]` Prova ingombro vano B2 **`[PROVA NON ESEGUITA]`**.
