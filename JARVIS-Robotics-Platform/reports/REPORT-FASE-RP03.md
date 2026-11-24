# JARVIS Robotics Platform — Relazione Formale Conclusiva
## FASE RP-03 — Eyes 3.0 Simulator e Fondamenta di Identity Studio

> **Data di Redazione:** 24 Novembre 2026  
> **Stato della Fase:** COMPLETATA CON SUCCESSO  
> **Commit Firmware di Riferimento:** `53f1bce` + Uncommitted Working Tree FASE 13.7 (19/11/2026)  
> **Ambiente Locale:** `127.0.0.1:5173` (Vite Server attivo in sandbox isolata)  
> **Prescrizione Operativa:** Nessuna modifica al firmware ESP32, ai file di fabbricazione KiCad/Gerber, alle partizioni NVS o ai servizi di produzione. Rispetto assoluto della Golden Baseline C++.

---

### Indice dei Contenuti
1. [Risultati dell'Audit Preliminare RP-02](#1-risultati-dellaudit-preliminare-rp-02)
2. [Esito della Validazione Formale JSON Schema Draft 2020-12](#2-esito-della-validazione-formale-json-schema-draft-2020-12)
3. [Esito dei Test di Sicurezza sui Pacchetti ZIP Sintetici Reali](#3-esito-dei-test-di-sicurezza-sui-pacchetti-zip-sintetici-reali)
4. [Risoluzione della Discrepanza Pinout ESP32-S3 e Aggiornamento Hardware](#4-risoluzione-della-discrepanza-pinout-esp32-s3-e-aggiornamento-hardware)
5. [Architettura del Frontend e Scelte Tecnologiche](#5-architettura-del-frontend-e-scelte-tecnologiche)
6. [Dettagli Implementativi del Framebuffer 128x64 e Compatibilità XBM/SH1106](#6-dettagli-implementativi-del-framebuffer-128x64-e-compatibilità-xbmsh1106)
7. [Porting Matematico Eyes 3.0: Corrispondenza e Formule](#7-porting-matematico-eyes-30-corrispondenza-e-formule)
8. [Catalogo delle 14 Espressioni Canoniche e 5 Micro-Espressioni](#8-catalogo-delle-14-espressioni-canoniche-e-5-micro-espressioni)
9. [Simulatore di Eventi Fisici, Touch e Rete](#9-simulatore-di-eventi-fisici-touch-e-rete)
10. [Simulatore di Reattività Audio e Inviluppo RMS](#10-simulatore-di-reattività-audio-e-inviluppo-rms)
11. [Skin Studio Parametrico e Conformità Schemi](#11-skin-studio-parametrico-e-conformità-schemi)
12. [Catalogo Multi-Identità della Piattaforma (5 Robot)](#12-catalogo-multi-identità-della-piattaforma-5-robot)
13. [Comparatore Ottico Dual-OLED Side-by-Side](#13-comparatore-ottico-dual-oled-side-by-side)
14. [Risultati della Test Suite Automatica Frontend (Vitest)](#14-risultati-della-test-suite-automatica-frontend-vitest)
15. [Istruzioni Operative per l'Avvio in Locale](#15-istruzioni-operative-per-lavvio-in-locale)
16. [Checklist dei Test Manuali Consigliati all'Utente](#16-checklist-dei-test-manuali-consigliati-allutente)
17. [Mappatura dei File Prodotti nella Piattaforma](#17-mappatura-dei-file-prodotti-nella-piattaforma)
18. [Conferma Rigorosa del Rispetto dei Vincoli Operativi](#18-conferma-rigorosa-del-rispetto-dei-vincoli-operativi)
19. [Stato di Allineamento con il Progetto Principale](#19-stato-di-allineamento-con-il-progetto-principale)
20. [Raccomandazioni Tecniche per la FASE RP-04](#20-raccomandazioni-tecniche-per-la-fase-rp-04)
21. [Tabella Sinottica di Avanzamento della Piattaforma](#21-tabella-sinottica-di-avanzamento-della-piattaforma)
22. [Dichiarazione Esplicita di STOP](#22-dichiarazione-esplicita-di-stop)

---

### 1. Risultati dell'Audit Preliminare RP-02

In apertura della FASE RP-03 è stato eseguito un audit approfondito su tutti i documenti e gli artefatti prodotti nella RP-02, documentato integralmente in `docs/02-AUDIT-PRELIMINARE-RP02.md`:

1. **Riconciliazione Conteggio Profili:**
   - Nel testo del report RP-02 era presente un refuso che dichiarava "28 profili", originato dall'indice dei 28 capitoli della RP-01.
   - Il conteggio esatto, verificato file per file sul filesystem, è di **27 profili ufficiali**:
     - 5 Skin (`jarvis-original`, `eva-elegant`, `nova-hud`, `tars-geometric`, `neko-feline`)
     - 5 Identità logiche (`jarvis`, `eva`, `nova`, `tars`, `neko`)
     - 5 Personalità conversazionali (`jarvis`, `eva`, `nova`, `tars`, `neko`)
     - 3 Voci acustiche (`riccardo`, `paola`, `corrado`)
     - 5 Wake Word neurali (`hey-jarvis`, `hey-eva`, `hey-nova`, `hey-tars`, `hey-neko`)
     - 3 Profili Hardware (`desktop-v1`, `mobile-v2`, `custom-robot`)
     - 1 Profilo Dispositivo fisico (`jarvis-desk-01`)
     - **Totale reale:** $5 + 5 + 5 + 3 + 5 + 3 + 1 = 27$.
2. **Stato della Carrier Board V1:**
   - La Carrier Board V1 personalizzata è stata progettata (schemi KiCad 8.0, routing 2-layer, netlist e pacchetto Gerber con file CPL/BOM) e ordinata presso il fabbricante PCBWay.
   - Lo stato ufficiale è: **Progettata e Ordinata in fabbrica (In transito / Attesa ricezione fisica)**. Nessun test di laboratorio, montaggio SMD manuale o collaudo sotto tensione è stato ancora effettuato.
3. **Infrastruttura Raspberry Pi 5:**
   - Chiarito formalmente che il Raspberry Pi 5 (8 GB RAM, Debian 13 arm64) opera attualmente su scheda microSD ad alte prestazioni (l'SSD NVMe PCIe Gen2/3 è un componente di upgrade futuro non presente fisicamente).
   - Le risorse CPU/RAM dell'host sono condivise con molteplici servizi domestici attivi (Portainer Business Edition, Nginx Proxy Manager, AdGuard Home DNS, Vaultwarden, Home Assistant) e supportate dal NAS Synology DS223j (RAID 1 Btrfs) per i backup. Nessun carico esclusivo deve essere assunto per la piattaforma robotica.
4. **Disaccoppiamento della Maturità delle Capacità:**
   - Lo schema `capability.schema.json` e la matrice sono stati blindati per disaccoppiare lo stato della capacità sulla piattaforma (`ACTIVE`, `EXPERIMENTAL`, `DESIRED`) dallo stato del firmware primario, evitando forzature o presunzioni di completamento.

---

### 2. Esito della Validazione Formale JSON Schema Draft 2020-12

È stato configurato un ambiente virtuale Python dedicato (`JARVIS-Robotics-Platform/.venv/`, Python 3.14.4) isolato dal sistema e dal Voice Bridge, installando la libreria standard `jsonschema` (v4.26.0) con il motore `Draft202012Validator`.

È stato sviluppato lo script formale `validators/validate_with_jsonschema.py`:
- **Convalida Metaschema:** Tutti i 10 schemi JSON sono stati convalidati rispetto al metaschema ufficiale di Draft 2020-12 (`https://json-schema.org/draft/2020-12/schema`).
- **Risoluzione Riferimenti Locali:** Implementata risoluzione offline di `$defs` e `$ref` verso `common.schema.json` tramite `referencing.Registry`.
- **Compatibilità `$schema`:** È stata aggiunta la proprietà `"$schema": { "type": "string" }` alle definizioni degli schemi con `additionalProperties: false`, garantendo la massima rigidezza senza conflitti di validazione.
- **Risultato:**
  - 10 Schemi su 10 validi al 100%.
  - 27 Profili ufficiali convalidati al 100%.
  - 4 Fixture di conformità convalidate al 100%.

---

### 3. Esito dei Test di Sicurezza sui Pacchetti ZIP Sintetici Reali

Per verificare in modo deterministico la robustezza del manifest dei pacchetti d'identità distribuiti (`.jarvis-*`) e del motore di importazione/estrazione, è stato sviluppato `validators/validate_zip_package.py`, eseguendo test su veri archivi ZIP binari generati dinamicamente in memoria:

| ID Test | Scenario di Sicurezza Verificato | Esito del Test | Note di Implementazione |
| :--- | :--- | :---: | :--- |
| **SEC-01** | Pacchetto sintetico conforme e integro | **PASS** | Verifica checksum SHA-256 e manifest `package.schema.json`. |
| **SEC-02** | Attacco Path Traversal Zip-Slip (`../`) | **PASS** | Intercettato e bloccato prima della scrittura su disco. |
| **SEC-03** | Attacco Path Traversal Windows (`..\`) | **PASS** | Intercettato e bloccato il separatore backslash. |
| **SEC-04** | Manomissione Payload / Checksum Mismatch | **PASS** | Rilevata discordanza tra hash dichiarato e calcolato. |
| **SEC-05** | Asset non autorizzato / File non dichiarato | **PASS** | Pacchetto respinto per presenza di file spuri o celati. |
| **SEC-06** | Superamento limite di quota massima (1 MB) | **PASS** | Pacchetto > 1048576 byte respinto preventivamente. |

Tutti i 6 test di sicurezza sui pacchetti ZIP hanno registrato un tasso di successo del **100%**.

---

### 4. Risoluzione della Discrepanza Pinout ESP32-S3 e Aggiornamento Hardware

Durante l'audit è emerso un errore critico nel report preliminare RP-02 che indicava l'OLED SH1106 collegato a SDA GPIO21 e SCL GPIO22.
Dall'ispezione delle specifiche ufficiali Espressif del silicio ESP32-S3 e dai sorgenti reali del firmware (`04-Firmware/jarvis-desk-buddy/include/pinout_config.h`), è emerso che:
1. **I GPIO 22, 23, 24 e 25 NON ESISTONO fisicamente** nel silicio dell'ESP32-S3 (omessi per ragioni architetturali del package). L'indicazione di GPIO 22 era un errore materiale.
2. La configurazione hardware reale collaudata sul prototipo da scrivania e stampata sulla Carrier Board V1 prevede:
   - **I2C0 SDA:** `GPIO 41` (`kI2cSdaPin`)
   - **I2C0 SCL:** `GPIO 42` (`kI2cSclPin`)
   - **Touch Capacitivo TTP223:** `GPIO 1` (`kTouchTtp223`, Active HIGH)
   - **Pulsante PTT Fisico:** `GPIO 0` (Active LOW)
   - **I2S Audio (MAX98357A + INMP441):** BCLK: `GPIO 4`, LRC/WS: `GPIO 5`, DOUT/DIN: `GPIO 6`/`GPIO 7`.
3. Nel profilo `mobile-v2.hardware.json` i pin del driver motori TB6612FNG sono stati rimappati sui GPIO liberi 11, 12, 13, 14, 39, 40 e 21, eliminando qualsiasi sovrapposizione con il bus I2C0 primario o con pin riservati dalla flash Octal.
4. I file `profiles/hardware/desktop-v1.hardware.json`, `profiles/hardware/mobile-v2.hardware.json` e `fixtures/valid-hardware.json` sono stati corretti, aggiornati e rivalidati con successo.

---

### 5. Architettura del Frontend e Scelte Tecnologiche

Il frontend di **JARVIS Identity Studio** è stato strutturato all'interno della directory `JARVIS-Robotics-Platform/frontend/` adottando un'architettura modulare e moderna:

- **Linguaggio e Tipizzazione:** TypeScript 5.6.3 in modalità strict (`strict: true`, `noImplicitAny: true`).
- **Framework UI:** React 18.3.1 con Functional Components, Custom Hooks e Context API.
- **Build System:** Vite 6.0.1 con bundling esbuild, hot module replacement (HMR) istantaneo (~400 ms) e compilazione di produzione ottimizzata.
- **Styling:** Tailwind CSS 3.4.16 con palette personalizzata *JARVIS Cybernetic* (dark `#080d14`, panel `#0e1624`, card `#142033`, cyan `#00e5ff`, glow fosfori).
- **Iconografia:** `lucide-react` 0.468.0.
- **Motore di Rendering:** HTML5 Canvas 2D accelerato via software con disabilitazione del filtro bilineare (`imageSmoothingEnabled = false`) per garantire una resa pixel-perfect 1:1 identica all'OLED fisico da 1.3 pollici.
- **Test Runner:** Vitest 2.1.8 integrato nell'ambiente Vite.

---

### 6. Dettagli Implementativi del Framebuffer 128x64 e Compatibilità XBM/SH1106

La classe `MonochromeFramebuffer.ts` riproduce fedelmente l'allocazione e l'organizzazione in memoria di `monochrome_fb.h` e `monochrome_fb.cpp` dell'ESP32:

- **Geometria:** Risoluzione 128 pixel orizzontali × 64 pixel verticali.
- **Rappresentazione Binaria:** 1 bit per pixel (0 = pixel spento / nero profondo, 1 = pixel acceso / ciano elettrico).
- **Organizzazione della Memoria (Stride):** 16 byte per riga ($128 / 8 = 16$), per un totale di **esattamente 1024 byte** (`Uint8Array(1024)`).
- **Packing LSB-First (Standard XBM):** Il bit meno significativo (`LSB`) corrisponde al pixel più a sinistra all'interno del byte:
  $$\text{byte\_index} = y \cdot 16 + \lfloor x / 8 \rfloor, \quad \text{bit\_mask} = 1 \ll (x \pmod 8)$$
- **Esportazione C++ Bit-Exact:** La funzione `.toXBM(varName)` produce codice C++ direttamente copiabile e utilizzabile con la funzione `u8g2.drawXBM(&u8g2, 0, 0, 128, 64, varName_bits)` del firmware, garantendo un'interoperabilità al 100% tra simulatore e robot fisico.
- **Primitive di Disegno Integrate:** `setPixel`, `getPixel`, `clear`, `drawHLine`, `fillRect`, `fillCircle`, `fillRoundedRect` per una computazione ottica ad alta velocità.

---

### 7. Porting Matematico Eyes 3.0: Corrispondenza e Formule

Il motore grafico `EyeEngine.ts` rappresenta la traduzione fedele, verificata equazione per equazione, dei 1106 righi del sorgente `eye_engine.cpp` del robot JARVIS originale:

1. **Equazione della Superellisse (Curva di Lamé):**
   Ciascun occhio è rasterizzato tramite la formulazione cartesiana normalizzata ad esponente $p$:
   $$\left| \frac{x - c_x}{r_x} \right|^p + \left| \frac{y - c_y}{r_y} \right|^p \le 1$$
   Dove per JARVIS Original Premium $p = 2.6$ (o $3.0$ in modalità skin parametrica), $r_x = 19$, $r_y = 19$.
2. **Fattore di Rastremazione Asimmetrica (Taper):**
   Per conferire espressività organica allo sguardo visore, il semiasse orizzontale varia linearmente lungo l'asse verticale:
   $$r_x(y) = r_x \cdot (1 - \text{taper} \cdot v), \quad v = \frac{y - c_y}{r_y} \in [-1, +1]$$
   Con $\text{taper} = 0.10$, la sommità dell'occhio risulta leggermente rastremata verso l'interno.
3. **Modellazione Palpebrale Parabolica (Curved Eyelids):**
   Le palpebre superiore e inferiore non sono tagli rettilinei ma curve paraboliche parametriche:
   $$y_{\text{lid}}(x) = y_{\text{base}} + \text{arch} \cdot (1 - u^2), \quad u = \frac{x - c_x}{r_x} \in [-1, +1]$$
4. **Pupilla Scura e Catchlight Tech Glint:**
   All'interno dell'occhio pieno viene intagliata una pupilla circolare scura (pixel a 0) di raggio $r = 7$ px, centrata con offset dinamico di sguardo (gaze saccadico). Al suo interno sono riaccesi a 1 due bagliori:
   - *Primary Catchlight:* blocco $2 \times 2$ pixel in alto a sinistra ($dx = -2, dy = -2$).
   - *Secondary Glint:* singolo pixel tecnologico in basso a destra ($dx = +3, dy = +3$).
5. **Generatore PRNG Deterministico xorshift32:**
   Tutti i movimenti involontari (saccadi, micro-espressioni, durata delle pause) derivano dal medesimo generatore xorshift32 a 32-bit inizializzato con il seed esatto del firmware:
   $$x \leftarrow x \oplus (x \ll 13), \quad x \leftarrow x \oplus (x \gg 17), \quad x \leftarrow x \oplus (x \ll 5) \quad (\text{Seed: } \mathtt{0xA511E9B3})$$
6. **Dinamica Temporale a Decadimento Esponenziale:**
   Tutti i parametri interpolano verso i target tramite filtro esponenziale continuo, indipendente dal frame rate:
   $$v(t + \Delta t) = v(t) + \left( v_{\text{target}} - v(t) \right) \cdot \left( 1 - e^{-\text{rate} \cdot \Delta t} \right)$$

---

### 8. Catalogo delle 14 Espressioni Canoniche e 5 Micro-Espressioni

Il simulatore supporta tutte le 14 espressioni canoniche definite nel firmware originale, oltre al rendering speciale per le espressioni iconiche:

1. **NEUTRAL:** Stato base di quiete vigile, occhio superellittico $38 \times 38$, pupilla centrale con catchlight.
2. **HAPPY:** Trasformazione in mezzaluna convessa verso l'alto con fossette stilizzate inferiori ($x \pm 14$).
3. **CURIOUS:** Asimmetria oculare (occhio sinistro ristretto e abbassato $30 \times 28$, occhio destro spalancato $42 \times 42$ con sopracciglio arcuato).
4. **SLEEPY:** Palpebre superiori calate di 11 px, pupilla bassa, movimento rallentato.
5. **LISTENING:** Occhi allargati in altezza a 42 px, dilatazione pupillare ($r = 8.5$), arresto delle saccadi involontarie.
6. **THINKING:** Sguardo deviato lateralmente in alto a destra (+4 px), contrazione orizzontale.
7. **SPEAKING:** Modulazione ritmica dell'arco palpebrale inferiore guidata dall'audio I2S.
8. **SURPRISED:** Spalancamento rapido ($39 \times 45$ px), boost di transizione esponenziale ($1.85 \times$), ammiccamento riflesso.
9. **SHY:** Occhi compressi e ravvicinati verso il centro, sguardo basso.
10. **LOVE:** Rendering procedurale a doppio cuore pieno pulsante con effetto battito cardiaco alternato.
11. **WINK:** Asimmetria con occhio sinistro aperto normale ed occhio destro chiuso a mezzaluna ammiccante.
12. **CONFUSED:** Inclinazione contrapposta delle sopracciglia, altezze asimmetriche.
13. **MISCHIEVOUS:** Sguardo felino obliquo con inclinazione palpebrale contrapposta e sopracciglia aggressive.
14. **SLEEPING:** Ciglia chiuse ricurve verso il basso e glifi procedurali animati a "Zzz" galleggianti.

**Le 5 Micro-Espressioni Procedurali:**
- `BrowRaise`: Sollevamento impercettibile del sopracciglio destro durante l'ascolto.
- `SideGlance`: Rapida occhiata laterale involontaria (120 ms).
- `QuickWink`: Micro-occhiolino d'intesa.
- `EyeSmile`: Leggera contrazione dell'arco inferiore durante interazioni positive.
- `PupilPulse`: Micro-dilatazione pupillare durante l'elaborazione di dati complessi.

---

### 9. Simulatore di Eventi Fisici, Touch e Rete

Il modulo `EventSimulator.ts` disaccoppia il collaudo grafico dal silicio fisico dell'ESP32, simulando la catena di interrupt ed eventi di sistema:

- **Pulsante PTT (GPIO 0):** Simula pressione prolungata (stato `LISTENING`) e rilascio (transizione automatica a `THINKING`).
- **Wake Word Recognition:** Attivazione da parola chiave locale (es. "Ehi Jarvis"), con transizione istantanea a `LISTENING` e orientamento dello sguardo frontale.
- **Sensore Touch Capacitivo TTP223 (GPIO 1):**
  - *Tocco Singolo (Tap < 400ms):* Reazione festosa (stato `HAPPY` + ammiccamento di compiacimento).
  - *Doppio Tocco Rapido (Double Tap):* Ammiccamento d'intesa (`WINK`).
  - *Tocco Prolungato (Long Press > 1.5s):* Attivazione modalità affetto a cuoricini (`LOVE`).
- **Ciclo di Conversazione Vocale:** Sequenza orchestrata `LISTENING` $\rightarrow$ `THINKING` $\rightarrow$ `SPEAKING` $\rightarrow$ `NEUTRAL`.
- **Risparmio Energetico:** Timeout di inattività simulato con transizione a `SLEEPING` e risveglio su stimolo touch/voce (`WAKEUP` $\rightarrow$ `SURPRISED` $\rightarrow$ `NEUTRAL`).
- **Registro Eventi:** Tabella cronologica interattiva con timestamp millisecondo, tipo evento, espressione mappata e spiegazione contestuale.

---

### 10. Simulatore di Reattività Audio e Inviluppo RMS

Il modulo `AudioSimulator.ts` emula il sottosistema audio I2S del firmware ESP32 (MAX98357A / INMP441) per collaudare la reattività vocale esclusivamente oculare in stato `SPEAKING`:

- **Vincolo Oculare Assoluto:** La reattività audio è rigorosamente confinata agli occhi (modulazione dell'arco palpebrale inferiore `lowerArch` da 0 a 4 px e leggera escursione in altezza). È categoricamente esclusa qualsiasi rappresentazione di bocca, labbra o tratti facciali antropomorfi.
- **Modalità di Generazione Sintetica:**
  - `SILENCE`: Livello RMS fisso a 0.0 (nessuna reazione oculare).
  - `CONSTANT`: Livello RMS calibrabile manualmente tramite slider continuo [0.0 .. 1.0].
  - `SINE`: Oscillatore sinusoidale a frequenza impostabile [0.5 .. 20.0 Hz] per collaudo dinamico di risposta in frequenza.
  - `SYLLABIC`: Generatore a doppia portante (6.5 Hz e 11.2 Hz) con pause frasali stocastiche, emulante la naturale cadenza fonetica del parlato vocale italiano.
- **Caricamento File WAV Reali (Web Audio API):** L'utente può caricare qualsiasi file audio WAV locale dal proprio PC. Il simulatore istanzia un nodo `AnalyserNode` con FFT a 256 campioni, calcola l'RMS temporale in tempo reale e sincronizza la modulazione dello sguardo all'audio riprodotto.

---

### 11. Skin Studio Parametrico e Conformità Schemi

La vista `SkinEditorView.tsx` fornisce un banco di progettazione e calibrazione per lo Skin Engine:

- **Regolazione Parametrica in Tempo Reale:**
  - Larghezza occhio ($16 - 44$ px)
  - Altezza occhio ($16 - 52$ px)
  - Spaziatura interoculare ($4 - 32$ px)
  - Esponente superellisse di Lamé ($1.0 - 5.0$)
  - Rastremazione rastremata asimmetrica taper ($0.00 - 0.45$)
  - Raggio di raccordo angoli ($0 - 14$ px)
  - Pupilla scura (raggio, abilitazione catchlight)
  - Sopracciglia stilizzate (offset verticale, curvatura arco, inclinazione)
- **Garanzia Baseline:** Pulsante di ripristino istantaneo alla Golden Baseline originale JARVIS (`Reset Baseline`).
- **Importazione ed Esportazione JSON:**
  - Generazione di file `.skin.json` pienamente validi e conformi a `skin.schema.json`.
  - Validatore frontend integrato che verifica la conformità semantica dei parametri prima del caricamento in memoria.

---

### 12. Catalogo Multi-Identità della Piattaforma (5 Robot)

La vista `CatalogueView.tsx` espone le 5 identità convalidate della piattaforma, permettendo l'anteprima OLED immediata e l'invio rapido allo Skin Editor o al Comparatore:

| ID Identità | Nome Robot | Ruolo & Personalità | Skin Oculare | Stato di Maturità |
| :--- | :--- | :--- | :--- | :---: |
| `jarvis` | **JARVIS Original** | Maggiordomo AI sobrio, ironico, tecnico | *Organic Visor Companion* ($p=2.6, 38\times38$) | **PRODUZIONE / ATTIVO (Baseline)** |
| `eva` | **EVA Companion** | Assistente empatico e rassicurante | *Smooth Friendly* ($p=2.3, 36\times40$) | **PREVIEW / SPERIMENTALE** |
| `nova` | **NOVA Explorer** | Robot analitico orientato alla scoperta | *Sharp Horizon* ($p=3.6, 32\times34$) | **PREVIEW / SPERIMENTALE** |
| `tars` | **TARS Monolith** | Pragmatico, sarcastico (75% humor) | *Minimal Bar* ($p=4.8, 42\times22$) | **PREVIEW / SPERIMENTALE** |
| `neko` | **NEKO Playful** | Compagno felino vivace e giocherellone | *Cute Manga Slit* ($p=2.2, 36\times42$) | **PREVIEW / SPERIMENTALE** |

---

### 13. Comparatore Ottico Dual-OLED Side-by-Side

La vista `SkinComparatorView.tsx` permette di convalidare otticamente qualsiasi nuova skin o variante rispetto alla Golden Baseline:

- **Doppio Display Sincrono:** Due pannelli OLED 128x64 affiancati (Sinistra: Golden Baseline JARVIS C++; Destra: Skin candidata).
- **Sincronia d'Orologio:** Controllo Play/Pausa sincronizzato, avanzamento manuale a singolo frame (+16 ms) e ammiccamento simultaneo.
- **Analisi Differenziale Quantitativa:** Calcolo automatico in tempo reale del delta geometrico ed energetico:
  - $\Delta$ Larghezza, $\Delta$ Altezza, $\Delta$ Spaziatura, $\Delta$ Superellisse, $\Delta$ Taper.
  - $\Delta$ Pixel illuminati attivi sul buffer (utile per stimare l'assorbimento di corrente del display fisico SH1106).

---

### 14. Risultati della Test Suite Automatica Frontend (Vitest)

È stata configurata ed eseguita la test suite unitaria frontend con Vitest, registrando il 100% di esito positivo su tutti i file:

```
 RUN  v2.1.9 JARVIS-Robotics-Platform/frontend

 ✓ src/tests/audioSimulator.test.ts (4 tests) 13ms
 ✓ src/tests/framebuffer.test.ts (6 tests) 26ms
 ✓ src/tests/eyeEngine.test.ts (7 tests) 40ms
 ✓ src/tests/eventSimulator.test.ts (2 tests) 45ms

 Test Files  4 passed (4)
      Tests  19 passed (19)
   Duration  1.73s
```

La build di produzione `npm run build` (`tsc && vite build`) ha compilato l'intero progetto senza errori né warning di tipo (`dist/index.html` 0.73 kB, `dist/assets/index-*.js` 262.98 kB).

---

### 15. Istruzioni Operative per l'Avvio in Locale

Il server di sviluppo locale è attualmente attivo e raggiungibile:

- **Indirizzo Locale:** `http://127.0.0.1:5173/`
- **Requisiti di Sistema:** Qualsiasi browser moderno (Chrome, Edge, Firefox) con supporto Canvas 2D e Web Audio API.

**Comandi manuali per riavvii futuri:**
```powershell
# Navigazione nella cartella frontend della piattaforma
cd "JARVIS-Robotics-Platform\frontend"

# Esecuzione dei test automatici
npm.cmd run test

# Compilazione di produzione
npm.cmd run build

# Avvio del server di sviluppo
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

---

### 16. Checklist dei Test Manuali Consigliati all'Utente

Per verificare personalmente l'esperienza d'uso e la fedeltà visiva, l'utente può eseguire la seguente procedura:

- [ ] **1. Apertura dell'Applicazione:** Aprire il browser all'indirizzo `http://127.0.0.1:5173/` e verificare la presenza del banner di sandbox "MODALITÀ SIMULATORE".
- [ ] **2. Ispezione della Dashboard:** Verificare il conteggio dei 27 profili formalizzati e i dati di pinout ESP32-S3 corretti (SDA 41, SCL 42).
- [ ] **3. Collaudo Eyes 3.0 Simulator:**
  - Cliccare su *Eyes 3.0 Simulator* nel menu laterale.
  - Verificare la fluidità a 30 FPS della Golden Baseline JARVIS con saccadi involontarie.
  - Selezionare varie espressioni (`HAPPY`, `CURIOUS`, `LOVE`, `SLEEPING`, `WINK`) e osservare la trasformazione fluida delle curve.
  - Cliccare su *Carezza Singola (Touch)* e verificare l'immediata reazione sorridente.
  - Nella sezione Audio, selezionare la modalità *Parlato Sillabico* e osservare la reattività dell'arco palpebrale inferiore.
- [ ] **4. Collaudo Parametrico Skin Studio:**
  - Selezionare *Skin Studio*.
  - Modificare lo slider *Esponente Superellisse* da 2.6 a 4.5 e osservare il display OLED che squadrata l'occhio in tempo reale.
  - Cliccare su *Reset Baseline* e verificare il ripristino istantaneo della forma organica JARVIS.
  - Cliccare su *Esporta JSON* e verificare il download del file conforme allo schema.
- [ ] **5. Esplorazione Catalogo Identità:**
  - Accedere a *Catalogo Identità*.
  - Scorrere le 5 identità (JARVIS, EVA, NOVA, TARS, NEKO) e osservare i mini-display OLED animati.
- [ ] **6. Verifica Comparatore Dual-OLED:**
  - Accedere a *Comparatore Dual-OLED*.
  - Mettere in pausa la riproduzione e premere `+1F` per avanzare frame-by-frame verificando la perfetta sincronia temporale.

---

### 17. Mappatura dei File Prodotti nella Piattaforma

Tutti gli sviluppi sono stati confinati rigorosamente all'interno di `JARVIS-Robotics-Platform/`:

```
JARVIS-Robotics-Platform/
├── docs/
│   └── 02-AUDIT-PRELIMINARE-RP02.md                     <- Verbale dell'audit correttivo
├── validators/
│   ├── validate_with_jsonschema.py                      <- Validatore formale Draft 2020-12
│   └── validate_zip_package.py                          <- Test di sicurezza pacchetti ZIP
├── frontend/                                            <- Applicazione Web Identity Studio
│   ├── index.html                                       <- Entrypoint HTML con Dark Mode
│   ├── package.json                                     <- Dipendenze locali isolate
│   ├── vite.config.ts                                   <- Configurazione Vite & Vitest
│   ├── tsconfig.json & tsconfig.node.json               <- Strict TypeScript
│   ├── tailwind.config.js & postcss.config.js           <- Tema grafico Cybernetic
│   └── src/
│       ├── main.tsx & index.css                         <- Bootstrap applicativo
│       ├── app/
│       │   └── App.tsx                                  <- Layout unificato e router a viste
│       ├── components/
│       │   └── OledDisplay.tsx                          <- Display OLED Canvas 2D + Export XBM/PNG
│       ├── engine/
│       │   ├── framebuffer/
│       │   │   └── MonochromeFramebuffer.ts            <- Framebuffer 128x64 1-bit bit-exact
│       │   ├── eyes/
│       │   │   ├── types.ts                             <- Definizioni e tipi Eyes 3.0
│       │   │   ├── baseline.ts                          <- Golden Baseline JARVIS e Catalogo
│       │   │   └── EyeEngine.ts                         <- Porting 1:1 C++ Eyes 3.0 in TypeScript
│       │   └── simulation/
│       │       ├── EventSimulator.ts                    <- Simulatore eventi fisici, touch, rete
│       │       └── AudioSimulator.ts                    <- Simulatore reattività RMS sillabica/WAV
│       ├── features/
│       │   ├── dashboard/DashboardView.tsx              <- Panoramica e stato infrastruttura
│       │   ├── simulator/SimulatorView.tsx              <- Simulatore interattivo completo
│       │   ├── skin-editor/SkinEditorView.tsx           <- Editor geometrico parametrico
│       │   ├── profiles/CatalogueView.tsx               <- Catalogo 5 identità robot
│       │   └── simulator/SkinComparatorView.tsx         <- Comparatore Dual-OLED Side-by-Side
│       └── tests/
│           ├── framebuffer.test.ts                      <- 6 test unitari framebuffer & XBM
│           ├── eyeEngine.test.ts                        <- 7 test unitari motore Eyes 3.0
│           ├── eventSimulator.test.ts                   <- 2 test unitari simulatore eventi
│           └── audioSimulator.test.ts                   <- 4 test unitari reattività vocale
└── reports/
    └── REPORT-FASE-RP03.md                              <- Presente relazione conclusiva
```

---

### 18. Conferma Rigorosa del Rispetto dei Vincoli Operativi

Si certifica che durante tutta la FASE RP-03 sono stati rispettati integralmente i vincoli operativi:
- **Zero modifiche al progetto principale:** Nessun file all'esterno di `JARVIS-Robotics-Platform/` è stato alterato, creato o rimosso.
- **Nessuna operazione Git distruttiva:** Nessun commit, push, checkout o reset sul repository.
- **Nessuna compilazione invasiva o flash ESP32:** Nessuna chiamata a `esptool.py`, `idf.py` o accesso a porte COM seriali.
- **Nessuna installazione globale:** Tutti i pacchetti Node.js e le dipendenze Python sono stati installati esclusivamente negli ambienti virtuali e nelle cartelle `node_modules` locali della piattaforma.
- **Nessun impatto di rete:** Nessun servizio sul Raspberry Pi 5 o sul NAS Synology è stato modificato; il simulatore opera esclusivamente su `127.0.0.1:5173`.

---

### 19. Stato di Allineamento con il Progetto Principale

- **Stato del Progetto Principale:** Il firmware `04-Firmware/jarvis-desk-buddy/` rimane immutato e allineato all'ultima revisione analizzata (Working Tree FASE 13.7 con supporto a Xiaozhi, Piper TTS e ST7789/SH1106).
- **Integrità della Golden Baseline:** L'implementazione TypeScript in `EyeEngine.ts` riflette esattamente la matematica di `eye_engine.cpp`, garantendo che quando il Core della piattaforma verrà estratto nelle fasi future, il robot capostipite JARVIS conserverà al 100% l'identità e la morbidezza visiva acquisite.

---

### 20. Raccomandazioni Tecniche per la FASE RP-04

Per la futura **FASE RP-04 — Architettura del Backend di Identity Studio e Storage Locale**, si raccomandano le seguenti scelte progettuali:

1. **Stack Tecnologico Backend:**
   - Adottare **Python con FastAPI** (o FastAPI / SQLite con modalità WAL), conforme alle linee guida di progetto e all'infrastruttura Docker del Raspberry Pi 5.
   - Utilizzare Pydantic V2 generato o validato direttamente contro i 10 schemi JSON Draft 2020-12 della RP-02.
2. **Database Locale SQLite:**
   - Database SQLite posizionato secondo gli standard architetturali (`/opt/docker/appdata/jarvis-identity-studio/data/studio.db`), con journaling WAL e backup orario verso il NAS Synology via API native `sqlite3_backup`.
3. **Canale Real-Time WebSocket:**
   - Implementazione dell'endpoint `/ws/v1/stream` conforme al protocollo specificato in `contracts/websocket-protocol-v1.md`, con compressione gzip opzionale e streaming di telemetria a 10 Hz.
4. **Proxy e Sicurezza:**
   - Integrazione con Nginx Proxy Manager per la terminazione TLS e routing LAN su dominio locale senza esporre porte non protette all'esterno.

---

### 21. Tabella Sinottica di Avanzamento della Piattaforma

| Fase | Denominazione Ufficiale | Stato | Conseguibili Principali |
| :---: | :--- | :---: | :--- |
| **RP-01** | Analisi, fattibilità e architettura | **COMPLETATA** | 28 documenti architetturali, scomposizione modulare a 12 motori logici. |
| **RP-02** | Consolidamento, schemi JSON e contratti | **COMPLETATA** | 10 Schemi Draft 2020-12, OpenAPI 3.1, WebSocket v1, 27 profili, 15 test. |
| **RP-03** | Eyes 3.0 Simulator & Identity Studio UI | **COMPLETATA** | Frontend React/Vite, porting C++ 1:1, Framebuffer 1024B, 19 test (100%), dev server attivo. |
| **RP-04** | Backend Identity Studio, SQLite & Storage | *DA AVVIARE* | Server FastAPI, SQLite WAL, Endpoint REST/WS, sincronizzazione pacchetti. |
| **RP-05** | Personality Studio & Prompt Engine | *PIANIFICATA* | Editor comportamenti, calibrazione intenti, simulazione multi-turn. |
| **RP-06** | Voice & Wake Word Engine | *PIANIFICATA* | Pipeline Piper TTS, profilazione modelli wake word, benchmark audio. |
| **RP-07** | Device Manager & Hardware Profiles | *PIANIFICATA* | Discovery mDNS, gestione flotta robot, telemetria hardware. |
| **RP-08** | Packaging, Deploy & Transazioni OTA | *PIANIFICATA* | Compilazione pacchetti firmati, staging differenziale, Safe Deferred Apply. |

---

### 22. Dichiarazione Esplicita di STOP

In osservanza delle prescrizioni del prompt e dei vincoli inderogabili di governance:

**LA FASE RP-03 È FORMALMENTE CONCLUSA.**  
**È RIGOROSAMENTE VIETATO AVVIARE AUTOMATICAMENTE LA FASE RP-04.**  
**IL SISTEMA SI ARRESTA IN ATTESA DI REVISIONE E AUTORIZZAZIONE ESPLICITA DA PARTE DELL'UTENTE.**
