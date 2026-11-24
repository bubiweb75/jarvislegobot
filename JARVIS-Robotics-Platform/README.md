# JARVIS Robotics Platform — Documentazione Ufficiale

> **FASE RP-01 & FASE RP-02 — Architettura, Contratti, Specifiche Formali e Schemi JSON**  
> **Data:** 24 Novembre 2026  
> **Revisione di Riferimento Analizzata:** Git commit `53f1bce` + Uncommitted Working Tree FASE 13.7 (19/11/2026)  
> **Vincolo Operativo:** Documentazione architetturale in sola lettura rispetto al progetto principale. Nessuna modifica al firmware primario, all'hardware o ai servizi di produzione.

---

## 1. Visione e Obiettivi della Piattaforma

La **JARVIS Robotics Platform** rappresenta l'evoluzione controllata e modulare del progetto *JARVIS LEGO BOT / JARVIS ESP32* in una piattaforma robotica unificata per la creazione di robot fisici eterogenei (statici da scrivania, basi mobili 2WD, involucri LEGO, scocche custom in stampa 3D).

L'obiettivo fondamentale è:
1. **Preservare integralmente** il robot capostipite **JARVIS** (tutte le funzionalità, la grafica *Organic Visor Companion* di Eyes 3.0, l'audio I2S, la personalità e l'hardware Carrier Board).
2. **Abilitare la creazione di nuovi robot multi-identità** senza dover riscrivere il firmware da zero, consentendo per ciascun robot:
   - Nome personalizzato indipendente.
   - Wake word individuale (locale su MCU con fallback o selezione runtime).
   - Identità visiva ed espressiva autonoma (Skin Engine basato esclusivamente sugli occhi).
   - Voce dedicata (Voice Engine TTS multi-provider).
   - Personalità conversazionale e profilo emotivo indipendenti (Personality Engine).
   - Memoria episodica e contestuale separata per Device ID.
   - Configurazione hardware modulare (Hardware Profiles).
   - Gestione coordinata multi-dispositivo tramite applicazione web centralizzata (**JARVIS Identity Studio**).

---

## 2. Struttura del Repository di Piattaforma

La piattaforma è organizzata nelle seguenti sezioni modulari:

```
JARVIS-Robotics-Platform/
├── schemas/         <- 10 Schemi JSON Draft 2020-12 rigorosi e offline-validati
├── contracts/       <- Contratti API OpenAPI 3.1, WebSocket v1, Specifica Pacchetti
├── profiles/        <- Profili ufficiali istanziati (Skins, Identities, Voices, Wakewords, HW)
│   ├── skins/
│   ├── identities/
│   ├── personalities/
│   ├── voices/
│   ├── wakewords/
│   ├── hardware/
│   └── devices/
├── docs/            <- Registro evidenze tecniche, errata RP-01 e studi di dettaglio
├── validators/      <- Motori di validazione isolati Python (sintattico e semantico)
├── fixtures/        <- Fixture di test valide e negative per regressione
├── tests/           <- Test suite automatica unitaria (15 test, 100% pass)
├── reports/         <- Report consuntivi formali di fase (RP-01 e RP-02)
└── *.md             <- 28 Documenti monografici di architettura e progettazione
```

---

## 3. Indice dei Conseguibili della FASE RP-02

### 3.1 Schemi JSON Formali (`schemas/`)
- [common.schema.json](JARVIS-Robotics-Platform/schemas/common.schema.json) — Tipi condivisi (semver, sha256, date ISO-8601, stati operativi).
- [skin.schema.json](JARVIS-Robotics-Platform/schemas/skin.schema.json) — Geometrie superellittiche, 14 espressioni Eyes 3.0 e micro-espressioni.
- [identity.schema.json](JARVIS-Robotics-Platform/schemas/identity.schema.json) — Profilo logico d'identità disaccoppiato dall'hardware.
- [voice.schema.json](JARVIS-Robotics-Platform/schemas/voice.schema.json) — Calibrazione e routing sintesi vocale TTS multi-provider.
- [wakeword.schema.json](JARVIS-Robotics-Platform/schemas/wakeword.schema.json) — Modelli acustici neurali quantizzati INT8 per ascolto continuo.
- [personality.schema.json](JARVIS-Robotics-Platform/schemas/personality.schema.json) — Prompt di sistema, slider comportamentali e intenti locali.
- [hardware.schema.json](JARVIS-Robotics-Platform/schemas/hardware.schema.json) — Pinout GPIO, caratteristiche elettroniche e pin riservati.
- [device.schema.json](JARVIS-Robotics-Platform/schemas/device.schema.json) — Telemetria, pairing e configurazione del robot fisico.
- [capability.schema.json](JARVIS-Robotics-Platform/schemas/capability.schema.json) — Matrice delle 15 capacità e ciclo di vita formale.
- [package.schema.json](JARVIS-Robotics-Platform/schemas/package.schema.json) — Manifest di distribuzione pacchetti `.jarvis-*`.

### 3.2 Contratti di Interfaccia (`contracts/`)
- [openapi-identity-studio.yaml](JARVIS-Robotics-Platform/contracts/openapi-identity-studio.yaml) — Specifica REST OpenAPI 3.1.
- [websocket-protocol-v1.md](JARVIS-Robotics-Platform/contracts/websocket-protocol-v1.md) — Protocollo bidirezionale WebSocket.
- [package-specification.md](JARVIS-Robotics-Platform/contracts/package-specification.md) — Formato pacchetti, protezione Zip-Slip e firma Ed25519.
- [capability-matrix.md](JARVIS-Robotics-Platform/contracts/capability-matrix.md) — Matrice formale delle capacità a 5 stati.

### 3.3 Studi Architetturali di Dettaglio (`docs/`)
- [00-REVISIONE-CORREZIONI-RP01.md](JARVIS-Robotics-Platform/docs/00-REVISIONE-CORREZIONI-RP01.md) — Audit delle 8 correzioni obbligatorie applicate.
- [01-REGISTRO-EVIDENZE-TECNICHE.md](JARVIS-Robotics-Platform/docs/01-REGISTRO-EVIDENZE-TECNICHE.md) — Mappatura sorgenti C++, commit Git e registri.
- [STUDIO-PARTIZIONI-ESP32S3.md](JARVIS-Robotics-Platform/docs/STUDIO-PARTIZIONI-ESP32S3.md) — Analisi del margine flash (1.25 MB vs 16 MB) e schema Dual OTA 4MB.
- [APPLICAZIONE-ATOMIC-CONFIGURAZIONI.md](JARVIS-Robotics-Platform/docs/APPLICAZIONE-ATOMIC-CONFIGURAZIONI.md) — Transazione atomica Safe Deferred Apply in IDLE con rollback a LKG.
- [BACKUP-RIPRISTINO-SQLITE.md](JARVIS-Robotics-Platform/docs/BACKUP-RIPRISTINO-SQLITE.md) — Backup coerente SQLite WAL tramite API native e replica su NAS Synology.
- [SPECIFICHE-SIMULATORE-RP03.md](JARVIS-Robotics-Platform/docs/SPECIFICHE-SIMULATORE-RP03.md) — Specifiche tecniche del simulatore oculare HTML5 Canvas / TypeScript per RP-03.
- [STRATEGIA-SVILUPPO-PARALLELO.md](JARVIS-Robotics-Platform/docs/STRATEGIA-SVILUPPO-PARALLELO.md) — Strategia di isolamento e tracciamento continuo upstream.

### 3.4 Validatori e Test Suite
- `validators/validate_schemas.py` — Validatore JSON Schema Draft 2020-12 offline.
- `validators/validate_semantic.py` — Validatore semantico GPIO, Zip-Slip, checksum e geometrie.
- `tests/test_platform_schemas.py` — Test suite automatizzata (15 test, 100% pass rate).

### 3.5 Report Conclusivo
- [REPORT-FASE-RP02.md](JARVIS-Robotics-Platform/reports/REPORT-FASE-RP02.md) — Relazione formale conclusiva per la FASE RP-02.

---

## 4. Conseguibili della FASE RP-03 (Eyes 3.0 Simulator & Identity Studio)

### 4.1 Frontend Web & Simulatore (`frontend/`)
- **Architettura:** React 18, TypeScript 5.6, Vite 6, Tailwind CSS, Canvas 2D, Vitest.
- **Porting Matematico 1:1:** Implementazione deterministica dell'algoritmo C++ Eyes 3.0 (`EyeEngine.ts`) con rendering superellittico $p=2.6$, curvatura palpebrale, saccadi PRNG xorshift32, 14 espressioni canoniche, 5 micro-espressioni e profili CALM/LIVELY/PLAYFUL.
- **Monochrome Framebuffer:** 128x64 monocromatico 1-bit, 1024 byte, esportazione bit-exact in formato C++ XBM compatibile con U8g2 e driver SH1106.
- **Reattività Vocale Audio:** Simulatore d'inviluppo RMS con modulazione sillabica e caricamento file audio WAV locali via Web Audio API (esclusivamente reattività oculare, zero bocca/viso).
- **Simulatore Eventi Interattivi:** Dispatcheur di eventi fisici (PTT, Touch GPIO1 single/double/long, Wakeword, Thinking, Speaking, Sleep, Wakeup).
- **Skin Studio Parametrico:** Editor geometrico in tempo reale con import/export JSON conforme a `skin.schema.json`.
- **Catalogo Identità:** Navigatore delle 5 identità (JARVIS Original Premium, EVA, NOVA, TARS, NEKO).
- **Comparatore Dual-OLED:** Studio side-by-side a doppio schermo con sincronizzazione di clock, stepping manuale a frame e calcolo del delta geometrico/ottico.

### 4.2 Test e Convalida
- **Vitest Unit Suite:** 19/19 test superati al 100% (`framebuffer.test.ts`, `eyeEngine.test.ts`, `eventSimulator.test.ts`, `audioSimulator.test.ts`).
- **Validazione Python Draft 2020-12:** 10 schemi conformi al metaschema, 27 profili ufficiali e fixture convalidate al 100%.
- **Test Sicurezza ZIP Sintetici:** 6 test di sicurezza (Zip-Slip traversal `../` e `..\`, checksum mismatch, asset non autorizzati, limite 1MB).
- **Server di Sviluppo Locale:** Attivo e verificato su `http://127.0.0.1:5173/`.

### 4.3 Report Ufficiale RP-03
- [REPORT-FASE-RP03.md](JARVIS-Robotics-Platform/reports/REPORT-FASE-RP03.md) — Relazione formale conclusiva a 22 punti della FASE RP-03.

