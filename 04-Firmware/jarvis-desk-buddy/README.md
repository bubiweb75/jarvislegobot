# JARVIS AI Desk Buddy — Firmware v0.1 (ESP32-S3 + OLED 1,3" I²C)

Primo firmware concreto per **Espressif ESP32-S3-DevKitC-1 N16R8** con display **Binghe OLED 1,3" I²C 128×64 monocromatico**, progettato con architettura a stati non bloccante (`millis()`) a 50 FPS e predisposto per il futuro collegamento seriale/USB al Raspberry Pi.

> [!NOTE]
> **Ambito di questa release:** Implementa esclusivamente il sottosistema visivo OLED (occhi espressivi, battito palpebre, sguardo organico), il pulsante fisico (`GPIO 47`) e l'interfaccia di controllo seriale per Raspberry Pi. Microfono `INMP441`, amplificatore `MAX98357A`, speaker e backend AI non sono ancora integrati.

---

## 1. Collegamenti Elettrici (ESP32-S3-DevKitC-1 N16R8 ↔ OLED 1,3" + Pulsante)

Tutti i pin rispettano la tabella definitiva del progetto (`01-Hardware/02_Tabella_Pinout_Definitiva.md`), evitando i pin riservati a PSRAM Octal (`GPIO 35–37`), strapping (`GPIO 0, 3, 45, 46`), USB nativo (`GPIO 19, 20`) e UART0 (`GPIO 43, 44`).

| Segnale | Pin OLED / Componente | Pin ESP32-S3 DevKitC-1 | Header DevKitC-1 | Note |
| :--- | :--- | :--- | :--- | :--- |
| **Alimentazione 3,3 V** | `VCC` (OLED) | **`3V3`** | `J1-1` o `J1-2` | Verificare sul retro PCB OLED che accetti `3,3 V` (standard moduli I²C) |
| **Massa comune** | `GND` (OLED) + Pin B Pulsante | **`GND`** | `J3-1` o `J1-22` | **Attenzione:** `J1-3` è `RST/EN`, **NON** `GND`! |
| **I²C Data** | `SDA` (OLED) | **`GPIO 41`** | `J3-7` | Bus I²C0 Hardware a `400 kHz` |
| **I²C Clock** | `SCL` (OLED) | **`GPIO 42`** | `J3-6` | Indirizzo tipico `0x3C` (rilevato automaticamente al boot) |
| **Pulsante Attivazione** | Pin A Pulsante NO | **`GPIO 47`** | `J3-17` | Pull-up interno abilitato, attivo `LOW` verso `GND` |

---

## 2. Verifica Controller OLED (`SH1106` vs `SSD1106/SSD1306`)

I display OLED 1,3" I²C commerciali (inclusi molti moduli Binghe dichiarati come *"SSD1106"*) montano molto spesso il controller **SH1106** (`132×64` RAM interna con offset di `2` pixel per lato), mentre altri montano **SSD1306/SSD1106** (`128×64` RAM). Poiché i due controller **non sono intercambiabili**, in `platformio.ini` sono pronti due ambienti di compilazione separati:

1. **`esp32s3_sh1106` (Default consigliato per 1,3"):** usa `U8G2_SH1106_128X64_NONAME_F_HW_I2C`.
2. **`esp32s3_ssd1306` (Alternativa):** usa `U8G2_SSD1306_128X64_NONAME_F_HW_I2C`.

**Come capire quale usare al primo test fisico:**
- Carica prima `esp32s3_sh1106`.
- Se l'immagine è nitida e centrata: il tuo modulo è **SH1106** (configurazione definitiva corretta).
- Se vedi una **banda verticale di rumore/pixel casuali larga 2 px sul bordo destro o sinistro** o lo schermo traslato orizzontalmente: compila e carica l'ambiente alternativo `esp32s3_ssd1306`.

---

## 3. Compilazione e Caricamento con PlatformIO

Dalla cartella `04-Firmware/jarvis-desk-buddy`:

```powershell
# Compila l'ambiente SH1106 (default)
pio run -e esp32s3_sh1106

# Compila l'ambiente alternativo SSD1306/SSD1106
pio run -e esp32s3_ssd1306

# Carica su ESP32-S3 via porta USB (sostituire COMx se necessario)
pio run -e esp32s3_sh1106 -t upload

# Apri il Monitor Seriale a 115200 baud
pio device monitor -b 115200
```

> **Nota porta USB su ESP32-S3-DevKitC-1:** La scheda ha due porte USB-C: **`USB`** (nativa CDC, usata da questo firmware con `-DARDUINO_USB_CDC_ON_BOOT=1`) e **`UART`** (bridge CP2102). Per il primo caricamento usa preferibilmente la porta **`USB`** (se non viene riconosciuta subito, tieni premuto `BOOT`, premi `RST`, poi rilascia `BOOT`).

---

## 4. Espressioni OLED, Protocollo Seriale e Preparazione Sensori (FASE 8.2A)

### A. Le 14 Espressioni OLED Supportate
Il firmware è allineato alle **14 espressioni** del simulatore Python (`eye_engine.py`):
- **Base / Operative (7):** `IDLE` (alias `NEUTRAL`), `HAPPY`, `CURIOUS`, `SLEEPY`, `LISTENING`, `THINKING`, `SPEAKING`
- **Espressive / Emotive (7):** `SURPRISED`, `SHY`, `LOVE`, `WINK`, `CONFUSED`, `MISCHIEVOUS`, `SLEEPING`

### B. Protocollo Seriale USB-CDC (`115200` baud, `\n`)
Comandi supportati:
- `PING` → `PONG`
- `STATUS` → `OK:STATE=...;AUTO=...;DRIVER=...`
- `DIAG` → `OK:DIAG;STATE=...;UPTIME_MS=...;FREE_HEAP=...;FREE_PSRAM=...;OLED_ADDR=0x...;DRIVER=...;SENSORS=STUB_ONLY`
- `HELP` → elenco comandi disponibili
- `STATE:<ESPRESSIONE>` → imposta una delle 14 espressioni (es. `STATE:LOVE`, `STATE:MISCHIEVOUS`, `STATE:IDLE`)
- `BLINK` → forza un battito di palpebre immediato
- `LOOK:<dx>,<dy>` → sposta lo sguardo per `2` secondi (`dx` in `-11..11`, `dy` in `-6..6`; fuori range restituisce `ERR:LOOK_RANGE (dx:-11..11,dy:-6..6)`)
- `AUTO:ON` / `AUTO:OFF` → attiva/disattiva la Demo Automatica

### C. Preparazione Architettura Sensori (FASE 8.2B — Solo Stub)
In `include/pinout_config.h` e `include/sensor_stub.h` sono predisposte le risorse per i sensori futuri senza driver attivi né letture simulate:
- `TTP223` (Touch capacitivo): `GPIO 8`
- `VL53L0X` (ToF prossimità, I²C `0x29`): `XSHUT` su `GPIO 9`
- `MPU6050` (IMU 6 assi, I²C `0x68`): `INT` su `GPIO 10`
- `BH1750` (Luce ambientale, I²C `0x23`): condiviso su I²C0 (`SDA=41`, `SCL=42`)

---

## 5. Compilazione PlatformIO su Windows e Primo Collaudo Fisico

### A. Comandi di Compilazione e Upload (Windows / PowerShell)
Dalla cartella `04-Firmware/jarvis-desk-buddy`:
```powershell
# Compilazione ambiente predefinito (SH1106 1.3")
pio run -e esp32s3_sh1106

# Compilazione ambiente alternativo (SSD1306 0.96")
pio run -e esp32s3_ssd1306

# Upload su ESP32-S3 e apertura Monitor Seriale
pio run -e esp32s3_sh1106 -t upload -t monitor --monitor-baud 115200
```

### B. Procedura di Collaudo Fisico (ESP32-S3 + OLED)
1. **Collegamento Hardware:** collega il display OLED a `3V3`, `GND`, `SDA=GPIO 41`, `SCL=GPIO 42` e il pulsante opzionale tra `GPIO 47` e `GND`.
2. **Test Rilevamento I²C:** apri il Monitor Seriale a `115200` baud e verifica il rilevamento all'indirizzo `0x3C` (o `0x3D`).
3. **Test Centratura Driver:** con `esp32s3_sh1106` i due occhi bianchi devono risultare centrati senza bande laterali di rumore (in caso di shift di 2px o rumore ai bordi, compila con `-e esp32s3_ssd1306`).
4. **Test Demo Automatica e Pulsante (`GPIO 47`):**
   - **Avvio:** cicla automaticamente tra le espressioni con blink e micro-movimenti dello sguardo.
   - **Pressione breve:** passa in modalità manuale e cicla l'espressione successiva.
   - **Pressione lunga (`>= 1,5 s`):** attiva/disattiva la Demo Automatica (`EVENT:AUTO_DEMO=ON/OFF`).
5. **Test Protocollo Seriale:** invia `PING`, `DIAG`, `STATUS`, `STATE:LOVE`, `STATE:CONFUSED`, `LOOK:5,-3`, `LOOK:99,0` (verifica `ERR:LOOK_RANGE`) e `BLINK`.

### C. Troubleshooting Rapido
- **Porta COM non visibile su Windows:** collega il cavo alla porta USB-CDC nativa (`USB` / `OTG`, non solo `UART` se presente) oppure premi `BOOT` + `RST` per entrare in bootloader.
- **OLED non rilevato (`OLED_ADDR=0x00` in `DIAG`):** controlla alimentazione `3V3` (non `5V` se il modulo non ha regolatore), inversione `SDA`/`SCL` (`GPIO 41`/`42`) e indirizzo I²C (`0x3C` vs `0x3D`).
- **Immagine spostata di 2 pixel o banda verticale disturbata:** il pannello monta controller SSD1306 invece di SH1106 (o viceversa); cambia ambiente PlatformIO tra `esp32s3_sh1106` e `esp32s3_ssd1306`.
- **Nessuna risposta ai comandi seriali:** verifica `115200` baud e terminatore di riga `\n` (`Newline` o `Both NL & CR`).
