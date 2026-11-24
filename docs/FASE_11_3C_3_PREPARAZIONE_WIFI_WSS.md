# FASE 11.3C.3 — Preparazione collegamento Wi-Fi sicuro (WSS/TLS)

> **Stato**: Configurazione TLS/WSS preparata e verificata localmente in loopback (`127.0.0.1`). Nessun flash eseguito, nessuna modifica applicata al firewall Windows, al router FRITZ!Box o al firmware stabile FASE 10.8.

---

## 1. Verifica preliminare backup e rete PC

- **Backup Flash FASE 10.8**:
  - Percorso: `%USERPROFILE%\Desktop\jarvis_flash_backups\jarvis_fase10_8_flash_backup.bin`
  - Esistenza e dimensione: **`16.777.216` byte** (`BACKUP_EXISTS=True`).
  - Integrità `SHA-256`: **`SHA256_MATCH=True`** (`43B9A85F6E1B9D3BCB32D25A58C179DA384AF6F7C379EA2315E9690F9A9015A9`).
- **Rete PC Windows riconfermata**:
  - Interfaccia `Wi-Fi`: **`<PC_LAN_IP>/24`** (subnet domestica `<LAN_IP>/24`).

## 2. Soluzione TLS/WSS verificata (`mkcert`)

- **CA locale rilevata**: `mkcert` (`mkcert development CA`, `CN=mkcert MINIPC\bcava@MiniPC (Bruno Cavallo)`) già presente sul PC.
- **Certificato server locale generato** (escluso da Git in `05-Voice-AI/.local_certs/`):
  - Certificato: `05-Voice-AI/.local_certs/jarvis_lan_cert.pem`
  - Chiave privata: `05-Voice-AI/.local_certs/jarvis_lan_key.pem`
  - **SAN verificati**: `DNS:localhost`, `IP Address:<PC_LAN_IP>`, `IP Address:127.0.0.1`
  - Validità: fino al `18 Feb 2029`.
- **Coerenza firmware ↔ backend**:
  - Firmware ([network_task.cpp](04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/network_task.cpp)): usa `g_ws.beginSslWithCA(host, port, ws_path, ca_cert)` con `JARVIS_WS_USE_TLS=1` e `JARVIS_ALLOW_INSECURE_LAN_WS=0` (verifica certificato CA attiva, subprotocol `"arduino"`).
  - Backend: `uvicorn voice_bridge.api:app --ssl-certfile .local_certs/jarvis_lan_cert.pem --ssl-keyfile .local_certs/jarvis_lan_key.pem`.

## 3. Sicurezza credenziali e `.gitignore`

- Aggiornato [.gitignore](.gitignore) aggiungendo solo `05-Voice-AI/.local_certs/`, `**/wifi_secrets.h` e `*.key` (lasciando versionato `wifi_secrets.example.h`).
- Creato localmente (non versionato, verificato con `git status --short`) `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/wifi_secrets.h` con:
  - `JARVIS_BRIDGE_HOST="<PC_LAN_IP>"`, `JARVIS_BRIDGE_PORT=8765`, `JARVIS_BRIDGE_WS_PATH="/ws/v1/esp32"`.
  - `JARVIS_ESP_TOKEN` generato casualmente e **separato** da `JARVIS_BRIDGE_TOKEN` (nessun segreto riportato in log o report).
  - `JARVIS_WS_USE_TLS=1`, `JARVIS_ALLOW_INSECURE_LAN_WS=0` e `JARVIS_WS_CA_CERT` contenente la sola CA pubblica (`1739` caratteri).
  - Placeholder `YOUR_WIFI_SSID` / `YOUR_WIFI_PASSWORD` da compilare localmente dall'utente prima del flash.

## 4. Test eseguiti

1. **Test reale WSS/TLS su loopback `127.0.0.1`** (`uvicorn` + `websockets` + `ssl.create_default_context(cafile=rootCA.pem)` + `subprotocols=["arduino"]`):
   - `WSS_TLS_HANDSHAKE_OK=True`
   - `WSS_AUTH_AND_PING_OK=True`
   - `TOKEN_IN_SERVER_OUTPUT=False` (nessuna esposizione del token nei log).
2. **Compilazione firmware con `wifi_secrets.h` e CA TLS integrata** (`arduino-cli compile --fqbn esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M`):
   - **`exit status 0`** (`1.154.749 B` Flash `88%`, `54.980 B` RAM `16%`).

## 5. Configurazione firewall e server LAN preparata (NON applicata)

1. **Regola firewall Windows** (profilo `Private`, sola subnet `<LAN_IP>/24`, porta TCP `8765`):
   ```powershell
   New-NetFirewallRule -DisplayName "JARVIS Voice Bridge LAN (TCP 8765)" `
     -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765 `
     -RemoteAddress <LAN_IP>/24 -Profile Private
   ```
2. **Avvio server LAN WSS** (con `JARVIS_ESP_DEVICE_TOKEN` letto da `wifi_secrets.h` locale e `JARVIS_BRIDGE_TOKEN` distinto per il browser):
   ```powershell
   Set-Location "05-Voice-AI"
   $env:JARVIS_BRIDGE_HOST = "0.0.0.0"
   $env:JARVIS_BRIDGE_PORT = "8765"
   $env:JARVIS_BRIDGE_REQUIRE_AUTH = "true"
   # impostare JARVIS_BRIDGE_TOKEN e JARVIS_ESP_DEVICE_TOKEN in sessione
   & ".\.venv\Scripts\python.exe" -m uvicorn voice_bridge.api:app `
     --host 0.0.0.0 --port 8765 `
     --ssl-certfile .local_certs\jarvis_lan_cert.pem `
     --ssl-keyfile .local_certs\jarvis_lan_key.pem
   ```

## 6. Rischi residui e autorizzazioni necessarie

- **Rischi residui**:
  - `JARVIS_WIFI_SSID` e `JARVIS_WIFI_PASSWORD` in `wifi_secrets.h` hanno ancora valori placeholder e vanno inseriti localmente prima del flash.
  - Con `build.partitions=default` lo sketch è all'`88%` (`1.154.749 B / 1.310.720 B`); su 16 MB resta consigliato `PartitionScheme=app3M_fat9M_16MB` se autorizzato al flash.
  - Il collegamento WSS reale da ESP32-S3 (`mbedTLS`) verso `uvicorn` è stato verificato da client Python ma **non ancora dalla scheda fisica**.
- **Autorizzazioni necessarie per la fase successiva (FASE 11.3C.4)**:
  1. Inserimento locale di SSID/password Wi-Fi reali in `wifi_secrets.h` (da parte dell'utente o su sua indicazione locale).
  2. Applicazione della regola firewall Windows per `<LAN_IP>/24` porta `8765` e avvio del server `uvicorn` WSS su `0.0.0.0:8765`.
  3. Autorizzazione esplicita al flash su `COM6` (eventualmente con `PartitionScheme=app3M_fat9M_16MB`).
