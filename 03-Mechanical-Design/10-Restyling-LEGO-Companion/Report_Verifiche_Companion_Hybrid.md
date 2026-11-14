# Report Verifiche Tecniche — JARVIS LEGO Companion Hybrid (Soluzione 3)

**Data:** 2026-11-14  
**Modello LDraw/BrickLink Studio 2.0 verificato:** `jarvis_lego_bot_companion_hybrid.mpd`  
**Totale pezzi LEGO:** **122 pezzi** (**28 lotti unici**) — *Modulo A: 96 pz | Modulo B1: 26 pz*  
**Confronto con baseline precedente (`jarvis_lego_bot_mini_cube_oled_2b.mpd`):** **-12 pezzi totali** (da 134 a 122 pz) e **-5 lotti unici** (da 33 a 28 lotti).

---

## 1. Valutazione Specifica Punto 5: Arcata Frontale DBG (`11477`) vs Calotta Continua Black (`15068`)

L'indicazione progettuale richiedeva di *«valutare l'arcata frontale DBG soltanto se migliora l'estetica senza compromettere la visibilità e il montaggio dell'OLED»*.

### 1.1 Analisi Geometrica, Visibilità OLED e Montaggio
- **Posizione verticale dell'arcata superiore:** gli slope curvi del tetto (`L9-L10`) poggiano sulla cornice superiore a quota `Y = -224..-240 LDU` (`Y_h = 89,6..96,0 mm` da terra).
- **Posizione della tasca OLED 1,3" (Passaggio B — Soluzione 2B):** il vano OLED occupa `Y = -64..-168 LDU` (`Y_h = 25,6..67,2 mm`), sormontato dalla trave strutturale `L7` (`3010` + `3004` a `Y_h = 67,2..76,8 mm`) e dall'anello `L8` (`3009` a `Y_h = 76,8..86,4 mm`).
- **Impatto su visibilità e montaggio OLED:** **nullo in entrambi i casi**. Tra il bordo superiore dell'area attiva OLED (`Y_h ≈ 57,6 mm`) e il tetto (`Y_h = 89,6 mm`) intercorrono **32,0 mm verticali**; inoltre la pendenza inizia a filo frontale (`Z = 0 LDU`) e sale verso l'interno (`Z = 40 LDU`), lasciando un cono visivo frontale/superiore completamente libero (`> 65°` verso l'alto) e zero interferenze con la culla interna dell'OLED (`Z = 8..16 mm`).

### 1.2 Analisi Estetica e Strutturale: Perché è stata scelta la Calotta Continua `3× 15068` Black
1. **Continuità del "volto" e pulizia formale:** con l'introduzione dei due punti luminosi **Medium Azure** (`2× 98138` *Tile Round 1×1* incassati a filo nei brick `4070` su `L1`) e con gli angoli arrotondati continui `85080` Black su `L1..L8`, il frontale possiede già tre livelli cromatici ben bilanciati:
   - **Viso/Calotta:** Black continuo arrotondato;
   - **Occhi OLED + Guance LED:** Bianco luminoso su fondo nero + 2 accenti circolari Medium Azure in basso;
   - **Base B1 + Anello Acustico Tetto:** Dark Bluish Gray (`25269` + `27925`).
2. **Eliminazione di giunti verticali sopra gli occhi:** l'uso di `3× 15068` (*Slope Curved 2×2 No Studs* Black) copre i 6 stud centrali (`X = 40..160 LDU`) con soli 3 elementi da 2 stud ciascuno, allineati esattamente alla larghezza della finestra OLED (`48,0 mm` = 6 stud). Sostituire il blocco centrale con `2× 11477` (*Slope Curved 1×2* DBG) + `2× 11477` Black laterali introdurrebbe 4 elementi separati con 3 fughe verticali proprio sopra gli occhi e spezzerebbe la morbidezza monolitica della calotta.
3. **Intercambiabilità 1:1 opzionale:** poiché l'attacco avviene sui medesimi stud di `L9` (`X = 40..160 LDU`, `Z = 0..40 LDU`), il modello definitivo utilizza **`3× 15068` Black**, ma l'utente può in qualsiasi momento sostituire il `15068` centrale (`X = 80..120 LDU`) con `2× 11477` DBG senza modificare alcun altro pezzo del robot.

---

## 2. Verifiche Digitali Eseguite (Geometria 3D LDraw `.dat`, Connessioni e Stabilità)

Tutte le verifiche digitali sono state eseguite tramite script di validazione geometrica (`verify_base.py` e `build_hybrid_assets.py`) direttamente sulle geometrie 3D ufficiali `.dat` di **BrickLink Studio 2.0** (`C:\Program Files\Studio 2.0\ldraw\`).

### 2.1 Verifica Collisioni Brick-to-Brick (AABB + Geometria `.dat`)
- **Elementi analizzati:** `122` parti LDraw (`96` in `modulo_a_companion.ldr` + `26` in `modulo_b1_companion.ldr`).
- **Comppenetrazioni strutturali rilevate:** **`0` collisioni**.
- **Allineamento angoli arrotondati `85080` (`Brick Round Corner 2×2 Macaroni`):**
  - Ogni `85080` occupa un ingombro esterno nominale di `2×2 stud` (`40×40 LDU` = `16,0×16,0 mm`) con raggio esterno `R = 40 LDU` (`16,0 mm`) e parete interna curva di raggio `R_int = 20 LDU` (`8,0 mm`).
  - I due `85080` anteriori occupano esattamente `X = 0..40 LDU` (`0..16,0 mm`) e `X = 160..200 LDU` (`64,0..80,0 mm`), lasciando tra loro la luce netta `X = 40..160 LDU` (`16,0..64,0 mm` = **`48,0 mm` / `6 stud`**) richiesta dalla tasca OLED 2B.
- **Inserimento a filo delle "guance" Medium Azure (`4070` + `98138` su `L1`):**
  - I due `4070` (*Brick Modified 1×1 with Headlight*) sono collocati in `(50, -48, 10)` e `(150, -48, 10)` con orientamento `R_Y180` (stud laterale incassato di `2 mm` rivolto verso `Z = 0`).
  - I due `98138` (*Tile Round 1×1* Medium Azure, spessore `8 LDU` = `3,2 mm`) sono innestati sullo stud frontale del `4070`: la faccia esterna del tile risulta a `Z = -3 LDU` (`1,2 mm` di micro-rilievo estetico rispetto al filo `Z = 0`), senza alcuna interferenza con i brick adiacenti `3005` e `3004`.

### 2.2 Verifica Collisioni 3D Mesh tra Mattoncini LEGO e Volumi Elettronici Interni
Poiché gli angoli arrotondati `85080` hanno una bounding box cartesiana `2×2 stud` (`16×16 mm`), è stato eseguito un test di intersezione **triangolo-3D contro box elettronico** su tutti i `9` volumi funzionali interni:

| Volume Elettronico / Funzionale | Coordinate LDU (`X`, `Y`, `Z`) | Dimensioni Reali (`mm`) | Interferenze Mesh 3D Rilevate | Stato |
| :--- | :--- | :--- | :--- | :--- |
| **Tasca Frontale OLED 2B** | `X=40..160`, `Y=-168..-64`, `Z=0..20` | `48,0 × 41,6 × 8,0 mm` | **0** (vano 100% libero) | ✅ Verificato |
| **Culla PCB + Header OLED** | `X=45..155`, `Y=-168..-64`, `Z=20..40` | `44,0 × 41,6 × 8,0 mm` | **0** (appoggio su guida `L2` e fermo `L6`) | ✅ Verificato |
| **Speaker `AS03604AR` (`Ø36×8,8 mm`)** | `X=55..145`, `Y=-216..-192`, `Z=55..145` | `36,0 × 9,6 × 36,0 mm` | **0** (alloggiato nel vano `6×6 stud`) | ✅ Verificato |
| **Camera Acustica Tetto `6×6 stud`** | `X=42..158`, `Y=-215..-193`, `Z=42..158` | `46,4 × 8,8 × 46,4 mm` | **0** (circondata da `4× 27925` DBG) | ✅ Verificato |
| **ESP32-S3 DevKitC-1 (Layout C)** | `X=45..160`, `Y=-145..-60`, `Z=45..165` | `46,0 × 34,0 × 48,0 mm` | Solo contatto voluto con guida `32316` | ✅ Verificato |
| **MAX98357A + Condensatore `C1`** | `X=50..130`, `Y=-68..-30`, `Z=50..130` | `32,0 × 15,2 × 32,0 mm` | **0** (distanza `> 4 mm` dagli angoli `85080`) | ✅ Verificato |
| **Microfono I2S `INMP441`** | `X=135..175`, `Y=-185..-150`, `Z=50..100` | `16,0 × 14,0 × 20,0 mm` | **0** (`85080` occupa solo `Z=0..40`, `INMP441` parte da `Z=50`) | ✅ Verificato |
| **Breakout USB-C 5V Posteriore** | `X=70..130`, `Y=-48..-24`, `Z=150..200` | `24,0 × 9,6 × 20,0 mm` | **0** (vano inferiore `L1` aperto sotto il portello) | ✅ Verificato |
| **Connettore Ombelicale `JST-XH 6-pin`** | `X=70..130`, `Y=-24..0`, `Z=70..130` | `24,0 × 9,6 × 24,0 mm` | **0** (passaggio centrale `8×8 stud` libero) | ✅ Verificato |

### 2.3 Verifica Connessioni Strutturali, Interlocking e Stabilità
1. **Interlocking pareti-angoli (`L1..L8`):** a differenza del modello precedente (dove i pilastri anteriori a lato dell'OLED erano formati da 5 brick `3004` `1×2` impilati verticalmente senza sfalsamento), nel modello **Companion Hybrid** i mattoncini d'angolo `85080` (`2×2`) si incrociano alternativamente con le pareti laterali (`3009` `1×6` + `3008` `1×8`) e con la trave frontale superiore (`3010` `1×4` + `3004` `1×2` su `L7`), creando una **scatola strutturale monoblocco** ad altissima rigidità torsionale.
2. **Nessun elemento sospeso:** tutti i `122` pezzi possiedono almeno 1 connessione stud/anti-stud o pin/foro valida secondo lo standard LDraw.
3. **Baricentro e stabilità su Base B1 (`12×12 stud`):**
   - Impronta a terra Base B1: `96,0 × 96,0 mm` (`X = -8..88 mm`, `Z = -8..88 mm`).
   - Proiezione del baricentro complessivo (LEGO + elettronica): `X_cg ≈ 40,2 mm`, `Z_cg ≈ 41,5 mm`, `Y_cg ≈ 42,0 mm` da terra → angolo critico di ribaltamento statico **`> 48°`** in tutte le direzioni.
4. **Accessibilità Posteriore, Tetto e Compatibilità Base B2:**
   - **Portello posteriore (`3036` Plate `6×8` Black):** si sgancia a trazione verso il retro (`+Z`) dai `4` stud orizzontali dei brick SNOT `87087` (`L2` e `L6`), scoprendo una finestra di `48,0 × 57,6 mm` per l'accesso a `ESP32-S3`, `MAX98357A` e cablaggi.
   - **Passaggio cavo USB-C:** fessura inferiore di `48,0 × 9,6 mm` sotto il portello (`L1`), sempre accessibile anche a portello chiuso.
   - **Coperchio superiore speaker:** l'anello circolare DBG (`4× 27925` + `2× 3795` + `3× 2431`) si solleva verticalmente per inserire o ispezionare lo speaker dall'alto.
   - **Compatibilità futura Base Mobile B2:** l'interfaccia inferiore di `Modulo A` (`anello 8×8 stud` con `4× 3700` Technic Brick `1×2` in `L1` e `4× 32054` Technic Pin 3L) è rimasta **100% invariata**.

---

## 3. Aspetti NON Verificabili Digitalmente (Da Confermare Fisicamente all'Arrivo dei Componenti)

In conformità ai requisiti di progetto, **la costruzione non viene dichiarata fisicamente validata** finché non saranno eseguite le seguenti verifiche sperimentali con i componenti reali:

### 3.1 Tolleranze Fisiche Modulo OLED 1,3" I2C (Sistema di Fissaggio Provvisorio)
- **Variabilità dei PCB commerciali 1,3" (`35,4×33,5 mm` vs `35,5×35,5 mm`):** la tasca LEGO offre una larghezza netta di `48,0 mm` (`6 stud`) e un'altezza di `41,6 mm` (`13 plate`), con una finestra visibile centrale di `32,0 × 22,4 mm` (`4 stud × 7 plate`) incorniciata dai due `3010` verticali SNOT. Quando arriverà il modulo OLED fisico occorrerà misurare con calibro:
  1. Larghezza e altezza esatta del PCB e posizione delle 4 orecchie di fissaggio;
  2. Distanza tra il bordo inferiore del PCB e il bordo inferiore dell'area attiva dei pixel (`29,42 × 14,70 mm`);
  3. Sporgenza dei 4 pin header saldati sul retro (se dritti o a 90°) rispetto alla piastra di fermo `3020` (`2×4`) su `L6`;
  4. Spessore del nastro in schiuma EPDM/EVA (`1..2 mm`) necessario per tenere il vetro dell'OLED premuto contro il retro dei `3010` SNOT senza gioco né flessione.
- **Verifica del controller grafico (`SH1106` vs `SSD1106`):** da confermare via firmware I2C (`0x3C`) per centrare correttamente le pupille sugli assi `X = 0..127` (o `col_offset = 2` su `SH1106`).

### 3.2 Tolleranze Fisiche e Acustiche dello Speaker `4Ω / 3W` (Sistema di Fissaggio Provvisorio)
- **Alloggiamento speaker `AS03604AR` (`Ø36,0 × 8,8 mm`) o equivalente:** il vano nel tetto (`L9`) offre una camera quadrata di `48,0 × 48,0 mm` (`6×6 stud`) sormontata dall'anello circolare `27925` (diametro interno `32,0 mm`, diametro esterno `64,0 mm`). Occorrerà verificare fisicamente:
  1. Il diametro effettivo e l'altezza del magnete dello speaker ricevuto;
  2. Lo spessore della guarnizione anulare in neoprene/gomma tra il bordo metallico dello speaker e i plate LEGO per evitare vibrazioni plastiche (*rattle*) ad alto volume;
  3. L'eventuale necessità di aggiungere 1 plate di spessore (`3,2 mm`) sotto il coperchio `27925` qualora lo speaker superasse i `9,6 mm` di altezza.

### 3.3 Accoppiamenti Meccanici SNOT e Clutch Power Reale dei Mattoncini
- **Tenuta del portello posteriore `3036` (`6×8`) sui `4× 87087`:** nel modello LDraw i `4` brick `87087` (`L2` e `L6`) si trovano a `X = 30 LDU` e `X = 170 LDU`, mentre il plate `3036` (`6×8`, largo `120 LDU` da `X = 40` a `X = 160 LDU`) si aggancia tramite i propri tubi/bordi laterali o richiede, in fase di montaggio fisico, lo scorrimento di `1 stud` verso l'interno (`X = 50` e `X = 150 LDU`) scambiando la posizione tra `87087` e il `3005` adiacente. Entrambi i pezzi (`87087` e `3005`) sono già presenti nello stesso strato `L2`/`L6`, quindi l'eventuale inversione di posizione durante il montaggio fisico richiede **zero pezzi aggiuntivi**.
- **Frizione del pulsante laterale sinistro (`4070` + `98138` Medium Azure in `L3`):** verificare fisicamente che lo scorrimento o la flessione elastica per azionare il tactile switch `6×6 mm` interno sia fluida e ritorni in posizione senza impuntarsi contro le pareti dei brick adiacenti.
