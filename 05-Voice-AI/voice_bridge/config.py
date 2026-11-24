"""Configuration loader for JARVIS Voice Bridge (environment-only secrets)."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional, Tuple

VALID_AI_MODES = frozenset({"DISABLED", "LOCAL_ONLY", "CLOUD_ONLY", "LOCAL_FIRST", "CLOUD_FIRST"})


def _normalize_ai_mode(raw: Optional[str]) -> str:
    if not raw:
        return "DISABLED"
    mode = raw.strip().upper()
    return mode if mode in VALID_AI_MODES else "DISABLED"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw.strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class BridgeConfig:
    host: str = "0.0.0.0"
    port: int = 8765
    device_token: str = ""
    require_auth: bool = True

    # Audio & Concurrency limits
    max_wav_bytes: int = 512 * 1024  # 512 KB (~16s @ 16kHz PCM16)
    max_audio_duration_s: float = 15.0
    silence_rms_threshold: int = 80
    max_concurrent_requests: int = 2
    temp_dir: Path = Path("/tmp/jarvis_voice_bridge")
    audio_ttl_s: float = 120.0
    target_sample_rate: int = 16000

    # Conversation context (limited & non-persistent by default)
    max_history_turns: int = 4
    conversation_max_messages: int = 8
    conversation_max_tokens: int = 1000
    log_conversation_text: bool = False
    log_stt_diag_text: bool = False

    # STT (faster-whisper)
    stt_model: str = "base"
    stt_language: str = "it"
    stt_compute_type: str = "int8"
    stt_allow_download: bool = False
    stt_timeout_s: float = 12.0
    stt_vad_filter: bool = True
    stt_speech_pad_ms: int = 0
    stt_beam_size: int = 1
    stt_condition_on_prev_text: bool = True
    stt_initial_prompt: str = ""
    enable_stt_diag: bool = True

    # Local Intents (Time/Date)
    timezone: str = ""

    # Hybrid AI Router (disabled by default for safe rollout)
    ai_mode: str = "DISABLED"
    ai_fallback_enabled: bool = False
    ai_timeout_s: float = 20.0

    # AI Priority 1: Ollama (PC Windows local)
    ollama_enabled: bool = False
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_probe_timeout_s: float = 1.5
    ollama_connect_timeout_s: float = 2.0
    ollama_generate_timeout_s: float = 20.0
    ollama_max_tokens: int = 120
    ollama_detail_max_tokens: int = 180
    ollama_num_ctx: int = 2048
    ollama_keep_alive: str = "30m"
    ollama_prewarm_on_startup: bool = True
    ollama_temperature: float = 0.5

    # AI Priority 2: Cloud API (configurable, disabled by default)
    cloud_enabled: bool = False
    cloud_provider: str = "openai"
    cloud_base_url: str = "https://api.openai.com/v1"
    cloud_model: str = "gpt-4o-mini"
    cloud_api_key: str = ""
    cloud_timeout_s: float = 20.0
    cloud_max_tokens: int = 220
    cloud_temperature: Optional[float] = 0.5
    cloud_max_requests_per_hour: int = 30
    cloud_max_daily_tokens: int = 50000

    # Allowed hosts for outbound provider URLs (empty -> localhost + private LAN allowed)
    allowed_provider_hosts: Tuple[str, ...] = ()

    # TTS (Piper — JARVIS Amichetto Profilo 08: WSOLA + noise_scale 0.60, no tanh)
    piper_bin: str = "piper"
    piper_model_path: str = "/models/piper/it_IT-riccardo-x_low.onnx"
    tts_timeout_s: float = 10.0
    tts_max_chars: int = 270
    tts_piper_speed: float = 1.00
    tts_piper_noise_scale: float = 0.60
    tts_piper_pitch_semitones: float = 5.0
    tts_piper_robot_mix: float = 0.0
    tts_piper_dsp_enabled: bool = True
    tts_piper_dsp_method: str = "wsola"
    tts_piper_limiter_enabled: bool = False

    # ESP32-S3 WebSocket Adapter (FASE 11.3A) — separate device token from browser token
    esp_device_token: str = ""
    esp_max_input_bytes: int = 256000     # 8 s @ 16 kHz PCM16 mono
    esp_max_tts_bytes: int = 640000       # 20 s @ 16 kHz PCM16 mono
    esp_ws_chunk_bytes: int = 2048        # 64 ms @ 16 kHz PCM16 mono
    esp_ws_idle_timeout_s: float = 60.0

    @classmethod
    def from_env(cls) -> "BridgeConfig":
        hosts_raw = os.getenv("JARVIS_ALLOWED_PROVIDER_HOSTS", "").strip()
        hosts = tuple(h.strip().lower() for h in hosts_raw.split(",") if h.strip())
        default_tmp = Path(os.getenv("TEMP", "/tmp")) / "jarvis_voice_bridge"
        max_turns = max(0, _env_int("JARVIS_MAX_HISTORY_TURNS", 4))
        max_messages_env = os.getenv("JARVIS_CONVERSATION_MAX_MESSAGES")
        max_messages = max(0, int(max_messages_env.strip())) if (max_messages_env and max_messages_env.strip().isdigit()) else max_turns * 2
        cloud_temp_raw = os.getenv("JARVIS_CLOUD_TEMPERATURE", "0.5").strip()
        cloud_temp: Optional[float]
        if not cloud_temp_raw or cloud_temp_raw.lower() in {"none", "null", "off"}:
            cloud_temp = None
        else:
            try:
                cloud_temp = float(cloud_temp_raw)
            except ValueError:
                cloud_temp = 0.5
        ai_timeout_raw = os.getenv("JARVIS_AI_TIMEOUT_SECONDS", os.getenv("JARVIS_AI_TIMEOUT_S", ""))
        try:
            ai_timeout = max(1.0, float(ai_timeout_raw.strip())) if ai_timeout_raw.strip() else 20.0
        except ValueError:
            ai_timeout = 20.0
        return cls(
            host=os.getenv("JARVIS_BRIDGE_HOST", "0.0.0.0"),
            port=_env_int("JARVIS_BRIDGE_PORT", 8765),
            device_token=os.getenv("JARVIS_BRIDGE_TOKEN", ""),
            require_auth=_env_bool("JARVIS_BRIDGE_REQUIRE_AUTH", True),
            max_wav_bytes=_env_int("JARVIS_MAX_WAV_BYTES", 512 * 1024),
            max_audio_duration_s=_env_float("JARVIS_MAX_AUDIO_DURATION_S", 15.0),
            silence_rms_threshold=_env_int("JARVIS_SILENCE_RMS_THRESHOLD", 80),
            max_concurrent_requests=max(1, _env_int("JARVIS_MAX_CONCURRENT_REQUESTS", 2)),
            temp_dir=Path(os.getenv("JARVIS_TEMP_DIR", str(default_tmp))),
            audio_ttl_s=_env_float("JARVIS_AUDIO_TTL_S", 120.0),
            max_history_turns=max_turns,
            conversation_max_messages=max_messages,
            conversation_max_tokens=max(100, _env_int("JARVIS_CONVERSATION_MAX_TOKENS", 1000)),
            log_conversation_text=_env_bool("JARVIS_LOG_CONVERSATION_TEXT", False),
            log_stt_diag_text=_env_bool("JARVIS_LOG_STT_DIAG_TEXT", False),
            stt_model=os.getenv("JARVIS_STT_MODEL", "base").strip() or "base",
            stt_language=os.getenv("JARVIS_STT_LANGUAGE", "it").strip() or "it",
            stt_compute_type=os.getenv("JARVIS_STT_COMPUTE_TYPE", "int8").strip() or "int8",
            stt_allow_download=_env_bool("JARVIS_STT_ALLOW_DOWNLOAD", False),
            stt_timeout_s=_env_float("JARVIS_STT_TIMEOUT_S", 12.0),
            stt_vad_filter=_env_bool("JARVIS_STT_VAD_FILTER", True),
            stt_speech_pad_ms=max(0, _env_int("JARVIS_STT_SPEECH_PAD_MS", 0)),
            stt_beam_size=max(1, _env_int("JARVIS_STT_BEAM_SIZE", 1)),
            stt_condition_on_prev_text=_env_bool("JARVIS_STT_CONDITION_ON_PREV_TEXT", True),
            stt_initial_prompt=os.getenv("JARVIS_STT_INITIAL_PROMPT", "").strip(),
            enable_stt_diag=_env_bool("JARVIS_ENABLE_STT_DIAG", True),
            timezone=os.getenv("JARVIS_TIMEZONE", "").strip(),
            ai_mode=_normalize_ai_mode(os.getenv("JARVIS_AI_MODE", "DISABLED")),
            ai_fallback_enabled=_env_bool("JARVIS_AI_FALLBACK_ENABLED", False),
            ai_timeout_s=ai_timeout,
            ollama_enabled=_env_bool("JARVIS_OLLAMA_ENABLED", False),
            ollama_url=os.getenv("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434").strip(),
            ollama_model=os.getenv("JARVIS_OLLAMA_MODEL", "qwen2.5:3b").strip(),
            ollama_probe_timeout_s=_env_float("JARVIS_OLLAMA_PROBE_TIMEOUT_S", 1.5),
            ollama_connect_timeout_s=_env_float("JARVIS_OLLAMA_CONNECT_TIMEOUT_S", 2.0),
            ollama_generate_timeout_s=_env_float("JARVIS_OLLAMA_GENERATE_TIMEOUT_S", ai_timeout),
            ollama_max_tokens=max(32, _env_int("JARVIS_OLLAMA_MAX_TOKENS", 120)),
            ollama_detail_max_tokens=max(64, _env_int("JARVIS_OLLAMA_DETAIL_MAX_TOKENS", 180)),
            ollama_num_ctx=max(512, _env_int("JARVIS_OLLAMA_NUM_CTX", 2048)),
            ollama_keep_alive=os.getenv("JARVIS_OLLAMA_KEEP_ALIVE", "30m").strip() or "30m",
            ollama_prewarm_on_startup=_env_bool("JARVIS_OLLAMA_PREWARM_ON_STARTUP", True),
            ollama_temperature=max(0.0, min(2.0, _env_float("JARVIS_OLLAMA_TEMPERATURE", 0.5))),
            cloud_enabled=_env_bool("JARVIS_CLOUD_ENABLED", False),
            cloud_provider=os.getenv("JARVIS_CLOUD_PROVIDER", "openai").strip().lower() or "openai",
            cloud_base_url=os.getenv("JARVIS_CLOUD_BASE_URL", "https://api.openai.com/v1").strip(),
            cloud_model=os.getenv("JARVIS_CLOUD_MODEL", "gpt-4o-mini").strip(),
            cloud_api_key=os.getenv("JARVIS_CLOUD_API_KEY", os.getenv("OPENAI_API_KEY", "")).strip(),
            cloud_timeout_s=_env_float("JARVIS_CLOUD_TIMEOUT_S", ai_timeout),
            cloud_max_tokens=max(32, _env_int("JARVIS_CLOUD_MAX_TOKENS", 220)),
            cloud_temperature=cloud_temp,
            cloud_max_requests_per_hour=max(0, _env_int("JARVIS_CLOUD_MAX_REQUESTS_PER_HOUR", 30)),
            cloud_max_daily_tokens=max(0, _env_int("JARVIS_CLOUD_MAX_DAILY_TOKENS", 50000)),
            allowed_provider_hosts=hosts,
            piper_bin=os.getenv("JARVIS_PIPER_BIN", "piper").strip(),
            piper_model_path=os.getenv(
                "JARVIS_PIPER_MODEL_PATH", "/models/piper/it_IT-riccardo-x_low.onnx"
            ).strip(),
            tts_timeout_s=_env_float("JARVIS_TTS_TIMEOUT_S", 10.0),
            tts_max_chars=max(80, _env_int("JARVIS_TTS_MAX_CHARS", 270)),
            tts_piper_speed=max(0.75, min(1.50, _env_float("JARVIS_TTS_PIPER_SPEED", 1.00))),
            tts_piper_noise_scale=max(0.2, min(1.5, _env_float("JARVIS_TTS_PIPER_NOISE_SCALE", 0.60))),
            tts_piper_pitch_semitones=max(-12.0, min(12.0, _env_float("JARVIS_TTS_PIPER_PITCH_SEMITONES", 5.0))),
            tts_piper_robot_mix=max(0.0, min(0.35, _env_float("JARVIS_TTS_PIPER_ROBOT_MIX", 0.0))),
            tts_piper_dsp_enabled=_env_bool("JARVIS_TTS_PIPER_DSP_ENABLED", True),
            tts_piper_dsp_method=(
                os.getenv("JARVIS_TTS_PIPER_DSP_METHOD", "wsola").strip().lower()
                if os.getenv("JARVIS_TTS_PIPER_DSP_METHOD", "wsola").strip().lower() in {"wsola", "phase_vocoder"}
                else "wsola"
            ),
            tts_piper_limiter_enabled=_env_bool("JARVIS_TTS_PIPER_LIMITER_ENABLED", False),
            esp_device_token=os.getenv("JARVIS_ESP_DEVICE_TOKEN", "").strip(),
            esp_max_input_bytes=max(3200, _env_int("JARVIS_ESP_MAX_INPUT_BYTES", 256000)),
            esp_max_tts_bytes=max(32000, _env_int("JARVIS_ESP_MAX_TTS_BYTES", 640000)),
            esp_ws_chunk_bytes=max(512, min(8192, _env_int("JARVIS_ESP_WS_CHUNK_BYTES", 2048))),
            esp_ws_idle_timeout_s=max(5.0, _env_float("JARVIS_ESP_WS_IDLE_TIMEOUT_S", 60.0)),
        )
