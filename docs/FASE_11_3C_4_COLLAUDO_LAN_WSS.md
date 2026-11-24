# FASE 11.3C.4 — Attivazione controllata LAN e verifica WSS

> **Stato**: Collaudo LAN/WSS locale (`<PC_LAN_IP>:8765`) **superato** su server temporaneo arrestato al termine. Nessun flash eseguito, nessuna modifica applicata al firewall Windows, nessuna modifica al firmware stabile FASE 10.8.

---

## 1. Verifica preliminare completata

- **Rete Windows**:
  - Interfaccia `Wi-Fi` (`FRITZ!Box 7590 BR 2`): **`<PC_LAN_IP>/24`** (subnet `<LAN_IP>/24`).
  - **Rilevamento importante**: il profilo di rete Windows attuale della connessione `Wi-Fi` è **`Public`** (`NetworkCategory: Public`), non `Private`.
- **Porta `8765`**: libera prima e dopo il test (`PORT_8765_IN_USE=False`).
- **Backup Flash FASE 10.8**: presente (`16.777.216` byte) e `SHA-256` corrispondente (`BACKUP_OK=True`).
- **Certificato TLS**: `05-Voice-AI/.local_certs/jarvis_lan_cert.pem` contiene SAN `IP Address:<PC_LAN_IP>`, `IP Address:127.0.0.1`, `DNS:localhost`.
- **Credenziali locali (`wifi_secrets.h`)**:
  - Token dispositivo `JARVIS_ESP_TOKEN` configurato (`ESP_TOKEN_CONFIGURED=True`), distinto dal token browser.
  - `JARVIS_WIFI_SSID` e `JARVIS_WIFI_PASSWORD` risultano ancora placeholder (`SSID_IS_PLACEHOLDER=True`, `PASS_IS_PLACEHOLDER=True`) e andranno compilati localmente prima del flash.

## 2. Firewall Windows (NON applicato in questa fase)

- **Regole esistenti**: `EXISTING_FW_RULES=0` per `JARVIS` / `8765`.
- **Azione preparata (richiede autorizzazione esplicita)**:
  1. Impostare il profilo della rete domestica `FRITZ!Box 7590 BR 2` su `Private` (necessario perché la regola `-Profile Private` si applichi senza esporre reti pubbliche):
     ```powershell
     Set-NetConnectionProfile -InterfaceAlias "Wi-Fi" -NetworkCategory Private
     ```
  2. Creare la regola in ingresso limitata a TCP `8765`, profilo `Private` e subnet `<LAN_IP>/24`:
     ```powershell
     New-NetFirewallRule -DisplayName "JARVIS Voice Bridge LAN (TCP 8765)" `
       -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765 `
       -RemoteAddress <LAN_IP>/24 -Profile Private
     ```
- **Rollback / rimozione regola**:
  ```powershell
  Remove-NetFirewallRule -DisplayName "JARVIS Voice Bridge LAN (TCP 8765)"
  ```

## 3. Collaudo WSS sull'IP LAN (`<PC_LAN_IP>:8765`)

Avviato temporaneamente `uvicorn voice_bridge.api:app --host <PC_LAN_IP> --port 8765` con TLS `mkcert` attivo (e terminato subito dopo il test):

- **Handshake WSS sull'IP LAN** (`wss://<PC_LAN_IP>:8765/ws/v1/esp32`, verifica rigorosa `rootCA.pem`, `subprotocols=["arduino"]`): **`LAN_WSS_AUTH_PING_OK=True`**.
- **Rifiuto token errato**: **`LAN_WSS_WRONG_TOKEN_REJECTED=True`** (`UNAUTHORIZED`).
- **Rifiuto token browser su endpoint ESP32**: **`LAN_WSS_BROWSER_TOKEN_REJECTED=True`** (`UNAUTHORIZED`).
- **Voice Lab HTTPS** (`https://<PC_LAN_IP>:8765/health` e `/`): **`LAN_HTTPS_HEALTH_AND_VOICELAB_OK=True`**.
- **Assenza segreti nei log**: `ESP_TOKEN_IN_LOGS=False`, `BROWSER_TOKEN_IN_LOGS=False`.
- *(Nota: nessun secondo dispositivo fisico è stato usato in questa fase perché la porta `8765` sul firewall resta chiusa fino ad autorizzazione.)*

## 4. Verifiche finali

- `unittest tests/test_esp32_ws_protocol.py tests/test_voice_bridge.py tests/test_voice_lab.py -v`: **26 test OK**.
- `PORT_8765_STILL_OPEN=False` (nessun processo temporaneo rimasto attivo).
- Nessun flash eseguito, nessuna partizione modificata, firmware stabile FASE 10.8 intatto.

## 5. Condizioni per autorizzare il primo flash (FASE 11.3C.5)

1. L'utente inserisce localmente `JARVIS_WIFI_SSID` e `JARVIS_WIFI_PASSWORD` reali in `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/wifi_secrets.h` (mai riportati in chat/report).
2. Autorizzazione esplicita a impostare `NetworkCategory Private` su `Wi-Fi` e creare la regola firewall per `<LAN_IP>/24` TCP `8765`.
3. Autorizzazione ad avviare il server `uvicorn` WSS su `<PC_LAN_IP>:8765` (o `0.0.0.0:8765`) durante il collaudo.
4. Autorizzazione esplicita al flash di `jarvis_wifi_voice_client` su `COM6` (consigliato `PartitionScheme=app3M_fat9M_16MB`).
