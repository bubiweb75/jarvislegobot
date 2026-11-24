# FASE 14.1 — Audit Generale del Repository e Preparazione GitHub

Data audit: `2026-11-24` | Repository locale: `main @ 53f1bce` | Remoto: `https://github.com/bubiweb75/jarvislegobot` (`origin/main @ 7c33314`, locale `ahead 1`).

---

## 1. Verifiche Conclusive FASE 13.8

- **Backup integrale 16 MB**: `05-Voice-AI/backups/fase13_8_stable/esp32_fase13_8_stable_full_16mb.bin`
  - Dimensione verificata: **`16.777.216` byte** (`16 MB` esatti)
  - SHA-256 verificato: `2C11FAA2C39175DA3A9BA8B190B23E1FF319BB7262556B8EC6D5293856AD434E`
- **Estrazione virtuale `app0` dal dump (`0x10000`, `1.299.328` B)**:
  - SHA-256 estratto: `44A548EDB0A83A318CFE684F6455EFAE71AD3E30B636B2C6FD17ABF7B12BBE32`
  - Confronto con `05-Voice-AI/backups/fase13_8_stable/fase13_8_app0.bin`: **`EXACT_MATCH: True`** (identità byte-per-byte confermata).
- **Stato `ESP32-S3` su `COM6` post-dump**:
  - Scheda attiva e responsiva al comando `STAT`: `[STAT] state=WIFI_CONNECTING heap=168088 min_heap=167584 psram=6787364 rx_hwm=11428 noise=180 thr=432`.
  - Nota: nei 6 s di osservazione non è stato raggiunto `IDLE` in quanto Voice Bridge / servizio locale non erano avviati in questa sessione di sola analisi.
- **Differenza SHA-256 tra build collaudata (`44A548ED...`) e build riprodotta (`08600E64...`)**:
  - Entrambi i binari hanno dimensione identica su disco (`1.299.328` B, RAM globale `55.972` B), ma **non sono dichiarati byte-identici**.
  - `esp_app_desc` a offset `0x20` riporta i metadati del core precompilato (`arduino-lib-builder`, IDF `v5.5.6`), mentre lo sketch promosso (`jarvis_wifi_voice_client.ino`) ha percorso/nome file diverso rispetto allo sketch sperimentale (`fase13_3-integrated.ino`): questo modifica le stringhe di percorso (`__FILE__`) e l'hash ELF incorporato nell'immagine ESP32.

---

## 2. Inventario Completo del Progetto

Totale sul disco (escluso `.git`): `~25.815` file (~`2,31 GB` inclusi `.venv`, `node_modules`, modelli e backup).

| Percorso | File | MB | Classificazione |
|---|---:|---:|---|
| `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` | 30 | ~0.5 | **Firmware stabile** (FASE 13.8) |
| `04-Firmware/experiments/fase13-wakeword/` | — | — | **Firmware sperimentale** (prototipo isolato FASE 13.1–13.2) |
| `04-Firmware/experiments/fase13_3-integrated/` | — | — | **Firmware sperimentale** (base FASE 13.3–13.7, con `build/` locale) |
| `04-Firmware/archive/fase12_27_jarvis_wifi_voice_client/` | 25 | ~0.1 | **Versioni archiviate** (ex stabile FASE 12.27) |
| `04-Firmware/jarvis-desk-buddy/` + `jarvis-desk-buddy-sim/` | — | — | **Firmware storico OLED/USB** + simulatore Python Eyes 2.0/3.0 |
| `04-Firmware/arduino-hw-test/*_hw_test/` + `esp32s3-diag-test/` | — | — | **Test e diagnostica** hardware singoli moduli (I²S, mic, speaker) |
| `04-Firmware/wokwi-*` | — | — | **Simulazioni Wokwi** (`wokwi-simulation`, `wokwi-touch`, `wokwi-web`, `wokwi-gpio1-diag`) |
| `05-Voice-AI/voice_bridge/`, `prompts/`, `tests/`, `*.py` | — | — | **Voice Bridge e servizi AI** (`faster-whisper`, `Ollama`, `Piper`, Control Center) |
| `05-Voice-AI/tts-lab/` | — | ~1300 | **Voice Bridge / modelli / campioni audio** (`bin/`, `models/`, `samples_fase12_*`) |
| `05-Voice-AI/backups/` | — | ~40 | **Backup** Flash 16 MB e immagini `app0` (escluso da GitHub) |
| `05-Voice-AI/.venv/`, `.local_certs/`, `data/` | — | — | **Ambiente locale / certificati / DB** (esclusi da GitHub) |
| `06-Hardware-Integration/` + `JARVIS_GPIO_MAPPING_PCB_V1.md` | 15+1 | 0.23 | **Progettazione elettronica** (pinout, schemi, guida montaggio, FASE 8 sensori) |
| `JARVIS_CARRIER_BOARD_V1_FINAL/` + `JARVIS_CARRIER_BOARD_V1_PRODUZIONE/` (+ `.zip`) | 86+2 | 6.9 | **PCB carrier board e Gerber** (con `.zip` duplicati) |
| `03-Mechanical-Design/` | 34 | 71.67 | **Progettazione meccanica LEGO** (`.mpd`, `.ldr`, istruzioni) + **contenitore 3D** (se presente STL/STEP) + `05-Mobile-Electronics/` (espansioni) |
| `JARVIS-Robotics-Platform/` | 9211 | 151.07 | **Espansione futura** (piattaforma robotica + `frontend/node_modules/` + `.venv/` non ignorato) |
| `docs/` | 82 | 33.58 | **Documentazione** (manuali PDF, report FASE 1–14) |
| `archive/` | 118 | 2.74 | **Versioni archiviate** (`01-Hardware`, `02-LEGO`, `legacy-mechanical-design`) |
| `Start_JARVIS_Control_Center.bat`, `README.md`, `.gitignore` | 3 | 0.01 | **Root / avvio / config Git** |

---

## 3. Struttura Attuale vs Struttura Proposta (FASE 14.2)

### Principi
- Mantenere la numerazione esistente (`03-Mechanical-Design/`, `04-Firmware/`, `05-Voice-AI/`, `06-Hardware-Integration/`, `docs/`, `archive/`).
- **Nessuno spostamento eseguito in FASE 14.1**.

### Struttura proposta
- `01-Hardware/` → *(resta in `archive/01-Hardware/`, attivo in `06-Hardware-Integration/`)*
- `02-PCB-Carrier-Board/` *(oppure `06-Hardware-Integration/pcb-carrier-board-v1/`)*: unificare `JARVIS_CARRIER_BOARD_V1_PRODUZIONE/` come fonte Gerber ufficiale, spostando `JARVIS_CARRIER_BOARD_V1_FINAL/` e i due `.zip` in `archive/pcb/` (o `.gitignore` per `.zip`), e consolidare `JARVIS_GPIO_MAPPING_PCB_V1.md` (oggi duplicato tra root e `06-Hardware-Integration/`).
- `03-Mechanical-Design/`: invariata.
- `04-Firmware/`:
  - `stable/jarvis_wifi_voice_client/` *(oppure mantenere `arduino-hw-test/jarvis_wifi_voice_client/` per non rompere script e `docs/FASE_13_8_*`)*
  - `archive/fase12_27_jarvis_wifi_voice_client/` (già archiviato)
  - `experiments/` (mantenere i prototipi di riferimento senza `build/`)
- `05-Voice-AI/`: invariata (escludere da Git tutti i `samples_fase12_*/*.wav` di test audio).
- `JARVIS-Robotics-Platform/`: mantenere separata per l'evoluzione futura, aggiungendo `JARVIS-Robotics-Platform/**/node_modules/` e `JARVIS-Robotics-Platform/**/.venv/` in `.gitignore`.
- `docs/`: mantenere tutti i report `FASE_*.md` e `manuals/`.

### Dipendenze e riferimenti impattati da eventuali spostamenti
- `README.md` (link a `03-Mechanical-Design/`, `04-Firmware/`, `05-Voice-AI/`, `06-Hardware-Integration/`, `docs/`)
- `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/README.md` (riferimenti a `04-Firmware/experiments/fase13-wakeword/libs` per `Chirale_TensorFLowLite-2.0.0`)
- `Start_JARVIS_Control_Center.bat` (avvio relativo verso `05-Voice-AI/`)
- `docs/FASE_13_*.md` (link diretti `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/`)

---

## 4. Verifica Coerenza Documentazione & Proposta `README.md`

La tabella di `README.md` root era ferma alla `FASE 9.5` (con una sola riga aggiunta in FASE 13.8) e non rifletteva chiaramente le FASI 10–13. Nel prossimo aggiornamento (`FASE 14.2`) va strutturata distinguendo:
1. **Funzionalità implementate e collaudate**:
   - Eyes 3.0 su OLED `SH1106` (`I2C`)
   - Conversazione vocale Wi-Fi/WSS TLS (`faster-whisper` + `Ollama qwen2.5:3b` + `Piper Profilo 08`)
   - Wake word locale continuo **«Hey Jarvis»** (`microWakeWord` v2 INT8), VAD adattivo, protezione anti-ri-trigger, speaker silenzioso in `IDLE`, `GPIO47` (PTT + cancel), diagnostica `STAT` (FASE 13.7–13.8).
2. **Funzionalità sperimentali**: prototipi isolati in `04-Firmware/experiments/` e `wokwi-*`.
3. **Componenti hardware**: `ESP32-S3-DevKitC-1 N16R8`, OLED `1.3"`, `INMP441`, `MAX98357A`, speaker `4 Ω 3 W`, pulsante `GPIO47`; PCB Carrier Board v1 in `JARVIS_CARRIER_BOARD_V1_PRODUZIONE/`.
4. **Funzionalità future**: sensori `VL53L0X`/`MPU6050`/`BH1750`/`TTP223` (pin riservati), Base Mobile B2 (`03-Mechanical-Design/05-Mobile-Electronics/`), `JARVIS-Robotics-Platform/`.
5. **Limiti tecnici attuali**: partizione `app0` da `1.310.720` B al `99%` (`11.392` B liberi); servizi AI eseguiti localmente su PC Windows 11.

---

## 5. Audit Sicurezza GitHub (Repository Pubblico)

- **Stato attuale**: `Tracked = 262`, `Untracked non ignorati = 9.034` (di cui `~9.000` dentro `JARVIS-Robotics-Platform/frontend/node_modules/`).
- **Cronologia Git**: verifica completa su `git log --all` → **0 segreti, `.env`, chiavi, DB o backup Flash committati nella storia**.
- **File sensibili attualmente esclusi correttamente**: `wifi_secrets.h`, `05-Voice-AI/.env`, `.local_certs/`, `05-Voice-AI/data/`, `05-Voice-AI/backups/`.
- **Criticità individuate prima di un `git add` / `push` pubblico**:
  1. **ALTA — `JARVIS-Robotics-Platform/frontend/node_modules/` e `.venv/`**: non sono in `.gitignore` (`~9.000` file di dipendenze terze da escludere).
  2. **MEDIA — `05-Voice-AI/tts-lab/samples_fase12_*/*.wav` e `04-Firmware/wokwi-*/*.bin|*.zip`**: file binari/audio di test non coperti dall'attuale `.gitignore`.
  3. **MEDIA — Dati di rete locale e personali in file tracciabili/documentali**:
     - `33` file citano IP privati LAN (`192.168.178.x`, es. `docs/FASE_11..12`, `wifi_secrets.example.h`, `jarvis-desk-01.device.json`).
     - `10` file citano il MAC address dell'ESP32-S3 (`docs/FASE_11..13`, `JARVIS-Robotics-Platform/`).
     - `54` file contengono il percorso personale Windows dell'utente (`C:\Users\...`).
     *(Nessuna password, token API o chiave privata reale esposta; tuttavia per un repo pubblico è consigliabile sanitizzare almeno `wifi_secrets.example.h` / `jarvis-desk-01.device.json` / script Python da IP/percorsi personali.)*
- **Licenze**:
  - `microWakeWord` (`hey_jarvis` v2) & `TFLite Micro` (`Chirale_TensorFlowLite`): **Apache-2.0**.
  - `arduinoWebSockets`: **LGPL-2.1**.
  - `U8g2`: **BSD-2-Clause**.
  - `faster-whisper`: **MIT** | `Ollama` (`qwen2.5:3b`): **MIT / Apache-2.0** | `Piper`: **MIT**.
  *(Raccomandazione: aggiungere un file `LICENSE` nella root e `THIRD_PARTY_NOTICES.md`.)*

---

## 6. Confronto Repository Locale vs Remoto

- **Remoto (`origin`)**: `https://github.com/bubiweb75/jarvislegobot.git`
  - `origin/main`: `7c33314` (`feat(personality): complete natural conversation and personality 2.0`)
- **Locale (`main`)**: `53f1bce` (`test(hardware): validate Eyes 3.0 on ESP32-S3 SH1106`) → **`ahead 1`** rispetto a `origin/main`.
- **Working tree**: `14` file tracciati modificati + decine di file/cartelle non tracciati (FASI 10.2–13.8, `JARVIS-Robotics-Platform/`, PCB Gerber).

---

## 7. Piano Operativo FASE 14.2 (Richiede Autorizzazione)

1. **Aggiornare `.gitignore`**: escludere `**/node_modules/`, `**/.venv/`, `05-Voice-AI/tts-lab/samples_fase12_*/`, `04-Firmware/wokwi-*/*.bin`, `04-Firmware/wokwi-*/*.zip`, `*.zip` PCB duplicati.
2. **Pulizia/riordino non distruttivo**: archiviare `JARVIS_CARRIER_BOARD_V1_FINAL/` e `.zip` duplicati, rimuovere la copia duplicata di `JARVIS_GPIO_MAPPING_PCB_V1.md` in root mantenendo quella in `06-Hardware-Integration/`.
3. **Sanitizzazione privacy**: sostituire eventuali percorsi `C:\Users\<utente>` negli script e placeholder IP/MAC nei file di esempio (`wifi_secrets.example.h`, `jarvis-desk-01.device.json`), e aggiungere `LICENSE` + `THIRD_PARTY_NOTICES.md`.
4. **Aggiornamento `README.md` root** con stato aggiornato alla FASE 13.8 e indice documentazione completo.
5. **Verifica finale `git status`** + commit ordinati per area + `git push origin main` su autorizzazione esplicita.

### Rischi e Decisioni da Approvare
- **Decisione 1**: vuoi mantenere `docs/FASE_11..13` così come sono (con IP LAN `192.168.178.x` e MAC hardware nei log storici) oppure anonimizzarli prima del push pubblico?
- **Decisione 2**: vuoi spostare la cartella stabile `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` o mantenerla dov'è (opzione consigliata per non rompere i riferimenti)?
- **Decisione 3**: vuoi includere `JARVIS-Robotics-Platform/` (senza `node_modules` e `.venv`) nello stesso repository oppure escluderlo / tenerlo separato?
