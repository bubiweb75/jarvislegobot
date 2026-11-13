# Elaborato D – Distinta Costruttiva Verificata (CSV) e Matrice Verifiche

**Fonte catalogo LEGO verificata:** `csv/parts.csv` e `csv/colors.csv` presenti nel repository.  
*(Non vengono inventati codici pezzo; sono indicate le quantità stimate e le alternative costruttive nel caso alcuni formati mancassero dalla collezione fisica).*

---

## 16. Elenco Pezzi LEGO Technic (`csv/parts.csv` – Modulo A + Modulo B1)

| `part_num` (CSV) | Nome Ufficiale (`csv/parts.csv`) | Colore Consigliato (`csv/colors.csv`) | Qtà Stimata | Funzione | Alternative Costruttive |
|---|---|---|---|---|---|
| **`3702`** | Technic Brick 1 x 8 [7 Pin Holes] | Dark Bluish Gray (`72`) | 4–6 | Pareti interfaccia `8×8` (Modulo A e B1) | 2× `3701` (1×4) bloccati con *Plate* |
| **`2730`** | Technic Brick 1 x 10 [9 Pin Holes] | Dark Bluish Gray (`72`) / Black (`0`) | 4 | Cornice esterna Base B1 / telaio | `3894` (1×6) + `3701` (1×4) |
| **`3895`** | Technic Brick 1 x 12 [11 Pin Holes] | Dark Bluish Gray (`72`) | 2 | Lati lunghi Base B1 (`12×11`) | `3894` (1×6) × 2 |
| **`3700`** | Technic Brick 1 x 2 [1 Pin Hole] | Black (`0`) / Dark Bluish Gray (`72`) | 4–6 | Foro acustico mic INMP441 + torrette `T1–T4` | `3701` (1×4) |
| **`32316` / `32524`** | Technic Beam 1 x 5 / 1 x 7 Thick | Dark Bluish Gray (`72`) | 4 | Slitta estraibile ESP32-S3 e traverse B1 | *Plate 2×N* in doppio strato |
| **`6558`** | Technic Pin Long with Friction Ridges (3L) | Blue (`1`) | **4** | **Pin di aggancio rapido Modulo A ↔ B1/B2** | `6587` (*Axle 3 with Stud*) + `3713` (*Bush*) |
| **`2780`** | Technic Pin with Friction Ridges | Black (`0`) | 8–12 | Bloccaggio telaio interno e slitta | Assali corti + `3713` (*Bush*) |
| **`3673`** | Technic Pin without Friction Ridges | Light Bluish Gray (`71`) | 4 | Fissaggio rapido sportello posteriore | `3937` + `3938` (cerniera 1×2) |

---

## 17. Elenco Mattoncini LEGO Classici (`csv/parts.csv` – Modulo A + Modulo B1)

| `part_num` (CSV) | Nome Ufficiale (`csv/parts.csv`) | Colori (`csv/colors.csv`) | Qtà Stimata | Funzione |
|---|---|---|---|---|
| **`3004` / `3010` / `3005`** | Brick 1×2 / 1×4 / 1×1 | Black (`0`), Dark Bluish Gray (`72`) | 35–48 | Pareti compatte `10×10 stud` Modulo A |
| **`3020` / `3021` / `3022` / `3023` / `3795` / `3036`** | Plate 2×4 / 2×3 / 2×2 / 1×2 / 2×6 / 6×8 | Black (`0`), Dark Bluish Gray (`72`) | 20–28 | Base B1, setto acustico, chiusura superiore, sportello `6×10` (`3036` + `3020`) |
| **`3040b` / `3039` / `54200`** | Slope 45° 2×1 / 2×2 / Cheese Slope 30° 1×1 | Black (`0`) | 6–12 | Calotta superiore rastremata e profilo visiera |
| **`3069b` / `2431` / `3070b`** | Tile 1×2 / 1×4 / 1×1 with Groove | Black (`0`), Dark Bluish Gray (`72`) | 8–14 | Cornice visiera OLED e finiture lisce |
| **`2412b`** | Tile Special 1 x 2 Grille with Bottom Groove | Dark Bluish Gray (`72`), Black (`0`) | 8–12 | Griglia speaker frontale e feritoie ventilazione |
| **`3023` / `3024` / `3069b`** | Plate / Tile di accento | Medium Azure (`322`) o Trans-Light Blue (`41`) | 8–12 | Dettagli luminosi/futuristici laterali e cornice speaker |
| **`98138` / `4150`** | Tile Round 1×1 / 2×2 | Medium Azure (`322`) / Trans-Light Blue (`41`) | 1 | Cappuccio pulsante fisico `GPIO 47` |

---

## 18. Elementi di Fissaggio, Connettori e Materiali (Non LEGO)

- **Connettore JST-XH 6 pin (2,54 mm) polarizzato:** 1 coppia M/F con cavi `22 AWG` (pin 1–2) e `26 AWG` (pin 3–6) per `Umbilical Port`.
- **Gommapiuma acustica (3–5 mm):** 2–3 ritagli (anello INMP441, battuta speaker/OLED, lato inferiore setto acustico lontano da ESP32).
- **Elastici piccoli / fascette nylon:** 2–4 per fissaggio rimovibile slitta ESP32-S3 / cavi.

---

## 19. Supporti 3D (Solo Opzionali) e 20. Alternative Costruttive

- **Supporti 3D:** Non necessari. Opzionali: cornice OLED inclinata 15° e anello speaker Ø 40 mm.
- **Alternative LEGO:** `3937`+`3938` (Hinge 1×2) per inclinare l'OLED (oppure OLED verticale dietro *Slope 45°*); `3701`+`3894` al posto di `2730`/`3895`; `3700` aperti al posto di `2412b` Grille.

---

## 21. Distinta Componenti Futura Base Mobile B2 (Pianificazione – NO Acquisti)

- 2× **Micro-motoriduttori metallici N20** (`6 V`, ~100–150 RPM, coppia ≥ `0,85–1,0 kg·cm`, `~24×12×10 mm`).
- 2× **Ruote motrici gommate** (`Ø 43–50 mm`, larghezza `14–22 mm`) + 1× **Ruota libera Caster** (`Ø 15–20 mm`).
- 1× **Driver motori `TB6612FNG`** (`1,2 A` cont. / `3,2 A` picco/ch, logica 3,3 V).
- 1× **Regolatore DC-DC Buck 5 V / ≥ 3 A** (dedicato al Modulo A).
- 1× **Pacco batteria 2S Li-Ion protetto (7,4 V con BMS)** + **Interruttore generale** + **Fusibile 3–5 A** + **PTC 2 A** (su `+5V_B2`).
- 1× **Sensore anticollisione I2C** (es. VL53L0X) su `GPIO 8/9` + **Lotto LEGO Technic B2** (`16×15 stud`).

---

## 22. Matrice Verifiche Obbligatorie (Documentali vs Dimensionali vs Da Eseguire)

| # | Verifica | Categoria | Stato | Esito e Note |
|---|---|---|---|---|
| **1** | Coerenza dimensioni tra disegni e documenti | **Documentale** | ✅ Verificato | `10×10`, `12×11`, `16×15`, `8×8 stud` coerenti in tutti i file. |
| **2** | Compatibilità vano `64×64×128 mm` con connettori | **Dimensionale** | ✅ Verificato con vincolo | Richiede **connettori low-profile** su ESP32 (`19–21 mm` gap da speaker) e cavo USB-C 90° o estrazione slitta in Modalità B. |
| **3** | Collegamento elettrico JST-XH 6 pin & GPIO `17,18,8,9` | **Documentale** | ✅ Verificato | GPIO puliti, nessun pilotaggio diretto motori, separazione rail motori/5 V, divieto hot-plug documentato. |
| **4** | Stabilità statica Base Fissa B1 | **Dimensionale** | ✅ Verificato | Impronta `96×88 mm` > corpo `80×80 mm`, h `16,3 cm`. |
| **5** | Trasferibilità A ↔ B2 e compatibilità 2WD + Caster | **Documentale / Dimensionale** | ✅ Verificato | Interfaccia `8×8` identica; calcolo coppia N20 (~`0,28 kg·cm` op., ≥ `0,85–1,0 kg·cm` con FS 3×). |
| **6** | Codici pezzi e colori LEGO | **Documentale (`csv/`)** | ✅ Verificato | Tutti i `part_num` e `color_id` verificati in `csv/parts.csv` e `csv/colors.csv`. |
| **7** | Tenuta meccanica 4 Pin `6558` sotto vibrazioni | **Prova Fisica** | ⏳ **Non eseguita** | Da testare fisicamente sul prototipo B2 prima di autorizzare il movimento. |
| **8** | Massa reale Modulo A e baricentro effettivo | **Prova Fisica** | ⏳ **Non eseguita** | Da pesare a Modulo A assemblato prima di acquistare i motori di B2. |
| **9** | Stress termico `SGM2212` e rientro acustico in `64×64×128 mm` | **Prova Fisica** | ⏳ **Non eseguita** | Test termico continuo e prova eco audio obbligatori in FASE 4. |
