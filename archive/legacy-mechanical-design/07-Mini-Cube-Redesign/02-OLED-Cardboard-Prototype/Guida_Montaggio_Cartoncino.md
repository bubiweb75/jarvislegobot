# Guida di Montaggio — Kit di Prototipazione OLED in Cartoncino (Scala 1:1)

> [!CAUTION]
> **REGOLE DI SICUREZZA OBBLIGATORIE:**
> 1. Esegui **tutte** le prove con il display OLED **completamente scollegato dall'alimentazione** e dai cavi elettrici.
> 2. **NON applicare MAI colla o nastro adesivo direttamente sul display**, sul vetro, sul nastro flessibile (flex) inferiore o sui componenti SMD posteriori.
> 3. Il nastro adesivo di carta (tipo *masking tape*) va applicato **esclusivamente tra cartoncino e cartoncino** o sulle linguette verso le pareti interne LEGO.

---

## Materiale consigliato
- Stampante domestica A4 (impostazione **Scala 100% / Dimensione effettiva**).
- Cartoncino da `200–300 g/m²` (oppure carta comune incollata su cartoncino sottile tipo scatola cereali, spessore `~0,4–0,5 mm`).
- Taglierino di precisione (cutter) + righello metallico + tappetino da taglio (o forbicine).
- Righello millimetrato o calibro, nastro di carta (*masking tape*).

---

## Procedura Passo-Passo (10 Passaggi)

### 1. Stampa al 100% (Nessun Adattamento)
- Apri [JARVIS_OLED_Sagome_A4_1a1.pdf](JARVIS_OLED_Sagome_A4_1a1.pdf) (2 pagine A4).
- Nella finestra di stampa seleziona: **Dimensione effettiva / Scala personalizzata 100%**, **disattiva** *"Adatta alla pagina"* o *"Riduci alle dimensioni di stampa"*.

### 2. Verifica del Quadrato da `50 × 50 mm` e del Righello `100 mm`
- Prima di tagliare, misura con un righello su **entrambe** le pagine stampate:
  - il **quadrato di controllo `50,0 × 50,0 mm`** (tolleranza accettabile `±0,3 mm`);
  - il **righello di riferimento `100,0 mm`**.
- Se la misura è errata, ristampa correggendo la percentuale di scala nel driver della stampante.

### 3. Ritaglio delle Sagome
- **Linee continue (`—`):** TAGLIA con il cutter lungo il bordo.
- **Linee tratteggiate verdi (`- -`):** NON tagliare — incidi leggermente sul lato esterno con il dorso del cutter (cordonatura) per facilitare la piega a `90°`.
- **Linee blu punto-linea (`- · -`):** Riferimenti di centraggio (non tagliare).
- Ritaglia:
  - **A** (Cornice frontale `47,5 × 41,1 mm` + finestra interna `32,0 × 19,2 mm`);
  - **C** (`4×` distanziatori `47,5 × 41,1 mm` con finestra interna `37,0 × 30,0 mm`);
  - **D1 / D2** (Volti simulati `128×64` a riposo e in ascolto);
  - **B** (Culla posteriore pieghevole con apertura centrale `31,0 × 29,0 mm`, scasso `4 pin` superiore e scarico `flex` inferiore);
  - **E1 / E2** (Sagome PCB `36×34` e `35,4×33,5` per confronto rapido prima ancora di toccare il display reale).

### 4. Piegatura della Culla Posteriore (`B`) e della Cornice (`A`)
- **Cornice A:** Piega indietro a `90°` le due alette laterali da `6,5 mm`.
- **Culla B:** Piega in avanti a `90°` le pareti perimetrali alte `6,1 mm` attorno all'apertura centrale, poi piega verso l'esterno a `90°` le due **linguette di fissaggio `±2,5 mm`**.
- Verifica che lo **scasso superiore (`14 mm`)** e lo **scarico inferiore (`18 mm`)** siano completamente aperti.

### 5. Montaggio Provvisorio del Display (Senza Danneggiarlo)
- Prima confronta il tuo display Binghe fisico con le sagome **E1 (`36×34`)** ed **E2 (`35,4×33,5`)** per individuare quale variante hai in mano.
- Sovrapponi alla cornice **A** il numero desiderato di **distanziatori C** (`es. 4 strati di cartoncino da 0,45 mm = ~1,8 mm` di incasso; oppure `2` o `6` strati per provare incassi diversi), fissando gli strati di cartoncino tra loro sul retro con piccoli pezzi di nastro di carta.
- Appoggia il display reale (oppure la sagoma **D1/D2**) dentro le pareti della culla **B**, verificando che:
  - i pin superiori escano liberamente dallo **scasso `14 mm`**;
  - il flex inferiore resti libero nello **scarico `18 mm`**;
  - il retro della PCB appoggi solo lungo il bordo della culla (l'apertura `31×29 mm` lascia liberi i componenti SMD).

### 6. Centratura dell'Area Attiva nella Finestra
- Accosta il retro della cornice+distanziatori **A+C** davanti al vetro del display senza premere.
- Allinea i riferimenti di centraggio (`F1/F2`, `G1/G2`) fino a centrare l'area attiva (o la sagoma **D1/D2**) nella finestra `32,0 × 19,2 mm`.

### 7. Inserimento del Prototipo nel Corpo LEGO
- Apri temporaneamente la tasca frontale del Mini Cubo (rimuovendo i mattoncini centrali di `L3..L6` per ottenere il vano `6` stud × `13` plate `48,0 × 41,6 mm`, oppure appoggia la cornice sul frontale se stai provando a cubo chiuso).
- Inserisci la cornice **A+C** dal retro a filo della faccia anteriore e blocca provvisoriamente le linguette della culla **B** alle pareti LEGO interne con nastro di carta (solo sul cartoncino).

### 8. Verifica della Visibilità degli Occhi da Diverse Angolazioni
- Posiziona il Mini Cubo sulla scrivania alla normale distanza d'uso (`40–70 cm`).
- Osserva la sagoma **D1/D2** frontalmente e spostandoti lateralmente (`±15°`, `±25°`, `±35°`) e verticalmente, annotando a quale angolo i bordi della cornice iniziano a coprire gli occhi bianchi.
- Prova a togliere o aggiungere un distanziatore **C** per valutare l'effetto estetico di diversi incassi (`~1,0 / 1,8 / 2,7 mm`).

### 9. Controllo dello Spazio per i 4 Collegamenti Superiori
- Apri lo **sportello posteriore `3036` (`6×8`)**.
- Verifica visivamente e con un cavetto/connettore Dupont **scollegato** (senza alimentare nulla) lo spazio sopra i 4 pin (`GND, VCC, SCL, SDA`) davanti allo speaker `AS03604AR` sul tetto e verso la zona dell'ESP32-S3 (Layout C).

### 10. Documentazione con Fotografie e Misure
- Scatta 3 foto: (1) vista frontale centrata, (2) vista angolata a ~30° per visibilità occhi, (3) vista interna dallo sportello posteriore aperto.
- Compila [Checklist_Verifica_Fisica.md](Checklist_Verifica_Fisica.md) e annota le quote rilevate su [15_Scheda_Misurazione_OLED_Binghe.md](../15_Scheda_Misurazione_OLED_Binghe.md) prima di passare alla culla 3D definitiva.
