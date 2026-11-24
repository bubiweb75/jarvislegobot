# FASE 11.2C.5 — Download controllato Whisper Small e confronto reale Base vs Small

## 1. Repository sorgente del modello Small

- **Repository ufficiale**: `Systran/faster-whisper-small` (verificato tramite `faster_whisper.utils._MODELS["small"]` in `faster-whisper==1.2.1`).
- Accesso pubblico senza credenziali Hugging Face.

## 2. Versione e dimensioni del modello

- **Libreria**: `faster-whisper==1.2.1`, CPU, `compute_type="int8"`.
- **Snapshot scaricato**: `536b0662742c02347bc0e980a01041f333bce120`.
- **File scaricati**: `config.json`, `model.bin`, `tokenizer.json`, `vocabulary.txt`.
- **Dimensione totale su disco**: `463,69 MB`.
- Nessun altro modello (`medium`, `large`, `tiny`, Ollama, Piper) è stato scaricato; il modello `base` preesistente non è stato modificato.

## 3. Percorso della cache

- **Cache Hugging Face locale**: `%USERPROFILE%\.cache\huggingface\hub`
- **Directory modello Small**: `%USERPROFILE%\.cache\huggingface\hub\models--Systran--faster-whisper-small\snapshots\536b0662742c02347bc0e980a01041f333bce120`

## 4. Esito del download

- Completato con successo in `44,85 s` su disco con `328,48 GB` liberi e `6,39 GB` di RAM disponibile su `15,39 GB` totali.

## 5. Esito del caricamento reale

- `WhisperModel("small", device="cpu", compute_type="int8", local_files_only=True)` caricato con successo in `1,417 s` (e `1161 ms` nella verifica sequenziale tramite `FasterWhisperEngine.compare_models`, contro `471 ms` per `base`).
- Il modello `small` viene istanziato temporaneamente in modo sequenziale e rilasciato (`del temp_model; gc.collect()`) al termine dell'inferenza diagnostica.
- Il modello predefinito della pipeline ordinaria rimane **`base`** (`JARVIS_STT_MODEL="base"`).

## 6. File modificati

- `05-Voice-AI/voice_bridge/stt_engine.py`: aggiunti `ALLOWED_COMPARE_MODELS = ("base", "small")`, `validate_compare_models`, `compute_wer`, `get_process_rss_mb` e `compare_models` sequenziale in `STTEngine`, `FasterWhisperEngine` e `MockSTTEngine`.
- `05-Voice-AI/voice_bridge/pipeline.py`: aggiunto `VoiceBridgeService.compare_stt_models`.
- `05-Voice-AI/voice_bridge/api.py`: aggiunto endpoint autenticato `POST /api/v1/stt/compare-models`.
- `05-Voice-AI/voice_bridge/static/index.html` e `05-Voice-AI/voice_bridge/static/app.js`: aggiunti `#stt-ref-input`, il pulsante **Confronta Whisper Base / Small** (`#btn-compare-models`) e il pannello risultati `#model-compare-box`.
- `05-Voice-AI/tests/test_voice_lab.py`: aggiunti `test_20_small_model_cached_and_wer_calculation` e `test_21_compare_models_endpoint_security_limits_errors_and_default_preserved`.
- `docs/FASE_11_2C_5_CONFRONTO_WHISPER_BASE_SMALL.md`: presente report.

## 7. Nuovo endpoint diagnostico

- `POST /api/v1/stt/compare-models`
  - Protetto da autenticazione (`HttpOnly` cookie + `X-CSRF-Token` o `Authorization: Bearer`) e solo su `127.0.0.1:8765`.
  - Accetta esclusivamente modelli in `("base", "small")` (rifiuta qualsiasi altro nome o path con HTTP `400 INVALID_STT_MODEL`).
  - Applica i limiti di dimensione (`max_wav_bytes`) e durata (`max_audio_duration_s`) e il `ConcurrencyLimiter`.
  - Non salva audio su disco, non espone path locali o credenziali, non genera risposte AI o TTS e non effettua chiamate cloud.

## 8. Risultati dei test automatici

Eseguiti con `05-Voice-AI/.venv/Scripts/python.exe` dopo le modifiche finali (con mock per i test HTTP/pipeline e verifica reale della presenza in cache di `small`):

1. `unittest tests/test_voice_bridge.py tests/test_voice_lab.py -v` -> **20 test OK** (0 fallimenti, 0 errori).
2. `unittest tests/test_control_center.py tests/test_conversation_engine.py tests/test_conversation_naturalizer.py tests/test_memory_engine.py tests/test_voice_ai.py -v` -> **50 test OK** (0 fallimenti, 0 errori).
3. `unittest test_behavior_engine.py test_sensor_manager.py test_simulator.py test_touch_manager.py -v` (in `04-Firmware/jarvis-desk-buddy-sim`) -> **44 test OK** (0 fallimenti, 0 errori).

## 9. Stato del confronto reale Base vs Small

- Il caricamento reale di entrambi i modelli (`base` e `small`) tramite `FasterWhisperEngine.compare_models` è stato verificato in locale.
- Il confronto vocale reale sulla frase *"Ciao Jarvis, che ore sono?"* pronunciata dall'utente **non è ancora stato eseguito** e attende il collaudo manuale nel browser.

## 10. Tempi e consumo di memoria osservati

- **Download `small`**: `44,85 s` (`463,69 MB`).
- **Caricamento `base` (`int8`)**: `471 ms` nella verifica sequenziale.
- **Caricamento `small` (`int8`)**: `1161–1417 ms`.
- **Nota sulla misura RSS**: nella verifica Python su Windows `K32GetProcessMemoryInfo` ha restituito `None` (non disponibile nella configurazione corrente di `ctypes` senza privilegi/modulo `psutil`); i tempi di caricamento e inferenza vengono comunque misurati e mostrati per ogni modello.

## 11. Eventuali problemi riscontrati

- Avviso non bloccante di `huggingface_hub` relativo all'assenza di symlink su Windows (i file risultano comunque correttamente scaricati e caricabili con `local_files_only=True`).
- Misura `rss_mb` non disponibile tramite `K32GetProcessMemoryInfo` (`None`), senza impatto sul funzionamento di STT o UI.

## 12. Procedura di collaudo manuale

1. Apri `http://127.0.0.1:8765/` (server attivo su PID `17056`, modalità offline, default `base`) e premi `Ctrl+F5`.
2. Sblocca la sessione con il token `jarvis-lab-locale-2026`.
3. Registra *"Ciao Jarvis, che ore sono?"* con guadagno `Originale (1×)`.
4. Ascolta il WAV dal player **Ascolta registrazione originale**.
5. Premi **Confronta Whisper Base / Small** nella sezione **Diagnostica**.
6. Confronta le trascrizioni di `base` e `small`, il WER rispetto al riferimento `"Ciao Jarvis, che ore sono?"`, e i tempi di caricamento/inferenza.
7. Verifica che il normale pulsante di registrazione continui a utilizzare `base`.

## 13. Raccomandazione preliminare

Mantenere `base` come modello predefinito finché il collaudo vocale reale dell'utente non confermerà che `small` riconosce in modo nettamente più accurato *"Ciao Jarvis, che ore sono?"* con una latenza accettabile sulla CPU Ryzen 7 5700U.
