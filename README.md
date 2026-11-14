# JARVIS LEGO BOT

Assistente vocale da scrivania in italiano costruito con mattoncini LEGO, basato su **ESP32-S3 N16R8**, **Ollama (`qwen2.5:3b`)**, **faster-whisper** e voce personalizzata **Piper Riccardo (Amichetto Vivace)** su PC Windows 11.

---

## Manuali PDF Illustrati (`docs/manuals/`)

Per consultare rapidamente il progetto senza cercare tra i file Markdown tecnici, apri direttamente i **5 manuali A4 in PDF**:

1. [Manuale 1 — Presentazione Generale JARVIS](docs/manuals/01_Presentazione_Generale_JARVIS.pdf)
2. [Manuale 2 — Elettronica e Collegamenti](docs/manuals/02_Elettronica_e_Collegamenti.pdf)
3. [Manuale 3 — Costruzione LEGO Companion v2](docs/manuals/03_Costruzione_LEGO_Companion_v2.pdf)
4. [Manuale 4 — Software e Utilizzo Windows](docs/manuals/04_Software_e_Utilizzo_Windows.pdf)
5. [Manuale 5 — Collaudo e Manutenzione](docs/manuals/05_Collaudo_e_Manutenzione.pdf)

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
| **FASE 7** | Collaudo hardware reale, integrazione USB e montaggio finale LEGO | ⏳ Da iniziare all'arrivo dei componenti |

---

## Indice Documentazione

### Documenti Generali e FASE 1
- [FASE 1 – Analisi Tecnica Iniziale](docs/FASE_1_Analisi_Tecnica.md)
- [FASE 1 – Integrazione e Decisioni Definitive](docs/FASE_1_Integrazione_e_Decisioni.md)

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

### FASE 6 – Preparazione Elettronica ESP32-S3 e Integrazione USB (`06-Hardware-Integration/`)
- [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md) — Verifica pinout ESP32-S3-DevKitC-1 N16R8 e mappatura completa OLED, INMP441, MAX98357A, Speaker e Pulsante
- [WIRING_GUIDE.md](06-Hardware-Integration/WIRING_GUIDE.md) — Schema elettronico leggibile e regole di cablaggio su breadboard
- [AUDIO_ARCHITECTURE.md](06-Hardware-Integration/AUDIO_ARCHITECTURE.md) — Strategia audio bidirezionale su USB-CDC, formati PCM, banda, buffer e interruzioni
- [USB_PROTOCOL.md](06-Hardware-Integration/USB_PROTOCOL.md) — Protocollo binario multiplexato retrocompatibile con i comandi degli occhi
- [HARDWARE_TEST_PLAN.md](06-Hardware-Integration/HARDWARE_TEST_PLAN.md) — Piano di collaudo progressivo in 5 test indipendenti
- [HARDWARE_CHECKLIST.md](06-Hardware-Integration/HARDWARE_CHECKLIST.md) — Checklist elettrica all'arrivo e verifica meccanica per `jarvis_lego_bot_companion_hybrid_v2_visor.mpd`
- [GITHUB_REPOS_ANALYSIS.md](06-Hardware-Integration/GITHUB_REPOS_ANALYSIS.md) — Analisi tecnica e licenze dei repository GitHub di riferimento (`xiaozhi-esp32`, `xiaozhi-esp32-server`, `Carmoruda/Jarvis`, `deskbuddy`, `blinky-desk-companion`)

---

## Architettura di Riferimento (v1)
- **Hardware Robot:** ESP32-S3-DevKitC-1 N16R8 + Display OLED 1,3" 128×64 I2C (SH1106/SSD1306) + Microfono I2S INMP441 + Amplificatore I2S MAX98357A + Speaker 4 Ω / 3 W + Pulsante meccanico su `GPIO 47`.
- **Firmware:** Variante di `bread-compact-wifi` da [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) con `GPIO 39/40` disabilitati e comunicazione WebSocket su LAN.
- **Backend Raspberry Pi 5 (Debian 13 ARM64):** Stack Docker isolato *Server-Only* (`xiaozhi-esp32-server:server_latest` ARM64) con ASR italiano (`Vosk` / opz. `Whisper`), TTS (`EdgeTTS`), LLM online (con futura estensione `Ollama` su PC Windows 11) e bridge di telemetria isolato (`jarvis-sys-bridge` + `docker-socket-proxy` solo `GET`).

---

## Regole di Progetto
- Nessuna modifica o interruzione ai servizi esistenti sul Raspberry Pi 5.
- Nessuna credenziale o API key nei sorgenti (solo variabili d'ambiente / `.env`).
- Nessuna assunzione non verificata; segnalare sempre eventuali varianti hardware da confermare fisicamente.
