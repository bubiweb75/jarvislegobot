# 03 — Analisi di Riutilizzo e Disaccoppiamento Tecnologico

> **JARVIS Robotics Platform** — Studio di Riutilizzo dei Moduli e Decoupling  
> **Fase:** RP-01  
> **Stato:** Approvato per Progettazione  

---

## 1. Obiettivo dell'Analisi

Lo scopo della JARVIS Robotics Platform non è riscrivere i componenti software ed elettronici sviluppati finora, ma valorizzare al 100% l'investimento ingegneristico realizzato, identificando con precisione:
1. I componenti riutilizzabili **immediatamente così come sono** (100% ready).
2. I componenti riutilizzabili **previo adattamento e disaccoppiamento** (parametrizzazione, rimozione di costanti hardcoded, estrazione interfacce).
3. I componenti da **progettare ex-novo** per supportare l'ecosistema multi-robot.

Inoltre, viene condotta un'analisi sistematica di tutti i riferimenti cablati al nome "JARVIS" per distinguere i contesti tecnici dai contesti d'identità.

---

## 2. Inventario di Riutilizzo per Modulo

### 2.1 Moduli Riutilizzabili Direttamente (Così come sono)

| Modulo / File Sorgente | Ruolo nel Progetto Originale | Riutilizzo nella Piattaforma |
|---|---|---|
| `display_driver.cpp / .h` | Inizializzazione U8g2 e refresh I2C per SH1106/SSD1306 | **Driver Ufficiale Display Oled**: invariato. Gestisce già il fast-mode 400 kHz e l'offset di 2 pixel per SH1106. |
| `monochrome_fb.cpp / .h` | Framebuffer XBM statico monocromatico 128×64 | **Core Graphics Buffer**: invariato. Zero allocazioni dinamiche (1024 byte), operazioni di rasterizzazione primitive e rendering istantaneo. |
| `touch_manager.cpp / .h` | Gestione debounce e gesture TTP223B su GPIO1 | **Touch Engine**: invariato. Configurazione dei tempi di tap/long-press già parametrizzabile via struct `TouchConfig`. |
| `audio_buffer.cpp / .h` | Buffer circolare in PSRAM per campioni PCM16 | **Audio Buffer Layer**: riutilizzabile tal quale per la gestione dell'audio streaming bidirezionale a 16 kHz. |
| `button_controller.cpp / .h` | Debounce e gestione PTT su GPIO47 | **Physical Button Driver**: invariato. Garantisce l'interazione manuale e la cancellazione immediata della riproduzione. |
| `Carrier Board PCB V1` | Scheda madre progettata e ordinata per ESP32-S3 + audio + display + touch | **Base Elettronica Standard Desktop V1**: compatibilità progettuale verificata al 100%; l'assemblaggio e il collaudo funzionale su scheda fisica avverranno al momento della consegna da JLCPCB. |

### 2.2 Moduli Riutilizzabili con Adattamenti

| Modulo / File Sorgente | Stato Attuale | Adattamento Necessario per la Piattaforma |
|---|---|---|
| `eye_engine.cpp / .h` | Contiene i target geometrici e l'animazione di Eyes 3.0 cablati nel codice | **Evoluzione in Eyes Engine + Skin Engine**: estrarre i parametri di forma, raggio, curvature e palpebre in profili di skin (es. struct `SkinDefinition`), lasciando il motore di interpolazione esponenziale, gaze e blink comune a tutte le identità. |
| `state_machine.cpp / .h` | Gestisce gli stati del companion con costanti seriali fisse | **Evoluzione in Core State Machine**: disaccoppiare la macchina a stati dai comandi seriali diretti, abilitando la ricezione di eventi da bus interno, WebSocket e driver fisici. |
| `esp_protocol.py` (Backend) | Gestisce la connessione WebSocket con token fisso e sessione singola | **Evoluzione in Multi-Device Protocol Handler**: estendere l'handshake `auth` per supportare Device ID multipli, selezione della personalità e routing dei flussi audio verso contesti separati. |
| `voice_bridge/config.py` | Configurazione statica per singola voce Piper (`riccardo`) e singolo prompt | **Evoluzione in Voice & Identity Config Engine**: consentire il caricamento dinamico di modelli vocali differenti per dispositivo e profili di sistema LLM dedicati. |
| `network_task.cpp` (Firmware) | Connessione Wi-Fi con credenziali da header `wifi_secrets.h` | **Evoluzione in Network Manager Provisionabile**: supportare provisioning Wi-Fi via Bluetooth/AP o NVS anziché credenziali hardcoded a tempo di compilazione. |
| `microWakeWord` (Firmware) | Riconosce unicamente il modello INT8 "Hey Jarvis" compilato nel sorgente | **Evoluzione in Wake Word Engine Modulare**: consentire la selezione tra modelli compilati (o partizione dedicata) per identità differenti. |

### 2.3 Moduli da Sviluppare Ex-Novo

1. **JARVIS Identity Studio (Web App):** Interfaccia grafica completa (React/Vite/FastAPI) per il design delle skin, anteprima vocale, gestione profili e configurazione dei robot fisici.
2. **Device Manager & Fleet Registry:** Servizio di registrazione, pairing sicuro, stato online/offline e sincronizzazione dei robot sulla rete locale.
3. **Skin Parser & Serializer:** Modulo di caricamento, validazione e serializzazione dei pacchetti `.jarvis-skin` in JSON/binario.
4. **Independent OLED Web Simulator:** Simulatore web ad alta precisione (128×64 pixel-perfect) integrato nello Studio per testare skin, animazioni e stati anche a robot spento.
5. **Mobile Motor Controller (Driver B2):** Driver FreeRTOS per il controllo dei motoriduttori N20 e del chip TB6612FNG con watchdog di sicurezza e arresto su timeout.

---

## 3. Disaccoppiamento dei Riferimenti al Nome "JARVIS"

Nel codice attuale il nome "JARVIS" compare in molteplici contesti concettualmente distinti. Per rendere la piattaforma multi-identità è essenziale formalizzare la separazione di questi livelli:

| Livello Concettuale | Significato e Ruolo | Riferimento Attuale nel Codice | Regola di Disaccoppiamento nella Piattaforma |
|---|---|---|---|
| **Piattaforma Tecnologica** | Nome dell'architettura e del framework | Cartelle `JARVIS LEGO BOT`, prefissi namespace `jarvis::` | **Mantenuto fisso:** `JARVIS Robotics Platform` e `jarvis::core` restano gli identificativi ingegneristici condivisi. |
| **Identificativo Dispositivo** | ID hardware univoco di un singolo robot fisico | Assente (singolo prototipo implicito) | **Generato dinamicamente:** Ogni robot riceve un `Device ID` univoco (es. `rob-esp32s3-288485870588`), immutabile e indipendente dal nome assegnato. |
| **Nome Visibile del Robot** | Nome scelto dall'utente per il dispositivo | Hardcoded "JARVIS" nei log e nella UI | **Configurabile a runtime:** Salvato in NVS e configurabile da Identity Studio (es. "Jarvis Desk", "Eva Studio", "Neko Mobile"). |
| **Identità Assistente AI** | Nome con cui l'LLM si presenta e riconosce se stesso | Prompt di sistema fisso "Tu sei JARVIS..." | **Configurabile nel Personality Profile:** Ogni identità possiede il proprio system prompt dedicato (es. "Tu sei Eva...", "Tu sei Tars..."). |
| **Wake Word Acustica** | Parola che risveglia il microfono | Rete neurale INT8 `hey_jarvis` | **Assegnabile per Identità:** La wake word acustica (es. "Hey Jarvis", "Hey Eva") è una proprietà del profilo d'identità, associata a un modello acustico compatibile. |
| **Hostname di Rete & mDNS** | Nome host per la risoluzione IP locale | `jarvis-esp32.local` | **Derivato univocamente:** Formato standardizzato `jarvis-<device-id-short>.local` per evitare collisioni quando più robot sono accesi contemporaneamente. |
| **Token Autenticazione** | Segreto di connessione WSS | `JARVIS_ESP_DEVICE_TOKEN` | **Token Individuale per Dispositivo:** Generato e registrato durante la procedura di pairing con il Device Manager. |

---

## 4. Preservazione dell'Identità Originale JARVIS

Come principio architetturale non negoziabile:
- La configurazione predefinita di fabbrica del firmware (**Default Out-of-the-Box**) sarà esattamente l'identità **JARVIS Original Premium — Organic Visor Companion**, con la voce italiana Piper Riccardo, il prompt di sistema professionale e la wake word "Hey Jarvis".
- La trasformazione in piattaforma multi-identità si realizza aggiungendo livelli di configurazione astratti sopra le fondamenta di JARVIS, garantendo che nessuna riga del comportamento originale venga compromessa.
