# FASE 11.3C.12 — Consolidamento Whisper `small/int8` e analisi volume audio

> **Stato**: Analisi completata e proposta tecnica pronta. Nessuna modifica applicata al firmware ESP32, nessun flash, nessun riavvio del Voice Bridge (`PID 13276` tuttora attivo con `small/int8`).

---

## 1. Esito del collaudo reale (`4/4` risposte corrette)

Dalle 4 prove vocali reali eseguite su ESP32-S3 (`<ESP32_LAN_IP>`) con Whisper `small/int8` (`PID 13276`, `task-3456.log`):

| # | Frase pronunciata | Request ID | Provider | Durata | RMS | Picco | Tempo STT | Tempo AI | Tempo TTS | Totale |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `"Ciao Jarvis, che ore sono?"` | `req_85a59acefa59` | `Local Intent` | `2.77 s` | `3958` | `32767` | `4277.4 ms` *(primo carico)* | `0.6 ms` | `603.2 ms` | `4895.1 ms` |
| 2 | `"Mi dici che ore sono?"` | `req_1d804438bd22` | `Local Intent` | `2.29 s` | `2779` | `23371` | `2841.4 ms` | `1.1 ms` | `597.1 ms` | `3451.5 ms` |
| 3 | `"Che giorno è oggi?"` | `req_c120bd20db20` | `Local Intent` | `2.34 s` | `3329` | `23151` | `2844.4 ms` | `0.7 ms` | `684.3 ms` | `3543.8 ms` |
| 4 | `"Dimmi che ore sono adesso."` | `req_e970b93aed5d` | `Local Intent` | `2.43 s` | `3622` | `25701` | `2852.5 ms` | `0.6 ms` | `595.5 ms` | `3461.2 ms` |

- **Verifica configurazione attiva**: `JARVIS_STT_MODEL=small`, `JARVIS_LOG_STT_DIAG_TEXT=false` (nessuna trascrizione presente in `task-3456.log`).
- **Memoria utilizzata dopo le 4 inferenze (`PID 13276`)**:
  - `WorkingSet`: **`402,39 MB`**
  - `PrivateMemory`: **`897,91 MB`** (su `15,39 GB` totali del PC).
- **Latenza STT a regime (`small/int8`)**: ~`2,84–2,85 s` su CPU Ryzen 7 5700U (primo turno `4,28 s` comprensivo del caricamento lazy del modello); tempo totale turno ~`3,45–3,54 s`.
- **Rollback a `base/int8`**: immediato impostando `JARVIS_STT_MODEL="base"` (il default in `config.py` è tuttora `"base"`).

## 2. Ripristino dopo eventuale riavvio del PC Windows

Senza introdurre servizi automatici, per ripristinare la configurazione consolidata dopo un riavvio del PC:
1. Avviare da `05-Voice-AI/` con `.venv\Scripts\python.exe` `uvicorn voice_bridge.api:app --host <PC_LAN_IP> --port 8765 --ssl-certfile .local_certs\jarvis_lan_cert.pem --ssl-keyfile .local_certs\jarvis_lan_key.pem` impostando `JARVIS_STT_MODEL="small"`, `JARVIS_TIMEZONE="Europe/Rome"`, `JARVIS_ESP_DEVICE_TOKEN` (da `wifi_secrets.h`), `JARVIS_OLLAMA_ENABLED="false"`, `JARVIS_CLOUD_ENABLED="false"`.
2. La regola firewall `JARVIS LEGO BOT - Voice Bridge WSS` è già persistente sul profilo `Public`.

## 3. Diagnostica catena audio e causa del volume basso

Analisi misurata lungo l'intera catena `Piper TTS → PCM16 → Voice Bridge → WSS → ESP32-S3 → I2S → MAX98357A → speaker 4Ω/3W`:

1. **Piper TTS (lato PC)**:
   - `"Sono le 19 e 18."`: `16.000 Hz`, `1 ch`, **`RMS = 5435 (16,6%)`**, **`Picco = 32767 (100,0%)`**.
   - `"Oggi è mercoledì 18 novembre 2026."`: `16.000 Hz`, `1 ch`, **`RMS = 7946 (24,3%)`**, **`Picco = 32767 (100,0%)`**.
   - **Conclusione lato PC**: Piper genera già audio a piena dinamica (`peak=32767`); `esp_protocol.py` trasmette i frame PCM16 senza alcuna attenuazione. Amplificare lato server causerebbe clipping certo.
2. **Firmware ESP32-S3 (`AudioPlayback` in `audio_playback.h` / `audio_playback.cpp`)**:
   - **Causa confermata**: `AudioPlayback` imposta `kDefaultVolumePct = 3` (`3%`!) e `kMaxVolumePct = 15` (`15%`).
   - Applicare il `3%` di volume digitale a una voce con `RMS 16,6%` riduce il segnale inviato a `I2S_NUM_1` a **`RMS ≈ 163` (`0,5%` del fondo scala, circa `-30 dB`)**.
3. **Altre cause possibili (secondarie)**:
   - Posizione interna dello speaker rispetto alla griglia LEGO (eventuale smorzamento acustico meccanico) e configurazione hardware del pin `GAIN` del modulo MAX98357A (non modificata né presunta).

## 4. Proposta tecnica di miglioramento (in attesa di autorizzazione)

- **Intervento lato PC**: **nessuno** su guadagno/normalizzazione Piper (già al `100%` di picco).
- **Intervento minimo e sicuro lato firmware isolato (`04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` esclusivamente, mai su FASE 10.8)**:
  1. Portare in `audio_playback.h` `kDefaultVolumePct` da `3` a **`10`** (`10%`, incremento di ~`+10,5 dB` rispetto al `3%`, molto conservativo per speaker `4Ω/3W` alimentato via USB 5V) e `kMaxVolumePct` da `15` a **`25`**.
  2. Aggiungere un comando seriale non bloccante `VOL <1..25>` in `jarvis_wifi_voice_client.ino` (richiamando `g_playback.SetVolumePct(pct)`) per confrontare in sicurezza livelli `3%` → `10%` → `15%` → `20%` senza riflashare.
  3. **Rollback**: `VOL 3` su seriale o ripristino `kDefaultVolumePct = 3`.
- **Piano di test dopo autorizzazione**:
  1. Compilazione isolata e upload di `jarvis_wifi_voice_client` su `COM6`.
  2. Confronto uditivo a `3%` (baseline), `10%` (nuovo default) e `15%` su frase Piper reale, verificando assenza di distorsione, clip o reset USB.
