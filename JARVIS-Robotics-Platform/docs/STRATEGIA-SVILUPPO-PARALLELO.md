# JARVIS Robotics Platform — Strategia di Sviluppo Parallelo e Tracciamento Upstream

**Documento ID:** `RP-DOC-02-UPSTREAM-TRACKING`  
**Fase di Riferimento:** RP-02 (Consolidamento Architetturale e Specifiche Formali)  
**Data:** 24 Novembre 2026  
**Autore:** Piattaforma Robotica JARVIS  
**Stato:** Approvato per Progettazione

---

## 1. Contesto e Vincolo di Non-Interferenza

Il progetto **JARVIS LEGO BOT / JARVIS ESP32** si trova in uno stato di attivo sviluppo parallelo (attualmente alla FASE 13.7 con revisione git `HEAD 53f1bce`).  
La **JARVIS Robotics Platform** ha il compito strategico di ingegnerizzare l'ecosistema multi-robot senza mai interferire, ritardare o alterare i sorgenti, il firmware o i test di laboratorio del robot originale.

---

## 2. Architettura di Isolamento Operativo

Per garantire l'assoluta integrità dei due rami di lavoro, è adottato il modello a compartimenti stagni:

```

│
├── [AREA UPSTREAM - READ-ONLY]
│   ├── 01-Firmware-ESP32/       <-- Codice sorgente C++ Eyes 3.0, Audio, Drivers (SOLA LETTURA)
│   ├── 02-Hardware-PCB/         <-- Gerber, KiCad, Schemi Carrier Board (SOLA LETTURA)
│   ├── 03-Docs/                 <-- Documentazione fasi JARVIS ESP32 (SOLA LETTURA)
│   └── 05-Voice-AI/             <-- Python backend, Piper TTS, Xiaozhi (SOLA LETTURA)
│
└── [AREA PIATTAFORMA - WRITE ALLOWED]
    └── JARVIS-Robotics-Platform/ <-- ESCLUSIVO perimetro di scrittura RP-01..RP-05
        ├── schemas/             <-- Schemi formali JSON Draft 2020-12
        ├── contracts/           <-- Specifiche OpenAPI, WebSocket, Pacchetti
        ├── profiles/            <-- Profili JSON validati (Skins, Identities, Voices, HW)
        ├── validators/          <-- Motori di validazione isolati Python
        ├── fixtures/            <-- Casi di test validi e negativi
        ├── tests/               <-- Test suite automatica di piattaforma
        └── docs/                <-- Studi architetturali ed evidenze tecniche
```

---

## 3. Registro e Monitoraggio dei Cambiamenti Upstream

Ad ogni nuova sessione di lavoro sulla piattaforma, viene eseguito il protocollo di sincronizzazione informativa in sola lettura:

1. **Lettura del Commit Git Corrente:**
   ```bash
   git log -1 --oneline
   # Verifica dell'hash di commit e dell'ultimo messaggio di release
   ```
2. **Ispezione dello Stato della Working Tree:**
   ```bash
   git status --short
   # Verifica se vi sono file modificati o non tracciati nel progetto principale
   ```
3. **Controllo dei file di registro hardware (`03-Docs/`):**
   - Verifica di aggiornamenti sullo stato della Carrier Board (ricezione, montaggio, collaudo elettrico).
   - Verifica dell'aggiunta di nuove espressioni grafiche in `eye_engine.h`.
   - Verifica di modifiche ai GPIO o al mapping dei pin I2S/I2C.
4. **Aggiornamento di `docs/01-REGISTRO-EVIDENZE-TECNICHE.md`:**
   - Qualsiasi variazione rilevata nell'upstream viene annotata nel registro formale delle evidenze tecniche senza alterare i sorgenti C++.

---

## 4. Astrazione Hardware (HAL) e Disaccoppiamento

La piattaforma introduce un'interfaccia logica tra l'applicazione e l'hardware, definita in `schemas/hardware.schema.json`:

- Il firmware applicativo JARVIS Core non indirizza direttamente numeri fissi di GPIO (`#define PIN 21`), ma interroga la struttura del profilo hardware attivo caricato dal profilo `hardware_profile_id`.
- Se il progetto principale JARVIS aggiorna un pinout per la Carrier Board V2, l'aggiornamento richiede esclusivamente la creazione di un nuovo file JSON (es. `desktop-v2.hardware.json`), lasciando intatto il codice comune del motore grafico e della personalità.

---

## 5. Criteri di Convergenza Futura (Fasi RP-04 e RP-05)

Quando la piattaforma passerà alle fasi di implementazione del codice (`RP-04`) e test su hardware (`RP-05`):
- Il codice di JARVIS Core verrà integrato mantenendo al 100% l'identità e il firmware originale di JARVIS come profilo hardware e identità predefinita di default (*Golden Master*).
- Non sarà mai consentito un refactoring che pregiudichi o regredisca le prestazioni, la fluidità grafica o la reattività acustica raggiunte da JARVIS LEGO BOT nel progetto principale.
