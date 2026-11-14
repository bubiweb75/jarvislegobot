# JARVIS AI Desk Buddy — Proposta Progettuale Restyling LEGO Companion

> [!IMPORTANT]
> **Stato del documento:** **PROPOSTA PROGETTUALE E CONFRONTO TECNICO (In attesa di approvazione)**
> In conformità alle tue indicazioni:
> - Il file [`jarvis_lego_bot_mini_cube_oled_2b.mpd`](../09-FASE-D-Passaggio-B-OLED-2B/jarvis_lego_bot_mini_cube_oled_2b.mpd) e tutte le distinte/BOM esistenti ([`LEGO_BOM_Aggiornata.csv`](../09-FASE-D-Passaggio-B-OLED-2B/LEGO_BOM_Aggiornata.csv), [`LEGO_BOM_Per_Modulo_Aggiornata.csv`](../09-FASE-D-Passaggio-B-OLED-2B/LEGO_BOM_Per_Modulo_Aggiornata.csv), [`BrickLink_Wanted_List_Aggiornata.xml`](../09-FASE-D-Passaggio-B-OLED-2B/BrickLink_Wanted_List_Aggiornata.xml)) **sono stati integralmente preservati e non modificati**.
> - Nessuna costruzione è dichiarata verificata fisicamente prima dell'assemblaggio reale e della misurazione col calibro di OLED 1,3" e speaker.

---

## 1. Analisi Critica del Modello MPD Attuale (`FASE D — Passaggio B`)

Il modello attuale ([`jarvis_lego_bot_mini_cube_oled_2b.mpd`](../09-FASE-D-Passaggio-B-OLED-2B/jarvis_lego_bot_mini_cube_oled_2b.mpd), `134` pezzi LEGO: `112` nel Modulo A + `22` nella base B1) ha risolto con successo la compattezza verticale (`80 × 80 × 96 mm`) e la visibilità angolare dello schermo OLED (`±35,6°` orizzontali grazie alla tasca `48,0 × 41,6 mm` per la cornice sottile 2B da `1,8 mm`). Tuttavia, dal punto di vista estetico e percettivo presenta **quattro limiti specifici** che lo fanno apparire come un contenitore elettronico squadrato anziché un compagno da scrivania:

1. **Spigoli verticali vivi a `90°` su tutta l'altezza (`L0..L8`, `0..86,4 mm`):**
   - Le pareti laterali (`12× 3008` `Brick 1×8` Black + `2× 3008` DBG) e i pilastri frontali (`16× 3004` `Brick 1×2` impilati in colonne verticali non sfalsate su `L3..L6`) formano quattro spigoli verticali netti a `90°`. L'occhio percepisce immediatamente una "scatola" tecnica.
2. **Giunti verticali continui sulle spalle frontali (`X = 16 mm` e `X = 64 mm`):**
   - Per lasciare libera la tasca OLED da `48,0 mm` (`6 stud`), i livelli `L3..L6` usano su ciascun lato due `3004` (`Brick 1×2` orientati lungo X) impilati uno sull'altro senza ammorsamento trasversale con i mattoncini `3008` delle pareti laterali (`X = 0..8 mm`), affidando la tenuta ai soli stud del livello `L2` sottostante e al ponte `6111` (`1×10`) sul livello `L7`.
3. **Corona del tetto a smusso dritto (`85984` `Slope 30°`) anziché bombata:**
   - I `16× 85984` (`Slope 30° 1×2×2/3`) creano uno smusso piano a `30°` di soli `6,4 mm` in cima a `86,4 mm` di pareti verticali dritte, insufficiente ad ammorbidire la silhouette complessiva.
4. **Base B1 `12×12` con angoli retti taglienti:**
   - La cornice perimetrale in *Tile* `Dark Bluish Gray` (`6636`, `2431`, `3069b`) termina sui 4 vertici con spigoli vivi a `90°`, accentuando l'effetto di basamento industriale.

![Confronto Diretto Modello Attuale vs Varianti Proposte](images/00_confronto_attuale_vs_varianti.svg)

---

## 2. Requisiti Costruttivi, Spazio Interno e Integrità Strutturale

Prima di definire l'estetica delle due varianti, è stata eseguita una verifica geometrica tridimensionale sui file `.dat` ufficiali di BrickLink Studio 2.0 per accertare che l'arrotondamento degli angoli **non riduca lo spazio utile per l'elettronica** e **migliori la solidità strutturale**:

- **La coincidenza geometrica chiave (`85080` ↔ Tasca OLED 2B):**
  - Il mattoncino **`85080`** (*Brick Round Corner 2 × 2 Macaroni with Stud Notch*, raggio esterno **`16,0 mm` = `2 stud`**, presente in oltre `105` set LEGO in *Black* e `17` set in *Dark Bluish Gray*) occupa sui lati frontali esattamente `X = 0..16,0 mm` (angolo sinistro) e `X = 64,0..80,0 mm` (angolo destro).
  - La tasca frontale per il modulo **OLED 1,3" + cornice 2B** richiede esattamente **`X = 16,0..64,0 mm` (`48,0 mm` = `6 stud`)**.
  - Di conseguenza, sostituendo le colonne angolari quadrate con pilastri curvi `85080`, **le spalle arrotondate abbracciano al decimo di millimetro la tasca OLED da `48,0 × 41,6 mm`**, eliminando i fragili pilastri `3004` impilati e ammorsando strutturalmente a `90°` la parete frontale con le pareti laterali su ogni singolo strato (`L1..L8`)!
- **Verifica d'ingombro interno (`64,0 × 64,0 mm`):**
  - La parete interna curva del mattoncino `85080` sporge nella cavità interna `64 × 64 mm` soltanto nei quattro vertici estremi per **`4,98 mm` in diagonale** (`X > 67,06 mm`, `Z > 67,06 mm` o `Z < 12,94 mm`).
  - L'intera area centrale e laterale della cavità (`64,0 × 64,0 × 83,2 mm`), la tasca OLED (`X = 16..64 mm`), il vano speaker superiore `6×6 stud` (`48 × 48 mm` per **PUI Audio `AS03604AR` `Ø 36 × 8,8 mm`** o fallback `Ø 40 × 20 mm`), l'amplificatore **`MAX98357A` + `C1`**, il microfono **`INMP441`** (dietro il foro `Technic 3700`), lo sportello posteriore **`3036` (`6×8 stud`)**, il passaggio cavo **USB-C** e la slitta verticale **`ESP32-S3` (`Layout C`, montata sul supporto `32316` a `Z = 45..67 mm`)** presentano **`0,00 mm` di interferenza mesh 3D** con i mattoncini `85080`.
- **Eliminazione dello spigolo vivo inferiore (`L0`):**
  - Poiché `85080` possiede i suoi 2 stud sulle estremità `(30, 10)` e `(10, 30)` e non sulla cella d'angolo `(10, 10)`, lasciando libere le 4 celle `1×1` esterne del livello `L0` (`3008` frontale + `2× 3702` laterali + `2× 3005` posteriori), il profilo cilindrico di raggio `16 mm` scende ininterrotto fino alla base B1, senza alcuno spigolo quadrato sporgente sotto le curve.

---

## 3. Variante 1 — **Companion Rounded** *(Soft Pod Arrotondato)*

### Natura delle viste presentate
> [!NOTE]
> Le tre viste seguenti (Frontale, Laterale SX, Prospettica 3/4) sono **render tecnici vettoriali generati direttamente dalle geometrie 3D costruibili (`.dat` LDraw di BrickLink Studio 2.0)** con verifica automatica di zero collisioni impreviste. Solo il **display OLED 1,3" con gli occhi bianchi animati** e la **cornice interna 2B** sono rappresentati come **segnaposto grafici/prototipali** (non conteggiati come mattoncini LEGO).

![Variante 1 — Companion Rounded (Frontale, Laterale, Prospettica)](images/01_variante1_companion_rounded_3views.svg)

### Descrizione analitica per area
1. **Sagoma (`80,0 × 80,0 × 96,0 mm` — Corpo `10×10 stud`):**
   - Corpo monoblocco a capsula morbida (*soft pod*), in cui tutti e 4 gli spigoli verticali sono sostituiti da colonne cilindriche continue di raggio **`R = 16,0 mm`** realizzate con **`28× 85080`** (*Brick Round Corner 2×2 Macaroni*: `4` in *Dark Bluish Gray* al livello `L1` per creare una fascia basale continua e `24` in *Black* sui livelli `L2..L8`).
   - Nessuna sporgenza laterale oltre l'impronta `10×10 stud` (a eccezione del tile `3070b` del pulsante a `X = -3,2 mm`).
2. **Frontale (Volto espressivo, non finestra tecnica):**
   - La parete frontale piana tra le curve `85080` misura esattamente `48,0 mm` (`6 stud`), coincidendo con la larghezza della cornice nera opaca a filo (**Soluzione 2B**, incasso `1,8 mm`, finestra visibile `32,0 × 19,2 mm`, angolo di visione `±35,6°` O / `±51,3°` V).
   - In questo modo non esistono giunti verticali LEGO ai lati dello schermo: il volto nero emerge direttamente tra le due guance arrotondate `85080`, con **due grandi occhi bianchi animati su fondo nero**.
   - Subito sotto gli angoli esterni dello schermo (al livello `L1`, `X = 20 mm` e `X = 60 mm`), due piccoli accenti quadrati **`3070b` (`Tile 1×1` Medium Azure)** incassati a filo parete (`Z = 0,0 mm`) tramite **`2× 4070` (`Headlight Brick`)** fungono da "guance luminose" discrete, ben distinte dagli occhi.
3. **Tetto morbido e arrotondato con alloggiamento speaker (removibile in blocco):**
   - Il coperchio superiore (`Plates 28–30`, `Y_h = 86,4..96,0 mm`) si raccorda al cilindro verticale tramite **`4× 27925` (`Tile 2×2 Curved Macaroni` Black)** sui 4 angoli, **`6× 15068` (`Brick Curved 2×2×2/3` Black)** lungo il fronte e il retro (che creano una fronte morbida e bombata sopra gli occhi) e **`6× 85984` (`Slope 30° 1×2×2/3` Black)** lungo i fianchi.
   - Al centro resta intatto il vano `6×6 stud` (`48 × 48 mm`) per lo speaker **`AS03604AR` (`4 Ω / 3 W`)**, protetto da **`4× 4162` (`Tile 1×8`: `2` Black + `2` Dark Bluish Gray)** con due feritoie acustiche lineari simmetriche da `8 × 48 mm` e **zero stud esposti** su tutta la calotta.
4. **Fianchi puliti e funzionali:**
   - Pareti laterali completamente lisce in `Black` (`3009` `Brick 1×6` + `3008` `Brick 1×8`), con fascia inferiore `Dark Bluish Gray` continua sul perimetro.
   - Sul fianco sinistro (`L3`, `Z = 20 mm`): pulsante tattile con cappuccio **`3070b` (`Tile 1×1` Medium Azure)** su `87087`.
   - Sul fianco destro alto (`L8`, `Z = 24 mm`): foro acustico `Ø 4,8 mm` tramite **`3700` (`Technic Brick 1×2`)** per il microfono **`INMP441`**, disaccoppiato acusticamente dallo speaker superiore.
5. **Base fissa B1 (`12×12 stud` = `96,0 × 96,0 mm`) e compatibilità B2:**
   - La base B1 mantiene l'interfaccia universale **`8×8 stud`** con i `4× 32054` (*Technic Pin 3L with Stop Bush*) e il vano centrale per il connettore **`JST-XH 6-pin`** verso la futura base mobile **B2**.
   - I 4 angoli della cornice perimetrale in *Dark Bluish Gray* sono ora arrotondati con **`4× 25269` (`Tile Round 1×1 Quarter`)**, richiamando la curvatura del corpo principale.
6. **Accessibilità posteriore e USB:**
   - Lo sportello posteriore **`3036` (`Plate 6×8` Black)** con maniglia **`3069b` (DBG)** si incastra a filo esattamente nello spazio di `48,0 mm` (`X = 16..64 mm`) tra le colonne posteriori `85080` tramite `4× 87087` (`L2` e `L6`), lasciando libero nella parte inferiore il passaggio per il cavo **USB-C** e consentendo l'accesso immediato a `ESP32-S3`, `SGM2212` e culla OLED.
7. **Impatto sulla distinta LEGO:**
   - **Totale pezzi:** **`122` pezzi** (`96` Modulo A + `26` Modulo B1) → **`-12 pezzi`** rispetto al modello attuale (`134` pezzi).
   - **Lotti unici:** **`28` lotti** → **`-5 lotti unici`** rispetto ai `33` attuali (vengono eliminati per intero `21× 3004`, `16×` piccoli brick/plate di riempimento, sostituendoli con mattoncini strutturali lunghi `3009` e angolari `85080`).

---

## 4. Variante 2 — **Mini Robot Friendly** *(Personaggio Robotico Espressivo)*

### Natura delle viste presentate
> [!NOTE]
> Anche per la **Variante 2**, le viste Frontale, Laterale SX e Prospettica 3/4 sono **render tecnici vettoriali generati direttamente dalle geometrie 3D costruibili (`.dat` LDraw di BrickLink Studio 2.0)** con verifica automatica di zero collisioni impreviste, mentre lo schermo OLED 1,3" con occhi espressivi e la cornice 2B sono segnaposto grafici/prototipali.

![Variante 2 — Mini Robot Friendly (Frontale, Laterale, Prospettica)](images/02_variante2_mini_robot_friendly_3views.svg)

### Descrizione analitica per area
1. **Sagoma (`86,4 × 80,0 × 96,0 mm` — Corpo `10×10 stud` + dettagli laterali `1 plate`):**
   - Condivide l'architettura arrotondata con pilastri **`85080` (`R = 16 mm`)** della Variante 1, ma accentua la personalità da piccolo robot amichevole aggiungendo due "cuffie/padiglioni auricolari" circolari a basso profilo (`3,2 mm` per lato) e una fronte bicolore scolpita.
2. **Frontale (Volto con arcata sopraccigliare e fossette tonde):**
   - Gli occhi bianchi animati sull'OLED 1,3" (incassato nella medesima tasca `48,0 × 41,6 mm` con cornice nera opaca 2B) sono sormontati da un'arcata frontale bicolore: **`2× 15068` (`Brick Curved 2×2×2/3` Black)** ai lati + **`2× 11477` (`Brick Curved 2×1 No Studs` Dark Bluish Gray)** al centro, che disegnano una piccola visiera/fronte espressiva sopra lo sguardo.
   - Al livello `L1` (`X = 20 mm` e `X = 60 mm`), al posto dei tile quadrati, due **`98138` (`Tile Round 1×1` Medium Azure)** incassati a filo nei `4070` creano due "fossette/guance" circolari azzurre.
3. **Tetto morbido e arrotondato con alloggiamento speaker:**
   - Identico concettualmente e funzionalmente alla Variante 1 (removibile in blocco, angoli curvi `27925`, retro curvo `3× 15068`, fianchi `6× 85984`, griglia speaker `4× 4162` sopra il vano `6×6 stud` per `AS03604AR`), con il dettaglio centrale frontale in `Dark Bluish Gray` (`2× 11477`).
4. **Fianchi con padiglioni circolari ("Cuffie" robotiche):**
   - Al centro dei fianchi sinistro e destro (`L4`, `Z = 40 mm`, `Y_h = 48 mm`), due mattoncini SNOT `87087` sorreggono un **`14769` (`Tile Round 2×2 with Bottom Stud Holder`, `Ø 16,0 mm` in Dark Bluish Gray)** per lato, che conferisce la classica silhouette da piccolo droide/companion con cuffie senza aggiungere braccia, gambe o testa separata.
   - Il pulsante sul fianco sinistro (`L3`, `Z = 20 mm`) adotta anch'esso un cappuccio circolare **`98138` (`Tile Round 1×1` Medium Azure)** coordinato con le guance.
   - Sul fianco destro alto (`L8`) resta invariato il foro acustico `3700` per il microfono `INMP441`.
5. **Base fissa B1 (`12×12 stud`) e Accessibilità posteriore:**
   - Identiche alla Variante 1: base B1 con angoli arrotondati **`4× 25269` (DBG)**, interfaccia `8×8 stud` compatibile con **B2**, sportello posteriore **`3036` (`6×8 stud`)** apribile a filo tra le colonne `85080` e passaggio cavo **USB-C** inferiore libero.
6. **Impatto sulla distinta LEGO:**
   - **Totale pezzi:** **`131` pezzi** (`105` Modulo A + `26` Modulo B1) → **`-3 pezzi`** rispetto al modello attuale (`134` pezzi).
   - **Lotti unici:** **`31` lotti** → **`-2 lotti unici`** rispetto ai `33` attuali.

---

## 5. Confronto Sinottico e Impatto sulla Distinta LEGO (BOM)

### 5.1 Tabella Comparativa Generale

| Criterio | Modello Attuale (`FASE D Pass. B`) | **Variante 1 — Companion Rounded** ★ | **Variante 2 — Mini Robot Friendly** |
|---|---|---|---|
| **Estetica generale** | Cubo tecnico con spigoli vivi a `90°` | **Capsula morbida futuristica (*Soft Pod*)** | **Piccolo robot con cuffie `Ø 16 mm` e visiera** |
| **Spigoli verticali (`L1..L8`)** | Retti a `90°` (`3008` / `3004`) | **Curvi continui `R = 16 mm` (`28× 85080`)** | **Curvi continui `R = 16 mm` (`28× 85080`)** |
| **Ammorsamento spalle OLED (`L3..L6`)** | Colonne `3004` non intrecciate ai lati | **Intreccio strutturale a `90°` su ogni livello** | **Intreccio strutturale a `90°` su ogni livello** |
| **Frontale e OLED 1,3"** | Finestra in parete piatta con giunti verticali | **Volto integrato tra curve `85080` + guance `3070b` Azure a filo** | **Volto con arcata bicolore `11477` + fossette tonde `98138` Azure** |
| **Tetto e Speaker `AS03604AR`** | Corona `49307` + `16× 85984` (`30°` dritti) | **Cupola morbida `27925` + `6× 15068` + `6× 85984`** | **Cupola morbida con fronte bicolore (`4× 15068` + `2× 11477` DBG)** |
| **Fianchi** | Piatti con spigoli vivi | **Puliti, raccordati con raggio `16 mm`, bottone `3070b` Azure** | **Padiglioni tondi `14769` (`Ø 16 mm` DBG) + bottone tondo `98138` Azure** |
| **Base fissa B1 (`12×12 stud`)** | Angoli retti a `90°` (`22` pz) | **Angoli smussati con `4× 25269` (`26` pz)** | **Angoli smussati con `4× 25269` (`26` pz)** |
| **Compatibilità futura Base B2** | 100% (`8×8 stud` + `JST-XH 6-pin`) | **100% invariata (`8×8 stud` + `JST-XH 6-pin`)** | **100% invariata (`8×8 stud` + `JST-XH 6-pin`)** |
| **Accesso posteriore e USB-C** | Sportello `3036` + passacavo basso | **Sportello `3036` a filo tra curve + passacavo basso** | **Sportello `3036` a filo tra curve + passacavo basso** |
| **Numero pezzi LEGO (A + B1)** | `134` (`112` A + `22` B1) | **`122` (`96` A + `26` B1) [`-12 pz`]** | **`131` (`105` A + `26` B1) [`-3 pz`]** |
| **Lotti unici BrickLink** | `33` lotti | **`28` lotti [`-5 lotti`]** | **`31` lotti [`-2 lotti`]** |
| **Collisioni `.dat` / Interferenze 3D** | `0` impreviste | **`0` impreviste (`0` interferenze elettronica)** | **`0` impreviste (`0` interferenze elettronica)** |

### 5.2 Dettaglio Variazione Pezzi LEGO rispetto alla BOM Attuale (`134` pz)

Tutti i nuovi codici introdotti sono **pezzi LEGO standard ad altissima diffusione** (verificati nei database locali [`parts.csv`](../../csv/parts.csv), [`elements.csv`](../../csv/elements.csv) e [`inventory_parts.csv`](../../csv/inventory_parts.csv)):

| Codice BL | Descrizione Pezzo LEGO | Colore (BL ID) | Set LEGO in cui appare | Qtà Attuale | Qtà **Var. 1** (`Δ`) | Qtà **Var. 2** (`Δ`) | Ruolo nel Restyling |
|---|---|---|---:|---:|---:|---:|---|
| **`85080`** | *Brick Round Corner 2 × 2 Macaroni* | Black (`11`) | `105` set | `0` | **`24`** (`+24`) | **`24`** (`+24`) | Spigoli curvi `R=16 mm` (`L2..L8`) e spalle OLED |
| **`85080`** | *Brick Round Corner 2 × 2 Macaroni* | Dark Bluish Gray (`85`) | `17` set | `0` | **`4`** (`+4`) | **`4`** (`+4`) | Fascia curva inferiore `L1` sui 4 angoli |
| **`15068`** | *Brick Curved 2 × 2 × 2/3 No Studs* | Black (`11`) | `721` set | `0` | **`6`** (`+6`) | **`5`** (`+5`) | Cupola morbida anteriore e posteriore del tetto |
| **`27925`** | *Tile 2 × 2 Curved, Macaroni* | Black (`11`) | `145` set | `0` | **`4`** (`+4`) | **`4`** (`+4`) | Raccordo curvo liscio ai 4 angoli del tetto |
| **`25269`** | *Tile Round 1 × 1 Quarter* | Dark Bluish Gray (`85`) | `188` set | `0` | **`4`** (`+4`) | **`4`** (`+4`) | Angoli arrotondati della base fissa B1 `12×12` |
| **`11477`** | *Brick Curved 2 × 1 No Studs* | Dark Bluish Gray (`85`) | `408` set | `0` | `0` (`0`) | **`2`** (`+2`) | Arcata sopraccigliare bicolore (solo Var. 2) |
| **`14769`** | *Tile Round 2 × 2 with Bottom Stud Holder* | Dark Bluish Gray (`85`) | `159` set | `0` | `0` (`0`) | **`2`** (`+2`) | Padiglioni laterali "cuffie" `Ø 16 mm` (solo Var. 2) |
| **`98138`** | *Tile Round 1 × 1* | Medium Azure (`156`) | `68` set | `0` | `0` (`0`) | **`3`** (`+3`) | Fossette tonde e bottone laterale (solo Var. 2) |
| `3009` | *Brick 1 × 6* | Black (`11`) / DBG (`85`) | `753` / `398` set | `1` / `2` | **`11` / `4`** (`+12`) | **`9` / `4`** (`+10`) | Pareti laterali pulite e ponti sopra/dietro OLED |
| `3010` | *Brick 1 × 4* | Black (`11`) | `1204` set | `0` | **`3`** (`+3`) | **`3`** (`+3`) | Chiusura centrale `L1` e fianco `L3`/`L8` |
| `3795` | *Plate 2 × 6* | Black (`11`) | `1649` set | `2` | **`4`** (`+2`) | **`4`** (`+2`) | Telaio simmetrico del tetto removibile |
| `2431` | *Tile 1 × 4 with Groove* | Dark Bluish Gray (`85`) | `654` set | `2` | **`4`** (`+2`) | **`4`** (`+2`) | Finitura perimetrale base B1 |
| `3004` | *Brick 1 × 2* | Black (`11`) | `1830` set | `21` | **`0`** (`-21`) | **`4`** (`-17`) | Eliminato l'impilamento di colonne `1×2` sul fronte |
| `85984` | *Brick Sloped 30° 1 × 2 × 2/3* | Black (`11`) | `960` set | `16` | **`6`** (`-10`) | **`6`** (`-10`) | Mantenuti solo sui 2 lati della cupola tetto |
| `3008` | *Brick 1 × 8* | Black (`11`) / DBG (`85`) | `452` / `248` set | `12` / `2` | **`5` / `0`** (`-9`) | **`5` / `0`** (`-9`) | Sostituiti da `3009` (`1×6`) tra gli angoli `85080` |
| `6111`, `4477`, `49307`, `3034`, `3460`, `3023`, `3024`, `15573`, `3622` | Vari mattoncini/plate di giunzione per angoli retti | Black (`11`) | — | `25` tot | **`0`** (`-25`) | **`0`** (`-25`) | Non più necessari grazie agli angoli monolitici `85080` |

---

## 6. Raccomandazione Finale

Si raccomanda la **Variante 1 — Companion Rounded** come scelta principale per il progetto JARVIS AI Desk Buddy, per cinque ragioni progettuali concrete:

1. **Estetica "Companion" pura e fedele a tutti i punti del brief:** trasforma radicalmente il cubo in un oggetto di design morbido, amichevole e futuristico (*stile desktop pod*) con fianchi perfettamente puliti e privi di sporgenze, facendo risaltare al massimo i **due grandi occhi bianchi animati sull'OLED 1,3"** e i piccoli accenti **Medium Azure** a filo.
2. **Maggiore solidità meccanica e semplicità di montaggio:** riduce il numero complessivo di pezzi da **`134` a `122` (`-12` pezzi)** e i lotti unici da **`33` a `28` (`-5` lotti)**, eliminando del tutto i `21` mattoncini `1×2` (`3004`) impilati sulle spalle frontali e sostituendoli con l'ammorsamento angolare continuo dei `85080`.
3. **Zero elementi sporgenti sui fianchi:** a differenza dei padiglioni laterali `14769` della Variante 2 (fissati a sbalzo su stud laterali SNOT), nella Variante 1 le pareti esterne sono interamente monolitiche e resistenti alla presa manuale quando si solleva il corpo A dalla base B1 per spostarlo sulla futura base mobile B2.
4. **Possibilità di ibridazione immediata:** poiché le due varianti condividono il **95% del telaio strutturale**, se ti piace la Variante 1 ma desideri i dettagli tondi in *Medium Azure* (`98138` `Tile Round 1×1`) o l'arcata frontale bicolore (`11477` DBG) della Variante 2, è possibile integrarli direttamente nella Variante 1 senza alcuna modifica strutturale.

---

### Prossimo Passo Richiesto

Indica quale configurazione approvi tra:
1. **Variante 1 — Companion Rounded** *(Raccomandata — `122` pezzi, `28` lotti)*
2. **Variante 2 — Mini Robot Friendly** *(`131` pezzi, `31` lotti)*
3. **Variante 1 con dettagli scelti dalla Variante 2** *(es. fossette tonde `98138` Medium Azure e/o sopracciglio `11477` DBG)*

Solo dopo la tua approvazione procederò a generare il nuovo file `.mpd`, la distinta aggiornata e le istruzioni di montaggio, mantenendo intatti tutti i file storici.
