# USB_PROTOCOL — Specifica Protocollo Seriale Binario Multiplexato (FASE 6)

> **Obiettivo:** Trasportare simultaneamente comandi testuali degli occhi OLED, eventi pulsante, audio microfono e audio speaker su una singola connessione **USB-CDC** mantenendo piena compatibilità logica con i comandi di `eye_bridge.py` e `state_machine.cpp`.

---

## 1. Compatibilità con il Protocollo Esistente

Il firmware attuale (`04-Firmware/jarvis-desk-buddy`) e `SerialEyeTransport` (`05-Voice-AI/eye_bridge.py`) utilizzano righe ASCII terminate da `\n`:
- **PC → ESP32:** `STATE:IDLE`, `STATE:LISTENING`, `STATE:THINKING`, `STATE:SPEAKING`, `STATE:HAPPY`, `STATE:CURIOUS`, `STATE:SLEEPY`, `BLINK`, `LOOK:<dx>,<dy>`, `AUTO:ON`, `AUTO:OFF`, `HELP`.
- **ESP32 → PC:** `EVENT:STATE=<nome>`.

**Strategia di retrocompatibilità:**
- All'avvio, il firmware può restare in ascolto sia di righe ASCII (`STATE:...`) per test manuali da Serial Monitor (Test 1 e Test 2), sia passare automaticamente in **Modalità Framed Binaria** non appena riceve il preambolo binario `0xAA 0x55` (o un comando `PROTO:BIN`).
- I comandi testuali degli occhi continuano a usare esattamente le stesse stringhe, incapsulate nel payload del frame `0x01 CMD_TEXT`.

---

## 2. Formato del Frame Binario

Ogni pacchetto ha header fisso da **6 byte** + payload variabile (`0..1024` byte) + **CRC-16/CCITT (2 byte)**:

```text
+-------+-------+------+-----+-------+-------+------------------+--------+--------+
| SYNC0 | SYNC1 | TYPE | SEQ | LEN_L | LEN_H |     PAYLOAD      | CRC_L  | CRC_H  |
| 0xAA  | 0x55  |  u8  |  u8 |  u8   |  u8   |  0 .. 1024 byte  |  u8    |  u8    |
+-------+-------+------+-----+-------+-------+------------------+--------+--------+
```

- **`SYNC0, SYNC1` (`0xAA`, `0x55`):** sequenza di sincronizzazione per riallineamento rapido su byte persi.
- **`TYPE` (`uint8`):** identificativo del canale logico.
- **`SEQ` (`uint8`):** contatore progressivo `0..255` per rilevare eventuali pacchetti persi.
- **`LEN_L, LEN_H` (`uint16` little-endian):** lunghezza del `PAYLOAD` in byte (`<= 1024`).
- **`CRC_L, CRC_H` (`uint16` little-endian):** CRC-16-CCITT calcolato su `TYPE + SEQ + LEN_L + LEN_H + PAYLOAD`. Se il CRC non coincide, il ricevitore scarta il frame e cerca il successivo `0xAA 0x55`.

---

## 3. Tabella dei Tipi di Frame (`TYPE`)

| `TYPE` | Nome | Direzione | Payload | Frequenza / Uso |
|---|---|---|---|---|
| `0x01` | `CMD_TEXT` | PC → ESP32 | Stringa UTF-8/ASCII (es. `STATE:SPEAKING`) | Asincrono (comandi occhi) |
| `0x02` | `EVT_TEXT` | ESP32 → PC | Stringa UTF-8/ASCII (es. `EVENT:STATE=LISTENING`) | Asincrono (stati e log) |
| `0x03` | `BTN_EVENT` | ESP32 → PC | 1 byte: `0x01=PRESS`, `0x02=RELEASE`, `0x03=LONG_PRESS` | Push-to-Talk fisico `GPIO 47` |
| `0x10` | `AUDIO_MIC_PCM` | ESP32 → PC | PCM 16 kHz, 16-bit signed mono (`640 B` = 20 ms) | Continuo durante `LISTENING` (o stream attivo) |
| `0x11` | `MIC_CTRL` | PC → ESP32 | 1 byte: `0x00=STOP`, `0x01=START` | Avvio/arresto cattura `INMP441` |
| `0x20` | `AUDIO_SPK_PCM` | PC → ESP32 | PCM 16 kHz, 16-bit signed mono (`640 B` = 20 ms) | Streaming TTS da `Piper` |
| `0x21` | `SPK_FLOW` | ESP32 → PC | 1 byte: `0x00=PAUSE`, `0x01=RESUME` | Controllo flusso ring buffer |
| `0x22` | `SPK_STOP` | PC → ESP32 | 0 byte (vuoto) | **Stop immediato** + flush buffer I²S1 |
| `0x23` | `SPK_DONE` | ESP32 → PC | 0 byte (vuoto) | Segnala svuotamento ring buffer speaker |
| `0x30` | `PING` | Bidir. | 4 byte timestamp ms | Keepalive ogni `1000 ms` |
| `0x31` | `PONG` | Bidir. | 4 byte echo timestamp ms | Verifica link USB attivo |

---

## 4. Gestione Errori e Riconnessione USB

1. **Rilevamento disconnessione (PC):** se la scrittura su porta COM fallisce o non arrivano `PONG`/`PING` entro `3000 ms`, `jarvis_app.py` imposta lo stato ponte USB su `Scollegato` (senza bloccare la GUI o l'AI locale) e ritenta l'apertura della porta COM ogni `1500 ms`.
2. **Rilevamento disconnessione (ESP32-S3):** se non riceve `PING` o frame dal PC per `5000 ms` durante `SPEAKING`/`LISTENING`, svuota il buffer audio, ferma I²S1 TX e riporta gli occhi in `IDLE` (o `AUTO:ON` configurabile).
3. **Allineamento flusso:** in caso di byte spuri all'apertura della COM Windows, il parser scarta finché non trova `0xAA 0x55` con `LEN <= 1024` e CRC valido.
