# JARVIS Robotics Platform — Audit Preliminare Esiti RP-02 e Verifiche Hardware

**Documento ID:** `RP-DOC-03-AUDIT-PRELIMINARE`  
**Fase di Riferimento:** RP-03 (Audit e Consolidamento Preliminare)  
**Data:** 24 Novembre 2026  
**Autore:** Piattaforma Robotica JARVIS  
**Stato:** Approvato — Correzioni Integrate

---

## 1. Obiettivo dell'Audit

Prima di avviare lo sviluppo applicativo della FASE RP-03, è stata eseguita una revisione critica e indipendente dei risultati della FASE RP-02 per individuare discrepanze hardware, lacune di validazione e imprecisioni documentali.

---

## 2. Risoluzione delle Criticità Identificate

### 2.1 Verifica Hardware e Pinout ESP32-S3 (Criticità Massima Risolta)
- **Problema Rilevato nel Report RP-02:**  
  Il report e i file hardware iniziali indicavano per il bus I2C0 del display OLED SH1106: `SDA = GPIO 21`, `SCL = GPIO 22`.  
- **Ispezione Hardware & Siliconica:**  
  1. **ESP32-S3 Datasheet:** I GPIO da 22 a 25 **non esistono fisicamente** sul silicio dell'ESP32-S3. L'assegnazione a GPIO 22 era un refuso ereditato dalla mappatura del classico ESP32-WROOM-32.
  2. **Codice Sorgente Reale (`04-Firmware/jarvis-desk-buddy/include/pinout_config.h`):**  
     L'OLED è configurato in modo inequivocabile su:  
     - **`kOledSda = 41`** (`J3-7`)  
     - **`kOledScl = 42`** (`J3-6`)  
     - Frequenza: `400 kHz Fast-Mode I2C`  
     - Indirizzo: `0x3C`
  3. **Carrier Board PCB V1 (`JARVIS_GPIO_MAPPING_PCB_V1.md`):**  
     La PCB ordinata a fabbricazione instrada le piste I2C0 esattamente su **GPIO 41** e **GPIO 42**.
  4. **Sensore Touch Capacitivo (TTP223):**  
     Nel firmware e nella specifica PCB V1 è attestato su **GPIO 1** (`kTouchTtp223`), e non su GPIO 14.
  5. **Profilo Mobile V2 (Trazione Differenziale TB6612FNG):**  
     Nel file iniziale di RP-02 i motori impegnavano erroneamente GPIO 41 e 42 (in collisione con l'OLED). Le assegnazioni sono state riordinate sui pin liberi dell'ESP32-S3:  
     `PWMA=11, AIN1=12, AIN2=13, PWMB=14, BIN1=39, BIN2=40, STBY=21, Cliff L=17, Cliff R=18`.
- **Azione Correttiva Applicata:**  
  Aggiornati formalmente `desktop-v1.hardware.json`, `mobile-v2.hardware.json` e `valid-hardware.json`.

---

### 2.2 Conteggio Effettivo dei Profili Istanziati
- **Discrepanza:** Il report RP-02 dichiarava genericamente "28 profili", mentre la somma analitica delle categorie ne conta 27.
- **Riconciliazione Effettiva:**
  - 5 Skin (`profiles/skins/`): `jarvis-original`, `eva-elegant`, `nova-hud`, `tars-geometric`, `neko-feline`
  - 5 Identità (`profiles/identities/`): `jarvis`, `eva`, `nova`, `tars`, `neko`
  - 5 Personalità (`profiles/personalities/`): `jarvis`, `eva`, `nova`, `tars`, `neko`
  - 3 Voci (`profiles/voices/`): `riccardo`, `paola`, `corrado`
  - 5 Wake Word (`profiles/wakewords/`): `hey-jarvis`, `hey-eva`, `hey-nova`, `hey-tars`, `hey-neko`
  - 3 Profili Hardware (`profiles/hardware/`): `desktop-v1`, `mobile-v2`, `custom-robot`
  - 1 Profilo Dispositivo (`profiles/devices/`): `jarvis-desk-01`
  - **Totale Reale = 27 profili ufficiali validati.**  
  *(Il valore 28 derivava dalla sovrapposizione mnemonica con i 28 capitoli della RP-01).*

---

### 2.3 Validazione Ufficiale JSON Schema Draft 2020-12
- È stato creato un ambiente virtuale Python dedicato alla piattaforma (`JARVIS-Robotics-Platform/.venv`), isolato dal Voice Bridge.
- È stata installata la libreria standard ufficiale `jsonschema` (versione 4.26.0) con motore `Draft202012Validator` e supporto per `referencing`.
- Implementato lo script di conformità formale [validators/validate_with_jsonschema.py](JARVIS-Robotics-Platform/validators/validate_with_jsonschema.py) per certificare tutti i 10 schemi contro il metaschema e verificare `$defs`, `$ref`, `oneOf`, `anyOf`, `allOf` e `additionalProperties: false`.

---

### 2.4 Separazione Maturità Capability vs Disponibilità su Dispositivo
- È stata formalmente ribadita la distinzione concettuale:
  - **Maturità Architetturale (`capability_lifecycle`):** Definisce lo stato di stabilità ingegneristica della feature a livello globale (`PROPOSED`, `EXPERIMENTAL`, `STABLE`, `DEPRECATED`, `RETIRED`).
  - **Disponibilità su Dispositivo (`device_capability_status`):** Una capability `STABLE` (es. `LOCAL_WAKEWORD` o `MOTOR_CONTROL`) è presente ed effettivamente attiva solo se il singolo dispositivo fisico possiede l'hardware necessario e la licenza firmware abilitata.

---

### 2.5 Tassonomia di Rollback e Livelli di Gestione
È stato formalizzato che il bootloader ESP32 gestisce unicamente il partizionamento a basso livello e non è responsabile dell'applicazione delle identità:
1. **Rollback Firmware OTA (Livello 0 - Bootloader ESP-IDF):**  
   Commuta tra partizione `app0` e `app1` leggendo lo stato `otadata` in caso di crash al boot (`esp_ota_mark_app_valid_cancel_rollback`).
2. **Rollback Configurazione & Identità (Livello 1 - Applicativo FreeRTOS):**  
   Gestito via software da `jarvis::identity::Manager` tramite record atomico NVS con puntatore `last_known_good_identity_id`. Se la nuova identità causa instabilità o allocazione fallita, l'applicazione ricarica l'identità precedente senza riavviare il chip.

---

### 2.6 Classificazione Obiettivi Prestazionali non ancora Misurati
Sono state formalmente riclassificate come **target progettuali da validare mediante benchmark futuri**:
- Commutazione identità < 15 ms (attualmente stima teorica senza I/O Flash dinamico).
- Ripristino database SQLite < 3 minuti (dipendente dalla dimensione effettiva su microSD).
- Distanza di arresto base mobile 5–20 mm (da misurare su banco con carichi inerziali reali).
- Caricamento dinamico contemporaneo di decine di modelli acustici wake word.
- Esecuzione simultanea di 3-4 agenti conversazionali su Raspberry Pi 5.

---

### 2.7 Sicurezza Pacchetti ZIP Reali e Revisione Ratio di Compressione
- Il limite di compressione teorico fisso di `10:1` è stato integrato con una soglia assoluta: per piccoli file JSON di pochi kilobyte, un ratio elevato non costituisce un pericolo. Il criterio di sicurezza primario diventa:
  `max_extracted_bytes <= 1.048.576` (1 MB assoluto) unitamente al divieto assoluto di Zip-Slip (`../`, `..\`, percorsi assoluti, symlink).
- Implementata suite di test su veri file `.zip` sintetici binari.
