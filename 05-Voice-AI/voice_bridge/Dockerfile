# JARVIS Voice Bridge — Linux arm64 (Raspberry Pi 5) / amd64 compatible
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY voice_bridge/requirements-bridge.txt /app/requirements-bridge.txt
RUN pip install --no-cache-dir -r /app/requirements-bridge.txt

# Copy only required 05-Voice-AI modules & voice_bridge package
COPY ai_providers.py stt_providers.py tts_providers.py voice_dsp.py config.py conversation_naturalizer.py /app/
COPY voice_bridge /app/voice_bridge

RUN useradd -m -u 10001 jarvis && mkdir -p /data/tmp /models/piper /models/whisper && chown -R jarvis:jarvis /app /data /models
USER jarvis

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8765/health || exit 1

CMD ["uvicorn", "voice_bridge.api:app", "--host", "0.0.0.0", "--port", "8765"]
