# 04 – Studio OLED 1,3" SH1106, Speaker sul Tetto e Microfono INMP441

---

## 1. Display OLED `1,3" SH1106` (Requisito Vincolante)

> **Vincolo:** Non sostituire con `0,96"`. Nessun pixel dell'area attiva deve essere coperto dalla cornice LEGO.

### Analisi dimensionale e meccanica
- **Area attiva effettiva (`1,3"` `128×64`):** `~29,42 × 14,70 mm`.
- **Ingombro PCB commerciale tipico (parametrico prudenziale fino a verifica scheda fisica):**
  - Larghezza PCB: **`~35,5 mm`** (parametrico `36,0 mm`).
  - Altezza PCB: **`~33,5 mm`** (parametrico `34,0 mm`).
  - Spessore modulo (vetro + PCB): **`~4,0 mm`**.
  - Fori di fissaggio: 4× fori agli angoli (`Ø ~2,0–2,5 mm`, interasse tipico `~30 × 28 mm`, variabile per fornitore).
  - Connettore 4 pin (`VCC, GND, SCL, SDA`): tipicamente sul bordo **superiore** della PCB (passo `2,54 mm`).
- **Soluzione di montaggio nel Mini Cubo:**
  - Finestra frontale netta **`4 × 2 brick` (`32,0 × 19,2 mm`)** → supera l'area attiva (`29,42 × 14,70 mm`) lasciando **`~1,3 mm` di margine per lato in X** e **`~2,2 mm` sopra/sotto in Y**, garantendo visibilità totale di tutti i `128 × 64` pixel.
  - Dietro la finestra (`8,0 mm` spessore parete), si ricava una tasca interna larga `6 stud` (`48 mm`) con battuta frontale in *Plate/Tile* e **header a 90°** (o cavi `26 AWG` saldati a basso profilo rivolti verso il basso/lato), mantenendo lo spessore totale entro **`~10–11 mm`** dalla faccia esterna.
  - Sostituibilità: sfilabile dal retro rimuovendo la spugnetta/staffa di pressione posteriore senza smontare le pareti portanti.
- **Funzioni software future (non implementate in FASE A):**
  1. Occhi a riposo (`idle`).
  2. Occhi animati durante l'ascolto.
  3. Animazione di elaborazione (`thinking`).
  4. Espressione vocale sincronizzata (`speaking`).
  5. Stato connessione Wi-Fi / backend.
  6. Errori e notifiche.

> **Verifica aperta:** prima di modellare i supporti definitivi in FASE B, confermare dimensioni esatte della PCB, posizione fori e lato del connettore 4 pin del modulo `SH1106 1,3"` effettivamente scelto.

---

## 2. Valutazione Acustica e Meccanica dello Speaker sul Tetto

### Confronto delle tre opzioni richieste

| Criterio | **Opzione A: Speaker superiore `Ø 40 × 20 mm`** | **Opzione B: Speaker superiore compatto (`Ø 32–36 × 12–15 mm`, 4 Ω / 3 W)** | **Opzione C: Speaker frontale (solo fallback)** |
|---|---|---|---|
| **Ingombro nel Mini Cubo** | `Ø 40 × 22,5 mm` (con guarnizione); richiede **`H = 96 mm`** e decentramento in **Layout C** | `Ø 32–36 × 15–17 mm`; consente eventualmente **`H = 89,6–96 mm`** con ampio margine | Sottrae `48×48 mm` al frontale; **incompatibile** con volto `OLED 1,3"` su `80×90 mm` |
| **Qualità audio attesa** *(non misurata)* | Migliore resa sui medio-bassi grazie al diametro `40 mm` | Buona intelligibilità vocale; leggera riduzione sui bassi rispetto al `40 mm` | Diretta verso l'utente, ma corpo costretto a crescere in altezza (`>120 mm`) |
| **Facilità di fissaggio** | Buona su anello/culla LEGO + guarnizione morbida sotto il tetto | Ottima: più spazio per anello antivibrazione e passaggio cavi | Facile (SNOT frontale), ma sacrifica l'estetica del volto |
| **Effetti sulla compattezza** | Compatibile con `80 × 80 × 96 mm` (`Layout C`) | Massima compattezza (`≤ 90–96 mm`) | **Negativo:** costringe a tornare a una torre |
| **Rischio di vibrazioni** | Medio-basso se isolato con anello in EVA/gommapiuma e zero contatto griglia-cono | Basso (meno massa mobile e più spazio per isolamento) | Medio (risonanza su pannello SNOT frontale) |
| **Separazione dal microfono** | **Buona** se `INMP441` è sul fianco opposto con anello fonoisolante | **Ottima** (maggiore distanza relativa nel tetto) | Buona in verticale, ma peggiora l'altezza |
| **Camera acustica** | Semiaperta verso l'interno (`~80–120 cm³` utili nel quadrante SX) con parete divisoria morbida verso `ESP32-S3` | Semiaperta `~100–140 cm³` | Chiusa anteriore (come vecchio progetto) |

**Verifica commerciale eseguita in FASE B (Opzione B):**
- **Componente commerciale individuato:** **PUI Audio `AS03604AR`** *(speaker dinamico rotondo ultra-compatto)*:
  - **Diametro:** `36,0 mm ± 0,2 mm`
  - **Profondità reale:** **`8,8 mm ± 0,2 mm`** (`~9,1 mm` max da datasheet — ben inferiore al limite `≤ 15 mm`)
  - **Impedenza / Potenza:** **`4 Ω ± 15%`**, **`3,0 W` nominali (`4,0 W` max)** — compatibile con `MAX98357A` a `5 V`
  - **Prestazioni dichiarate:** `88 dB SPL` (`1 W / 0,5 m`), frequenza di risonanza `f0 = 180 Hz ± 20%`, `THD < 5%` a `230 Hz / 3 W`
  - **Fissaggio richiesto:** telaio tondo nudo (richiede anello/guarnizione in gomma EVA `2 mm` + clip/battuta inferiore non-LEGO sotto il telaio tetto `6×6` stud, senza pressione sul cono).
- **Alternativa compatta analizzata:** **Visaton `BF 32` (`4 Ω`, Art. 2243)** (`32 × 32 mm`, profondità `11–15 mm`, `2 W` RMS / `5 W` max, `78 dB 1W/1m`) — scartata rispetto a `AS03604AR` per potenza nominale inferiore (`2 W` vs `3 W`) e sensibilità più bassa.
- **Fallback conservato:** **Opzione A (`Ø 40 × 20 mm`)** resta documentata come alternativa nel caso `AS03604AR` non fosse reperibile.

### Requisiti costruttivi del tetto speaker
- **Griglia:** *Tile Grille `2412b`* o *Plate modificati* fissati su cornice perimetrale robusta `10×10` (nessuna flessione sul bordo), con **luce libera ≥ 2,5–3,0 mm sopra la sospensione del cono** (pressione zero sul cono).
- **Supporto e antivibrazione:** anello/guarnizione in EVA o gommapiuma (`2 mm`) tra flangia speaker e cornice superiore; staffetta o culla inferiore rimovibile (oppure fissaggio integrato nel coperchio superiore removibile).
- **Rimozione per manutenzione:** il gruppo tetto (cornice + griglia + speaker) si sfila verso l'alto grazie a `4 stud` di ritenuta moderata o pin senza frizione, con cavetto speaker dotato di connettore `JST-XH 2-pin` inline.

---

## 3. Microfono `INMP441` e Gestione Audio

- **Posizionamento raccomandato:** sul **fianco destro alto** (o lato opposto al centro speaker, vicino all'angolo anteriore-superiore), dietro un **`Technic Brick 1×2 (3700)`** con foro acustico `Ø 4,8 mm` diretto verso l'esterno.
- **Isolamento meccanico e acustico:**
  - Il breakout `INMP441` (`Ø 14 × 3 mm`) è montato in una **guarnizione di gommapiuma / EVA** che disaccoppia il PCB dai mattoncini LEGO (riduzione vibrazioni trasmesse dal telaio) e sigilla il retro della capsula dal volume interno della camera acustica dello speaker.
  - Il percorso sonoro verso l'esterno attraverso il foro `3700` è completamente libero (`~4 mm` di profondità).
- **Cablaggio:** 5 fili `26 AWG` (`VDD, GND, WS, SCK, SD`) instradati lungo il bordo laterale fino ai pin `J1` (`GPIO 4, 5, 6`) dell'`ESP32-S3`.
- **Nota obbligatoria su eco (AEC):** la separazione meccanica e l'isolamento riducono l'accoppiamento diretto, ma **non eliminano l'eco acustico** in un cubo di `80 mm`. Restano obbligatorie **cancellazione eco software (AEC / half-duplex o barge-in su firmware `xiaozhi-esp32`)** e **prove reali di ascolto durante la riproduzione audio** nella fase di collaudo.
