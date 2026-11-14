# 03 – Design Esterno e Dimensioni Proposte (Mini Cubo)

## 1. Confronto Dimensionale Vecchio vs Nuovo

| Parametro | Vecchio Progetto (`jarvis_lego_bot.mpd`) | **Nuovo Mini Cubo (Proposto)** | Variazione |
|---|---|---|---|
| **Impronta Modulo A** | `10 × 10 stud` (`80,0 × 80,0 mm`) | **`10 × 10 stud` (`80,0 × 80,0 mm`)** | Invariata |
| **Altezza Modulo A** | `15 brick` (`144,0 mm`) | **`10 brick` (`96,0 mm`)** *(o `89,6 mm` con speaker slim)* | **`-48,0 mm` (`-33%`)** |
| **Rapporto di forma (L:P:H)** | `1 : 1 : 1,80` (torre) | **`1 : 1 : 1,20`** (quasi cubo) | Proporzionato |
| **Base fissa B1** | `12 × 11 stud` (`96 × 88 mm`) | **`12 × 12 stud` (`96 × 96 mm`)** o `12 × 11 stud` | Bordo sottile `1 plate` (`3,2 mm`) |
| **Altezza totale su B1** | `~156,8 mm` | **`99,2 – 102,4 mm`** *(in target `100–115 mm`)* | **`~ -54 mm`** |

> **Nota sulle alternative dimensionali (regola Section 3):** Se la verifica finale su OLED commerciale + speaker `Ø 40 × 20 mm` dovesse richiedere più luce verticale per i connettori superiori, le alternative ordinate per compattezza sono:
> 1. **`80 × 80 × 89,6 mm` (`9b+1p`)** — possibile solo con speaker slim `≤ 15 mm`.
> 2. **`80 × 80 × 96,0 mm` (`10 brick`)** — **raccomandata**, compatibile anche con speaker `Ø 40 × 20 mm`.
> 3. **`80 × 80 × 99,2 mm` (`10b+1p`)** — margine extra di `3,2 mm` sul tetto se i pin OLED verticali risultassero molto sporgenti.

---

## 2. Architettura Estetica e Funzionale delle Sei Facce

- **Palette cromatica:**
  - **Principale:** `Black` (`0`).
  - **Secondario / Tecnico:** `Dark Bluish Gray` (`72`) per fasce laterali, griglia tetto, cornice visiera e base B1.
  - **Accenti luminosi:** `Medium Azure` (`322`) — piccoli dettagli mirati (2 piccoli accent lateralmente al volto OLED + cappuccio pulsante sul fianco), senza appesantire il frontale.
- **Linee pulite e smussi:** bordi superiori rastremati con *Slope 45° / 30°* leggeri lungo i lati non occupati dalla griglia, nessuna sporgenza superflua, **nessun occhio LEGO decorativo**.

| Faccia | Configurazione prevista |
|---|---|
| **Frontale** | **Dominata dal volto digitale OLED `1,3" SH1106`** (`finestra netta ~32 × 19,2 mm` / `4 × 2 brick` con cornice *Tile* DBG + piccoli accenti `Medium Azure`), incassato a filo dietro una visiera pulita senza cerniere sporgenti. |
| **Tetto (Superiore)** | **Griglia acustica LEGO removibile** (stile *Grille Tile `2412b`* su cornice rinforzata `10×10` con vano interno `6×6`/`5×5` per speaker rivolto verso l'alto) + feritoia posteriore passiva per aria calda. |
| **Fianco Destro / Sinistro** | **Pulsante fisico `GPIO 47`** incassato a filo su un fianco (con tile/bottone tattile `Medium Azure`) + **foro acustico `INMP441`** (tramite *Technic Brick `3700`* con foro `Ø 4,8 mm` sul fianco/angolo superiore, lontano dal tetto speaker) + prese d'aria inferiori discrete. |
| **Posteriore** | **Sportello di manutenzione apribile** (`6×7` o `6×8` stud SNOT su `87087` o cerniera a incastro) con **passacavo basso `USB-C`** per Modalità A (`Breakout 5 V`) e accesso immediato alla slitta `ESP32-S3` / porta `USB-C` debug / `SGM2212`. |
| **Fondo** | **Interfaccia universale `8 × 8 stud`** compatibile con base fissa **B1** e futura base mobile **B2**, con vano `JST-XH 6-pin` integrato. |
