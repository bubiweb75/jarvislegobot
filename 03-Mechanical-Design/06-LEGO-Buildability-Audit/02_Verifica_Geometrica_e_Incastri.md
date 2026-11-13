# 02 – Verifica Geometrica, Incastri e Analisi dei Quattro Moduli

**Sistema dimensionale di riferimento:** `1 stud = 8,0 mm` | `1 brick = 9,6 mm` (`3 plate`) | `1 plate = 3,2 mm`.  
**Modello LDraw:** [jarvis_lego_bot.mpd](jarvis_lego_bot.mpd) (`187` pezzi totali: `136` Modulo A + `19` Modulo B1 + `32` Modulo B2).

---

## 1. Limiti dell'Ambiente di Verifica (Dichiarazione Esplicita)
In questo ambiente **non è installato BrickLink Studio 2.0** né un motore CAD a mesh completo. Pertanto:
- **Controlli effettivamente eseguiti (via Python su `jarvis_lego_bot.mpd`):**
  1. Conteggio esatto e riconciliazione 1:1 di tutti i `187` riferimenti LDraw.
  2. Controllo collisioni **AABB 3D** (`tolleranza 0,05 mm`) escludendo solo gli accoppiamenti coassiali intenzionali (pin/assali dentro fori Technic, pneumatici `56898` su cerchioni `56904`): **`0` collisioni non intenzionali** in A, B1, B2.
  3. Verifica allineamento griglia stud (`8,0 mm`), multipli di brick/plate (`9,6 / 3,2 mm`) e quote Z dei fori Technic.
- **Controlli NON eseguibili in questo ambiente (NON dichiarati `VERIFICATO DIGITALMENTE`):**
  - Verifica interferenze su **mesh 3D reale** (smussi, tubi inferiori dei brick, attrito reale dei pin, gioco delle cerniere `3937/3938` inclinate).
  - Simulazione cinematica di apertura sportello, rotazione ruote e verifica resistenza meccanica/vibrazioni: **`DA VERIFICARE FISICAMENTE`** (o previo import di `jarvis_lego_bot.mpd` in BrickLink Studio 2.0).

---

## 2. Verifica Separata dei Quattro Moduli

### 2.1 Modulo A (`10 × 10 stud` = `80 × 80 mm`, `15 brick` = `144 mm`, `136` pezzi nel MPD)
- **Pareti e griglia frontale SNOT:** apertura speaker `6 × 5 brick` (`48 × 48 mm`) chiusa da pannello SNOT **`3× 3795` (`Plate 2×6`) + `9× 2412b` (`Grille Tile`)**, fissato su **`4× 87087`** incassati (`Y=0,8..1,8 stud`), che lascia `Y=1,8..9,0` (`57,6 mm`) liberi dietro la griglia.
- **Visiera OLED `1,3"`:** finestra `6 × 4 brick`, incorniciata da **`6× 3069b`** + **`4× 54200`** (`Medium Azure`) su faccia `Y = -0,4..0,0`, e supportata internamente da **`2× 3937 + 2× 3938`** (`Hinge 1×2`) a `Z = 27..31 plate`.
- **Sportello posteriore apribile (`6 × 12 stud` = `48 × 96 mm`):** montato a filo (`Y = 9,6..10,0`) su **`4× 87087`** incassati (`Y = 8,6..9,6`). La composizione `3036` (`6×8`) + `3031` (`4×4`) + `3022` (`2×2`) + `2431`/`3069b` chiude esattamente `48 × 96 mm` (`10 brick`), apribile manualmente a scatto.
- **Foro mic `INMP441`:** `1× 3700` (`Technic Brick 1×2`) al centro di `Brick 13` (`Z = 36..39`), sopra il setto acustico **`3035` (`Plate 4×8`)** a `Z = 26..27`.

### 2.2 Modulo B1 – Base fissa (`12 × 11 stud` = `96 × 88 mm`, `19` pezzi nel MPD)
- **Superficie di appoggio stabile:** piastra base completa `12 × 11 = 132 stud²` esatti (`2× 3035` + `2× 3031` + `1× 3034` + `1× 3020` + `1× 3460` + `1× 3710`), con cornice `3895` (`1×12`) + `2× 2730` (`1×10`). Modulo A appoggia in `X=1..11, Y=1..11` (filo posteriore per accesso USB-C e sportello).

### 2.3 Interfaccia Removibile `A ↔ B1/B2` (`8 × 8 stud` + `4× 32054`)
- **Allineamento fori Technic:** su B1 (`Z = 4..7 plate`) e su B2 (`Z = 11..14 plate`) l'anello `8 × 8` (`2× 3702` + `2× 3009`) entra nel vano inferiore di Modulo A (`Z = 0..3 plate` con `2× 3702`). I fori dei `3702` di A e dei `3702` di B1/B2 risultano **coassiali** (`Y = 3,5` e `Y = 7,5` relative a B1).
- **Inserimento `4× 32054`:** lunghezza utile `2L` (`16 mm`) attraversa esattamente `1 stud` parete A (`8 mm`) + `1 stud` parete B1/B2 (`8 mm`), mentre il collare/stop bush `1L` sporge all'esterno per presa manuale senza invadere il vano interno.

### 2.4 Modulo B2 – Base mobile (`16 × 15 stud` = `128 × 120 mm`, `32` pezzi nel MPD)
- **Telaio e trasmissione:** `2× 32278` (`1×15`) + `2× 3702` (`1×8`) uniti da `4× 2780`, luce da terra `~10 mm` (`3 plate`). L'interfaccia `8×8` poggia su 4 pilastri angolari (`4× 3004 + 8× 3023`, `5 plate = 16 mm`) collegati al telaio (nessuna parte sospesa).
- **Ruote e semiassi:** `2× 4519` (`Axle 3L`, `24 mm`) attraversano il foro centrale (`Y=7,5`) dei longheroni `32278` (`8 mm`) entrando nei mozzi `56904` (`14 mm`) con pneumatici `56898` (`Ø 43,2 × 14 mm`). Caster posteriore `2654` + `3022` a `Z = 0..3 plate`.
- **Nota onesta:** i giunti `D 3 mm → 4519` e le staffe N20 **non sono parti LEGO** e non sono modellati nel `.mpd` (`DA PROGETTARE E VERIFICARE FISICAMENTE`).
