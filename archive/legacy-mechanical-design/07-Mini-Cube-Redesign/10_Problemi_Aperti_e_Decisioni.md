# 10 – Problemi Aperti, Verifiche Richieste e Decisioni per Passare alla FASE B

---

## 1. Criticità e Misure Commerciali da Confermare

1. **Disegno dimensionale esatto dell'OLED `1,3" SH1106 I2C`:**
   - In FASE A è stato utilizzato un ingombro parametrico prudenziale (`36,0 × 34,0 × 11,0 mm` inclusi pin 90°/cavi).
   - Prima di modellare in dettaglio la tasca frontale in FASE B, occorre verificare sul modulo commerciale acquistato/selezionato: dimensioni esatte della PCB (es. `35,4 × 33,5 mm`), posizione dei 4 fori di fissaggio e lato di uscita del connettore a 4 pin (`alto` vs `basso`).
2. **Profondità reale dello Speaker `4 Ω / 3 W`:**
   - Verificare se lo speaker scelto ha profondità `20 mm` (**Opzione A**, compatibile con Mini Cubo `80 × 80 × 96 mm`) oppure se è disponibile uno speaker slim `Ø 36 × 14–15 mm` (**Opzione B**, che offre ancora più margine interno o consente `89,6 mm`).
3. **Connettori a profilo basso obbligatori:**
   - Dentro `64 × 64 mm` netti non è possibile usare connettori DuPont dritti lunghi sull'`ESP32-S3` e sull'`OLED`. Sono richiesti header a **90°** oppure saldatura diretta compatta con guaina termorestringente e connettori inline `JST` lungo i cavi per la manutenzione.
4. **Cancellazione eco software (AEC):**
   - La separazione fisica `INMP441` (fianco) / `Speaker` (tetto) non garantisce da sola l'assenza di eco in un volume compatto da `80 mm`; andrà validata con firmware AEC / barge-in e test acustici reali.
5. **Elementi non LEGO da dichiarare esplicitamente (se necessari):**
   - Spessori in **gommapiuma/EVA** per isolamento acustico `INMP441` e guarnizione speaker.
   - Eventuali **staffe/distanziali stampati 3D** per fissare la PCB OLED o la culla speaker qualora i soli mattoncini LEGO non offrissero tenuta sufficiente (da valutare nella modellazione di FASE B senza mai spacciarli per pezzi LEGO).
   - Adattatori `N20` su futura base mobile **B2** (`giunti D 3 mm → 4519` e `staffe motore`), tuttora da progettare.
6. **Inventario LEGO reale dell'utente:** da verificare dopo la generazione della distinta in FASE B.

---

## 2. Stato Finale della Progettazione Digitale (FASE C — Variante C+B)

| Parametro | Stato / Valore |
|---|---|
| **Formato Corpo A** | **Mini Cubo `10 × 10 stud × 10 brick` (`80,0 × 80,0 × 96,0 mm`)** — `98` pezzi in `jarvis_lego_bot_mini_cube.mpd` (angoli `11477` + barre basse `3069b` Azure) |
| **Base Fissa B1** | **`12 × 12 stud` (`96 × 96 mm`)** con finitura liscia perimetrale, `22` pezzi, altezza totale assiemata **`99,2 mm`** |
| **Layout Interno** | **Layout C (`ESP32-S3` verticale decentrato posteriore-destro)** — `0` collisioni vs LEGO/elettronica |
| **Display Frontale** | **OLED `1,3" SH1106` I2C** — **supporto PARAMETRICO (`36×34×11 mm`)**, da finalizzare dopo misura PCB commerciale |
| **Speaker sul Tetto** | **PUI Audio `AS03604AR` (`Ø 36 × 8,8 mm`, `4 Ω`, `3 W`)** sotto griglia liscia `3× 4162` (fallback: `Ø 40 × 20 mm`) |
| **Validazione CAD finale** | `0` collisioni su mesh `.dat` Studio 2.0 in Python; **validazione GUI finale in BrickLink Studio 2.0 su PC Windows utente** |

---

## 3. Verifiche Ancora Aperte (Prima di Acquisti o Costruzione)

1. **Conferma visiva in BrickLink Studio 2.0 GUI** su Windows importando [`jarvis_lego_bot_mini_cube.mpd`](jarvis_lego_bot_mini_cube.mpd).
2. **Misura reale del modulo OLED `1,3" SH1106` commerciale** (PCB, posizione area attiva e lato header 4 pin) prima di chiudere il supporto frontale.
3. **Conferma reperibilità `PUI Audio AS03604AR`** (o scelta fallback `Ø 40 × 20 mm`) e progettazione guarnizione EVA / clip non-LEGO di ritenuta sotto tetto.
4. **Inventario LEGO reale utente** su [`07_Distinta_LEGO.md`](07_Distinta_LEGO.md) (`108` pezzi).
5. **Prove fisiche su prototipo** (AEC software su `INMP441`, stabilità B1, accessibilità `GPIO 47`, temperatura `SGM2212`) e progettazione successiva di **B2**.

*(Nessun acquisto, cablaggio o costruzione fisica è stato avviato).*
