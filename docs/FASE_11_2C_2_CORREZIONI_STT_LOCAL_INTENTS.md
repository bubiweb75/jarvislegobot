# FASE 11.2C.2 — Correzione STT, diagnostica audio e intenzioni locali

## 1. Obiettivo

Risolvere le cause individuate durante il primo collaudo reale del **JARVIS Voice Lab** (`"Ciao Jarvis, che ore sono?"` trascritto erroneamente come `"C'è un giarbice che ho riso o no?"`), aggiungere metriche diagnostiche audio reali, introdurre una sezione di confronto STT controllato (A–E) e gestire localmente in italiano le richieste su ora, giorno e data prima di interrogare Ollama o API cloud.

## 2. Diagnostica audio implementata

Nel modulo [audio.py](05-Voice-AI/voice_bridge/audio.py) (`ValidatedAudio` e `validate_and_normalize_wav`) e nello schema [schemas.py](05-Voice-AI/voice_bridge/schemas.py) (`VoiceProcessResponse`) vengono ora calcolati e restituiti:

- `input_duration_s`: durata effettiva del WAV acquisito (secondi).
- `input_sample_rate`: sample rate originale del WAV inviato dal client.
- `input_rms_16`: valore RMS PCM16.
- `input_peak_16`: picco massimo assoluto (`max(|sample|)`).
- `input_clipped_count`: numero di campioni in clipping (`|sample| >= 32767`).
- `input_wav_bytes_len`: dimensione effettiva in byte del payload WAV ricevuto.
- `timezone_note`: nota diagnostica sul fuso orario utilizzato per eventuali risposte locali su ora/data.

Tutte queste metriche vengono mostrate nella sezione **Diagnostica** di [index.html](05-Voice-AI/voice_bridge/static/index.html) / [app.js](05-Voice-AI/voice_bridge/static/app.js).

Nessuna registrazione vocale viene salvata su disco né inserita nei log applicativi. Quando `JARVIS_ENABLE_STT_DIAG=true` (default), `VoiceBridgeService` conserva temporaneamente **solo in RAM** (`_last_diag_wav`) l'ultimo WAV normalizzato della sessione diagnostica per consentire il confronto STT sullo stesso audio.

## 3. Correzione acquisizione audio browser (`Voice Lab`)

In [app.js](05-Voice-AI/voice_bridge/static/app.js):

- Rimossa la funzione `resampleLinear` (ricampionamento lineare privo di filtro anti-aliasing, che a 48 kHz -> 16 kHz introduceva aliasing sulle armoniche vocali).
- Sostituita con `resampleAntiAliased`, basata su `OfflineAudioContext(1, targetLen, 16000)` + `AudioBufferSourceNode`, che applica il filtraggio anti-aliasing nativo del browser durante il downsampling a 16 kHz (con fallback lineare solo su browser privi di `OfflineAudioContext`).
- Nessun padding artificiale o media mobile a 3 campioni; allo stop vengono uniti i chunk acquisiti senza alterare la durata reale del WAV.

## 4. Parametri Whisper configurabili e confronto STT (A–E)

In [config.py](05-Voice-AI/voice_bridge/config.py) e [stt_engine.py](05-Voice-AI/voice_bridge/stt_engine.py):

- Mantenuto il modello `base` (`int8`) già presente in cache locale, senza download di nuovi modelli.
- Introdotta la dataclass `STTOptions` e rese configurabili da `.env` le opzioni `JARVIS_STT_VAD_FILTER` (default `true`), `JARVIS_STT_SPEECH_PAD_MS` (default `0`), `JARVIS_STT_BEAM_SIZE` (default `3`), `JARVIS_STT_CONDITION_ON_PREV_TEXT` (default `true`) e `JARVIS_STT_INITIAL_PROMPT` (default `""`).
- Aggiunto l'endpoint autenticato `POST /api/v1/stt/compare` in [api.py](05-Voice-AI/voice_bridge/api.py) (protetto da cookie `HttpOnly` + `X-CSRF-Token` o `Authorization: Bearer`) e il pulsante **Confronta STT (A–E)** nella UI per eseguire sullo stesso WAV i 5 preset diagnostici:
  - **A**: Baseline (`vad_filter=True`, `speech_pad_ms=0`, `beam_size=3`)
  - **B**: Senza VAD (`vad_filter=False`, `beam_size=3`)
  - **C**: VAD con padding (`vad_filter=True`, `speech_pad_ms=250`, `beam_size=3`)
  - **D**: Beam 5 (`vad_filter=True`, `speech_pad_ms=0`, `beam_size=5`)
  - **E**: Prompt JARVIS (`vad_filter=True`, `speech_pad_ms=250`, `beam_size=5`, `condition_on_previous_text=False`, `initial_prompt="JARVIS, assistente vocale in italiano."`)

Nessuna sostituzione arbitraria di parole viene applicata alla trascrizione restituita da Whisper.

## 5. Stato del confronto reale A–E

Il confronto automatico sugli endpoint e sul flusso end-to-end è stato verificato con test di integrazione (`test_15_stt_compare_diag_endpoint_and_auth_and_flag`). L'esecuzione dei preset A–E su una registrazione vocale reale al microfono è pronta nella pagina Voice Lab tramite il pulsante **Confronta STT (A–E)** e attende il prossimo collaudo interattivo dell'utente.

## 6. Gestione locale di ora e data (`LocalIntentHandler`)

Creato [local_intents.py](05-Voice-AI/voice_bridge/local_intents.py) e integrato in [ai_router.py](05-Voice-AI/voice_bridge/ai_router.py) **prima** di Ollama, API cloud e fallback offline:

- Riconosce in modo deterministico varianti italiane su ora, giorno e data (con eventuale prefisso `"ciao jarvis"`, `"ehi jarvis"`, `"jarvis"`), tra cui:
  - `"che ore sono"`, `"che ora è"`, `"dimmi l'ora"` -> es. `"Sono le 22 e 53."`
  - `"che giorno è oggi"` -> es. `"Oggi è martedì 17 novembre 2026."`
  - `"che data è oggi"` -> es. `"Oggi è il 17 novembre 2026."`
- Imposta `provider_used = "Local Intent"` e `fallback_used = False`.
- La risposta viene poi passata normalmente a Piper TTS per la sintesi vocale in WAV 16 kHz mono.
- Le frasi non riconosciute o corrotte (es. `"C'è un giarbice che ho riso o no?"`) **non** vengono forzate come richieste di ora/data e proseguono lungo la catena standard Ollama → Cloud → Fallback offline.

## 7. Gestione del fuso orario (`JARVIS_TIMEZONE`)

- Supporta `JARVIS_TIMEZONE` tramite `zoneinfo.ZoneInfo`.
- Per `UTC` utilizza direttamente `datetime.timezone.utc`.
- Su Windows senza pacchetto `tzdata` (dove `ZoneInfo("Europe/Rome")` solleva `ZoneInfoNotFoundError`), se il fuso richiesto è `Europe/Rome` e il fuso locale del sistema operativo ha offset equivalente (+01:00 / +02:00, es. `ora solare Europa occidentale` / `W. Europe Standard Time`), utilizza l'ora locale OS segnalando esplicitamente la nota diagnostica in `timezone_note`; in caso contrario restituisce un errore esplicito senza sostituire silenziosamente un fuso diverso e senza installare pacchetti aggiuntivi.

## 8. File modificati e creati

- Creato: `05-Voice-AI/voice_bridge/local_intents.py`
- Aggiornati:
  - `05-Voice-AI/voice_bridge/config.py`
  - `05-Voice-AI/voice_bridge/schemas.py`
  - `05-Voice-AI/voice_bridge/audio.py`
  - `05-Voice-AI/voice_bridge/stt_engine.py`
  - `05-Voice-AI/voice_bridge/ai_router.py`
  - `05-Voice-AI/voice_bridge/pipeline.py`
  - `05-Voice-AI/voice_bridge/api.py`
  - `05-Voice-AI/voice_bridge/static/index.html`
  - `05-Voice-AI/voice_bridge/static/app.js`
  - `05-Voice-AI/tests/test_voice_bridge.py`
  - `05-Voice-AI/tests/test_voice_lab.py`
- Creato report: `docs/FASE_11_2C_2_CORREZIONI_STT_LOCAL_INTENTS.md`

## 9. Verifica test automatici dopo le modifiche finali

Tutti i test sono stati eseguiti con `05-Voice-AI/.venv/Scripts/python.exe` dopo l'ultima modifica:

1. `unittest tests/test_voice_bridge.py tests/test_voice_lab.py -v` -> **15 test OK** (0 errori, 0 fallimenti).
2. `unittest tests/test_control_center.py tests/test_conversation_engine.py tests/test_conversation_naturalizer.py tests/test_memory_engine.py tests/test_voice_ai.py -v` -> **50 test OK** (0 errori, 0 fallimenti).
3. `unittest test_behavior_engine.py test_sensor_manager.py test_simulator.py test_touch_manager.py -v` (in `04-Firmware/jarvis-desk-buddy-sim`) -> **44 test OK** (0 errori, 0 fallimenti).

> **Nota operativa:** se il server locale di collaudo (`task-2856` su `127.0.0.1:8765`) era già avviato prima di queste modifiche, occorre riavviarlo per caricare i nuovi moduli Python e i file statici aggiornati prima del prossimo test nel browser.
