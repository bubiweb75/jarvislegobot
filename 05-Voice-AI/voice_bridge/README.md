# JARVIS Voice Bridge (FASE 11.2)

Microservizio FastAPI modulare per la pipeline vocale `WAV → STT (faster-whisper) → AI Router (Ollama → Cloud → Offline) → TTS (Piper 16 kHz mono PCM16) → WAV`.

## Avvio Locale su Windows (Test Manuale)

```powershell
cd "05-Voice-AI"
$env:JARVIS_BRIDGE_TOKEN="test-token-locale"
$env:JARVIS_BRIDGE_REQUIRE_AUTH="true"
.\.venv\Scripts\python.exe -m uvicorn voice_bridge.api:app --host 127.0.0.1 --port 8765
```

- Documentazione interattiva OpenAPI: `http://127.0.0.1:8765/docs`
- Healthcheck: `GET http://127.0.0.1:8765/health`
- Readiness (richiede `Authorization: Bearer <TOKEN>`): `GET http://127.0.0.1:8765/ready`
- Pipeline vocale: `POST http://127.0.0.1:8765/api/v1/voice/process` (multipart `file=@domanda.wav`)
- Diagnostica STT / TTS: `POST /api/v1/stt`, `POST /api/v1/tts`
- Recupero WAV temporaneo: `GET /api/v1/voice/audio/{audio_id}?consume=true`

## Nota Sicurezza LAN
Su loopback è ammesso HTTP. Prima del deployment in LAN su Raspberry Pi 5, proteggere il token in transito (TLS tramite Nginx Proxy Manager interno o tunnel cifrato).
