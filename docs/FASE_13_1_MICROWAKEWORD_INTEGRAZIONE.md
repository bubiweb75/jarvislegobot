# FASE 13.1 — Integrazione reale `microWakeWord` + «Hey Jarvis» (prototipo isolato)

**Data**: 2026-11-19  
**Stato**: **COMPLETATA (prototipo reale compilato con `exit code 0`; nessun flash eseguito; firmware stabile invariato)**

---

## 1. Modello e licenza verificati

- **Sorgente ufficiale**: `esphome/micro-wake-word-models` (`models/v2/hey_jarvis.json`, `models/v2/hey_jarvis.tflite`) — autore Kevin Ahrendt (`microWakeWord` v2).
- **Licenza**: **Apache-2.0** (`04-Firmware/experiments/fase13-wakeword/model/LICENSE`, `11.357` B).
- **Dimensione modello**: **`52.272` byte** (`SHA256 = 21A7976ADD39EE24EC96C63D96B7AAA18E24D1D9824B963E451DA8FEB4B78B77`).
- **Parametri ufficiali (`hey_jarvis.json`)**:
  - `wake_word`: `"Hey Jarvis"`, `trained_languages`: `["en"]`, `version`: `2`.
  - `probability_cutoff`: `0.97`, `feature_step_size`: `10` ms, `sliding_window_size`: `5`, `tensor_arena_size`: `22860` B.
- **Ispezione FlatBuffer (`hey_jarvis.tflite`)**:
  - Input `serving_default_input_audio:0`: `shape=[1, 3, 40]`, `INT8`, `scale=0.1019607857`, `zp=-128`.
  - Output `StatefulPartitionedCall:0`: `shape=[1, 1]`, `UINT8`, `scale=0.00390625` (`1/256`), `zp=0`.
  - Operatori usati: `ASSIGN_VARIABLE`, `CALL_ONCE`, `CONCATENATION`, `CONV_2D`, `DEPTHWISE_CONV_2D`, `FULLY_CONNECTED`, `LOGISTIC`, `QUANTIZE`, `READ_VARIABLE`, `RESHAPE`, `STRIDED_SLICE`, `VAR_HANDLE`.

---

## 2. Runtime TensorFlow Lite Micro e dipendenze locali

- **Libreria integrata localmente** (senza installazioni globali Arduino): **`Chirale_TensorFLowLite 2.0.0`** in `04-Firmware/experiments/fase13-wakeword/libs/Chirale_TensorFLowLite-2.0.0/`.
- Include nativamente sia tutti i 12 operatori richiesti (inclusi `VAR_HANDLE`, `READ_VARIABLE`, `ASSIGN_VARIABLE`, `CALL_ONCE` + `MicroResourceVariables`), sia `tensorflow/lite/experimental/microfrontend/lib/frontend.h` (`FrontendProcessSamples`) per la generazione delle 40 bande Mel ogni `10 ms` (`window=30 ms`, `125–7500 Hz`, noise reduction, PCAN gain, log scale).
- **Core Arduino**: `esp32:esp32 3.3.13` (`ESP_I2S 3.3.13`, `Wire 3.3.13`).

---

## 3. File creati/aggiornati (area isolata `04-Firmware/experiments/fase13-wakeword/`)

- `model/hey_jarvis.json`, `model/hey_jarvis.tflite`, `model/LICENSE`
- `hey_jarvis_model.h` (`const unsigned char g_hey_jarvis_tflite[52272]`, `alignas(16)`)
- `wakeword_engine.h` & `wakeword_engine.cpp`: classe `MicroWakeWordDetector` (sostituisce `PreGateStubDetector`), `PreRollRingBuffer` PSRAM (`8.000` campioni = `500 ms`), `MicroMutableOpResolver<13>`, `MicroResourceVariables`, smoothing su `5` finestre e soglia `0.97`.
- `fase13-wakeword.ino`: proprietario singolo `I2S0` (`WS=4`, `SCK=5`, `SD=6`), fallback `GPIO47`, stati `BOOT -> WAKE_LISTENING -> WAKE_DETECTED -> COMMAND_LISTENING -> PROCESSING -> SPEAKING -> RECOVERY`, guardia post-TTS `250 ms` e log `[WAKE_INIT_OK]`, `[WAKE_MODEL_LOADED]`, `[WAKE_ARENA_BYTES]`, `[WAKE_INFERENCE_MS]`, `[WAKE_SCORE]`, `[WAKE_DETECTED]`, `[WAKE_RESET]`, `[WAKE_ERROR]`.
- `tests/test_fase13_1_offline.py`: test automatici offline.

---

## 4. Misurazioni reali di compilazione vs stime

Comando eseguito (senza flash):
```powershell
arduino-cli compile --fqbn "esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M" --library "...\libs\Chirale_TensorFLowLite-2.0.0" "04-Firmware\experiments\fase13-wakeword"
```
- **Esito**: **`exit code 0`**
- **Flash prototipo FASE 13.1 (reale `microWakeWord`)**: **`484.301` byte** (`36%` di `1.310.720` B) — incremento reale rispetto allo stub FASE 13 (`317.725` B) pari a **`+166.576` byte** (`52.272` B modello + `~114.304` B runtime TFLite Micro & microfrontend).
- **RAM dinamica globale (reale)**: **`25.964` byte** (`7%` di `327.680` B, `301.716` B liberi) — incremento reale rispetto allo stub (`23.708` B) pari a **`+2.256` byte**.
- **Tensor arena configurata**: `32.768` byte (`>= 22.860` B richiesti dal modello; allocazione primaria in SRAM interna con fallback PSRAM).
- **Pre-roll buffer**: `16.000` byte in PSRAM (`8.000` campioni @ `16 kHz`).
- **Tempi di inferenza CPU e heap runtime**: *non misurabili senza esecuzione fisica su ESP32-S3* (previsti nella futura FASE 13.2).

---

## 5. Verifica compatibilità con partizione `app0` attuale (`1.310.720` byte)

- Firmware stabile attuale (FASE 12.27): **`1.155.664` byte** (`155.056` B liberi in `app0`).
- Delta reale misurato di `microWakeWord + hey_jarvis.tflite`: **`+166.576` byte**.
- **Somma stimata sull'attuale firmware completo**: `1.155.664 + 166.576 = 1.322.240` byte -> **eccede il limite `app0` attuale (`1.310.720` B) di ~`11.520` byte (~`11.3 KB`)**.
- **Implicazioni**:
  1. **FASE 13.2 (collaudo fisico del prototipo isolato)**: **già compatibile** con la partizione `app0` attuale (`484.301` B = `36%`), senza toccare le partizioni.
  2. **Futura integrazione completa nel firmware stabile**: richiederà o il passaggio autorizzato allo schema `app3M_fat9M_16MB` (`3.145.728` B per `app0`, `~1.8 MB` di margine), oppure una riduzione di `~15 KB` nel firmware principale.

---

## 6. Pronuncia italiana e rischi residui

- `hey_jarvis.tflite` v2 è addestrato su dataset inglese (`"trained_languages": ["en"]`). L'accuratezza reale con pronuncia italiana naturale (falsi positivi e falsi negativi) **non può essere certificata offline** e dovrà essere verificata fisicamente nella FASE 13.2 (regolando eventualmente `kProbabilityCutoff` / `kSlidingWindowSize` o pianificando un fine-tuning con campioni Piper).
- Test offline (`test_fase13_1_offline.py`): **`4/4 OK`**.
- **Firmware stabile**: `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` **100% invariato**; **nessun flash eseguito**.

---

## 7. Piano per la FASE 13.2 (subordinato a nuova autorizzazione esplicita)

1. Verifica porta seriale, chip `ESP32-S3` e tabella partizioni.
2. Verifica integrità backup `esp32_preflash_full_16mb_backup.bin` (o nuovo snapshot se necessario).
3. Flash controllato **del solo prototipo isolato** (`484.301` B in `app0`, nessuna modifica alle partizioni).
4. Misurazione reale via seriale di `[WAKE_ARENA_BYTES]`, `[WAKE_INFERENCE_MS]`, heap libero, riconoscimento *"Hey Jarvis"* con voce italiana, falsi positivi/negativi, rumore ambientale e stabilità.
5. Ripristino del firmware stabile FASE 12.27 al termine delle prove sperimentali.
