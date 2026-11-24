# 09 — Eyes 3.0: Baseline Grafica Ufficiale e Golden Standard

> **JARVIS Robotics Platform** — Specifiche della Baseline Grafica Eyes 3.0  
> **Fase:** RP-01  
> **Stato:** Approvato per Progettazione  

---

## 1. Il Ruolo di Eyes 3.0: Golden Baseline Assoluta

Un vincolo inderogabile della **JARVIS Robotics Platform** impone di **non riprogettare una grafica semplificata o approssimativa** per JARVIS.

Il punto di riferimento ufficiale della piattaforma è l'implementazione grafica reale, collaudata ed entusiasticamente approvata su hardware fisico: **Eyes 3.0 (*Organic Visor Companion*)**, documentata e verificata nei sorgenti:
- `04-Firmware/jarvis-desk-buddy/include/eye_engine.h`
- `04-Firmware/jarvis-desk-buddy/src/eye_engine.cpp`
- `04-Firmware/arduino-hw-test/jarvis_eyes3_hw_test/`
- `04-Firmware/jarvis-desk-buddy-sim/eye_engine.py`

La prima skin ufficiale della piattaforma prende la denominazione formale di:
> **`JARVIS Original Premium — Organic Visor Companion`**

Nessuna nuova skin o simulazione potrà sostituire questa estetica con forme ovali generiche o rettangoli primitivi. Tutte le future skin dovranno raggiungere un livello qualitativo e dinamico pienamente equivalente.

---

## 2. Specifiche Geometriche e Parametriche Verificate

L'analisi del codice C++ reale ha evidenziato con precisione i parametri geometrici di riferimento (risolvendo le discrepanze presenti in vecchi documenti storici):

| Parametro Geometrico | Valore Codificato nel Firmware | Descrizione e Ruolo Visivo |
|---|---|---|
| **Larghezza Occhio Base (`width`)** | **`38,0 px`** | Dimensione orizzontale di ciascun occhio nello stato `NEUTRAL` (nota: documenti storici indicavano 30 px; il valore reale è 38 px). |
| **Altezza Occhio Base (`height`)** | **`38,0 px`** | Dimensione verticale di ciascun occhio nello stato `NEUTRAL` (nota: documenti storici indicavano 32 px; il valore reale è 38 px). |
| **Raggio di Curvatura (`corner_radius`)** | **`11,0 px`** | Raggio dei quattro raccordi d'angolo della capsula. |
| **Esponente Geometrico (`shape_power`)** | **`2,6`** | Esponente della superellisse organica (valore > 2.0 che conferisce l'aspetto a capsula moderna con lati tesi ma dolcemente curvati). |
| **Fattore di Conicità (`taper`)** | **`0,10`** | Leggera rastremazione verticale che dona tridimensionalità e naturalezza allo sguardo. |
| **Spaziatura Occhi (`spacing_px`)** | **`16 px`** | Distanza fissa tra il bordo interno dell'occhio sinistro e dell'occhio destro. |
| **Raggio Pupilla Base (`pupil_radius`)** | **`7,0 px`** | Pupilla scura interna contrastata rispetto alla sclera luminosa. |
| **Sopracciglia Base (`brow_offset`)** | **`4,0 px`** | Distanza verticale del sopracciglio dall'apice superiore dell'occhio. |
| **Arco Sopracciglia (`brow_arch`)** | **`2,2`** | Curvatura parabolica del sopracciglio. |
| **Inclinazione Sopracciglia (`brow_tilt`)** | **`0,0 px`** | Inclinazione neutra in stato di riposo (varia da -4.5 a +4.5 nelle espressioni emotive). |

---

## 3. Motore Dinamico e Pipeline di Rendering

### 3.1 Interpolazione Esponenziale Indipendente dal Frame Rate
Il movimento tra le espressioni e durante le saccadi dello sguardo non fa uso di semplici incrementi lineari, ma di un'equazione differenziale a decadimento esponenziale calcolata in funzione del tempo reale trascorso (`dt_sec`):

$$\alpha = 1.0 - e^{-\text{rate} \cdot \Delta t}$$
$$\text{valore}_{\text{attuale}} = \text{valore}_{\text{attuale}} + (\text{target} - \text{valore}_{\text{attuale}}) \cdot \alpha$$

Questo garantisce che la fluidità visiva rimanga assolutamente identica sia a 30 FPS su ESP32-S3 sia a 60 FPS nel simulatore web/desktop, con transizioni morbide e naturali prive di scatti.

### 3.2 Natural Gaze Engine (Sguardo Naturale e Micro-Saccadi)
Lo sguardo non è mai statico o robotico:
- **Micro-saccadi discrete:** Spostamenti involontari casuali di ampiezza minima (±1..3 pixel) ogni 1,2–2,5 secondi.
- **Saccadi esplorative:** Spostamenti coordinati dello sguardo in tutte le direzioni (-11..+11 pixel in X, -6..+6 pixel in Y) con bias di ritorno naturale al centro.
- **Stabilità in Ascolto:** Quando il robot entra in `LISTENING`, le saccadi ampie vengono automaticamente soppresse per mantenere il contatto visivo concentrato verso l'utente.

### 3.3 Advanced Blink Engine (Ammiccamento Avanzato)
Il battito palpebrale è gestito da una macchina a stati interna a 4 fasi non bloccanti:
1. `kOpen`: Occhio completamente aperto; calcolo del tempo al prossimo ammiccamento con jitter pseudocasuale deterministico (PRNG xorshift32).
2. `kClosing`: Chiusura rapida (rate elevato: 18.0 / sec).
3. `kHoldClosed`: Mantenimento della palpebra chiusa per 42 ms (130 ms se lo stato è `SLEEPY`).
4. `kOpening`: Riapertura progressiva con curva organica di *ease-out*.
- **Doppio Battito Spontaneo (`double_blink`):** Probabilità del 20% in stato `NEUTRAL`/`HAPPY` di generare un secondo battito rapido immediatamente dopo il primo.

### 3.4 Micro-Expressions Engine (Micro-Espressioni Contestuali)
Unico nel suo genere, il motore inietta spontaneamente micro-espressioni emotive transitorie (durata 300–580 ms) senza alterare l'espressione di base:
- `kBrowRaise`: Sollevamento asimmetrico di un sopracciglio (attenzione/curiosità).
- `kSideGlance`: Sguardo fugace laterale e ritorno al centro.
- `kQuickWink`: Occhiolino rapido dell'occhio destro.
- `kEyeSmile`: Chiusura parziale della palpebra inferiore (micro-sorriso).
- `kPupilPulse`: Leggera dilatazione della pupilla (+1,5 px) per simulare focalizzazione.

---

## 4. Profili di Personalità Visiva (Visual Profiles)

Il comportamento grafico supporta 3 profili visivi formalizzati:

| Profilo Visivo | `SpeedScale` | `GazeFreq` | `MicroFreq` | `BlinkFreq` | Probabilità Double-Blink | Sensazione Visiva |
|---|---|---|---|---|---|---|
| **`CALM`** | `0,72` | `0,65` | `0,45` | `0,80` | `8%` | Rilassato, discreto, ideale per scrivanie silenziose o notte. |
| **`LIVELY`** *(Default)* | `1,00` | `1,00` | `1,00` | `1,00` | `20%` | "Amichetto Vivace", equilibrato, empatico, reattivo. |
| **`PLAYFUL`** | `1,22` | `1,35` | `1,65` | `1,15` | `28%` | Estremamente espressivo, vivace, frequenti occhiolini e micro-sorrisi. |

---

## 5. Criteri di Equivalenza e Accettazione

Perché una skin o un simulatore della piattaforma sia certificato conforme a Eyes 3.0, deve superare la seguente matrice di equivalenza visiva:

1. **Parità Geometrica Pixel-Perfect:** Le forme nello stato `NEUTRAL` devono sovrapporsi al 100% con il rendering dell'algoritmo C++ su griglia 128×64.
2. **Parità di Frame Rate:** Rendering a **30 FPS stabili** (intervallo frame ≤ 33 ms) con tempo di calcolo framebuffer ≤ 4 ms su ESP32-S3 @ 240 MHz.
3. **Parità di Reattività:** Transizioni tra espressioni fluide e interrompibili istantaneamente all'arrivo di nuovi eventi o tocchi.
