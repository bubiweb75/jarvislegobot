# FASE 11.3C.11 — Miglioramento riconoscimento vocale italiano (`small/int8` + `"che ora sono"`)

> **Stato**: Preparazione completata e Voice Bridge attivo con `small/int8` (`PID 13276` su `https://<PC_LAN_IP>:8765`, `JARVIS_LOG_STT_DIAG_TEXT=false`). **In attesa del collaudo reale sulle 4 frasi da parte dell'utente.**

---

## 1. Verifiche preliminari e benchmark locale (`FASE A`)

- **Cache modello `small`**: `SMALL_CACHED=True` (`faster-whisper pronto (modello 'small', CPU int8)`).
- **RAM PC**: `15,39 GB` totali, `5,88 GB` disponibili.
- **Benchmark controllato su campione sintetico Piper in RAM** (`"Ciao Jarvis, che ore sono?"`, nessuna registrazione microfono):
  - `base/int8`: `load=367 ms`, `inf=2231 ms`, trascritto=`'Ciao ciao, già riuscura su!'`
  - `small/int8`: `load=2234 ms`, `inf=2033 ms`, trascritto=`'Ciao Jarvis, che ora sono?'`
  *(Nota: campione sintetico di riferimento; il confronto definitivo richiede il collaudo vocale reale sull'ESP32.)*

## 2. Modifiche applicate (`FASE B–C`)

- [local_intents.py](05-Voice-AI/voice_bridge/local_intents.py): aggiunte le varianti `"che ora sono"`, `"mi dici che ora sono"`, `"dimmi che ora sono"` all'intento `time`, senza regole permissive (frasi corrotte come `"Medici che è rsono"` e domande generiche restano escluse).
- [test_voice_lab.py](05-Voice-AI/tests/test_voice_lab.py): aggiunto `test_24_local_intent_che_ora_sono_and_no_false_positives`.
- Configurazione permanente (`config.py` / `.env`): invariata (`base` resta il default su file per rollback immediato; `small` attivato solo nella sessione corrente tramite `JARVIS_STT_MODEL="small"`).

## 3. Test automatici e stato Voice Bridge

- `unittest tests/test_esp32_ws_protocol.py tests/test_voice_bridge.py tests/test_voice_lab.py -v`: **29 test OK** (0 errori, 0 fallimenti).
- Server precedente `PID 8100`: arrestato ordinatamente (`STOPPED_PID_8100=True`).
- Nuovo Voice Bridge `PID 13276` (`task-3456`): attivo su `https://<PC_LAN_IP>:8765`, WSS/TLS, `JARVIS_STT_MODEL=small`, `JARVIS_LOG_STT_DIAG_TEXT=false`, `Ollama=false`, `Cloud=false`.
- `READY=True` (`faster-whisper pronto (modello 'small', CPU int8)`), `SMALL_WSS_AUTH_PING_OK=True`, ESP32-S3 (`<ESP32_LAN_IP>`) riconnesso automaticamente.

## 4. Collaudo vocale reale richiesto (`FASE D`)

Pronunciare in sequenza sul pulsante `GPIO47` del robot:
1. `"Ciao Jarvis, che ore sono?"`
2. `"Mi dici che ore sono?"`
3. `"Che giorno è oggi?"`
4. `"Dimmi che ore sono adesso."`

## 5. Rollback immediato a `base/int8`

In caso di errori o consumi/latenze eccessive con `small/int8`:
1. `Stop-Process -Id 13276`
2. Riavviare `uvicorn` con `$env:JARVIS_STT_MODEL="base"` (nessun file permanente modificato).
