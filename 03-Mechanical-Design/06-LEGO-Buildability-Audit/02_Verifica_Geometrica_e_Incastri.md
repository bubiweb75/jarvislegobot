# 02 – Verifica Geometrica, Incastri e Analisi dei Quattro Moduli

**Sistema dimensionale di riferimento:** `1 stud = 8,0 mm` | `1 brick = 9,6 mm` (`3 plate`) | `1 plate = 3,2 mm`.  
**Modello LDraw:** [jarvis_lego_bot.mpd](jarvis_lego_bot.mpd) (`184` pezzi totali: `132` Modulo A + `19` Modulo B1 + `33` Modulo B2).

---

## 1. Ambiente di Verifica e Controlli Eseguiti
Le verifiche geometriche sono state aggiornate utilizzando direttamente i file `.dat` reali installati da **BrickLink Studio 2.0** (`C:\Program Files\Studio 2.0\ldraw\`) — vedi dettaglio completo in [08_Correzione_Collisioni_Studio.md](08_Correzione_Collisioni_Studio.md):
- **Controlli effettivamente eseguiti (via Python su `jarvis_lego_bot.mpd` + mesh `.dat` di Studio 2.0):**
  1. Conteggio esatto e riconciliazione 1:1 di tutti i `184` riferimenti LDraw (`132 A + 19 B1 + 33 B2`).
  2. Controllo collisioni sui vertici reali `.dat` trasformati (`tolleranza > 0,2 mm` / `0,5 LDU`, esclusi stud superiori, stud laterale `87087` e accoppiamenti coassiali intenzionali): **`0` collisioni corpo-corpo** in Modulo A (`132`), Modulo B1 (`19`), Modulo B2 (`33`), Assieme `A+B1` (`151`) e Assieme `A+B2` (`165`).
  3. Controllo ingombri elettronica nei vani interni (`OLED`, `Speaker`, `ESP32-S3`, `MAX98357A`, `JST-XH`, `2S 18650`, `2× N20`): **`0` interferenze**.
- **Controlli da completare sulla GUI di Studio 2.0 e su prototipo fisico:**
  - Conferma visiva finale con il motore collisioni interno della GUI di BrickLink Studio 2.0 sul PC dell'utente.
  - Simulazione fisica reale di apertura sportello, gioco delle cerniere `3937/3938`, rotazione ruote e resistenza meccanica/vibrazioni: **`DA VERIFICARE FISICAMENTE`**.

---

## 2. Verifica Separata dei Quattro Moduli

### 2.1 Modulo A (`10 × 10 stud` = `80 × 80 mm`, `15 brick` = `144 mm`, `132` pezzi nel MPD)
- **Pareti e griglia frontale SNOT:** apertura speaker `6 × 5 brick` (`48 × 48 mm`) chiusa da pannello SNOT **`3× 3795` (`Plate 2×6`) + `9× 2412b` (`Grille Tile`)**, fissato su **`4× 87087`** incassati (`Z=20..40`), che lascia `57,6 mm` liberi dietro la griglia.
- **Visiera OLED `0,96"`:** finestra incorniciata da **`2× 3069b`** + **`2× 54200`** (`Medium Azure`) su faccia frontale, supportata internamente da **`2× 3937 + 2× 3938`** (`Hinge 1×2`) accoppiate a passo reale Studio `4 LDU` (`Y=-240/-244`).
- **Sportello posteriore apribile (`6 × 14 stud`):** montato a filo posteriore su **`4× 87087`** incassati. La composizione `3036` (`6×8`, orientata `6` stud in X × `8` in Y) + `3031` (`4×4`) + `2× 3022` (`2×2`) + `2431`/`3069b` chiude la luce netta posteriore senza invadere le pareti laterali.
- **Calotta superiore:** `8× 3040b` perimetrali + `1× 3035` (`4×8` centrale) + `2× 3034` (`2×8` superiore) + `2× 2412b` feritoie.
- **Foro mic `INMP441`:** `1× 3700` (`Technic Brick 1×2`) sopra il setto acustico **`3035` (`Plate 4×8`)**.

### 2.2 Modulo B1 – Base fissa (`12 × 11 stud` = `96 × 88 mm`, `19` pezzi nel MPD)
- **Superficie di appoggio stabile:** piastra base completa `12 × 11 = 132 stud²` esatti (`2× 3035` + `2× 3031` + `1× 3034` + `1× 3020` + `1× 3460` + `1× 3710`), con cornice `3895` (`1×12`) + `2× 2730` (`1×10`). Modulo A appoggia in `X=1..11, Y=1..11` (filo posteriore per accesso USB-C e sportello).

### 2.3 Interfaccia Removibile `A ↔ B1/B2` (`8 × 8 stud` + `4× 32054`)
- **Allineamento fori Technic:** su B1 (`Z = 4..7 plate`) e su B2 (`Z = 11..14 plate`) l'anello `8 × 8` (`2× 3702` + `2× 3009`) entra nel vano inferiore di Modulo A (`Z = 0..3 plate` con `2× 3702`). I fori dei `3702` di A e dei `3702` di B1/B2 risultano **coassiali** (`Y = 3,5` e `Y = 7,5` relative a B1).
- **Inserimento `4× 32054`:** lunghezza utile `2L` (`16 mm`) attraversa esattamente `1 stud` parete A (`8 mm`) + `1 stud` parete B1/B2 (`8 mm`), mentre il collare/stop bush `1L` sporge all'esterno per presa manuale senza invadere il vano interno.

### 2.4 Modulo B2 – Base mobile (`16 × 15 stud` = `128 × 120 mm`, `33` pezzi nel MPD)
- **Telaio e trasmissione:** `2× 32278` (`1×15` lungo asse Z) + `2× 3702` (`1×8` traverse) uniti da `4× 2780`, luce da terra `~10 mm`. L'interfaccia `8×8` poggia su 4 pilastri angolari (`4× 3004 + 8× 3023`, `5 plate = 16 mm`) collegati al telaio (nessuna parte sospesa).
- **Ruote e semiassi:** `2× 4519` (`Axle 3L`, `24 mm`) attraversano il foro centrale dei longheroni `32278` (`8 mm`) entrando nei mozzi `56904` (`14 mm`) con pneumatici `56898` (`Ø 43,2 × 14 mm`), tutti orientati lungo l'asse X (`R_Y90`). Caster posteriore `3020` (`2×4` ponte dalla traversa) + `3022` (`2×2`) + `2654` (`Boat Stud`).
- **Nota onesta:** i giunti `D 3 mm → 4519` e le staffe N20 **non sono parti LEGO** e non sono modellati nel `.mpd` (`DA PROGETTARE E VERIFICARE FISICAMENTE`).
