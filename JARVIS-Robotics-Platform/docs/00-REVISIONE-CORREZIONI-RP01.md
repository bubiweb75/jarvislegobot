# Revisione Critica e Correzioni della Fase RP-01

> **JARVIS Robotics Platform** — Documento di Tracciabilità e Rettifica RP-01  
> **Fase:** RP-02  
> **Data:** 24 Novembre 2026  
> **Stato:** Approvato e Integrato  

---

## 1. Premessa e Obiettivo del Documento

In ottemperanza alle prescrizioni di autorizzazione della **FASE RP-02**, il presente documento registra in modo formale e puntuale tutte le rettifiche apportate alla documentazione della Fase RP-01.

Tutte le incongruenze riscontrate tra le analisi preliminari e la realtà ingegneristica verificata sui sorgenti sono state corrette all'interno dei documenti originali di RP-01 e vengono qui sintetizzate punto per punto per garantire la massima trasparenza metodologica.

---

## 2. Registro Dettagliato delle Correzioni

### 4.1 Carrier Board PCB V1 — Stato di Fabbricazione vs Collaudo Prototipale
- **Incongruenza RP-01:** Alcune formulazioni potevano indurre a ritenere la Carrier Board PCB V1 già fisicamente consegnata, saldata e collaudata a banco su scheda finale.
- **Rettifica Applicata:**
  - *Compatibilità Progettuale:* **Verificata al 100%** rispetto a tutti i pinout e limiti hardware dell'ESP32-S3 (`JARVIS_GPIO_MAPPING_PCB_V1.md`).
  - *Verifica File di Produzione:* **Completata con successo** (Gerber, BOM, CPL generati e archiviati in `JARVIS_CARRIER_BOARD_V1_PRODUZIONE/`).
  - *Disponibilità Fisica:* La scheda PCB è stata **ordinata presso il service JLCPCB ed è attualmente in transito/attesa di consegna**.
  - *Assemblaggio e Collaudo Fisico PCB:* **Non ancora eseguiti sulla scheda PCB stampata**. Tutti i collaudi fisici citati nei report storici (FASE 10.3, 12.27, 13.7) sono stati condotti con successo su cablaggi prototipali e breadboard a banco.
- **Documenti Aggiornati:** `02-STATO-FIRMWARE-ESISTENTE.md`, `03-ANALISI-RIUTILIZZO.md`, `06-HARDWARE-PROFILES.md`, `28-REPORT-FASE-RP01.md`.

### 4.2 Infrastruttura Raspberry Pi 5 — Configurazione Reale e Risorse
- **Incongruenza RP-01:** Veniva menzionata l'archiviazione su SSD NVMe come già operativa e si ipotizzava la piena disponibilità della memoria RAM da 8 GB per i soli compiti di JARVIS.
- **Rettifica Applicata:**
  - *Supporto di Archiviazione Effettivo:* Il Raspberry Pi 5 opera attualmente su **microSD ad alte prestazioni**. L'upgrade a SSD NVMe M.2 tramite Pi M.2 HAT+ costituisce una miglioria futura pianificata e non un componente attualmente presente.
  - *Carico di Sistema Preesistente:* Sul nodo host operano già molteplici servizi domestici attivi (Nginx Proxy Manager, AdGuard Home, Portainer Business Edition e container applicativi preesistenti). Le risorse per JARVIS devono essere dimensionate tenendo conto di questo carico concorrente.
- **Documenti Aggiornati:** `23-INFRASTRUTTURA.md`.

### 4.3 Architettura AI Flessibile — Decoupling e Modalità Alternative
- **Incongruenza RP-01:** Veniva presentata come vincolante la presenza di Ollama sul Raspberry Pi 5 per tutti i robot.
- **Rettifica Applicata:**
  - L'architettura AI è formalizzata come **pienamente modulare e agnostica rispetto al provider**:
    1. *AI Locale su PC Windows:* Per massime prestazioni di calcolo con GPU dedicata.
    2. *AI Locale su Raspberry Pi 5:* Subordinata a benchmark prestazionali effettivi a banco.
    3. *Provider AI Cloud Esterni:* Supporto ad API esterne conformi OpenAI / Anthropic.
    4. *Architettura Ibrida:* Intenti locali deterministici a latenza zero (< 15 ms) per orologio, volume e comandi di sistema.
    5. *Modalità Degradata:* Funzionamento autonomo del robot anche in assenza temporanea dell'LLM.
  - I provider STT (Faster-Whisper), LLM (Ollama/Cloud) e TTS (Piper) rimangono indipendenti e configurabili singolarmente.
  - Il NAS Synology DS223j (1 GB RAM) è rigorosamente dedicato a storage freddo e backup cifrati, **escludendo categoricamente l'esecuzione di LLM pesanti**.
- **Documenti Aggiornati:** `16-PERSONALITY-ENGINE.md`, `23-INFRASTRUTTURA.md`.

### 4.4 Prestazioni e Latenze — Distinzione tra Misurazioni e Obiettivi
- **Incongruenza RP-01:** Alcune stime teoriche di concorrenza multi-robot (es. 3–4 robot simultanei) venivano presentate in modo assertivo.
- **Rettifica Applicata:**
  - I dati prestazionali sono ora classificati formalmente in:
    * *Dati Misurati:* Rilevati su PC Windows 11 con hardware ESP32-S3 `COM6` in FASE 12.27 e 13.7 (STT ~210–320 ms, Piper ~140–190 ms, wake word ~110 ms, FPS display 30.0 costanti).
    * *Obiettivi Progettuali:* Latenza end-to-end ≤ 2500 ms su Raspberry Pi 5.
    * *Stime Teoriche di Concorrenza:* La gestione simultanea di più robot con streaming audio duplex richiede benchmark dedicati di rete e CPU prima di essere garantita.
- **Documenti Aggiornati:** `23-INFRASTRUTTURA.md`, `24-SICUREZZA-PRESTAZIONI.md`.

### 4.5 Grafica Esclusivamente Oculare — Eliminazione Totale Riferimenti a Elementi Facciali
- **Incongruenza RP-01:** Nel documento `20-SIMULATORE.md` e in un diagramma di flusso compariva un riferimento alla reazione dinamica della "bocca stilizzata" al volume della voce.
- **Rettifica Applicata:**
  - **Eliminato categoricamente qualsiasi riferimento a bocca, naso, baffi, guance o orecchie grafiche a schermo.**
  - La reattività visiva al volume del parlato (inviluppo audio RMS) è realizzata **esclusivamente mediante animazioni oculari**: sollevamento/curvatura della palpebra inferiore (`lower_arch`), dilatazione della pupilla e micro-saccadi coordinate.
- **Documenti Aggiornati:** `10-EYES3-STATI-ESPRESSIONI.md`, `20-SIMULATORE.md`.

### 4.6 Wake Word — Tassonomia degli Stati del Catalogo
- **Incongruenza RP-01:** L'assegnazione di wake word differenti nei profili di identità dimostrativi poteva far intendere che i modelli acustici fossero già tutti compilati e collaudati.
- **Rettifica Applicata:**
  - Formalizzata la tassonomia degli stati del modello: `DESIRED`, `UNAVAILABLE`, `AVAILABLE`, `COMPATIBLE`, `INSTALLED`, `VALIDATED`, `ACTIVE`.
  - Solo il modello `hey_jarvis` (microWakeWord INT8) è attualmente `VALIDATED` e `ACTIVE` sul firmware.
  - I modelli `hey_eva`, `hey_nova`, `hey_tars`, `hey_neko` sono classificati come `DESIRED`: la loro presenza nel catalogo identità costituisce un obiettivo che richiederà addestramento acustico dedicato prima della distribuzione.
  - Il pulsante meccanico PTT su `GPIO47` rimane sempre attivo come garanzia universale di risveglio.
- **Documenti Aggiornati:** `15-WAKE-WORD-ENGINE.md`, `27-MATRICE-FATTIBILITA.md`.

### 4.7 Backup SQLite — Consistenza Transazionale e WAL Checkpointing
- **Incongruenza RP-01:** Veniva citato il backup come copia diretta di file, pratica rischiosa con database SQLite operanti in modalità WAL (*Write-Ahead Logging*).
- **Rettifica Applicata:**
  - La procedura di backup adotta rigorosamente la **SQLite Online Backup API** (`sqlite3_backup_*` o comando atomico `VACUUM INTO`) con checkpoint WAL preventivo (`PRAGMA wal_checkpoint(TRUNCATE)`).
  - Verifica automatica di integrità tramite `PRAGMA integrity_check` prima dell'archiviazione e del trasferimento su NAS Synology.
- **Documenti Aggiornati:** `17-MEMORIA-SERVIZI-CONDIVISI.md`.

### 4.8 Sicurezza della Base Mobile (Modulo B2) — Elettronica, Frenata e Termini Tecnici
- **Incongruenza RP-01:** Veniva utilizzato impropriamente il termine "separazione galvanica" in presenza di masse collegate e si parlava di "arresto istantaneo in meno di 10 ms".
- **Rettifica Applicata:**
  - *Topologia Elettrica:* Sostituito con **massa comune a stella con filtraggio LC dedicato**, descrivendo accuratamente il circuito reale.
  - *Dinamica di Arresto:* Dettagliata la catena temporale reale del chip Toshiba TB6612FNG:
    1. Rilevamento ottico sensore cliff: ≤ 2 ms.
    2. Elaborazione interrupt MCU: ≤ 1 ms.
    3. Comando ponte H in modalità `BRAKE` attiva (`IN1=HIGH, IN2=HIGH`), seguito da `STBY = LOW`: ≤ 2 ms.
    4. Arresto elettrico della rotazione: ≤ 15 ms.
    5. Arresto meccanico effettivo: decelerazione inerziale dipendente da massa, velocità e attrito ruote (spazio di frenata stimato 5–20 mm).
  - *Prescrizione di Sicurezza:* Nei collaudi su superfici elevate è **obbligatorio l'uso di barriere fisiche di contenimento** o supporto ruote sollevate (*wheels-up*), senza fare affidamento esclusivo sui soli sensori per prevenire cadute.
- **Documenti Aggiornati:** `06-HARDWARE-PROFILES.md`, `24-SICUREZZA-PRESTAZIONI.md`.
