# JARVIS LEGO BOT

Assistente vocale da scrivania in italiano costruito con mattoncini LEGO, basato su **ESP32-S3 N16R8**, **Ollama (`qwen2.5:3b`)**, **faster-whisper** e voce personalizzata **Piper Riccardo (Amichetto Vivace)** su PC Windows 11.

---

## Manuali PDF Illustrati (`docs/manuals/`)

Per consultare rapidamente il progetto senza cercare tra i file Markdown tecnici, apri direttamente i **6 manuali A4 in PDF**:

1. [Manuale 1 — Presentazione Generale JARVIS](docs/manuals/01_Presentazione_Generale_JARVIS.pdf)
2. [Manuale 2 — Elettronica e Collegamenti](docs/manuals/02_Elettronica_e_Collegamenti.pdf)
3. [Manuale 3 — Costruzione LEGO Companion v2](docs/manuals/03_Costruzione_LEGO_Companion_v2.pdf)
4. [Manuale 4 — Software e Utilizzo Windows](docs/manuals/04_Software_e_Utilizzo_Windows.pdf)
5. [Manuale 5 — Collaudo e Manutenzione](docs/manuals/05_Collaudo_e_Manutenzione.pdf)
6. [Manuale 6 — Personalità, Emozioni e Reazioni (FASE 7)](docs/manuals/06_Personalita_Emozioni_e_Reazioni.pdf)

*(Sorgenti HTML/SVG e script ripetibile `build_manuals.py` in `docs/manual-sources/`).*

---

## Stato Avanzamento Progetto

| Fase | Descrizione | Stato |
|---|---|---|
| **FASE 1** | Ricerca tecnica, validazione hardware e integrazione decisioni | ✅ Completata e approvata |
| **FASE 2** | Progettazione esecutiva hardware (schema, pinout, BOM, breadboard, test) | ✅ Completata e approvata (con collaudo termico in FASE 4) |
| **FASE 3** | Design LEGO e progetto costruttivo (Monoblocco modulare + Base intercambiabile) | ✅ Elaborati pronti in `03-Mechanical-Design/` (in attesa di approvazione) |
| **FASE 4** | Firmware `jarvis-desk-buddy` (occhi OLED 7 espressioni) + Simulatore Windows | ✅ Compilabile e testato su simulatore |
| **FASE 5** | Voice & AI su PC Windows 11 (`faster-whisper` + `Ollama qwen2.5:3b` + `Piper Riccardo Amichetto Vivace`) | ✅ Operativo su PC Windows 11 |
| **FASE 6** | Preparazione elettronica ESP32-S3, architettura audio USB e piano collaudo | ✅ Documentazione pronta (`06-Hardware-Integration/`), in attesa componenti |
| **FASE 7** | Emotion &amp; Reaction Engine (Personalità C, 14 espressioni OLED, integrato su PC/Simulatore) | ✅ Implementato e consolidato (`ab98924`) |
| **FASE 8** | Progettazione sensori (`VL53L0X`, `TTP223`, `MPU6050`, `BH1750`) + **FASE 8.1 Sensor Lab simulato** | ✅ Progetto e simulatore PC pronti (`06-Hardware-Integration/FASE_8_SENSORY_INTERACTION.md`); hardware da collaudare |

---

## Indice Documentazione

### Documenti Generali, FASE 1 e FASE 9
- [FASE 1 – Analisi Tecnica Iniziale](docs/FASE_1_Analisi_Tecnica.md)
- [FASE 1 – Integrazione e Decisioni Definitive](docs/FASE_1_Integrazione_e_Decisioni.md)
- [FASE 9.0 – Analisi e Progettazione JARVIS BRAIN 2.0](docs/FASE_9_JARVIS_BRAIN_2_0.md)

### FASE 2 – Hardware Storico (`archive/01-Hardware/`, archiviato — sostituito da `06-Hardware-Integration/` per v1 USB)
- [Elaborato A – Schema Elettronico, Alimentazione e Protezioni](archive/01-Hardware/01_Schema_Elettronico_e_Alimentazione.md)
- [Elaborato B – Tabella Pinout Definitiva](archive/01-Hardware/02_Tabella_Pinout_Definitiva.md)
- [Elaborati C & D – Distinta Componenti (BOM) e Stima Costi](archive/01-Hardware/03_Distinta_Componenti_BOM_e_Costi.md)
- [Elaborati E, F & G – Montaggio Breadboard, Trasferimento LEGO e Test Pre-Alimentazione](archive/01-Hardware/04_Montaggio_Breadboard_Collaudo_e_Trasferimento_LEGO.md)

### FASE 3 – Progettazione Meccanica Modulare (`03-Mechanical-Design/`)
- [Indice Cartella `03-Mechanical-Design`](03-Mechanical-Design/README.md)
- [Elaborato A – Progetto Visivo e Viste (Design Compatto)](03-Mechanical-Design/01_Progetto_Visivo_e_Viste.md)
- [Elaborato B – Interfaccia Universale, Base B1 e Futura Base B2 (2WD+Caster)](03-Mechanical-Design/02_Progetto_Modulare_e_Mobilita.md)
- [Elaborato C – Progetto Interno, Ingombri Reali, Acustica e Raffreddamento](03-Mechanical-Design/03_Progetto_Interno_e_Raffreddamento.md)
- [Elaborato D – Distinta Costruttiva, Base Mobile e Verifiche](03-Mechanical-Design/04_Distinta_Costruttiva_e_Verifiche.md)
- **Estensione Elettrica Base Mobile B2 (`03-Mechanical-Design/05-Mobile-Electronics/` — progettazione documentale chiusa, prove su banco da eseguire):**
  - [01 – Architettura Elettrica B2](03-Mechanical-Design/05-Mobile-Electronics/01_Architettura_Elettrica_B2.md)
  - [02 – Alimentazione, Protezione Stallo INA3221, Termica e Batteria 2S](03-Mechanical-Design/05-Mobile-Electronics/02_Schema_Alimentazione_B2.md)
  - [03 – Controllo Motori, UART, Anticollisione e Matrice Fail-Safe](03-Mechanical-Design/05-Mobile-Electronics/03_Controllo_Motori_UART_TB6612.md)
  - [04 – Pinout Connettore JST-XH 6 Pin](03-Mechanical-Design/05-Mobile-Electronics/04_Pinout_Connettore_JST-XH.md)
  - [05 – BOM Elettrica Preliminare B2](03-Mechanical-Design/05-Mobile-Electronics/05_BOM_Elettrica_B2.md)
  - [06 – Procedure di Sicurezza, Collaudo e Tabella Approvazione B2](03-Mechanical-Design/05-Mobile-Electronics/06_Procedure_Sicurezza_e_Collaudo.md)
- Render compatto: [Vista Prospettica Compatta](03-Mechanical-Design/images/jarvis_compact_perspective.jpg)

*(Nota: la precedente bozza Testa+Collo+Busto in `archive/02-LEGO/` e le vecchie iterazioni `06..09` in `archive/legacy-mechanical-design/` sono state archiviate. Il design LEGO definitivo attivo è [Companion Hybrid v2 — Visiera Capsula Arrotondata SNOT](03-Mechanical-Design/10-Restyling-LEGO-Companion/Istruzioni_Montaggio_Companion_Hybrid_v2_Visor.md)).*

### FASE 6 & FASE 8.2B-0 – Preparazione Elettronica ESP32-S3, Schemi e Guida al Montaggio (`06-Hardware-Integration/`)
- [GUIDA_MONTAGGIO_ELETTRONICA.md](06-Hardware-Integration/GUIDA_MONTAGGIO_ELETTRONICA.md) — **Guida illustrata passo per passo al montaggio, verifiche elettriche, collaudo in 6 test e integrazione LEGO `Companion Hybrid v2`** (con schemi SVG in `06-Hardware-Integration/images/`: [Schema Generale](06-Hardware-Integration/images/01_schema_elettrico_generale.svg), [Test 1-3](06-Hardware-Integration/images/02_test_1_2_3_esp32_oled_pulsante.svg), [Test 4-5 Audio](06-Hardware-Integration/images/03_test_4_5_audio_i2s.svg), [Test 6 Sensori](06-Hardware-Integration/images/04_test_6_sensori_i2c_touch.svg), [Esploso LEGO](06-Hardware-Integration/images/05_integrazione_lego_esploso.svg))
- [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md) — Verifica pinout ESP32-S3-DevKitC-1 N16R8 e mappatura completa OLED, INMP441, MAX98357A, Speaker e Pulsante
- [WIRING_GUIDE.md](06-Hardware-Integration/WIRING_GUIDE.md) — Schema elettronico leggibile e regole di cablaggio su breadboard
- [AUDIO_ARCHITECTURE.md](06-Hardware-Integration/AUDIO_ARCHITECTURE.md) — Strategia audio bidirezionale su USB-CDC, formati PCM, banda, buffer e interruzioni
- [USB_PROTOCOL.md](06-Hardware-Integration/USB_PROTOCOL.md) — Protocollo binario multiplexato retrocompatibile con i comandi degli occhi
- [HARDWARE_TEST_PLAN.md](06-Hardware-Integration/HARDWARE_TEST_PLAN.md) — Piano di collaudo progressivo in 5 test indipendenti
- [HARDWARE_CHECKLIST.md](06-Hardware-Integration/HARDWARE_CHECKLIST.md) — Checklist elettrica all'arrivo e verifica meccanica per `jarvis_lego_bot_companion_hybrid_v2_visor.mpd`
- [GITHUB_REPOS_ANALYSIS.md](06-Hardware-Integration/GITHUB_REPOS_ANALYSIS.md) — Analisi tecnica e licenze dei repository GitHub di riferimento (`xiaozhi-esp32`, `xiaozhi-esp32-server`, `Carmoruda/Jarvis`, `deskbuddy`, `blinky-desk-companion`)

---

## Architettura di Riferimento

### Architettura Attuale (Windows 11 + ESP32-S3, `main`)
- **Hardware Robot:** ESP32-S3-DevKitC-1 N16R8 + Display OLED 1,3" 128×64 I²C (`SH1106`/`SSD1306`) + Pulsante meccanico (`GPIO 47`) + predisposizione audio I²S (`INMP441`, `MAX98357A`, Speaker 36 mm 4 Ω / 3 W) e sensori (`VL53L0X`, `TTP223`, `MPU6050`, `BH1750`).
- **Firmware ESP32-S3:** `04-Firmware/jarvis-desk-buddy/` (14 espressioni OLED, protocollo seriale USB-CDC `PING`/`STATUS`/`DIAG`/`STATE`/`LOOK`, stub sensori `FASE 8.2A`).
- **Voice AI & Simulatore su PC Windows 11:** `05-Voice-AI/` (`faster-whisper` + `Ollama qwen2.5:3b` + voce personalizzata `Piper Riccardo Amichetto Vivace`) + `04-Firmware/jarvis-desk-buddy-sim/` (`EmotionEngine` Personalità C e `Sensor Lab`).

### Architettura Storica (v1 iniziale, FASE 6)
- **Firmware iniziale di riferimento:** variante di `bread-compact-wifi` da [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) con `GPIO 39/40` disabilitati e comunicazione WebSocket su LAN.
- **Backend Raspberry Pi 5 (Debian 13 ARM64):** stack Docker isolato *Server-Only* (`xiaozhi-esp32-server:server_latest` ARM64) con ASR (`Vosk`/`Whisper`), TTS (`EdgeTTS`) e bridge di telemetria isolato (`jarvis-sys-bridge` + `docker-socket-proxy` solo `GET`).

---

## Avvio JARVIS Control Center & Stato Collaudo Software (Windows 11)

### Avvio rapido
- **Avvio normale (Voice AI reale: Microfono + faster-whisper + Ollama + Piper):**
  - Doppio clic su `Start_JARVIS_Control_Center.bat`, oppure da PowerShell:
    ```powershell
    & "05-Voice-AI\.venv\Scripts\python.exe" "05-Voice-AI\jarvis_app.py"
    ```
  - Per disabilitare le iniziative vocali spontanee in modalità normale:
    ```powershell
    & "05-Voice-AI\.venv\Scripts\python.exe" "05-Voice-AI\jarvis_app.py" --no-spontaneous
    ```
- **Avvio in modalità Demo leggera (senza STT/Ollama/Piper/spontanee):**
  ```powershell
  & "05-Voice-AI\.venv\Scripts\python.exe" "05-Voice-AI\jarvis_app.py" --demo
  ```

### Stato effettivo del collaudo
- ✅ **Software Windows 11 collaudato**: Control Center a 8 schede, simulatore OLED fluido, scheda Memoria (L2/L3/L4 con consenso esplicito, ricerca, filtri, modifica/eliminazione), integrazione memoria con `Ollama qwen2.5:3b` e conversazione vocale reale end-to-end (`Microfono` → `faster-whisper` → `Ollama qwen2.5:3b` → `Piper Riccardo`).
- ⏳ **Hardware fisico ESP32-S3**: non ancora testato fisicamente; il collaudo su scheda reale e periferiche resta da eseguire.

---

## Regole di Progetto
- Nessuna modifica o interruzione ai servizi esistenti sul Raspberry Pi 5.
- Nessuna credenziale o API key nei sorgenti (solo variabili d'ambiente / `.env`).
- Nessuna assunzione non verificata; segnalare sempre eventuali varianti hardware da confermare fisicamente.
