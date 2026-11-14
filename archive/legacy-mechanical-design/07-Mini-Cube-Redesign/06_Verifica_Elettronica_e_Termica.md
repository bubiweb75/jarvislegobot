# 06 – Verifica Elettronica, Alimentazione e Raffreddamento (Mini Cubo)

---

## 1. Pinout Conservato (`ESP32-S3-DevKitC-1 N16R8`)

Nessuna modifica al pinout approvato in [`01-Hardware/02_Tabella_Pinout_Definitiva.md`](../../01-Hardware/02_Tabella_Pinout_Definitiva.md) e [`03-Mechanical-Design/05-Mobile-Electronics/04_Pinout_Connettore_JST-XH.md`](../05-Mobile-Electronics/04_Pinout_Connettore_JST-XH.md):

| Periferica | Pin / GPIO ESP32-S3 | Note |
|---|---|---|
| **INMP441 (I2S RX)** | `WS=GPIO 4`, `SCK=GPIO 5`, `SD=GPIO 6`, `L/R=GND`, `VDD=3.3V` | Solo `3,3 V` |
| **MAX98357A (I2S TX)** | `DIN=GPIO 7`, `BCLK=GPIO 15`, `LRC=GPIO 16`, `VIN=5V`, `SD=3.3V` | Speaker su `OUT+`/`OUT-`, mai verso GND; `C1 (470 µF)` + `C2 (100 nF)` su `VIN/GND` |
| **OLED 1,3" SH1106 (I2C)** | `SDA=GPIO 41`, `SCL=GPIO 42`, `VCC=3.3V` | Indirizzo `0x3C` tipico (da verificare su modulo fisico) |
| **Pulsante Meccanico NO** | `GPIO 47` → pulsante → `GND` | Pull-up interno abilitato (~45 kΩ) |
| **Espansione B2 (JST-XH 6-pin)** | `UART TX=GPIO 17`, `RX=GPIO 18`, `I2C=GPIO 8/9`, `+5V_A`, `GND` | Cablaggio predisposto sul fondo |
| **Pin Vietati / Riservati** | `GPIO 35–37` (PSRAM), `GPIO 0/3/45/46` (strapping), `GPIO 39/40` (disabilitati), `J1-3` (`RST`) | Invariati |

---

## 2. Alimentazione USB 5 V, Sicurezza e Commutazione B2

- **Modalità A (uso autonomo da scrivania):** ingresso dal **Breakout USB-C 5 V** (resistenze `CC 5,1 kΩ`, portata ≥ 2 A) collocato nella zona inferiore-posteriore, con distribuzione a stella verso **`J1-21` (`5V`)** della DevKitC-1 e verso **`VIN` (`MAX98357A`)**.
- **Modalità B (programmazione/debug da PC):** cavo `5 V` esterno scollegato; collegamento diretto alla porta `USB-C` della `DevKitC-1` tramite apertura dello sportello posteriore (e leggera estrazione della slitta o cavo USB-C a 90°).
- **Futura alimentazione da Base B2:** la linea `+5V_A` proveniente dal `Buck 5,09 V` di B2 entra attraverso il connettore `JST-XH 6-pin` protetta da **Ideal Diode `LM66100`** (`1,5 A` max) su B2 e dai diodi `D1/D7` (`1N5819HW-7-F`) onboard della `DevKitC-1`, evitando ritorni di corrente. Restano tassativi il **divieto di alimentazione simultanea** (USB-C PC + alimentazione esterna / B2) e l'inserimento del `JST-XH` esclusivamente a base B2 spenta.
- **Nessuna batteria nel Corpo A.**

---

## 3. Raffreddamento Passivo, Antenna Wi-Fi e Accessibilità `SGM2212`

- **Ventilazione passiva nel Mini Cubo (`Layout C`):**
  - Ingressi aria discreti lungo la parte inferiore delle pareti laterali/posteriore (`1–2` fessure `1×2` o *Grille Tile* basse, protette contro polvere/contatti).
  - Camino d'aria verticale libero nella metà posteriore-sinistra (`~24 × 22 mm`), che sale dalla zona `MAX98357A` / `Breakout USB-C` lungo la `ESP32-S3` fino a una **feritoia di sfogo superiore-posteriore** (`2412b` sul bordo posteriore del tetto, separata dalla camera speaker).
- **Accesso al regolatore `LDO SGM2212`:**
  - Con `ESP32-S3` montato verticalmente nel quadrante posteriore-destro (`Layout C`), il lato componenti della DevKitC-1 (incluso `SGM2212`) guarda direttamente verso lo **sportello posteriore apribile**, consentendo il controllo termico con termocoppia/IR durante il collaudo della FASE 4 senza smontare il cubo.
- **Antenna Wi-Fi PCB (`ESP32-S3`):**
  - Orientata verso l'alto nell'angolo posteriore-destro (`Z ≈ 72–79 mm`), circondata esclusivamente da plastica ABS LEGO, distante `≥ 2,6 mm` (con speaker `Ø 40 mm`) o `> 6 mm` (con speaker `Ø 36 mm`) dal magnete dello speaker e lontana da cavi audio/alimentazione.

*(Nessun collegamento elettrico, acquisto o montaggio è avviato in questa fase).*
