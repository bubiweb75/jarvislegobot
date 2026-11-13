# JARVIS LEGO BOT – FASE 3: Progetto Costruttivo, Alloggiamenti e Raffreddamento

---

## 1. Progetto Costruttivo LEGO (Technic Interno + System Esterno)

Il principio costruttivo separa nettamente **struttura portante** e **scocca estetica**:

### 1.1 Base (14 × 12 stud, h = 8 plate / ~25,6 mm)
- **Struttura interna Technic:** Anello perimetrale realizzato con *Technic Brick 1×N* (con fori per pin) collegati agli angoli da *Technic Beam / Liftarm* o piastre LEGO sopra/sotto.
- **Predisposizione futura motorizzazione:**
  - Sui lati destro e sinistro sono presenti almeno **4 fori Technic allineati** all'altezza del piano inferiore per montare in futuro due motori (es. motori LEGO o motoriduttori N20/TT con adattatore Technic) e gli assali delle ruote.
  - La parte centrale della base resta **vuota internamente** (area utile 10 × 8 stud, altezza ~16 mm) per ospitare un domani il driver motori (`TB6612FNG` / `DRV8833`) o una batteria, ed è chiusa sotto solo parzialmente da traverse così da fungere anche da **presa d'aria inferiore**.
- **Alternativa costruttiva:** Se non si hanno *Technic Brick 1×12/1×14*, si possono unire due *Technic Brick 1×6* + *1×8* bloccandoli sopra e sotto con *Plate 2×N* sfalsati (*overlapping*).

### 1.2 Busto (12 × 10 stud esterni | 10 × 8 stud / 80 × 64 mm interni, h = 10 brick / 96 mm)
- **Telaio interno Technic:** 4 colonne angolari con *Technic Brick* / *Brick 1×2* collegati in alto e in basso da due cornici rettangolari (10 × 8 stud).
- **Rivestimento esterno System:** Pareti in *Brick 1×N* neri e grigio scuro agganciati al telaio tramite stud laterali o incastro diretto tra le piastre di base e di chiusura superiore.
- **Sportello posteriore apribile (8 × 6 stud):** Realizzato su una *Plate 6×8* (o *4×8* + *2×8*) incernierata lateralmente con *Hinge Brick / Plate* oppure fissata a pressione morbida tramite **2–4 Technic Pin senza frizione (grigi)** per sfilarla completamente con un dito durante la manutenzione.
- **Alternativa costruttiva:** Se non si hanno cerniere LEGO, il fissaggio a **2 pin Technic grigi (senza frizione)** su un pannello posteriore è ancora più comodo, perché permette di togliere del tutto il pannello senza ingombri dietro al robot.

### 1.3 Collo (4 × 4 stud, h = 5 plate / 16 mm)
- Realizzato con una cornice di *Brick/Plate 1×2* e *1×4* che lascia un **condotto centrale libero di 2 × 2 stud (16 × 16 mm)**.
- Attraverso questo condotto passano i **7 fili flessibili 26 AWG** dalla testa al busto senza schiacciamenti.
- La testa si aggancia al collo tramite **4 stud superiori** (facilmente sfilabile verso l'alto per ispezioni o modifiche).

### 1.4 Testa (10 × 8 stud esterni | 8 × 6 stud / 64 × 48 mm interni, h = 7 brick / 67,2 mm)
- **Telaio interno:** Culla in *Plate* e *Brick 1×N* che lascia libero tutto il vano frontale di `48 × 48 mm` per OLED e microfono.
- **Pannello frontale:** Cornice nera attorno all'area attiva del display OLED 1,3". Per evitare riflessi e non attenuare il microfono, **non coprire il foro del microfono** e lasciare l'OLED a filo dietro una cornice in *Tile* lisci.
- **Calotta superiore smontabile:** Chiusura superiore in *Plate* + *Slope* neri fissata su 4–6 stud per poter aprire la testa dall'alto se necessario.

---

## 2. Alloggiamento Elettronico (Coerente al 100% con FASE 2)

Nessuna modifica al pinout (`GPIO 4/5/6`, `7/15/16`, `41/42`, `47`, `GPIO 39/40` disabilitati, `GPIO 35–37` riservati PSRAM).

| Componente (da BOM FASE 2) | Dimensioni | Posizione nel Robot | Fissaggio Smontabile |
|---|---|---|---|
| **Display OLED 1,3" I2C** | ~35,5 × 33,5 × 4 mm | **Testa (fronte)** | Incastrato in una sede 5 × 5 stud dietro cornice di *Tile*; bloccato posteriormente da due *Bracket* / *Plate* rimovibili con spessore in gommapiuma morbida (niente colla). |
| **Microfono INMP441** | Ø ~14 mm | **Testa (fronte-basso)** | Appoggiato dietro un foro passante di un *Technic Brick 1×2* con foro Ø 4,8 mm, isolato dalle vibrazioni con un piccolo anello di spugna/gommapiuma. |
| **ESP32-S3-DevKitC-1 N16R8** | ~63 × 25,4 × 13 mm | **Busto (retro-verticale)** | Montata verticalmente su **slitta/vassoio estraibile** (o su mini breadboard 170 pt / millefori fissata a una *Plate 4×8* con elastici o clip Technic), con **porta USB-C accessibile** dal basso/retro e **`SGM2212` rivolto verso lo sportello posteriore**. Antenna PCB rivolta verso l'alto. |
| **Altoparlante 4 Ω / 3 W** | Ø 36–40 mm, prof. 15–20 mm | **Busto (fronte-basso)** | Alloggiato in un vano 5 × 5 stud dietro *Grille Tile 1×2*, bloccato da due traverse posteriori in LEGO (con striscia di gommapiuma antivibrazione). Magnete rivolto verso l'interno ma distanziato ≥ 15 mm dall'ESP32. |
| **MAX98357A + `C1`/`C2`** | ~19 × 18 × 3 mm | **Busto (zona inferiore)** | Montato sul vassoio modulare vicino allo speaker e al nodo di alimentazione 5 V. |
| **Breakout USB-C 5 V** | ~15 × 12 × 4 mm | **Busto (retro-basso)** | Fissato in una sede da 2 × 2 stud allineata all'apertura posteriore `2×1 stud` per l'ingresso del cavo di alimentazione 5 V / ≥ 2 A. |
| **Pulsante Meccanico NO (`GPIO 47`)** | 6×6 mm o Ø 12 mm | **Busto (spalla destra o petto alto)** | Inserito in un foro *Technic* o sede dedicata con attuatore realizzato tramite un perno/bottone LEGO (*Round Tile 1×1* o *1×2* su *Technic Pin*) che preme il pulsante sottostante. |
| **Prototipo su Breadboard** | 830 pt (banco) / 170 pt (interno) | **Banco → Vassoio interno** | La breadboard **830 punti** resta sul banco per i collaudi di FASE 4; per il montaggio nel robot si usa una **mini breadboard 170 pt (`45×35 mm`)** o basetta con connettori **JST-XH / DuPont bloccati** sul vassoio estraibile. |

---

## 3. Raffreddamento Passivo e Manutenzione (Verifica FASE 2)

In conformità alla **Soluzione C** approvata nella FASE 2 (mantenimento LDO `SGM2212-3.3XKC3G/TR` onboard):
1. **Circuito convettivo verticale (effetto camino):**
   - **Ingresso aria fresca (basso):** 2 aperture con *Grille Tile* / fori Technic sui lati inferiori del busto e attraverso il vano aperto della base.
   - **Uscita aria calda (alto):** 2 feritoie posteriori nella parte alta del busto (sopra la zona ESP32-S3) tramite *Grille Tile 1×2* o *Technic Brick* aperti.
2. **Nessuna chiusura ermetica:** Il vano elettronico non è sigillato; la distanza tra i componenti interni garantisce il passaggio d'aria attorno all'ESP32-S3.
3. **Accesso diretto al regolatore `SGM2212`:** Aprendo lo **sportello posteriore**, la faccia superiore della ESP32-S3-DevKitC-1 (dove risiede l'integrato `U2` `SGM2212` in package `SOT-223-3`) rimane **direttamente visibile e accessibile** per applicare una sonda termica / termometro IR durante i test di stress della FASE 4 senza dover smontare la scocca.
