# FASE 11.3C.8 — Riavvio controllato Voice Bridge e collaudo vocale

> **Stato**: Riavvio controllato completato (`PID 13428` attivo su `https://<PC_LAN_IP>:8765`). L'ESP32-S3 (`<ESP32_LAN_IP>`) si è riconnesso automaticamente via WSS/TLS. In attesa del collaudo vocale reale dell'utente sulle 4 frasi previste.

---

## 1. Operazioni eseguite

1. **Verifica e arresto processo precedente**:
   - Confermato che `PID 11300` era l'istanza `uvicorn voice_bridge.api:app` su `<PC_LAN_IP>:8765` (nessun altro servizio sulla porta `8765`).
   - Arrestato esclusivamente `PID 11300` (`STOPPED_PID_11300=True`).
2. **Riavvio Voice Bridge aggiornato (`PID 13428`)**:
   - Avviato da `05-Voice-AI/.venv/Scripts/python.exe` su `<PC_LAN_IP>:8765` con WSS/TLS (`jarvis_lan_cert.pem` / `jarvis_lan_key.pem`), `JARVIS_STT_MODEL="base"`, `JARVIS_TIMEZONE="Europe/Rome"`, `JARVIS_OLLAMA_ENABLED="false"`, `JARVIS_CLOUD_ENABLED="false"`.
3. **Verifiche immediate**:
   - `WSS_RECONNECT_AUTH_PING_OK=True` (handshake TLS rigoroso con `rootCA.pem`, `auth` → `auth_ok`, `ping` → `pong`).
   - Riconnessione automatica dell'ESP32-S3 osservata nei log del server:
     `INFO: <ESP32_LAN_IP>:50702 - "WebSocket /ws/v1/esp32" [accepted]` (`connection open`).
   - Nessuna credenziale o token nei log.

## 2. Collaudo vocale richiesto all'utente (sul pulsante `GPIO47` del robot)

Pronunciare in sequenza le 4 frasi seguenti (le prime 3 attese su `Local Intent`, la 4ª attesa su `offline_fallback` con motore AI disabilitato):

1. `"Ciao Jarvis, che ore sono?"`
2. `"Mi dici che ore sono?"`
3. `"Che giorno è oggi?"`
4. `"Come ti chiami?"`

Al termine, confermare per ispezionare i nuovi log diagnostici (`provider`, `dur`, `rms`, `peak`, `stt`, `ai`, `tts`, `total`) generati su `task-3399` (`PID 13428`) e aggiornare i risultati reali.
