# AUDIO_ARCHITECTURE — Strategia Audio USB v1 (FASE 6)

> **Obiettivo:** Definire come ESP32-S3 e PC Windows 11 si scambiano comandi OLED e flussi audio (microfono + speaker) su **un singolo cavo USB**, preservando `faster-whisper`, `Ollama qwen2.5:3b` e `Piper Riccardo (Amichetto Vivace)`.

---

## 1. Ripartizione dei Ruoli (v1 USB)

| Componente | Responsabilità nella v1 |
|---|---|
| **ESP32-S3-DevKitC-1 N16R8** | Rendering occhi OLED 128×64, acquisizione I²S0 (`INMP441`), riproduzione I²S1 (`MAX98357A` + Speaker 4 Ω / 3 W), lettura pulsante `GPIO 47`, framing USB-CDC |
| **PC Windows 11 (`05-Voice-AI/`)** | `faster-whisper` (STT), `Ollama qwen2.5:3b` (LLM), `Piper Riccardo` + `voice_dsp.py` (TTS), logica conversazione e invio comandi occhi |

Wi-Fi, Bluetooth e Raspberry Pi sono esclusi dalla v1 per mantenere bassa latenza e zero dipendenze di rete.

---

## 2. Analisi della Banda e Formati PCM

| Flusso | Formato consigliato | Banda grezza PCM | Banda con framing (~5%) |
|---|---|---|---|
| **Microfono (`INMP441` → PC)** | `16 kHz`, `16-bit signed`, `Mono` | `32.000 B/s` (`256 kbps`) | `~33,6 KB/s` |
| **Speaker (`PC → MAX98357A`)** | `16 kHz` (o `22,05 kHz`), `16-bit signed`, `Mono` | `32.000 B/s` (`44.100 B/s` a 22,05 kHz) | `~33,6 – 46,5 KB/s` |
| **Comandi Occhi + Telemetria** | Messaggi brevi asincroni | `< 1 KB/s` | `< 1 KB/s` |
| **Totale Full-Duplex** | Bidirezionale simultaneo | **~64 – 76 KB/s** | **< 80 KB/s** |

- Il protocollo solo testo a `115200 baud` (~11,5 KB/s reali su UART) **non** può trasportare audio PCM.
- La porta **`USB` nativa** (`GPIO 19/20`, `-DARDUINO_USB_CDC_ON_BOOT=1`) opera su **USB 2.0 Full-Speed (12 Mbps)** con throughput pratico di **400–800 KB/s**, gestendo facilmente l'audio full-duplex tramite il framing binario descritto in [USB_PROTOCOL.md](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/06-Hardware-Integration/USB_PROTOCOL.md).

---

## 3. Latenza, Buffering e Gestione Interruzioni (`Stop`)

1. **Ring buffer speaker su ESP32-S3:** `16 KB` (~500 ms a 16 kHz) con pre-buffer `60–80 ms` prima di avviare I²S1 TX.
2. **Backpressure (`SPK_FLOW`):** `PAUSE` sopra il 75% di riempimento, `RESUME` sotto il 35%.
3. **Stop immediato (`SPK_STOP`):** svuota il ring buffer, azzera il DMA I²S1 TX e riporta gli occhi a `IDLE` in `< 20 ms`.
4. **Anti-eco:** disabilita l'acquisizione `INMP441` durante `SPEAKING` fino a `SPK_DONE` / `SPK_STOP`.
