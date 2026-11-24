# JARVIS LEGO BOT — FASE 10.8: Acquisizione & Riproduzione Audio FreeRTOS + Eyes 3.0

Variante isolata con **doppio task FreeRTOS dedicato** (`jarvis_audio_rx` su `I2S_NUM_0` e `jarvis_audio_tx` su `I2S_NUM_1`), che mantiene **Eyes 3.0 animati** sia durante `LISTENING` che durante `PLAYING` senza interferenze I²C OLED.

- **Preserva integralmente**: `04-Firmware/jarvis-desk-buddy/`, `jarvis_voice_hw_test`, `jarvis_duplex_hw_test`, `jarvis_audio_diag_hw_test` e i progetti Wokwi.

---

## 1. Architettura FreeRTOS

| Task | Core | Priorità | Stack | Funzione |
|---|---|---|---|---|
| **`jarvis_audio_rx`** (`AudioCapture`) | `0` | `3` | `4096 B` | Legge `I2S_NUM_0` (`GPIO4/5/6`, `16 kHz`, 32→16 bit), scrive in `AudioBuffer` (PSRAM) durante `LISTENING` |
| **`jarvis_audio_tx`** (`AudioPlayback`) | `0` | `3` | `4096 B` | Legge `AudioBuffer` (PSRAM), riproduce su `I2S_NUM_1` (`GPIO15/16/7`, `16 kHz`, vol `3%`, max `15%`) durante `PLAYING` |
| **`loopTask`** (Arduino `loop()`) | `1` | `1` | default | `EyeController` (SH1106 `0x3C`, `GPIO41/42`), `ButtonController` (`GPIO47`), `SerialCommands`, `StateMachine` |

- **Sincronizzazione e proprietà buffer**:
  - `AudioCapture` e `AudioPlayback` operano in **half-duplex sequenziale** (`LISTENING` → `PROCESSING` → `PLAYING`).
  - `StartRecording()` / `StopRecording()` e `Start()` / `Stop()` usano `ulTaskNotifyTake(pdTRUE, portMAX_DELAY)` (`0%` CPU in idle), `xSemaphoreCreateBinary()` (`done_sem_` con timeout `150 ms` per arresto garantito prima di qualsiasi riproduzione) e `portMUX_TYPE` (`mux_`) per proteggere flag e metriche condivise.

---

## 2. Diagnostica (`[DIAG_RX]` e `[DIAG_TX]`)

- **`[DIAG_RX]`**: `MIN`, `MAX`, `DC24`, `RMS`, `PEAK`, `SAT` (conteggio e `%`), `CLIP`, `SAMPLES`, `DUR`, `ELAPSED`, `EST_LOSS` *(stima: `max(0, ELAPSED * 16 - SAMPLES)`)*, `RX_ERR`, `PARTIAL`, `TIMEOUTS`, `MAX_GAP`, `INTER>30ms`, `INTER>90ms`, `BUF_FULL`.
- **`[DIAG_TX]`**: `BYTES`, `PARTIAL`, `TX_ERR`, `MAX_GAP`, `MAX_WRITE`, `MAX_INTER_WRITE`, `INTER>30ms`, `INTER>90ms`, `MAX_OLED`.

---

## 3. Procedura di Collaudo su Hardware Reale (Arduino IDE 2)

1. Apri `04-Firmware\arduino-hw-test\jarvis_duplex_rtos_hw_test\jarvis_duplex_rtos_hw_test.ino`.
2. Imposta: `ESP32S3 Dev Module`, `Flash Size: 16MB (128Mb)`, `Flash Mode: QIO 80MHz`, **`PSRAM: OPI PSRAM`**, `USB CDC On Boot: Disabled` (UART CH343) o `Enabled` (USB nativa).
3. Carica e apri il **Monitor Seriale** a **`115200 baud`**.
4. **Checklist test richiesti**:
   - [ ] `TONE_TEST` con Eyes 3.0 animati (`MAX_INTER_WRITE < 2 ms`, `INTER>30ms=0`, tono pulito).
   - [ ] `LOOPBACK_TEST` con Eyes 3.0 animati anche durante `LISTENING`: verificare `SAMPLES ≈ 48.000` (`DUR ≈ 3.000 ms`, `EST_LOSS` minimo/nullo, `INTER>30ms=0`) e **voce pulita**.
   - [ ] Confronto opzionale `LOOPBACK_TEST_NO_OLED`.
   - [ ] Pulsante `GPIO47`: pressione breve (`< 300 ms`), Push-to-Talk (`2–3 s`), limite `5 s`.
   - [ ] `5` cicli consecutivi registrazione/riproduzione verificando `MEMORY` e assenza di deadlock/riavvii.
   - [ ] `STOP` durante `RECORD` / `LISTENING` e `STOP` durante `PLAY` / `PLAYING`.
