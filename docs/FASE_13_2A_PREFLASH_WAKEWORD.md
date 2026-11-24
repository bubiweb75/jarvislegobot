# FASE 13.2A — Preparazione pre-flash al test fisico `microWakeWord` («Hey Jarvis»)

**Data**: 2026-11-19  
**Stato**: **PRONTO AL FLASH** (nessun flash eseguito; firmware stabile FASE 12.27 e servizi live invariati)

---

## 1. Identificazione hardware e porta seriale

- **Porta seriale verificata**: `COM6` (`USB-Enhanced-SERIAL CH343`, `USB\VID_1A86&PID_55D3\5C83027497`, unico dispositivo seriale connesso, porta libera).
- **Chip rilevato via `esptool v5.3.1`**: `ESP32-S3 (QFN56) (revision v0.2)`.
- **Flash**: `16 MB` (Manufacturer `68`, Device `4018`, mode `quad`, `3.3V`).
- **PSRAM**: `Embedded PSRAM 8MB (AP_3v3)`.
- **MAC**: `<ESP32_MAC_ADDRESS>`.

---

## 2. Backup pre-flash e integrità (`05-Voice-AI/backups/fase13_2_preflash/`)

- **Backup completo 16 MB della Flash attuale**: `esp32_fase13_2_preflash_full_16mb.bin`
  - **Dimensione**: `16.777.216` byte (`16 MB`)
  - **SHA-256**: `3206F1933AF561A72C35CC376C45EF162BC543D7351ABE32B58D5AF8FFF22307`
  - **Metodo**: lettura non distruttiva in 4 blocchi da `4 MB` (`chunk0` a `460800` baud, `chunk1..3` a `921600` baud) con `esptool v5.3.1`, assemblati e verificati (`16.777.216` B). *(Da non includere nei push GitHub perché potenzialmente contenente NVS/credenziali).*
- **Backup precedente FASE 12.27 verificato presente**: `05-Voice-AI/backups/fase12_27_preflash/esp32_preflash_full_16mb_backup.bin` (`16.777.216` B).
- **Tabella partizioni salvata**: `05-Voice-AI/backups/fase13_2_preflash/preflash_partitions.bin` (`4.096` B).

---

## 3. Tabella partizioni effettiva (letta da `0x8000`)

| Partizione | Type | SubType | Offset | Dimensione |
| :--- | :---: | :---: | :--- | :--- |
| `nvs` | 1 | 2 | `0x009000` | `0x005000` (`20.480` B) |
| `otadata` | 1 | 0 | `0x00E000` | `0x002000` (`8.192` B) |
| **`app0`** | **0** | **16** | **`0x010000`** | **`0x140000` (`1.310.720` B)** |
| `app1` | 0 | 17 | `0x150000` | `0x140000` (`1.310.720` B) |
| `spiffs` | 1 | 130 | `0x290000` | `0x160000` (`1.441.792` B) |
| `coredump` | 1 | 3 | `0x3F0000` | `0x010000` (`65.536` B) |

Confermato `app0: offset 0x010000, size 0x140000` (`1.310.720` B).

---

## 4. Verifica prototipo e compilazione finale

- **Sorgenti verificati (`04-Firmware/experiments/fase13-wakeword/`)**:
  - `MicroWakeWordDetector` reale con `hey_jarvis.tflite` (`52.272` B, `SHA256: 21A7976A...`, Apache-2.0), `Chirale_TensorFLowLite 2.0.0`, `FrontendProcessSamples` (`microfrontend` 40 bande Mel), `kTensorArenaBytes = 32768U`, `kProbabilityCutoff = 0.97f`, `kSlidingWindowSize = 5U`, `PreRollRingBuffer` PSRAM (`8.000` campioni = `500 ms`), `I2S0` singolo proprietario (`WS=4, SCK=5, SD=6`), fallback `GPIO47`, log seriali strutturati, nessuna scrittura persistente su Flash/NVS.
- **Compilazione finale**:
  - Comando: `arduino-cli compile --fqbn "esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M" --library "...\Chirale_TensorFLowLite-2.0.0" --output-dir "05-Voice-AI\backups\fase13_2_preflash\proto_bin" "04-Firmware\experiments\fase13-wakeword"`
  - **Esito**: `exit code 0`
  - **Artefatto**: `05-Voice-AI/backups/fase13_2_preflash/proto_bin/fase13-wakeword.ino.bin`
  - **Dimensione binario**: **`484.448` byte** (`484.301` B programma, **`36%`** di `1.310.720` B — margine `826.272` B in `app0`).
  - **RAM globale**: **`25.964` byte** (`7%` di `327.680` B, `301.716` B liberi).
  - **SHA-256 binario sperimentale**: `C51FBF34760D6063C1893D4294890BE6B826D8DDA64A2A0D02BDB952F0A6DD75`.

---

## 5. Piano di flash controllato (FASE 13.2B, solo su autorizzazione)

Scrittura del **solo binario applicativo** in `app0` (`0x10000`), senza `erase-flash`, senza modificare bootloader, partizioni o NVS:
```powershell
esptool.exe --chip esp32s3 --port COM6 --baud 921600 --before default-reset --after hard-reset write-flash -z --flash-mode dio --flash-freq 80m --flash-size 16MB 0x10000 "05-Voice-AI\backups\fase13_2_preflash\proto_bin\fase13-wakeword.ino.bin"
```

---

## 6. Piano di ripristino del firmware stabile (FASE 12.27)

### A. Ripristino del solo firmware applicativo (metodo ordinario raccomandato)
Ripristina esclusivamente `app0` (`0x10000`) preservando `nvs`, `otadata`, `spiffs` e `app1`:
- Binario stabile verificato: `%USERPROFILE%\AppData\Local\arduino\sketches\AEB726B127D25F7785B9334C50418BFD\jarvis_wifi_voice_client.ino.bin` (`1.155.664` B, `SHA256 = AED27D18E64FE65DFBD007D31CE40944607A7182880A8B02B347EE7F0EF57E14`), scrivibile a `0x10000` (ripristina Wi-Fi, WSS Voice Bridge, OLED, microfono, speaker, pulsante `GPIO47` e limite 8 s).

### B. Ripristino integrale della Flash (operazione eccezionale)
Da eseguire solo in caso di corruzione estesa e previa autorizzazione dedicata (sovrascrive tutta la Flash inclusi `nvs`/`spiffs`):
- Immagine completa: `05-Voice-AI/backups/fase13_2_preflash/esp32_fase13_2_preflash_full_16mb.bin` (`16.777.216` B, `SHA256 = 3206F1933AF561A72C35CC376C45EF162BC543D7351ABE32B58D5AF8FFF22307`).

---

## 7. Piano di collaudo previsto per la FASE 13.2B e rischi

- **Test A–I**: avvio e allocazione arena/PSRAM, riconoscimento *"Hey Jarvis"* (distanze varie, 5 ripetizioni, pronuncia italiana naturale), falsi positivi, rumore ambientale, fallback `GPIO47` e stabilità prolungata (`[WAKE_INFERENCE_MS]`, `[WAKE_SCORE]`, heap/PSRAM).
- **Rischi / criticità**:
  1. Durante il test del solo prototipo isolato, le normali funzioni di assistente Wi-Fi/WSS/OLED/TTS del robot saranno temporaneamente sospese fino al ripristino di `app0` stabile.
  2. Il modello `hey_jarvis.tflite` è addestrato in inglese (`trained_languages: ["en"]`): l'accuratezza con pronuncia italiana naturale va verificata fisicamente.
