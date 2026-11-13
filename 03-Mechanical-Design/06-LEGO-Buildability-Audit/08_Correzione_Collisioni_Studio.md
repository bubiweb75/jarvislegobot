# 08 — Correzione Collisioni Rilevate in BrickLink Studio 2.0

**Data:** 2026-11-13  
**File MPD verificato:** [`jarvis_lego_bot.mpd`](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/03-Mechanical-Design/06-LEGO-Buildability-Audit/jarvis_lego_bot.mpd)  
**Libreria geometrica di riferimento:** Mesh reali `.dat` di BrickLink Studio 2.0 (`C:\Program Files\Studio 2.0\ldraw\parts\` e `p\`)

---

## 1. Perché il controllo AABB precedente non bastava

La prima versione dell'MPD aveva superato un controllo basato su **bounding box nominali stimati** (dimensioni teoriche da tabella `stud × plate`), che assumeva convenzioni di origine e assi locali non sempre coincidenti con quelle reali della libreria LDraw/Studio 2.0.

Importando il file in **BrickLink Studio 2.0** con il controllo collisioni attivo, sono emerse compenetrazioni reali dovute a cinque cause radice geometriche:

1. **Assi locali di Technic Liftarm (`32278`, `32316`):** nella libreria Studio `.dat` la lunghezza del beam corre lungo l'asse locale **Z** (non X). Applicando `R_Y90` o `R_XP90` con orientamento errato, i beam longitudinali risultavano ruotati trasversalmente attraverso il telaio e la cavità interna.
2. **Asse locale di Cerchione e Pneumatico (`56904`, `56898`):** nella libreria `.dat` di Studio l'asse di rotazione della ruota corre lungo **Z** (non X). La rotazione precedente (`0 1 0 ...` / `R_Y180`) lasciava le ruote orientate di 90° rispetto ai semiassi `4519` (asse X), intersecando i longheroni `32278`.
3. **Origine verticale e offset SNOT di `54200` (Cheese Slope), `3040b` (Slope 45°) e `87087` (Brick 1×1 with Stud on Side):**
   - `54200` ha `Y_local = [-15.6, 0.0]` (vertice inclinato rivolto verso `-Y` e base a `Y = 0`), non `[-24, 0]`.
   - `3040b` ha `Z_local = [-30, +10]` (sporgenza/pendenza su `-Z`, non centrata), quindi richiede rotazioni esatte (`R_Y90` / `R_Y270` / `R_Y180`) per avere la faccia inclinata verso l'esterno senza invadere la piastra di copertura.
   - `87087` ha lo stud laterale su `Z_local = [-14, -10]` e il corpo su `[-10, +10]`: gli elementi SNOT (`2412b`, `3069b`, `14769`, `3795`) devono avere la faccia posteriore esattamente a contatto con `Z = -10` (o `±20` rispetto al centro brick) ruotata verso l'esterno (`R_SNOT_FRONT`).
4. **Sovrapposizione tetto e sportello posteriore (`3036` 6×8 e `3035` / `3034`):**
   - Sul tetto di Modulo A (`Y = -360..-368`), una piastra `3036` (6×8) occupava la zona `Z = 1..2` dove insistono gli `8× 3040b` perimetrali. È stata sostituita con una piastra `3035` (`4×8`, `Z = 2..6`) più `2× 3034` (`2×8`, copertura superiore `Y = -368..-376`), lasciando libero lo smusso perimetrale degli `3040b`.
   - Sullo sportello posteriore (`Z = 180..188`), la piastra `3036` (`6×8`) era ruotata con lato 8 in orizzontale (invadendo le pareti laterali): ruotandola con `R_DOOR` (`6` stud in X × `8` stud in Y, `X = 40..160`, `Y = -224..-64`) insieme a `1× 3031` (`4×4`, `Y = -304..-224`) e `2× 3022` (`2×2` di chiusura inferiore `Y = -64..-24`), lo sportello si chiude a filo nella cornice `6×14` stud senza collisioni.
5. **Cerniere OLED (`3937` / `3938`) e piastrine frontali:**
   - L'accoppiamento reale nei `.dat` di Studio tra `3937` (base) e `3938` (top) avviene a **4 LDU** di passo verticale (`Y = -240` e `Y = -244`, non 24 LDU).
   - La cornice OLED inferiore (`1× 3069b` Dark Bluish Gray? -> nel modello v2 `2× 3069b` Medium Azure laterali + `2× 54200` Medium Azure inferiori/laterali, con `2× 3022` di appoggio) è stata allineata alle quote reali dei `.dat` di Studio eliminando le interferenze con le cerniere `3938` e con la griglia speaker.

---

## 2. Riepilogo delle correzioni per zona critica

| Zona controllata | Problema precedente in Studio | Soluzione implementata in `jarvis_lego_bot.mpd` |
|---|---|---|
| **Apertura frontale OLED** | Interferenza tra `3937/3938`, tile bezel e `54200` | Cerniere `3937` (`Y=-240`) e `3938` (`Y=-244`) accoppiate a 4 LDU; cornice `2× 3069b` (`322`) + `2× 54200` (`322`) allineati su `Z=12..20` con `0` collisioni |
| **Griglia speaker e attacchi SNOT** | Offset errato tra `87087`, `3795` (`2×6`) e `2412b` | `3795` e `2412b` orientati con `R_SNOT_FRONT` sullo stud laterale `Z=-10` degli `87087` (`X=40..160`, `Y=-192..-96`) |
| **Sportello posteriore** | `3036` ruotato di 90° dentro i pilastri laterali | Orientato `3036` (`6×8` stud) con `R_DOOR` nella luce netta `6` stud (`X=40..160`), completato da `3031` (`4×4`) e `2× 3022` (`2×2`) |
| **Tetto inclinato** | `3036` sovrapposto agli `3040b` | `8× 3040b` lungo i bordi + `1× 3035` (`4×8`) centrale + `2× 3034` (`2×8`) a livello `-368..-376` + `1× 14769` + `1× 2431` |
| **Slitta interna ESP32-S3 (`32316`)** | `32316` ruotato trasversalmente | `2× 32316` orientati verticalmente lungo Y (`X=50` e `X=150`, `Z=135`), lasciando `32,8 mm` netti per l'ESP32-S3 (`25,4 mm`) |
| **Base fissa B1 (`12×11` stud)** | Spessore e accoppiamento piastre base/anello `8×8` | Anello `8×8` (`3009` + `3702`) + `4× 32054` coassiali nei fori Technic di `3702`, raccordato a `Modulo A` a `(+20, -32, +20)` LDU |
| **Base mobile B2 (`16×15` stud)** | `32278` trasversali e ruote `56904/56898` ruotate di 90° | `2× 32278` longitudinali lungo Z (`X=70, 250`), `4× 2780` coassiali alle traverse `3702`, assali `4519` + ruote `56904/56898` con `R_Y90` (asse X), caster `3020` + `3022` + `2654` |

---

## 3. Verifica geometrica su mesh reali `.dat` di BrickLink Studio 2.0

È stato eseguito lo script di verifica sui vertici reali `.dat` caricati da `C:\Program Files\Studio 2.0\ldraw\` (ricorsione completa su subfile `parts/` e `p/`, esclusi esclusivamente gli stud superiori `Y_local < -0.1`, lo stud laterale `87087` `Z_local < -10.1` e gli accoppiamenti coassiali dichiarati pin/assale/cerniera/pneumatico).

### Risultati collisioni corpo-corpo (`soglia > 0,2 mm` / `0,5 LDU`)

| Configurazione verificata | Numero parti | Collisioni rilevate (`> 0,2 mm`) |
|---|---:|---:|
| **Modulo A** | 132 | **0** |
| **Modulo B1** | 19 | **0** |
| **Modulo B2** | 33 | **0** |
| **Assieme A + B1** | 151 | **0** |
| **Assieme A + B2** | 165 | **0** |
| **Totale parti distinte nell'MPD** | **184** | **0** |

### Risultati ingombri elettronica nei vani interni

| Modulo | Componente verificato | Collisioni con parti LEGO (`> 0,2 mm`) |
|---|---|---:|
| Modulo A | `OLED 0,96"` (`27 × 27 × 4 mm`) | **0** |
| Modulo A | `Speaker 40×40×20 mm` | **0** |
| Modulo A | `ESP32-S3 DevKit` (`51 × 25,5 × 12 mm`) | **0** |
| Modulo A | `MAX98357A` | **0** |
| Modulo A | `JST-XH 6-pin` | **0** |
| Modulo B2 | `Pacco batteria 2S 18650` | **0** |
| Modulo B2 | `Motore N20 SX` | **0** |
| Modulo B2 | `Motore N20 DX` | **0** |

---

## 4. Stato della validazione finale in BrickLink Studio 2.0 GUI

- La verifica automatica è stata eseguita in Python direttamente sulle **mesh `.dat` ufficiali installate da Studio 2.0** su questo PC (`0` collisioni su tutti i moduli e su entrambi gli assiemi `A+B1` e `A+B2`).
- Il motore interno della GUI di BrickLink Studio 2.0 esegue inoltre controlli propri su connettività delle clip/cerniere e tolleranze di snap durante il rendering interattivo: **è raccomandato un ultimo import visivo di [`jarvis_lego_bot.mpd`](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/03-Mechanical-Design/06-LEGO-Buildability-Audit/jarvis_lego_bot.mpd) in Studio 2.0 sul PC dell'utente** con controllo collisioni attivo come conferma finale prima di procedere agli acquisti.
