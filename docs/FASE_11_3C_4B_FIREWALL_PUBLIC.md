# FASE 11.3C.4B — Configurazione firewall sicura mantenendo la rete Pubblica

> **Stato**: Verifiche preliminari completate; **azione manuale/UAC richiesta** per creare la regola firewall (la sessione corrente non ha privilegi amministrativi: `IS_ADMIN=False`). Nessuna modifica applicata al profilo `Public`, al firewall, al router o al firmware stabile FASE 10.8.

---

## 1. Stato verificato

- **Profilo rete Windows**: `FRITZ!Box 7590 BR 2` (`Wi-Fi`) confermato su **`Public`**.
- **IPv4 LAN PC**: **`<PC_LAN_IP>/24`** (subnet domestica `<LAN_IP>/24`).
- **Backup Flash FASE 10.8**: presente (`16.777.216` byte) e `SHA-256` verificato (`BACKUP_OK=True`).
- **Regole firewall esistenti su TCP `8765`**: **`0`** (`RULES_ON_8765=0`).
- **Eseguibile reale in ascolto**: `05-Voice-AI\.venv\Scripts\python.exe` è il launcher del virtualenv che avvia **`C:\Python314\python.exe`** (`sys._base_executable`).

## 2. Regola firewall da approvare manualmente (PowerShell come Amministratore)

Aprire **PowerShell come Amministratore** (approvando il prompt UAC di Windows) ed eseguire esattamente:

```powershell
New-NetFirewallRule -DisplayName "JARVIS LEGO BOT - Voice Bridge WSS" `
  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765 `
  -RemoteAddress <LAN_IP>/24 -Profile Public `
  -Program "C:\Python314\python.exe"
```

Verifica dopo la creazione:
```powershell
Get-NetFirewallRule -DisplayName "JARVIS LEGO BOT - Voice Bridge WSS" |
  Select-Object DisplayName, Enabled, Direction, Action, Profile
```

## 3. Procedura di rollback

Per rimuovere esattamente la regola creata (da PowerShell come Amministratore):
```powershell
Remove-NetFirewallRule -DisplayName "JARVIS LEGO BOT - Voice Bridge WSS"
```

## 4. Verifiche LAN/WSS e credenziali Wi-Fi

- **Verifica WSS su IP LAN `<PC_LAN_IP>:8765`**: già superata nella FASE 11.3C.4 (`LAN_WSS_AUTH_PING_OK=True`, rifiuto token errati/browser `UNAUTHORIZED`, `ESP_TOKEN_IN_LOGS=False`).
- **Verifica da un secondo dispositivo della rete**: in attesa dell'approvazione UAC della regola firewall sopra indicata.
- **Credenziali Wi-Fi (`wifi_secrets.h`)**: `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/wifi_secrets.h` contiene tuttora i placeholder `YOUR_WIFI_SSID` e `YOUR_WIFI_PASSWORD`. Prima del primo flash, l'utente deve aprirlo localmente con un editor e sostituire esclusivamente quelle due righe con SSID e password reali della propria rete Wi-Fi, senza condividerle in chat.

## 5. Prerequisiti ancora mancanti per il primo flash

1. Creazione della regola firewall `JARVIS LEGO BOT - Voice Bridge WSS` tramite PowerShell come Amministratore.
2. Inserimento locale di SSID e password Wi-Fi reali in `wifi_secrets.h`.
3. Autorizzazione esplicita al flash di `jarvis_wifi_voice_client` su `COM6` (`PartitionScheme=app3M_fat9M_16MB` consigliato).
