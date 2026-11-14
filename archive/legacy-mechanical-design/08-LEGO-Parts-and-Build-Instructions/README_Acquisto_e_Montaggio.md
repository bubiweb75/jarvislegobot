# JARVIS LEGO BOT — Distinta LEGO, Acquisto e Istruzioni Preliminari

> [!WARNING]
> **Avvertenza importante:**
> - Il robot **non è ancora stato costruito fisicamente**: la costruibilità reale e il comportamento degli incastri non sono dichiarati verificati sulla sola base del modello digitale `jarvis_lego_bot_mini_cube.mpd`.
> - **`13` pezzi su `137`** (elencati alla Sezione 4) sono contrassegnati come **PROVVISORI** perché potrebbero cambiare al **Passaggio B dell'integrazione OLED (Soluzione 2B)**. Attendi la prova in cartoncino prima di ordinare quei 13 pezzi.

---

## 1. File Presenti in Questa Cartella

- **[LEGO_BOM_Completa.csv](LEGO_BOM_Completa.csv):** Distinta unificata (`35` tipologie codice+colore, `137` pezzi totali) con codici BrickLink, `Element ID` LEGO, colori BrickLink, suddivisione A/B1 e stato provvisorio.
- **[LEGO_BOM_Per_Modulo.csv](LEGO_BOM_Per_Modulo.csv):** Distinta separata per **Modulo A** (`115` pezzi) e **Modulo B1** (`22` pezzi); base mobile **B2 esclusa**.
- **[BrickLink_Wanted_List.xml](BrickLink_Wanted_List.xml):** File XML pronto per l'importazione diretta in **BrickLink → Want → Upload → Upload BrickLink XML format** (con colori BrickLink verificati `11`, `85`, `156` e note sui pezzi provvisori).
- **[LEGO_Inventario_Stampabile.pdf](LEGO_Inventario_Stampabile.pdf):** Inventario A4 stampabile (`2` pagine) con caselle **Ho / Manca / OK** per fare spunta dei pezzi già posseduti.
- **[Istruzioni_Montaggio_Preliminari.pdf](Istruzioni_Montaggio_Preliminari.pdf):** Sequenza preliminare illustrata passo-passo (`3` pagine A4) generata direttamente dalle coordinate del modello MPD.

---

## 2. Riepilogo Quantità e Colori (Coerenza `137` Parti Verificata)

Estrazione diretta dal file `03-Mechanical-Design/07-Mini-Cube-Redesign/jarvis_lego_bot_mini_cube.mpd` (`main.ldr` istanzia `1× modulo_a_mini.ldr` e `1× modulo_b1_mini.ldr`, senza duplicazioni):

| Modulo | Numero Pezzi | Tipologie differenti |
|---|---:|---:|
| **Modulo A** (Corpo removibile) | `115` | `30` |
| **Modulo B1** (Base fissa `12×12` stud) | `22` | `9` |
| **Totale (A + B1)** | **`137`** | **`35`** (unificate) |

**Ripartizione per colore BrickLink:**
- **Black** (BrickLink ID `11`, LDraw `0`): **`112` pezzi**
- **Dark Bluish Gray** (BrickLink ID `85`, LDraw `72`): **`22` pezzi**
- **Medium Azure** (BrickLink ID `156`, LDraw `322`): **`3` pezzi**

---

## 3. Parti Provvisorie da Confermare Prima dell'Acquisto (`13` pezzi in Modulo A)

Se nel **Passaggio B della FASE D** verrà adottata definitivamente la **Soluzione 2B** (tasca frontale `48,0 × 41,6 mm` per l'inserto cornice 3D), i seguenti **`13` pezzi** del modello attuale verranno sostituiti o rimossi:

| Codice | Colore BrickLink | Qtà provvisoria (su tot. A) | Motivo della possibile variazione in Passaggio B |
|---|---|---:|---|
| `3622` | Black (`11`) | **`8`** (su `9`) | Spalle OLED `L3..L6`: sostituibili da `8× 3004` (`Brick 1×2` Black) per allargare la tasca a `6` stud (`48 mm`). Il 9° pezzo (fianco DX L8 mic) resta confermato. |
| `3710` | Dark Bluish Gray (`85`) | **`2`** (su `2`) | Base davanzale OLED `L3`: rimossi se si adotta la cornice 3D 2B. |
| `2431` | Dark Bluish Gray (`85`) | **`1`** (su `1` in A; `2` in B1) | Davanzale liscio OLED `L3`: rimosso in Modulo A con la cornice 2B (i `2` pezzi in B1 restano confermati). |
| `3010` | Dark Bluish Gray (`85`) | **`1`** (su `1`) | Architrave OLED `L6`: rimosso se si adotta la cornice 3D 2B. |
| `3009` | Black (`11`) | **`1`** (su `2`) | Centro mento `L2`: sostituibile da `2× 3666` (`Plate 1×6` Black) per ricavare lo scarico inferiore del flex OLED. Il 2° pezzo (fianco SX L3) resta confermato. |

---

## 4. Distinzione Componenti NON LEGO (Esclusi da Questa Distinta)

- **Supporti stampabili in 3D (prototipo non validato):** Cornice frontale 2B + Culla posteriore regolabile (`01-OLED-Support-Prototype/`).
- **Display OLED:** Modulo Binghe `1,3"` (`SH1106`/`SSD1106` da confermare) + `4` fili I²C.
- **Elettronica:** `ESP32-S3`, speaker `PUI Audio AS03604AR`, `MAX98357A`, microfono `INMP441`, pulsante laterale `GPIO 47`, breakout `USB-C 5V`, connettore `JST-XH`.
- **Futura Base Mobile B2:** Esclusa da questa distinta.
