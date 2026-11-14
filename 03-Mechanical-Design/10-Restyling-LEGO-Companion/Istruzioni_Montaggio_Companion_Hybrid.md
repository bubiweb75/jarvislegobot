# Istruzioni di Montaggio — JARVIS LEGO BOT Companion Hybrid (Soluzione 3)

**Modello di riferimento:** [`jarvis_lego_bot_companion_hybrid.mpd`](jarvis_lego_bot_companion_hybrid.mpd)  
**Totale pezzi LEGO:** **`122` pezzi** (`96` Modulo A + `26` Modulo B1) in **`28` lotti unici** (`92` Black `BL 11`, `27` Dark Bluish Gray `BL 85`, `3` Medium Azure `BL 156`).  
**Tavola tecnica delle 4 viste:** [`03_companion_hybrid_4views_definitive.svg`](images/03_companion_hybrid_4views_definitive.svg)

> [!WARNING]
> **Avvertenza sulle quote di OLED e Speaker:** le dimensioni effettive del modulo **OLED 1,3"** e dello **speaker `4 Ω / 3 W`** e il relativo sistema di fissaggio interno restano **provvisori e da confermare** alla ricezione dei componenti fisici. Non incollare alcun elemento LEGO.

---

## Fase 1 — Costruzione della Base Fissa Arrotondata `Modulo B1` (`12 × 12 stud`, `26` pezzi)

1. **Piastra base `12 × 12 stud` (`Y = -8..0 LDU`):**
   - Affianca sul piano di lavoro **`2× 3036`** (`Plate 6×8` Black), **`1× 3035`** (`Plate 4×8` Black) e **`1× 3031`** (`Plate 4×4` Black) per formare l'impronta quadrata `12 × 12 stud` (`96,0 × 96,0 mm`).
2. **Cornice perimetrale liscia con angoli arrotondati (`Y = -16..-8 LDU`):**
   - Posiziona sui 4 vertici esterni i **`4× 25269`** (*Tile Round 1×1 Quarter* Dark Bluish Gray) orientando l'arco convesso verso l'esterno di ciascun angolo.
   - Completa il bordo anteriore e posteriore (`10 stud` tra gli angoli) con **`2× 6636`** (`Tile 1×6` DBG) + **`2× 2431`** (`Tile 1×4` DBG), sfalsando i giunti tra fronte e retro per massimizzare la rigidità della piastra base.
   - Sui lati sinistro e destro, posiziona **`4× 3069b`** (`Tile 1×2` DBG, vicino agli angoli) e **`2× 2431`** (`Tile 1×4` DBG, al centro), lasciando liberi i 4 canali laterali (`Z = 60..80` e `160..180`) per l'estrazione dei pin di bloccaggio.
3. **Anello d'innesto universale `8 × 8 stud` (`Y = -32..-8 LDU`):**
   - Monta al centro della base i **`2× 3702`** (`Technic Brick 1×8` Black, sui lati sinistro e destro) e i **`2× 3009`** (`Brick 1×6` Dark Bluish Gray, sul fronte e sul retro).
   - Inserisci dall'esterno i **`4× 32054`** (*Technic Pin 3L with Stop Bush* Black) nei fori n° 2 e n° 7 dei `3702`. Il vano centrale `6 × 6 stud` resta libero per il futuro connettore **`JST-XH 6-pin`** della base mobile **B2**.

---

## Fase 2 — Modulo A: Basamento e Guance Circolari Medium Azure (`Livelli L0–L2`)

1. **Livello `L0` (`Y = -24..0 LDU`, anello d'accoppiamento inferiore):**
   - Costruisci il telaio inferiore posizionando **`2× 3702`** (`Technic Brick 1×8` Black) sui lati sinistro e destro (`X = 0..20` e `180..200`, `Z = 20..180`), **`1× 3008`** (`Brick 1×8` Black) sul fronte (`X = 20..180`, `Z = 0..20`) e **`2× 3005`** (`Brick 1×1` Black) come pilastri posteriori (`X = 20..40` e `160..180`, `Z = 180..200`).
   - *Nota costruttiva:* le 4 celle `1×1` ai vertici esterni restano intenzionalmente libere affinché gli spigoli curvi `85080` del livello `L1` scendano fino alla base senza alcuno spigolo retto sporgente.
2. **Livello `L1` (`Y = -48..-24 LDU`, fascia curva DBG + fossette Medium Azure a filo):**
   - Monta sui 4 angoli i **`4× 85080`** (*Brick Round Corner 2×2 Macaroni* **Dark Bluish Gray**), che si innestano a ponte tra il fronte/retro e i fianchi di `L0`, bloccando ortogonalmente la base del corpo.
   - Chiudi i due fianchi tra gli angoli con **`2× 3009`** (`Brick 1×6` **Dark Bluish Gray**).
   - Sul fronte (`X = 40..160`), monta al centro **`1× 3010`** (`Brick 1×4` Black, `X = 60..140`) e ai due lati (`X = 40..60` e `140..160`) i **`2× 4070`** (*Brick Special 1×1 with Headlight* Black) con lo stud frontale incassato rivolto in avanti (`-Z`).
   - Applica sui due `4070` i **`2× 98138`** (*Tile Round 1×1* **Medium Azure**): grazie al recesso di `4070`, i due dettagli circolari azzurri risultano **perfettamente a filo della parete frontale (`Z = 0,0 mm`)**.
3. **Livello `L2` (`Y = -72..-48 LDU`, soglia tasca OLED + attacchi inferiori sportello):**
   - Angoli anteriori: monta **`2× 85080`** (Black) a sinistra e a destra.
   - Fianchi e retro: monta **`2× 3008`** (`Brick 1×8` Black, da `Z = 40` a `Z = 200`) e affianca all'interno dei pilastri posteriori i **`2× 87087`** (*Brick 1×1 with Stud on Side* Black, `X = 30` e `170`, `Z = 190`) con lo stud laterale rivolto verso il retro (`+Z`).
   - Soglia inferiore della tasca OLED *(provvisoria fino a misura fisica OLED)*: sovrapponi **`2× 3666`** (`Plate 1×6` Black, `X = 40..160`, `Y = -56` e `-64`), portando la quota del davanzale interno a `Y_h = 25,6 mm`.

---

## Fase 3 — Corpo Arrotondato, Tasca OLED 2B, Pulsante e Microfono (`Livelli L3–L8`)

1. **Livello `L3` (`Y = -96..-72 LDU`, pulsante laterale `GPIO 47`):**
   - Monta sui 4 angoli **`4× 85080`** (Black).
   - Fianco sinistro (`Z = 40..160`): posiziona **`1× 87087`** (`Z = 40..60`, stud rivolto verso `-X`) con applicato **`1× 98138`** (*Tile Round 1×1* **Medium Azure**) come cappuccio del pulsante, seguito da **`1× 3005`** (`1×1` Black, `Z = 60..80`) e **`1× 3010`** (`1×4` Black, `Z = 80..160`).
   - Fianco destro: **`1× 3009`** (`Brick 1×6` Black).
2. **Livelli `L4` e `L5` (`Y = -120` e `-144 LDU`, pareti lisce e spalle OLED):**
   - Su ciascun livello monta **`4× 85080`** (Black) ai 4 angoli e **`2× 3009`** (`Brick 1×6` Black) sui fianchi sinistro e destro.
   - Sul fronte resta completamente aperta la **tasca da `48,0 × 41,6 mm` (`X = 40..160 LDU`)** tra i profili curvi dei `85080`.
3. **Livello `L6` (`Y = -168..-144 LDU`, attacchi superiori sportello posteriore):**
   - Monta **`2× 85080`** (Black) sugli angoli anteriori, **`2× 3008`** (`Brick 1×8` Black, `Z = 40..200`) sui fianchi e **`2× 87087`** (Black, `X = 30` e `170`, `Z = 190`, stud verso `+Z`) per l'aggancio superiore dello sportello.
4. **Livello `L7` (`Y = -192..-168 LDU`, ponte superiore OLED):**
   - Monta **`4× 85080`** (Black) ai 4 angoli, **`2× 3009`** (Black) sui fianchi e **`1× 3009`** (`Brick 1×6` Black, `X = 40..160`, `Z = 0..20`) come architrave sopra la tasca OLED, collegando rigidamente le due colonne anteriori.
5. **Livello `L8` (`Y = -216..-192 LDU`, anello superiore e foro microfono `INMP441`):**
   - Monta **`4× 85080`** (Black) ai 4 angoli, **`1× 3009`** (Black) sul fronte, **`1× 3009`** (Black) sul retro (sopra lo sportello posteriore) e **`1× 3009`** (Black) sul fianco sinistro.
   - Sul fianco destro (`Z = 40..160`), monta anteriormente **`1× 3700`** (*Technic Brick 1×2 with Hole* Black, `Z = 40..80`, foro acustico `Ø 4,8 mm` per la capsula `INMP441`) seguito da **`1× 3010`** (`Brick 1×4` Black, `Z = 80..160`).
6. **Guida interna `ESP32-S3` e Sportello Posteriore:**
   - All'interno del vano posteriore-destro (`Layout C`), posiziona il supporto **`1× 32316`** (*Technic Beam 1×5* DBG) per la slitta verticale dell'`ESP32-S3`.
   - Applica la maniglia **`1× 3069b`** (`Tile 1×2` DBG) al centro dello sportello **`1× 3036`** (`Plate 6×8` Black) e aggancia lo sportello a pressione sui `4× 87087` posteriori (`L2` e `L6`). Nella parte bassa (`Y = -32..0 LDU`) resta aperta la feritoia passacavo **USB-C**.

---

## Fase 4 — Cupola Morbida Removibile con Alloggiamento Speaker (`Plates 28–30`, `24` pezzi)

1. **Telaio base del coperchio (`Plate 28`, `Y = -224..-216 LDU`):**
   - Unisci **`4× 3795`** (`Plate 2×6` Black: 2 su fronte/retro `X = 40..160` e 2 sui lati `Z = 40..160`) lasciando al centro il vano quadrato **`6 × 6 stud` (`48,0 × 48,0 mm`)** per lo speaker.
   - Applica sui 4 angoli del telaio (in corrispondenza degli `85080` sottostanti) i **`4× 27925`** (*Tile 2×2 Curved Macaroni* Black), in modo che il coperchio si innesti sul livello `L8` con ritenuta calibrata e sia facilmente rimovibile verso l'alto.
2. **Cupola perimetrale morbida (`Plates 29–30`, `Y = -240..-224 LDU`):**
   - Sul bordo anteriore (`Z = 0..40`) e posteriore (`Z = 160..200`) monta **`6× 15068`** (*Brick Curved 2×2×2/3 No Studs* Black: `3` davanti e `3` dietro) con la curvatura che scende verso l'esterno.
   - Sui bordi esterni sinistro (`X = 0..20`) e destro (`X = 180..200`) monta **`6× 85984`** (*Slope 30° 1×2×2/3* Black: `3` per lato).
3. **Supporto e Griglia Acustica Speaker (`Plates 29–30`):**
   - Sulla fila interna dei lati sinistro e destro (`X = 20..40` e `160..180`, `Z = 40..160`, `Plate 29`) posiziona **`2× 3666`** (`Plate 1×6` Black) per creare i `3,2 mm` di luce verticale sopra la membrana dello speaker.
   - Al livello superiore (`Plate 30`, `Y = -240..-232 LDU`), fissa a ponte tra i due `3666` le **`4× 4162`** (*Tile 1×8 with Groove*: `2` Black esterne a `Z = 50` e `150` + `2` Dark Bluish Gray centrali a `Z = 90` e `110`), ottenendo due feritoie acustiche simmetriche da `8 × 48 mm` e una superficie superiore interamente priva di stud.
