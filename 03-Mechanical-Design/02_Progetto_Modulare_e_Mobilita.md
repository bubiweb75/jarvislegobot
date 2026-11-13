# Elaborato B – Interfaccia Universale, Base Fissa B1, Base Mobile B2 e Collegamento JST-XH

**Dimensioni mantenute:** Modulo A `10×10 stud` (`8×8×14,4 cm`), B1 `12×11 stud` (`9,6×8,8 cm`), B2 `16×15 stud` (`12,8×12×4,5 cm`), Interfaccia `8×8 stud` (`6,4×6,4 cm`).

---

## 6. Vista Esplosa Modulare (Modulo A + B1 + B2)

```text
          ┌───────────────────────────────────────┐
          │         MODULO A (10 × 10 stud)       │
          │     Corpo Monoblocco Removibile       │
          └──────┬─────────────────────────┬──────┘
                 │  Interfaccia 8×8 stud   │
                 ▼  + Umbilical 2×4 stud   ▼
       ====[6558]╬═════════════════════════╬[6558]====  <- 4× Pin 6558 (3L)
                 │   [JST-XH 6 pin]        │               (2 sx, 2 dx)
        ┌────────▼────────┐       ┌────────▼──────────────────┐
        │   MODULO B1     │       │        MODULO B2          │
        │  Base Fissa     │  ==>  │  Base Mobile (16×15 stud) │
        │  12 × 11 stud   │       │  2 Ruote Motrici + Caster │
        │  (Scrivania)    │       │  Batteria+TB6612+Buck 5V  │
        └─────────────────┘       └───────────────────────────┘
```

---

## 7. Interfaccia Universale (`8 × 8 stud` = `64 × 64 mm`) e Sistema di Fissaggio

```text
         PIANTA INTERFACCIA SUPERIORE SU B1 / B2 (8 × 8 stud = 64 × 64 mm)

                 ◄────────── 64 mm (8 stud) ──────────►
              ▲  ┌────┬──────────────────────────┬────┐
              │  │ T1 │   Technic Brick 1×8      │ T2 │  T1..T4: 4 torrette di
              │  ├────┘                          └────┤  centraggio angolari
         64mm │  │        ┌──────────────────┐        │  (alte 1 brick = 9,6mm)
        (8st) │  │ [Foro] │ UMBILICAL PORT   │ [Foro] │
              │  │ [Pin1] │   2 × 4 stud     │ [Pin3] │  Pin1..Pin4: 4× LEGO
              │  │        │  (16 × 32 mm)    │        │  6558 (Pin 3L con friz.)
              │  │ [Foro] └──────────────────┘ [Foro] │  inseriti da sx e dx
              │  │ [Pin2]                      [Pin4] │
              │  ├────┐                          ┌────┤
              ▼  │ T3 │   Technic Brick 1×8      │ T4 │
                 └────┴──────────────────────────┴────┘
```

### Dettaglio Meccanico dei 4 Pin Technic 3L
- **Componente esatto (`csv/parts.csv`):** **4× `6558` – *Technic Pin Long with Friction Ridges Lengthwise, 2 Center Slots* (3L, Blu)**.
  - *Alternativa manuale più rapida:* `6587` (*Technic Axle 3 with Stud*) + `3713` (*Technic Bush*) se si desidera uno sfilamento ancora più agevole con le dita.
- **Inserimento e rimozione:** I 4 pin vengono inseriti orizzontalmente dall'esterno (2 sul lato sinistro, 2 sul lato destro) attraversando `1 stud` della parete della base B1/B2 e `2 stud` del telaio inferiore del Modulo A.
- **Sistema anti-sgancio e distribuzione sforzi:**
  - Le **4 torrette angolari (`T1–T4`, alte `9,6 mm`)** assorbono tutti gli sforzi laterali (X/Y) e di torsione, impedendo oscillazioni.
  - I 4 pin `6558` lavorano **esclusivamente a taglio** lungo l'asse verticale Z, trattenuti dalle nervature di frizione (*friction ridges*).
  - **Verifica fisica obbligatoria:** La tenuta reale alle vibrazioni e ai micro-urti su pavimento deve essere verificata sperimentalmente sul prototipo B2 prima di autorizzare il movimento autonomo.

---

## 8. Collegamento Elettrico A ↔ B2: Connettore JST-XH 6 Pin

- **Posizione e fissaggio:** Attraverso l'`Umbilical Port` (`2 × 4 stud` = `16 × 32 mm`) sul pavimento del Modulo A. Connettore **JST-XH 2.54 mm a 6 pin polarizzato meccanicamente** (chiavetta anti-inversione), con cavi fissati tramite fascetta anti-trazione sulla slitta interna.
- **DIVIETO HOT-PLUG:** Il JST-XH **NON è un connettore hot-plug**. Collegare e scollegare **sempre** ad alimentazione completamente spenta (interruttore B2 OFF e cavo USB-C scollegato).

| Pin | Segnale | Direzione | Tensione | Funzione |
|---|---|---|---|---|
| **1** | `+5V_B2` | B2 → A | **5,0 V DC** | Alimentazione dal regolatore DC-DC Buck 5 V di B2 verso il nodo `5V` del Modulo A (`J1-21` + `MAX98357A VIN`). Protetto su B2 con **fusibile PTC 2 A** + **anti-inversione** (MOSFET P-channel o diodo Schottky). In B1 questo pin resta scollegato. |
| **2** | `GND` | Comune | **0 V** | Massa di riferimento comune tra B2 e Modulo A. |
| **3** | `UART_TX_MOT` (**`GPIO 17`**) | A → B2 | **3,3 V** | Segnale logico seriale TX (comandi velocità/direzione verso il controller/driver motori su B2) con resistore serie `1 kΩ`. **Non pilota direttamente i motori.** |
| **4** | `UART_RX_MOT` (**`GPIO 18`**) | B2 → A | **3,3 V** | Segnale logico seriale RX (telemetria batteria/stato driver da B2) con resistore serie `1 kΩ`. |
| **5** | `I2C_EXT_SDA` (**`GPIO 8`**) | Bidir. | **3,3 V** | Bus I2C dedicato ai sensori anticollisione su B2 (es. ToF VL53L0X), **separato** dal bus `GPIO 41/42` dell'OLED. |
| **6** | `I2C_EXT_SCL` (**`GPIO 9`**) | A → B2 | **3,3 V** | Clock I2C dedicato ai sensori su B2. |

- **Verifica compatibilità GPIO `17, 18, 8, 9`:** Confermati tutti e 4 come GPIO digitali puliti a 3,3 V su ESP32-S3-DevKitC-1 N16R8 (nessun conflitto con strapping `0/3/45/46`, PSRAM Octal `35–37`, USB `19–20`, UART0 `43–44`, audio o OLED).
- **Separazione alimentazione motori / elettronica:** I motori DC sono alimentati **direttamente dalla batteria (es. 7,4 V 2S)** tramite il driver `TB6612FNG` su B2, **mai** dal rail `5 V` dell'ESP32-S3/audio.
- **Procedura di collegamento:** (1) Spegnere interruttore B2 e scollegare eventuali cavi USB-C su A; (2) Inserire il connettore JST-XH 6 pin fino al click; (3) Posare Modulo A su B2 e inserire i 4 pin `6558`; (4) Accendere interruttore B2.

---

## 9. Base Mobile 2WD + Caster – Modulo B2 (`16 × 15 stud` = `12,8 × 12,0 cm`, h `4,5 cm`)

Configurazione tassativa: **2 ruote motrici indipendenti laterali + 1 ruota libera caster** (sterzata differenziale).

```text
         PIANTA QUOTATA MODULO B2 (16 × 15 stud = 128 × 120 mm, h ≈ 45 mm)

                          ◄─────── 128 mm (16 stud) ───────►
                       ▲  ┌────────────────────────────────┐
     Sensore           │  │    [Allogg. Sensore ToF Ant.]  │
     Anticollisione ───┼──┤   ┌────────────────────────┐   │
     (es. VL53L0X)     │  │   │  Interfaccia 8×8 stud  │   │
                  ┌──┐ │  │   │  + Umbilical Port 2×4  │   │  ┌──┐
    Ruota Mot. SX │  ├─┼──┼───┤ [Motorid. N20] [N20]   ├───┼──┤  │ Ruota Mot. DX
    Ø 43–50 mm    │  │ │  │   │  (24×12×10mm)          │   │  │  │ Ø 43–50 mm
    Largh. 14–22mm└──┘ │  │   ├────────────────────────┤   │  └──┘ Largh. 14–22mm
                  120mm│  │   │ [TB6612FNG] [Buck 5V]  │   │
                 (15st)│  │   │ [Vano Batteria 2S]     │   │  <- Fondo ribassato
                       │  │   │ [Interruttore + Fusib.]│   │     (baricentro basso)
                       ▼  │   └───────────(O)──────────┘   │
                          └─────────────[CASTER]───────────┘
                                  Ruota libera Ø 15–20mm
```

### Stima Ragionata di Massa, Coppia e Dimensionamento Componenti B2
- **Stima masse (analitica, da verificare su bilancia a prototipo montato):**
  - Modulo A completo: ~300–400 g.
  - Modulo B2 (telaio Technic + 2 motori + ruote + caster + batteria 2S + schede): ~350–450 g.
  - **Massa totale di progetto (con margine cautelativo):** **`1,0 kg`** ($F_g \approx 9,81\,\text{N}$).
- **Scelta ruote e geometria:**
  - **2× Ruote motrici:** diametro **`43–50 mm`**, larghezza **`14–22 mm`**, asse motori posizionato leggermente arretrato/centrato sotto il baricentro del Modulo A (l'altezza da terra ~10–12 mm porta l'altezza totale della base a `~45 mm`).
  - **1× Ruota caster:** Ø `15–20 mm` al posteriore centrale, per appoggio stabile su 3 punti.
- **Calcolo coppia necessaria per motoriduttore:**
  - Con $m = 1,0\,\text{kg}$, raggio ruota $r = 0,022\,\text{m}$ (Ø 44 mm) e coefficiente di resistenza/accelerazione combinato $\mu_{eff} = 0,25$: forza totale $F \approx 2,5\,\text{N}$ ($\sim 1,25\,\text{N}$ per ruota).
  - Coppia operativa per ruota: $\tau_{op} = 1,25\,\text{N} \times 0,022\,\text{m} \approx 0,0275\,\text{N}\cdot\text{m} \approx \mathbf{0,28\,\text{kg}\cdot\text{cm}}$.
  - Applicando fattore di sicurezza **`3×`** (attrito su tappeto/curve sul posto): coppia nominale richiesta **$\ge 0,85\text{–}1,0\,\text{kg}\cdot\text{cm}$** per motore.
- **Componenti elettrici/meccanici previsti per B2:**
  - **Motoriduttori:** 2× **Micro-motoriduttori metallici N20** (`6 V`, ~`100–150 RPM`, ingombro `~24 × 12 × 10 mm`, coppia tipica 1,0–1,6 kg·cm, corrente stallo ~0,8–1,2 A).
  - **Driver motori:** 1× **`TB6612FNG`** (`1,2 A` continui / `3,2 A` picco per canale, alimentazione motori separata da batteria).
  - **Regolatore DC-DC:** 1× **Modulo Buck 5 V / ≥ 3 A** (es. basato su MP1584 / TPS5430 / XL4015 compatto) per alimentare il Modulo A via JST-XH Pin 1–2.
  - **Batteria:** Pacco **2S Li-Ion protetto (7,4 V nominali, BMS integrato)** nel vano inferiore centrale per mantenere il baricentro basso.
  - **Protezioni B2:** Interruttore generale a slitta/bilanciere + Fusibile principale `3–5 A` su batteria + PTC `2 A` e anti-inversione su linea `+5V_B2`.
