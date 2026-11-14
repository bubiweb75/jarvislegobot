# Report Verifiche Tecniche & Ottimizzazione Mattoncini Sfusi — FASE D, Passaggio B

**Modello aggiornato:** `jarvis_lego_bot_mini_cube_oled_2b.mpd` (`134` pezzi LEGO: `112` Modulo A + `22` Modulo B1; Modulo B2 escluso; supporto 3D OLED 2B escluso dal conteggio LEGO).  
**Backup originale preservato:** `jarvis_lego_bot_mini_cube_137_backup.mpd` (`137` pezzi).

> [!WARNING]
> **Stato di validazione:** le verifiche riportate di seguito si basano su **controlli geometrici automatici** sui volumi `.dat` reali di Studio 2.0 (`AABB`, tolleranza `0,2 mm`) e sui volumi di ingombro della tasca OLED 2B. **La costruibilità fisica reale, la tenuta meccanica dell'incastro e il montaggio del modulo OLED Binghe non sono ancora stati verificati né nella GUI di BrickLink Studio né fisicamente.**

---

## 1. Riepilogo delle 7 Verifiche Tecniche

| # | Verifica | Metodo | Esito osservato | Cosa resta da verificare |
|---|---|---|---|---|
| 1 | **Collisioni corpi LEGO (`.dat` AABB)** | Script Python su `.dat` Studio 2.0 (`>0,2 mm`) | **0 collisioni impreviste** su `112` (A), `22` (B1) e `134` (A+B1). Uniche `2` sovrapposizioni intenzionali: `4070 + 3070b` (`8,00 × 8,00 × 1,60 mm`), incastro frontale previsto degli accenti Medium Azure. | Controllo collisioni/snap nella GUI di BrickLink Studio 2.0 (`Collision` attivo). |
| 2 | **Ingombro tasca cornice 3D OLED 2B** | Verifica AABB contro `X=16..64 mm`, `Y_h=25,6..67,2 mm`, `Z=0..8,0 mm` | **0 interferenze**. La tasca è libera su tutti i `48,0 × 41,6 mm` (`6 stud × 13 plate`). | Prova di inserimento fisico con sagoma in cartoncino (`02-OLED-Cardboard-Prototype`) e futura stampa 3D. |
| 3 | **Ingombro culla posteriore & cavità interna** | Verifica AABB contro `X=16..64 mm`, `Y_h=25,6..67,2 mm`, `Z=8..28 mm` | **0 interferenze** LEGO nella zona culla/PCB. | Ingombro reale di culla, viti/regolazione, connettore I²C superiore (`GND, VCC, SCL, SDA`) e cavo flex inferiore. |
| 4 | **Tenuta strutturale parete frontale (`L2..L7`)** | Analisi appoggi e ponti LDraw | Le spalle `3004` (`1×2` Black, `X=0..16` e `64..80`) su `L3..L6` poggiano su `3005` (`X=0..8`) + `4070` (`X=8..16`, stud superiore a `Y=-72`); `6111` (`1×10` Black su `L7`) fa ponte sui `48 mm` superiori; `2× 3666` (`1×6` Black su `L2`) formano la soglia inferiore (`Y_h=19,2..25,6 mm`). | Verifica fisica della rigidità delle colonne `1×2` durante il montaggio e l'inserimento dell'inserto 2B senza incollaggi. |
| 5 | **Preservazione design FASE C & dimensioni** | Verifica AABB globale Modulo A | Corpo principale `80 × 80 × 96 mm` invariato (`X=[-3,2, 80,0] mm` per pin Technic laterale, `Y_h=[0,0, 96,0] mm`, `Z=[0,0, 83,2] mm`). Corona `49307` + `85984`, griglia speaker `AS03604AR`, tetto removibile e sportello posteriore invariati. | Ispezione visiva in BrickLink Studio 2.0. |
| 6 | **Coerenza BOM CSV, XML BrickLink e PDF** | Verifica incrociata script su `134` pezzi | `LEGO_BOM_Aggiornata.csv` e `BrickLink_Wanted_List_Aggiornata.xml` allineati esattamente (`33` lotti, `134` pezzi: `113` Black `BL 11`, `18` Dark Bluish Gray `BL 85`, `3` Medium Azure `BL 156`). PDF inventario (2 pag.) e istruzioni (3 pag.) generati senza errori. | Verifica visiva dei PDF prima della stampa e importazione test della XML su BrickLink. |
| 7 | **Compatibilità Modulo B1 e futuro B2** | Confronto coordinate interfaccia A↔B1 | Modulo B1 (`22` pezzi, base `12×12` stud) invariato; nessun pezzo del nuovo frontale scende sotto `Y_h=0`. Compatibilità con futura base mobile B2 preservata. | Verifica fisica accoppiamento A su B1. |

---

## 2. Elementi Provvisori in Attesa di Conferma Fisica OLED

Le seguenti parti restano marcate come **provvisorie (`Da confermare dopo prova fisica OLED`)** nella distinta fino al rilievo con calibro del modulo **Binghe OLED 1,3"** e alla prova della sagoma:
- **`3666` (`Plate 1 × 6` Black, `2` di `4` pezzi su `L2` centro):** determina l'altezza inferiore della tasca (`Y_h = 25,6 mm`).
- **`3004` (`Brick 1 × 2` Black, `8` di `21` pezzi su `L3..L6` spalle SX/DX):** determina la larghezza libera della tasca (`48,0 mm` = `6` stud).
- **Discrepanza controller firmware:** il progetto prevede `SH1106`, mentre la scheda commerciale Binghe riporta `SSD1106` — **da verificare fisicamente al primo test I²C**, poiché i due controller non sono intercambiabili senza adeguare il driver.
- **Quote PCB non riconciliate:** `35,40 × 33,50 mm` (disegno tecnico) vs `36 × 34 mm` (immagini commerciali).

---

## 3. Opzioni Separate di Ottimizzazione per Mattoncini Sfusi

> [!IMPORTANT]
> Le sostituzioni seguenti **NON sono state applicate automaticamente** né al modello `.mpd` né alla distinta `LEGO_BOM_Aggiornata.csv` / `BrickLink_Wanted_List_Aggiornata.xml`. Sono alternative valide **solo se** vuoi massimizzare il riuso di mattoncini sfusi già in tuo possesso.

| Pezzo attuale (BOM 134) | Qtà | Sostituzione possibile con sfusi | Vincolo strutturale / impatto |
|---|---:|---|---|
| `4477` — Plate 1 × 10 (Black) | `2` | `2× 3460` (`1×8`) + `2× 3023` (`1×2`), oppure combinazioni `3666` (`1×6`) + `3710` (`1×4`) | **Sicura su L1**, purché i giunti tra le plate siano sfalsati rispetto ai brick di `L0` e `L2`. |
| `6111` — Brick 1 × 10 (Black) | `4` | `4× 3008` (`1×8`) + `4× 3004` (`1×2`) alternando SX/DX tra i livelli | **Accettabile su L0/L7/L8/retro**, ma su `L7` (ponte sopra l'OLED) l'eventuale giunto deve cadere sopra una spalla (`X=0..16` o `64..80`), **mai** nel vuoto centrale `X=16..64`. |
| `3034` — Plate 2 × 8 (Black, telaio tetto) | `2` | `4× 3020` (`2×4`) oppure `2× 3795` (`2×6`) + `2× 3022` (`2×2`) | **Possibile solo se** il giunto poggia sulle pareti `L8` (`Z=0..8`) e viene bloccato sopra dagli elementi di chiusura `3460`/`49307`/`85984`. |
| `4162` — Tile 1 × 8 (Black, griglia tetto) | `6` | **NESSUNA — NON SPEZZARE** | Attraversa a ponte la cavità aperta dello speaker (`6×6` stud senza stud sottostanti): pezzi più corti cadrebbero dentro il vano speaker. |
| `3460` — Plate 1 × 8 (Black, tetto) | `2` | **NESSUNA — NON SPEZZARE** | Funge da traversa portante sulla cavità speaker. |
| `85984` — Slope 30° 1 × 2 × 2/3 (Black) | `16` | `32× 54200` (`Cheese Slope 1×1`) oppure `16× 3040b` (`Slope 45° 2×1`) | **Sconsigliata per estetica:** cambia il profilo superiore continuo da `30°` a `45°` (o molto frammentato con `54200`). |
