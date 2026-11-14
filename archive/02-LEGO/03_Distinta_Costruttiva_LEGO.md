# JARVIS LEGO BOT – FASE 3: Distinta Costruttiva LEGO (Indicativa)

**Nota importante:** Non vengono inventati codici pezzo proprietari; sono indicate esclusivamente tipologie e dimensioni standard LEGO System e LEGO Technic, con alternative costruttive qualora alcuni formati mancassero dalla tua collezione.

---

## 1. Elementi Strutturali LEGO Technic (Telaio Interno e Base)

| Tipologia Pezzo | Dimensione Indicativa | Qtà Stimata | Funzione | Alternative Costruttive |
|---|---|---|---|---|
| **Technic Brick con fori (1×N)** | 1×6, 1×8, 1×10, 1×12 | 12–16 | Perimetro base (predisposizione motori/ruote), colonne busto e foro microfono | Unire pezzi più corti (es. 1×4 + 1×6) bloccati con *Plate* sopra e sotto |
| **Technic Liftarm / Beam** | 1×7, 1×9, 1×11 (o 1×5) | 4–6 | Rinforzo interno vassoio estraibile e traverse supporto speaker | Sostituibili con *Plate 2×N* sovrapposte in doppio strato |
| **Technic Pin con frizione (neri)** | Standard 2L | 12–16 | Bloccaggio angoli telaio e slitta elettronica | Assali corti + bush, oppure incastro misto System/Technic |
| **Technic Pin senza frizione (grigi)** | Standard 2L | 2–4 | Fissaggio rapido a pressione dello sportello posteriore estraibile | Sostituibili con 2 *Hinge Brick/Plate* laterali |
| **Technic Axle (assale corto)** | 3L o 4L | 2–4 | Eventuale perno attuatore del pulsante fisico o bloccaggio vassoio | *Bar 3L/4L* o semplice *Plate* di spinta |

---

## 2. Mattoncini di Rivestimento LEGO System (Nero, Grigio Scuro, Azzurro/Ciano)

### 2.1 Struttura e Pareti (Nero & Grigio Scuro)
| Tipologia Pezzo | Dimensione Indicativa | Qtà Stimata | Colore Consigliato | Funzione |
|---|---|---|---|---|
| **Brick classici** | 1×2, 1×3, 1×4, 1×6 | 35–50 | Nero / Grigio Scuro | Pareti testa, collo e busto |
| **Brick angolari (Corner Brick)** | 2×2 corner | 4–8 | Nero / Grigio Scuro | Angoli puliti di testa e busto (sostituibili con 1×2 + 1×1 sfalsati) |
| **Plate classiche** | 1×2, 1×4, 2×4, 2×6, 2×8, 6×8 | 20–30 | Nero / Grigio Scuro | Piani di chiusura base, collo, tetto testa, sportello posteriore |
| **Slope (inclinati)** | 1×2 (30°/45°), 2×2, 2×3 | 6–10 | Nero | Smussatura superiore testa e profilo futuristico spalle |
| **Tile lisci (senza stud)** | 1×2, 1×4, 2×2 | 8–14 | Nero / Grigio Scuro | Finitura visiera frontale attorno all'OLED e sommità testa |
| **Grille Tile (griglie 1×2)** | 1×2 | 8–12 | Grigio Scuro / Nero | Griglia frontale altoparlante e feritoie di ventilazione passive |

### 2.2 Dettagli Futuristico-Cromatici (Azzurro / Ciano / Trans-Light Blue)
| Tipologia Pezzo | Dimensione Indicativa | Qtà Stimata | Colore Consigliato | Funzione |
|---|---|---|---|---|
| **Plate / Tile di accento** | 1×2, 1×4, 1×1 round | 8–12 | Azzurro (`Medium Azure`) o Ciano/Trans-Light Blue | Cornice laterale testa, cornice griglia speaker, linee estetiche sul petto |
| **Round Tile / Bottone** | 1×1 o 2×2 round | 1 | Azzurro / Trans-Light Blue | Tasto estetico sopra il pulsante fisico di attivazione (`GPIO 47`) |

---

## 3. Elementi di Fissaggio, Isolamento e Manutenzione (Non LEGO)

| Materiale | Quantità | Funzione |
|---|---|---|
| **Striscia di gommapiuma / neoprene sottile (3–5 mm)** | 1 piccolo ritaglio | Disaccoppiamento acustico INMP441 e tenuta antivibrazione posteriore per OLED e speaker (evita colla!) |
| **Elastici piccoli o fascette in velcro/nylon** | 2–4 | Fissaggio sicuro ma rimovibile di ESP32-S3 e MAX98357A sul vassoio interno LEGO |

---

## 4. Eventuali Supporti Stampabili in 3D (Solo Opzionali)

Il progetto è **100% realizzabile con soli mattoncini LEGO** + gommapiuma/elastici.  
Tuttavia, qualora disponessi di una stampante 3D (non obbligatoria), risultano utili al massimo **2 piccoli adattatori**:
1. **Cornice adattatore OLED 1,3" → 6×6 stud:** Mascherina sottile nera con fori compatibili con 4 stud LEGO per centrare al millimetro la finestra attiva dell'OLED 1,3". *(Alternativa LEGO: cornice costruita con Tile 1×4 e 1×2 + spessore posteriore in gommapiuma).*
2. **Anello supporto Speaker Ø 36/40 mm → 5×5 stud:** Anello piatto per centrare lo speaker circolare dentro il vano quadrato LEGO. *(Alternativa LEGO: 4 Brick/Plate angolari a contatto tangenziale sui 4 lati dello speaker + gommapiuma).*
