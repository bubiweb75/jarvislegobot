# Elaborato C – Ingombri Interni (`64 × 64 × 128 mm`), Cablaggi e Raffreddamento

**Vincolo:** Nessuna modifica a schema elettrico, pinout FASE 2 (`GPIO 4/5/6`, `7/15/16`, `41/42`, `47`; `GPIO 39/40` disabilitati; `GPIO 35–37` PSRAM) e LDO `SGM2212` onboard.

---

## 11. Pianta Quotata e Sezione del Vano Interno (`64 × 64 × 128 mm`)

```text
   PIANTA ZONA INFERIORE (64 × 64 mm interni)       SEZIONE LATERALE (64 × 128 mm interni)
   ◄────────── 64 mm (8 stud) ──────────►          ┌──────────────────────────────────┐
   ┌────────────────────────────────────┐ ▲        │  [•] INMP441 (Ø14)               │
   │  [PARETE FRONTALE - GRIGLIA]       │ │        │  / OLED 1.3" \   [Zona Antenna   │ Z_sup
   │   ┌─────────────────┐  ┌────────┐  │ │ 20mm   │  \ (~15°)    /    Wi-Fi Libera!] │ ~48mm
   │   │ Speaker Ø40mm   │  │MAX98357│  │ │(Spk)   │──────────────────┐               │
   │   │ (spess. ~20mm)  │  │19×18mm │  │ ▼        │ SETTO ACUSTICO   │ [Canale Aria  │ 6.4mm
   │   └────────┬────────┘  └────────┘  │          │ (Plate+Spugna)   │  Retro 22mm]  │
   │            │  GAP ~19–21 mm        │          │──────────────────┘               │
   │            ▼  (con connettori      │ 64mm     │  (BTN) GPIO 47    ┌────────────┐ │
   │     ┌───────────────────┐  low-prf)│(8st)     │  ┌─────────────┐  │ ESP32-S3   │ │ Z_inf
   │     │ ESP32-S3-DevKitC  │          │ │        │  │ Speaker     │19│ [SGM2212]◄─┼─┼─ Retro
   │     │ (25.4 × 13 mm)    │ [Breakout│ │        │  │ Ø40×20mm    │mm│ (63×25.4)  │ │ ~74mm
   │     │ + connett. ~10mm  │  USB-C]  │ │        │  │             │  │ [USB-C]    │ │
   │     └───────────────────┘          │ ▼        │  └─────────────┘  └─────┬──────┘ │
   └───────[SPORTELLO POSTERIORE]───────┘          │  [MAX98357A] [Breakout] │ ~11mm  │
                                                   └──────┬──────────────────┴────────┘
                                                          │  Umbilical Port (2×4 stud)
```

### Verifica Reale con Connettori, Cavi, Supporti e Manutenzione
1. **Distanziamento Speaker ↔ ESP32-S3 (`64,0 mm` su asse Y):**
   - Speaker Ø `36–40 mm` (profondità `18–20 mm` + `2 mm` guarnizione) = **`20–22 mm`**.
   - ESP32-S3-DevKitC-1 (`13 mm` spessore con pin header) + **connettori DuPont dritti standard (`~20 mm` con curva filo)** = `33 mm` → `22 + 33 = 55 mm` (resterebbero solo **`9 mm`**, troppo stretti per manutenzione comoda).
   - **Soluzione obbligatoria per mantenere `64 mm`:** utilizzare **connettori a profilo basso** (header a **90°** oppure connettori DuPont corti/cavi saldati con guaina termorestringente, sporgenza `~8–10 mm`) → ingombro ESP32+cavi = **`21–23 mm`** → **restano `19–21 mm` di gap netto** tra i pin ESP32 e il magnete dello speaker!
2. **Accessibilità Porta USB-C (Modalità B – Programmazione/Debug da PC):**
   - La DevKitC-1 (`63 mm` in Z) è montata **verticalmente su slitta estraibile** nella zona inferiore (`~74 mm` utili in Z), sollevata di **`~11 mm`** dal pavimento.
   - Con un cavo USB-C dritto ci vorrebbero ~25 mm sotto la scheda; pertanto in **Modalità B (Debug PC)** si apre lo **sportello posteriore `6×10 stud`**, si sfila leggermente la slitta verso l'esterno (grazie ai `~3 cm` di ricchezza dei cavi) e si collega il cavo USB-C comodamente (oppure si usa un **cavo USB-C a 90°**). In **Modalità A (uso autonomo)**, l'alimentazione entra esclusivamente dal **Breakout USB-C 5 V** basso-posteriore verso `J1-21` (`5V`).
3. **Supporti e fissaggio senza colla:** Slitta interna in *Technic Beam* + elastici/fascette rimovibili; speaker e OLED trattenuti da battute LEGO e spessori in gommapiuma.

---

## 12. Percorso Cablaggi e Zona Antenna ESP32

- **Antenna Wi-Fi libera:** La DevKitC-1 è orientata con l'antenna PCB **verso l'alto**, affacciata al vano posteriore superiore libero (`~48 mm` di altezza e `~22 mm` dietro l'OLED), lontana dal magnete dello speaker.
- **Salita cavi I2C/I2S:** I 9 fili `26 AWG` (4 OLED + 5 INMP441) salgono lungo il fianco interno sinistro attraverso la tacca laterale del setto acustico, senza passare davanti all'antenna né sopra l'LDO `SGM2212`.

---

## 13. Acustica, Ventilazione Passiva e Accesso `SGM2212`

- **Separazione acustica:** INMP441 in alto (dietro foro Ø 4,8 mm, avvolto in anello di gommapiuma), Speaker in basso dietro *Grille Tile*, separati dal **setto orizzontale** con fonoassorbente **solo sotto** (lato speaker).
- **Ventilazione passiva:** Il setto si ferma a `~22 mm` (`~2,7 stud`) dalla parete posteriore, lasciando un camino verticale libero dall'ingresso aria inferiore (fianchi bassi + base) fino alle feritoie superiori posteriori (`2412b`).
- **Accesso `SGM2212`:** Aprendo lo sportello posteriore `6×10 stud` (4 pin `3673` senza frizione), l'LDO `SGM2212` sulla faccia superiore della DevKitC-1 è **immediatamente accessibile** per la misura della temperatura durante il collaudo della FASE 4.
