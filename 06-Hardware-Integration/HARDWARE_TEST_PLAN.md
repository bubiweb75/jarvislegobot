# HARDWARE_TEST_PLAN — Piano di Collaudo Progressivo (FASE 6)

> **Stato attuale:** Tutti i test riportati di seguito sono **DA ESEGUIRE** dopo l'arrivo dei componenti fisici. Nessun test hardware è stato ancora eseguito o dichiarato superato.

---

## Test 1 — ESP32-S3 e Display OLED 1,3"

- **Prerequisiti:**
  - ESP32-S3-DevKitC-1 N16R8 e OLED 1,3" I²C collegati su breadboard **a USB scollegata**, seguendo [WIRING_GUIDE.md](06-Hardware-Integration/WIRING_GUIDE.md) (`VCC->3V3`, `GND->GND`, `SDA->GPIO41`, `SCL->GPIO42`).
  - Controllo visivo serigrafie `VCC/GND` e verifica col multimetro assenza cortocircuiti tra `3V3` e `GND`.
- **Istruzioni:**
  1. Collegare il cavo USB-C alla porta **`USB`** nativa della DevKitC-1 e al PC Windows 11.
  2. Verificare in *Gestione Dispositivi* di Windows la comparsa della porta COM USB-CDC.
  3. Compilare e caricare il firmware già presente in `04-Firmware/jarvis-desk-buddy` usando inizialmente l'ambiente `esp32s3_sh1106` (`pio run -e esp32s3_sh1106 -t upload`).
  4. Aprire il Serial Monitor a `115200` baud e leggere il log di avvio (`I2C OLED detected at 0x3C`).
  5. Testare tutte e **14 le espressioni OLED** (estensione delle 7 espressioni storiche della FASE 6):
     - *7 espressioni base (FASE 4/6):* `STATE:IDLE` (`NEUTRAL`), `STATE:HAPPY`, `STATE:CURIOUS`, `STATE:LISTENING`, `STATE:THINKING`, `STATE:SPEAKING`, `STATE:SLEEPY`
     - *7 espressioni emotive (FASE 7/8.2A):* `STATE:SURPRISED`, `STATE:SHY`, `STATE:LOVE`, `STATE:WINK`, `STATE:CONFUSED`, `STATE:MISCHIEVOUS`, `STATE:SLEEPING`
     - Verificare inoltre i comandi `PING`, `STATUS`, `DIAG`, `LOOK:5,-3` e il pulsante su `GPIO 47`.
  6. Se lo schermo presenta uno spostamento orizzontale di 2 pixel o una barra di rumore sul bordo, compilare e caricare `esp32s3_ssd1306`.
- **Risultati attesi:** Rilevamento I²C a `0x3C` (o `0x3D`), occhi nitidi e centrati a 50 FPS, tutte e 14 le espressioni distinguibili.
- **Criteri di superamento:** Porta COM stabile, `I2C OLED detected`, zero artefatti grafici su tutte le 14 espressioni.
- **Diagnosi errori:**
  - *Porta COM assente:* verificare cavo USB-C (deve essere dati, non solo ricarica) o provare modalità bootloader (`BOOT` + `RST`).
  - *`WARN: No OLED ACK`:* verificare inversione `SDA`/`SCL` (`41`/`42`), polarità `VCC`/`GND` e tensione `3.3 V` ai pin OLED.
  - *Schermo spostato di 2 px / rumore a destra:* passare da `esp32s3_sh1106` a `esp32s3_ssd1306`.

---

## Test 2 — Collegamento JARVIS Windows ↔ ESP32-S3 (Solo Occhi)

- **Prerequisiti:** Test 1 superato; `Ollama` attivo in locale su `127.0.0.1:11434`.
- **Istruzioni:**
  1. Chiudere eventuali Serial Monitor aperti (la porta COM può essere usata da un solo programma).
  2. Avviare `05-Voice-AI/jarvis_app.py` e collegare il trasporto seriale (`SerialEyeTransport`) alla porta COM dell'ESP32-S3.
  3. Inviare un messaggio testuale o usare il microfono PC e osservare la sequenza sugli occhi OLED reali (`LISTENING` → `THINKING` → `SPEAKING` → `IDLE`).
  4. Scollegare fisicamente il cavo USB durante lo stato `IDLE` e ricollegarlo dopo 5 secondi.
- **Risultati attesi:** Sincronia tra gli stati di `VoiceController` e l'OLED fisico; dopo il ricollegamento USB, il sistema riprende senza crash dell'app Windows.
- **Criteri di superamento:** Transizioni OLED corrispondenti al 100% agli stati UI e recupero pulito dopo disconnessione/riconnessione USB.
- **Diagnosi errori:**
  - *Accesso negato alla COM:* un altro terminale/PlatformIO Monitor sta occupando la porta.
  - *Mancato aggiornamento occhi:* verificare `115200` baud, terminatore `\n` e assenza di `AUTO:ON` che sovrascrive gli stati.

---

## Test 3 — Amplificatore MAX98357A e Speaker 4 Ω / 3 W

- **Prerequisiti:** Test 1 superato; MAX98357A e speaker collegati a USB scollegata (`VIN->5V`, `GND->GND`, `SD->3V3`, `DIN->GPIO7`, `BCLK->GPIO15`, `LRC->GPIO16`, Speaker su `OUT+`/`OUT-`).
- **Istruzioni:**
  1. Verificare con multimetro che né `OUT+` né `OUT-` abbiano continuità verso `GND`.
  2. Alimentare via USB e caricare uno sketch di test I²S1 TX che generi una sinusoide o un breve tono a **volume prudente (15–25%)**.
  3. Riprodurre poi una frase breve generata da `Piper Riccardo (Amichetto Vivace)` via USB.
  4. Aumentare gradualmente fino al volume operativo verificando temperatura del MAX98357A e stabilità della tensione `5V`/`3V3`.
- **Risultati attesi:** Suono chiaro, assenza di ronzii costanti, assenza di clipping o reset dell'ESP32-S3 per calo di tensione.
- **Criteri di superamento:** Riproduzione pulita senza distorsioni né riavvii MCU; chip MAX98357A tiepido.
- **Diagnosi errori:**
  - *Nessun audio:* verificare pin `SD` (deve abilitare il chip secondo datasheet del breakout ricevuto) e ordine `BCLK`/`LRC`/`DIN`.
  - *Reset ESP32-S3 all'avvio suono:* `VIN` collegato per errore a `3V3` invece che a `5V`, oppure cavo USB troppo sottile/lungo.
  - *Distorsione forte:* ridurre ampiezza digitale PCM o controllare pin `GAIN`.

---

## Test 4 — Microfono Digitale INMP441

- **Prerequisiti:** Test 1 superato; INMP441 collegato a USB scollegata (`VDD->3V3`, `GND->GND`, `L/R->GND`, `WS->GPIO4`, `SCK->GPIO5`, `SD->GPIO6`).
- **Istruzioni:**
  1. Verificare visivamente che `VDD` sia su `3V3` (mai `5V`) e `L/R` su `GND`.
  2. Caricare uno sketch di test I²S0 RX a `16 kHz`, `mono`, e trasmettere i campioni al PC registrando un file `.wav` di 5 secondi parlando a ~30–50 cm.
  3. Analizzare su PC forma d'onda, livello RMS, assenza di saturazione/clipping e rumore di fondo (silenzio in stanza).
- **Risultati attesi:** Voce chiara e comprensibile al riascolto, livello picco tra `-12 dBFS` e `-3 dBFS`, rumore di fondo contenuto.
- **Criteri di superamento:** Registrazione `.wav` a 16 kHz priva di glitch/scatti I²S e trascrivibile correttamente da `faster-whisper`.
- **Diagnosi errori:**
  - *Solo zeri / silenzio:* `L/R` lasciato flottante o invertito (`VDD` per canale Right se configurato Left), oppure `WS`/`SCK` scambiati.
  - *Rumore bianco/fruscio fortissimo:* allineamento bit I²S errato (24-bit in frame 32-bit MSB-first per INMP441) o cattivo contatto breadboard su `SCK`.

---

## Test 5 — Conversazione Completa End-to-End (Robot ↔ PC Windows)

- **Prerequisiti:** Test 1, 2, 3 e 4 superati; `Ollama (qwen2.5:3b)`, `faster-whisper` e `Piper Riccardo (Amichetto Vivace)` operativi su PC Windows 11.
- **Istruzioni:**
  1. Collegare l'ESP32-S3 (con OLED, INMP441, MAX98357A, Speaker e Pulsante `GPIO 47`) al PC via porta `USB`.
  2. Avviare `JARVIS AI Desk Buddy` in modalità bridge hardware USB.
  3. Premere il pulsante su `GPIO 47`: verificare passaggio occhi a `LISTENING` e avvio cattura `INMP441`.
  4. Pronunciare una domanda in italiano (es. *"Ciao JARVIS, come stai oggi?"*) e rilasciare/terminare l'ascolto.
  5. Osservare: `THINKING` (trascrizione `faster-whisper` + risposta `Ollama`) → `SPEAKING` (sintesi `Piper Riccardo` riprodotta dallo speaker del robot) → ritorno a `IDLE`.
  6. Ripetere interrompendo la risposta a metà tramite pulsante **Stop** / pulsante fisico.
- **Risultati attesi:** Ciclo completo reattivo, voce comprensibile dallo speaker del robot, occhi sincronizzati in ogni fase e Stop immediato.
- **Criteri di superamento:** Almeno 3 turni consecutivi in italiano completati senza errori USB, crash o desincronizzazione degli occhi, più 1 test di interruzione immediata superato.
- **Diagnosi errori:**
  - *Eco / auto-ascolto:* assicurarsi che il microfono `INMP441` non registri durante `SPEAKING` (il PC/ESP32 disabilita la cattura mic finché lo speaker sta suonando).
  - *Scatti audio nello speaker:* aumentare pre-buffer I²S1 TX da `60 ms` a `100 ms` e verificare flusso `SPK_FLOW`.
