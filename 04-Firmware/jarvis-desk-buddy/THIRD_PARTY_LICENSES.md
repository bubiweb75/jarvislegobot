# Third-Party Licenses & Attribution Audit

Questo documento registra l'analisi delle licenze dei repository GitHub studiati per la realizzazione del firmware **JARVIS AI Desk Buddy** (`04-Firmware/jarvis-desk-buddy`) e le relative attribuzioni.

---

## 1. Riepilogo Repository Studiati

| Repository | Licenza Rilevata | Codice Riutilizzato / Adattato | Stato Conformità |
| :--- | :--- | :--- | :--- |
| **`Carmoruda/Jarvis`** (`github.com/Carmoruda/Jarvis`) | **MIT License** (`Copyright (c) 2026 Carmoruda`) | Architettura di rendering non bloccante degli occhi (`Eye` struct, mascheratura palpebre, `BlinkPhase`, `UpdateBlinker` e movimenti `Idle`) adattata e riscritta in `include/eye_engine.h` e `src/eye_engine.cpp`, con aggiunta delle espressioni *Curious*, *Listening*, *Thinking*, *Speaking* e dei comandi seriali per Raspberry Pi. | ✅ **Conforme** (avviso MIT preservato sotto e nelle intestazioni dei file `eye_engine.h` / `eye_engine.cpp`) |
| **`FamousWolf/deskbuddy`** (`github.com/FamousWolf/deskbuddy`) | **MIT License** (`Copyright (c) 2024 Rudy Gnodde`) | Studiato solo a livello concettuale (mappatura degli stati d'animo del companion). Poiché usa ESPHome + display LCD a colori 2,4" su ESP32-S3-Box-3, **nessun codice è stato copiato**. | ✅ **Conforme** |
| **`StefanRiese/blinky-desk-companion`** (`github.com/StefanRiese/blinky-desk-companion`) | **Nessuna licenza dichiarata** (*All Rights Reserved* di default) | Studiato solo ad alto livello architetturale per l'idea di separazione tra stato UI sull'ESP32-S3 e protocollo seriale verso un host esterno (*Buddy Link*). **Zero righe di codice copiate.** | ✅ **Conforme** (implementazione 100% originale in `state_machine.h/.cpp`) |

---

## 2. Librerie di Terze Parti (PlatformIO `lib_deps`)

- **`olikraus/U8g2`** (`^2.35.30`): rilasciata sotto **BSD-2-Clause License** (`Copyright (c) 2016, olikraus@gmail.com`). Utilizzata tramite PlatformIO per la gestione nativa I²C di **SH1106** (`U8G2_SH1106_128X64_NONAME_F_HW_I2C`) e **SSD1306/SSD1106** (`U8G2_SSD1306_128X64_NONAME_F_HW_I2C`).

---

## 3. Testo Integrale Licenza MIT — `Carmoruda/Jarvis`

```text
Copyright (c) 2026 Carmoruda

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
