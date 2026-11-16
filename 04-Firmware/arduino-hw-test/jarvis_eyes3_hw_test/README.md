# JARVIS LEGO BOT — Collaudo Hardware Eyes 3.0 (Arduino IDE 2)

Cartella isolata utilizzata per il primo collaudo reale di **Eyes 3.0** su **ESP32-S3-DevKitC-1 N16R8** + **OLED SH1106 128×64 I²C** (`0x3C`, `SDA=GPIO41`, `SCL=GPIO42`).

- **Non modifica** `04-Firmware/jarvis-desk-buddy/` né i progetti Wokwi.
- **Esclude** `TouchManager` (`GPIO1`) e sensori non collegati (`SensorBridgeStub` inattivo).
- **Mantiene** tutte le 14 espressioni, Natural Gaze, Advanced Blink, transizioni, profili (`CALM`, `LIVELY`, `PLAYFUL`), comandi seriali e `GPIO47` (`INPUT_PULLUP`, sicuro anche se scollegato).

---

## 1. Esito Collaudo Reale

**Superati su hardware reale:**
- Riconoscimento ESP32-S3 da Windows via USB.
- OLED SH1106 `128×64` I²C rilevato e funzionante all'indirizzo `0x3C` (`SDA=GPIO41`, `SCL=GPIO42`).
- Compilazione e caricamento tramite Arduino IDE 2.
- Animazioni automatiche Eyes 3.0 funzionanti.
- Comandi seriali funzionanti (incluso `STATE:HAPPY`).
- Pulsante `GPIO47`: pressione breve (cambio espressione) e pressione lunga `≥ 1500 ms` (`EVENT:AUTO_DEMO=ON` confermato su Monitor Seriale).

**Da eseguire successivamente:**
- Verifica individuale di tutte le 14 espressioni e profili su OLED reale.
- Collaudo fisico `TTP223B` (`GPIO1`), `INMP441` (`GPIO4/5/6`) e `MAX98357A` (`GPIO7/15/16`).

Rapporto completo: `docs/FASE_10_2_COLLAUDO_HW_EYES_3_0.md`.

---

## 2. Configurazione in Arduino IDE 2

1. Apri `04-Firmware\arduino-hw-test\jarvis_eyes3_hw_test\jarvis_eyes3_hw_test.ino`.
2. Nel menu **Strumenti (Tools)** imposta:
   - **Board**: `ESP32S3 Dev Module`
   - **Flash Size**: `16MB (128Mb)`
   - **Flash Mode**: `QIO 80MHz`
   - **PSRAM**: `OPI PSRAM`
   - **Partition Scheme**: `Default 4MB with spiffs` (oppure `16M Flash (3MB APP/9.9MB FATFS)`)
   - **Upload Speed**: `921600` (o `460800` se necessario)
   - **Port**: la porta COM dell'ESP32-S3

| Porta fisica usata sulla DevKitC-1 | Impostazione **USB CDC On Boot** | Note |
|---|---|---|
| **Porta UART (bridge CH343, es. COM4)** | **`Disabled`** (`ARDUINO_USB_CDC_ON_BOOT=0`) | Log su chip UART/CH343 (`115200 baud`). |
| **Porta USB nativa (OTG)** | **`Enabled`** (`ARDUINO_USB_CDC_ON_BOOT=1`) | Log su CDC USB nativa (`115200 baud`). |

---

## 3. Nota sul comportamento della pressione lunga (`GPIO47`)

In `state_machine.cpp`:
- La soglia `kLongPressMs = 1500` attiva il toggle `EVENT:AUTO_DEMO=ON|OFF` mentre il pulsante è ancora premuto (`≥ 1,5 s`), resettando `last_demo_switch_ms_ = now_ms`.
- Il primo cambio automatico di espressione avviene quindi `5 s` (`kDemoIntervalMs`) dopo il trigger, ed è immediatamente confermabile sul Monitor Seriale tramite `EVENT:AUTO_DEMO=ON` / `EVENT:AUTO_DEMO=OFF`.
