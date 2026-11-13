# JARVIS LEGO BOT

Assistente vocale da scrivania in italiano costruito con mattoncini LEGO classici e LEGO Technic, basato su **ESP32-S3 N16R8**, firmware open source **XiaoZhi ESP32** e backend **Docker ARM64** su **Raspberry Pi 5**.

---

## Stato Avanzamento Progetto

| Fase | Descrizione | Stato |
|---|---|---|
| **FASE 1** | Ricerca tecnica, validazione hardware e integrazione decisioni | ✅ Completata e approvata |
| **FASE 2** | Progettazione esecutiva hardware (schema, pinout, BOM, breadboard, test) | ✅ Completata e approvata (con collaudo termico in FASE 4) |
| **FASE 3** | Design LEGO e progetto costruttivo (Monoblocco modulare + Base intercambiabile) | ✅ Elaborati pronti in `03-Mechanical-Design/` (in attesa di approvazione) |
| **FASE 4** | Firmware `xiaozhi-esp32` e prima conversazione vocale | ⏳ Da iniziare |
| **FASE 5** | Backend Raspberry Pi 5 (Docker ARM64, ASR/TTS/LLM italiano, Bridge sicuro) | ⏳ Da iniziare |
| **FASE 6** | Personalizzazione volto animato OLED e personalità JARVIS | ⏳ Da iniziare |
| **FASE 7** | Test finale integrato e documentazione completa | ⏳ Da iniziare |

---

## Indice Documentazione

### Documenti Generali e FASE 1
- [FASE 1 – Analisi Tecnica Iniziale](docs/FASE_1_Analisi_Tecnica.md)
- [FASE 1 – Integrazione e Decisioni Definitive](docs/FASE_1_Integrazione_e_Decisioni.md)

### FASE 2 – Hardware (`01-Hardware/`)
- [Elaborato A – Schema Elettronico, Alimentazione e Protezioni](01-Hardware/01_Schema_Elettronico_e_Alimentazione.md)
- [Elaborato B – Tabella Pinout Definitiva](01-Hardware/02_Tabella_Pinout_Definitiva.md)
- [Elaborati C & D – Distinta Componenti (BOM) e Stima Costi](01-Hardware/03_Distinta_Componenti_BOM_e_Costi.md)
- [Elaborati E, F & G – Montaggio Breadboard, Trasferimento LEGO e Test Pre-Alimentazione](01-Hardware/04_Montaggio_Breadboard_Collaudo_e_Trasferimento_LEGO.md)

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

*(Nota: la precedente bozza Testa+Collo+Busto in `02-LEGO/` è stata superata dalla decisione progettuale Monoblocco Modulare in `03-Mechanical-Design/`).*

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
