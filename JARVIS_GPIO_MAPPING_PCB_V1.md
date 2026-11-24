# JARVIS LEGO BOT — Mappatura Tecnica Completa GPIO e Specifica per Carrier Board PCB (V1)

- **Documento:** `JARVIS_GPIO_MAPPING_PCB_V1.md`
- **Target MCU:** Espressif **ESP32-S3-DevKitC-1 N16R8** (Modulo `ESP32-S3-WROOM-1-N16R8`: 16 MB Flash QIO + 8 MB Octal PSRAM OPI)
- **Scopo:** Documentazione tecnica di riferimento per lo sbroglio e la progettazione schematica in **KiCad** della **Carrier Board PCB personalizzata** di JARVIS LEGO BOT (Modulo A — Corpo Companion `10×10 stud`, con predisposizione per Modulo B2 — Base Mobile 2WD).
- **Vincolo Operativo:** Documento di sola analisi e specifica hardware. Nessun file del firmware stabile, configurazione o cablaggio è stato alterato.

---

## Legenda dello Stato di Verifica

Per garantire la massima tracciabilità ingegneristica in fase di cattura schematica KiCad, ogni informazione riportata in questo documento è classificata con uno dei seguenti tag:

- **`[VERIFICATO DAL CODICE]`**: Assegnazione, protocollo, pull-up o direzione riscontrati direttamente nei file sorgente del repository firmware (`04-Firmware/`).
- **`[DERIVATO DA DOC HARDWARE]`**: Dato ricavato dai datasheet ufficiali Espressif (`ESP32-S3`, `DevKitC-1 v1.1`) o dalla documentazione progettuale interna del repository (`06-Hardware-Integration/`, `03-Mechanical-Design/`).
- **`[DA VERIFICARE FISICAMENTE]`**: Caratteristica dipendente dal lotto/clone commerciale dei moduli breakout acquistati (ordine pin header, serigrafia, presenza LDO onboard, resistenze di pull-up pre-saldate, ingombri meccanici col calibro) da misurare a banco prima della produzione/saldatura del PCB.

---

## 1. Sintesi Architetturale del Firmware nel Repository

Nel repository coesistono due rami principali di firmware per l'ESP32-S3 (`[VERIFICATO DAL CODICE]`):

1. **Firmware Companion Display & Touch (`04-Firmware/jarvis-desk-buddy/` e `04-Firmware/wokwi-touch/`):**
   - Gestisce il motore grafico procedurale **Eyes 3.0** (14 espressioni su OLED I²C `GPIO 41/42`), il pulsante fisico (`GPIO 47`), il protocollo comandi su **USB-CDC nativo** (`GPIO 19/20`), il gestore touch capacitivo `TTP223B` su `GPIO 1` (compilato quando il flag `-DJARVIS_ENABLE_TOUCH=1` è attivo) e lo stub per i sensori ambientali (`sensor_stub.h`).
2. **Firmware Audio Full-Duplex FreeRTOS & Wi-Fi Voice Client (`04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` e `jarvis_duplex_rtos_hw_test/`):**
   - Integra su **Core 0** i task FreeRTOS per l'acquisizione microfono **I²S0 RX** (`INMP441` su `GPIO 4, 5, 6`) e la riproduzione audio **I²S1 TX** (`MAX98357A` su `GPIO 7, 15, 16`), oltre a OLED (`GPIO 41/42`), pulsante Push-to-Talk (`GPIO 47`) e streaming WebSocket Wi-Fi su **Core 1**.

La **Carrier Board PCB** deve supportare l'**unione completa** di queste periferiche, garantendo la totale compatibilità elettrica e meccanica con entrambi i firmware senza richiedere alcuna modifica ai pin definiti nel codice.

---

## 2. Tabella Completa di Analisi GPIO e Pin Header (ESP32-S3-DevKitC-1 N16R8)

La scheda **ESP32-S3-DevKitC-1** dispone di due file da 22 pin passo `2,54 mm` (`J1` a sinistra, `J3` a destra, guardando la scheda dal lato componenti con i connettori USB-C rivolti verso il basso e l'antenna PCB verso l'alto).
*(Nota: verificare sempre la serigrafia della propria DevKitC-1 fisica, poiché tra cloni a 44 pin e 38/40 pin la posizione di alcuni pin di massa può variare — `[DA VERIFICARE FISICAMENTE]`).*

### 2.1 Tabella Master di Tutti i GPIO dell'ESP32-S3 (GPIO 0 – GPIO 48)

| GPIO | Pin Header DevKitC-1 (44-pin) | Funzione Assegnata | Componente Collegato | Direzione | Protocollo / Segnale | Pull-up / Pull-down | Stato nel Progetto | Limitazioni Hardware ESP32-S3 (N16R8) | Riferimento File Sorgente / Doc | Stato di Verifica |
| :--- | :---: | :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **GPIO 0** | `J3-14` | Boot Mode Strapping / Tasto `BOOT` onboard | Pulsante `BOOT` su DevKitC-1 | INPUT | Strapping / Digital | Pull-up interno di default | **RISERVATO (Boot)** | **Strapping Pin**: se `LOW` al reset forza il chip in *Download Boot*. Non collegare carichi esterni che lo tirino basso all'avvio. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L43) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 1** | `J3-2` *(o J1/J3 var.)* | `kTouchTtp223` (Ingresso Touch Capacitivo) | Sensore Tattile **TTP223B** (pin `SIG`/`OUT`) | INPUT | Digital GPIO (`Active HIGH`) | **NESSUNO** (`pinMode(1, INPUT)` senza pull-up) | **CONFIGURATO (Attivo con `JARVIS_ENABLE_TOUCH=1`)** | `RTC_GPIO1`, `ADC1_CH0`, `TOUCH1`. Pin pulito, nessun vincolo di boot. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L24), [state_machine.cpp](04-Firmware/jarvis-desk-buddy/src/state_machine.cpp#L56) | `[VERIFICATO DAL CODICE]` |
| **GPIO 2** | `J3-3` *(o var.)* | Libero (Espansione) | — | — | GPIO / ADC / RTC | — | **LIBERO** | `RTC_GPIO2`, `ADC1_CH1`, `TOUCH2`. Pin completamente libero e sicuro. | [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L84) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 3** | `J1-13` | JTAG Signal Source Strapping | — | — | Strapping | Pull-down interno debole al reset | **RISERVATO / SCONSIGLIATO** | **Strapping Pin**: seleziona la sorgente JTAG al reset insieme a `eFuse`. Evitare su Carrier Board. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L43) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 4** | `J1-4` | `kI2sWsPin` (`I2S_MIC_WS` / `LRCLK`) | Microfono **INMP441** (pin `WS`) | OUTPUT | **I²S0 RX** (Word Select 16 kHz) | Nessuno (pilotato push-pull) | **UTILIZZATO (Attivo nel ramo Audio/Voice)** | `RTC_GPIO4`, `ADC1_CH3`, `TOUCH4`. Nessun vincolo di boot. | [audio_capture.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_capture.h#L73), [audio_capture.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_capture.cpp#L20) | `[VERIFICATO DAL CODICE]` |
| **GPIO 5** | `J1-5` | `kI2sSckPin` (`I2S_MIC_SCK` / `BCLK`) | Microfono **INMP441** (pin `SCK`) | OUTPUT | **I²S0 RX** (Bit Clock) | Nessuno (pilotato push-pull) | **UTILIZZATO (Attivo nel ramo Audio/Voice)** | `RTC_GPIO5`, `ADC1_CH4`, `TOUCH5`. Nessun vincolo di boot. | [audio_capture.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_capture.h#L74), [audio_capture.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_capture.cpp#L20) | `[VERIFICATO DAL CODICE]` |
| **GPIO 6** | `J1-6` | `kI2sSdPin` (`I2S_MIC_SD` / `DIN`) | Microfono **INMP441** (pin `SD`) | INPUT | **I²S0 RX** (Serial Data 24-bit in slot 32-bit) | Nessuno (consigliato `100 kΩ` pull-down su PCB per evitare floating a mic spento) | **UTILIZZATO (Attivo nel ramo Audio/Voice)** | `RTC_GPIO6`, `ADC1_CH5`, `TOUCH6`. Nessun vincolo di boot. | [audio_capture.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_capture.h#L75), [audio_capture.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_capture.cpp#L20) | `[VERIFICATO DAL CODICE]` |
| **GPIO 7** | `J1-7` | `kI2sDinPin` (`I2S_SPK_DIN` / `DOUT`) | Amplificatore **MAX98357A** (pin `DIN`) | OUTPUT | **I²S1 TX** (Serial Data 16-bit stereo L=R) | Nessuno (pilotato push-pull) | **UTILIZZATO (Attivo nel ramo Audio/Voice)** | `RTC_GPIO7`, `ADC1_CH6`, `TOUCH7`. Nessun vincolo di boot. | [audio_playback.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_playback.h#L45), [audio_playback.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_playback.cpp#L19) | `[VERIFICATO DAL CODICE]` |
| **GPIO 8** | `J1-10` | Predisposto `I2C_EXT_SDA` (JST-XH Pin 5 verso Base B2) | Connettore **JST-XH 6-pin** (Pin 5) / Ex-Touch in doc Fase 8 | Bidirezionale | I²C1 SDA (futuro) / GPIO | Pull-up esterno `4,7 kΩ` verso `3V3` solo se usato come `I2C_EXT` | **IN CONFLITTO DOCUMENTALE (Risolto in codice spostando Touch su GPIO 1)** | `RTC_GPIO8`, `ADC1_CH7`, `TOUCH8`, `SUBSPICS1`. In `FASE_8` era indicato per `TTP223`, ma in `pinout_config.h` il Touch è stato spostato a `GPIO 1` per liberare `GPIO 8` per B2. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L22-L24), [04_Pinout_Connettore_JST-XH.md](03-Mechanical-Design/05-Mobile-Electronics/04_Pinout_Connettore_JST-XH.md#L16) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 9** | `J1-15` | `kTofXshut` (Opz. `VL53L0X XSHUT`) **OPPURE** `I2C_EXT_SCL` (JST-XH Pin 6) | **VL53L0X** (`XSHUT`) o Connettore **JST-XH 6-pin** (Pin 6) | OUTPUT | Digital GPIO / I²C1 SCL (futuro) | Pull-up `10 kΩ` consigliato su `XSHUT` (o `4,7 kΩ` se `I2C_EXT_SCL`) | **CONFIGURATO MA NON ATTIVO / IN CONFLITTO** | `RTC_GPIO9`, `ADC1_CH8`, `TOUCH9`. **Conflitto**: definito in `pinout_config.h` come `kTofXshut = 9`, ma assegnato in `04_Pinout_Connettore_JST-XH.md` al Pin 6 (`I2C_SCL` verso B2). | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L34), [04_Pinout_Connettore_JST-XH.md](03-Mechanical-Design/05-Mobile-Electronics/04_Pinout_Connettore_JST-XH.md#L17) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 10** | `J1-16` | `kImuInt` (Opz. Interrupt `MPU6050`) | **MPU6050** (pin `INT`) | INPUT | Digital Interrupt | Configurabile (push-pull o open-drain da registro MPU6050) | **CONFIGURATO MA NON ATTIVO (Costante `kImuInt`)** | `RTC_GPIO10`, `ADC1_CH9`, `TOUCH10`, `FSPICS0`. Nessun vincolo di boot. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L35) | `[VERIFICATO DAL CODICE]` |
| **GPIO 11** | `J1-17` | Libero (Espansione) | — | — | GPIO / SPI / Touch / ADC2 | — | **LIBERO** | `RTC_GPIO11`, `ADC2_CH0`, `TOUCH11`, `FSPID`. Nota: `ADC2` non è usabile insieme al Wi-Fi, ma come GPIO digitale/PWM/I²C/UART funziona senza limiti. | [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L84) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 12** | `J1-18` | Libero (Espansione) | — | — | GPIO / SPI / Touch / ADC2 | — | **LIBERO** | `RTC_GPIO12`, `ADC2_CH1`, `TOUCH12`, `FSPICLK`. Come GPIO digitale è completamente libero. | [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L84) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 13** | `J1-19` | Libero (Espansione) | — | — | GPIO / SPI / Touch / ADC2 | — | **LIBERO** | `RTC_GPIO13`, `ADC2_CH2`, `TOUCH13`, `FSPIQ`. Come GPIO digitale è completamente libero. | [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L84) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 14** | `J1-20` | Libero (Espansione) | — | — | GPIO / SPI / Touch / ADC2 | — | **LIBERO** | `RTC_GPIO14`, `ADC2_CH3`, `TOUCH14`, `FSPIWP`. Ottimo candidato per `XSHUT`, cliff sensor o PWM. | [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L84) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 15** | `J1-8` | `kI2sBclkPin` (`I2S_SPK_BCLK`) | Amplificatore **MAX98357A** (pin `BCLK`) | OUTPUT | **I²S1 TX** (Bit Clock) | Nessuno (pilotato push-pull) | **UTILIZZATO (Attivo nel ramo Audio/Voice)** | `RTC_GPIO15`, `ADC2_CH4`, `XTAL_32K_P`. Nessun conflitto poiché non c'è quarzo 32 kHz esterno. | [audio_playback.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_playback.h#L43), [audio_playback.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_playback.cpp#L19) | `[VERIFICATO DAL CODICE]` |
| **GPIO 16** | `J1-9` | `kI2sLrcPin` (`I2S_SPK_LRC` / `LRCLK`) | Amplificatore **MAX98357A** (pin `LRC`) | OUTPUT | **I²S1 TX** (Word Select 16 kHz) | Nessuno (pilotato push-pull) | **UTILIZZATO (Attivo nel ramo Audio/Voice)** | `RTC_GPIO16`, `ADC2_CH5`, `XTAL_32K_N`. Nessun conflitto. | [audio_playback.h](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_playback.h#L44), [audio_playback.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_playback.cpp#L19) | `[VERIFICATO DAL CODICE]` |
| **GPIO 17** | `J1-11` | Predisposto `UART_TX_A` (`UART1_TX` verso Base B2) | Connettore **JST-XH 6-pin** (Pin 3) | OUTPUT | UART1 TX (3,3 V LVCMOS) | Resistore serie `220–330 Ω` consigliato su PCB | **LIBERO NEL FIRMWARE / PREDISPOSTO PER B2** | `RTC_GPIO17`, `ADC2_CH6`, `U1TXD` nativo. Ideale per UART verso B2 o driver motori. | [04_Pinout_Connettore_JST-XH.md](03-Mechanical-Design/05-Mobile-Electronics/04_Pinout_Connettore_JST-XH.md#L14) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 18** | `J1-12` | Predisposto `UART_RX_A` (`UART1_RX` da Base B2) | Connettore **JST-XH 6-pin** (Pin 4) | INPUT | UART1 RX (3,3 V LVCMOS) | Resistore serie `220–330 Ω` + pull-up debole | **LIBERO NEL FIRMWARE / PREDISPOSTO PER B2** | `RTC_GPIO18`, `ADC2_CH7`, `U1RXD` nativo. Ideale per UART da B2 o driver motori. | [04_Pinout_Connettore_JST-XH.md](03-Mechanical-Design/05-Mobile-Electronics/04_Pinout_Connettore_JST-XH.md#L15) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 19** | `J3-20` | `USB_D-` (Porta USB Nativa) | Connettore micro/USB-C `USB` onboard | Bidirezionale | **USB 2.0 Full-Speed (`D-`)** | Gestito dal PHY USB interno | **RISERVATO / UTILIZZATO (`Serial` USB-CDC)** | Dedicato a USB-OTG / USB-Serial-JTAG (`-DARDUINO_USB_MODE=1 -DARDUINO_USB_CDC_ON_BOOT=1`). **Non collegare nulla sui pin header `19/20` della PCB.** | [platformio.ini](04-Firmware/jarvis-desk-buddy/platformio.ini#L29-L30), [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L44) | `[VERIFICATO DAL CODICE]` |
| **GPIO 20** | `J3-19` | `USB_D+` (Porta USB Nativa) | Connettore micro/USB-C `USB` onboard | Bidirezionale | **USB 2.0 Full-Speed (`D+`)** | Pull-up interno PHY USB | **RISERVATO / UTILIZZATO (`Serial` USB-CDC)** | Dedicato a USB-OTG / USB-Serial-JTAG. **Non collegare piste o carichi sui pin header `19/20` per non degradare l'impedenza differenziale 90 Ω.** | [platformio.ini](04-Firmware/jarvis-desk-buddy/platformio.ini#L29-L30), [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L44) | `[VERIFICATO DAL CODICE]` |
| **GPIO 21** | `J3-18` | Libero (Espansione) | — | — | GPIO digitale / PWM / I²C | — | **LIBERO** | `RTC_GPIO21`. GPIO digitale puro completamente libero e privo di funzioni di strapping. | [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L84) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 22–25** | Non esistenti | — | — | — | — | — | **NON ESISTENTI** | Questi numeri di GPIO non esistono nell'architettura siliconica dell'ESP32-S3. | Datasheet ESP32-S3 | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 26–32** | Non esposti | Bus SPI0/1 Flash & PSRAM interno | Chip Flash QIO 16 MB + PSRAM 8 MB interni al modulo WROOM-1 | Bidirezionale | Quad/Octal SPI | Interni al modulo | **RISERVATI / NON ESPOSTI** | Usati internamente dal modulo `ESP32-S3-WROOM-1` per Flash e PSRAM. Non presenti sugli header. | [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L23) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 33, 34** | Non esposti su N16R8 | Bus Octal SPI PSRAM (`SPIIO4`, `SPIIO5`) | Octal PSRAM 8 MB interna (`R8`) | Bidirezionale | Octal SPI (OPI) | Interni al modulo | **VIETATI / NON ESPOSTI** | Nei moduli `N16R8` (`ESP32-S3R8`) i GPIO `33–37` sono cablati internamente alla PSRAM Octal. | Datasheet ESP32-S3-WROOM-1 | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 35** | `J3-13` | Bus Octal SPI PSRAM (`SPIIO6`) | Octal PSRAM 8 MB interna (`R8`) | Bidirezionale | Octal SPI (OPI) | Interno al modulo | **VIETATO (Crash Immediato)** | **CRITICITÀ MASSIMA PCB**: Anche se il pin `35` è fisicamente esposto sull'header `J3-13` della DevKitC-1, è usato dalla PSRAM OPI (`board_build.psram_type = opi`). **Lasciare la piazzola KiCad `No-Connect (NC)`**. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L42), [platformio.ini](04-Firmware/jarvis-desk-buddy/platformio.ini#L20) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 36** | `J3-12` | Bus Octal SPI PSRAM (`SPIIO7`) | Octal PSRAM 8 MB interna (`R8`) | Bidirezionale | Octal SPI (OPI) | Interno al modulo | **VIETATO (Crash Immediato)** | **CRITICITÀ MASSIMA PCB**: Usato dalla PSRAM OPI. **Lasciare la piazzola KiCad `No-Connect (NC)`**. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L42) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 37** | `J3-11` | Bus Octal SPI PSRAM (`SPIDQS`) | Octal PSRAM 8 MB interna (`R8`) | Bidirezionale | Octal SPI (OPI) | Interno al modulo | **VIETATO (Crash Immediato)** | **CRITICITÀ MASSIMA PCB**: Usato dalla PSRAM OPI. **Lasciare la piazzola KiCad `No-Connect (NC)`**. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L42) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 38** | `J3-10` | LED RGB NeoPixel onboard (su DevKitC-1 v1.1) | `WS2812` RGB LED onboard | OUTPUT | Single-wire NZR | — | **RISERVATO (LED Onboard v1.1)** | Su DevKitC-1 v1.1 pilota il LED RGB onboard (tramite jumper `RGB`). Non usare per carichi critici. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L46) | `[VERIFICATO DAL CODICE]` `[DA VERIFICARE FISICAMENTE]` |
| **GPIO 39** | `J3-9` | Libero (Ex-tasto volume disabilitato) | — | — | GPIO / JTAG `MTCK` | — | **LIBERO** | Funzione JTAG opzionale (`MTCK`), ma con `ARDUINO_USB_MODE=1` il JTAG passa su USB o è disabilitato. Utilizzabile come GPIO digitale standard. | [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L43) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 40** | `J3-8` | Libero (Ex-tasto volume disabilitato) | — | — | GPIO / JTAG `MTDO` | — | **LIBERO** | Funzione JTAG opzionale (`MTDO`). Utilizzabile come GPIO digitale standard. | [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L43) | `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 41** | `J3-7` | `kOledSda` (`I2C0_SDA`) | **OLED SH1106** (`0x3C`) + futuri **VL53L0X** (`0x29`), **MPU6050** (`0x68`), **BH1750** (`0x23`) | Bidirezionale (Open-Drain) | **I²C0 Data (`400 kHz`)** | Pull-up interni deboli + **pull-up esterni sui moduli (`2,2–4,7 kΩ` eq.)** | **UTILIZZATO (Attivo in tutti i firmware)** | Funzione JTAG opzionale (`MTDI`), disabilitata in configurazione standard Arduino USB. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L13), [display_driver.cpp](04-Firmware/jarvis-desk-buddy/src/display_driver.cpp#L21) | `[VERIFICATO DAL CODICE]` |
| **GPIO 42** | `J3-6` | `kOledScl` (`I2C0_SCL`) | **OLED SH1106** (`0x3C`) + futuri **VL53L0X**, **MPU6050**, **BH1750** | OUTPUT / Bidir. (Open-Drain) | **I²C0 Clock (`400 kHz`)** | Pull-up interni deboli + **pull-up esterni sui moduli (`2,2–4,7 kΩ` eq.)** | **UTILIZZATO (Attivo in tutti i firmware)** | Funzione JTAG opzionale (`MTMS`), disabilitata in configurazione standard Arduino USB. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L14), [display_driver.cpp](04-Firmware/jarvis-desk-buddy/src/display_driver.cpp#L21) | `[VERIFICATO DAL CODICE]` |
| **GPIO 43** | `J3-5` *(o J3-2)* | `U0TXD` (Console UART0 Boot/Debug) | Bridge USB-to-UART onboard (Porta `UART` / `COM`) | OUTPUT | **UART0 TX** | Pull-up interno | **RISERVATO (UART0 / Programmazione)** | Emette sempre i log del bootloader ROM all'accensione ed è collegato al chip bridge USB-UART della DevKitC-1. Non collegare periferiche esterne. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L45) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 44** | `J3-4` *(o J3-3)* | `U0RXD` (Console UART0 Boot/Debug) | Bridge USB-to-UART onboard (Porta `UART` / `COM`) | INPUT | **UART0 RX** | Pull-up interno | **RISERVATO (UART0 / Programmazione)** | Collegato all'uscita TX del chip bridge USB-UART onboard. Non collegare altre uscite per evitare contese di livello. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L45) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 45** | `J3-15` | `VDD_SPI` Voltage Strapping | — | — | Strapping | Pull-down interno debole | **VIETATO (Strapping Critico N16R8)** | **CRITICITÀ MASSIMA**: seleziona la tensione `VDD_SPI` (`0 = 3,3 V`, `1 = 1,8 V`). Sul modulo `N16R8` la PSRAM/Flash richiede `3,3 V`: se `GPIO 45` è `HIGH` al boot, la scheda **non si avvia**. Lasciare `NC`. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L43), [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L27) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 46** | `J1-14` | Boot Mode & ROM Log Strapping | — | — | Strapping | Pull-down interno debole | **VIETATO (Strapping Boot)** | **Strapping Pin**: deve essere `LOW` per consentire il Download Boot con `GPIO 0 = LOW`. Non collegare pull-up esterni. Lasciare `NC`. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L43), [HARDWARE_PINOUT.md](06-Hardware-Integration/HARDWARE_PINOUT.md#L28) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **GPIO 47** | `J3-17` | `kButtonActivate` (Pulsante Utente / PTT) | **Pulsante Fisico NO** (verso `GND`) | INPUT | Digital GPIO (`Active LOW`) | **`INPUT_PULLUP` interno attivo** (~45 kΩ); opz. `10 kΩ` esterno + `100 nF` su PCB | **UTILIZZATO (Attivo in tutti i firmware)** | Appartiene al dominio `VDD3P3_CPU`. Nessun vincolo di boot o PSRAM. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L19), [state_machine.cpp](04-Firmware/jarvis-desk-buddy/src/state_machine.cpp#L50), [button_controller.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/button_controller.cpp#L9) | `[VERIFICATO DAL CODICE]` |
| **GPIO 48** | `J3-16` | LED RGB NeoPixel onboard (su DevKitC-1 v1.0) | `WS2812` RGB LED onboard (v1.0) | OUTPUT | Single-wire NZR | — | **RISERVATO (LED Onboard v1.0)** | Su DevKitC-1 v1.0 pilota il LED NeoPixel onboard (`GPIO 38` su v1.1). Lasciare `NC` sulla Carrier Board per compatibilità v1.0/v1.1. | [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L46) | `[VERIFICATO DAL CODICE]` `[DA VERIFICARE FISICAMENTE]` |

### 2.2 Pin di Alimentazione e Controllo sull'Header DevKitC-1

| Pin Header | Nome Segnale | Funzione | Note Critiche per Carrier Board PCB | Stato di Verifica |
| :---: | :--- | :--- | :--- | :--- |
| `J1-1`, `J1-2` | **`3V3`** | Uscita Regolatore LDO `3,3 V` onboard (`SGM2212-3.3`, max `800 mA` totali inclusi MCU+Wi-Fi) | Alimenta il rail logico `+3V3` della Carrier Board (`OLED`, `INMP441`, `TTP223B`, `VL53L0X`, `MPU6050`, `BH1750`, pin `SD` del `MAX98357A`). **MAI collegare `VIN` del MAX98357A o i motori a `3V3`.** | `[DERIVATO DA DOC HARDWARE]` |
| `J1-3` | **`RST` (`EN` / `CHIP_PU`)** | Ingresso di Reset / Abilitazione Chip (Attivo `LOW`) | **ATTENZIONE CRITICA**: Si trova subito sotto i due pin `3V3`. Molti utenti lo scambiano per `GND`. **NON collegare MAI a `GND`** (blocca l'ESP32-S3 in reset permanente). Lasciare `NC` o portare solo a un eventuale pad di test/reset esterno. | `[DERIVATO DA DOC HARDWARE]` |
| `J1-21` | **`5V` (`VCC_5V`)** | Rail `5 V` a valle dei diodi Schottky USB `D1`/`D7` (`1N5819HW`) | Usato come nodo `+5V` per alimentare `VIN` del `MAX98357A` (in modalità USB PC) oppure come ingresso `+5V_A` regolato (`4,90–5,10 V`) proveniente da alimentatore esterno / Base Mobile B2. | `[DERIVATO DA DOC HARDWARE]` |
| `J1-22`, `J3-1`, `J3-21`, `J3-22` | **`GND`** | Massa comune di riferimento (`0 V`) | Collegare **tutti** i pin `GND` della DevKitC-1 direttamente al piano di massa (`GND plane`) continuo della Carrier Board PCB. | `[DERIVATO DA DOC HARDWARE]` `[DA VERIFICARE FISICAMENTE]` |

---

## 3. Classificazione Chiara dei GPIO per la Progettazione PCB

Per evitare qualsiasi errore durante il disegno dello schematico KiCad, i GPIO sono suddivisi nelle 4 categorie richieste:

### 3.1 GPIO Effettivamente Utilizzati e Attivi nel Firmware
1. **`GPIO 41` (`I2C0_SDA`)** e **`GPIO 42` (`I2C0_SCL`)**: Attivi a `400 kHz` in **tutti** i firmware (`jarvis-desk-buddy` e `jarvis_wifi_voice_client`) per il pilotaggio dell'OLED `SH1106`/`SSD1306` (`0x3C` o `0x3D`) (`[VERIFICATO DAL CODICE]`).
2. **`GPIO 47` (`kButtonActivate`)**: Attivo in **tutti** i firmware come ingresso digitale con `INPUT_PULLUP` interno (`Active LOW` verso `GND`) per il pulsante fisico / Push-to-Talk (`[VERIFICATO DAL CODICE]`).
3. **`GPIO 4` (`WS`)**, **`GPIO 5` (`SCK`)**, **`GPIO 6` (`SD`)**: Attivi nel firmware vocale/duplex (`audio_capture.h/.cpp`) sul controller **I²S0 RX** (`16 kHz`, 32-bit slot, Mono Left) per il microfono `INMP441` (`[VERIFICATO DAL CODICE]`).
4. **`GPIO 7` (`DIN`)**, **`GPIO 15` (`BCLK`)**, **`GPIO 16` (`LRC`)**: Attivi nel firmware vocale/duplex (`audio_playback.h/.cpp`) sul controller **I²S1 TX** (`16 kHz`, 16-bit Stereo `L=R`) per l'amplificatore `MAX98357A` (`[VERIFICATO DAL CODICE]`).
5. **`GPIO 19` (`USB_D-`)** e **`GPIO 20` (`USB_D+`)**: Attivi tramite hardware USB-CDC nativo (`Serial` a 12 Mbps) per il collegamento al PC Windows 11. **Non devono essere cablati sulla Carrier Board** poiché passano direttamente dal connettore USB-C `USB` onboard della DevKitC-1 (`[VERIFICATO DAL CODICE]`).

### 3.2 GPIO Configurati nel Codice ma Non Attivi di Default (o Condizionali)
1. **`GPIO 1` (`kTouchTtp223`)**: Definito in `pinout_config.h` e implementato in `state_machine.cpp` + `touch_manager.cpp` (`pinMode(1, INPUT)`, Active `HIGH`). Nel progetto `04-Firmware/wokwi-touch/` è compilato e attivo (`-DJARVIS_ENABLE_TOUCH=1`), mentre in `04-Firmware/jarvis-desk-buddy/platformio.ini` il flag `-DJARVIS_ENABLE_TOUCH=1` non è ancora abilitato di default nei build flags (`[VERIFICATO DAL CODICE]`). Sulla PCB **va cablato definitivamente** al connettore del sensore `TTP223B`.
2. **`GPIO 9` (`kTofXshut`)**: Definito come `constexpr uint8_t kTofXshut = 9;` in `pinout_config.h`, ma non ancora invocato da alcun driver (`sensor_stub.h` è uno stub passivo). Inoltre è in conflitto documentale con `I2C_EXT_SCL` della Base Mobile B2 (`[VERIFICATO DAL CODICE]`).
3. **`GPIO 10` (`kImuInt`)**: Definito come `constexpr uint8_t kImuInt = 10;` in `pinout_config.h` per l'interrupt opzionale dell'`MPU6050`, ma non ancora invocato nel codice attivo (`[VERIFICATO DAL CODICE]`).

### 3.3 GPIO Disponibili, Puliti e Accessibili sui Pin Header
I seguenti GPIO sono fisicamente esposti sugli header della DevKitC-1, non sono usati dal firmware attuale e non sono pin di strapping o PSRAM (`[DERIVATO DA DOC HARDWARE]`):
- **`GPIO 2`**: Libero (`ADC1_CH1`, `RTC_GPIO2`, `TOUCH2`).
- **`GPIO 8`**: Libero nel codice attuale (in precedenza ipotizzato per il Touch, poi liberato spostando il Touch su `GPIO 1`; candidato per `I2C_EXT_SDA` verso Base B2).
- **`GPIO 11, 12, 13, 14`**: Liberi (GPIO digitali, PWM, SPI, Touch capacitivo, `ADC2`).
- **`GPIO 17, 18`**: Liberi nel codice attuale (`U1TXD` / `U1RXD` hardware nativi; già documentati come `UART_TX_A` / `UART_RX_A` sul connettore JST-XH 6-pin verso la Base Mobile B2).
- **`GPIO 21`**: Libero (GPIO digitale puro / `RTC_GPIO21`).
- **`GPIO 39, 40`**: Liberi (ex-tasti volume disabilitati; funzioni JTAG `MTCK`/`MTDO` non usate).

### 3.4 GPIO Riservati, Vietati o Sconsigliati (Da Lasciare `NC` in KiCad)
- **`GPIO 35, 36, 37` (VIETATI ASSOLUTI)**: Riservati al bus interno **Octal PSRAM (`R8`)**. In KiCad marcare i pin `J3-13`, `J3-12`, `J3-11` con il simbolo **`No-Connect (X)`** (`[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]`).
- **`GPIO 26–34` (NON ESPOSTI / VIETATI)**: Riservati internamente a Flash QIO e PSRAM OPI.
- **`GPIO 0, 3, 45, 46` (STRAPPING PINS — VIETATI)**: `GPIO 45` altera la tensione `VDD_SPI` (3,3 V vs 1,8 V) bloccando il boot della PSRAM `R8`; `GPIO 0` e `GPIO 46` controllano il Download Boot; `GPIO 3` configura il JTAG. Lasciare **`No-Connect (X)`** sulla Carrier Board.
- **`GPIO 19, 20` (RISERVATI USB NATIVA)**: Collegati alla porta `USB` onboard. Lasciare **`No-Connect (X)`** sull'header della Carrier Board per evitare stub capacitivi sulle linee differenziali USB.
- **`GPIO 43, 44` (RISERVATI UART0)**: Collegati al convertitore USB-UART onboard. Lasciare **`No-Connect (X)`** (o portare solo a test point di debug `TP_TX0`/`TP_RX0`).
- **`GPIO 38, 48` (RISERVATI LED RGB ONBOARD)**: Collegati al NeoPixel onboard (a seconda della rev. v1.0 o v1.1). Lasciare **`No-Connect (X)`**.

---

## 4. Verifica Dettagliata dei Componenti Acquisti e Previsti

### 4.1 ESP32-S3 DevKitC-1 N16R8
- **Configurazione verificata in `platformio.ini`**: `board = esp32-s3-devkitc-1`, `board_build.arduino.memory_type = qio_opi`, `flash_mode = qio`, `psram_type = opi`, `flash_size = 16MB`, `-DBOARD_HAS_PSRAM`, `-DARDUINO_USB_MODE=1`, `-DARDUINO_USB_CDC_ON_BOOT=1` (`[VERIFICATO DAL CODICE]`).
- **Collaudo fisico**: Scheda già verificata tramite `04-Firmware/esp32s3-diag-test` (`COM4`, 16 MB Flash, 8 MB PSRAM OPI funzionanti) (`[DERIVATO DA DOC HARDWARE]`).
- **Verifica fisica pre-PCB**: Misurare con calibro il passo tra le due file di pin `J1` e `J3` (tipicamente **`22,86 mm` = `900 mil`** sulle DevKitC-1 standard Espressif, ma alcuni cloni cinesi usano `25,40 mm` = `1000 mil`) e il numero esatto di pin per fila (`22×2 = 44 pin`) (`[DA VERIFICARE FISICAMENTE]`).

### 4.2 Microfono Digitale MEMS I²S INMP441
- **Interfaccia**: Controller **I²S0 RX** dedicato (`GPIO 4 = WS`, `GPIO 5 = SCK`, `GPIO 6 = SD`), `16 kHz`, 32-bit slot, Mono Left (`[VERIFICATO DAL CODICE]`).
- **Configurazione hardware pin**:
  - `VDD` → **`3V3`** (**Tassativo**: tensione max `3,6 V`; `5 V` distruggono il microfono).
  - `GND` → **`GND`**.
  - `L/R` → **`GND`** (**Obbligatorio**: seleziona il canale **Left**, coerente con `I2S_STD_SLOT_LEFT` nel firmware; non lasciare mai flottante).
- **Requisito KiCad**: Prevedere sulla Carrier Board un condensatore ceramico di disaccoppiamento da **`100 nF`** vicino al connettore del microfono e un resistore di pull-down da **`100 kΩ`** tra `SD` (`GPIO 6`) e `GND` per azzerare la linea dati in tri-state (`[DERIVATO DA DOC HARDWARE]`).

### 4.3 Amplificatore Audio I²S Classe-D MAX98357A + Speaker 4 Ω / 3 W
- **Interfaccia**: Controller **I²S1 TX** dedicato (`GPIO 7 = DIN`, `GPIO 15 = BCLK`, `GPIO 16 = LRC`), `16 kHz`, 16-bit Stereo (`L=R`), clock completamente separato dal microfono per evitare conflitti full-duplex (`[VERIFICATO DAL CODICE]`).
- **Alimentazione e pin di controllo**:
  - `VIN` → **`+5V`** (rail di potenza 5 V; **MAI collegare al pin `3V3`** dell'ESP32-S3 per evitare il collasso dell'LDO `SGM2212` durante i picchi audio fino a `~680 mA`).
  - `GND` → **`GND`** (con piste larghe `≥ 0,8–1,0 mm` o piano dedicato).
  - `SD` (`#SD_MODE`) → Collegato a **`3V3`** nei documenti di cablaggio attuali (`WIRING_GUIDE.md`) per abilitare l'amplificatore. *Nota tecnica KiCad*: sul breakout commerciale `MAX98357A`, è presente internamente un pull-up verso `VIN`; forzando `SD` a `3,3 V` diretti si seleziona solitamente il canale **Left** (che funziona correttamente perché `audio_playback.cpp` duplica l'audio su entrambi i canali `stereo_buf_[2*i] = sample; stereo_buf_[2*i+1] = sample;`). Sulla Carrier Board è consigliabile collegare `SD` a `3V3` tramite un jumper saldabile (o resistore `0 Ω`) in modo da poterlo anche lasciare flottante o pilotare se necessario (`[VERIFICATO DAL CODICE]` `[DA VERIFICARE FISICAMENTE]`).
  - `GAIN` → **Non collegato (`NC`)** per il guadagno standard di **`9 dB`** (in KiCad si può predisporre un jumper 3-vie opzionale `GND / NC / VIN` per `12 dB / 9 dB / 6 dB`).
  - `OUT+` e `OUT-` → Connettore **JST-PH 2.0 mm a 2 pin** diretto allo Speaker `4 Ω / 3 W` (`Ø 36–40 mm`). **DIVIETO ASSOLUTO**: uscita a ponte differenziale BTL — **non collegare MAI `OUT-` o `OUT+` a `GND`!** (`[DERIVATO DA DOC HARDWARE]`).

### 4.4 Display OLED 1,3" 128×64 I²C (SH1106 / SSD1306)
- **Interfaccia**: Bus **I²C0** (`GPIO 41 = SDA`, `GPIO 42 = SCL`) a `400 kHz`. Il firmware esegue all'avvio la scansione automatica di **`0x3C`** e **`0x3D`** (`display_driver.cpp`) e supporta sia controller `SH1106` (default in `platformio.ini`) sia `SSD1306` (`[VERIFICATO DAL CODICE]`).
- **Alimentazione**: `VCC` → **`3V3`**, `GND` → **`GND`** (consumo `~15–25 mA`).
- **Criticità PCB KiCad**: Sui moduli OLED 1,3" I²C a 4 pin esistono in commercio due pinout opposti per l'alimentazione: **`GND - VCC - SCL - SDA`** oppure **`VCC - GND - SCL - SDA`**. Prima di ordinare la PCB (o tramite 2 ponticelli `0 Ω` incrociati `JP_OLED_PWR` sulla Carrier Board), **verificare visivamente la serigrafia del modulo OLED fisico acquistato** (`[DA VERIFICARE FISICAMENTE]`).

### 4.5 Pulsante Fisico Momentaneo (NO)
- **Interfaccia**: **`GPIO 47`** (`kButtonActivate`) verso **`GND`**, normalmente aperto (NO), attivo `LOW` (`[VERIFICATO DAL CODICE]`).
- **Pull-up e Debounce**: Il firmware abilita `INPUT_PULLUP` interno (~`45 kΩ`) e applica un debounce software di `30–40 ms` (con pressione lunga a `1500 ms` in `jarvis-desk-buddy` o logica Push-to-Talk in `jarvis_wifi_voice_client`).
- **Requisito KiCad**: Prevedere sulla Carrier Board le piazzole opzionali (DNP o popolate) per un resistore di pull-up esterno da **`10 kΩ`** verso `3V3` e un condensatore filtro da **`100 nF`** verso `GND` per immunizzare il cavo (lungo ~10–15 cm verso il fianco `L3` del corpo LEGO) dai disturbi EMI dell'amplificatore Classe-D (`[DERIVATO DA DOC HARDWARE]`).

### 4.6 Sensore Tattile Capacitivo TTP223B
- **Interfaccia**: **`GPIO 1`** (`kTouchTtp223`), ingresso digitale puro (`pinMode(1, INPUT)` **senza** pull-up interno), attivo **`HIGH`** di default (ponticelli `A` aperto, `B` aperto sul modulo TTP223B) (`[VERIFICATO DAL CODICE]`).
- **Alimentazione**: `VCC` → **`3V3`** (**Tassativo**: se alimentato a `5 V`, l'uscita `SIG` eroga `5 V` danneggiando `GPIO 1` dell'ESP32-S3!), `GND` → **`GND`**.
- **Nota Operativa**: Il `TTP223B` esegue l'autocalibrazione nei primi `~0,5 s` dopo l'accensione. Sulla Carrier Board prevedere un condensatore da **`100 nF`** tra `VCC` e `GND` dedicato sul connettore del TTP223B per evitare falsi trigger indotti dal ripple sul rail `3,3 V` (`[DERIVATO DA DOC HARDWARE]` `[DA VERIFICARE FISICAMENTE]`).

### 4.7 Sensore di Distanza ToF VL53L0X / VL53L1X (Modello da Confermare)
- **Interfaccia I²C**: Condivide il bus **I²C0** (`GPIO 41 = SDA`, `GPIO 42 = SCL`), indirizzo hardware di default **`0x29`** (`kVl53l0xI2cAddr = 0x29` in `pinout_config.h`) (`[VERIFICATO DAL CODICE]`).
- **Compatibilità `VL53L0X` vs `VL53L1X`**:
  - Entrambi i chip STMicroelectronics hanno indirizzo I²C di default **`0x29`**, alimentazione nativa `2,8 V` (gestita su tutti i breakout commerciali tipo `GY-530` / Pololu da un regolatore LDO onboard + level shifter I²C) e lo stesso pinout a 4 o 6 pin (`VCC/VIN`, `GND`, `SDA`, `SCL`, più opzionali `XSHUT` e `GPIO1`).
  - A livello hardware/PCB KiCad, **un connettore a 5 o 6 pin passo `2,54 mm` (o JST-SH/XH) con `3V3`, `GND`, `SDA (GPIO 41)`, `SCL (GPIO 42)`, `XSHUT` è elettricamente compatibile sia con `VL53L0X` sia con `VL53L1X`** (`[DERIVATO DA DOC HARDWARE]`).
  - A livello software, i registri interni differiscono (`VL53L0X` range fino a ~1,2–2 m; `VL53L1X` range fino a ~4 m): poiché nel firmware attuale il driver reale non è ancora attivo (`sensor_stub.h`), la scelta del modello fisico richiederà solo l'inclusione della libreria corrispondente in FASE 8.2B, senza alcuna modifica alla Carrier Board PCB!
- **Verifica fisica**: Controllare se il breakout acquistato espone 4 pin (senza `XSHUT`) o 6 pin (con `XSHUT` e `GPIO1`) e verificare che l'LDO onboard funzioni regolarmente con `VIN = 3,3 V` (`[DA VERIFICARE FISICAMENTE]`).

### 4.8 Sensore di Luminosità Ambientale BH1750 (`GY-302`)
- **Interfaccia I²C**: Condivide il bus **I²C0** (`GPIO 41 = SDA`, `GPIO 42 = SCL`), indirizzo **`0x23`** (`kBh1750I2cAddr = 0x23` in `pinout_config.h`, con pin `ADDR` a `GND` o lasciato al pull-down interno del breakout; `0x5C` se `ADDR = 3V3`) (`[VERIFICATO DAL CODICE]`).
- **Alimentazione**: `VCC` → **`3V3`**, `GND` → **`GND`**, `ADDR` → **`GND`**.
- **Verifica fisica**: Il chip `BH1750FVI` accetta max `3,6 V`; i moduli `GY-302` montano solitamente un LDO `3,3 V` a basso dropout compatibile con `VCC = 3,3 V`. Verificare col multimetro prima del montaggio (`[DA VERIFICARE FISICAMENTE]`).

### 4.9 Accelerometro e Giroscopio a 6 Assi MPU6050 (`GY-521`)
- **Interfaccia I²C**: Condivide il bus **I²C0** (`GPIO 41 = SDA`, `GPIO 42 = SCL`), indirizzo **`0x68`** (`kMpu6050I2cAddr = 0x68` in `pinout_config.h`, con pin `AD0 = GND`; diventa `0x69` se `AD0 = 3V3`). Pin interrupt opzionale **`INT` → `GPIO 10`** (`kImuInt = 10`) (`[VERIFICATO DAL CODICE]`).
- **Criticità Elettrica `GY-521` (Dropout LDO)**: Molti moduli `GY-521` montano un regolatore LDO `3,3 V` (`662K`) in serie al pin `VCC` e hanno resistenze di pull-up da `4,7 kΩ` su `SDA/SCL` collegate all'uscita `3,3 V` dell'LDO.
  - Se alimentato con `VCC = 3,3 V`, l'uscita dell'LDO scende a `~3,0–3,1 V` (comunque dentro il range operativo `2,375–3,46 V` del chip `MPU6050`, ma da verificare a banco).
  - Se alimentato con `VCC = 5 V`, **bisogna prima verificare col multimetro a modulo scollegato che i pull-up di `SDA/SCL` sul `GY-521` siano effettivamente collegati a valle dell'LDO (`3,3 V`) e NON al `5 V`**!
  - **Soluzione KiCad**: Prevedere un jumper di selezione alimentazione a 3 piazzole (`JP_MPU_VCC`: `3V3` di default / `5V` opzionale) sul connettore del `GY-521` (`[DERIVATO DA DOC HARDWARE]` `[DA VERIFICARE FISICAMENTE]`).

### 4.10 Altri Componenti Previsti nel Repository
Dalla scansione completa del repository (`03-Mechanical-Design/05-Mobile-Electronics/`) risultano previsti esclusivamente per la futura **Base Mobile B2** (su una seconda scheda o nel vano inferiore B2, collegata alla Carrier Board del Modulo A tramite il connettore **JST-XH a 6 pin**):
- **ESP32-C3 SuperMini** (co-processore motori su B2), **Driver `TB6612FNG`**, **2× Motoriduttori N20 6V**, **Sensore di corrente a 3 canali `INA3221` (`0x40`)**, **Ideal Diode `LM66100`**, **2× Regolatori Buck (`5,09 V` e `6,0 V`)**, **Batteria Li-Ion 2S (`7,4 V`) con BMS** (`[DERIVATO DA DOC HARDWARE]`).

---

## 5. Alimentazione, Livelli Logici e Interfacce Bus

### 5.1 Tabella Tensioni, Correnti e Livelli Logici per Componente

| Componente | Tensione Alimentazione Pin Modulo | Tensione Logica I/O | Corrente Tipica | Corrente di Picco | Compatibilità Livelli ESP32-S3 (`3,3 V`) | Stato di Verifica |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **ESP32-S3-DevKitC-1 N16R8** | `5,0 V` (su USB o pin `5V` `J1-21`) → LDO interno `3,3 V` | **`3,3 V`** (NON 5V-tolerant!) | `150–220 mA` | `~355–500 mA` (Wi-Fi TX + Dual Core + PSRAM) | Nativa `3,3 V` | `[DERIVATO DA DOC HARDWARE]` |
| **OLED 1,3" SH1106** | **`3,3 V`** (`VCC`) | `3,3 V` (`SDA`, `SCL`) | `15 mA` | `25 mA` | ✅ 100% compatibile a `3,3 V` | `[VERIFICATO DAL CODICE]` `[DA VERIFICARE FISICAMENTE]` |
| **Microfono INMP441** | **`3,3 V`** (`VDD`, max `3,6 V`) | `3,3 V` (`WS`, `SCK`, `SD`) | `1,4 mA` | `1,5 mA` | ✅ 100% compatibile (MAI alimentare a 5 V) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **Amplificatore MAX98357A + Speaker 4 Ω / 3 W** | **`5,0 V`** (`VIN` potenza) + **`3,3 V`** (`SD` enable) | `3,3 V` (`DIN`, `BCLK`, `LRC` accettano logica `3,3 V` con `VIN = 5 V`) | `230–340 mA` (su `5V`) | `~680 mA` (su `5V` @ 3 W) | ✅ Ingressi I²S compatibili `3,3 V` (soglia $V_{IH} = 1,4\text{ V}$) | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **Pulsante Fisico NO** | Passivo verso `GND` | `3,3 V` (`INPUT_PULLUP`) | `< 0,1 mA` | `< 0,4 mA` (con `10 kΩ`) | ✅ 100% compatibile | `[VERIFICATO DAL CODICE]` |
| **Sensore Touch TTP223B** | **`3,3 V`** (`VCC`) | `3,3 V` (`SIG` push-pull) | `~3 µA` (idle) | `0,5 mA` | ✅ Sicuro **solo** se `VCC = 3,3 V` | `[VERIFICATO DAL CODICE]` `[DERIVATO DA DOC HARDWARE]` |
| **ToF VL53L0X / VL53L1X** | **`3,3 V`** (`VIN/VCC` → LDO `2,8 V` onboard) | `3,3 V` (`SDA`, `SCL`, `XSHUT`) | `19 mA` | `40 mA` | ✅ Level-shifter onboard a `3,3 V` | `[DERIVATO DA DOC HARDWARE]` `[DA VERIFICARE FISICAMENTE]` |
| **Luxmetro BH1750 (`GY-302`)** | **`3,3 V`** (`VCC`) | `3,3 V` (`SDA`, `SCL`) | `0,12 mA` | `0,2 mA` | ✅ Compatibile a `3,3 V` | `[DERIVATO DA DOC HARDWARE]` `[DA VERIFICARE FISICAMENTE]` |
| **IMU MPU6050 (`GY-521`)** | **`3,3 V`** (o `5 V` solo se LDO/pull-up verificati) | `3,3 V` (`SDA`, `SCL`, `INT`) | `3,8 mA` | `5 mA` | ⚠️ Verificare dropout LDO `662K` e tensione pull-up col multimetro | `[DERIVATO DA DOC HARDWARE]` `[DA VERIFICARE FISICAMENTE]` |

### 5.2 Bilancio Energetico e Dissipazione LDO `SGM2212-3.3`
- **Totale corrente sul Rail `+3,3 V`**: `~190–265 mA` tipici / `~570 mA` di picco impulsivo Wi-Fi TX (`[DERIVATO DA DOC HARDWARE]`).
  - L'LDO onboard `SGM2212-3.3` della DevKitC-1 eroga fino a `800 mA` ma dissipa $P_D = (5,0\text{ V} - 3,3\text{ V}) \times I_{3V3} \approx 0,32\text{–}0,45\text{ W}$ medi.
  - **Consiglio per la Carrier Board PCB**: È possibile utilizzare direttamente il rail `3V3` della DevKitC-1 (`J1-1` e `J1-2` uniti in parallelo sulla PCB per dimezzare la resistenza di contatto), **oppure** prevedere sulla Carrier Board l'impronta opzionale per un piccolo regolatore `3,3 V` ausiliario (es. `AMS1117-3.3` o buck `3,3 V`) dedicato ai soli sensori esterni/OLED, selezionabile via jumper `JP_3V3_SRC`, alleggerendo così il carico termico sull'LDO della DevKitC-1.
- **Totale corrente sul Rail `+5,0 V`**: `~420–605 mA` tipici / **`~1,25 A` di picco** (Wi-Fi TX + audio 3 W).
  - **Regola di distribuzione a stella su PCB**: Dal punto di ingresso `+5V` (o dal pin `J1-21` quando alimentato via USB-C della DevKitC-1), tracciare una pista larga (`≥ 1,0–1,5 mm`, `1 oz Cu`) diretta verso `VIN` del `MAX98357A`, posizionando un condensatore elettrolitico da **`470 µF / 16 V`** (`C_AUDIO_BULK`) + un ceramico da **`100 nF`** (`C_AUDIO_DEC`) a meno di `5 mm` dal pin `VIN` del `MAX98357A`.

### 5.3 Architettura dei Bus I²C e Problema dei Pull-Up Paralleli
1. **Bus `I2C0` Primario (`GPIO 41 = SDA`, `GPIO 42 = SCL` @ `400 kHz`)** (`[VERIFICATO DAL CODICE]`):
   - Ospita 4 dispositivi:
     - **OLED SH1106 / SSD1306**: indirizzo **`0x3C`** (o `0x3D`)
     - **VL53L0X / VL53L1X**: indirizzo **`0x29`**
     - **MPU6050 (`AD0 = GND`)**: indirizzo **`0x68`**
     - **BH1750 (`ADDR = GND`)**: indirizzo **`0x23`**
   - **Conflitti di indirizzo**: **ZERO** (tutti e 4 gli indirizzi a 7-bit sono distinti).
   - **CRITICITÀ PULL-UP IN PARALLELO (`[DERIVATO DA DOC HARDWARE]` `[DA VERIFICARE FISICAMENTE]`)**:
     - Ciascuno dei 4 moduli breakout commerciali monta tipicamente una coppia di resistori di pull-up da `4,7 kΩ` (o `10 kΩ`) tra `SDA/SCL` e `3V3`.
     - Collegando 4 moduli con pull-up da `4,7 kΩ` in parallelo sullo stesso bus `I2C0`, la resistenza equivalente scende a $R_{eq} = 4,7\text{ k}\Omega / 4 \approx \mathbf{1,17\text{ k}\Omega}$ (corrente di sink `~2,8 mA`, vicina al limite di specifica Fast-Mode I²C di `3 mA`, con fronti distorti e rischio di NACK sull'OLED).
     - **Prescrizione per KiCad**:
       1. Prevedere sulla Carrier Board due resistori di pull-up master `R_I2C0_SDA` e `R_I2C0_SCL` da **`4,7 kΩ` marcati `DNP` (Do Not Populate)** se si usano i moduli breakout con pull-up già montati.
       2. Prima di inserire i 4 moduli nei connettori della Carrier Board, misurare con il multimetro la resistenza tra `SDA` e `3V3` di ciascun modulo e, se $R_{eq, \text{totale}} < 2,2\text{ k}\Omega$, dissaldare le resistenze di pull-up SMD da `MPU6050` e `BH1750` (lasciando attive solo quelle sull'OLED e sul `VL53L0X`, per ottenere $R_{eq} \approx 2,35\text{–}3,3\text{ k}\Omega$).
2. **Bus `I2C1` Esterno Opzionale (`GPIO 8 = SDA`, `GPIO 9` o `GPIO 14 = SCL`)**:
   - L'ESP32-S3 dispone di **due controller I²C hardware indipendenti** (`Wire` / `I2C_NUM_0` e `Wire1` / `I2C_NUM_1`). Se in futuro si desidera isolare il traffico continuo a 30 FPS dell'OLED (`I2C0` su `GPIO 41/42`) dalle letture dei sensori o della Base Mobile B2, `Wire1` può essere mappato su `GPIO 8` e `GPIO 9` (o `GPIO 14`).

### 5.4 Linee I²S Utilizzate
L'ESP32-S3 dispone di **due periferiche I²S hardware indipendenti** (`I2S_NUM_0` e `I2S_NUM_1`), entrambe sfruttate dal firmware vocale (`[VERIFICATO DAL CODICE]`):
- **I²S0 RX (Microfono `INMP441`)**:
  - `WS (LRCLK)` = **`GPIO 4`**
  - `SCK (BCLK)` = **`GPIO 5`**
  - `SD (DIN)` = **`GPIO 6`**
- **I²S1 TX (Amplificatore `MAX98357A`)**:
  - `DIN (DOUT)` = **`GPIO 7`**
  - `BCLK` = **`GPIO 15`**
  - `LRC (LRCLK)` = **`GPIO 16`**
- **Separazione su PCB**: Mantenere le 3 piste di `I²S0 RX` (`GPIO 4, 5, 6`) ad almeno `3–5 mm` di distanza dalle piste `I²S1 TX` (`GPIO 7, 15, 16`) e soprattutto lontane dalle piste di potenza `OUT+ / OUT-` dello speaker, interponendo una traccia di guardia collegata a `GND` con vie di cucitura (*GND stitching vias*) per evitare accoppiamento capacitivo e auto-oscillazioni/eco elettrico.

---

## 6. Conflitti Rilevati e Criticità da Risolvere prima dello Sbroglio KiCad

Dall'analisi incrociata tra codice sorgente (`04-Firmware/`) e documentazione meccanica/elettrica (`06-Hardware-Integration/` e `03-Mechanical-Design/`), emergono **3 conflitti/incongruenze documentali** che devono essere gestiti sulla Carrier Board PCB:

### Criticità #1 — Conflitto Documentale su `GPIO 8` (Touch `TTP223B` vs `I2C_EXT_SDA` Base Mobile B2)
- **Situazione riscontrata**:
  - Nei documenti di Fase 8 ([FASE_8_SENSORY_INTERACTION.md](06-Hardware-Integration/FASE_8_SENSORY_INTERACTION.md#L37) e [GUIDA_MONTAGGIO_ELETTRONICA.md](06-Hardware-Integration/GUIDA_MONTAGGIO_ELETTRONICA.md#L45)), il sensore touch `TTP223` è indicato su **`GPIO 8`**.
  - Nei documenti della Base Mobile B2 ([02_Progetto_Modulare_e_Mobilita.md](03-Mechanical-Design/02_Progetto_Modulare_e_Mobilita.md#L70) e [04_Pinout_Connettore_JST-XH.md](03-Mechanical-Design/05-Mobile-Electronics/04_Pinout_Connettore_JST-XH.md#L16)), **`GPIO 8`** è assegnato al Pin 5 del connettore `JST-XH` (`I2C_EXT_SDA`).
  - **Nel codice firmware attuale** ([pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L21-L24)), il conflitto è **già stato risolto** spostando `kTouchTtp223` su **`GPIO 1`** (`constexpr uint8_t kTouchTtp223 = 1;`).
- **Soluzione per il PCB KiCad**: Cablare il connettore del sensore **`TTP223B` su `GPIO 1`** (coerente al 100% con il firmware attuale) e lasciare **`GPIO 8` dedicato al Pin 5 del connettore `JST-XH 6-pin`** (`I2C_EXT_SDA`). Opzionalmente, inserire un jumper SMD a 3 piazzole (`JP_TOUCH`: centro → `TTP223_SIG`, lato 1 → `GPIO 1` [default chiuso], lato 2 → `GPIO 8`) per massima flessibilità.

### Criticità #2 — Conflitto su `GPIO 9` (`kTofXshut` in `pinout_config.h` vs `I2C_EXT_SCL` su `JST-XH Pin 6`)
- **Situazione riscontrata**:
  - In [pinout_config.h](04-Firmware/jarvis-desk-buddy/include/pinout_config.h#L34) è definita la costante `constexpr uint8_t kTofXshut = 9;` (non ancora usata nel codice attivo).
  - In [04_Pinout_Connettore_JST-XH.md](03-Mechanical-Design/05-Mobile-Electronics/04_Pinout_Connettore_JST-XH.md#L17), **`GPIO 9`** è assegnato al Pin 6 del connettore `JST-XH` (`I2C_SCL`).
- **Soluzione per il PCB KiCad**: Inserire un jumper di selezione SMD a 3 piazzole (o due resistori `0 Ω` alternativi `R_JMP_GPIO9` / `R_JMP_GPIO14`):
  - Così `GPIO 9` può essere indirizzato a `VL53L0X XSHUT` (configurazione statica stand-alone fedele a `pinout_config.h`) oppure al Pin 6 del connettore `JST-XH` (`I2C_EXT_SCL`), mentre `VL53L0X XSHUT` può essere collegato a `GPIO 14` (o tenuto alto a `3V3` tramite pull-up da `10 kΩ`).

### Criticità #3 — Divieto di Alimentazione Simultanea USB-C (PC) + `+5V_A` Esterno (Base Mobile B2)
- **Situazione riscontrata**:
  - Sulla DevKitC-1, la porta USB nativa è protetta verso monte dal diodo Schottky `D1`/`D7` (`1N5819HW`, 1 A max), mentre il pin `5V` (`J1-21`) è collegato direttamente al nodo interno `VCC_5V` (`[DERIVATO DA DOC HARDWARE]`).
  - Se si alimenta `J1-21` dalla Base Mobile B2 (`+5V_A` su `JST-XH Pin 1`) e contemporaneamente si collega il cavo USB-C al PC, i due generatori da 5 V entrano in contesa attraverso `D1`/`D7`.
- **Soluzione per il PCB KiCad**:
  - Riportare chiaramente sulla **serigrafia (Silkscreen)** della Carrier Board vicino al connettore `JST-XH`: **`"NO HOT-PLUG / SCOLLEGARE USB-C PRIMA DI ACCENDERE B2"`**.
  - Opzionalmente, inserire sulla Carrier Board un diodo Schottky a bassissima caduta o un Ideal Diode (`LM66100` / MOSFET P-channel) o un jumper di isolamento `JP_5V_EXT` sul Pin 1 del connettore `JST-XH`.

---

## 7. Predisposizione Futura Base Mobile (Modulo B2) ed Espansioni

Come richiesto al Punto 4, **non viene modificato il firmware né assegnato definitivamente alcun nuovo GPIO nel codice**, ma si definiscono le **due opzioni architetturali candidate** da predisporre sui connettori di espansione della Carrier Board PCB (nettamente distinte dalle assegnazioni già implementate).

### 7.1 Opzione Candidata A (Architettura Modulare Documentata in `05-Mobile-Electronics` — Consigliata)
In questa architettura (già dettagliata in [01_Architettura_Elettrica_B2.md](03-Mechanical-Design/05-Mobile-Electronics/01_Architettura_Elettrica_B2.md)), la Base Mobile B2 ospita un piccolo co-processore dedicato (`ESP32-C3 SuperMini`) che pilota localmente il `TB6612FNG` e legge l'`INA3221`, comunicando con la Carrier Board dell'ESP32-S3 (Modulo A) tramite il solo **connettore ombelicale JST-XH a 6 pin** (`passo 2,50 mm` o `2,54 mm`):

| Pin Connettore `J_B2_UMBILICAL` (JST-XH 6-pin) | Segnale Proposto | GPIO Candidato su ESP32-S3 | Direzione | Funzione e Protezioni da Integrare sulla Carrier Board PCB | Stato |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **Pin 1** | `+5V_A` (`+5V_B2`) | Pin `5V` (`J1-21`) | B2 → A | Ingresso alimentazione `5,0 V` regolata dal Buck di B2 (protetto da fusibile/jumper). | *Candidato (Doc B2)* |
| **Pin 2** | `GND` | Piano `GND` | Comune | Massa comune di potenza e segnale. | *Candidato (Doc B2)* |
| **Pin 3** | `UART_TX_MOT` | **`GPIO 17`** (`U1TXD`) | OUTPUT (A → B2) | Trasmissione comandi velocità/direzione verso B2. **Inserire resistore serie `220–330 Ω` sulla PCB.** | *Candidato (Libero in FW)* |
| **Pin 4** | `UART_RX_MOT` | **`GPIO 18`** (`U1RXD`) | INPUT (B2 → A) | Ricezione telemetria batteria/stallo da B2. **Inserire resistore serie `220–330 Ω` sulla PCB.** | *Candidato (Libero in FW)* |
| **Pin 5** | `I2C_EXT_SDA` | **`GPIO 8`** | Bidirezionale | Linea dati I²C secondaria (`Wire1`) o GPIO ausiliario verso B2. Predisporre piazzola pull-up `4,7 kΩ` (`DNP`). | *Candidato (Libero in FW)* |
| **Pin 6** | `I2C_EXT_SCL` | **`GPIO 9`** *(o `GPIO 14` via jumper)* | OUTPUT / Bidir. | Linea clock I²C secondaria (`Wire1`) o GPIO ausiliario verso B2. Predisporre piazzola pull-up `4,7 kΩ` (`DNP`). | *Candidato (Selezionabile)* |

### 7.2 Opzione Candidata B (Pilotaggio Diretto `TB6612FNG` + Sensori Anticollisione/Anticaduta dall'ESP32-S3)
Qualora si desiderasse in futuro pilotare il driver motori **Toshiba `TB6612FNG`** e i sensori di sicurezza **direttamente dall'ESP32-S3** (senza usare l'`ESP32-C3 SuperMini`), l'ESP32-S3 dispone di **11 GPIO liberi e puliti** (`GPIO 2, 8, 11, 12, 13, 14, 17, 18, 21, 39, 40`).
Sulla Carrier Board PCB è sufficiente esporre un **Header di Espansione ausiliario (`J_EXP_MOTION`, es. 2×6 o 1×10 pin passo 2,54 mm)** con la seguente mappatura candidata:

| Funzione Futura (Pilotaggio Diretto) | Segnale Modulo | GPIO Candidato ESP32-S3 | Tipo Segnale / Periferica ESP32-S3 | Note Tecniche e Requisiti PCB | Stato |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **TB6612FNG — Motore SX PWM** | `PWMA` | **`GPIO 17`** | Output PWM (`LEDC` Ch 0, `20 kHz`) | Qualsiasi GPIO di output dell'ESP32-S3 supporta il PWM hardware `LEDC`. | *Proposta Candidata* |
| **TB6612FNG — Motore SX Dir 1** | `AIN1` | **`GPIO 11`** | Output Digitale | Controllo direzione ponte H canale A. | *Proposta Candidata* |
| **TB6612FNG — Motore SX Dir 2** | `AIN2` | **`GPIO 12`** | Output Digitale | Controllo direzione ponte H canale A. | *Proposta Candidata* |
| **TB6612FNG — Motore DX PWM** | `PWMB` | **`GPIO 18`** | Output PWM (`LEDC` Ch 1, `20 kHz`) | PWM hardware `LEDC`. | *Proposta Candidata* |
| **TB6612FNG — Motore DX Dir 1** | `BIN1` | **`GPIO 13`** | Output Digitale | Controllo direzione ponte H canale B. | *Proposta Candidata* |
| **TB6612FNG — Motore DX Dir 2** | `BIN2` | **`GPIO 14`** | Output Digitale | Controllo direzione ponte H canale B. | *Proposta Candidata* |
| **TB6612FNG — Standby / Enable** | `STBY` | **`GPIO 21`** | Output Digitale | **OBBLIGATORIO pull-down hardware `10 kΩ` verso `GND`** per tenere i motori disabilitati (`High-Z`) durante il boot/reset dell'ESP32-S3. | *Proposta Candidata* |
| **Sensore Anticaduta (Cliff SX)** | `CLIFF_L_OUT` (es. `TCRT5000` a `3,3 V`) | **`GPIO 2`** | Input Digitale / Interrupt (o `ADC1_CH1` analogico!) | **Vantaggio chiave**: `GPIO 2` appartiene ad **`ADC1`** (`ADC1_CH1`), quindi su ESP32-S3 può leggere anche un segnale **analogico** con il Wi-Fi attivo (`ADC2` invece è bloccato dal Wi-Fi!). | *Proposta Candidata* |
| **Sensore Anticaduta (Cliff DX)** | `CLIFF_R_OUT` (es. `TCRT5000` a `3,3 V`) | **`GPIO 8`** | Input Digitale / Interrupt (o `ADC1_CH7` analogico!) | Anche `GPIO 8` appartiene ad **`ADC1`** (`ADC1_CH7`), funzionante in analogico anche con Wi-Fi attivo! | *Proposta Candidata* |
| **Sensore Anticollisione Frontale/Posteriore aggiuntivo** | Secondo `VL53L0X/L1X` `XSHUT_2` (o bumper) | **`GPIO 39`** e **`GPIO 40`** | Output Digitale (`XSHUT_2`) / Input Digitale (`BUMPER_IN`) | Permette di avere un secondo ToF sullo stesso bus I²C riassegnandogli l'indirizzo via `XSHUT` al boot, più un microswitch bumper meccanico. | *Proposta Candidata* |

> **Suggerimento progettuale per KiCad**: Poiché i pin `GPIO 8, 9, 17, 18` sono condivisi tra l'Opzione A (UART + I²C verso B2) e l'Opzione B (pilotaggio diretto), basta portare `GPIO 17, 18, 8, 9` al connettore `JST-XH 6-pin` **e** riportare in parallelo tutti i GPIO liberi (`GPIO 2, 8, 9, 11, 12, 13, 14, 17, 18, 21, 39, 40` + `3V3` + `GND`) su un header ausiliario `J_EXP` sulla Carrier Board. In questo modo la stessa identica PCB supporterà entrambe le architetture senza alcuna modifica hardware!

---

## 8. Linee Guida e Requisiti per la Progettazione in KiCad

### 8.1 Vincoli Meccanici di Ingombro nel Corpo LEGO (`Companion Hybrid v2`)
Dalla documentazione meccanica verificata ([03_Progetto_Interno_e_Raffreddamento.md](03-Mechanical-Design/03_Progetto_Interno_e_Raffreddamento.md) e [GUIDA_MONTAGGIO_ELETTRONICA.md](06-Hardware-Integration/GUIDA_MONTAGGIO_ELETTRONICA.md#L149-L158)):
1. **Vano interno utile del Modulo A (`10×10 stud` esterni)**:
   - Sezione interna libera: **`64,0 × 64,0 mm` (`8×8 stud`)** (`[DERIVATO DA DOC HARDWARE]`).
   - Apertura del portello posteriore di manutenzione (`Plate 6×8` cod. `3036`): **`48,0 × 57,6 mm`**.
   - Altezza interna utile: **`~86,4 mm`** (nella variante `Companion Hybrid v2 Visor`) / fino a `~128 mm` (nella variante alta).
2. **Dimensioni massime raccomandate per la Carrier Board PCB**:
   - Se la Carrier Board viene montata **verticalmente** sulla guida posteriore `Technic Liftarm 1×5` (`32316`, a `Z = 54 mm`):
     - Larghezza massima consigliata: **`≤ 46,0 mm`** (così può essere inserita/estratta agevolmente anche attraverso il portello posteriore da `48,0 mm`, oppure **`≤ 60,0 mm`** se inserita dall'alto rimuovendo il tetto speaker).
     - Altezza massima consigliata: **`≤ 65,0 – 70,0 mm`** (la DevKitC-1 è lunga circa `63,0 mm`).
   - **Altezza dei componenti (Profilo Z)**:
     - Tra la guida `Z = 54 mm` e la parete posteriore restano `~18 mm`; verso il fronte (`OLED` a `Z = 12 mm`) restano `~42 mm`.
     - **Usare socket femmina a basso profilo (`Low-Profile Female Headers`, altezza `5,0–5,7 mm` invece degli standard da `8,5 mm`)** per innestare la DevKitC-1 sulla Carrier Board, e **connettori JST-XH / JST-PH a 90° (orizzontali)** sui bordi della PCB per evitare che i cavi puntino contro il magnete dello speaker o contro il retro dell'OLED (`[DERIVATO DA DOC HARDWARE]` `[DA VERIFICARE FISICAMENTE]`).
   - **Keep-Out Area Antenna Wi-Fi (`2,4 GHz`)**:
     - L'antenna PCB dell'`ESP32-S3-WROOM-1` sporge nella parte superiore della DevKitC-1.
     - Sulla Carrier Board KiCad, **non posizionare alcun piano di rame (`GND` o `3V3`), né piste, né connettori metallici** nell'area sottostante e circostante l'antenna del modulo WROOM-1 (lasciare una fascia di *Copper Keep-Out* su `F.Cu` e `B.Cu` di almeno `10–15 mm` attorno all'antenna, oppure fare sporgere l'antenna della DevKitC-1 oltre il bordo superiore della Carrier Board PCB).

### 8.2 Connettori Consigliati sullo Schematico KiCad

| Sigla KiCad | Funzione Connettore | Tipo Footprint Consigliato | Pinout Connettore Suggerito | Note KiCad |
| :--- | :--- | :--- | :--- | :--- |
| **`U1_DEVKIT`** | Alloggiamento **ESP32-S3-DevKitC-1 N16R8** | 2× Header Femmina `1×22` passo `2,54 mm` (verificare interasse `22,86 mm` / `900 mil` con calibro!) | Pin-to-pin 1..22 su `J1` e 1..22 su `J3` | Marcare con flag `No-Connect (X)` i pin `GPIO 0, 3, 19, 20, 35, 36, 37, 38, 43, 44, 45, 46, 48` e `RST`. |
| **`J_OLED`** | Display **OLED 1,3" SH1106** | `JST-XH` o Header `1×04` passo `2,54 mm` | `1: VCC (3V3)`, `2: GND`, `3: SCL (GPIO42)`, `4: SDA (GPIO41)` | **Inserire jumper di inversione `JP_OLED_PWR`** per scambiare Pin 1 (`VCC`) e Pin 2 (`GND`) in base al lotto dell'OLED! |
| **`J_MIC`** | Microfono **INMP441** | Header / `JST-SH/XH` `1×06` passo `2,54 mm` | `1: VDD (3V3)`, `2: GND`, `3: L/R (GND)`, `4: WS (GPIO4)`, `5: SCK (GPIO5)`, `6: SD (GPIO6)` | Collegare il pin `L/R` direttamente a `GND` sulla PCB + `100 nF` su `VDD` + `100 kΩ` pull-down su `SD`. |
| **`U_AMP` / `J_AMP`** | Breakout **MAX98357A** | 2× Header Femmina `1×07` (per montare il breakout come modulo plug-in sulla Carrier Board) | `VIN (+5V)`, `GND`, `SD (3V3 via JP)`, `GAIN (NC)`, `DIN (GPIO7)`, `BCLK (GPIO15)`, `LRC (GPIO16)` | Posizionare `C1 = 470 µF 16V` + `C2 = 100 nF` vicinissimi a `VIN`/`GND`. |
| **`J_SPK`** | **Speaker 4 Ω / 3 W** | `JST-PH 2.0 mm` `1×02` (o morsetto del breakout MAX98357A) | `1: OUT+`, `2: OUT-` | **Piste differenziali larghe (`≥ 1,0 mm`), completamente isolate da `GND`!** |
| **`J_BTN`** | **Pulsante Fisico NO** | `JST-XH` / `JST-PH` `1×02` | `1: BTN (GPIO47)`, `2: GND` | Aggiungere footprint per `R_PU = 10 kΩ` verso `3V3` (`DNP`) + `C_DEB = 100 nF` verso `GND`. |
| **`J_TOUCH`** | Sensore **TTP223B** | `JST-XH` / `JST-PH` `1×03` | `1: VCC (3V3)`, `2: GND`, `3: SIG (GPIO1)` | Aggiungere `100 nF` su `VCC` + jumper opzionale `GPIO1 / GPIO8`. **Solo 3,3 V!** |
| **`J_TOF`** | Sensore **VL53L0X / VL53L1X** | `JST-XH` / Header `1×06` | `1: VCC (3V3)`, `2: GND`, `3: SCL (GPIO42)`, `4: SDA (GPIO41)`, `5: GPIO1_TOF (NC)`, `6: XSHUT (GPIO9/14)` | Compatibile sia con breakout a 4 pin sia a 6 pin (`GY-530` / Pololu). |
| **`J_LUX`** | Sensore **BH1750 (`GY-302`)** | `JST-XH` / Header `1×05` | `1: VCC (3V3)`, `2: GND`, `3: SCL (GPIO42)`, `4: SDA (GPIO41)`, `5: ADDR (GND)` | Pin 5 (`ADDR`) legato a `GND` sulla PCB per fissare l'indirizzo `0x23`. |
| **`J_IMU`** | Sensore **MPU6050 (`GY-521`)** | Header Femmina `1×08` | `VCC (via JP 3V3/5V)`, `GND`, `SCL (GPIO42)`, `SDA (GPIO41)`, `XDA (NC)`, `XCL (NC)`, `AD0 (GND)`, `INT (GPIO10)` | Pin `AD0` legato a `GND` (`0x68`). Jumper `JP_MPU_VCC` su `3V3` di default. |
| **`J_B2_UMB`** | Connettore **Base Mobile B2** | **`JST-XH 6-pin`** verticale o 90° (`passo 2,50/2,54 mm`) | `1: +5V_A`, `2: GND`, `3: TX (GPIO17)`, `4: RX (GPIO18)`, `5: SDA_EXT (GPIO8)`, `6: SCL_EXT (GPIO9/14)` | Resistori serie `220–330 Ω` su `GPIO 17` e `GPIO 18`. Serigrafia *"NO HOT-PLUG"*. |
| **`J_EXP_AUX`** | Header Espansione Futura (`TB6612` / Cliff) | Header `2×07` o `1×12` passo `2,54 mm` | `3V3`, `GND`, `GPIO 2, 8, 9, 11, 12, 13, 14, 17, 18, 21, 39, 40` | Espone tutti i GPIO liberi per test point con oscilloscopio o pilotaggio diretto motori/cliff. |

### 8.3 Checklist Passivi e Componenti Ausiliari da Inserire nello Schematico KiCad
1. **Condensatori di disaccoppiamento**:
   - `C1`: **`470 µF / 16 V`** elettrolitico low-ESR sul rail `+5V` vicino a `MAX98357A VIN`.
   - `C2..C8`: **`7× 100 nF / 16 V` (0603 o 0805 X7R)**, uno accanto a ciascun connettore (`MAX98357A`, `OLED`, `INMP441`, `TTP223B`, `VL53L0X`, `BH1750`, `MPU6050`).
   - `C9`: **`10 µF / 10 V` (0805 X5R)** sul rail principale `+3V3` della Carrier Board.
2. **Resistori di protezione e configurazione**:
   - `R1, R2`: **`2× 220 Ω` (o `330 Ω`)** in serie a `GPIO 17` (`UART_TX`) e `GPIO 18` (`UART_RX`) verso il connettore `JST-XH 6-pin`.
   - `R3`: **`100 kΩ`** pull-down tra `GPIO 6` (`I2S_MIC_SD`) e `GND`.
   - `R4, R5`: **`2× 4,7 kΩ` (`DNP`)** pull-up opzionali su `I2C0_SDA` (`GPIO 41`) e `I2C0_SCL` (`GPIO 42`).
   - `R6, R7`: **`2× 4,7 kΩ` (`DNP`)** pull-up opzionali su `I2C_EXT_SDA` (`GPIO 8`) e `I2C_EXT_SCL` (`GPIO 9`).
   - `R8`: **`10 kΩ`** pull-up opzionale su `VL53L0X XSHUT`.
   - `R9`: **`10 kΩ` (`DNP`)** pull-up opzionale su `GPIO 47` (`BTN`) + `C10 = 100 nF` verso `GND`.
3. **Fori di montaggio meccanico LEGO-compatibili**:
   - Il passo standard dei fori LEGO Technic è **`8,00 mm`** con diametro foro **`Ø 4,85 mm`** (per perni Technic standard) oppure **`Ø 3,2 mm` (M3)** per distanziali in nylon. Prevedere 2 o 4 fori con interasse multiplo di **`8,00 mm`** (es. `32,0 mm` o `40,0 mm`) consente di agganciare la Carrier Board direttamente ai liftarm LEGO Technic (`32316`) senza colla né modifiche alla scocca! (`[DERIVATO DA DOC HARDWARE]`).
