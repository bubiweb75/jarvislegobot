# FASE 11.3C.4C — Verifica finale prima del primo flash Wi-Fi

> **Esito complessivo**: **PRIMO FLASH AUTORIZZABILE** — Nessun problema bloccante rilevato. Nessun flash eseguito in questa fase; firmware stabile FASE 10.8 intatto.

---

## Tabella riepilogativa dei controlli

| # | Controllo | Esito | Dettaglio verificato |
|---|---|---|---|
| 1 | Regola firewall unica `JARVIS LEGO BOT - Voice Bridge WSS` | **PASS** | `Count=1`, `Enabled=True`, `Inbound`, `Allow`, `TCP 8765`, `Profile=Public`, `Remote=<LAN_IP>/24`, `Program=C:\Python314\python.exe` |
| 2 | Windows Defender Firewall attivo | **PASS** | `Domain=True`, `Private=True`, `Public=True` |
| 3 | Credenziali `wifi_secrets.h` senza placeholder | **PASS** | `SSID_SET=True`, `PASS_SET=True`, `HOST=<PC_LAN_IP>`, `PORT=8765` (nessun segreto stampato) |
| 4 | Configurazione TLS/WSS e token dispositivo | **PASS** | `TLS_1_INSEC_0=True`, `CA_PRESENT=True`, `TOKEN_SET=True` |
| 5 | Backup Flash 16 MB + SHA-256 | **PASS** | `%USERPROFILE%\Desktop\jarvis_flash_backups\jarvis_fase10_8_flash_backup.bin` (`16.777.216 B`, SHA-256 `43B9A85F6E1B9D3BCB32D25A58C179DA384AF6F7C379EA2315E9690F9A9015A9`) |
| 6 | Riconoscimento ESP32-S3 su `COM6` (solo lettura) | **PASS** | `COM6` libera (`CH343`), `ESP32-S3 (QFN56) v0.2`, `16MB` Flash, `8MB` PSRAM (riconfermato con `flash-id`) |
| 7 | Voice Bridge WSS/TLS su `<PC_LAN_IP>:8765` (stesso PC) | **PASS** | Handshake TLS con verifica rigorosa `rootCA.pem`, `auth_ok`, `ping`/`pong`, rifiuto token errato, `TOKEN_IN_LOGS=False`; server arrestato |
| 8 | Raggiungibilità `<PC_LAN_IP>:8765` da un secondo dispositivo LAN | **NON VERIFICATO** | Non eseguito da un secondo client esterno; verrà verificato direttamente con il primo collegamento reale dell'ESP32-S3 |
| 9 | Compilazione firmware con `wifi_secrets.h` definitivo | **PASS** | `arduino-cli compile` (`esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M`): `exit status 0`, Flash `1.154.733 B` (`88%` di `1.310.720 B` su schema `default`), RAM `54.980 B` (`16%`) |
| 10 | Sicurezza Git e integrità FASE 10.8 / infrastruttura | **PASS** | `wifi_secrets.h` e `.local_certs/` esclusi da Git (`git status --short`), FASE 10.8 intatta, nessuna modifica a router/Raspberry/NAS |

---

## Nota su partizioni e autorizzazione al flash

- La compilazione con `PartitionScheme=default` è riuscita (`88%`, `155.987 B` liberi). Se si desidera mantenere più margine per future evoluzioni su 16 MB, al momento del flash in **FASE 11.3C.5** è possibile usare `PartitionScheme=app3M_fat9M_16MB` (senza modificarlo automaticamente ora).
- **Nessun blocco residuo**: tutti i prerequisiti tecnici, di sicurezza e di backup sono soddisfatti per autorizzare la **FASE 11.3C.5 (Primo flash e collaudo Wi-Fi/WSS progressivo)**.
