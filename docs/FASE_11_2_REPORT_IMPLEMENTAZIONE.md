# FASE 11.2 — Report Implementazione Voice Bridge (`jarvis-voice-bridge`)

---

## 1. File Creati e Modificati

### Creati (`05-Voice-AI/voice_bridge/`, `05-Voice-AI/tests/`, `docs/`)
- `05-Voice-AI/voice_bridge/__init__.py`
- `05-Voice-AI/voice_bridge/config.py` — configurazione `.env` (token, limiti audio, timeout STT/Ollama/Cloud/TTS, Piper/Whisper).
- `05-Voice-AI/voice_bridge/schemas.py` — `BridgeError`, `VoiceProcessResponse`, `TimingBreakdown`, `HealthResponse`, `ReadyResponse`.
- `05-Voice-AI/voice_bridge/security.py` — auth Bearer `hmac.compare_digest`, `redact_secrets()`, `validate_provider_url()`, `safe_temp_path()`, `TempAudioStore` (TTL + cleanup), `ConcurrencyLimiter`.
- `05-Voice-AI/voice_bridge/audio.py` — validazione header RIFF/WAVE, limiti byte/durata, rilevamento silenzio, downmix stereo→mono, ricampionamento lineare a `16.000 Hz`, lettura metadati `<model>.onnx.json`.
- `05-Voice-AI/voice_bridge/stt_engine.py` — `FasterWhisperEngine` (adapter thread-safe su `stt_providers.py`) + `MockSTTEngine`.
- `05-Voice-AI/voice_bridge/offline_fallback.py` — `OfflineFallbackProvider` (risposte italiane deterministiche senza pretendere capacità LLM).
- `05-Voice-AI/voice_bridge/ai_router.py` — `OllamaRouterClient` (probe/connect/generate separati), `CloudAIClient` (adapter `OpenAIProvider`), `AIRouter` (`Ollama → Cloud → Offline`).
- `05-Voice-AI/voice_bridge/tts_engine.py` — `PiperTTSEngine` (headless verso `bytes` WAV `16 kHz` mono PCM16, zero `winsound`) + `MockTTSEngine`.
- `05-Voice-AI/voice_bridge/conversation.py` — `BridgeConversationContext` (contesto in RAM limitato, nessuna persistenza vocale su disco).
- `05-Voice-AI/voice_bridge/diagnostics.py` — `BridgeDiagnostics` (ID correlazione `req_...`, tempi, redazione segreti).
- `05-Voice-AI/voice_bridge/pipeline.py` — `VoiceBridgeService`, `CancellationToken`.
- `05-Voice-AI/voice_bridge/api.py` — app FastAPI (`create_app`, `app`).
- Docker / Config (non eseguiti): `requirements-bridge.txt`, `Dockerfile`, `.dockerignore`, `docker-compose.example.yml`, `.env.bridge.example`, `README.md`.
- Test: `05-Voice-AI/tests/test_voice_bridge.py`.
- Report: `docs/FASE_11_2_REPORT_IMPLEMENTAZIONE.md`.

### Nessuna modifica a componenti stabili
Firmware ESP32 (`04-Firmware/`), simulatori, moduli esistenti di `05-Voice-AI/*.py`, container Raspberry e servizi Windows non sono stati modificati.

---

## 2. Architettura Implementata

Pipeline modulare: `WAV → validate_and_normalize_wav → STT Engine → BridgeConversationContext → AI Router → TTS Engine (16 kHz mono PCM16) → TempAudioStore + JSON/Base64`.
Tutte le richieste sono protette da `ConcurrencyLimiter`, `CancellationToken` e gestione strutturata `BridgeError`.

---

## 3. Componenti Esistenti Riutilizzati

- `05-Voice-AI/stt_providers.py` (`FasterWhisperSTTProvider`, `STTError`) → avvolto da `FasterWhisperEngine`.
- `05-Voice-AI/ai_providers.py` (`OpenAIProvider`, `AIProvider`, `AIProviderError`, `AIResponse`) → avvolto da `CloudAIClient` e `AIRouter`.
- `05-Voice-AI/conversation_naturalizer.py` (`prepare_for_tts`) → riutilizzato da `BridgeConversationContext`.

---

## 4. Endpoint Disponibili (`FastAPI` + OpenAPI `/docs`)

| Metodo & Path | Auth | Funzione |
|---|---|---|
| `GET /health` | No | Stato minimo non sensibile (`status`, `service`, `version`) |
| `GET /ready` | Bearer | Readiness globale + stato separato `stt`, `tts`, `ollama`, `cloud`, `offline_fallback` |
| `POST /api/v1/voice/process` | Bearer | Upload WAV → JSON (`request_id`, `transcript`, `reply_text`, `provider_used`, `fallback_used`, `timings`, `audio_url`, `audio_wav_base64`) |
| `GET /api/v1/voice/audio/{audio_id}` | Bearer | Recupero WAV temporaneo (`?consume=true` per rimozione immediata) |
| `POST /api/v1/stt` | Bearer | Diagnostica solo STT |
| `POST /api/v1/tts` | Bearer | Diagnostica solo TTS (`{"text": "..."}` → `audio/wav` `16 kHz` mono PCM16) |

---

## 5. Risultati di Tutti i Test (Eseguiti in Questa Sessione)

Esecuzione con `05-Voice-AI\.venv\Scripts\python.exe` (offline, senza servizi cloud reali, senza download modelli):
- **`05-Voice-AI/tests/`**: **`56/56` superati** (`Ran 56 tests in 15.309s` → `OK`):
  - `50` test Voice AI preesistenti preservati.
  - `6` test `TestVoiceBridge` che verificano tutti i 20 scenari previsti (avvio FastAPI, `/health`, `/ready`, validazione WAV + ricampionamento, rifiuto file non validi/troppo grandi, STT/TTS mock, metadati Piper `.onnx.json`, priorità `Ollama → Cloud → Offline`, auth 401, timeout STT 504, errori strutturati, `CancellationToken`, cleanup temp + path traversal, WAV uscita `16 kHz` mono 16-bit, redazione segreti nei log).
- **`04-Firmware/jarvis-desk-buddy-sim/`**: **`44/44` superati** (`Ran 44 tests in 4.193s` → `OK`).

---

## 6. Dipendenze Installate in `05-Voice-AI/.venv`

Installate **esclusivamente** in `05-Voice-AI\.venv` (nessuna installazione globale):
- `fastapi==0.163.2` (`starlette==1.10.0`, `pydantic==2.14.3`, `pydantic-core==2.50.4`)
- `uvicorn==0.54.0`
- `python-multipart==0.0.34`

---

## 7. Limitazioni, Problemi Aperti e Compatibilità Raspberry Pi 5 da Verificare

1. **Test reali STT/TTS/Ollama**: i test automatici usano mock/fixture; la latenza reale di `faster-whisper` (`base` vs `tiny` `int8`), `Piper` (`piper` CLI su Linux arm64) e `Ollama` su Windows 11 dovrà essere misurata in collaudo manuale dedicato.
2. **Compatibilità Raspberry Pi 5 (`arm64`)**: `Dockerfile` e `docker-compose.example.yml` sono pronti ma **non eseguiti**; occorre verificare su Pi 5 il pacchetto `piper` arm64 (es. binario/wheel `piper-tts`) e le prestazioni di `faster-whisper` su Cortex-A76.
3. **Trasporto token in LAN**: il test locale su loopback usa HTTP; prima dell'uso in LAN reale proteggere il token con TLS (Nginx Proxy Manager interno o tunnel).
4. **Streaming ESP32-S3 (`> 5 s`)**: fuori perimetro FASE 11.2, previsto in FASE 11.3–11.4.

---

## 8. Istruzioni per il Collaudo Locale su Windows

```powershell
cd "05-Voice-AI"
$env:JARVIS_BRIDGE_TOKEN="test-token-locale"
$env:JARVIS_BRIDGE_REQUIRE_AUTH="true"
$env:JARVIS_PIPER_BIN="tts-lab\bin\piper\piper.exe"
$env:JARVIS_PIPER_MODEL_PATH="tts-lab\models\piper\it_IT-riccardo-x_low.onnx"
.\.venv\Scripts\python.exe -m uvicorn voice_bridge.api:app --host 127.0.0.1 --port 8765
```

1. Apri `http://127.0.0.1:8765/docs` oppure testa `GET http://127.0.0.1:8765/health`.
2. Invia `POST /api/v1/tts` con `Authorization: Bearer test-token-locale` e `{"text": "Ciao, sono Jarvis!"}` per verificare l'audio reale `16 kHz` generato da Piper locale.
3. Invia `POST /api/v1/voice/process` con un file WAV di prova (`16 kHz` o `22 kHz`) verificando trascrizione (`faster-whisper` se modello in cache), routing AI (`Ollama` se attivo su `11434`, altrimenti `offline_fallback`) e WAV di risposta.

---

## 9. Proposta per la FASE 11.3

- Aggiungere endpoint **WebSocket `/ws/voice`** autenticato su `jarvis-voice-bridge` e implementare su ESP32-S3 (nuova variante isolata da `jarvis_duplex_rtos_hw_test`) la connettività **Wi-Fi + WebSocket** per controllo stati (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `ERROR`) e `CANCEL`, prima dello streaming audio completo (FASE 11.4).
