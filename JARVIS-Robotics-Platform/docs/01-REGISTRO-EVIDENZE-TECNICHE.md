# Registro delle Evidenze Tecniche della Baseline

> **JARVIS Robotics Platform** — Tracciamento Fonti Tecniche e Baseline  
> **Fase:** RP-02  
> **Data:** 24 Novembre 2026  
> **Stato:** Baseline Verificata e Immutabile  

---

## 1. Dati di Ispezione del Repository Principale

- **Repository Locale:** ``
- **Branch:** `main` (ahead di 1 commit rispetto a `origin/main`)
- **Ultimo Commit Ufficiale su HEAD:** `53f1bce test(hardware): validate Eyes 3.0 on ESP32-S3 SH1106`
- **Working Tree:** Modifiche locali e file untracked comprendenti le Fasi 10.2, 10.3, 11, 12 e 13 consolidate al 19 Novembre 2026.
- **Hardware Target di Riferimento:**
  - MCU: Espressif **ESP32-S3-DevKitC-1 N16R8** (ESP32-S3 QFN56 rev v0.2, Dual-Core Xtensa LX7 @ 240 MHz).
  - MAC Address rilevato fisicamente: **`<ESP32_MAC_ADDRESS>`**.
  - Porta di Comunicazione: **`COM6`** (`USB-Enhanced-SERIAL CH343`).
  - Memoria: **16 MB Flash SPI**, **8 MB Octal PSRAM OPI**.
  - Display: **OLED SH1106 monocromatico 128×64 da 1,3 pollici** (I2C `GPIO 41 SDA / 42 SCL`, indirizzo `0x3C`, Fast-Mode 400 kHz).
  - Audio Input: **Microfono I2S MEMS INMP441** (`WS=GPIO4`, `SCK=GPIO5`, `SD=GPIO6`), 16 kHz 16-bit mono.
  - Audio Output: **Amplificatore I2S Class-D MAX98357A** (`DIN=GPIO7`, `BCLK=GPIO15`, `LRC=GPIO16`), speaker 4 Ω / 3 W.
  - Input Utente: **Sensore capacitivo TTP223B** (`GPIO 1`, active HIGH) + **Pulsante PTT fisico** (`GPIO 47`, active LOW).

---

## 2. Riferimenti di Codice della Golden Baseline Eyes 3.0

I file sorgente analizzati per definire la baseline grafica immutabile sono:
- `04-Firmware/jarvis-desk-buddy/include/eye_engine.h`
- `04-Firmware/jarvis-desk-buddy/src/eye_engine.cpp`
- `04-Firmware/arduino-hw-test/jarvis_eyes3_hw_test/`
- `04-Firmware/jarvis-desk-buddy-sim/eye_engine.py`

### Parametri Costitutivi della Geometria Baseline Verificata
```cpp
// Coordinate e Geometria Ufficiale (eye_engine.h / eye_engine.cpp)
static constexpr int kDefaultEyeWidth = 38;      // Larghezza nominale 38 px
static constexpr int kDefaultEyeHeight = 38;     // Altezza nominale 38 px
static constexpr int kDefaultCornerRadius = 11;  // Raggio raccordi 11 px
static constexpr int kDefaultSpacingPx = 16;     // Spaziatura tra occhi 16 px

// Parametri Superellittici Organici
float shape_power = 2.6f;                        // Esponente superellisse
float taper = 0.10f;                             // Conicità verticale
float pupil_radius = 7.0f;                       // Raggio pupilla base
float brow_offset = 4.0f;                        // Offset sopracciglia
float brow_arch = 2.2f;                          // Arco sopracciglia
float brow_tilt = 0.0f;                          // Inclinazione sopracciglia neutra
```

### Enumerazione Ufficiale delle 14 Espressioni
```cpp
enum class Expression : uint8_t {
    kNeutral = 0,
    kHappy,
    kCurious,
    kSleepy,
    kListening,
    kThinking,
    kSpeaking,
    kSurprised,
    kShy,
    kLove,
    kWink,
    kConfused,
    kMischievous,
    kSleeping
};
```

---

## 3. Riferimenti Build Firmware e Partizioni Esistenti

- **Tabella Partizioni Attuale (letta da offset `0x8000` via esptool):**
  - `nvs`: `0x009000` (`20.480` B)
  - `otadata`: `0x00E000` (`8.192` B)
  - `app0`: `0x010000` (`1.310.720` B = `1.25 MB`)
  - `app1`: `0x150000` (`1.310.720` B = `1.25 MB`)
  - `spiffs`: `0x290000` (`1.441.792` B)
  - `coredump`: `0x3F0000` (`65.536` B)
- **Dimensione Firmware FASE 13.6 collaudato:** `1.299.328` byte (margine residuo in `app0`: `11.392` byte).
- **Backup di Rollback di Riferimento:** `05-Voice-AI/backups/fase13_2_preflash/fase12_27_app0_rollback.bin` (`SHA256 = AED27D18E64FE65DFBD007D31CE40944607A7182880A8B02B347EE7F0EF57E14`).
- **Backup 16 MB Integrale Flash:** `05-Voice-AI/backups/fase12_27_preflash/esp32_preflash_full_16mb_backup.bin` (`SHA256 = 34D8C031F74E3227766757645881442574B59201C99CA8580ADDE5C940FC3CC6`).
