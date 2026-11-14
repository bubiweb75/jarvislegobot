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

## 4. Procedura di Test (Software vs Hardware)

### A. Verifiche Software Completate in Sviluppo
- Compilazione pulita PlatformIO per **entrambi** gli ambienti (`esp32s3_sh1106` e `esp32s3_ssd1306`) con `-Wall -Wextra`.
- Architettura 100% non bloccante (`0` chiamate `delay()` nel `loop()`).
- Verifica pinout ESP32-S3 N16R8 (`GPIO 41/42/47` liberi e compatibili con Octal PSRAM).

### B. Procedura di Collaudo Fisico (Da Eseguire Quando Arrivano i Componenti)
1. **Test Rilevamento I²C:** collega OLED (`3V3`, `GND`, `SDA=41`, `SCL=42`) e apri il Monitor Seriale (`115200` baud). Verifica la stampa `I2C OLED detected at 0x3C` (o `0x3D`).
2. **Test Centratura Driver:** verifica che con `esp32s3_sh1106` i due occhi bianchi siano perfettamente centrati senza bande di rumore ai bordi (altrimenti passa a `esp32s3_ssd1306`).
3. **Test Demo Automatica:** all'avvio il firmware cicla ogni `5` secondi tra le espressioni `NEUTRAL`, `HAPPY`, `CURIOUS`, `LISTENING`, `THINKING`, `SPEAKING`, `SLEEPY`, con battito palpebre e movimenti organici dello sguardo.
4. **Test Pulsante (`GPIO 47`):**
   - **Pressione breve:** passa alla modalità manuale e cicla l'espressione successiva.
   - **Pressione lunga (`>= 1,5 s`):** attiva/disattiva la Demo Automatica (`EVENT:AUTO_DEMO=ON/OFF`).
5. **Test Protocollo Seriale / Raspberry Pi (`115200` baud, terminazione `\n`):**
   Invia da Serial Monitor (o futuro script Python su Raspberry Pi) i seguenti comandi e verifica la risposta:
   - `PING` → `PONG`
   - `STATUS` → `OK:STATE=...;AUTO=...;DRIVER=...`
   - `STATE:HAPPY`, `STATE:CURIOUS`, `STATE:SLEEPY`, `STATE:LISTENING`, `STATE:THINKING`, `STATE:SPEAKING`, `STATE:NEUTRAL`
   - `BLINK` → forza un battito di palpebre immediato
   - `LOOK:10,-5` → sposta lo sguardo per `2` secondi
   - `AUTO:ON` / `AUTO:OFF` → riattiva/disattiva il ciclo automatico
