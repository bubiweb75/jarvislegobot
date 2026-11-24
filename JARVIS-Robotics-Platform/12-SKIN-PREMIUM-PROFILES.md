# 12 — Le Cinque Identità Dimostrative Iniziali

> **JARVIS Robotics Platform** — Specifiche delle Cinque Skin Premium di Lancio  
> **Fase:** RP-01  
> **Stato:** Approvato per Progettazione  

---

## 1. Visione d'Insieme delle Cinque Identità

Per inaugurare la piattaforma e dimostrare la potenza espressiva dello Skin Engine, sono state progettate **cinque identità dimostrative complete**.

Ciascuna identità rispetta rigorosamente i canoni di qualità e i vincoli ingegneristici della piattaforma:
1. **Rappresentazione Esclusivamente Oculare:** Nessun elemento facciale estraneo (bocca, naso, baffi o guance) viene disegnato sullo schermo.
2. **Copertura Integrale delle 14 Espressioni:** Ogni profilo dispone della propria interpretazione grafica di tutte le 14 espressioni di Eyes 3.0 (70 combinazioni grafiche fondamentali, escluse micro-espressioni).
3. **Qualità Visiva Paritetica:** Tutte le skin mantengono la ricchezza di transizione, il Natural Gaze e l'Advanced Blink della baseline originale di JARVIS.

```
+-----------------------------------------------------------------------------------------+
|                              LE CINQUE IDENTITÀ PREMIUM                                 |
+---------------------+-------------------+-------------------+-------------------+-------+
| 1. JARVIS           | 2. EVA            | 3. NOVA           | 4. TARS           | 5. NEKO
| Original Companion  | Elegant & Soft    | Advanced Ocular HUD| Geometric Minimal | Feline Eyes
+---------------------+-------------------+-------------------+-------------------+-------+
```

---

## 2. Profilo 1: JARVIS — Original Premium

Il punto di riferimento e l'identità nativa della piattaforma.

- **Filosofia Visiva:** L'estetica collaudata *Organic Visor Companion*. Linee sobrie, moderne e rassicuranti.
- **Geometria Oculare:** Superellissi organiche (38×38 px, `shape_power = 2,6`, `taper = 0,10`, raggio 11 px, spaziatura 16 px). Pupille scure centrate contrastate (raggio 7,0 px), catchlight doppi 2×2 px, sopracciglia curve integrate.
- **Dinamica Visiva:** Profilo `LIVELY` di default. Transizioni bilanciate, micro-saccadi coordinate, double-blink spontaneo (20%).
- **Voce Predefinita:** *Piper Riccardo* (`it_IT-riccardo-x_low.onnx`, 16 kHz mono, velocità 1.00×, pitch +5 st, profilo DSP Profile B per massima intelligibilità).
- **Personalità:** Assistente brillante, professionale, rassicurante e cordiale.
- **Wake Word Ufficiale:** `"Hey Jarvis"` (modello `hey_jarvis_v2.tflite` INT8 su microWakeWord).

---

## 3. Profilo 2: EVA — Elegant

Identità raffinata, delicata, calda ed empatica.

- **Filosofia Visiva:** Geometrie morbide e sinuose con accenti delicati.
- **Geometria Oculare:**
  - Bulbo oculare ad asola/ovale organico affusolato (36×36 px, raggio 14 px, `shape_power = 2,2`).
  - Leggera inclinazione convergente verso il basso (angolo 3,5°).
  - Ciglia stilizzate sottili (2 tratti curvi continui sull'angolo esterno superiore dell'occhio).
  - Palpebre morbide a doppia curvatura; riflessi di luce ovali sovrapposti (catchlight asimmetrici 3×2 px).
- **Dinamica Visiva:** Movimenti fluidi e controllati, ammiccamento lento e aggraziato (profilo `CALM` con velocità 0.85×), frequenti micro-sorrisi (`kEyeSmile`).
- **Interpretazione Espressioni Chiave:**
  - `HAPPY`: Archi sottili doppi con ciglia sollevate verso l'esterno.
  - `SHY`: Occhi leggermente socchiusi e reclinati con ammiccamento rapido.
  - `LOVE`: Cuori allungati eleganti con contorno sottile.
- **Voce Consigliata:** Femminile calda e melodica (es. Piper *Paola*).
- **Personalità:** Empatica, comprensiva, attenta al benessere dell'utente, dolce ed incoraggiante.
- **Wake Word Proposta:** `"Hey Eva"`.

---

## 4. Profilo 3: NOVA — Advanced Ocular HUD

Identità tecnologica, futuristica, scientifica e dinamica.

- **Filosofia Visiva:** Estetica da interfaccia olografica avanzata integrata esclusivamente all'interno dell'occhio.
- **Geometria Oculare:**
  - Occhi circolari/ottagonali smussati (diametro 38 px).
  - Anello perimetrale sottile concentrico con micro-fessure (reticolo ottico graduato).
  - Pupilla dinamica segmentata in 4 settori che pulsano leggermente con il carico computazionale.
  - Linee di scansione orizzontali interne che si attivano durante `THINKING`.
- **Dinamica Visiva:** Transizioni rapide, saccadi scattanti e precise, ammiccamento tecnologico con contrazione istantanea del diaframma dell'iride.
- **Interpretazione Espressioni Chiave:**
  - `LISTENING`: L'anello esterno si espande ed esegue una rotazione fluida.
  - `THINKING`: Linea di scansione verticale che attraversa la pupilla da sinistra a destra.
  - `SURPRISED`: Flash istantaneo a schermo invertito con espansione istantanea dell'anello HUD.
- **Voce Consigliata:** Voce chiara, cristallina, moderna e naturale a tonalità neutra.
- **Personalità:** Analitica, curiosa, appassionata di scienza e tecnologia, efficiente e proattiva.
- **Wake Word Proposta:** `"Hey Nova"`.

---

## 5. Profilo 4: TARS — Geometric Minimal

Identità pragmatica, geometrica, solida e monolitica.

- **Filosofia Visiva:** Minimalismo geometrico ispirato all'ingegneria spaziale.
- **Geometria Oculare:**
  - Occhi rettangolari evoluti (40×32 px, `corner_radius = 4 px`, `shape_power = 4,0`).
  - Maschere angolari a 45° per palpebre superiori e inferiori.
  - Pupille rettangolari ad alto contrasto (8×14 px) che scorrono su guide orizzontali.
- **Dinamica Visiva:** Movimenti cartesiani netti, transizioni meccaniche sofisticate (easing cubico), assenza totale di movimenti casuali o oscillazioni organiche.
- **Interpretazione Espressioni Chiave:**
  - `HAPPY`: Occhi che si dividono in due segmenti orizzontali paralleli stilizzati.
  - `THINKING`: La pupilla rettangolare si muove a impulsi discreti lungo il bordo superiore.
  - `MISCHIEVOUS`: Taglio diagonale a 45° della palpebra superiore, simulando uno sguardo tagliente e ironico.
- **Voce Consigliata:** Maschile profonda, ferma, controllata e scandita.
- **Personalità:** Pragmatica, asciutta, dotata di umorismo sarcastico intelligente e logica inappuntabile.
- **Wake Word Proposta:** `"Hey Tars"`.

---

## 6. Profilo 5: NEKO — Feline Robotic

Identità ispirata all'etologia e all'espressività dei felini.

- **Filosofia Visiva:** La natura felina è evocata **esclusivamente attraverso la forma e il moto degli occhi**.
- **Vincolo Invalicabile:** Nessun baffo, naso o bocca disegnati sul display. L'eventuale scocca fisica (in stampa 3D o LEGO) può integrare orecchie sagomate esterne, ma il display rimane dedicato unicamente agli occhi.
- **Geometria Oculare:**
  - Occhi a mandorla organici leggermente inclinati verso l'alto (38×32 px).
  - Pupille verticali a fessura ellittica (*slit pupils*), con larghezza dinamica (da 2 px a riposo fino a 14 px dilatate al buio o durante la caccia/ascolto).
  - Doppio catchlight rotondo luminoso posizionato in alto a sinistra.
- **Dinamica Visiva:** Movimenti oculari curiosi, saccadi improvvise seguite da fissazione prolungata, ammiccamento lento e rilassato (*slow blink* felino che comunica affetto).
- **Interpretazione Espressioni Chiave:**
  - `LISTENING`: Pupille istantaneamente spalancate a cerchio nero quasi totale (14 px).
  - `HAPPY`: Archi felini rovesciati con palpebre socchiuse e ammiccamento lento.
  - `SLEEPY`: Palpebre pesanti che scendono morbidamente, pupilla sottilissima a filo di luce.
- **Effetti Acustici Opzionali:** Modulo sonoro con fusa continue a basso volume durante le coccole al tocco (TOUCH_LONG) e discreti miagolii di benvenuto. Gli effetti sonori sono completamente disattivabili e non interferiscono mai con il microfono I2S o con il TTS.
- **Voce Consigliata:** Voce femminile giovane, dolce, squillante e giocosa.
- **Personalità:** Curiosa, vivace, indipendente, affettuosa a tratti, amante del gioco e delle scoperte.
- **Wake Word Proposta:** `"Hey Neko"`.

---

## 7. Matrice Riassuntiva delle 5 Identità di Lancio

| Identità | Stile Oculare | Forma Pupilla | Profilo Visivo | Voce Indicativa | Wake Word | Tratto Distintivo |
|---|---|---|---|---|---|---|
| **JARVIS** | Superellisse organica 38×38 | Rotonda 7 px + catchlight | `LIVELY` (1.00×) | Riccardo (WSOLA 1.00×) | *Hey Jarvis* | Riferimento ufficiale, zero regressioni |
| **EVA** | Ovale morbido con ciglia | Ovale morbido + riflessi | `CALM` (0.85×) | Paola / Femminile dolce | *Hey Eva* | Dolcezza, empatia, eleganza |
| **NOVA** | Circolare HUD tecnologico | Segmentata a quadranti | `LIVELY` (1.10×) | Neutra / Sintetica chiara | *Hey Nova* | Reticoli e anelli HUD nell'occhio |
| **TARS** | Rettangolare geometrico | Rettangolare 8×14 px | `PLAYFUL` (meccanico) | Maschile profonda | *Hey Tars* | Minimalismo, precisione cartesiana |
| **NEKO** | Mandorla felina | Fessura verticale dinamica | `PLAYFUL` (1.25×) | Giocosa / Squillante | *Hey Neko* | Pupille dilatabili, slow blink felino |
