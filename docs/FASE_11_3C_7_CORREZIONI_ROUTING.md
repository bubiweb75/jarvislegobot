# FASE 11.3C.7 — Correzione Local Intent, Offline Fallback e diagnostica

> **Stato**: Correzioni applicate e verificate con test automatici (`121` test verdi). Il server Voice Bridge attivo per il robot (`task-3345`, `PID 11300` su `<PC_LAN_IP>:8765`) **non è stato interrotto**; occorre riavviarlo su autorizzazione per rendere operative le modifiche sul robot.

---

## 1. File modificati

1. [local_intents.py](05-Voice-AI/voice_bridge/local_intents.py):
   - Esteso `_PREFIX_RE` per rimuovere saluti iniziali opzionali (`ciao`, `ehi`, `hey`, `salve`, `ok`, `buongiorno`, `buonasera`, `scusa`, `scusami`) anche senza `"jarvis"`.
   - Aggiunto `_SUFFIX_RE` per rimuovere espressioni di cortesia/tempo finali (`per favore`, `per piacere`, `grazie`, `adesso`, `subito`, `scusa`) senza intaccare `"l'ora"`.
   - Esteso `LocalIntentHandler.try_handle` alle parafrasi naturali su ora, giorno e data (`"Mi dici che ore sono?"`, `"Dimmi che ore sono"`, `"Che ore sono adesso?"`, `"Mi dici l'ora per favore?"`, `"Qual è la data di oggi?"`, ecc.), mantenendo il rifiuto netto di domande generiche e trascrizioni corrotte.
2. [offline_fallback.py](05-Voice-AI/voice_bridge/offline_fallback.py):
   - Corretto l'ordine di valutazione in `OfflineFallbackProvider.generate_reply`: le richieste esplicite di ora (`"che ore sono"`, `"che ora è"`, `"che ora e"`) vengono valutate **prima** dei saluti generici (`"ciao"`, `"buongiorno"`, ecc.).
   - Invariato il fallback per le domande generiche che richiedono un motore AI.
3. [diagnostics.py](05-Voice-AI/voice_bridge/diagnostics.py) e [pipeline.py](05-Voice-AI/voice_bridge/pipeline.py):
   - Configurato uno `StreamHandler` singolo su `logging.getLogger("jarvis.voice_bridge")` (`propagate = False`, livello default `INFO`, nessun handler duplicato).
   - `VoiceBridgeService.process_voice` registra su console solo metriche tecniche non sensibili (`provider`, `fallback`, `dur`, `rms`, `peak`, `stt`, `ai`, `tts`, `total`, oltre ai codici di `BridgeError`), senza mai stampare trascrizioni, audio, token o chiavi.
4. [test_voice_lab.py](05-Voice-AI/tests/test_voice_lab.py):
   - Aggiunto `test_22_local_intent_paraphrases_offline_order_and_safe_diagnostics`.

## 2. Test eseguiti e risultati (`05-Voice-AI/.venv/Scripts/python.exe`)

- `unittest tests/test_esp32_ws_protocol.py tests/test_voice_bridge.py tests/test_voice_lab.py -v`: **27 test OK** (inclusi tutti i 6 test WebSocket ESP32 invariati + tutte le frasi richieste e i casi negativi).
- `unittest tests/test_control_center.py tests/test_conversation_engine.py tests/test_conversation_naturalizer.py tests/test_memory_engine.py tests/test_voice_ai.py -v`: **50 test OK**.
- `unittest test_behavior_engine.py test_sensor_manager.py test_simulator.py test_touch_manager.py -v` (`04-Firmware/jarvis-desk-buddy-sim`): **44 test OK**.
- **Totale**: **121 test OK**, nessuna regressione rilevata.

## 3. Procedura per rendere operative le modifiche sul Voice Bridge

Il server attualmente in esecuzione (`PID 11300`, `https://<PC_LAN_IP>:8765`) ha in memoria i moduli precedenti alle modifiche. Per attivare le correzioni senza toccare firmware, firewall o configurazioni di rete:

1. Terminare esclusivamente il processo server precedente (`Stop-Process -Id 11300`).
2. Riavviare `uvicorn voice_bridge.api:app --host <PC_LAN_IP> --port 8765 --ssl-certfile .local_certs\jarvis_lan_cert.pem --ssl-keyfile .local_certs\jarvis_lan_key.pem` con le stesse variabili d'ambiente (`JARVIS_ESP_DEVICE_TOKEN` letto da `wifi_secrets.h`, `JARVIS_STT_MODEL="base"`, `JARVIS_TIMEZONE="Europe/Rome"`, `JARVIS_OLLAMA_ENABLED="false"`, `JARVIS_CLOUD_ENABLED="false"`).
3. Verificare la riconnessione automatica dell'ESP32-S3 e ripetere il test vocale sul pulsante `GPIO47`.
