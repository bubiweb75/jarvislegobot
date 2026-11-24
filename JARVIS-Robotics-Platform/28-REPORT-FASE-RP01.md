# 28 — Report Conclusivo della Fase RP-01

> **JARVIS Robotics Platform** — Report Consuntivo di Analisi, Fattibilità e Progettazione  
> **Fase:** RP-01  
> **Data:** 24 Novembre 2026  
> **Esito:** **COMPLETATA CON SUCCESSO — STOP OBBLIGATORIO ATTIVO**  

---

## 1. Premessa e Stato dei Vincoli Operativi

La **FASE RP-01** è stata condotta nel rigoroso rispetto dei vincoli operativi stabiliti:
- **Zero Modifiche al Firmware Esistente:** Nessun file sorgente del firmware principale, di Eyes 3.0, di EmotionEngine, di TouchManager, dei driver audio o delle simulazioni è stato alterato o cancellato.
- **Zero Operazioni Hardware Invasive:** Nessun flash della memoria dell'ESP32-S3, nessun accesso non autorizzato alla porta seriale fisica e nessuna modifica ai servizi attivi sul Raspberry Pi 5 o sul NAS Synology.
- **Isolamento dei Deliverable:** L'intera documentazione tecnica prodotta (28 documenti monografici + README) è stata creata esclusivamente all'interno della cartella dedicata `JARVIS-Robotics-Platform/`.
- **Nessuna Alterazione Git:** Il branch di sviluppo e lo stato della working tree principale non sono stati modificati o sporcati da operazioni di commit/push non autorizzate.

---

## 2. Consuntivo dei 34 Punti di Ispezione e Progettazione

### 1. Stato Effettivo del Progetto Principale
Il progetto si trova a uno stadio di maturità ingegneristica straordinariamente avanzato: l'hardware fisico di JARVIS (ESP32-S3 N16R8, display OLED SH1106, microfono I2S INMP441, amplificatore I2S MAX98357A, pulsante PTT GPIO47 e touch capacitivo TTP223B su GPIO1) è pienamente funzionante, assemblato sulla Carrier Board personalizzata e validato in FASE 13.7.

### 2. Revisione dei Sorgenti Analizzati
- **Commit Git su HEAD:** `53f1bce test(hardware): validate Eyes 3.0 on ESP32-S3 SH1106`.
- **Working Tree Non Committata:** Contiene il consolidamento fino a **FASE 13.7** (`04-Firmware/experiments/fase13_3-integrated/` e `05-Voice-AI/voice_bridge/`), aggiornato al 19 Novembre 2026.

### 3. Ultimo Firmware Stabile Identificato
- **Ramo Stabile di Partenza:** Firmware FASE 12.27 (`04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/`, hash verificato).
- **Ultima Build Sperimentale Collaudata a Banco:** FASE 13.6/13.7 (`fase13_3-integrated.ino.bin`, SHA-256 `44A548EDB0A8...`), collaudata su ESP32-S3 MAC `<ESP32_MAC_ADDRESS>` con 15 conversazioni continue riuscite e zero crash.

### 4. Funzionalità Già Riutilizzabili (100% Ready)
- Motore grafico **Eyes 3.0 (*Organic Visor Companion*)** a 30 FPS.
- Driver display `U8g2` per **SH1106** con correzione offset +2px.
- Framebuffer statico **MonochromeFramebuffer** da 1024 byte (zero allocazioni dinamiche).
- Gestore touch capacitivo **TouchManager** per sensore TTP223B su GPIO1.
- Driver pulsante **ButtonController** con debounce hardware/software su GPIO47.
- Pipeline audio **FreeRTOS Dual-Core I2S0 RX / I2S1 TX** a 16 kHz.
- Motore vocale host **Piper TTS** con voce italiana *Riccardo* e post-processing WSOLA Profile B.
- Rete neurale locale **microWakeWord** INT8 *"Hey Jarvis"* streaming.
- Scheda elettronica **Carrier Board PCB V1** (JLCPCB zip pronti).

### 5. Moduli che Richiedono Adattamenti
- `eye_engine.cpp`: Estrazione dei parametri geometrici in tabelle di configurazione (`SkinDefinition`) per consentire la variazione delle skin senza toccare l'interpolatore esponenziale e il Natural Gaze.
- `state_machine.cpp`: Generalizzazione dei messaggi di stato per ricezione da bus eventi locale e WebSocket.
- `voice_bridge/esp_protocol.py`: Estensione dell'handshake `auth` per supportare Device ID multipli e personalità multiple.
- `voice_bridge/config.py`: Supporto al caricamento dinamico di più voci Piper e system prompt LLM differenziati.

### 6. Riferimenti Hardcoded al Nome JARVIS
Identificata e risolta la distinzione tra:
- **Piattaforma:** `JARVIS Robotics Platform` e namespace C++ `jarvis::` (mantenuti fissi).
- **Dispositivo Fisico:** `Device ID` univoco (`rob-esp32s3-<MAC>`) immutabile.
- **Nome Visibile:** `user_label` (configurabile a piacere dall'utente a runtime).
- **Assistente AI:** Nome nel system prompt LLM (configurabile per identità).
- **Wake Word:** Parola acustica associata al modello INT8 (es. "Hey Jarvis", "Hey Eva").
- **Hostname di Rete:** `jarvis-<short_mac>.local` (univoco per prevenire collisioni mDNS).

### 7. Inventario Effettivo degli Stati Eyes 3.0
Stati operativi verificati: `IDLE`, `WIFI_CONNECTING`, `WIFI_CONNECTED`, `RECORDING` / `LISTENING`, `UPLOADING`, `PROCESSING`, `RECEIVING`, `PLAYING` / `SPEAKING`, `SLEEPING`, `ERROR`, `CANCELLED`.

### 8. Inventario Effettivo delle Espressioni
Identificate le **14 espressioni reali del codice C++** (enum `Expression`):  
`kNeutral`, `kHappy`, `kCurious`, `kSleepy`, `kListening`, `kThinking`, `kSpeaking`, `kSurprised`, `kShy`, `kLove`, `kWink`, `kConfused`, `kMischievous`, `kSleeping`.  
*(Discrepanza storica risolta: il codice adotta `SHY` e `WINK` al posto di `SAD` ed `EXCITED`).*

### 9. Inventario delle Micro-Espressioni
5 micro-espressioni contestuali spontanee non distruttive:  
`kBrowRaise` (sopracciglio alzato), `kSideGlance` (sguardo laterale), `kQuickWink` (occhiolino destro), `kEyeSmile` (micro-sorriso inferiore), `kPupilPulse` (dilatazione pupilla focalizzata).

### 10. Inventario delle Animazioni
- Natural Gaze Engine: micro-saccadi casuali (±1..3 px) e saccadi esplorative (-11..+11 X, -6..+6 Y) con bias di ritorno al centro e soppressione in ascolto.
- Advanced Blink Engine: 4 fasi (`Open` → `Closing` → `HoldClosed` → `Opening` con ease-out) e probabilità di double-blink spontaneo.
- Cinematic Transitions: interpolazione esponenziale indipendente dal frame rate con boost accelerato 1.85× su `SURPRISED`.

### 11. Profili Comportamentali
3 profili visivi formalizzati:  
- `CALM` (velocità 0.72×, sguardo 0.65×, ammiccamento 0.80×, double-blink 8%).
- `LIVELY` (velocità 1.00×, default "Amichetto Vivace", double-blink 20%).
- `PLAYFUL` (velocità 1.22×, sguardo 1.35×, micro-espressioni 1.65×, double-blink 28%).

### 12. Baseline Grafica Originale
Geometria superellittica: occhi base 38×38 px, `shape_power = 2.6`, `taper = 0.10`, raggio 11 px, spaziatura 16 px, pupille 7 px, sopracciglia offset 4 px arch 2.2. Rendering 128×64 monocromatico 1-bit.

### 13. Strategia di Preservazione della Skin JARVIS
Denominazione ufficiale: **`JARVIS Original Premium — Organic Visor Companion`**.  
Configurazione predefinita cablata come factory default permanente del firmware. Criterio di accettazione bit-exact per zero regressioni.

### 14. Fattibilità delle Cinque Skin Premium
Pienamente fattibili entro i vincoli dello Skin Engine monocromatico:  
1. *JARVIS* (Original Companion), 2. *EVA* (Elegant con ciglia morbide), 3. *NOVA* (Ocular HUD tecnologico), 4. *TARS* (Geometric Minimal cartesiano), 5. *NEKO* (Feline con pupille a taglio verticale). Tutte e 5 mappano integralmente le 14 espressioni.

### 15. Fattibilità del Firmware Comune
Fattibile e raccomandato: un unico binario JARVIS Core basato su FreeRTOS con parametri caricati a caldo da NVS/WebSocket per l'hardware da scrivania; profilo di compilazione dedicato (`-DJARVIS_HW_PROFILE_MOBILE_V2`) per il robot mobile.

### 16. Fattibilità del Cambio Nome
Pienamente fattibile a runtime senza riflash: il nome è una proprietà memorizzata in NVS e nel database SQLite di Identity Studio.

### 17. Fattibilità del Cambio Skin
Pienamente fattibile a caldo via WebSocket senza riavvio del chip: l'ESP32 aggiorna i target geometrici in memoria e passa morbidamente alla nuova forma oculare.

### 18. Fattibilità del Cambio Voce
Pienamente fattibile e integrato in V1: Piper TTS locale su host supporta lo switch istantaneo tra le voci italiane precaricate (`Riccardo`, `Paola`, `Corrado`) con anteprima audio web immediata.

### 19. Fattibilità del Cambio Wake Word
Fattibile a runtime per i modelli INT8 preinstallati (`hey_jarvis`, `hey_eva`, `hey_nova`) grazie al footprint ridotto (~35 KB cad.) di microWakeWord; upload di nuovi modelli su partizione `spiffs` previsto come evoluzione V2.

### 20. Fattibilità del Cambio Personalità
Pienamente fattibile a runtime: i prompt di sistema LLM e i parametri comportamentali risiedono sull'host e vengono iniettati dinamicamente per ciascun robot.

### 21. Fattibilità della Gestione Multi-Robot
Pienamente fattibile: architettura WebSocket multi-sessione, Device ID univoci derivati da MAC, hostname mDNS disaccoppiati e canali di streaming audio concorrenti isolati.

### 22. Limitazioni di Xiaozhi e Alternative Tecniche
Xiaozhi Cloud presenta forti dipendenze esterne, latenza elevata e supporto italiano scarso. L'architettura **Voice Bridge locale** (Faster-Whisper + Ollama + Piper TTS) garantisce sovranità, latenza < 2,5 s e operatività 100% offline.

### 23. Alternative Tecniche per Wake Word
Esaminato WakeNet (scartato per partizione da 3.8 MB incompatibile) e Porcupine (scartato per licenza cloud). Scelta definitiva: **microWakeWord INT8 Apache-2.0 locale su ESP32-S3**.

### 24. Compatibilità Carrier Board PCB V1
La Carrier Board già progettata e ordinata è il componente hardware centrale del Modulo A: pienamente compatibile con tutti i robot Desktop V1 e con la parte superiore del robot Mobile V2.

### 25. Compatibilità Futura con Base Mobile (Modulo B2)
Predisposizione definita: aggancio meccanico 8×8 stud con 4 pin Technic 6558, connettore ombelicale JST 6-pin, driver TB6612FNG, 2x N20 e 2 sensori cliff frontali anti-caduta con watchdog a 500 ms.

### 26. Risorse Hardware dell'ESP32-S3
- Flash `app0`: 1.299.328 B occupati su 1.310.720 B (margine 11 KB; consigliata espansione futura ad `app3M`).
- SRAM: 129.252 B liberi costanti (zero leak).
- PSRAM: ~6,78 MB liberi su 8 MB.

### 27. Architettura Raccomandata
Architettura a 5 livelli (A: JARVIS Core, B: Hardware Profile, C: Identity Profile, D: Device Configuration, E: Shared Services).

### 28. Rischi Principali e Mitigazioni
- *Rischio saturazione Flash:* Mitigato con modelli quantizzati compatti e futuro ripartizionamento a 3 MB.
- *Rischio caduta base mobile:* Mitigato con sensori cliff ad interrupt hardware e arresto in 15 ms.
- *Rischio regressioni JARVIS:* Mitigato con baseline intatta e backup 16 MB pronto per rollback.

### 29. Decisioni Assunte in Autonomia
- Adozione della denominazione ufficiale delle 14 espressioni da codice reale (`SHY` e `WINK` confermate).
- Scelta di Piper TTS come motore primario V1 a scapito di servizi cloud a pagamento.
- Progettazione dello Skin Designer con doppio livello (Semplice per tutti, Avanzato per designer).

### 30. Questioni Aperte per l'Utente
1. Valutare l'autorizzazione al passaggio da tabella partizioni standard (app0 da 1.25 MB) a tabella partizioni estesa (*Huge App* da 3 MB su Flash 16 MB) nella futura fase RP-11 per garantire ampio spazio a molteplici modelli wake word INT8.
2. Definire l'ordine di priorità tra lo sviluppo dello Skin Designer Web (RP-04/09) e l'assemblaggio del secondo prototipo hardware per il collaudo multi-robot reale (RP-13).

### 31. Documenti Creati nella Cartella `JARVIS-Robotics-Platform/`
Creata la suite completa di 29 file markdown:
- `README.md`
- `01-VISIONE-PROGETTO.md` fino a `28-REPORT-FASE-RP01.md`.

### 32. Proposta per la Fase RP-02
Avviare la **FASE RP-02 — Specifiche Formali, Contratti e Schemi JSON**, finalizzata alla stesura formale degli schemi JSON Schema, dei contratti OpenAPI v3 e delle strutture dati per l'interscambio dei pacchetti.

### 33. Conferma delle Operazioni NON Eseguite
Si attesta formalmente che durante la Fase RP-01:
- Nessun firmware è stato modificato, compilato o flashato.
- Nessuna porta seriale o pinout è stato alterato.
- Nessuna modifica è stata apportata a gerber, schemi KiCad o file Wokwi.
- Nessun pacchetto software o dipendenza globale è stato installato sul PC o sul Raspberry Pi.
- Nessun deployment Docker o modifica ai servizi di produzione è stato avviato.

### 34. Conferma di Integrità del Progetto Principale
Il workspace principale di JARVIS LEGO BOT è rimasto **perfettamente intatto, integro e immutato**. L'intero lavoro della Fase RP-01 risiede isolato all'interno della cartella `JARVIS-Robotics-Platform/`.

---

## 3. Dichiarazione di STOP

In osservanza del punto 34 delle specifiche di missione:
> **LE ATTIVITÀ DELLA FASE RP-01 SONO UFFICIALMENTE CONCLUSE.**  
> **IL SISTEMA SI ARRESTA RIGOROSAMENTE IN ATTESA DELL'APPROVAZIONE FORMALE DELL'UTENTE PRIMA DI PROCEDERE A QUALSIASI ATTIVITÀ SUCCESSIVA.**
