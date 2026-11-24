# FASE 11.2C.3 — Verifica qualità audio originale

## 1. Obiettivo

Consentire all'utente di ascoltare esattamente il WAV inviato a Whisper nel **JARVIS Voice Lab**, senza ulteriori elaborazioni, per verificare direttamente la qualità della registrazione vocale prima di intervenire ulteriormente su STT o AI Router.

## 2. Modifiche implementate

1. **Player "Ascolta registrazione originale"** ([index.html](05-Voice-AI/voice_bridge/static/index.html), [app.js](05-Voice-AI/voice_bridge/static/app.js)):
   - Aggiunto l'elemento `<audio id="original-audio-player" controls preload="auto"></audio>` nella card **Microfono**.
   - In `stopAndUpload()`, subito dopo `const wavBlob = encodeWavPcm16Mono(resampled, TARGET_SR);`, viene creato un Object URL in memoria (`URL.createObjectURL(wavBlob)`) dallo **stesso identico `wavBlob`** inviato al backend tramite `form.append("file", wavBlob, "voice_lab.wav")`.
   - L'Object URL precedente viene revocato con `URL.revokeObjectURL(currentOriginalAudioUrl)` a ogni nuova registrazione e al logout; nessun file viene salvato su disco e nessun endpoint pubblico di download è stato aggiunto.

2. **Verifiche su ricampionamento e acquisizione microfono**:
   - **Ricampionamento `OfflineAudioContext`**: verificato che `offline.createBuffer(1, floatSamples.length, srcRate)` combinato con `OfflineAudioContext(1, Math.round(floatSamples.length * (dstRate / srcRate)), dstRate)` e `playbackRate = 1.0` mantiene inalterati durata, velocità e tono della voce.
   - **Opzioni microfono configurabili** (`getUserMedia`): rese configurabili da UI tramite checkbox (tutte attive di default come in precedenza, senza disabilitazioni indiscriminate) `Echo cancellation` (`#opt-echo`), `Noise suppression` (`#opt-noise`) e `Auto gain control` (`#opt-agc`), così da poter confrontare direttamente all'ascolto l'effetto delle elaborazioni del browser.

## 3. Vincoli rispettati

- Nessuna modifica ai modelli Whisper, ai parametri STT o all'AI Router.
- Nessun salvataggio su disco e nessun endpoint pubblico di download.
- Autenticazione, cookie `HttpOnly` e protezione CSRF invariati.
- Nessuna installazione, download, modifica al firmware ESP32, ai simulatori, al Raspberry o ai servizi Windows.

## 4. Test eseguiti

- `05-Voice-AI/.venv/Scripts/python.exe -m unittest tests/test_voice_bridge.py tests/test_voice_lab.py -v` -> **16 test OK** (incluso `test_17_original_audio_player_uses_exact_uploaded_wav_and_configurable_mic_options`).
- Verificato sul server locale attivo (`http://127.0.0.1:8765/`, PID `15220`) che `/` e `/static/app.js` servono il nuovo player, le checkbox microfono e `URL.createObjectURL(wavBlob)`.
