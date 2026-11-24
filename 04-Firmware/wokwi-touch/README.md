# JARVIS LEGO BOT — Simulazione Wokwi Touch (FASE 11.1)

Variante sperimentale isolata per testare l'interazione tattile (`TouchManager` su **GPIO1**) insieme al firmware **Eyes 3.0** e al pulsante principale **GPIO47**, senza alterare `04-Firmware/wokwi-simulation` né `04-Firmware/wokwi-web`.

---

## Circuitazione Virtuale (`diagram.json`)

| Componente | Collegamento ESP32-S3 | Comportamento |
|---|---|---|
| **OLED `board-ssd1306` (`0x3C`)** | `SDA → GPIO41`, `SCL → GPIO42`, `VCC → 3V3`, `GND → GND.1` | 14 espressioni Eyes 3.0 (`128×64`) |
| **Pulsante Principale (`btn1`, blu)** | `GPIO47 → GND.2` (`INPUT_PULLUP`, tasto `Space`) | Breve: cambia espressione; Lunga ≥1,5 s: Auto-Demo ON/OFF |
| **Sensore Touch Virtuale (`btn_touch`, verde)** | `GPIO1 → 3V3` con pull-down `10 kΩ` verso `GND.3` (tasto `T`) | Replica l'uscita digitale attiva `HIGH` del `TTP223B` (nessuna capacità ABS simulata) |
| **Serial Monitor (`115200 baud`)** | `esp:TX` / `esp:RX` → `$serialMonitor` | Log eventi `EVENT:TOUCH_*` e comandi seriali |

---

## Procedura per provare i due pulsanti su Wokwi Online (Chrome)

1. Apri **https://wokwi.com/projects/new/esp32-s3**.
2. Nella scheda **`diagram.json`**, sostituisci tutto con il contenuto di [diagram.json](diagram.json).
3. Clicca nella scheda **`sketch.ino`**, premi **`F1`** e seleziona **`Upload Firmware and Start Simulation...`**.
4. Seleziona il firmware compilato:
   `04-Firmware\wokwi-touch\jarvis-esp32s3-wokwi-touch-merged.bin`
5. Prova i due pulsanti nella finestra di simulazione:
   - **Tocco singolo** (clic rapido sul pulsante verde `TOUCH GPIO1` o tasto **`T`**): dopo `350 ms` stampa `EVENT:TOUCH_SINGLE` → `HAPPY` (`2,2 s`) → ripristina lo stato precedente.
   - **Doppio tocco** (2 clic rapidi su **`T`** entro `350 ms`): stampa `EVENT:TOUCH_DOUBLE` → `MISCHIEVOUS` (`2,6 s`) → ripristina lo stato precedente.
   - **Tocco prolungato** (tieni premuto **`T`** ≥ `1,2 s` e poi rilascia): stampa `EVENT:TOUCH_LONG` → `LOVE` finché premuto + `1,8 s` dopo `EVENT:TOUCH_RELEASE` → ripristina lo stato precedente.
   - **Pulsante principale (`BTN GPIO47` / `Spazio`)**: continua a cambiare espressione o attivare/disattivare l'auto-demo (`1,5 s`), annullando eventuali reazioni tattili temporanee in corso.
   - **Stati prioritari** (es. invia `LISTENING`, `THINKING` o `SPEAKING` dal Serial Monitor e poi premi `T`): stampa `EVENT:TOUCH_IGNORED=BUSY` e non interrompe la conversazione.

> Per salvare il progetto nel tuo account Wokwi e condividere un link permanente, usa i file in `web-project/` (o `jarvis-wokwi-touch-web.zip`) aggiungendo `U8g2` nel Library Manager.
