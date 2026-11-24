# 07 — Compatibilità Meccanica e Involucri Fisici

> **JARVIS Robotics Platform** — Linee Guida Meccaniche e Involucri  
> **Fase:** RP-01  
> **Stato:** Approvato per Progettazione  

---

## 1. Visione Meccanica della Piattaforma

La **JARVIS Robotics Platform** è progettata per disaccoppiare la logica elettronica e l'identità del robot dalla sua specifica forma fisica.

Un medesimo profilo elettronico (**Desktop V1**) può essere alloggiato con successo all'interno di:
- **Involucri LEGO Technic e System:** La struttura originale di JARVIS, caratterizzata da massima modularità, facilità di riconfigurazione e manutenzione senza attrezzi.
- **Involucri Stampati in 3D (FDM / SLA):** Scocche personalizzate dalle linee organiche, futuristiche o stilizzate (es. scocca gatto per NEKO, chassis monolitico per TARS o corpo curvato per EVA).
- **Robot Statici da Scrivania:** Companion con baricentro basso e piedini in gomma antiscivolo.
- **Robot Mobili:** Connessione rapida a basi con ruote motrici o cingoli.

---

## 2. Modulo A — Corpo Principale Companion (Standard di Piattaforma)

Il **Modulo A** è il nucleo meccanico standardizzato che ospita l'elettronica principale, l'interfaccia utente e i sensori primari.

### 2.1 Ingombri e Quote Standard LEGO
- **Impronta alla Base:** `10 × 10 stud` LEGO (`8,0 × 8,0 cm`).
- **Altezza Complessiva:** `18 plate` / `6 brick` (`~14,4 cm`).
- **Volume Utile Interno:** Progettato per accogliere la **Carrier Board PCB V1** montata verticalmente o orizzontalmente con supporti antivibranti.

### 2.2 Layout delle Aperture e Alloggiamento Periferiche

```
        +----------------------------------------+
        |   [ TOP LID ] - Touch Pad TTP223B      |
        |   Lamina capacitiva sotto plate LEGO   |
        +----------------------------------------+
        |                                        |
 [FRONT]|   [ DISPLAY OLED SH1106 1.3" ]         |
        |   Finestra a filo scocca (35x20 mm)    |
        |                                        |
        |   [ MIC INMP441 ] - Foro acustico Ø 2mm|
        |   Isolato con guarnizione in gomma     |
        |                                        |
        +----------------------------------------+
        |   [ CARRIER BOARD PCB V1 + ESP32-S3 ]  |
        |   Connettori JST per tutti i cablaggi  |
        +----------------------------------------+
 [BASE] |   [ SPEAKER 4Ω 3W ] Cassa Reflex       |
        |   Griglia acustica rivolta in basso    |
        +----------------------------------------+
```

1. **Finestra Display OLED (Fronte):**  
   Apertura rettangolare calibrata per il display da 1,3 pollici (area visibile attiva ~29,4 × 14,7 mm). Nel telaio LEGO, l'OLED è incassato dietro un bordo rifinito in tile scuri per eliminare riflessi e proteggere la matrice in vetro da urti.
2. **Condotto Acustico del Microfono (INMP441):**  
   Il microfono MEMS richiede un foro di cattura acustica (diametro 1,5–2,0 mm) orientato verso la parte frontale o superiore. Per garantire registrazioni nitide prive di rumore interno:
   - La capsula MEMS è sigillata ermeticamente contro la parete esterna mediante guarnizione in silicone/gommapiuma a cellule chiuse.
   - È presente un disaccoppiamento fisico rigido tra la cassa acustica dello speaker e la camera del microfono per evitare accoppiamenti diretti e auto-attivazione.
3. **Cassa di Risonanza dello Speaker (Base):**  
   Lo speaker da 4 Ω / 3 W è alloggiato nel terzo inferiore del Modulo A. L'emissione acustica avviene verso il piano d'appoggio attraverso una griglia forata LEGO (o feritoie sagomate nella stampa 3D). La camera posteriore è sigillata per ottimizzare la resa delle basse frequenze e migliorare la naturalezza delle voci maschili.
4. **Piastra Tattile Capacitiva (Testa):**  
   Il sensore capacitivo TTP223B è installato a ridosso della piastra superiore della testa. Una piccola lamina in rame adesivo (20 × 20 mm) posta a contatto con la plastica ABS (spessore tile 1,6 mm) garantisce una risposta immediata al tocco della mano senza parti metalliche a vista.
5. **Dissipazione Termica e Manutenzione:**  
   Feritoie di ventilazione convettiva naturale disposte sulle pareti posteriori e superiori. Il coperchio posteriore del Modulo A è rimovibile a scatto (*quick-release*), consentendo l'accesso istantaneo alla porta USB-C di programmazione, al selettore di alimentazione e ai connettori JST.

---

## 3. Interfaccia Meccanica con la Base Mobile (Modulo B2)

Il collegamento tra il robot companion (Modulo A) e la base mobile (Modulo B2) è concepito come un sistema di innesto modulare rapido e reversibile.

### 3.1 Geometria di Aggancio Meccanico
- **Interfaccia di Accoppiamento:** Matrice standard `8 × 8 stud` centrata sulla base inferiore del Modulo A.
- **Elementi di Bloccaggio:** **4 perni LEGO Technic Pin 6558 (3L con attrito)** inseriti negli angoli della matrice, che garantiscono tenuta meccanica contro vibrazioni e ribaltamento durante il moto, pur consentendo lo sgancio manuale in pochi secondi.
- **Applicazione Stampa 3D:** Per chassis in plastica stampata in 3D, l'interfaccia adotta quattro perni cilindrici conici maschio/femmina a baionetta con fermo a scatto elastico.

### 3.2 Connessione Elettrica Ombelicale (Umbilical Port)
- **Apertura di Passaggio:** Apertura passante centrale da `2 × 4 stud` (`1,6 × 3,2 cm`) sul fondo del Modulo A.
- **Connettore Unificato:** Connettore polarizzato **JST-XH a 6 pin** (passo 2,54 mm):
  - Pin 1: `+5V_B2` (Alimentazione principale regolata da batteria 2S, 5.0V @ 2.5A).
  - Pin 2: `GND` (Ritorno di massa comune di potenza e segnale).
  - Pin 3: `PWM_L` / `PWM_R` (Segnali di controllo motori o bus seriale I2C esteso).
  - Pin 4: `DIR_L` / `DIR_R` (Segnali di direzione e standby driver).
  - Pin 5: `CLIFF_IRQ` (Segnale di allarme sensori anti-caduta a riflessione).
  - Pin 6: `SENSE_BATT` (Partitore di tensione analogico per monitoraggio livello LiPo).

---

## 4. Personalizzazioni Estetiche e Involucri 3D delle Identità

La modularità meccanica consente di costruire involucri esterni dedicati alle diverse identità senza toccare l'elettronica comune:

| Identità | Stile Involucro Consigliato | Elementi Meccanici Caratteristici |
|---|---|---|
| **JARVIS** | Cubo Companion LEGO Technic/System | Linee precise, grigio scuro/nero con accenti rossi e oro, finitura liscia in tile. |
| **EVA** | Scocca 3D Organica / Ceramica | Forme morbide e arrotondate, bianco lucido con dettagli argento satinato. |
| **NOVA** | Chassis Cyberpunk / Industrial | Finitura scura opaca, sfaccettature poligonali, fessure di ventilazione geometriche. |
| **TARS** | Monolite Geometrico Minimalista | Sezioni rettangolari pure, alluminio anodizzato o filamento caricato fibra di carbonio. |
| **NEKO** | Scocca Meccanica Felina | Orecchie sagomate fisiche sulla scocca superiore (prive di elettronica), profilo sinuoso. |

Tutte le varianti rispettano i medesimi punti di fissaggio interni della Carrier Board e la medesima finestra frontale OLED 128×64, assicurando completa intercambiabilità.
