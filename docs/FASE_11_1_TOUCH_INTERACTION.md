# FASE 11.1 — Touch Interaction (Sensore Tattile e Reazioni Emotive)

## 1. Architettura e Isolamento

La FASE 11.1 introduce `TouchManager` (`04-Firmware/jarvis-desk-buddy/include/touch_manager.h`, `src/touch_manager.cpp`) integrato in `StateMachine` (`state_machine.h` / `state_machine.cpp`) **esclusivamente** quando è attivo il flag di build `-DJARVIS_ENABLE_TOUCH=1`.

- Quando `JARVIS_ENABLE_TOUCH` **non** è definito (`esp32s3_sh1106`, `esp32s3_ssd1306`, `esp32s3_wokwi`), il comportamento del firmware resta identico alla baseline precedente.
- `Eyes 3.0` (`EyeEngine`), le 14 espressioni, `GPIO47`, `04-Firmware/wokwi-simulation`, `04-Firmware/wokwi-web` e `05-Voice-AI` restano invariati.

---

## 2. GPIO Utilizzati

| Funzione | GPIO ESP32-S3 | Modalità | Note |
|---|---|---|---|
| **OLED SDA / SCL** | `GPIO41` / `GPIO42` | I²C0 `400 kHz` | Invariato |
| **Pulsante principale** | `GPIO47` | `INPUT_PULLUP` (attivo `LOW`) | Invariato |
| **Sensore Touch (`TTP223B`)** | **`GPIO1`** | `INPUT` (attivo `HIGH`) | Lascia liberi `GPIO8/9` per `I2C_EXT` della futura Base Mobile B2 |

---

## 3. Gestione Eventi e Temporizzazioni (`TouchManager`)

Parametri di default (`TouchConfig`):
- `active_high = true`
- `debounce_ms = 40` (rimbalzi `< 40 ms` scartati)
- `double_tap_window_ms = 350` (finestra dopo il primo rilascio)
- `long_press_ms = 1200` (soglia pressione prolungata)

Comportamento deterministico non bloccante (zero `delay()`):
- **`TOUCH_SINGLE`**: confermato **solo** allo scadere della finestra `350 ms` dopo il primo rilascio senza secondo tocco (nessun doppio evento `SINGLE` + `DOUBLE`).
- **`TOUCH_DOUBLE`**: emesso al rilascio del secondo tocco breve entro `350 ms` dal primo rilascio.
- **`TOUCH_LONG`**: emesso una sola volta al raggiungimento di `1200 ms` di pressione continua.
- **`TOUCH_RELEASE`**: emesso al rilascio di qualsiasi pressione stabile; se era attivo `TOUCH_LONG`, avvia la coda di `1800 ms` prima del ripristino.

---

## 4. Priorità degli Eventi e Integrazione Eyes 3.0

1. **Stati conversazionali attivi (`LISTENING`, `THINKING`, `SPEAKING`)**: le reazioni tattili vengono **scartate** (`EVENT:TOUCH_IGNORED=BUSY`) per non interrompere ascolto, pensiero o parlato ed evitare code illimitate.
2. **Comandi espliciti (`GPIO47`, `STATE:*`, `AUTO:*`)**: annullano immediatamente eventuali reazioni tattili temporanee.
3. **Risveglio (`SLEEPING`, `SLEEPY`)**: al termine della reazione tattile JARVIS torna sveglio su `IDLE`/`NEUTRAL`.
4. **Mappatura reazioni**:
   - `TOUCH_SINGLE` → `HAPPY` (`2200 ms`) → `EVENT:TOUCH_RESTORE=<expr>`
   - `TOUCH_DOUBLE` → `MISCHIEVOUS` (`2600 ms`) → `EVENT:TOUCH_RESTORE=<expr>`
   - `TOUCH_LONG` → `LOVE` (finché premuto + `1800 ms` dopo `TOUCH_RELEASE`) → `EVENT:TOUCH_RESTORE=<expr>`

---

## 5. Simulazione Wokwi (`04-Firmware/wokwi-touch/`)

- Variante isolata con `esp32s3_wokwi_touch`, `board-ssd1306` (`0x3C`), `btn1` (`GPIO47`, tasto `Space`), `btn_touch` (`GPIO1 → 3V3` con `r_touch` `10 kΩ → GND`, tasto `T`).
- Immagine browser pronta: `04-Firmware/wokwi-touch/jarvis-esp32s3-wokwi-touch-merged.bin` (oltre a `web-project/` e `jarvis-wokwi-touch-web.zip`).
- **Limite della simulazione**: `btn_touch` replica esclusivamente il segnale digitale `HIGH/LOW` del `TTP223B`, **non** la capacità attraverso plastica ABS LEGO né eventuali interferenze I²S/Wi-Fi.

---

## 6. Collegamento Futuro del `TTP223B` Reale e Verifiche Elettriche

- Collegamenti previsti: `VCC → 3V3`, `GND → GND`, `OUT → GPIO1` (senza `INPUT_PULLUP` interno).
- Prima del montaggio fisico: verificare serigrafia e polarità del modulo acquistato (default `A=0, B=0` → uscita momentanea attiva `HIGH`), non toccare l'elettrodo nei primi `0,5 s` di autocalibrazione al boot, e collaudare la sensibilità reale attraverso il brick/tile LEGO scelto con audio `MAX98357A` attivo.

---

## 7. Checklist Test Manuali Wokwi (Utente)

1. Avvio simulazione su `wokwi.com` con `diagram.json` + `.bin` merged.
2. Verifica occhi animati Eyes 3.0.
3. Tocco singolo (`T`) → `EVENT:TOUCH_SINGLE` → `HAPPY` → ripristino.
4. Doppio tocco (`T` × 2 rapido) → `EVENT:TOUCH_DOUBLE` → `MISCHIEVOUS` → ripristino.
5. Tocco prolungato (`T` ≥ `1,2 s`) → `EVENT:TOUCH_LONG` → `LOVE` → `EVENT:TOUCH_RELEASE` → ripristino.
6. Verifica pulsante `GPIO47` (`Space`) e ciclo automatico.
7. Verifica priorità (`STATE:LISTENING` → `T` → `EVENT:TOUCH_IGNORED=BUSY`).
