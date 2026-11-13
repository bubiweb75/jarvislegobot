# Elaborato A – Schema Elettronico Completo, Alimentazione e Protezioni

**Progetto:** JARVIS LEGO BOT – FASE 2 (Progettazione Esecutiva Hardware)  
**MCU di riferimento:** ESP32-S3-DevKitC-1 N16R8 (16 MB Flash, 8 MB Octal PSRAM)  
**Profilo firmware di riferimento:** `78/xiaozhi-esp32` (`bread-compact-wifi`)

---

## 1. Schema Elettronico Completo (Interconnessioni Logiche e Alimentazione)

```text
                MODALITÀ A: ALIMENTAZIONE AUTONOMA ROBOT
                Alimentatore USB 5V / >= 2A (Cavo USB-C)
                                   │
                [Breakout USB-C 5V (CC 5.1kΩ, >= 2A)]
                        │                    │
                  (+5V VBUS)               (GND)
                        │                    │
        ┌───────────────┴──────────────┐     │
        │ (Ramo 1: Logica)             │ (Ramo 2: Potenza Audio)
        ▼                              ▼
   [J1-21: 5V]                  [C1: 470µF 16V] + [C2: 100nF]
  ┌──────────────────────┐             │   (vicino a VIN/GND)
  │ ESP32-S3-DevKitC-1   │             ▼
  │       N16R8          │      ┌─────────────┐
  │                      │      │  MAX98357A  │
  │ J1-1/2 (3V3) ──┬─────┼─────►│ SD   (3.3V) │
  │                │     │ 5V ─►│ VIN         │      ┌──────────────┐
  │ J1-22 / J3-1,  │     │ GND ►│ GND         │      │ Speaker      │
  │ 21,22  (GND) ──┼─────┼──┐   │             │ OUT+ ►│ (+) 4Ω / 3W  │
  │                │     │  │   │             │ OUT- ►│ (-)          │
  │      GPIO 7  ──┼─────┼──┼──►│ DIN         │      └──────────────┘
  │      GPIO 15 ──┼─────┼──┼──►│ BCLK        │
  │      GPIO 16 ──┼─────┼──┼──►│ LRC         │
  │                │     │  │   │ GAIN (NC)   │
  │                │     │  │   └─────────────┘
  │                │     │  │
  │                │     │  │   ┌─────────────┐
  │                ├─────┼──┼──►│ VDD  INMP441│
  │                │     ├──┼──►│ GND         │
  │                │     ├──┼──►│ L/R (Left)  │
  │      GPIO 4  ──┼─────┼──┼──►│ WS          │
  │      GPIO 5  ──┼─────┼──┼──►│ SCK         │
  │      GPIO 6  ◄─┼─────┼──┼───┤ SD          │
  │                │     │  │   └─────────────┘
  │                │     │  │
  │                │     │  │   ┌─────────────┐
  │                └─────┼──┼──►│ VCC  OLED   │
  │                      │  ├──►│ GND  1.3"   │
  │      GPIO 41 ────────┼──┼──►│ SDA  128x64 │
  │      GPIO 42 ────────┼──┼──►│ SCL (0x3C)  │
  │                      │  │   └─────────────┘
  │                      │  │
  │      GPIO 47 ────────┼──┼───┐
  │ (Pull-up interno)    │  │   │ [Pulsante Meccanico NO]
  │                      │  └───┴──o/ o──┘
  └──────────────────────┘
```

*(Nota: Tutte le masse `GND` del breakout USB-C, della DevKitC-1 `J1-22` / `J3-1,21,22`, del MAX98357A, dell'INMP441, dell'OLED e del pulsante confluiscono su un nodo comune di massa a stella).*

---

## 2. Modalità di Alimentazione e Protezioni Hardware

### 2.1 Le due modalità operative (obbligatorie)

#### Modalità A – Alimentazione autonoma del robot
- **Sorgente:** Alimentatore esterno **5 V / ≥ 2 A** collegato a un **breakout USB-C 5 V** certificato per almeno 2 A.
- **Distribuzione a stella:** Il nodo `+5V` del breakout alimenta in parallelo due rami distinti:
  1. **Ramo 1 (Logica):** pin **`J1-21` (`5V`)** della ESP32-S3-DevKitC-1.
  2. **Ramo 2 (Potenza Audio):** pin **`VIN`** del MAX98357A (protetto da `C1` + `C2`).
- **Massa comune:** Ritorno a stella verso il `GND` del breakout e i pin `GND` della DevKitC-1 (`J1-22`, `J3-1`, `J3-21`, `J3-22`).
- **Nota sul breakout USB-C:** Le resistenze CC da **5,1 kΩ** (su `CC1` e `CC2` verso `GND`) identificano semplicemente il dispositivo come utilizzatore USB-C (*Sink*) a 5 V, ma **non garantiscono automaticamente una disponibilità di 3 A**. La corrente reale dipende dall'alimentatore, dal cavo USB-C e dalla portata delle piste/connettore del breakout, che vanno verificati prima dell'uso.

#### Modalità B – Programmazione e debug da PC
- **Scollegare il ramo 5 V esterno** (staccare il cavo dal breakout USB-C o aprire un eventuale interruttore sul `+5V` esterno).
- Collegare la **ESP32-S3-DevKitC-1 direttamente al PC** tramite una delle sue porte USB-C onboard.
- **DIVIETO ASSOLUTO:** Non alimentare **mai** contemporaneamente la DevKitC-1 dalla porta USB-C del PC e dall'alimentazione esterna sul pin `5V` (`J1-21`).

### 2.2 Circuito di protezione della ESP32-S3-DevKitC-1 (Verifica da schema ufficiale)
Dall'analisi dello schema elettrico ufficiale Espressif **ESP32-S3-DevKitC-1 (v1.1)**:
- Sui rami di ingresso delle due porte USB (`VBUS` porta USB-to-UART e `VBUSB` porta USB nativa) sono presenti due **diodi Schottky `D1` e `D7` (sigla `1N5819HW-7-F`, 40 V / 1 A max)** in configurazione OR-ing verso la linea comune `VCC_5V`.
- Il pin **`J1-21` (`5V`)** è collegato alla linea `VCC_5V` (a valle dei diodi `D1`/`D7`), mentre il regolatore LDO **`U2` (`SGM2212-3.3XKC3G/TR`)** converte `VCC_5V` nei **`3,3 V`** (`VCC_3V3`) che alimentano il modulo ESP32-S3 e il pin `3V3` (`J1-1`, `J1-2`).
- **Motivazione della distribuzione a stella:** Prelevare la corrente di picco dell'amplificatore audio (3 W) passando attraverso i diodi USB onboard (`1 A` nominali) li porterebbe vicino al limite di corrente causando cadute di tensione. Alimentando a stella in **Modalità A**, la corrente del MAX98357A non attraversa né i diodi `D1`/`D7` né le piste della DevKitC-1.
- **Nota per varianti/cloni:** Su schede compatibili di terze parti o revisioni diverse dalla v1.1, sigla del diodo e dell'LDO possono differire; resta obbligatoria la verifica visiva sulla scheda fisica acquistata.

### 2.3 Protezioni e Filtraggio
- **Condensatore elettrolitico `C1` (470 µF, ≥ 10 V / 16 V):** Posizionato il più vicino possibile a `VIN` e `GND` del MAX98357A per assorbire i picchi di corrente audio.
- **Condensatore ceramico `C2` (100 nF, ≥ 16 V):** In parallelo a `C1` per filtrare disturbi ad alta frequenza della commutazione Classe D.
- **Livelli logici a 3,3 V:** INMP441, OLED 1,3" e pin `SD` del MAX98357A vanno alimentati esclusivamente da `3V3` (`J1-1` / `J1-2`), **mai a 5 V**. Il MAX98357A **non** va mai alimentato dal pin `3V3`.
- **Altoparlante:** Collegare lo speaker da 4 Ω / 3 W **esclusivamente** tra i morsetti differenziali `OUT+` e `OUT-` del MAX98357A (mai riferire un polo a `GND`).

### 2.4 Dimensionamento Cavi
- **Alimentazione 5 V, GND principali e cavi Speaker (`OUT+`, `OUT-`):** **22 AWG** multifilare flessibile (< 15 cm).
- **Segnali digitali (`I2S`, `I2C`, `GPIO 47`) e alimentazione `3,3 V`:** **26 AWG – 28 AWG**.

---

## 3. Bilancio Energetico (Distinzione Rail 3,3 V vs Ramo 5 V)

Poiché il regolatore `U2` (`SGM2212-3.3`) è un **LDO lineare**, la corrente prelevata dal ramo `5 V` per alimentare il rail `3,3 V` è approssimativamente **1:1** rispetto alla corrente assorbita a `3,3 V` ($I_{5V,LDO} \approx I_{3V3}$ + corrente di quiescenza trascurabile; la differenza di tensione $1,7\,\text{V}$ viene dissipata in calore dall'LDO).

### 3.1 Carico sul Rail 3,3 V (alimentato da LDO `U2` della DevKitC-1)

| Componente | Tensione | Corrente Tipica (3,3 V) | Corrente Picco (3,3 V) | Ipotesi / Note |
|---|---|---|---|---|
| **ESP32-S3-WROOM-1 N16R8** | 3,3 V | 150 – 220 mA *(stima operativa)* | ~355 mA *(datasheet Wi-Fi TX 802.11b 20,5 dBm)* / ~500 mA *(stima conservativa peggiore con CPU 240 MHz + PSRAM)* | Valori datasheet Wi-Fi TX: 285–297 mA (802.11g/n), 355 mA (802.11b). Il valore 500 mA è una stima cautelativa di picco simultaneo, non un consumo continuo |
| **OLED 1,3" 128×64** (SH1106/SSD1306) | 3,3 V | 15 mA | ~25 mA | Schermo con volto animato / testo ad alta copertura pixel |
| **Microfono INMP441** | 3,3 V | 1,4 mA | 1,5 mA | Assorbimento nominale da datasheet |
| **MAX98357A (pin logico `SD`)** | 3,3 V | < 0,1 mA | < 0,1 mA | Solo riferimento logico di abilitazione |
| **Subtotale Rail 3,3 V** | **3,3 V** | **~167 – 237 mA** | **~527 mA** | **Corrisponde a ~167 – 237 mA (tip.) / ~527 mA (picco) sul ramo 5 V** |

### 3.2 Carico Totale sul Ramo 5 V (visto dall'alimentatore)

| Ramo / Utenza a 5 V | Corrente Tipica (5 V) | Corrente Picco (5 V) | Ipotesi / Calcolo |
|---|---|---|---|
| **Ramo 1: DevKitC-1 (`J1-21` → LDO 3,3 V + bridge UART/LED)** | ~175 – 245 mA | ~535 mA | Subtotale rail 3,3 V (rapporto 1:1 su LDO) + ~8 mA circuiteria 5 V/LED |
| **Ramo 2: MAX98357A + Speaker 4 Ω / 3 W** | ~230 – 340 mA | ~682 mA | Tipica: ~1,0–1,5 W medi con efficienza Classe D ~88% ($P / (0,88 \cdot 5\,\text{V})$). Picco: 3 W nominali ($3\,\text{W} / (0,88 \cdot 5\,\text{V}) \approx 682\,\text{mA}$, con transienti istantanei attenuati da `C1`) |
| **TOTALE SU ALIMENTATORE 5 V** | **~405 – 585 mA** | **~1,22 A** | (~2,0 – 2,9 W medi; ~6,1 W picco simultaneo Wi-Fi TX + audio max) |

**Verifica alimentatore:**
- Un alimentatore **5 V / 2 A (10 W)** certificato offre un margine di **~0,78 A (~39%)** oltre il picco peggiore simultaneo (1,22 A).

### 3.3 Verifica Termica del Regolatore LDO `SGM2212-3.3XKC3G/TR`
- **Parametri da datasheet:** $I_{out,\max} = 800\text{ mA}$, package `SOT-223-3`, $\theta_{JA} \approx 117\,^\circ\text{C/W}$, $T_{J,\max} = 125\,^\circ\text{C}$, $I_Q \approx 80\,\mu\text{A}$.
- **Salto di tensione (caso peggiore Modalità A, $V_{IN} = 5,0\text{ V}$):** $\Delta V = 5,0\text{ V} - 3,3\text{ V} = 1,7\text{ V}$.
- **Regime tipico (167 – 237 mA):**
  - $P_D = 1,7\text{ V} \times 0,167\text{–}0,237\text{ A} = \mathbf{0,284\text{ – }0,403\text{ W}}$
  - $\Delta T = P_D \times 117\,^\circ\text{C/W} = \mathbf{33,2\text{ – }47,1\,^\circ\text{C}}$
  - Con $T_A = 35\,^\circ\text{C}$ (interno scocca ventilata): $T_J \approx 68\text{ – }82\,^\circ\text{C}$ (**margine ~43–57 °C** rispetto a $125\,^\circ\text{C}$).
- **Picco teorico (527 mA):** $P_D = 0,896\text{ W} \Rightarrow \Delta T = 104,8\,^\circ\text{C}$ ($T_J = 139,8\,^\circ\text{C}$ a $T_A = 35\,^\circ\text{C}$, **non sostenibile in regime continuo**). Tuttavia i picchi Wi-Fi TX (285–355 mA da datasheet, fino a ~500 mA stimati) sono **impulsivi (ms)** e vengono mediati dall'inerzia termica del package SOT-223-3 e del rame PCB.
- **Decisione:** Mantenere la configurazione originale (**Soluzione C**), vincolata a **ventilazione passiva nella scocca LEGO (FASE 3)** e a **test termico sotto carico continuo (FASE 4)**.

---

## 4. Nota Architetturale sul Bridge Raspberry Pi 5 (Sicurezza e Separazione)

- **Metriche Hardware Raspberry Pi 5** (CPU, RAM, temperatura, uptime, rete): lette in sola lettura da `/proc` e `/sys/class/thermal` in container non privilegiato (`cap_drop: [ALL]`), senza accesso a Docker.
- **Metriche Container Docker:** lette esclusivamente tramite **`docker-socket-proxy`** isolato su rete interna (`POST=0`, `EXEC=0`, `IMAGES=0`, `VOLUMES=0`, solo `GET` su `CONTAINERS=1` e `INFO=1`).
- **Zero modifiche** ai servizi esistenti sul Raspberry Pi 5.
