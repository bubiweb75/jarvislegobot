# Verifica Mirata del Frontale — Simulazione OLED 1,3" e Cornice LEGO Arrotondata

**Data:** 2026-11-14  
**Modello esaminato (NON modificato):** [jarvis_lego_bot_companion_hybrid.mpd](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/03-Mechanical-Design/10-Restyling-LEGO-Companion/jarvis_lego_bot_companion_hybrid.mpd) (`122` pezzi LEGO)  
**Tavola comparativa a 4 viste + sezione quotata:** [04_verifica_frontale_oled_confronto.svg](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/03-Mechanical-Design/10-Restyling-LEGO-Companion/images/04_verifica_frontale_oled_confronto.svg)

---

## 1. Diagnosi: Perché in BrickLink Studio il Frontale Appare come un "Contenitore Tecnico"

L'ispezione del modello `jarvis_lego_bot_companion_hybrid.mpd` (`122` pezzi) con e senza il display OLED 1,3" realistico ha evidenziato **due cause distinte**:

### 1.1 Nel modello LEGO puro visto in BrickLink Studio (Vista 1 della tavola)
Il modello aveva ereditato dalla FASE D Passaggio B la **tasca aperta da `48,0 × 41,6 mm` (`6 stud × 13 plate`, `X = 16..64 mm`, `Y_h = 25,6..67,2 mm`)** originariamente concepita per ospitare una cornice stampata in 3D. Senza inserto 3D né cornice LEGO:
1. **6 stud esposti sulla soglia inferiore (`L2`):** le due plate `3666` (`Plate 1×6` Black a `Y_h = 25,6 mm`) lasciano **6 stud rivolti verso l'alto** direttamente in vista sul bordo inferiore della finestra;
2. **Componenti Technic e strutturali interni visibili attraverso il foro:** guardando dentro l'apertura da `48,0 × 41,6 mm` si vedono nitidamente il **liftarm Technic `32316` Dark Bluish Gray (`1×5` con i 5 fori passanti)** a `Z = 54 mm`, i **brick Technic inferiori `3702`** e i tubi anti-stud del portello posteriore `3036`.

### 1.2 Anche installando il vero modulo OLED 1,3" nella tasca attuale (Vista 2 della tavola)
Simulando il modulo **OLED 1,3" I²C (Binghe)** con le sue dimensioni realistiche:
- **PCB complessivo:** **`35,40 × 33,50 mm`** (fino a `36,0 × 34,0 mm` max commerciale), spessore `1,6 mm`;
- **Pannello in vetro OLED:** **`34,50 × 23,00 × 1,40 mm`**;
- **Area attiva pixel (`128 × 64 px`):** **`29,42 × 14,70 mm`**;

emerge che **il PCB (`35,4 × 33,5 mm`) è più piccolo della finestra aperta (`48,0 × 41,6 mm`)**:
- **Fessure laterali aperte di `6,30 mm` per lato (`(48,0 - 35,4)/2`):** lasciano intravedere la cavità interna e l'estremità destra del liftarm Technic `32316` DBG;
- **Elementi tecnici del PCB completamente esposti sul volto:** restano visibili frontalmente i **4 fori di fissaggio angolari del PCB**, le **4 piazzole/pin I²C superiori (`GND, VCC, SCL, SDA`)**, il **flat cable flessibile arancione (FPC)** inferiore e i **6 stud LEGO** della soglia `3666` (`L2`).

---

## 2. Verifica Interferenze Fisiche vs Visibilità (Punto 3)

| Elemento Interno | Posizione nel Modello (`mm`) | Interferenza Fisica con OLED 1,3" (`Z = 5,6..9,6 mm`) | Visibilità Attorno al Display (Modello Attuale vs Con Nuova Cornice LEGO) |
| :--- | :--- | :--- | :--- |
| **Liftarm Technic `32316` (`1×5` DBG)** | `X = 28..68`, `Y_h = 40..48`, `Z = 50..58 mm` | **Nessuna (`0 mm`)** — distante `> 40 mm` in profondità (`Z`) dal retro del PCB OLED | ❌ **Visibile** nel modello attuale (attraverso il foro e il gap destro da `6,3 mm`)<br>✅ **100% Nascosto** con la nuova cornice LEGO |
| **Technic Brick `3702` (`1×8` Black, L0)** | `Y_h = 0..9,6 mm` (anello base) | **Nessuna (`0 mm`)** — `21,6 mm` più in basso del bordo inferiore del PCB OLED (`Y_h = 31,2 mm`) | ❌ **Visibile** in Studio senza OLED<br>✅ **100% Nascosto** con la nuova cornice LEGO |
| **Technic Brick `3700` (`1×2` Black, L8)** | `X = 72..80`, `Y_h = 76,8..86,4 mm` (foro mic) | **Nessuna (`0 mm`)** — esterno lateralmente e `12 mm` sopra il PCB OLED | ✅ **100% Nascosto** in entrambi |
| **6 Stud della Plate `3666` (`1×6` Black, L2)** | `X = 16..64`, `Y_h = 25,6..27,4`, `Z = 0..8 mm` | **Nessuna collisione col PCB** (`Y_h >= 31,2 mm`), ma impedisce l'appoggio liscio inferiore | ❌ **Tutti e 6 gli stud sono visibili** sotto lo schermo nel modello attuale<br>✅ **0 stud visibili** sostituendo la soglia con il Tile liscio `6636` (`1×6`) |
| **PCB OLED (`35,4×33,5`), 4 fori, 4 pin I²C, FPC** | `X = 22,3..57,7`, `Y_h = 31,2..64,8 mm` | Alloggiato in battuta a `Z = 5,6..8,6 mm` senza collisioni con pareti o angoli `85080` | ❌ **Tutti esposti frontalmente** nel modello attuale<br>✅ **100% Nascosti** dietro la nuova cornice LEGO |

---

## 3. Valutazione della Nuova Cornice Frontale LEGO (Punto 4 e Impatto BOM)

Per trasformare il frontale in un vero **volto da AI Desk Buddy** senza riprogettare il corpo `10×10 stud`, la base `B1` o l'interfaccia `B2`, sono state progettate e verificate **due soluzioni 100% LEGO** che si inseriscono esattamente nel vano `6 stud × 5 brick` (`48,0 × 48,0 mm`) tra gli spigoli arrotondati `85080`:

### 🌟 Soluzione Cornice 1 (RACCOMANDATA — Mostrata nelle Viste 3 e 4): Visiera "Capsula Arrotondata" SNOT (`27925`) Leggermente Incassata
- **Geometria e aspetto estetico:**
  - Sfrutta i **4× `27925` (*Tile Round Corner 2×2 Macaroni* Black)** + **2× `3069b` (*Tile 1×2* Black)** montati in piano frontale SNOT sui **4× `4070` (*Brick 1×1 Headlight* Black)** posti sulle colonne laterali (`X = 50` e `X = 150 LDU`).
  - Poiché lo stud frontale del brick `4070` è arretrato di `6 LDU`, l'intera visiera liscia si posiziona a **`Z = 6..14 LDU` (`2,4..5,6 mm`)**, risultando **leggermente incassata di `2,4 mm`** rispetto al filo frontale `Z = 0` del corpo arrotondato.
  - Il vetro dell'OLED 1,3" poggia subito dietro la visiera a **`Z = 14 LDU` (`5,6 mm`)**, quindi lo schermo risulta **incassato di soli `3,2 mm` (`1 plate`)** rispetto alla superficie della visiera (eliminando l'effetto tunnel da `8,0 mm` e portando l'angolo visivo utile a **`±22,0°` orizzontale e `±35,1°` verticale**).
  - I 4 archi concavi interni dei tile `27925` (`R = 8,0 mm`) creano una **finestra a capsula arrotondata da `32,0 × 16,0 mm`** (`centrata a X = 40,0 mm, Y_h = 48,0 mm`):
    - Lascia **100% visibili** i due grandi occhi bianchi espressivi nell'area attiva (`29,42 × 14,70 mm`, con `2,1–3,7 mm` di margine nero attorno alle pupille);
    - Sormonta il vetro OLED (`34,5 × 23,0 mm`) di `1,25 mm` ai lati e `3,50 mm` sopra/sotto, e sormonta il PCB (`35,4 × 33,5 mm`) di `1,70 mm` ai lati e `8,75 mm` sopra/sotto → **anche con `±2,5 mm` di tolleranza di montaggio, il 100% di PCB, fori, saldature I²C, flat cable FPC e parti Technic interne è completamente invisibile**.
  - Sulla soglia inferiore (`L2`), le `2× 3666` con stud a vista vengono sostituite da `1× 3009` (`Brick 1×6` Black) + **`1× 6636` (`Tile 1×6` Black liscio)** (`0` stud visibili), mentre una delle due `3666` rimosse viene **riusata a costo zero** sotto `L7` (`Y = -168 LDU`).
- **Impatto sulla Distinta LEGO (BOM):**

| Azione | Codice BrickLink | Descrizione Pezzo | Colore | Qtà | Note |
| :---: | :---: | :--- | :--- | :-: | :--- |
| **Rimosso** | `3666` | Plate 1 × 6 | Black (`11`) | **-1** | 1 dei 2 pz su `L2` viene riusato sotto `L7`; l'altro viene rimosso |
| **Aggiunto** | `27925` | Tile, Round Corner 2 × 2 Macaroni | Black (`11`) | **+4** | Angoli arrotondati visiera SNOT *(già presente in distinta!)* |
| **Aggiunto** | `4070` | Brick, Modified 1 × 1 with Headlight | Black (`11`) | **+4** | Supporti SNOT arretrati per la visiera *(già presente in distinta!)* |
| **Aggiunto** | `3005` | Brick 1 × 1 | Black (`11`) | **+2** | Pilastri laterali interni `L3` *(già presente in distinta!)* |
| **Aggiunto** | `3069b` | Tile 1 × 2 with Groove | Black (`11`) | **+2** | Chiusura centrale superiore/inferiore visiera |
| **Aggiunto** | `3009` | Brick 1 × 6 | Black (`11`) | **+1** | Base solida soglia `L2` *(già presente in distinta!)* |
| **Aggiunto** | `6636` | Tile 1 × 6 with Groove | Black (`11`) | **+1** | Soglia liscia senza stud `L2` |
| **TOTALE** | | **Variazione netta Soluzione Cornice 1** | | **+13 pz** | **Da `122` a `135` pezzi totali** (`Modulo A: 96 → 109 pz`, `Modulo B1: 26 pz`) |

---

### 💡 Soluzione Cornice 2 (Alternativa a Minimo Numero Assoluto di Pezzi: `+6` pezzi netti): Cornice Smussata Studs-Up (`85984`)
Se preferisci il **minimo incremento possibile di pezzi (`+6` pezzi netti)** senza montaggio SNOT frontale:
- **Struttura:**
  - `L2` (`Y = -48..-72 LDU`): `1× 3009` (`Brick 1×6` Black, sostituisce le `2× 3666`);
  - `L3` centro (`X = 60..140 LDU`): `1× 3710` (`Plate 1×4` Black) + **`2× 85984` (`Slope 30° 1×2×2/3 No Studs` Black)** inclinati verso il vetro OLED → **elimina i 6 stud esposti** e crea uno smusso inferiore a 30°;
  - `L3, L4, L5` spalle (`X = 0..60` e `140..200 LDU`): `4× 3004` (`Brick 1×2` Black sulle spalle `X = 40..60` e `140..160`);
  - `L6` (`Y = -144..-168 LDU`): `1× 3009` (`Brick 1×6` Black, copre interamente i 4 pin I²C e la parte alta del PCB).
- **Confronto con Cornice 1:** nasconde anch'essa il 100% di PCB, pin I²C, stud e Technic `32316` con soli **`+6` pezzi netti** (`122 → 128` pezzi totali), ma mantiene una finestra rettangolare `32,0 × 19,2 mm` con i 4 angoli interni retti a `90°` anziché arrotondati a capsula (`R = 8 mm`).
