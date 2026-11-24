# 02 — Stato Reale del Firmware e dell'Hardware Esistente

> **JARVIS Robotics Platform** — Documento di Ispezione Tecnica della Baseline  
> **Fase:** RP-01  
> **Data:** 24 Novembre 2026  
> **Revisione Git Analizzata:** `HEAD` @ commit `53f1bce test(hardware): validate Eyes 3.0 on ESP32-S3 SH1106` + Working Tree fino a **FASE 13.7** (19/11/2026)  

---

## 1. Metodologia di Ispezione

L'analisi dello stato reale del progetto JARVIS è stata condotta direttamente sui sorgenti C++, header, configurazioni PlatformIO, script Python, log di collaudo fisico e documenti tecnici presenti nel repository.

A differenza di una ricognizione generica, è stata effettuata una **verifica di corrispondenza codice-hardware** per accertare quali funzionalità siano effettivamente compilate e collaudate a banco sull'hardware reale (ESP32-S3 MAC `<ESP32_MAC_ADDRESS>`, display SH1106, audio I2S, pulsante PTT e touch).

---

## 2. Classificazione Rigorosa delle Funzionalità

Per evitare di considerare operative tecnologie solo teorizzate nei manuali, lo stato di avanzamento è suddiviso nelle 5 categorie formali richieste dalle linee guida:

### 2.1 Categoria 1: Funzionalità Implementate e Collaudate su Hardware Fisico

| Componente / Modulo | Percorso Sorgente Verificato | Dettaglio Tecnico e Riferimento Collaudo |
|---|---|---|
| **Eyes 3.0 (*Organic Visor Companion*)** | `04-Firmware/jarvis-desk-buddy/src/eye_engine.cpp`<br>`04-Firmware/arduino-hw-test/jarvis_eyes3_hw_test/` | Geometria organica superellittica (38×38 px, `shape_power=2.6`, `taper=0.10`, `corner_radius=11`, `spacing=16 px`). 14 espressioni, 5 micro-espressioni contestuali, Natural Gaze, Advanced Blink, 3 profili visivi (`CALM`, `LIVELY`, `PLAYFUL`). Collaudato a 30 FPS su OLED SH1106 (I2C `GPIO41/42`, `0x3C`, 400 kHz). |
| **Driver Display SH1106 / SSD1306** | `04-Firmware/jarvis-desk-buddy/src/display_driver.cpp` | Driver `U8g2` con gestione nativa dell'offset +2px su SH1106 (132×64 RAM). Monocromatico 128×64 tramite framebuffer statico XBM (1024 byte, zero allocazioni dinamiche). |
| **Pulsante PTT Fisico (GPIO47)** | `04-Firmware/jarvis-desk-buddy/src/state_machine.cpp`<br>`.../jarvis_wifi_voice_client/button_controller.cpp` | Input digitale attivo LOW con pull-up interno e debounce software a 35 ms. Gestione pressione breve, pressione prolungata (1500 ms) e cancellazione immediata in riproduzione audio. Collaudato fisicamente. |
| **Touch Capacitivo TTP223B (GPIO1)** | `04-Firmware/jarvis-desk-buddy/src/touch_manager.cpp` | Gestore gesture non bloccante attivo HIGH: `TOUCH_SINGLE`, `TOUCH_DOUBLE`, `TOUCH_LONG`, `TOUCH_RELEASE`. Filtraggio software e reazioni visive integrate. Collaudato con flag `-DJARVIS_ENABLE_TOUCH=1`. |
| **Audio I2S Full-Duplex FreeRTOS** | `04-Firmware/arduino-hw-test/jarvis_duplex_rtos_hw_test/` | Architettura dual-core: Core 0 dedicato ai task real-time `AudioCapture` (I2S0 RX, INMP441 su GPIO 4, 5, 6, 16 kHz 16-bit mono) e `AudioPlayback` (I2S1 TX, MAX98357A su GPIO 7, 15, 16, speaker 4Ω 3W). Zero interferenze con OLED. |
| **Streaming Wi-Fi & Protocollo WebSocket** | `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/`<br>`05-Voice-AI/voice_bridge/esp_protocol.py` | Client WebSocket `Links2004/arduinoWebSockets` su Core 1 con code FreeRTOS thread-safe. Connessione cifrata WSS verso Voice Bridge (`/ws/v1/esp32`), scambio frame JSON di controllo e streaming binario PCM16 16 kHz. |
| **Pipeline Vocale Voice Bridge (Host)** | `05-Voice-AI/voice_bridge/` | Server FastAPI locale con STT `faster-whisper`, Router AI Ibrido (Ollama `qwen2.5:3b` locale + Cloud fallback), TTS `Piper` con voce italiana `it_IT-riccardo-x_low.onnx`, ottimizzazione WSOLA (Profile B 1.00x) e normalizzazione audio. |
| **microWakeWord "Hey Jarvis" locale** | `04-Firmware/experiments/fase13_3-integrated/` | Inferenza locale su ESP32-S3 tramite rete INT8 TFLite Micro streaming. Riconoscimento continuo "Hey Jarvis" integrato con Voice Activity Detection (VAD), pre-roll 500 ms, holdoff 300 ms anti-ri-trigger. Collaudato con successo in **FASE 13.7** (15 sessioni consecutive, >10 minuti senza memory leak, zero falsi positivi). |
| **Carrier Board PCB V1 (File di Produzione)** | `JARVIS_CARRIER_BOARD_V1_FINAL/`<br>`JARVIS_CARRIER_BOARD_V1_PRODUZIONE/` | Scheda PCB a 2 layer progettata e sbrogliata in KiCad per modulo companion 10×10 stud. Compatibilità progettuale verificata e file di produzione (Gerber, BOM, CPL) generati e ordinati per fabbricazione JLCPCB. *(Nota di rigore: i collaudi funzionali precedenti sono stati condotti su cablaggio prototipale; l'assemblaggio, il collaudo elettrico e funzionale della PCB V1 fisica avverranno al momento della consegna).* |

### 2.2 Categoria 2: Funzionalità Implementate ma non ancora Collaudate a Banco Fisico

| FunzionalitÃ  | Sorgente / Riferimento | Motivazione e Stato Attuale |
|---|---|---|
| **Sensori Ambientali I2C Esterni** | `sensor_stub.h`, `pinout_config.h` | Mappatura logica pronta per sensore ToF `VL53L0X` (0x29), IMU `MPU6050` (0x68) e Luxmetro `BH1750` (0x23). Driver implementati come stub; hardware non ancora saldato sui prototipi. |
| **Gestione Connessione TLS WSS con CA Custom** | `jarvis_wifi_voice_client.ino` | Codice predisposto per autenticazione bidirezionale con certificato CA incorporato; nei test LAN attuali è stata utilizzata cifratura self-signed / LAN trust. |

### 2.3 Categoria 3: Funzionalità in Sviluppo

| FunzionalitÃ  | Percorso / Riferimento | Note di Avanzamento |
|---|---|---|
| **Promozione Firmware FASE 13 a Ramo Stabile** | `04-Firmware/experiments/fase13_3-integrated/` | La build unificata (Eyes 3.0 + Duplex Audio + microWakeWord) è stata collaudata a banco ma non è ancora stata promossa formalmente in `04-Firmware/jarvis-desk-buddy/`. |
| **Simulatore Desktop Integrato v3** | `04-Firmware/jarvis-desk-buddy-sim/compare_eyes_v2_v3.py` | Script comparativo funzionante in Python; interfaccia GUI in wxPython/Tkinter parzialmente disallineata rispetto alle ultime micro-espressioni C++. |

### 2.4 Categoria 4: Funzionalità Pianificate

| FunzionalitÃ  | Riferimento Architetturale | Descrizione |
|---|---|---|
| **Base Mobile 2WD (Modulo B2)** | `03-Mechanical-Design/02_Progetto_Modulare_e_Mobilita.md` | Meccanica a due motoriduttori N20 con ruota libera caster, driver `TB6612FNG`, alimentazione 2S LiPo con buck 5V e connettore ombelicale JST a 6 pin. |
| **Aggiornamenti Firmware OTA Dual-Partition** | Tabella partizioni ESP32 | Presenza della partizione `app1` (1.25 MB); logica di download e switch OTA pianificata ma non integrata nel flusso operativo. |

### 2.5 Categoria 5: Funzionalità Ipotizzate (Non Implementate)

| Concetto Ipotizzato | Valutazione Tecnica nei Sorgenti |
|---|---|
| **Protocollo Nativo Xiaozhi Cloud** | Citato storicamente in analisi preliminari, ma **totalmente assente** nei sorgenti effettivi. L'architettura reale è basata sul sistema proprietario **Voice Bridge**. |
| **Cambio Dinamico delle Wake Word da NVS** | Il firmware attuale include un modello INT8 compilato staticamente nel codice C++ (`const uint8_t hey_jarvis_model[]`). Non esiste un loader dinamico di modelli da partizione dati. |
| **Clonazione Vocale e TTS Arbitrari su ESP32** | L'ESP32-S3 funge esclusivamente da endpoint audio streaming (PCM16 16 kHz). Tutta la sintesi vocale e i modelli neurali risiedono sull'host Python. |

---

## 3. Risorse Hardware Verificate (ESP32-S3-DevKitC-1 N16R8)

I collaudi strumentali registrati nella FASE 12.27 e FASE 13.7 certificano il seguente bilancio di memoria:

- **Flash (16 MB SPI)**:
  - Partizione `app0` attuale: `1.310.720` byte (`1.25 MB`).
  - Occupazione firmware FASE 13.6 (`microWakeWord` + Eyes 3.0 + Audio + Wi-Fi): **`1.299.328` byte**.
  - Margine residuo in `app0`: **`11.392` byte** (criticità: per espansioni future sarà opportuno adottare una tabella di partizionamento con partizioni applicative da 3 MB).
- **SRAM Interna (512 KB)**:
  - Heap libera a regime: **`129.252` byte** costanti su 10+ minuti di stress-test (zero memory leak riscontrati).
  - Minimum Heap: `121.296` byte.
  - Stack HWM Task Audio RX: `10.036` byte liberi su `12.288` allocati (`81.7%` margine).
- **Octal PSRAM (8 MB OPI)**:
  - Buffer Audio RX (8 s @ 16 kHz mono): `256.000` byte.
  - Buffer Audio TX (MAX98357A): `640.000` byte.
  - Buffer WSS TTS Net: `640.000` byte.
  - PSRAM libera residua: **`6.787.696` byte** (~6.5 MB liberi per buffer grafici, cache e future espansioni).

---

## 4. Conclusioni dell'Analisi di Stato

Il progetto dispone di una base tecnologica eccezionalmente solida e collaudata a banco. Il motore grafico Eyes 3.0 e la pipeline vocale duplex Voice Bridge rappresentano componenti di qualità industriale pronti per essere integrati nell'architettura unificata **JARVIS Robotics Platform**.
