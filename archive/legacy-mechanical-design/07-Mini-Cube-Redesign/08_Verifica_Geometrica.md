# 08 — Verifica Geometrica e Controllo Collisioni (FASE C: Rifinitura Estetica Finale)

> **Modello verificato:** `jarvis_lego_bot_mini_cube.mpd` (`115` Modulo A + `22` Modulo B1 = `137` pezzi).
> **Nota trasparenza:** Le verifiche riportate di seguito derivano dall'analisi automatica delle mesh `.dat` (bounding-box AABB e sub-geometria `.dat` di Studio 2.0) e dei volumi parametrici dell'elettronica. **Il controllo collisioni interattivo di BrickLink Studio 2.0 GUI non è ancora stato eseguito** e resta in carico alla tua verifica finale prima dell'approvazione definitiva.

---

## 1. Quote Effettive e Corona Superiore (`49307` + `85984`)

Misurazione diretta dai vertici `.dat` trasformati nel sistema di coordinate mondo:
- **Modulo A completo:** `80,00 × 80,00 × 96,00 mm` (`10×10` stud × `10` brick).
- **Corona superiore (`4× 49307` + `16× 85984` su Plate 29–30):**
  - `X = [0,00, 80,00] mm` (**0,00 mm** di sporgenza laterale)
  - `Z = [0,00, 80,00] mm` (**0,00 mm** di sporgenza frontale/posteriore)
  - `Y (altezza) = [89,60, 96,00] mm` (**96,00 mm** esatti, nessun elemento sollevato oltre il tetto)
- **Orientamento `85984`:** Verificato direttamente su `85984.dat` (lato alto `Y = -15,6` a `Z_locale = +6..+10`, lato inclinato a `Z_locale = -10`). I 16 pezzi sono orientati con il bordo inclinato verso l'esterno su tutti e 4 i lati (`R_ID` frontale, `R_Y180` posteriore, `R_Y90` sinistro, `R_Y270` destro).
- **Base B1:** `96,00 × 96,00 mm` (`12×12` stud).

---

## 2. Controllo Collisioni `.dat` (AABB) e Analisi `4070 + 3070b`

- **Modulo B1 (`22` pezzi):** `0` collisioni AABB.
- **Corona tetto, griglia speaker (`4162` su `3460`/`3666`), cornice OLED (`3710`/`2431`), pareti, sportello SNOT:** `0` collisioni AABB.
- **Assemblaggio `15573 + 4070 + 3070b` (2 accenti Medium Azure frontali a `X = 30` e `X = 170`):**
  - Il controllo AABB rileva **2 sovrapposizioni di bounding-box** (`#56 vs #57` a SX e `#59 vs #60` a DX, overlap nominale `8,00 × 8,00 × 1,60 mm`).
  - **Distinzione tra incastro previsto e interferenza reale:**
    - In `4070.dat`, la parete frontale incassata dove risiede lo stud laterale (`stud2a.dat`) si trova a **`Z_locale = -6,0` LDU** (`Z_mondo = 14,0` LDU = `5,60 mm`), mentre il labbro inferiore sporge fino a `Z_locale = -10,0` LDU solo nella fascia bassa `Y_locale = +20..+24` (`Y_mondo = -52..-48` LDU).
    - Il `3070b` (`Tile 1×1`, spessore `8` LDU) è montato sullo stud di `4070` tra **`Z_mondo = 6,0..14,0` LDU** (`2,40..5,60 mm` dietro il filo frontale `Z = 0`) e tra **`Y_mondo = -72..-52` LDU** (interamente sopra il labbro inferiore di `4070`).
    - Pertanto il `3070b` alloggia nella tasca frontale incassata di `4070` senza sporgere davanti al frontale (`0,00 mm` di sporgenza oltre `Z = 0`). La verifica finale nel collision checker mesh di BrickLink Studio 2.0 confermerà l'assenza di falsi positivi.

---

## 3. Verifica Volumi Elettronica Parametrica (`0` interferenze)

| Sottosistema Elettronico | Volume Parametrico LDU `(X0,Y0,Z0)..(X1,Y1,Z1)` | Collisioni rilevate | Note |
|---|---|---:|---|
| `OLED_SH1106_Param_36x34x11` | `(55, -155, 20)..(145, -70, 47.5)` | **0** | Gli accenti a `X=20..40` e `160..180` restano esterni a `X=55..145` |
| `Speaker_AS03604AR_36x8.8mm` | `(55, -224, 55)..(145, -202, 145)` | **0** | Griglia `4162` a `Y=-240..-232` lascia `3,2 mm` di clearance sopra il cono |
| `ESP32_S3_DevKitC_LayoutC` | `(115, -197.5, 125)..(178.5, -40, 180)` | **0** | Accessibile dallo sportello posteriore `3036` (`6×8`) |
| `MAX98357A_plus_C1` | `(30, -75, 52)..(85, -25, 102)` | **0** | I `15573` (`Z=0..40`) lasciano `4,8 mm` di margine prima di `Z=52` |
| `INMP441_UpperRight` | `(160, -214, 35)..(178, -184, 75)` | **0** | Allineato al foro `3700` su fianco DX L8 |
| `Breakout_USBC_5V` | `(45, -45, 135)..(90, -25, 178)` | **0** | — |
| `JST_XH_6pin_Bottom` | `(78.75, -20, 90)..(121.25, 0, 110)` | **0** | — |
