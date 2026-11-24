# FASE 14.3 — Pubblicazione Ufficiale GitHub e Rilascio `v1.3.8-stable`

Data pubblicazione: `2026-11-24`

---

## 1. Riferimenti di Rilascio
- **Repository GitHub**: https://github.com/bubiweb75/jarvislegobot
- **Branch**: `main` (`main...origin/main` allineati)
- **Commit di rilascio (`v1.3.8-stable`)**: `fbc3fce669310f3a3c50daa7ba7ab4cd87d3fe65`
  - Messaggio: `release: consolidate JARVIS stable firmware 13.8 and robotics platform foundations`
  - File interessati: `1.050` modificati/aggiunti (`1.284` file totali nell'albero del commit)
- **Tag ufficiale**: `v1.3.8-stable` (oggetto tag `c508cdcdbd45ac446f09e734fc45642d229cf217` → `fbc3fce669310f3a3c50daa7ba7ab4cd87d3fe65`)
  - Link tag: https://github.com/bubiweb75/jarvislegobot/releases/tag/v1.3.8-stable
  - Nota: il tag identifica il firmware stabile collaudato **FASE 13.8**; `JARVIS-Robotics-Platform` rimane in sviluppo.

---

## 2. Risultati dei 144 Test e Verifiche Pre-Pubblicazione

| Suite / Verifica | Risultato | Note |
|---|---|---|
| **Voice Bridge (`05-Voice-AI/tests`)** | **`104/104` OK** (`26.04 s`) | Incluso `test_fase12_24_wsola_profile08.py` (`7/7` OK) dopo FASE 14.3A |
| **Prova negativa F0 (`pitch=0.0`)** | **Superata** | `ratio=1.0000` (`< 1.28`) e `139.1 Hz` (`< 180 Hz`) intercettati |
| **Unit test firmware (`test_fase13_4_logic.py`)** | **`6/6` OK** (`0.003 s`) | Transizioni, guardia `1500 ms`, DMA discard, VAD `300 ms`, `WriteZeroFlush` |
| **Backend `JARVIS-Robotics-Platform/tests`** | **`15/15` OK** (`0.030 s`) | Validazione schemi, profili, pinout e sicurezza |
| **Frontend `JARVIS-Robotics-Platform/frontend`** | **`19/19` OK** (`vitest`) + `tsc && vite build` OK (`4.58 s`) | Zero errori TypeScript/build |
| **Totale test automatici** | **`144/144` OK** | `104 + 6 + 15 + 19 = 144` |
| **ESP32-S3 `COM6` con Voice Bridge attivo** | **Verificato `IDLE`** | `[STAT] state=IDLE heap=129676 min_heap=122092 psram=6787504 rx_hwm=10228` |

---

## 3. Sicurezza, Dimensioni e Backup
- **Audit staging e albero `fbc3fce`**: `1.284` file totali, **`0` file sensibili** (`wifi_secrets.h`, `.env`, `.key`, `.pem`, `.db`, `.sqlite`, `backups/`, `node_modules/`, `.venv/`, `build/`, `.wav`), **`0` MAC address**, **`0` percorsi personali Windows**.
- **Dimensione complessiva albero di lavoro candidato**: `~124,76 MB` (max singolo file `18,25 MB`, ben sotto il limite GitHub `100 MB`).
- **Backup locali intatti (non pubblicati)**:
  - `05-Voice-AI/backups/fase13_8_stable/esp32_fase13_8_stable_full_16mb.bin` (`16.777.216` B, SHA-256 `2C11FAA2C39175DA3A9BA8B190B23E1FF319BB7262556B8EC6D5293856AD434E`, `EXACT_MATCH: True` con `fase13_8_app0.bin`)
  - `05-Voice-AI/backups/fase13_8_stable/fase13_8_app0.bin` (`1.299.328` B, SHA-256 `44A548EDB0A83A318CFE684F6455EFAE71AD3E30B636B2C6FD17ABF7B12BBE32`)
  - `05-Voice-AI/backups/fase13_2_preflash/fase12_27_app0_rollback.bin` (`1.310.720` B, SHA-256 `94E0B14E676E535685F960658C71D7324550A25A88AEB409D10B87A912418E47`)

---

## 4. Stato Finale Componenti e Limitazioni Residue
- **Firmware stabile (`FASE 13.8`, `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/`)**: collaudato e rilasciato su `v1.3.8-stable` (`Eyes 3.0`, wake word locale *«Hey Jarvis»*, `VAD` adattivo, protezione anti-ri-trigger, speaker silenzioso in `IDLE`, `GPIO47`, `STAT`, `WSS` TLS con `faster-whisper` + `Ollama qwen2.5:3b` + `Piper Profilo 08`).
- **Limitazioni tecniche residue**: partizione `app0` (`1.310.720` B) al `99%` (`11.392` B liberi); servizi STT/LLM/TTS eseguiti su PC Windows 11 in LAN.
- **JARVIS Robotics Platform (`JARVIS-Robotics-Platform/`)**: fondamenta architetturali, schemi, profili e simulatore frontend pubblicati nello stato **in sviluppo** (non ancora integrati sul robot fisico).
