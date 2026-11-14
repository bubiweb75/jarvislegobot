# 09 — Istruzioni di Montaggio (FASE C: Rifinitura Estetica Finale)

> **Modello:** `jarvis_lego_bot_mini_cube.mpd` (`137` pezzi totali: `115` Modulo A + `22` Modulo B1).
> **Tavole di riferimento:**
> - [Viste Ortogonali](images/mini_cube_orthographic_views.svg)
> - [Prospettiva Assemblata A+B1](images/mini_cube_perspective_iso.svg)
> - [Vista Esplosa](images/mini_cube_exploded_assembly.svg)

---

## Fase 1 — Base Fissa B1 (`12×12` stud, `22` pezzi)
1. Unisci le piastre base Black (`2× 3036` 6×8, `1× 3035` 4×8, `1× 3031` 4×4) a formare il quadrato `12×12` stud.
2. Rifinisci il bordo esterno da 1 stud con i tile Dark Bluish Gray (`4× 6636` sui lati ant/post; `4× 3069b` + `2× 2431` sui lati SX/DX) per eliminare gli stud esposti.
3. Costruisci l'anello interfaccia interno `8×8` (`2× 3702` Technic 1×8 ai lati SX/DX + `2× 3009` DBG ant/post) e inserisci i **4× `32054`** Technic Pin Long per l'aggancio al Modulo A.

---

## Fase 2 — Modulo A: Basamento e Mento Incassato (`L0–L2`)
1. **Layer 0 (Interfaccia `8×8`):** Posiziona `2× 3702` (SX/DX), `1× 6111` (frontale) e `2× 3004` (angoli posteriori).
2. **Layer 1 (Trim e supporto accenti):**
   - Lati SX/DX: `2× 3008` Dark Bluish Gray (`1×8`).
   - Posteriore: `2× 3004` (`1×2`).
   - Frontale (altezza 3 plate = 1 brick): sovrapponi `2× 4477` (`Plate 1×10` Black), quindi sul terzo plate superiore posiziona agli angoli `2× 3024` (`1×1`), al centro `1× 3666` (`1×6`), e nelle due posizioni `X=1,5` e `X=8,5` i **2× `15573`** (Jumper 1×2 orientati verso l'interno lungo Z) per arretrare di mezzo stud i supporti degli accenti.
3. **Layer 2 (Accenti Medium Azure incassati a filo):**
   - Frontale: `2× 3005` agli angoli esterni, `1× 3009` (`1×6`) al centro, e sui due Jumper `15573` monta **2× `4070`** (*Headlight* Black, stud frontale rivolto in avanti `-Z`) con applicati **2× `3070b`** (*Tile 1×1* Medium Azure). I tile restano completamente incassati nella nicchia (`0,00 mm` di sporgenza).
   - Lati SX/DX: `2× 3008` Black. Posteriore: `2× 3005` + `2× 87087` (attacchi SNOT inferiori dello sportello).

---

## Fase 3 — Corpo, Finestra OLED, Tasto, Mic e Layout C (`L3–L8`)
1. **Layer 3 (Davanzale liscio OLED + Tasto `GPIO 47`):**
   - Frontale: `2× 3622` (`1×3` Black) ai lati; al centro impila **`2× 3710`** (`Plate 1×4` DBG) + **`1× 2431`** (`Tile 1×4` DBG liscio) per ottenere un davanzale privo di stud visibili sotto il display.
   - Fianco SX: `3005` ant + `87087` (con `3070b` Medium Azure per il tasto) + `3009` post.
2. **Layer 4–6 (Spalle e cornice superiore OLED):**
   - `2× 3622` per lato sui Layer 4, 5 e 6, chiudendo superiormente la finestra `4×2` al Layer 6 con `1× 3010` (`Brick 1×4` DBG).
   - Al Layer 6 posteriore posiziona i due `87087` superiori per l'aggancio dello sportello `3036` (`Plate 6×8` Black con presa `3069b` DBG).
3. **Layer 7–8 (Fronte alta, foro microfono e guida interna):**
   - Frontale L7–L8: `2× 6111` (`1×10` Black). Posteriore L8: `1× 6111`.
   - Fianco DX L8: `3005` + **`3700`** (foro acustico `INMP441`) + `3622` + `3004`.
   - Interno (Layout C): fissa la guida verticale `32316` (`Technic Beam 1×5` DBG) sul lato posteriore destro per la slitta dell'ESP32-S3.

---

## Fase 4 — Tetto Removibile con Corona Continua e Griglia Liscia (`Layer 9`)
1. **Telaio base removibile (Plate 28):** Unisci `2× 3034` (`2×8`), `4× 3023` (`1×2`) e `2× 3795` (`2×6`) a formare l'anello `10×10` con apertura centrale `6×6` per lo speaker `AS03604AR`.
2. **Anello interno rialzo (Plate 29):** Posiziona `2× 3460` (`1×8` ant/post) e `2× 3666` (`1×6` SX/DX) sul bordo interno `6×6` per garantire i `3,2 mm` di clearance sopra il cono dello speaker.
3. **Corona perimetrale continua (Plate 29–30):**
   - Sui 4 angoli del Plate 28 monta **4× `49307`** (*Brick Curved 1×1×2/3*, Black).
   - Lungo i 4 lati tra gli angoli monta **16× `85984`** (*Slope 30° 1×2×2/3*, Black, `4` per lato) con la faccia inclinata rivolta **verso l'esterno**.
4. **Griglia acustica superiore (Plate 30):** Ancora **6× `4162`** (*Tile 1×8*, `4` Black + `2` DBG al centro) alle estremità sui `3666` laterali, lasciando due feritoie acustiche lineari simmetriche sopra lo speaker.
5. **Chiusura modulare:** Inserisci il Modulo A sulla Base B1 tramite i 4 pin `32054` e appoggia il tetto removibile sul Layer 8.
