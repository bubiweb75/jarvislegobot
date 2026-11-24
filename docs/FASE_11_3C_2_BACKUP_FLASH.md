# FASE 11.3C.2 — Backup integrale della Flash ESP32-S3

> **Stato**: **COMPLETATO CON SUCCESSO** — Backup integrale da `16 MB` (`16.777.216` byte) acquisito e verificato con `SHA-256`. Nessuna operazione di scrittura o cancellazione eseguita sulla Flash; firmware stabile FASE 10.8 intatto.

---

## 1. Identificazione scheda e porta COM

- **Porta utilizzata**: `COM6` (`USB-Enhanced-SERIAL CH343`, porta **UART** hardware della scheda; la porta `USB` nativa `COM7` interrompeva la lettura stub a `0x00071000` / `462.848 B`).
- **Chip**: `ESP32-S3 (QFN56) (revision v0.2)`
- **Features**: `Wi-Fi, BT 5 (LE), Dual Core + LP Core, 240MHz, Embedded PSRAM 8MB (AP_3v3)`
- **MAC**: `<ESP32_MAC_ADDRESS>`
- **Flash rilevata**: **`16MB`** (`Manufacturer: 68`, `Device: 4018`, `quad`, `3.3V`)

## 2. Backup eseguito (`esptool v5.3.1`)

- **Comando**:
  `esptool.exe --chip esp32s3 --port COM6 --baud 460800 read-flash 0x0 0x1000000 "%USERPROFILE%\Desktop\jarvis_flash_backups\jarvis_fase10_8_flash_backup.bin"`
- **Durata**: `410,9 s` (`326,7 kbit/s`)
- **File salvato (fuori da Git)**: `%USERPROFILE%\Desktop\jarvis_flash_backups\jarvis_fase10_8_flash_backup.bin`
- **File verifica hash**: `%USERPROFILE%\Desktop\jarvis_flash_backups\jarvis_fase10_8_flash_backup.bin.sha256`
- **Dimensione esatta verificata**: **`16.777.216` byte** (`16 MiB` esatti)
- **SHA-256 verificato**:
  `43B9A85F6E1B9D3BCB32D25A58C179DA384AF6F7C379EA2315E9690F9A9015A9`
- **Nota sulla seconda lettura**: la prima lettura completa da `16 MB` è terminata con successo (`exit status 0`, `16.777.216` byte esatti) in `410,9 s`; una seconda lettura di ripetibilità (~`7 min`) non è stata avviata automaticamente ma può essere eseguita su richiesta prima del flash.

## 3. Comando di ripristino preparato (NON eseguito)

```powershell
$ESPTOOL = "$env:LOCALAPPDATA\Arduino15\packages\esp32\tools\esptool_py\5.3.1\esptool.exe"
$BACKUP = "$env:USERPROFILE\Desktop\jarvis_flash_backups\jarvis_fase10_8_flash_backup.bin"
& $ESPTOOL --chip esp32s3 --port COM6 --baud 460800 write-flash 0x0 $BACKUP
```
*(Verificare prima che `(Get-FileHash $BACKUP -Algorithm SHA256).Hash` corrisponda a `43B9A85F6E1B9D3BCB32D25A58C179DA384AF6F7C379EA2315E9690F9A9015A9`.)*
