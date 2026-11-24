# FASE 11.3C.1 — Backup firmware stabile e preparazione collaudo Wi-Fi

> **Stato**: Procedura operativa verificata prima del collegamento fisico della scheda. Nessun flash eseguito, nessuna cancellazione Flash, nessuna modifica al firmware stabile FASE 10.8, al firewall Windows, al router FRITZ!Box o al Raspberry Pi.

---

## 1. Strumenti verificati sul PC Windows

- **`esptool.exe`**: versione **`5.3.1`** presente in:
  `%USERPROFILE%\AppData\Local\Arduino15\packages\esp32\tools\esptool_py\5.3.1\esptool.exe`
- **`arduino-cli.exe`**: presente in:
  `C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe`
- **Core ESP32**: `esp32:esp32 3.3.13`
- **Indirizzo IPv4 LAN rilevato sul PC Windows**: `<PC_LAN_IP>/24` (interfaccia `Wi-Fi`, subnet `<LAN_IP>/24`).
- **Nota `.gitignore`**: `wifi_secrets.h` non è ancora elencato in `.gitignore`; prima di creare `wifi_secrets.h` o certificati locali (`*.pem`, `*.key`), aggiungerli a `.gitignore`.

## 2. Procedura di backup completo Flash 16 MB (da eseguire a scheda collegata)

Collegare l'ESP32-S3-DevKitC-1 N16R8 tramite cavo USB dati (alimentazione solo USB del PC) e identificare la porta `COM<N>` con `Get-CimInstance Win32_SerialPort`.

1. **Verifica identità Flash (`16 MB` = `0x1000000` byte)**:
   ```powershell
   $ESPTOOL = "$env:LOCALAPPDATA\Arduino15\packages\esp32\tools\esptool_py\5.3.1\esptool.exe"
   & $ESPTOOL --chip esp32s3 --port COM<N> flash-id
   ```
2. **Lettura completa della Flash (`0x0` → `0x1000000`)** in una directory locale fuori da Git (es. `%USERPROFILE%\Desktop\jarvis_flash_backups\`):
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\Desktop\jarvis_flash_backups" | Out-Null
   $BACKUP = "$env:USERPROFILE\Desktop\jarvis_flash_backups\esp32s3_fase10_8_full16mb.bin"
   & $ESPTOOL --chip esp32s3 --port COM<N> --baud 921600 read-flash 0x0 0x1000000 $BACKUP
   ```
   *(Se `921600` desse errori di sincronizzazione USB-UART, ripetere a `--baud 460800`.)*

## 3. Verifica integrità del backup (SHA-256 + seconda lettura opzionale)

Verificare che il file sia esattamente `16.777.216` byte (`16 MiB`) e calcolarne l'impronta SHA-256:

```powershell
(Get-Item $BACKUP).Length
Get-FileHash $BACKUP -Algorithm SHA256 | Tee-Object -FilePath "$BACKUP.sha256"
```

Conservare sia `.bin` sia `.sha256`. Prima di un eventuale ripristino, ricontrollare `Get-FileHash` confrontandolo con il file `.sha256`.

## 4. Ripristino del firmware stabile FASE 10.8

- **Opzione A — Ripristino integrale immagine 16 MB (include partizioni, NVS, bootloader e firmware 10.8)**:
  ```powershell
  & $ESPTOOL --chip esp32s3 --port COM<N> --baud 460800 write-flash 0x0 $BACKUP
  ```
- **Opzione B — Ricompilazione e upload diretto del progetto stabile FASE 10.8** (`jarvis_duplex_rtos_hw_test/` non modificato):
  ```powershell
  & "C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe" compile --upload -p COM<N> --fqbn esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M "04-Firmware\arduino-hw-test\jarvis_duplex_rtos_hw_test"
  ```

## 5. Configurazione firmware Wi-Fi e compilazione ESP32-S3

- **FQBN di riferimento**: `esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M`
  *(Per il flash definitivo su 16 MB si raccomanda di autorizzare `PartitionScheme=app3M_fat9M_16MB` per portare l'app dal `87%` su `default` al ~`36%`.)*
- **Credenziali locali**: copiare `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/wifi_secrets.example.h` in `wifi_secrets.h` (non versionato), inserendo:
  - `JARVIS_WIFI_SSID` / `JARVIS_WIFI_PASSWORD` (solo in `wifi_secrets.h` locale)
  - `JARVIS_BRIDGE_HOST` = `"<PC_LAN_IP>"` (IP LAN attuale del PC)
  - `JARVIS_BRIDGE_PORT` = `8765`
  - `JARVIS_ESP_DEVICE_TOKEN` = `<token_dispositivo_dedicato>` (diverso da `JARVIS_BRIDGE_TOKEN`)

## 6. Configurazione WSS e sicurezza

- **Canale consigliato (WSS con CA locale)**:
  - Generare localmente (fuori da Git) una CA privata + certificato server per `<PC_LAN_IP>` (`SAN = IP:<PC_LAN_IP>`).
  - Avviare `uvicorn` con `--ssl-certfile` e `--ssl-keyfile`.
  - Inserire il certificato PEM della sola CA pubblica in `JARVIS_WS_CA_CERT` dentro `wifi_secrets.h` e impostare `JARVIS_WS_USE_TLS 1`, `JARVIS_ALLOW_INSECURE_LAN_WS 0`.
- **Alternativa temporanea solo se autorizzata (`ws://` LAN)**: `JARVIS_WS_USE_TLS 0` e `JARVIS_ALLOW_INSECURE_LAN_WS 1` (espone il token dispositivo al traffico LAN locale).
- Il token dispositivo non viene mai stampato su Serial né nei log del backend (`BridgeDiagnostics` lo redige automaticamente).

## 7. Verifiche di rete e firewall (NON applicate in questa fase)

1. Consentire TCP in ingresso sulla porta `8765` nel firewall Windows **esclusivamente** per il profilo Privato e per la subnet locale `<LAN_IP>/24`.
2. Avviare il Voice Bridge con profilo LAN esplicito:
   - `JARVIS_BRIDGE_HOST=0.0.0.0`
   - `JARVIS_BRIDGE_PORT=8765`
   - `JARVIS_ESP_DEVICE_TOKEN=<token_dispositivo_dedicato>`
   - `JARVIS_BRIDGE_TOKEN=<token_browser_separato>`

## 8. Piano di collaudo progressivo (FASE 11.3C.2+)

1. **Step 1 — Avvio hardware**: verifica log seriali (`115200 baud`), PSRAM (`g_rx_buffer` `160 KB`, `g_tx_buffer` `640 KB`, `tts_buf_` `640 KB`), `INMP441`, `MAX98357A`, `OLED SH1106` e `Eyes 3.0` (`IDLE`).
2. **Step 2 — Connessione Wi-Fi**: verifica transizione `WIFI_CONNECTING` → `WIFI_CONNECTED` e assegnazione IP LAN.
3. **Step 3 — Autenticazione WebSocket**: verifica `auth` → `auth_ok` → `IDLE` e heartbeat `ping`/`pong` ogni `15 s` senza blocco animazioni OLED.
4. **Step 4 — Registrazione e upload**: pressione/rilascio `GPIO47`, invio `audio_start` + chunk binari `2048 B` + `audio_end`.
5. **Step 5 — Elaborazione e riproduzione TTS**: verifica `Local Intent` (*"Ciao Jarvis, che ore sono?"*) → Piper TTS → ricezione `tts_start` / chunk binari / `tts_end` → riproduzione pulita su `MAX98357A`.
6. **Step 6 — STOP/CANCEL**: pressione `GPIO47` durante `PLAYING` o `PROCESSING`.

## 9. Criteri di arresto e ripristino immediato

Interrompere il collaudo e ripristinare subito il backup FASE 10.8 (Sezione 4) se si verifica uno di questi casi:
- Boot-loop, guru meditation / panic CPU o fallimento allocazione PSRAM.
- Distorsione grave I²S o blocco evidente delle animazioni `Eyes 3.0`.
- Errori ripetuti di connessione/autenticazione non spiegati da configurazione LAN.
- Surriscaldamento anomalo o assorbimento anomalo sulla porta USB.

## 10. Autorizzazioni necessarie prima di eseguire operazioni fisiche

1. Collegamento fisico USB della scheda ESP32-S3 ed esecuzione del backup completo `16 MB` + verifica `SHA-256`.
2. Scelta tra `WSS` (CA locale) o `ws://` LAN temporaneo e creazione di `wifi_secrets.h` locale (più aggiornamento `.gitignore`).
3. Apertura regola firewall Windows TCP `8765` per `<LAN_IP>/24` (profilo Privato) e avvio `jarvis-voice-bridge` su `0.0.0.0:8765`.
4. Flash del firmware isolato `jarvis_wifi_voice_client` (eventualmente con `PartitionScheme=app3M_fat9M_16MB`).
