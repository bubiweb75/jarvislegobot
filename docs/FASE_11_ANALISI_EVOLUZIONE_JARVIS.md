# FASE 11 — Analisi Tecnica, Architetturale e Funzionale dell'Evoluzione di JARVIS LEGO BOT

> **Stato documento:** Analisi preliminare (FASE 11 — Parte A/B/C). **Nessuna implementazione**, nessuna modifica al firmware esistente, nessun flash e nessun commit/push eseguiti.

---

## 1. Stato Attuale Verificato nel Repository

Ispezione diretta della working tree locale (``, ultimo commit su `HEAD`: `7c33314` — FASE 9.5):

| Fase | Stato verificato su file locali | Note Git / Hardware |
|---|---|---|
| **FASE 9.5** (`05-Voice-AI`) | ✅ Presente e collaudata (`7c33314`): `faster-whisper`, `Ollama qwen2.5:3b`, `Piper Riccardo`, `MemoryEngine` L2/L3/L4, `ConversationEngine`, `VoiceController`, `EyeBridge` (`set_state`, `on_audio_level`), Control Center. | Committata su `origin/main` (`7c33314`). |
| **FASE 10.1** (`04-Firmware/esp32s3-diag-test`) | ✅ Firmware diagnostico ESP32-S3-N16R8 presente (collaudo seriale fisico eseguito su `COM4`). | Non ancora committata (untracked). |
| **FASE 10.2 / 10.3** (`04-Firmware/jarvis-desk-buddy` e `-sim`) | ✅ Motore **Eyes 3.0** (*Organic Visor Companion*, 14 espressioni), `StateMachine` (`GPIO47`, comandi seriali), `DisplayDriver` (`SH1106` default / `SSD1306`), `SensorBridgeStub` (`sensor_stub.h`), `SensorManager` simulatore (`sensor_manager.py`). | Modifiche locali non committate. OLED reale e audio I2S non ancora collegati fisicamente. |
| **FASE 10.2-SIM** (`04-Firmware/wokwi-simulation`) | ✅ Progetto PlatformIO per VS Code (`esp32s3_wokwi`, `board-ssd1306`, `GPIO47`). | Non committata; compilazione verificata, esecuzione VS Code non avviata. |
| **FASE 10.2-WEB** (`04-Firmware/wokwi-web`) | ✅ Immagine `jarvis-esp32s3-wokwi-merged.bin` + `web-project/` + `diagram.json` collaudati online dall'utente su `wokwi.com`. | Non committata; collaudo web confermato dall'utente. |

---

## 2. Analisi dei Quattro Progetti Funzionali

### 2.1 Sensore Tattile — Touch Interaction
- **Obiettivo**: rilevare tocchi sulla testa/scocca LEGO (`TOUCH_SINGLE`, `TOUCH_DOUBLE`, `TOUCH_LONG`, `TOUCH_RELEASE`) e tradurli in reazioni contestuali (felicità, giocosità, coccole/riposo, risveglio dal sonno, reazione in conversazione).
- **Valutazione Hardware (TTP223B vs alternative)**:
  1. **TTP223 / TTP223B**: sensore capacitivo a canale singolo (`2.0–5.5 V` → pienamente compatibile con `3.3 V`), uscita digitale push-pull attiva `HIGH` (default con ponticelli `A=0, B=0`). **Non è elettricamente equivalente a un pulsante**: un pulsante è passivo verso `GND` (`INPUT_PULLUP`), mentre il TTP223 pilota attivamente `HIGH`/`LOW` (`INPUT` semplice, **senza** `INPUT_PULLUP` per non alterare il fronte o sovraccaricare l'uscita).
  2. **Alternative**:
     - *Touch capacitivo nativo ESP32-S3* (`T1..T14` su `GPIO1..14`): possibile con elettrodo in rame/alluminio, ma più sensibile a rumore I2S, alimentazione USB e umidità se non tarato con filtro software.
     - *TTP223B con pad esterno*: il TTP223 integrato ha pad da ~11×11 mm; attraverso plastica ABS LEGO (spessore tile `1.6 mm` o plate `3.2 mm`) funziona, ma oltre ~3–4 mm o con intercapedine d'aria perde sensibilità. È possibile saldare una piccola lamina di rame adesiva dietro il brick/tile superiore (distanza `< 2 mm`), ricordando che il TTP223 si autocalibra nei primi ~0.5 s dall'accensione (non toccare la testa al boot!).
  3. **Falsi tocchi e interferenze**: possibili vicino a cavi I2S (`MAX98357A`, `GPIO7/15/16`), Wi-Fi attivo o alimentatore USB rumoroso. Mitigazioni: cavi corti, alimentazione `3V3` pulita (condensatore `100 nF` vicino al TTP223), debounce `30–40 ms`, rifiuto impulsi `< 40 ms`, schermatura rispetto ai cavi speaker.
  4. **GPIO**: in `pinout_config.h` `GPIO8` è già annotato come `kTouchTtp223`, ma attenzione al conflitto documentale con `02_Progetto_Modulare_e_Mobilita.md` (vedi Sezione 5).
  5. **Simulazione Wokwi**: `wokwi-pushbutton` o custom chip `ttp223` (con logica inversa rispetto al pulsante su `GPIO47`: `HIGH` = tocco).

### 2.2 Espressioni Avanzate — Eyes 4.0
- **Obiettivo**: evolvere `EyeEngine` (Eyes 3.0) senza perdere l'identità *Organic Visor Companion*, aumentando naturalezza, dinamica espressiva e introducendo una piccola **bocca animata opzionale** sincronizzata al parlato.
- **Fattibilità su `128×64` monocromatico**:
  - Gli occhi Eyes 3.0 attuali sono `38×38 px` centrati a `y = 34` (occupano circa `y = 15..53`). Per inserire una **piccola bocca opzionale** (`16–24 px` di larghezza, `4–8 px` di altezza a `y = 56..61`) senza sacrificare la leggibilità, durante `SPEAKING` (quando l'opzione bocca è attiva) conviene alzare leggermente `base_y` di `3–4 px` e ridurre l'altezza target di `2–3 px` (es. `34×34`), lasciando aria pulita tra occhi e bocca.
  - **Nuove animazioni incrementali su `EyeEngine`**:
    - Blink asimmetrico leggero (ritardo `25–45 ms` tra occhio sx e dx in profili `LIVELY`/`PLAYFUL`).
    - Sguardo morbido con easing non lineare e micro-movimenti di respirazione verticale (`±0.5 px`).
    - Bocca opzionale a 3–4 forme procedurali (chiusa/sorriso, semi-aperta, aperta O/A) pilotata dal livello audio (`0..100`).
    - Sopracciglia più dinamiche con curvatura variabile continua.
  - **Budget CPU/RAM ESP32-S3**: `MonochromeFramebuffer` resta `1024 byte` statici, zero allocazioni dinamiche; costo CPU stimato `< 1.5 ms`/frame su ESP32-S3 @ 240 MHz (ben dentro il budget di `33 ms` @ 30 FPS).

### 2.3 Reazioni Vocali — Voice Reactive Expressions
- **Stato esistente riutilizzabile al 90%**:
  - `05-Voice-AI/tts_providers.py` e `conversation_engine.py` espongono già la callback `on_audio_level(level: float)`.
  - `05-Voice-AI/eye_bridge.py` possiede già `EyeBridge` (`set_state`, `blink`, `look`, `set_auto_demo`, `on_audio_level`) e `SerialEyeTransport`.
  - `05-Voice-AI/voice_controller.py` invia già `LISTENING`, `THINKING`, `SPEAKING`, `HAPPY`, `IDLE`.
- **Confronto approcci di sincronizzazione parlato**:
  - **A. Eventi TTS** (`START`/`STOP`): latenza minima, zero CPU extra, ma bocca/occhi statici durante frasi lunghe.
  - **B. Analisi del volume audio (RMS/inviluppo)** *(Consigliato)*: `tts_providers.py` fornisce già il livello `0.0..1.0`. Con un throttling lato PC a `15–20 Hz` (`AUDIO:<0..100>` su seriale) e smoothing esponenziale lato ESP32-S3, la bocca e la vivacità degli occhi si muovono in tempo reale col parlato con carico CPU trascurabile e zero dipendenza da modelli esterni.
  - **C. Fonemi / Visemi**: **scartato** — `Piper` restituisce WAV/PCM senza timestamp fonemici pronti nella pipeline attuale; richiederebbe allineamento forzato costoso e fragile senza reale beneficio su OLED `128×64`.
- **Mappatura stati**: `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `HAPPY`, `SURPRISED`, `CONFUSED` (anche per errore), `SLEEPING` — **tutti già presenti** nelle 14 espressioni di `EyeEngine` e in `StateMachine`. L'unica estensione necessaria è aggiungere `AUDIO:<0..100>` (e opzionalmente `VOICE_EVENT:...` con ritorno automatico allo stato precedente).

### 2.4 Base Mobile — JARVIS Mobile 2WD (Modulo B2)
- **Verifica documentazione meccanica esistente**: `03-Mechanical-Design/02_Progetto_Modulare_e_Mobilita.md` definisce già con precisione il progetto modulare:
  - **Modulo A** (`10×10 stud` = `8×8×14,4 cm`, elettronica principale riutilizzabile).
  - **Modulo B2** (`16×15 stud` = `12,8×12,0×4,5 cm`), aggancio rapido `8×8 stud` con **4× Technic Pin `6558` (3L)** e connettore **JST-XH 6 pin** attraverso `Umbilical Port` `2×4 stud`.
  - **2 ruote motrici laterali** (`Ø 43–50 mm`) con **2× motoriduttori N20** (`24×12×10 mm`) + **1 ruota libera caster** (`Ø 15–20 mm`).
- **Analisi elettrica obbligatoria (Stima conservativa)**:
  - **Motoriduttori N20 6V (es. 100–200 RPM)**: corrente a vuoto ~`40–70 mA` cad., a carico nominale ~`150–250 mA` cad., **corrente di stallo ~`0.8–1.2 A` ciascuno** (picco combinato `~1.6–2.4 A`).
  - **Driver `TB6612FNG`**: supporta fino a `1.2 A` continui / `3.2 A` di picco per canale (`VM` `2.5–13.5 V`, logica `VCC` `2.7–5.5 V` → compatibile `3.3 V` ESP32-S3). Idoneo per motoriduttori N20; **non** idoneo per motori ad alto assorbimento oltre `1.2 A` continui.
  - **Alimentazione separata**:
    - Rail motori (`VM`): pacco batteria **Li-Ion/LiPo 2S (`7.4 V` nominali, `6.0–8.4 V`)** con **BMS integrato** + interruttore generale + fusibile.
    - Rail elettronica (`+5V_B2`): regolatore **Buck DC-DC 5V (≥ 2–3 A)** dalla 2S verso `5V` Modulo A (ESP32-S3 + `MAX98357A`, picchi speaker fino a `~0.8 A`), protetto da fusibile PTC `2 A` e protezione anti-inversione.
    - **Masse comuni (`GND`)** tra batteria, `TB6612FNG`, Buck `5V` e Modulo A, con condensatori di disaccoppiamento (`470 µF` + `100 nF`) su `VM` per filtrare i disturbi delle spazzole dei motori.
  - **Autonomia indicativa**: con pacco `2S 1500–2000 mAh` (~`11–14 Wh`) e assorbimento medio `0.4–0.7 A` in movimento + AI/audio, autonomia stimata `~1.5–2.5 ore` di uso misto (da verificare su prototipo reale).
- **Sicurezza mobilità**:
  - Watchdog/timeout comandi (`500 ms` senza heartbeat → `STOP` automatico), limite velocità PWM (`max_duty` configurabile), `STBY` LOW hardware al boot/reset, comando `STOP` prioritario, modalità test *wheels-up* (ruote sollevate).
  - **Rischio caduta da scrivania**: un solo sensore frontale (`VL53L0X` / `HC-SR04`) **non rileva i bordi/vuoti**. Servono almeno **2 sensori IR cliff rivolti verso il basso** sul bordo anteriore di B2 **oppure** vincolo operativo tassativo: uso di B2 **solo a pavimento**, mai su tavoli/scrivanie senza barriere.

---

## 3. Valutazione dei Progetti Wokwi di Riferimento

> Nota di trasparenza: l'ispezione web senza browser interattivo non espone il codice sorgente completo né il campo licenza esplicito di tutti gli sketch Wokwi; si riportano esclusivamente gli elementi effettivamente osservati e verificati.

| URL Wokwi | Titolo / Elementi osservati | Licenza verificabile | Parti concettuali utili / Decisione |
|---|---|---|---|
| `https://wokwi.com/projects/479955562917618689` | *Touch Reactive Robot Eyes – ESP32-C3 & OLED* (occhi reattivi al tocco su OLED). | Non esposta pubblicamente nei metadati indicizzati. | Solo riferimento concettuale (mappatura tocco → espressione). **Nessuna copia di codice**. |
| `https://wokwi.com/projects/453480668955342849` | Progetto pubblico Wokwi su display/animazione embedded. | Non esposta nei metadati indicizzati. | Richiede apertura manuale in Chrome per visione diretta; nessuna copia di codice. |
| `https://wokwi.com/projects/426385808890236929` | Progetto stile *Dasai Mochi* su ESP32-S3 + SSD1306. | Non verificabile / tipicamente assente nei cloni Mochi. | **Vietato copiare codice/asset** (coerente con `GITHUB_REPOS_ANALYSIS.md`). JARVIS mantiene il design originale *Organic Visor Companion*. |
| `https://wokwi.com/projects/480225012712409089` | `robo_face_wokwi` (faccia robotica su SSD1306 128×64 con stati happy, sad, angry, sleepy). | Non esposta nei metadati indicizzati. | Solo riferimento concettuale per contrasto/leggibilità su 128×64. |
| `https://wokwi.com/projects/479190168637387777` | Progetto pubblico Wokwi per logica di controllo/robotica. | Non esposta nei metadati indicizzati. | Richiede apertura manuale in Chrome per ispezione codice; nessuna copia di codice. |

---

## 4. Compatibilità Hardware e Disponibilità GPIO

### Pinout Attuale (Invariato)
- **I²C0 OLED**: `GPIO41` (SDA), `GPIO42` (SCL)
- **I²S0 Mic INMP441**: `GPIO4` (WS), `GPIO5` (SCK), `GPIO6` (SD)
- **I²S1 Amp MAX98357A**: `GPIO7` (DIN), `GPIO15` (BCLK), `GPIO16` (LRC)
- **Pulsante NO**: `GPIO47`

### Pin Riservati / Vietati (N16R8)
`GPIO0`, `GPIO3`, `GPIO19/20` (USB), `GPIO26–32` (Flash), `GPIO35–37` (Octal PSRAM), `GPIO38/48` (NeoPixel), `GPIO43/44` (UART0), `GPIO45/46` (Strapping).

### GPIO Disponibili e Conflitto Documentale Rilevato
⚠️ **Conflitto da risolvere prima dell'implementazione**:
- In `04-Firmware/jarvis-desk-buddy/include/pinout_config.h`, `GPIO8` è annotato come `kTouchTtp223` e `GPIO9` come `kTofXshut`.
- In `03-Mechanical-Design/02_Progetto_Modulare_e_Mobilita.md`, `GPIO8` e `GPIO9` sono invece assegnati a `I2C_EXT_SDA` / `I2C_EXT_SCL` (connettore JST-XH verso Base Mobile B2), mentre `GPIO17` e `GPIO18` sono `UART_TX_MOT` / `UART_RX_MOT`.

**Proposta pulita senza conflitti** (usando i GPIO liberi `1, 2, 10, 11, 12, 13, 14, 21`):
- **Sensore Tattile TTP223**: **`GPIO1`** (o **`GPIO14`**) — GPIO pulito, supporta interrupt hardware e wake-up RTC (`EXT0`/`EXT1`), lascia liberi `GPIO8/9` per il bus I²C esterno della base B2!
- **Base Mobile B2 (JST-XH 6 pin)**: mantiene `GPIO17/18` (UART o PWM/DIR se pilotaggio diretto) e `GPIO8/9` (`I2C_EXT` per `VL53L0X`), più eventuale `GPIO10` / `GPIO11` per sensori cliff IR o `STBY`.

---

## 5. Architettura Software Proposta e Opportunità di Riutilizzo

```text
[05-Voice-AI (PC / futuro RPi)]
   VoiceController ──▶ EyeBridge (SerialEyeTransport) ──▶ USB-CDC / UART
                                                              │
                                                              ▼
[ESP32-S3 Firmware (04-Firmware/jarvis-desk-buddy)]
   ├── StateMachine (estesa: AUDIO:<0..100>, EVENT:TOUCH=...)
   ├── TouchManager (nuovo, opzionale via #ifdef / feature flag)
   │      └── Debounce + Single / Double / Long / Release
   ├── EyeEngine v4 (evoluzione incrementale di Eyes 3.0)
   │      ├── 14 espressioni invariate
   │      ├── Blink asimmetrico + micro-animazioni
   │      └── Bocca opzionale sincronizzata con AudioLevel
   ├── SensorManager (evoluzione di SensorBridgeStub)
   └── MotionController (nuovo, disabilitato di default se B2 assente)
          └── Watchdog 500 ms + limiti PWM + STOP prioritario + cliff check
```

**Principi di modularità e compatibilità**:
- Ogni nuova funzione è attivabile/disattivabile a compile-time o runtime (graceful fallback): JARVIS continua ad avviarsi e funzionare identicamente in configurazione statica senza touch né base mobile.
- **Massimo riutilizzo**: `EyeBridge`, `StateMachine`, `EyeEngine` (Eyes 3.0), `DisplayDriver` (`SH1106`/`SSD1306`) e `MonochromeFramebuffer` restano la base unica.

---

## 6. Possibilità e Limiti di Simulazione su Wokwi

| Funzionalità | Supporto Wokwi Online (`wokwi.com`) | Come simularla in sicurezza (isolata da Eyes 3.0) | Limiti rispetto al reale |
|---|---|---|---|
| **Touch** | ⚠️ `TTP223` non è part nativo (esistono custom chip o `wokwi-pushbutton` su GPIO dedicato). | Usare un secondo `wokwi-pushbutton` dedicato (logica touch) o seriale `SIM:TOUCH_*` in una copia/branch sperimentale, lasciando intatto `wokwi-web`. | Non testa capacità attraverso plastica ABS né falsi tocchi RF/I2S. |
| **Eyes 4.0** | ✅ Pieno (`board-ssd1306` + `U8g2`). | Testabile al 100% su Wokwi Web con frame rate, transizioni e bocca. | `SSD1306` (`0 px` offset) vs `SH1106` (`+2 px`). |
| **Voice Reactions** | ⚠️ Nessun microfono/audio AI reale su Wokwi. | Simulazione eventi via Serial Monitor (`STATE:LISTENING`, `THINKING`, `SPEAKING`, `AUDIO:75`). | Non testa latenza USB reale né sincronizzazione audio `MAX98357A`. |
| **Base Mobile** | ⚠️ `TB6612FNG` / `VL53L0X` richiedono custom chips; `HC-SR04` e `LED`/`Servo` sono nativi. | Testare solo la **logica** (macchina a stati motori, timeout watchdog, stop ostacoli con `wokwi-hc-sr04` e LED direzionali). | Non testa spunto/stallo motori, cadute reali da tavolo, Buck 5V né attrito ruote LEGO. |

---

## 7. Distinta Componenti Preliminare

### Già posseduti / Confermati nel progetto
- ESP32-S3-DevKitC-1 N16R8 (collaudata FASE 10.1)
- OLED 1,3" I²C `1.30'' IIC V2.2` (da collaudare elettricamente)
- Microfono INMP441, Amplificatore MAX98357A, Speaker 4 Ω / 3 W, Pulsante NO

### Componenti aggiuntivi da valutare (NON acquistati)

| Componente | Funzione | Specifiche essenziali | Compatibilità ESP32-S3 / GPIO | Alim. / Consumo indicativo | Dim. indicative | Fascia prezzo indicativa | Necessità |
|---|---|---|---|---|---|---|---|
| **Modulo Touch TTP223B** (o TTP223) | Rilevamento tocco sulla testa LEGO | `2.0–5.5 V`, uscita digitale push-pull, risposta ~60 ms | ✅ 3,3 V / 1 GPIO (`GPIO1` o `GPIO14`) | `3.3 V` / ~`1.5–3 µA` idle, ~`0.5 mA` attivo | ~`15×11 mm` | ~`1–3 €` (pack multipli) | **Consigliato** (FASE 11.1) |
| **2× Motoriduttori DC N20 6V** (100–200 RPM) + ruote LEGO-compatibili | Trazione differenziale Modulo B2 | Albero D 3 mm, coppia ~1–2 kg·cm | Tramite driver `TB6612FNG` | `6–7.4 V` / `150–250 mA` nom., `~1 A` stallo cad. | `24×12×10 mm` | ~`8–15 €` la coppia | **Necessario** solo per FASE 11.4 |
| **Driver motori TB6612FNG** | Controllo PWM + direzione 2 motori | Dual H-Bridge `1.2 A` cont. / `3.2 A` picco | ✅ Logica `3.3 V` / 5–7 GPIO (o MCU su B2 via UART) | `VM 6–8.4 V`, `VCC 3.3 V` | ~`20×20 mm` | ~`3–6 €` | **Necessario** solo per FASE 11.4 |
| **Ruota libera (Caster)** | Terzo punto d'appoggio B2 | Sfera metallo/nylon `Ø 15–20 mm` | Meccanica | — | `Ø 15–20 mm` | ~`2–4 €` | **Necessario** solo per FASE 11.4 |
| **Sensore ToF VL53L0X** | Anticollisione frontale | I²C `0x29`, range `30–1200 mm` | ✅ `3.3 V` / I²C esterno (`GPIO8/9`) | `3.3 V` / ~`20 mA` | ~`13×10 mm` | ~`3–6 €` | **Necessario** per FASE 11.4 |
| **2× Sensori IR Cliff** (es. TCRT5000) | Rilevamento bordi tavolo (anti-caduta) | Uscita digitale/analogica corto raggio | ✅ `3.3 V` / 2 GPIO su B2 | `3.3–5 V` / ~`20 mA` cad. | ~`14×32 mm` | ~`2–5 €` | **Opzionale** (obbligatorio se usato su tavoli) |
| **Batteria Li-Ion/LiPo 2S (7.4 V) con BMS + Buck DC-DC 5V 3A + Interruttore + Fusibile** | Alimentazione autonoma B2 + Modulo A | Protezione sovracorrente/scarica, `5 V` stabili per ESP32+Audio | — | `7.4 V` → `5 V` | Vano B2 | ~`15–25 €` | **Necessario** solo per FASE 11.4 |

*(Prezzi e disponibilità commerciali sono fasce indicative di mercato per breakout hobby comuni e vanno verificati al momento dell'acquisto.)*

---

## 8. Rischi Tecnici Principali e Mitigazioni

1. **Conflitto GPIO `8/9` tra Touch (`pinout_config.h`) e `I2C_EXT` (`02_Progetto_Modulare_e_Mobilita.md`)**: assegnare subito il Touch a `GPIO1` (o `GPIO14`).
2. **Falsi tocchi TTP223 attraverso ABS o vicino a I2S**: testare con tile reale da `1.6 mm`, eventuale lamina rame interna, debounce + filtro temporale.
3. **Sovraccarico rail `3.3 V` o `5 V` da motori/speaker**: separazione netta tra rail batteria `VM` (motori) e rail Buck `5 V` (ESP32-S3 + MAX98357A), massa comune, condensatori di disaccoppiamento e fusibile PTC `2 A`.
4. **Caduta da superfici rialzate**: bloccare uso di B2 a pavimento oppure integrare 2 sensori cliff anteriori prima di qualsiasi movimento autonomo.
5. **Regressione sulla simulazione Wokwi funzionante**: sviluppare ogni nuova sottofase in modo isolato/incrementale senza toccare i file base di `wokwi-web` finché non validata.

---

## 9. Piano di Sviluppo per Sottofasi e Raccomandazione Sequenza

### Valutazione della sequenza
L'utente ha chiesto di valutare se convenga anticipare parte della **FASE 11.3 (Voice Reactions)** rispetto alla **11.2 (Eyes 4.0)**.
**Raccomandazione tecnica: SÌ, anticipare o accorpare il collegamento base `Voice AI ↔ ESP32-S3` prima o insieme a Eyes 4.0.** Motivazione:
- `EyeBridge`, `SerialEyeTransport`, `VoiceController` e `StateMachine` esistono **già** e funzionano.
- Collegando subito gli eventi conversazionali reali (`LISTENING`, `THINKING`, `SPEAKING`, `HAPPY`, `IDLE`, `CONFUSED`) + `AUDIO:<0..100>` si verifica immediatamente la pipeline end-to-end su Wokwi/seriale, e la **bocca animata** di Eyes 4.0 nasce già guidata da dati reali anziché fittizi.

### Sequenza consigliata
1. **FASE 11.1 — Touch Interaction**: `TouchManager` (`TOUCH_SINGLE`, `TOUCH_DOUBLE`, `TOUCH_LONG`, `TOUCH_RELEASE`), assegnazione `GPIO1`, test logico su Wokwi (pulsante dedicato) e futuro test su TTP223B reale sotto ABS LEGO.
2. **FASE 11.3-A — Voice Reactions (Core)**: collegamento `VoiceController → SerialEyeTransport → StateMachine` + comando `AUDIO:<0..100>` throttled.
3. **FASE 11.2 — Eyes 4.0**: evoluzione incrementale di `EyeEngine` (blink asimmetrico, micro-animazioni, bocca opzionale guidata da `AUDIO:<0..100>`), testata su Wokwi Web.
4. **FASE 11.4 — Mobile Base (Modulo B2)**: progettazione dettagliata PCB/cablaggio JST-XH, logica `MotionController` con watchdog e test *wheels-up*, poi prototipo fisico a pavimento.

*(Prerequisito hardware parallelo raccomandato prima dei test fisici di audio/touch: completare il collaudo elettrico dell'OLED SH1106 reale già in possesso.)*

---

## 10. Test e Criteri di Accettazione

- **Touch**:
  - *Simulato / Automatico*: unità C++/Python per debounce (`35 ms`), finestra doppio tocco (`350 ms`), soglia tocco lungo (`1200 ms`), priorità su auto-demo e rilascio pulito.
  - *Hardware reale*: prova attraverso brick/tile ABS `1.6 mm` con audio MAX98357A attivo (0 falsi trigger in 5 minuti).
- **Eyes 4.0**:
  - *Simulato / Automatico*: `30 FPS` stabili, nessuna regressione sui `35` test simulatore e sui `14` ID espressione, zero pixel fuori margini `128×64`, consumo RAM statico invariato (`1024 B` framebuffer).
  - *Wokwi Web*: verifica visiva fluidità transizioni e leggibilità bocca+occhi.
- **Voice Reactions**:
  - *Automatico*: latenza comando `EyeBridge → StateMachine` `< 50 ms`, throttling `AUDIO` (`≤ 20 Hz`), ripristino stato `IDLE` su interruzione o errore TTS/STT.
- **Mobile Base**:
  - *Logica / Simulato*: timeout watchdog `500 ms` → `STOP`, precedenza assoluta comando `STOP`, `STBY=LOW` al boot.
  - *Hardware reale progressivo*: (1) test banco senza carico, (2) test *wheels-up* con alimentazione 2S + Buck 5V, (3) test a pavimento a velocità ridotta con arresto ostacolo `VL53L0X`.

---

## 11. Decisioni Ancora Necessarie dall'Utente

1. **Sequenza di avvio**: confermare se iniziare dalla **FASE 11.1 (Touch Interaction)** oppure anticipare la **FASE 11.3-A (Voice Reactions bridge)** / **11.2 (Eyes 4.0 su Wokwi)**.
2. **GPIO per Touch TTP223**: approvare l'uso di **`GPIO1`** (o **`GPIO14`**) al posto di `GPIO8` per evitare il conflitto con `I2C_EXT_SDA` della futura Base Mobile B2.
3. **Bocca animata in Eyes 4.0**: confermare se desideri la bocca opzionale attiva durante `SPEAKING` (alzando leggermente gli occhi su `128×64`) oppure preferisci mantenere solo l'espressività degli occhi.
4. **Uso Base Mobile B2**: confermare il vincolo di utilizzo **solo a pavimento** (evitando sensori cliff aggiuntivi) oppure l'aggiunta di 2 sensori cliff per eventuale uso su tavolo.
