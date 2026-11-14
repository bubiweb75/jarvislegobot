# WIRING_GUIDE — Schema Elettronico e Guida ai Collegamenti (FASE 6)

> **Stato:** Schema di preparazione su breadboard (nessun componente ancora collegato).
> **Regola fondamentale:** Eseguire tutti i cablaggi **a USB scollegata**, verificare le polarità con multimetro/controllo visivo delle serigrafie, e solo dopo collegare la porta **USB nativa** al PC.

---

## 1. Schema a Blocchi dei Collegamenti

```text
                       +-----------------------------------+
                       |        PC WINDOWS 11 (USB)        |
                       |   faster-whisper + Ollama + Piper |
                       +-----------------+-----------------+
                                         | Cavo USB-C (Dati + 5V)
                                         v
                       +-----------------------------------+
                       |     PORTA "USB" (GPIO 19 / 20)    |
                       |    ESP32-S3-DevKitC-1 (N16R8)     |
                       +--+----+----+----+----+----+----+--+
                          |    |    |    |    |    |    |
       +------------------+    |    |    |    |    |    +-------------------+
       | [ALIM]                |    |    |    |    |                        | [ALIM]
       v 3V3                   |    |    |    |    |                        v 5V (VBUS)
  +----+----+                  |    |    |    |    |                  +-----+-----+
  | Rail    |                  |    |    |    |    |                  |  MAX98357A  |
  | +3.3 V  |                  |    |    |    |    |                  |   VIN (5V)  |
  +--+---+--+                  |    |    |    |    |                  |   GND       +---> GND
     |   |                     |    |    |    |    |                  |   SD <------+--- 3V3
     |   +---> OLED VCC        |    |    |    |    |                  |   GAIN (NC) |
     |   +---> INMP441 VDD     |    |    |    |    |                  |   DIN  <----+--- GPIO 7
     |                         |    |    |    |    |                  |   BCLK <----+--- GPIO 15
     | [I2C0]                  |    |    |    |    |                  |   LRC  <----+--- GPIO 16
     |   GPIO 41 <-------------+----+    |    |    |                  +---+-----+---+
     |   GPIO 42 <-------------+---------+    |    |                      |     |
     |   (OLED SDA / SCL)      |              |    |               OUT+ --+     +-- OUT-
     |                         | [I2S0 RX]    |    |                      |     |  (DIFFERENZIALE!
     |                         |  GPIO 4  --->+----+ INMP441 WS           v     v   MAI A GND)
     |                         |  GPIO 5  --->+----+ INMP441 SCK      +-------------+
     |                         |  GPIO 6  <---+----+ INMP441 SD       |   SPEAKER   |
     |                         |              |      INMP441 L/R->GND | 4 Ohm / 3 W |
     |                         | [PULSANTE]   |                       | (JST-PH2.0) |
     |                         |  GPIO 47 <---+----[ NO ]----> GND    +-------------+
     |                                                                       ^
     +----------------------- MASSE COMUNI (GND) ----------------------------+
        ESP32-S3 GND <---> OLED GND <---> INMP441 GND <---> MAX98357A GND <---> Pulsante
```

---

## 2. Distinzione Funzionale delle Linee

### A. Alimentazione e Masse Comuni
- **`5V` (VBUS dalla DevKitC-1) → `MAX98357A VIN`:** alimenta esclusivamente lo stadio di potenza Classe-D dell'amplificatore.
- **`3V3` (uscita regolatore DevKitC-1) → `OLED VCC`, `INMP441 VDD`, `MAX98357A SD`:** alimenta la logica a 3,3 V. L'assorbimento combinato di OLED (~15–20 mA) e INMP441 (~1,4 mA) rientra ampiamente nei limiti del regolatore onboard.
- **`GND` comune:** tutti i riferimenti di massa (`ESP32-S3 GND`, `OLED GND`, `INMP441 GND`, `INMP441 L/R`, `MAX98357A GND`, un terminale del `Pulsante`) convergono sul bus `GND` della breadboard.
- **Avvertenza critica:** NON collegare il pin `RST`/`EN` (spesso adiacente a `3V3` sul lato sinistro `J1`) a massa.

### B. Bus I²C0 — Display OLED 1,3" (128×64)
| Da (ESP32-S3) | A (OLED 1,3") | Colore consigliato (28 AWG / Dupont) | Note |
|---|---|---|---|
| `3V3` | `VCC` | Rosso | Verificare ordine pin sulla serigrafia OLED |
| `GND` | `GND` | Nero | Massa comune |
| `GPIO 41` | `SDA` | Blu | Dati I²C (400 kHz) |
| `GPIO 42` | `SCL` | Giallo | Clock I²C |

### C. Bus I²S0 RX — Microfono Digitale INMP441
| Da (ESP32-S3) | A (INMP441) | Colore consigliato | Note |
|---|---|---|---|
| `3V3` | `VDD` | Rosso | **Mai collegare a 5 V** |
| `GND` | `GND` | Nero | Massa comune |
| `GND` | `L/R` | Nero | Seleziona canale **Left** (obbligatorio, non lasciare flottante) |
| `GPIO 4` | `WS` | Verde | Word Select / LRCLK |
| `GPIO 5` | `SCK` | Bianco | Bit Clock |
| `GPIO 6` | `SD` | Viola | Serial Data (mic → ESP32-S3) |

### D. Bus I²S1 TX — Amplificatore MAX98357A
| Da (ESP32-S3) | A (MAX98357A) | Colore consigliato | Note |
|---|---|---|---|
| `5V` | `VIN` | Rosso/Arancio | Alimentazione stadio audio 5 V |
| `GND` | `GND` | Nero | Massa comune |
| `3V3` | `SD` | Grigio | Abilitazione amplificatore (verificare datasheet del breakout ricevuto) |
| — | `GAIN` | — | Lasciare scollegato per guadagno default (`9 dB`) |
| `GPIO 7` | `DIN` | Verde | Dati audio digitali (ESP32-S3 → ampli) |
| `GPIO 15` | `BCLK` | Giallo | Bit Clock |
| `GPIO 16` | `LRC` | Blu | Left/Right Clock |

### E. Uscite Amplificate verso Speaker 4 Ω / 3 W (JST-PH2.0)
| Da (MAX98357A) | A (Speaker 4 Ω / 3 W) | Regole di Sicurezza |
|---|---|---|
| `OUT+` (`+`) | Filo positivo speaker (`+`) | **Collegare SOLO alle uscite del MAX98357A.** |
| `OUT-` (`-`) | Filo negativo speaker (`-`) | **MAI collegare `OUT-` o `OUT+` a `GND`.** L'uscita è a ponte differenziale (BTL); cortocircuitare un polo a massa danneggia l'amplificatore. **MAI collegare lo speaker direttamente ai GPIO dell'ESP32-S3.** |

### F. Pulsante Momentaneo Normalmente Aperto (NO)
| Da (ESP32-S3) | A (Pulsante) | Note |
|---|---|---|
| `GPIO 47` | Pin A del pulsante | `INPUT_PULLUP` interno attivo nel firmware (`active LOW`). |
| `GND` | Pin B del pulsante | Massa comune. |

---

## 3. Regole Pratiche per Breadboard e Cablaggio Definitivo (28 AWG)
1. **Separazione fisica dei cavi:** tenere i cavi audio dell'altoparlante (`OUT+`/`OUT-`) e l'alimentazione `5V` distanti dai cavi del microfono (`INMP441`) e del bus `I²C` per ridurre diafonia e ronzii.
2. **Lunghezza cavi:** su breadboard usare cavetti Dupont corti; nel montaggio definitivo dentro il corpo LEGO usare cavi flessibili **28 AWG** intestati con connettori **JST-PH2.0** (speaker) o saldature protette da guaina termorestringente.
3. **Nessun componente aggiuntivo obbligatorio** per la v1 su breadboard (pull-up I²C e pull-up pulsante sono già presenti rispettivamente su modulo OLED e internamente all'ESP32-S3), salvo verifica pratica durante il collaudo fisico.
