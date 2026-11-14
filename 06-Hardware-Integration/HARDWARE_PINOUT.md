# HARDWARE_PINOUT — Verifica Pinout ESP32-S3-DevKitC-1 N16R8 (FASE 6)

> **Stato:** Preparazione documentale pre-hardware. I componenti elettronici non sono ancora arrivati; nessuna modifica al firmware o flash è stata eseguita.
> **Riferimenti incrociati:** [02_Tabella_Pinout_Definitiva.md](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/01-Hardware/02_Tabella_Pinout_Definitiva.md) | [pinout_config.h](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/04-Firmware/jarvis-desk-buddy/include/pinout_config.h)

---

## 1. Analisi della Scheda: ESP32-S3-DevKitC-1 (WROOM-1-N16R8)

- **MCU:** ESP32-S3 dual-core LX7 @ 240 MHz.
- **Memoria (`N16R8`):** 16 MB Flash QIO + **8 MB Octal PSRAM (OPI)** (come già configurato in [platformio.ini](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/04-Firmware/jarvis-desk-buddy/platformio.ini)).
- **Connettori USB sulla DevKitC-1:**
  - **Porta `USB` (Native USB-OTG / USB-Serial/JTAG):** collegata a **GPIO 19 (`D-`)** e **GPIO 20 (`D+`)**. Il firmware attuale usa `-DARDUINO_USB_MODE=1 -DARDUINO_USB_CDC_ON_BOOT=1`, quindi `Serial` passa da questa porta.
  - **Porta `UART` (USB-to-UART Bridge):** collegata a **GPIO 43 (`U0TXD`)** e **GPIO 44 (`U0RXD`)**. Utile per log di boot/emergenza, ma limitata dal baud rate del bridge.

### Verifica dei Pin Riservati / Vietati (N16R8)

| GPIO | Funzione Interna / Vincolo | Stato | Motivazione |
|---|---|---|---|
| **GPIO 0** | Strapping (`Boot Mode`) + tasto `BOOT` | **RISERVATO** | Se `LOW` al reset entra in Download Mode. Non collegare periferiche. |
| **GPIO 3** | Strapping (JTAG signal source) | **VIETATO** | Pin di strapping hardware. |
| **GPIO 19, 20** | USB Nativo (`D-`, `D+`) | **RISERVATO** | Usati dalla porta `USB` (CDC seriale + futuro audio USB). |
| **GPIO 26–32** | Flash SPI interna | **NON ESPOSTI / VIETATI** | Bus Flash interno. |
| **GPIO 35, 36, 37** | **Octal PSRAM (`R8`)** | **VIETATI** | Usati internamente dalla PSRAM OPI. Qualsiasi uso causa crash immediato. |
| **GPIO 38 / 48** | LED RGB NeoPixel onboard | **RISERVATO** | `GPIO 48` su DevKitC-1 v1.0, `GPIO 38` su v1.1. Non collegare carichi esterni. |
| **GPIO 43, 44** | `UART0` (`U0TXD`, `U0RXD`) | **RISERVATO** | Collegati al bridge USB-UART della porta `UART`. |
| **GPIO 45** | Strapping (`VDD_SPI` voltage) | **VIETATO** | Deve restare `LOW` al boot per Flash/PSRAM a 3,3 V. |
| **GPIO 46** | Strapping (`Boot Mode` / ROM log) | **VIETATO** | Pin di strapping hardware. |
| **RST / EN** | `CHIP_PU` (Reset / Enable) | **RISERVATO** | **Attenzione:** su molti DevKitC-1 si trova su `J1-3` vicino a `3V3`. **Mai collegare a `GND`.** |

---

## 2. Verifica dei GPIO già proposti dal Firmware Attuale

Nel file [pinout_config.h](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/04-Firmware/jarvis-desk-buddy/include/pinout_config.h) risultano già configurati:
- `OLED SDA = GPIO 41`
- `OLED SCL = GPIO 42`
- `Pulsante = GPIO 47`

**Esito della verifica documentale:**
1. **`GPIO 41` (SDA) e `GPIO 42` (SCL):**
   - **Idonei per I²C0 (400 kHz):** non sono strapping pin, non confliggono con Flash/PSRAM Octal (`35–37`), né con USB (`19–20`).
   - **Nota JTAG:** su ESP32-S3 i pin `GPIO 39–42` possono fungere da JTAG esterno (`MTDI/MTDO/MTCK/MTMS`) *solo* se abilitati via eFuse o GPIO matrix; nella configurazione standard USB-CDC (`ARDUINO_USB_MODE=1`) il debug JTAG esterno è disabilitato, quindi `GPIO 41/42` sono pienamente disponibili come I²C.
   - **Da verificare fisicamente:** presenza effettiva della serigrafia `41` e `42` sui connettori della scheda ricevuta (alcuni cloni non-standard hanno layout leggermente diverso).
2. **`GPIO 47` (Pulsante NO):**
   - **Idoneo come ingresso digitale:** non è strapping pin, supporta `INPUT_PULLUP` interno (~45 kΩ), attivo `LOW` verso `GND`. Nessun conflitto con I²C, I²S, USB o PSRAM.
   - **Nota elettrica:** appartiene al dominio `VDD_SPI` (3,3 V). Se il cavo del pulsante supera ~15 cm o è vicino a linee audio/alimentazione, valutare in collaudo un resistore di pull-up esterno da `10 kΩ` verso `3V3` solo se si osservano falsi trigger.

---

## 3. Tabella Pinout Completa Proposta (FASE 6)

| Periferica | Pin Modulo | GPIO ESP32-S3 | Bus / Tipo | Alimentazione / Riferimento | Note di Sicurezza |
|---|---|---|---|---|---|
| **OLED 1,3" I²C** (`SH1106`/`SSD1306`) | `VCC` | — | Power | `3V3` | **Verificare serigrafia** (`VCC`/`GND` possono essere invertiti su alcuni moduli). |
| **OLED 1,3" I²C** | `GND` | — | Ground | `GND` | Massa comune. |
| **OLED 1,3" I²C** | `SDA` | **GPIO 41** | I²C0 Data | Logica 3,3 V | Già attivo in `pinout_config.h` (`400 kHz`, indirizzo tipico `0x3C`). |
| **OLED 1,3" I²C** | `SCL` | **GPIO 42** | I²C0 Clock | Logica 3,3 V | Già attivo in `pinout_config.h`. |
| **Microfono INMP441** | `VDD` | — | Power | `3V3` | **SOLO 3,3 V** (5 V distruggono il MEMS). |
| **Microfono INMP441** | `GND` | — | Ground | `GND` | Massa comune. |
| **Microfono INMP441** | `L/R` | — | Config canale | `GND` | Collegare a `GND` per selezionare canale Left (mono). |
| **Microfono INMP441** | `WS` | **GPIO 4** | I²S0 RX (LRCLK) | Logica 3,3 V | Word Select 16 kHz. Nessun conflitto. |
| **Microfono INMP441** | `SCK` | **GPIO 5** | I²S0 RX (BCLK) | Logica 3,3 V | Bit Clock I²S RX. Nessun conflitto. |
| **Microfono INMP441** | `SD` | **GPIO 6** | I²S0 RX (DIN) | Logica 3,3 V | Dati audio digitali verso ESP32-S3. |
| **Amplificatore MAX98357A** | `VIN` | — | Power | `5V` (rail USB 5 V) | **MAI alimentare `VIN` dal pin `3V3`**: i picchi dello speaker (fino a ~600–800 mA) saturano il regolatore 3,3 V della DevKitC-1. |
| **Amplificatore MAX98357A** | `GND` | — | Ground | `GND` | Massa comune. |
| **Amplificatore MAX98357A** | `SD` | — | Enable / Mode | `3V3` (da verificare) | Su molti breakout `SD` a `3V3` abilita il canale Left+Right/2 o Left; verificare datasheet del modulo ricevuto. |
| **Amplificatore MAX98357A** | `GAIN` | — | Guadagno | Non collegato | Default `9 dB` (prudente per speaker 3 W); verificare su modulo fisico. |
| **Amplificatore MAX98357A** | `DIN` | **GPIO 7** | I²S1 TX (DOUT) | Logica 3,3 V | Dati audio dall'ESP32-S3 verso l'ampli. |
| **Amplificatore MAX98357A** | `BCLK` | **GPIO 15** | I²S1 TX (BCLK) | Logica 3,3 V | Bit Clock I²S TX. |
| **Amplificatore MAX98357A** | `LRC` | **GPIO 16** | I²S1 TX (LRCLK) | Logica 3,3 V | Left/Right Clock I²S TX. |
| **Speaker 4 Ω / 3 W** | `+` / `-` (JST-PH2.0) | **Nessuno** | Uscita BTL | Solo `MAX98357A OUT+ / OUT-` | **Uscita differenziale Classe-D:** mai collegare ai GPIO dell'ESP32-S3 e mai collegare `OUT-` a `GND`. |
| **Pulsante Momentaneo NO** | Terminale A | **GPIO 47** | Input digitale | `INPUT_PULLUP` (3,3 V) | Attivo `LOW`. Già configurato in `pinout_config.h`. |
| **Pulsante Momentaneo NO** | Terminale B | — | Ground | `GND` | Massa comune. |

---

## 4. Verifica Assenza Conflitti tra Periferiche

- **I²C0 (OLED):** `GPIO 41, 42` — bus dedicato.
- **I²S0 RX (INMP441):** `GPIO 4, 5, 6` — controller I²S #0 dedicato all'ingresso microfono.
- **I²S1 TX (MAX98357A):** `GPIO 7, 15, 16` — controller I²S #1 dedicato all'uscita speaker (clock completamente indipendenti da I²S0, evita vincoli di clock condiviso tra mic 16 kHz e speaker).
- **Pulsante:** `GPIO 47` — GPIO indipendente.
- **Pin liberi per future espansioni (es. Base Mobile B2):** `GPIO 1, 2, 8, 9, 10, 11, 12, 13, 14, 17, 18, 21`.
- **GPIO 39, 40:** lasciati liberi/scollegati.

---

## 5. Stato di Verifica: Documentale vs Collaudo Fisico

| Elemento | Verificato da Documentazione | Da Verificare Fisicamente all'Arrivo |
|---|---|---|
| Assegnazione `GPIO 41, 42, 47, 4, 5, 6, 7, 15, 16` | ✅ Nessun conflitto con strapping, PSRAM OPI o USB CDC | ⏳ Confermare posizione/serigrafia su scheda ricevuta |
| Controller OLED (`SH1106` vs `SSD1306`) e indirizzo (`0x3C`/`0x3D`) | ✅ Entrambi supportati in `platformio.ini` | ⏳ Verificare su PCB e tramite scan I²C (Test 1) |
| Ordine pin `VCC/GND` sull'OLED | ⚠️ Varia tra lotti/produttori | ⏳ Controllo visivo serigrafia prima di alimentare |
| Pin `SD` e `GAIN` del modulo `MAX98357A` | ⚠️ Dipende dalle resistenze montate sul breakout | ⏳ Controllare schema/serigrafia del modulo ricevuto |
