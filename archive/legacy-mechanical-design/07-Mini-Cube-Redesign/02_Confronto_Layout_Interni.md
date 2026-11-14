# 02 – Confronto Obbligatorio dei Tre Layout Interni

Tutti e tre i layout sono valutati dentro il vano netto **`64,0 × 64,0 mm`** (`8 × 8 stud`) di un corpo **`80 × 80 mm`** (`10 × 10 stud`), considerando ingombri reali comprensivi di header, raggio di curvatura cavi (`~8–10 mm`), spessori di fissaggio e accessibilità.

---

## 1. Tabella Dimensioni Reali + Margini di Ingombro Considerati

| Componente | Corpo nudo (`mm`) | Con header/connettori/cavi (`mm`) | Note di ingombro |
|---|---|---|---|
| **ESP32-S3-DevKitC-1 N16R8** | `63,0 × 25,4 × 13,0` | **`63,0 × 25,4 × 22,0`** (con pin 90° / cavi) | Spina USB-C dritta richiede `+20 mm` assiali; con slitta estraibile o cavo 90° bastano `~10–14 mm` |
| **OLED 1,3" SH1106** *(parametrico)* | `~35,5 × 33,5 × 4,0` | **`36,0 × 34,0 × 11,0`** | Include 4 pin I2C + curva fili `26 AWG` |
| **Speaker 4 Ω / 3 W (Opz. A)** | `Ø 40,0 × 20,0` | **`Ø 40,0 × 22,5`** | Include guarnizione `~2 mm` + cavi saldati |
| **Speaker 4 Ω / 3 W (Opz. B slim)** | `Ø 36,0 × 14,0` | **`Ø 36,0 × 16,5`** | Alternativa compatta consigliata se disponibile |
| **MAX98357A + C1/C2** | `19,0 × 18,0 × 3,0` | **`22,0 × 20,0 × 14,0`** | Include `C1 (470 µF Ø8×11 mm)` vicino a `VIN/GND` |
| **INMP441** | `Ø 14,0 × 3,0` | **`Ø 16,0 × 10,0`** | Include anello gommapiuma + cavi `26 AWG` |
| **Breakout USB-C 5 V** | `15,0 × 12,0 × 4,0` | **`18,0 × 15,0 × 8,0`** | Zona posteriore bassa |
| **JST-XH 6-pin (A ↔ B2)** | `17,5 × 8,0 × 6,0` | **`18,0 × 12,0 × 10,0`** | Zona inferiore centrale verso umbilical port |

---

## 2. Layout A — ESP32-S3 Verticale Centrato

```text
  PIANTA (64 × 64 mm)                     SEZIONE LATERALE (H_est = 105.6 mm min)
  ┌──────────────────────────┐            ┌──────────────────────────┐
  │     [OLED 1.3" 36mm]     │ Fronte     │  [Griglia Tetto]         │
  ├──────────────────────────┤            │  [Speaker Ø40 × 20mm]    │ 23 mm
  │   ╭──────────────────╮   │            ├──────────────────────────┤
  │   │  Speaker Ø40mm   │   │            │  [OLED] │ GAP INSUFF.!   │
  │   │   (sopra / Y12..52)  │            │         │ [ESP32-S3]     │ 63 mm
  │   ╰──────────────────╯   │            │         │ [63 × 22mm]    │
  │   ┌──────────────────┐   │            │         │                │
  │   │ ESP32-S3 (25×22) │   │            │         └────[USB-C]─────│ 10 mm
  │   └──────────────────┘   │ Retro      └──────────────────────────┘
  └──────────────────────────┘            Altezza interna richiesta >= 93 mm -> H_est >= 105.6 mm!
```

- **Analisi geometrica:** Con `ESP32-S3` centrato lungo la parete posteriore (`Y = 42..64 mm`), lo speaker `Ø 40 mm` centrato sul tetto (`Y = 12..52 mm`) **collide in pianta** (`10 mm` di interferenza su Y) se si scende sotto `105,6 mm` di altezza esterna. Per evitare la collisione bisognerebbe impilare verticalmente `23 mm` (speaker) + `63 mm` (ESP32) + `10 mm` (USB-C/base) = **`96 mm` interni → `108,8 mm` esterni**, tornando a una torre alta fuori obiettivo.
- **Esito:** **SCARTATO** (viola compattezza o crea interferenza meccanica).

---

## 3. Layout B — ESP32-S3 Orizzontale

```text
  PIANTA (64 × 64 mm)                     SEZIONE LATERALE (H_est = 89.6–96.0 mm)
  ┌──────────────────────────┐            ┌──────────────────────────┐
  │     [OLED 1.3" 36mm]     │ Fronte     │  [Griglia] [Speaker Ø40] │ 22 mm
  ├──────────────────────────┤            ├──────────────────────────┤
  │  ┌────────────────────┐  │            │  [OLED 34mm]  [Cavi]     │
  │  │  ESP32-S3 (63mm!)  │  │            │  [MAX98357A]  [INMP441]  │ 34 mm
  │  │  (25.4 × 22 mm)    │  │            ├──────────────────────────┤
  │  └────────────────────┘  │            │  [ESP32-S3 orizz. 22mm]  │ 22 mm
  │  0.5mm gap per lato!     │ Retro      │  [USB-C bloccata da muro]│ 10 mm
  └──────────────────────────┘            └──────────────────────────┘
```

- **Analisi geometrica:**
  - `ESP32-S3` è lunga **`63,0 mm`** contro un vano interno di **`64,0 mm`**.
  - Disposta trasversalmente (`X`): restano **`0,5 mm` per lato** — tolleranza insufficiente per montaggio reale, nessuna possibilità di inserire un cavo USB-C laterale senza forare e indebolire un'intera colonna portante, e antenna Wi-Fi premuta contro la parete laterale.
  - Disposta longitudinalmente (`Y`): occupa `63 mm` su `64 mm`, entrando in conflitto con il retro dell'OLED / connettore `JST-XH` inferiore e bloccando la slitta di estrazione.
  - Inoltre l'ESP32-S3 sdraiata sul fondo copre l'umbilical port `JST-XH` verso B1/B2 e ostacola l'accesso al regolatore `SGM2212`.
- **Esito:** **SCARTATO** (non montabile né manutenibile comodamente dentro `64 × 64 mm`).

---

## 4. Layout C — ESP32-S3 Verticale Decentrato (RACCOMANDATO)

```text
  PIANTA ZONA SUPERIORE / MEDIA (64 × 64 mm)         SEZIONE LATERALE (H_est = 96.0 mm / 10 brick)
  ◄──────────── 64 mm (8 stud) ────────────►         ┌────────────────────────────────────────┐
  ┌────────────────────────────────────────┐ ▲       │ [Griglia Tetto Removibile]   (3.2 mm)  │
  │  [OLED 1.3" incassato in fronte 8mm]   │ │       │  ┌─────────────────┐  [Ant.WiFi↑]     │
  ├───────────────────────┬────────────────┤ │       │  │ Speaker Ø40×20  │  [ESP32-S3]     │
  │   ╭───────────────╮   │                │ │       │  │ (centro 22,26)  │  [Verticale]    │
  │   │ Speaker Ø40mm │   │ [INMP441] ant. │ │64mm   │  └────────┬────────┘  [63×25.4×22]    │
  │   │ centro (22,26)│   │ [ESP32-S3]     │ │       │ [OLED 1.3"]  │        [SGM2212◄─Retro]│
  │   │ r = 20 mm     │   │ post-DX        │ │       │ [36×34×11mm] │        [USB-C ↓]       │
  │   ╰───────────────╯   │ X=38..63.4     │ │       │  [MAX98357A + C1/C2]  [Breakout USB]  │
  │  [MAX98357A] (basso)  │ Y=42..64       │ ▼       ├────────────────────────────────────────┤
  └───────────────────────┴────────────────┘         │  Interfaccia 8×8 + JST-XH   (9.6 mm)   │
  Distanza centro speaker (22,26) ↔ angolo ESP32 (38,42) = √(16²+16²) = 22,6 mm > 20,0 mm!
```

- **Verifica matematica di non interferenza (`Layout C`):**
  - `ESP32-S3` ruotato di 90° su una parete angolare posteriore-destra (`X = 38,0..63,4 mm`, `Y = 42,0..64,0 mm`, `Z_cav = 6,4..69,4 mm` su `83,2 mm` netti):
    - **Antenna Wi-Fi** in alto nell'angolo posteriore-destro (`Z_abs ≈ 72..79 mm`), lontana da magnete speaker, PCB OLED e parti metalliche.
    - **Regolatore `SGM2212`** rivolto verso lo sportello posteriore apribile (`accesso diretto` per misura termica).
    - **Porta USB-C** in basso a `6,4 mm` dal fondo interno, accessibile aprendo lo sportello posteriore ed estraendo leggermente la slitta `Technic` (o con cavo `USB-C 90°`).
  - **Speaker sul tetto (`Ø 40 × 20 mm`):** centrato leggermente verso il quadrante anteriore-sinistro (`X = 22 mm`, `Y = 26 mm` nel vano `64×64`, ossia `2 mm` a sinistra e `6 mm` in avanti rispetto al centro geometrico):
    - Raggio speaker = `20,0 mm`. Distanza minima dall'angolo ingombro `ESP32-S3` (`X=38, Y=42`) = **`22,6 mm`** → **`2,6 mm` di luce radiale anche nella zona di sovrapposizione verticale** (`Z_cav = 63..69 mm`, soli `6 mm`), che diventano **`> 6 mm`** con speaker `Ø 36 mm`!
    - Sotto lo speaker (`Z_cav = 0..61 mm`) restano liberi i volumi per **OLED frontale** (incassato parzialmente nella parete `8 mm`, sporgenza interna `~6 mm`) e **`MAX98357A` + `C1/C2`** sul fondo sinistro (`X = 2..24 mm`).
  - **Microfono `INMP441`:** collocato nell'angolo anteriore-destro alto (oppure fianco sinistro alto), separato dalla camera speaker.
  - **Pulsante `GPIO 47`:** sul fianco destro o sinistro, con accesso comodo.
  - **Ventilazione passiva:** camino verticale libero dietro la zona centrale-posteriore (`Y = 36..64 mm` lato sinistro) da feritoie basse fino al bordo posteriore del tetto.

---

## 5. Matrice Comparativa Sintetica

| Criterio | Layout A (Vert. centrato) | Layout B (Orizzontale) | **Layout C (Vert. decentrato)** |
|---|---|---|---|
| Altezza minima realistica (con `Ø 40×20`) | `~108,8 mm` *(fuori target)* | `~92,8 mm` | **`96,0 mm`** *(10 brick — in target)* |
| Tolleranze di montaggio | Scarse (collide in Y) | Critiche (`0,5 mm` in X) | **Buone (`≥ 2,6 mm` radiali)** |
| Accesso USB-C e `SGM2212` | Medio | Scarso (bloccato sotto) | **Ottimo (da sportello post.)** |
| Posizione Antenna Wi-Fi | Coperta parzialmente | Contro parete/fondo | **Libera in angolo superiore** |
| Cablaggi e manutenzione | Stretti | Molto difficili | **Ordinati per zone separate** |
| **Scelta FASE A** | Scartato | Scartato | **RACCOMANDATO** |
