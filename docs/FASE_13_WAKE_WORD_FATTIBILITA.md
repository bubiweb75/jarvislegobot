# FASE 13 — Wake Word sempre attiva «Hey Jarvis»: Studio di fattibilità, architettura e prototipo isolato

**Data**: 2026-11-19  
**Stato**: **Studio di fattibilità completato + prototipo scheletrico isolato compilato (nessuna modifica al firmware stabile, nessun flash eseguito)**

---

## 1. Analisi hardware esistente

Hardware verificato (FASE 12.27):
- **MCU**: `ESP32-S3-DevKitC-1 N16R8` (`ESP32-S3 QFN56 rev v0.2`, dual-core Xtensa LX7 @ 240 MHz con istruzioni vettoriali SIMD/PIE, **Flash 16 MB**, **PSRAM OPI 8 MB**).
- **Microfono**: `INMP441` I²S (`WS=GPIO4`, `SCK=GPIO5`, `SD=GPIO6`), `16000 Hz`, mono, 24-bit in slot 32-bit convertiti a PCM16.
- **Amplificatore + Speaker**: `MAX98357A` I²S (`DIN=GPIO7`, `BCLK=GPIO15`, `LRC=GPIO16`), speaker `4 Ω / 3 W`.
- **OLED**: `SH1106 128×64` (`SDA=GPIO41`, `SCL=GPIO42`).
- **Pulsante**: `GPIO47` active LOW.

**Verdetto hardware**: l'hardware esistente è **pienamente sufficiente** per il rilevamento locale continuo di una wake word tramite reti neurali quantizzate INT8 o WakeNet, senza alcun acquisto o modifica di pinout.

---

## 2. Analisi compatibilità firmware attuale (FASE 12.27)

Valori **misurati** sul firmware stabile (`04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/`):
- **Core Arduino**: `esp32` **`3.3.13`** (`ESP_I2S`, `U8g2`, `WebSockets`, `ESP_SR` presente nella toolchain).
- **Partizione applicativa realmente installata** (letta da `0x8000` nella FASE 12.27):
  - `app0`: offset `0x010000`, dimensione **`0x140000` (`1.310.720` byte = `1.25 MB`)**.
  - **Nessuna partizione `model` presente** (`nvs`, `otadata`, `app0`, `app1`, `spiffs`, `coredump`).
- **Occupazione attuale del firmware stabile (FASE 12.26)**:
  - **Flash programma**: `1.155.664` byte (`88.2%` della partizione `app0` da `1.310.720` B -> **`155.056` byte liberi** in `app0`).
  - **RAM dinamica globale**: `55.036` byte (`16%` di `327.680` B -> **`272.644` byte liberi**).
  - **PSRAM audio usata**: `256.000` B (RX 8 s) + `640.000` B (TX) + `640.000` B (TTS net) = `1.536.000` B (`1.46 MB` su `8 MB` -> **~`6.5 MB` liberi**).

---

## 3. Tecnologie esaminate e supporto reale di «Hey Jarvis»

### A. Espressif `ESP-SR` / `WakeNet9` (incluso in Arduino ESP32 `3.3.13`)
- **Supporto ESP32-S3**: nativo, accelerato via istruzioni SIMD ESP32-S3.
- **Supporto esatto «Hey Jarvis»**: **NO** nei modelli preaddestrati pubblici. Il catalogo `esp-sr` include `wn9_jarvis_tts` (**"Jarvis"**, non **"Hey Jarvis"**) oltre a modelli come `Hi, ESP` / `Alexa`. L'addestramento di una wake word personalizzata per WakeNet non è aperto in self-service gratuito (richiede richiesta/servizio di personalizzazione Espressif).
- **Vincolo critico sulle partizioni**: `esp32-hal-sr.c` richiede partizioni dedicate `esp_sr_16` / `esp_sr_16_app4M` con partizione `model` da **`3.875 MB`** (`0x3E0000` in `esp_sr_16.csv`), **incompatibile** con la partizione `app0` attuale senza ripartizionare la Flash.

### B. `microWakeWord` (`kahrendt/microWakeWord` / ESPHome + TFLite Micro)
- **Supporto ESP32-S3**: sì, progettato specificamente per ESP32-S3 (`16 kHz` mono PCM16, 40 feature Mel-spettrogramma ogni `10 ms` con `micro_speech` frontend, rete MixConv INT8 streaming).
- **Supporto esatto «Hey Jarvis»**: **SÌ**, esiste il modello ufficiale preaddestrato **`hey_jarvis` / `hey_jarvis_v2` (`.tflite` INT8)** pronto all'uso, ed è possibile eseguire fine-tuning aperto con campioni sintetici Piper (incluse pronunce italiane/inglesi di *"Hey Jarvis"*).
- **Licenza**: **Apache-2.0** (100% open-source, nessuna chiave cloud, nessun check online).
- **Impatto partizioni e Flash**: modello `.tflite` **`~20–50 KB`** incorporabile come array C `const uint8_t[]` direttamente dentro `app0` (nessuna partizione `model` separata!). Runtime TFLite Micro + frontend `~80–150 KB` di codice Flash (nota: con `155 KB` residui nell'attuale `app0` da `1.25 MB`, l'integrazione finale potrebbe avvicinarsi al tetto di `1.25 MB`, rendendo opzionale un futuro passaggio a `app3M_fat9M_16MB` se il binario superasse `1.310.720` B).
- **Compatibilità Arduino**: `TFLite Micro` non è pre-incluso nel core Arduino `3.3.13`; richiede l'integrazione di una libreria `esp-tflite-micro` / `TensorFlowLite_ESP32` compatibile con ESP32-S3 (oppure build ESP-IDF / PlatformIO).

### C. Picovoice Porcupine (alternativa commerciale/proprietaria)
- **Supporto ESP32-S3**: sì, inferenza offline a bassa latenza (`16 kHz` PCM16).
- **Supporto esatto «Hey Jarvis»**: keyword integrata `"Jarvis"`; `"Hey Jarvis"` richiede generazione custom via Picovoice Console (spesso vincolata a UUID hardware su target MCU).
- **Vincolo critico di licenza/offline**: richiede `AccessKey` e validazione periodica/iniziale verso i server Picovoice (non è 100% privo di dipendenze di licenza cloud nel tier gratuito).

---

## 4. Tabella comparativa tecnica

*(I valori indicati come **stima** provengono dalla documentazione ufficiale delle rispettive librerie; i valori **misurati** provengono dal repository locale.)*

| Criterio | A. Espressif `ESP-SR` (`WakeNet9`) | B. `microWakeWord` (`TFLite Micro`) | C. Picovoice Porcupine |
| :--- | :--- | :--- | :--- |
| Supporto ESP32-S3 | Sì (nativo SIMD) | Sì (streaming INT8) | Sì |
| Wake word esatta «Hey Jarvis» | **No** (solo `wn9_jarvis_tts` = "Jarvis") | **Sì** (`hey_jarvis.tflite` ufficiale) | Parziale ("Jarvis" built-in; custom via Console) |
| Funzionamento 100% offline | Sì | **Sì** | Inferenza offline, ma check `AccessKey` |
| RAM (SRAM) richiesta | Stima ~`200–350 KB` (AFE + WN9) | Stima ~`23–100 KB` (tensor arena + frontend) | Stima ~`50–100 KB` |
| PSRAM richiesta | Consigliata/usata da AFE (~`1–2 MB` stima) | Opzionale (`16 KB` pre-roll + arena se in PSRAM) | Minima |
| Flash richiesta | **Misurato**: partizione `model` `3.875 MB` (`esp_sr_16.csv`) | Stima `~20–50 KB` modello + `~80–150 KB` TFLite Micro | Stima `~100–200 KB` |
| Carico CPU | Stima medio (1 core dedicato AFE+WN) | Stima moderato (`10 ms` frame streaming) | Stima basso |
| Latenza rilevamento | Stima `< 200 ms` | Stima `~100–250 ms` | Stima `< 100 ms` |
| Falsi positivi / negativi | Basso su modelli ufficiali | Basso (`hey_jarvis_v2`); regolabile via soglia | Molto basso |
| Compatibilità Arduino `3.3.13` | Inclusa (`ESP_SR`), ma richiede partizione `esp_sr` | Richiede libreria `esp-tflite-micro` esterna | Richiede SDK/wrapper C + `AccessKey` |
| Complessità integrazione | Media (ma richiede ripartizionamento) | Media (dipendenza TFLite Micro + frontend) | Media-Alta (licenza/UUID) |
| Licenza | Espressif (binari precompilati) | **Apache-2.0** | Proprietaria (`AccessKey`) |

---

## 5. Soluzione raccomandata

**Raccomandazione: `microWakeWord` (`hey_jarvis_v2` INT8 su `TFLite Micro`)** — **Fattibilità: POSSIBILE CON LIMITAZIONI**.

Motivazioni:
1. È **l'unica soluzione open-source (Apache-2.0) e 100% offline** con modello preaddestrato ufficiale per la frase esatta **«Hey Jarvis»**.
2. Non richiede alcuna chiave cloud (`AccessKey`) e consente eventuale **fine-tuning locale** con campioni sintetici Piper per ottimizzare la pronuncia italiana di *"Hey Jarvis"*.
3. Non richiede la partizione `model` da `3.875 MB` di `ESP_SR`.
4. **Limitazione principale da gestire nella futura fase di integrazione**:
   - Porting/inclusione del runtime `esp-tflite-micro` + `micro_speech` frontend in Arduino `3.3.13` (oppure build PlatformIO/ESP-IDF).
   - Lo spazio residuo nell'attuale partizione `app0` da `1.25 MB` è **`155.056` B**: se `TFLite Micro + hey_jarvis.tflite` dovesse superare `~155 KB`, sarà necessaria una futura autorizzazione dedicata per passare a `app3M_fat9M_16MB` (nessuna modifica fatta ora).

*(Nota su addestramento personalizzato, Sez. 5.D: qualora il modello standard `hey_jarvis` avesse falsi negativi con accento italiano, l'addestramento aggiuntivo con `kahrendt/microWakeWord` richiederebbe ~5.000–20.000 campioni positivi sintetici/reali con voci diverse e ~10.000+ negativi con rumore ambientale e parole simili come "Ehi Gianni", "Jarvis", TV/conversazioni — nessun addestramento avviato in questa fase.)*

---

## 6. Architettura audio e macchina a stati

### Unico proprietario I²S (`I2S0`)
Un solo task FreeRTOS (`Core 0`, `Prio 3`) legge in modo continuo dal microfono `INMP441` frame da `10 ms` (`160` campioni @ `16000 Hz`, mono `PCM16`) e li instrada al **dispatcher**:
- In `WAKE_LISTENING`: scrive nel `PreRollRingBuffer` volatile (`8.000` campioni = `500 ms` in PSRAM, `16 KB`) e alimenta `IWakeWordDetector::ProcessFrame10ms()`. **Nessun dato viene inviato via Wi-Fi/WSS.**
- Al trigger (`WAKE_DETECTED` da «Hey Jarvis» o pressione pulsante `GPIO47`): svuota il pre-roll da `500 ms` in testa a `g_rx_buffer` (`256.000` B = `8 s` max), cambia occhi OLED, riproduce un eventuale breve beep locale, e passa a `COMMAND_LISTENING` (fino a `8 s` max, con eventuale timeout di silenzio opzionale).
- In `PROCESSING`: invia `g_rx_buffer` via WSS al Voice Bridge (se offline, ritorna in `RECOVERY` -> `WAKE_LISTENING` senza bloccare la wake word locale).
- In `SPEAKING`: sospende/inibisce il detector (`detector.Reset()` + gate attivo finché `g_playback.IsPlaying()` + `250 ms` di guardia post-TTS) per **prevenire l'autoattivazione** dalla voce di JARVIS.
- In `ERROR` / `RECOVERY`: timeout di sicurezza (`2000 ms`) con reset controllato dello stato e ritorno automatico a `WAKE_LISTENING`.

### OLED (Eyes 3.0) e Pulsante `GPIO47` — Requisito definitivo per l'integrazione completa
- **`IDLE` (riposo + `microWakeWord` attivo in background)**: mantiene le animazioni naturali esistenti di **Eyes 3.0** (movimento degli occhi, sguardi e battiti di palpebre, `SystemState::kIdle`), **senza cambiare espressione** durante l'ascolto passivo della wake word e con speaker silenzioso.
- **`WAKE_DETECTED` / `COMMAND_LISTENING` (o pressione `GPIO47`)**: passa immediatamente all'animazione **`LISTENING`** esistente di Eyes 3.0 (`SystemState::kListening`).
- **`PROCESSING`**: mostra **`THINKING` / `Processing`** (`SystemState::kProcessing`).
- **`SPEAKING`**: mostra **`SPEAKING`** (`SystemState::kPlaying`) durante la risposta vocale, quindi torna automaticamente alle animazioni **`IDLE`** al termine.
- **Vincoli di integrazione**: riutilizzare integralmente `EyeController` / `EyeEngine` (Eyes 3.0) su Core 1 (`I2C` 400 kHz) senza ricreare animazioni provvisorie nel prototipo isolato e senza bloccare il rendering OLED durante l'inferenza `microWakeWord` (`~2.9 ms` su Core 0/1).
- `GPIO47` resta pienamente funzionante come attivazione alternativa manuale (in `IDLE` avvia `LISTENING`; in `LISTENING`/`PROCESSING`/`SPEAKING` mantiene la semantica attuale di stop/cancel).

---

## 7. Prevenzione rischi e privacy

- **Falsi positivi / negativi**: soglia di confidenza + finestra di voto su frame consecutivi (es. media mobile su 3–5 frame da `10 ms`); eventuale fine-tuning con accento italiano.
- **Autoattivazione**: inibizione del detector durante `SPEAKING` + `250 ms` di coda silenziosa.
- **Perdita inizio domanda**: `PreRollRingBuffer` volatile da `500 ms` (`16 KB` PSRAM) copiato all'inizio della registrazione.
- **Privacy**: il ring buffer è esclusivamente volatile in RAM/PSRAM e sovrascritto ogni `500 ms`; **nessun audio ambientale viene salvato o trasmesso** fino a `WAKE_DETECTED`.
- **Rollback funzionale**: flag di compilazione/runtime `ENABLE_WAKE_WORD` (disabilitabile per tornare istantaneamente al solo pulsante `GPIO47`).

---

## 8. Prototipo isolato (`04-Firmware/experiments/fase13-wakeword/`)

Creato un prototipo scheletrico modulare e completamente isolato dal firmware stabile:
- [fase13-wakeword.ino](04-Firmware/experiments/fase13-wakeword/fase13-wakeword.ino)
- [wakeword_engine.h](04-Firmware/experiments/fase13-wakeword/wakeword_engine.h)
- [wakeword_engine.cpp](04-Firmware/experiments/fase13-wakeword/wakeword_engine.cpp)

### Risultati compilazione (senza flash)
Comando:
```powershell
arduino-cli compile --fqbn "esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M" "04-Firmware\experiments\fase13-wakeword"
```
- **Esito**: **`exit code 0`**
- **Flash**: `317.725` byte (`24%` di `1.310.720` B)
- **RAM dinamica globale**: `23.708` byte (`7%` di `327.680` B, `303.972` B liberi)
- **Limiti del prototipo iniziale**: usava `PreGateStubDetector` nella prima iterazione; nella successiva **FASE 13.1** è stato sostituito dal vero rilevatore `MicroWakeWordDetector` (`Chirale_TensorFLowLite 2.0.0` + `hey_jarvis.tflite` `52.272` B), portando il binario compilato a **`484.301` byte Flash (`36%`, delta `+166.576` B)** e **`25.964` byte RAM globale (`7%`, delta `+2.256` B)**. Dettagli completi in [FASE_13_1_MICROWAKEWORD_INTEGRAZIONE.md](docs/FASE_13_1_MICROWAKEWORD_INTEGRAZIONE.md). **Nessun test fisico o flash eseguito.**

---

## 9. Piano di test per la futura fase autorizzata

Una volta integrato `microWakeWord` (`hey_jarvis`) su autorizzazione esplicita:
- **Test A–B**: attivazione *"Hey Jarvis"* a `0.5 m`, `1.5 m`, `3.0 m` (target riconoscimento `>= 90%`, latenza `< 300 ms`).
- **Test C–D**: rumore ambientale (TV/voci) e parole simili (*"Ehi Gianni"*, *"Jarvis"*, *"Hey Siri"*) per misurare falsi risvegli/ora (`target <= 1/ora`).
- **Test E–F**: attivazioni consecutive e test anti-autoattivazione durante TTS Profilo 08.
- **Test G–H**: riconoscimento locale con Voice Bridge offline + verifica pulsante `GPIO47`.
- **Test I**: stabilità prolungata (heap libero, PSRAM libera, assenza reset WDT).

---

## 10. Risultati Collaudo Prototipo Isolato — FASE 13.2F e FASE 13.2G (Test D–I)

Collaudo eseguito su `ESP32-S3` (`COM6`, `115200` baud) con il prototipo isolato FASE 13.2E/F (`proto_bin_13_2e/fase13-wakeword.ino.bin`, `485.136` B, `SHA-256 = 7B48BA7459D0136D6C97E5DA1AF140AD3189217F9D9163D16F9E5C5417A6495E` in `app0` @ `0x10000`), mantenendo invariati modello `hey_jarvis_v2_int8` (`52.272` B), soglia `0.970`, speaker silenzioso su `I2S_NUM_1` e stato iniziale `IDLE`.

### Riepilogo sessioni FASE 13.2G (osservazione seriale diretta)

| Test | Obiettivo | Finestra | Risultato osservato | Telemetria chiave |
|---|---|---|---|---|
| **D — Distanza** | `30 cm`, `1 m`, `2 m` (3× ciascuno) | `90 s` (`task-4456`) | **9 `[WAKE_DETECTED]`** (`score=0.988–0.996`, `smooth=0.973–0.994`), più 1 picco sotto soglia alle `17:05:02.206` (`raw=0.938`, `smooth=0.916`) | `heap=284380`, `psram=8368656`, inf `2.87–2.98 ms`, `clip=0`, `sat=0`, 0 reset |
| **E — Pronuncia** | Italiano naturale vs Inglese (3× ciascuno) | `60 s` (`task-4464`) | **8 `[WAKE_DETECTED]`** (`score=0.996`, `smooth=0.970–0.993`), ritorno regolare in `IDLE` | `heap=284380`, `psram=8368656`, inf `2.86–2.98 ms`, `clip=0 sat=0` a regime, 0 reset |
| **F — Falsi positivi** | Parole diverse, incluso «Jarvis» solo | `60 s` (`task-4468`) | **1 `[WAKE_DETECTED]`** alle `17:07:41.767` (`score=0.996`, `smooth=0.980`); **1 picco sotto soglia** alle `17:07:26.466` (`raw=0.633`, `smooth=0.775`); resto della sessione `raw=0.000` | `heap=284380`, `psram=8368656`, inf `2.89–2.97 ms`, `clip=0 sat=0` a regime, 0 reset |
| **G — Rumore ambientale** | Silenzio vs TV moderata | `60 s` (`task-4472`) | **0 falsi positivi** nei tratti senza wake word (`rms=88–385`); **4 `[WAKE_DETECTED]`** (`score=0.996`, `smooth=0.973–0.990`) | `heap=284380`, `psram=8368656`, inf `2.89–2.97 ms`, `clip=0 sat=0` a regime, 0 reset |
| **H — Pulsante GPIO47** | Attivazione manuale e ritorno in `IDLE` | `30 s` (`task-4476`) | **5/5 attivazioni `src=GPIO47`** con ciclo completo `IDLE → WAKE_DETECTED → COMMAND_LISTENING → PROCESSING → SPEAKING → IDLE` (`0.41–2.34 s`) | `heap=284380`, `psram=8368656`, inf `2.87–3.05 ms`, `clip=0 sat=0` a regime, 0 reset |
| **I — Stabilità** | `>= 10 minuti` continui | `610 s` (`task-4480`) | **`303` campioni inferenza**, **`0` reset**, **`0` errori**, **`0` falsi positivi** (`wakes=0`) | `heap=284856` fisso (zero leak), `psram=8368656` fisso, inf `min=2.89 / avg=2.92 / max=3.01 ms` |

### Note tecniche emerse
1. **Stabilità e memoria**: in oltre 10 minuti continui (`610 s`), `heap` (`284.856` B in `IDLE` continuo; `284.380` B dopo attivazioni) e `psram` (`8.368.656` B) sono rimasti perfettamente costanti senza memory leak, errori o reset WDT.
2. **Tempi di inferenza**: stabili tra `2.86 ms` e `3.05 ms` (media `2.92 ms` su `303` campioni nel Test I).
3. **Transitorio avvio I²S**: al solo primo frame post-boot (`~1.7 s` dopo `POWERON`) si osserva un breve transitorio ADC/I²S (`clip=11..170`), poi `clip=0` e `sat=0` per l'intera durata della sessione.
4. **Falso positivo / controllo Test F**: l'attivazione alle `17:07:41.767` in Test F è stata registrata nei log e resta da classificare in base alla parola pronunciata in quell'istante (es. «Jarvis» isolato vs prova di controllo).
5. **Requisito integrazione Eyes 3.0**: confermato che il prototipo isolato non include Eyes 3.0; durante la futura integrazione nel firmware completo, lo stato `IDLE` dovrà mantenere le animazioni naturali Eyes 3.0 su OLED con `microWakeWord` in background e passare a `LISTENING` / `THINKING` / `SPEAKING` solo su `WAKE_DETECTED` o `GPIO47`.
