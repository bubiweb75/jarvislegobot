# JARVIS LEGO BOT — FASE 10.4: Collaudo Hardware MAX98357A + Speaker

Sketch Arduino isolato per verificare l'uscita audio I²S dell'**ESP32-S3-DevKitC-1 N16R8** tramite amplificatore **MAX98357A** e speaker **4 Ω / 3 W**, senza modificare Eyes 3.0, `inmp441_hw_test`, Wokwi, `TouchManager` o `GPIO1`.

---

## 1. Collegamenti Hardware

| Segnale `MAX98357A` | ESP32-S3 / Alimentazione | Note |
|---|---|---|
| `LRC` (WS) | `GPIO16` | Word Select I²S |
| `BCLK` | `GPIO15` | Bit Clock I²S |
| `DIN` | `GPIO7` | Data Out da ESP32-S3 |
| `GAIN` | Non collegato | Guadagno default `9 dB` |
| `SD` | `3V3` | Abilitazione amplificatore |
| `GND` | `GND` | Massa comune |
| `VIN` | `3V3` *(solo primo test 1%)* | Vedi sezione Sicurezza Elettrica sotto |
| Speaker `+` / `−` | Morsetti `+` / `−` MAX98357A | Speaker `4 Ω / 3 W` **mai** verso `GND` |

---

## 2. Sicurezza Elettrica (Verifiche Obbligatorie Prima dell'Accensione)

1. **Multimetro a scheda scollegata**:
   - Nessun cortocircuito tra `3V3` e `GND`.
   - Nessun cortocircuito tra i morsetti speaker `+` e `−`.
   - Nessuna continuità tra i morsetti speaker (`+` o `−`) e `GND` (uscita BTL differenziale: collegare un polo a `GND` danneggia lo stadio finale).
   - `VIN` e `SD` collegati correttamente a `3V3`.
2. **Limiti del regolatore `3V3` dell'ESP32-S3-DevKitC-1**:
   - Sulla linea `3V3` sono già alimentati ESP32-S3 (`~60–120 mA`, picchi fino a `~200 mA`), OLED SH1106 (`~10–25 mA`) e INMP441 (`~1,4 mA`).
   - A **1% di ampiezza PCM** per `300 ms`, la corrente assorbita dal MAX98357A rimane ridotta (`< 50 mA` di picco).
   - **Attenzione**: a volume medio/alto su carico `4 Ω`, il MAX98357A può assorbire picchi di **`400–550 mA`** (su `3,3 V`), rischiando brownout/reset della ESP32-S3 o surriscaldamento del regolatore LDO interno.
   - **Regola**: **non aumentare il volume** durante questo test su `3V3`. Per uso continuativo o volumi superiori, alimentare `VIN` del MAX98357A da una linea **`5V` dedicata/adeguata** condividendo **`GND`** con l'ESP32-S3.

---

## 3. Configurazione I²S e Comportamento dello Sketch

- **API**: `<ESP_I2S.h>` (`I2SClass`), core Arduino-ESP32 `3.3.12`.
- **Modalità**: Master TX, `I2S_MODE_STD` (Philips), `16000 Hz`, `I2S_DATA_BIT_WIDTH_16BIT`, `I2S_SLOT_MODE_STEREO`, `I2S_STD_SLOT_BOTH`.
- **Duplicazione L/R**: ogni campione mono `int16_t` è scritto identico su entrambi gli slot (`[sample, sample]`), così l'uscita è corretta indipendentemente dalla soglia di selezione canale sul pin `SD`.
- **Tono**: `440 Hz`, `300 ms`, ampiezza massima `327` (`~1%` di `32767`), fade-in e fade-out da `20 ms`, seguito da `60 ms` di zeri.
- **Ripetizione**: suona **una sola volta** all'avvio; ripetibile inviando `TEST` sul Monitor Seriale (`115200 baud`).

---

## 4. Procedura Arduino IDE 2

1. Apri `04-Firmware\arduino-hw-test\max98357a_hw_test\max98357a_hw_test.ino`.
2. In **Strumenti (Tools)**:
   - **Board**: `ESP32S3 Dev Module` (core **Espressif ESP32 3.x**)
   - **Flash Size**: `16MB (128Mb)` | **Flash Mode**: `QIO 80MHz` | **PSRAM**: `OPI PSRAM`
   - **USB CDC On Boot**: `Disabled` (porta **UART CH343**) oppure `Enabled` (porta **USB** nativa)
   - **Port**: la porta COM rilevata
3. Verifica (`Ctrl+R`), Carica (`Ctrl+U`) e apri il **Monitor Seriale** a **`115200 baud`**.
4. Controlla `I2S TX inizializzato...` e `TONE_DONE: ... errors=0`.
