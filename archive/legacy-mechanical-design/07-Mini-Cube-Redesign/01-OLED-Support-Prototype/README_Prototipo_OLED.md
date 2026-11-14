# FASE D — Prototipo Parametrico Supporto OLED Binghe 1,3" (Soluzione 2B)

> [!WARNING]
> **STATO: PROTOTIPO DIMENSIONALE NON VALIDATO.**
> - `jarvis_lego_bot_mini_cube.mpd` **non è stato modificato**.
> - I file STL in `stl_prototipi_non_validati/` sono **prototipi dimensionali non validati**, basati su quote provvisorie ancora da riconciliare sul modulo fisico.
> - La verifica del controller **`SH1106` vs `SSD1106`** resta aperta per la fase firmware.

---

## 1. File Prodotti in Questa Cartella

- **Modello CAD parametrico (OpenSCAD):** [oled_support_parametric.scad](oled_support_parametric.scad) (`part = "bezel" | "cradle" | "assembly"`)
- **Generatore STL & verifica 3D sub-box:** [generate_oled_prototype_assets.py](generate_oled_prototype_assets.py)
- **STL prototipo cornice (non validato):** [PROTOTIPO_NON_VALIDATO_cornice_2B.stl](stl_prototipi_non_validati/PROTOTIPO_NON_VALIDATO_cornice_2B.stl)
- **STL prototipo culla regolabile (non validato):** [PROTOTIPO_NON_VALIDATO_culla_regolabile.stl](stl_prototipi_non_validati/PROTOTIPO_NON_VALIDATO_culla_regolabile.stl)
- **Viste tecniche:**
  - [Vista frontale con occhi OLED 128×64](images/01_vista_frontale_occhi_oled.svg)
  - [Sezione quotata del display installato](images/02_sezione_quotata_display_installato.svg)
  - [Vista esplosa del montaggio](images/03_vista_esplosa_montaggio.svg)

---

## 2. Analisi delle Due Revisioni Dimensionali & Scomposizione `11,30 mm`

| Parametro | Rev. A (disegno tecnico recente) | Rev. B (inserzione precedente) | Gestione nel prototipo |
|---|---:|---:|---|
| **PCB (`L × H`)** | `35,40 × 33,50 mm` | `36,00 × 34,00 mm` | Tasca culla dimensionata su `36,00 + 2×0,25 = 36,50 × 34,50 mm` (con spessori elastici/centraggio morbido per `35,4×33,5`, senza incastri forzati) |
| **Interasse fori** | `30,40 × 28,50 mm` (`Ø 3,00`) | `31,00 mm` (O) | **Non usato per bloccaggio rigido:** finché le due revisioni non saranno riconciliate fisicamente, la PCB è tenuta perimetralmente dalla culla |
| **Offset area attiva** | `7,35 mm` da bordo sup. PCB | Non quotato | Centro area attiva = `14,70 mm` dal top PCB (`2,05..2,30 mm` sopra il centro geometrico PCB) |
| **Quota laterale `11,30 mm`** | `11,30 mm` totali vista laterale | — | **Scomposta parametricamente:** vetro `~1,40 mm` + PCB `~1,60 mm` + sporgenza header/pin `~8,30 mm` (non è lo spessore del solo display!) |

---

## 3. Parametri Esposti in `oled_support_parametric.scad` e Quote Ancora Incerte

| Parametro OpenSCAD | Valore provvisorio | Stato |
|---|---:|---|
| `pcb_w_min` / `pcb_w_max` | `35.40` / `36.00 mm` | **Da riconciliare con calibro** |
| `pcb_h_min` / `pcb_h_max` | `33.50` / `34.00 mm` | **Da riconciliare con calibro** |
| `pcb_thickness` | `1.60 mm` | **Provvisorio (da misurare)** |
| `glass_thickness` | `1.40 mm` | **Provvisorio (da misurare)** |
| `rear_smd_protrusion` | `2.00 mm` | **Provvisorio (da misurare)** |
| `active_top_offset` | `7.35 mm` | Da confermare su display acceso |
| `hole_pitch_x_min/max`, `hole_pitch_y`, `hole_dia` | `30.40/31.00`, `28.50`, `3.00 mm` | **Non ancora riconciliati** |
| `recess_depth`, `glass_relief` | `1.80 mm`, `0.35 mm` | Confermato Soluzione 2B |
| `print_tol_xy`, `print_tol_z`, `slot_travel` | `0.25`, `0.20`, `±2.50 mm` | Tarabile per stampante FDM |
| `header_w`, `header_h`, `header_protrusion` | `14.00`, `7.00`, `8.30 mm` | **Provvisorio (tipo connettore dritto vs 90°)** |

---

## 4. Analisi Interferenze 3D (Sub-Box Reali, `0` Collisioni)

Eseguita verifica 3D per singoli sottovolumi reali (non solo AABB globale) rispetto al Mini Cubo (`80 × 80 × 96 mm`, tasca frontale `48,0 × 41,6 mm` a `Y_h = 25,6..67,2 mm`):
- **Total 3D sub-box hits:** **`0`** (con tasca cornice centrata a `Y_h = 46,4 mm`, offset `-1,60 mm` rispetto alla finestra `48,0 mm`).
- **Speaker `AS03604AR` (`Z = 22..58`):** `8,55 mm` di margine libero davanti allo speaker anche con header/pin da `8,30 mm` (`Z_max = 13,45 mm`).
- **`MAX98357A + C1` (`Z = 20,8..40,8`):** `11,15 mm` di margine libero dietro la culla (`Z_max = 9,65 mm`).
- **`ESP32-S3` Layout C (`Z = 50..71,4`):** `36,55 mm` di margine libero.
- **Accenti frontali `4070 + 3070b` (`Y_h = 19,2..28,8`, `X = 8..16` e `64..72`):** Nessuna interferenza con le flange laterali della cornice (`Y_h = 29,1..63,7 mm`).

---

## 5. Modifiche Necessarie al Modello LEGO (Solo al Futuro Passaggio B)

Per installare la cornice 2B e la culla regolabile mantenendo invariate le dimensioni esterne (`80×80×96 mm`), nel futuro aggiornamento di `jarvis_lego_bot_mini_cube.mpd` occorrerà soltanto aprire la tasca interna frontale a **`48,0 × 41,6 mm`** (`6` stud × `13` plate):
1. **Layer 3..6 (`Y_h = 28,8..67,2 mm`):** Sostituire le `3622` (`1×3`) laterali con `3004` (`1×2`, `X = 0..16` e `64..80`) ed eliminare `3710`/`2431` (L3) e `3010` (L6) centrali (sostituiti dalla cornice 3D nera opaca a filo `Z = 0`).
2. **Layer 2 centrale (`X = 16..64 mm`):** Sostituire `3009` (`Brick 1×6`) con **`2× 3666`** (`2` plate = `6,4 mm`, `Y_h = 19,2..25,6 mm`), portando la base della tasca a `25,6 mm` per lasciare `3,1..3,6 mm` di margine sotto la PCB e proteggere il flex FPC inferiore.

---

## 6. Istruzioni Preliminari di Montaggio e Regolazione

1. **Inserimento cornice (senza colla):** Inserire la cornice 3D dal retro nella tasca LEGO `48,0 × 41,6 mm` fino a portare la faccia frontale a filo `Z = 0,0 mm`; le due flange laterali appoggiano dietro i mattoncini `3004`.
2. **Posizionamento OLED:** Appoggiare il modulo OLED nella tasca della culla posteriore (zero contatto sul vetro frontale grazie allo scarico `1,8 + 0,35 mm`; flex inferiore libero nello scasso dedicato).
3. **Serraggio e centratura fine (`±2,5 mm`):** Accoppiare la culla alle flange della cornice con **4× viti M2,5 + rondelle** attraverso le finestre asolate `±2,5 mm`, accendere una schermata di test `128×64`, centrare l'area attiva nella finestra `32×19,2 mm` e serrare dallo sportello posteriore `3036` (prima di inserire la slitta ESP32-S3 per massima comodità).
4. **Cablaggio (`GND, VCC 3,3V, SCL=GPIO42, SDA=GPIO41`):** Collegare i 4 fili flessibili allo scasso superiore della culla e guidarli verso `ESP32-S3` sotto allo speaker `AS03604AR`.

---

## 7. Criticità residue da confermare prima del Passaggio B
- Riconciliare `35,40×33,50` vs `36,00×34,00` e la quota `11,30 mm` sul modulo fisico reale.
- Confermare orientamento e tipo di connettore (pin dritti vs `90°` vs pad liberi).
- Confermare compatibilità `3,3 V` su `VCC` e controller **`SH1106` vs `SSD1106`**.
