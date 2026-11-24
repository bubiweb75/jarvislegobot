# FASE 13.3 — Piano di Integrazione Definitiva (`microWakeWord` + `Eyes 3.0` + `FASE 12.27`)

## 1. Obiettivo e Vincoli
Integrare il rilevamento locale continuo **"Hey Jarvis"** (`microWakeWord` v2 INT8) nel firmware vocale completo **FASE 12.27** (`jarvis_wifi_voice_client`), mantenendo intatti:
- Animazioni originali **Eyes 3.0** su OLED I2C (`SSD1306` / `SH1106`), senza riscriverle.
- Stack vocale completo **Wi-Fi + WSS TLS + Whisper + Ollama + Piper Profilo 08**.
- Pulsante **GPIO47** come attivazione alternativa e cancellazione (`STOP/CANCEL`).
- Speaker silenzioso su `I2S_NUM_1` durante `IDLE` e correzione anti-ri-trigger (`kPostCycleGuardMs = 1000 ms`).

---

## 2. Analisi Architetturale del Firmware Stabile (FASE 12.27)

Il firmware stabile [jarvis_wifi_voice_client.ino](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/jarvis_wifi_voice_client.ino) è già strutturato in moduli indipendenti:

| Modulo | Responsabilità | Core / Risorse |
|---|---|---|
| `AudioCapture` | Acquisizione `I2S_NUM_0` (`WS=4, SCK=5, SD=6`, `16 kHz`, shift `>> 6` dopo `>> 8` con rimozione DC) | Core 0 task `jarvis_audio_rx` (prio 3, stack `4096 B`) |
| `AudioPlayback` | Riproduzione `I2S_NUM_1` (`BCLK=15, LRC=16, DIN=7`, `16 kHz`, fade + `kSilenceFlushFrames=960`) | Core 0 task `jarvis_audio_tx` (prio 3, stack `4096 B`) |
| `NetworkBridgeClient` | Wi-Fi + `WebSocketsClient` TLS verso Voice Bridge | Core 1 task `network_task` |
| `EyeController` / `EyeEngine` | Animazioni `Eyes 3.0` su OLED `I2C` (`30 FPS`) | Core 1 `loop()` |
| `ButtonController` | Debounce e fronti su `GPIO47` | Core 1 `loop()` |

### Mappatura Stati `RobotState` → `Eyes 3.0` (`SystemState`)
Già presente in `MapToEyeState()`:
- `kIdle` → `SystemState::kIdle` (`Expression::kNeutral`: sguardi naturali e battiti di palpebre `EyeEngine`)
- `kRecording` → `SystemState::kListening` (`Expression::kListening`)
- `kUploading` / `kProcessing` / `kReceiving` → `SystemState::kProcessing` (`Expression::kThinking`)
- `kPlaying` → `SystemState::kPlaying` (`Expression::kSpeaking` + blink e sguardo)
- `kError` → `SystemState::kError` (`Expression::kConfused`)

---

## 3. Risultati della Build Integrata Separata (Verifica Obbligatoria)

È stata creata e compilata una copia sperimentale isolata in [fase13_3-integrated](04-Firmware/experiments/fase13_3-integrated/fase13_3-integrated.ino), **senza modificare** il firmware stabile FASE 12.27 e **senza eseguire flash**.

- **Comando**: `arduino-cli compile --fqbn "esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M"` con `--libraries "04-Firmware\experiments\fase13-wakeword\libs"` e `"%USERPROFILE%\Documents\Arduino\libraries"`.
- **Esito**: **`exit code 0`** (nessun conflitto di simboli o librerie tra `ESP_I2S 3.3.13`, `U8g2 2.36.19`, `Wire 3.3.13`, `WiFi 3.3.13`, `WebSockets 2.7.2`, `NetworkClientSecure 3.3.13` e `Chirale_TensorFlowLite 2.0.0`).
- **Flash occupata**: **`1.297.733` byte (`99%`)** su **`1.310.720` byte** (`app0`), margine residuo **`12.987` byte**.
- **RAM dinamica globale**: **`72.244` byte (`22%`)** su **`327.680` byte**, **`255.436` byte** liberi per stack/heap.
- **PSRAM stimata**: `g_rx_buffer` (`256 KB`) + `g_tx_buffer` (`640 KB`) + `g_net` TTS (`640 KB`) + `g_preroll` (`16 KB`) ≈ **`1,55 MB`** su `8 MB` OPI (`~6,4 MB` liberi).

---

## 4. Punti Chiave di Integrazione e Ottimizzazioni Consigliate

### A. Margine Flash (`99%` di `app0`)
Il binario entra in `app0` senza modificare la tabella delle partizioni, ma con margine ridotto (`12.987 B`). Prima di considerare qualsiasi ripartizionamento, si applicano ottimizzazioni sicure:
1. Ridurre o condizionare dietro `#ifdef JARVIS_DEBUG_VERBOSE` i log seriali non essenziali (guadagno stimato `4–8 KB`).
2. Verificare l'uso del solo costruttore/font `U8g2` strettamente utilizzato in `display_driver.cpp`.
3. Disabilitare eventuali log interni di `WebSocketsClient` / `Chirale_TensorFlowLite` non richiesti in produzione.

### B. Speaker silenzioso in `IDLE`
In `AudioPlayback::Begin()`, aggiungere `WriteZeroFlush(kSilenceFlushFrames)` subito dopo `i2s_tx_.begin(...)` (come già validato in FASE 13.2E/F), eliminando ogni fruscio sul MAX98357A fin dal boot.

### C. Concorrenza Audio, Wake Word e Animazioni `Eyes 3.0`
- **Opzione consigliata in produzione**: eseguire `ReadChunk(160)` + `g_preroll.Push()` + `g_wake.ProcessFrame10ms()` nel task `jarvis_audio_rx` su **Core 0** quando `state == kIdle` (aumentando `kTaskStackBytes` di `AudioCapture` da `4096` a `8192–12288` byte per l'interprete TFLite Micro), comunicando `WAKE_DETECTED` a Core 1 tramite flag atomico/coda. In questo modo `loop()` su **Core 1** non attende mai `I2S` né i `~2,92 ms` di inferenza, garantendo `Eyes 3.0` fluidi a `30 FPS` su `I2C`.
- **Inibizione durante `SPEAKING` e anti-ri-trigger**: il detector resta fermo durante `kRecording`, `kUploading`, `kProcessing`, `kReceiving`, `kPlaying`; al ritorno a `kIdle`, esegue `g_wake.Reset()`, `g_preroll.Clear()` e applica `kPostCycleGuardMs = 1000 ms`.

### D. Fine registrazione vocale (VAD End-of-Speech)
Con `GPIO47` (push-to-talk), la registrazione termina al rilascio del pulsante. Con attivazione **"Hey Jarvis"**, l'utente non tiene premuto alcun tasto: serve quindi un **rilevatore di fine parlato (VAD)** in `kRecording` (es. arresto automatico dopo `~1.0–1.2 s` di silenzio consecutivo sotto soglia RMS dopo aver superato una soglia minima di parlato, mantenendo `kMaxRecordMs = 8000 ms` come limite massimo e `GPIO47` per stop anticipato).

---

## 5. Piano di Test, Accettazione e Rollback

1. **Test 1 — Boot & Idle**: OLED mostra `Eyes 3.0` naturali fluidi (`30 FPS`), speaker silenzioso (`0` fruscio), Wi-Fi/WSS autenticati, `microWakeWord` attivo in background.
2. **Test 2 — Wake Word E2E**: pronunciare «Hey Jarvis» + domanda -> passaggio immediato a `LISTENING` -> stop VAD a fine frase -> `THINKING` -> `SPEAKING` (risposta Piper Profilo 08) -> ritorno a `IDLE` senza ri-trigger.
3. **Test 3 — Fallback GPIO47**: pressione manuale `GPIO47` funziona sia per avviare la registrazione in `IDLE` sia per interrompere (`CANCEL`) in `PROCESSING`/`SPEAKING`.
4. **Test 4 — Stabilità & Memoria**: verifica runtime di `ESP.getFreeHeap()`, `ESP.getFreePsram()`, `uxTaskGetStackHighWaterMark()` e assenza di reset WDT per >= 10 minuti.

### Strategia di Rollback
- **Software**: flag `#define JARVIS_ENABLE_WAKEWORD 1` per disattivare la wake word in un click tornando al solo `GPIO47`.
- **Hardware/Flash**: il backup completo `16 MB` FASE 12.27 (`esp32_fase13_2_preflash_full_16mb.bin`, `SHA-256 = 3206F193...`) resta integro in `05-Voice-AI/backups/fase13_2_preflash/` per ripristino immediato in `app0`.
