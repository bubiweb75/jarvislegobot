# FASE 11.2C.4 — Amplificazione microfono e confronto Whisper

## 1. Obiettivo

Aggiungere a **JARVIS Voice Lab** una modalità diagnostica con guadagno software regolabile (`1×`, `2×`, `3×`) e protezione anti-clipping, per confrontare sulla stessa registrazione vocale (senza ri-registrare) l'audio originale e le versioni amplificate insieme alle rispettive trascrizioni Whisper.

## 2. Implementazione

### 2.1 Guadagno regolabile con protezione anti-clipping

- **Interfaccia browser** ([index.html](05-Voice-AI/voice_bridge/static/index.html), [app.js](05-Voice-AI/voice_bridge/static/app.js)):
  - Selettore `#gain-select` nella card **Microfono** con opzioni `Originale (1×)` (predefinito), `Guadagno 2×` e `Guadagno 3×`.
  - Funzione `applySafeGain(floatSamples, requestedGain, safetyHeadroom = 0.95)` applicata al segnale PCM a 16 kHz **prima** della codifica WAV (`encodeWavPcm16Mono`), senza alterare velocità o tono.
  - Protezione anti-clipping: misura il picco `peakIn = max(|sample|)` e limita automaticamente il guadagno effettivo a `min(requestedGain, 0.95 / peakIn)`, lasciando un margine di sicurezza del 5% sotto il fondo scala PCM16.
  - Nella sezione **Diagnostica** vengono mostrati: `Guadagno (ric. / eff.)`, `RMS / Picco`, `Clipping`, `Durata reg.` e `Sample rate`.
  - Nota esplicita in UI: *"L'amplificazione software aumenta anche il rumore di fondo e non garantisce un miglioramento STT."*

- **Supporto backend** ([audio.py](05-Voice-AI/voice_bridge/audio.py), [pipeline.py](05-Voice-AI/voice_bridge/pipeline.py)):
  - Aggiunta la funzione `apply_safe_gain_wav(...)` con dataclass `GainResult` per validazione e test automatici dell'amplificazione PCM16 anti-clipping.
  - Aggiornato `VoiceBridgeService.transcribe_only` (`/api/v1/stt`) per restituire anche `input_duration_s`, `input_sample_rate`, `input_rms_16`, `input_peak_16`, `input_clipped_count` e `input_wav_bytes_len`.

### 2.2 Confronto 1× / 2× / 3× sulla stessa registrazione

- `app.js` conserva solo in RAM della sessione browser l'ultimo buffer ricampionato a 16 kHz (`lastResampled16k`), revocando tutti gli Object URL al logout o alla registrazione successiva.
- Premendo **Confronta guadagni (1× / 2× / 3×)** (`#btn-compare-gain`), il browser genera i tre WAV (`1×`, `2×`, `3×`) dallo stesso buffer `lastResampled16k`, crea un player `<audio controls>` dedicato per ascoltare ciascuna versione e invia richieste **sequenziali** (una dopo l'altra, evitando richieste parallele non controllate) a `POST /api/v1/stt` con cookie `HttpOnly` e header `X-CSRF-Token`.

### 2.3 Sicurezza e privacy

- Nessun salvataggio permanente su disco, nessun download automatico, nessuna registrazione continua e nessuna esposizione su Internet (`127.0.0.1:8765`).
- Autenticazione, cookie `HttpOnly` e protezione CSRF invariati.

## 3. Risultati dei test automatici

Tutti i test sono stati eseguiti con `05-Voice-AI/.venv/Scripts/python.exe` dopo le modifiche finali:

1. `unittest tests/test_voice_bridge.py tests/test_voice_lab.py -v` -> **18 test OK** (inclusi `test_18_safe_gain_anti_clipping_wav_integrity_and_silence` e `test_19_gain_comparison_sequential_stt_and_ui_controls` che verificano guadagno effettivo, assenza di clipping, integrità WAV, durata/sample rate invariati, confronto sequenziale sullo stesso audio, silenzio ed errori).
2. `unittest tests/test_control_center.py tests/test_conversation_engine.py tests/test_conversation_naturalizer.py tests/test_memory_engine.py tests/test_voice_ai.py -v` -> **50 test OK**.
3. `unittest test_behavior_engine.py test_sensor_manager.py test_simulator.py test_touch_manager.py -v` (in `04-Firmware/jarvis-desk-buddy-sim`) -> **44 test OK**.

## 4. Procedura per il collaudo manuale nel browser

1. Apri `http://127.0.0.1:8765/` e premi `Ctrl+F5` per ricaricare i file statici aggiornati (il server `PID 15220` già attivo serve direttamente i file aggiornati di `static/`, ma se necessario può essere riavviato per ricaricare anche le estensioni di `/api/v1/stt`).
2. Sblocca la sessione con il token `jarvis-lab-locale-2026`.
3. Lascia `Guadagno: Originale (1×)` e registra *"Ciao Jarvis, che ore sono?"*.
4. Ascolta la registrazione originale dal player nella card **Microfono** e verifica `RMS / Picco` e `Clipping` in **Diagnostica**.
5. Premi **Confronta guadagni (1× / 2× / 3×)** nella card **Diagnostica**:
   - Ascolta ciascuno dei tre player (`1×`, `2×`, `3×`) per verificare la qualità dell'audio e l'eventuale incremento del rumore di fondo.
   - Confronta guadagno richiesto vs guadagno effettivo, RMS, picco, clipping (atteso `0`) e le tre trascrizioni Whisper.
6. Opzionalmente seleziona `Guadagno 2×` o `Guadagno 3×` nel menu a tendina **Microfono** ed esegui una nuova registrazione end-to-end.
