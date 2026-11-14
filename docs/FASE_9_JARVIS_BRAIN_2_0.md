# FASE 9.0 — Analisi e Progettazione di JARVIS BRAIN 2.0

> **Stato:** Documento di analisi e progettazione architetturale (`FASE 9.0`).  
> **Vincoli rispettati:** Nessuna modifica a firmware (`04-Firmware/jarvis-desk-buddy/`), simulatore (`04-Firmware/jarvis-desk-buddy-sim/`), Voice AI (`05-Voice-AI/`) o design LEGO (`03-Mechanical-Design/`); nessuna nuova dipendenza o hardware aggiuntivo.  
> **Commit di riferimento:** `8465e91` (`main`).

---

## 1. Analisi AS-IS del Progetto

L'architettura attuale su `main` integra tre sottosistemi Python su PC Windows 11 (target Ryzen 7 5700U, 16 GB RAM) e un firmware C++ su ESP32-S3 pronto per il primo collaudo fisico:

1. **Firmware ESP32-S3 (`04-Firmware/jarvis-desk-buddy/`):** compilabile su `esp32s3_sh1106` e `esp32s3_ssd1306` (0 warning), implementa 14 espressioni OLED (`eye_engine.cpp`), macchina a stati non bloccante (`millis()`), pulsante su `GPIO 47`, protocollo seriale USB-CDC (`PING`, `STATUS`, `DIAG`, `HELP`, `BLINK`, `AUTO:ON/OFF`, `STATE:*`, `LOOK:dx,dy`) e `SensorBridgeStub` (`SENSORS=STUB_ONLY`). Non gestisce ancora audio I²S né driver sensori reali.
2. **Simulatore Windows (`04-Firmware/jarvis-desk-buddy-sim/`):** `JarvisSimulatorApp` (`simulator_gui.py`) esegue `EyeEngine`, `EmotionEngine` (Personalità C, `21` `StimulusType`, priorità e cooldown), `SensorManager` (`Sensor Lab` per `VL53L0X`, `TTP223`, `MPU6050`, `BH1750` con isteresi, debounce, dwell e cooldown) e `monochrome_fb.py`. Verificato da **20 test automatici**.
3. **Voice AI (`05-Voice-AI/`):** `JarvisUnifiedApp` (`jarvis_app.py`) affianca il simulatore OLED al pannello Voice & AI. `VoiceController` coordina Push-to-Talk (`WindowsMciAudioRecorder`), STT (`faster-whisper` via `AutoLocalSTTProvider`), LLM (`OllamaProvider` su `qwen2.5:3b`, `OpenAIProvider`, `DemoAIProvider`), TTS (`PiperWithFallbackTTSProvider` con voce `Piper Riccardo` + `voice_dsp.py` *Amichetto Vivace*), `ConversationManager` (solo RAM di sessione, `max_turns=6`) ed `EyeBridge` (`SimulatorQueueTransport` / `SerialEyeTransport`). Verificato da **12 test automatici**.
4. **Hardware & Meccanica (`06-Hardware-Integration/`, `03-Mechanical-Design/`):** guida al montaggio illustrata (FASE 8.2B-0) e progetto LEGO `Companion Hybrid v2` (144 pezzi, `10×10 stud`) pronti ma **in attesa dell'arrivo dei componenti fisici**.

---

## 2. Visione Funzionale JARVIS 2.0

JARVIS BRAIN 2.0 trasforma il sistema da *assistente Push-to-Talk reattivo a singoli stimoli* a **piccolo robot da compagnia coerente**, mantenendo la natura simulata (nessuna pretesa di coscienza o emozioni reali) e l'eseguibilità completa su Windows anche senza hardware fisico:
- **Identità costante:** giocoso, affettuoso, curioso, leggermente birichino, espressivo ma mai invadente.
- **Continuità tra sessioni:** ricorda solo preferenze e fatti autorizzati dall'utente, evitando ripetizioni meccaniche.
- **Comportamento coordinato:** voce, occhi OLED, sensori e routine quotidiane rispondono a un arbitro unico (`BehaviorEngine`) senza conflitti.

---

## 3. Matrice Funzionalità Esistenti / Mancanti

| Funzionalità / Modulo | Stato Attuale | Note e Riferimento Reale |
|---|---|---|
| **Firmware ESP32-S3 (14 espressioni, `DIAG`, `LOOK`, `GPIO 47`)** | 🟡 Implementato, non verificato fisicamente | Compila su `sh1106`/`ssd1306`; in attesa scheda reale |
| **Simulatore OLED 128×64 (`EyeEngine` + `JarvisSimulatorApp`)** | 🟢 Implementato e verificato | 20 test unitari passati (`test_simulator.py`) |
| **`EmotionEngine` (Personalità C, priorità, cooldown)** | 🟢 Implementato e verificato | Deterministico con seed, 21 stimoli (`emotion_engine.py`) |
| **`SensorManager` + `Sensor Lab` (4 sensori simulati)** | 🟢 Implementato e verificato | `test_sensor_manager.py` (6 test); driver reali mancanti |
| **Pipeline Voice AI (`faster-whisper` → `Ollama` → `Piper`)** | 🟢 Implementato e verificato | 12 test (`test_voice_ai.py`); voce *Riccardo Amichetto* |
| **`SerialEyeTransport` (PC → ESP32-S3 via USB)** | 🟡 Parzialmente implementato | Classe presente in `eye_bridge.py`, mai testata su COM reale |
| **Audio I²S su ESP32-S3 (`INMP441`, `MAX98357A`) e streaming USB** | 🟠 Soltanto documentato | `AUDIO_ARCHITECTURE.md` / `USB_PROTOCOL.md`; assente in C++ |
| **Driver fisici `VL53L0X`, `TTP223`, `MPU6050`, `BH1750` su ESP32** | 🟠 Soltanto documentato / stub | Solo `sensor_stub.h` (`SENSORS=STUB_ONLY`) in FASE 8.2A |
| **Personalità 2.0 (umore simulato, variazione risposte, preferenze)** | 🔴 Mancante | Oggi solo prompt statico `jarvis_system_it.txt` + `EmotionEngine` |
| **Behavior Engine (routine, quiet mode, arbitro centrale)** | 🔴 Mancante | Logica sparsa tra `VoiceController` e `EmotionEngine` |
| **Memory Engine locale controllabile (SQLite/JSON selettivo)** | 🔴 Mancante | `ConversationManager` è solo volatile (`max_turns=6`) |
| **Conversation Engine 2.0 (barge-in, turni, fallback offline)** | 🟡 Parzialmente implementato | Esiste `interrupt` su `VoiceController`; mancano pause/barge-in fluido |
| **Control Center unificato (evoluzione `JarvisUnifiedApp`)** | 🟡 Parzialmente implementato | `jarvis_app.py` integra già simulatore + Voice AI; mancano tab Memoria/Personalità/Diagnostica |

---

## 4. Architettura TO-BE (Modulare su Codice Esistente)

Nessun microservizio superfluo: tutto gira in un singolo processo Python locale su Windows (`JarvisUnifiedApp`), riutilizzando `EyeEngine`, `EmotionEngine`, `SensorManager`, `VoiceController` ed `EyeBridge`.

```text
[Sensori Simulati / Futuri Seriali] ──► [SensorManager] ──┐
[Timer / Routine / Orologio Locale] ─────────────────────┼─► [BehaviorEngine]
[VoiceController (STT/LLM/TTS)] ◄────────────────────────┘         │
        │                                  │                       ▼
        ▼                                  ▼               [EmotionEngine]
[MemoryEngine (SQLite/JSON)]      [PersonalityProfile]             │
        │                                                          ▼
        └──────────────► [ConversationEngine 2.0] ────────► [EyeEngine 2.0 / EyeBridge]
                                                                   │
                                                   ┌───────────────┴───────────────┐
                                                   ▼                               ▼
                                          [Simulatore Tk]               [SerialEyeTransport]
```

### Responsabilità dei Nuovi Moduli (senza ricreare l'esistente)
- **`PersonalityProfile` (`05-Voice-AI/personality.py`):** stato interno simulato (`energy`, `playfulness`, `affection` in `[0.0..1.0]`, decadimento graduale verso baseline) + parametri configurabili dall'utente (frequenza iniziative spontanee, tono, limiti). Non modifica `Piper Riccardo` né `voice_dsp.py`.
- **`BehaviorEngine` (`04-Firmware/jarvis-desk-buddy-sim/behavior_engine.py` o modulo condiviso):** arbitro centrale a tick deterministico (`update(now_ms)`). Riceve eventi da `SensorManager`, `VoiceController` e scheduler routine; applica `Quiet Mode`, modalità riposo, anti-ripetizione e passa gli stimoli validati a `EmotionEngine` senza duplicarne le tabelle priorità/cooldown.
- **`MemoryEngine` (`05-Voice-AI/memory_engine.py`):** archivio locale trasparente (JSON o SQLite locale con schema versionato).
- **`JarvisControlCenter`:** evoluzione diretta della colonna destra di `JarvisUnifiedApp` (`jarvis_app.py`) con notebook a schede (`Conversazione`, `Sensor Lab`, `Personalità & Routine`, `Memoria`, `Hardware & Diagnostica`), evitando una seconda GUI separata.

### Prestazioni su Windows (Ryzen 7 5700U, 16 GB RAM)
- `Ollama qwen2.5:3b` (~2–3 GB RAM) + `faster-whisper` (`small`/`base` CPU, ~0.5–1 GB) + `Piper` (~100 MB) + GUI Tkinter (`<80 MB`): l'aggiunta di `BehaviorEngine`, `PersonalityProfile` e `MemoryEngine` (SQLite/JSON locale) introduce **< 15 MB di RAM** e **< 1% CPU** a riposo, pienamente compatibile con 16 GB RAM.

---

## 5. Specifiche dei Comportamenti e Personalità 2.0

- **Tratti:** giocoso, affettuoso, curioso, leggermente birichino, ma rispettoso del silenzio.
- **Variazione naturale:** per i micro-cue ripetitivi (saluti, reazione a carezza `TTP223`, risveglio), `BehaviorEngine` mantiene una coda circolare degli ultimi `N=3` template usati per evitare ripetizioni consecutive.
- **Limiti alle iniziative spontanee:**
  - Massimo `1` iniziativa vocale spontanea ogni `15–20` minuti (solo fuori da `LISTENING`/`THINKING`/`SPEAKING` e fuori da `Quiet Mode`).
  - Se l'utente ignora `2` iniziative consecutive, backoff automatico (`2×` intervallo).
  - **Modalità Silenziosa (`Quiet Mode`):** disattiva ogni voce spontanea mantenendo solo reazioni OLED silenziose.
  - **Routine quotidiane (configurabili):** buongiorno al primo stimolo mattutino (`BH1750` luce o comando/pressione), promemoria pausa scrivania opzionale, modalità riposo serale (`SLEEPY` → `SLEEPING`).
- **Gestione errori / offline:** se `Ollama` o `faster-whisper` non rispondono, `BehaviorEngine` degrada in modo trasparente a risposte brevi di cortesia / `TEMP_ERROR` su OLED e `DemoAIProvider` opzionale, senza bloccare la GUI o il simulatore.

---

## 6. Proposta Memory Engine

Distinzione netta in **4 livelli**, con regola ferrea: **nessuna registrazione audio su disco** e **nessun salvataggio automatico indiscriminato delle chat**:

| Livello | Contenuto | Persistenza | Controllo Utente |
|---|---|---|---|
| **L1 — Contesto di sessione** | Ultimi `N` turni (`ConversationManager`, max 6–10) | Solo RAM (cancellato alla chiusura) | Pulsante *Nuova sessione* |
| **L2 — Preferenze confermate** | Nome utente, tono preferito, orari `Quiet Mode`, durata pause | Disco locale (opt-in) | Modifica / Reset da Control Center |
| **L3 — Fatti persistenti autorizzati** | Es. *"L'utente lavora spesso di sera"*, *"Ama i LEGO"* — salvati **solo** su conferma esplicita o comando | Disco locale (max `100` voci, TTL configurabile) | Lista consultabile, editabile ed eliminabile riga per riga |
| **L4 — Ricordi episodici selezionati** | Brevi riassunti di eventi speciali (es. *"Prima accensione completata"*) | Disco locale (max `30` voci con rotazione FIFO) | Toggle ON/OFF globale + cancella tutto |

**Prevenzione allucinazioni da memoria:**
- I fatti L2/L3 iniettati nel system prompt di `Ollama` sono etichettati con data e confidenza (`[FATTO CONFERMATO]`) e preceduti dall'istruzione esplicita di **non inventare dettagli non presenti** e di ammettere quando non ricorda qualcosa.
- Nessun filtro segreto: l'utente vede esattamente cosa viene passato al prompt.

---

## 7. Conversation Engine 2.0 ed EyeEngine 2.0

### Conversation Engine 2.0 (`faster-whisper → Ollama → Piper`)
- **Turni più fluidi e pause naturali:** separazione in chunk brevi per frasi complete (`. ! ?`) verso `Piper` così la sintesi inizia prima della fine completa della risposta LLM (riduzione latenza percepita), preservando al 100% `Piper Riccardo` e i parametri `voice_dsp.py` (*Amichetto Vivace*).
- **Interruzione del parlato (barge-in):** già supportata lato `VoiceController` tramite `_cancel_gen` su evento Stop/pulsante; in 2.0 può essere estesa a pulsante fisico `GPIO 47` (quando letto via seriale) o hotkey su PC.
- **Timeout e resilienza:** timeout espliciti su `Ollama` (con messaggio breve vocale/testuale di fallback invece di attesa muta) e coda audio protetta contro sovrapposizioni.

### EyeEngine 2.0 (Compatibile col Firmware 8.2A senza modifiche C++)
- **Eseguibile subito sia su Simulatore sia su Firmware ESP32-S3 pubblicato:**
  - **Sequenze di espressioni temporizzate** orchestrate da Python via `EyeBridge` (`STATE:SURPRISED` 600 ms → `STATE:CURIOUS` 1,5 s → `STATE:IDLE`).
  - **Sguardi contestuali** tramite il comando già esistente `LOOK:dx,dy` (es. sguardo verso il lato del microfono durante `LISTENING`, sguardo verso l'alto/lato in `THINKING`, piccoli sguardi esplorativi in `IDLE`).
  - **Sincronizzazione precisa** `LISTENING` → `THINKING` → `SPEAKING` → `HAPPY`/`WINK`/`IDLE`.
- **Proposte future (richiedono modifiche C++, NON implementate):** lip-sync/ampiezza bocca/occhi reattiva al volume PCM su ESP32 (`AUDIO_LEVEL` via seriale/USB), nuovi glyph animati su framebuffer C++.

---

## 8. JARVIS Control Center (Evoluzione di `JarvisUnifiedApp`)

Invece di creare una seconda applicazione, si evolve `05-Voice-AI/jarvis_app.py` (che già ospita `JarvisSimulatorApp` a sinistra e il pannello Voice a destra) trasformando la colonna destra in un **Control Center a schede (`ttk.Notebook`)**:
1. **Tab Conversazione & Stato:** fase attuale, espressione OLED attiva, umore simulato, chat, Push-to-Talk / Stop, `Quiet Mode` rapido.
2. **Tab Sensor Lab:** controllo interattivo dei 4 sensori simulati (`VL53L0X`, `TTP223`, `MPU6050`, `BH1750`) già esistenti in `simulator_gui.py`/`sensor_manager.py`.
3. **Tab Personalità & Routine:** slider giocosità/frequenza iniziative, orari riposo/silenzio, toggle routine.
4. **Tab Memoria:** visualizzazione, modifica, cancellazione selettiva di L2/L3/L4 e pulsante *Cancella tutto*.
5. **Tab Hardware & Diagnostica:** selezione porta COM (`SerialEyeTransport`), invio rapido `PING`/`DIAG`, stato `Ollama`/`faster-whisper`/`Piper`, log essenziali filtrati.

---

## 9. Roadmap Incrementale, Strategia di Test e Rischi

| Fase | Obiettivo | Hardware Richiesto? | Test e Criteri di Accettazione |
|---|---|---|---|
| **FASE 9.1** | `PersonalityProfile` + `BehaviorEngine` + `EyeEngine 2.0` (sequenze/sguardi via `EyeBridge`) | ❌ No (100% simulabile) | Unit test deterministici su priorità, `Quiet Mode`, anti-ripetizione, backoff |
| **FASE 9.2** | `MemoryEngine` selettivo (L1–L4) + integrazione `ConversationManager` | ❌ No | Test CRUD memoria, limiti TTL/cap, verifica assenza salvataggi non autorizzati |
| **FASE 9.3** | `Conversation Engine 2.0` (streaming frasi verso `Piper`, fallback offline/timeout) | ❌ No | Test latenza, interruzione pulita, fallback `Ollama` spento |
| **FASE 9.4** | `JARVIS Control Center` (evoluzione `jarvis_app.py` a schede + bridge `Sensor Lab`) | ❌ No (COM opzionale) | Smoke test GUI, persistenza impostazioni, invio comandi seriali mockati |
| **FASE 8.2B / 9.5** | Collaudo fisico ESP32-S3 + OLED + sensori + audio I²S | ✅ Sì (dopo consegna) | Checklist FASE 8.2B-0 + 6 test fisici progressivi |

**Rischi tecnici principali:**
- Conflitti di stato tra `BehaviorEngine` e `EmotionEngine` se non si mantiene `EmotionEngine` come esecutore unico dei cooldown per stimolo.
- Latenza su CPU Windows durante esecuzione simultanea di `Ollama` + `faster-whisper` (mitigata mantenendo modelli compatti e chunking leggero).
- Deriva della memoria persistente (mitigata da opt-in esplicito e limiti rigidi su numero voci).

---

## 10. Decisioni Approvate (Consolidamento FASE 9.0)

1. **Formato persistenza (`MemoryEngine` — FASE 9.2):** **SQLite** per preferenze e ricordi autorizzati; **JSON** per configurazioni applicative semplici. *(Non implementato in FASE 9.0/9.1).*
2. **Iniziative vocali spontanee:** massimo **`2` all'ora**, intervallo minimo **`20` minuti** (entrambe le soglie configurabili), con **disattivazione completa** possibile. Nessuna iniziativa vocale durante conversazioni, ascolto, riproduzione vocale o `Quiet Mode`.
3. **Roadmap:** approvata l'esecuzione della **FASE 9.1** (`BehaviorEngine` + `PersonalityProfile` + `EyeEngine 2.0`) dopo il consolidamento documentale della FASE 9.0.

---

## 11. Stato Implementazione FASE 9.1 — Moduli, Interfacce e Limiti Attuali

- **Funzionalità implementate e verificate (FASE 9.1):**
  - `04-Firmware/jarvis-desk-buddy-sim/personality.py` (`PersonalityProfile`, `PersonalityConfig`, `MoodState`): tratti Personalità C, controllo intensità/frequenza/variazione, selezione non ripetitiva dei cue (`pick_cue`) e validazione sicura dei limiti (`NaN`/negativi).
  - `04-Firmware/jarvis-desk-buddy-sim/eye_engine_v2.py` (`EyeEngine2`, `EyeStep`, `clamp_firmware_look`): sequenze temporizzate e sguardi contestuali compatibili al 100% con le 14 espressioni e i comandi `STATE:*`, `LOOK:dx,dy` (`-11..11`, `-6..6`), `BLINK` del firmware FASE 8.2A.
  - `04-Firmware/jarvis-desk-buddy-sim/behavior_engine.py` (`BehaviorEngine`, `RobotMode`, `BehaviorEvent`, `BehaviorDecision`): arbitro deterministico con priorità, interruzione sequenze a priorità inferiore, `Quiet Mode`, cooldown, limiti `2/ora` e `20 min`, blocco iniziative in `LISTENING`/`THINKING`/`SPEAKING`/`SLEEPING`, diagnostica limitata senza dati sensibili.
  - Integrazione nel loop non bloccante di `simulator_gui.py` (con protezione `try/except` e sincronizzazione modalità).
- **Funzionalità simulate:** `SensorManager` + `SimulatedSensorProvider` (`VL53L0X`, `TTP223`, `MPU6050`, `BH1750`), decadimento umore simulato in RAM.
- **Funzionalità predisposte ma non ancora integrate:**
  - *Iniziative vocali spontanee:* `BehaviorEngine` decide e produce il testo `voice_cue` rispettando tutti i vincoli, ma **non** è ancora collegato a `VoiceController` / `Piper` per la riproduzione audio effettiva (previsto nella **FASE 9.3**).
  - `MemoryEngine` (FASE 9.2) e `JARVIS Control Center` a schede (FASE 9.4) restano solo progettati.
- **Funzionalità che richiedono hardware fisico:** collaudo su ESP32-S3 reale, OLED fisico `SH1106`/`SSD1306`, sensori fisici e audio I²S (`INMP441`, `MAX98357A`).
