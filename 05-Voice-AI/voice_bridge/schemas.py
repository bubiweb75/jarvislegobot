"""Structured schemas and error types for JARVIS Voice Bridge."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


class BridgeError(RuntimeError):
    """Structured error carrying HTTP status, error code, and recoverability."""

    def __init__(
        self,
        code: str,
        message: str,
        http_status: int = 500,
        recoverable: bool = True,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.recoverable = recoverable

    def to_dict(self, request_id: str = "") -> Dict[str, Any]:
        return {
            "request_id": request_id,
            "error": {
                "code": self.code,
                "message": self.message,
                "recoverable": self.recoverable,
            },
        }


@dataclass
class TimingBreakdown:
    stt_ms: float = 0.0
    ai_ms: float = 0.0
    tts_ms: float = 0.0
    total_ms: float = 0.0


@dataclass
class VoiceProcessResponse:
    request_id: str
    transcript: str
    reply_text: str
    provider_used: str
    fallback_used: bool
    timings: TimingBreakdown
    audio_id: Optional[str] = None
    audio_url: Optional[str] = None
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_bits: int = 16
    audio_bytes_len: int = 0
    audio_wav_base64: Optional[str] = None
    input_duration_s: float = 0.0
    input_sample_rate: int = 16000
    input_rms_16: int = 0
    input_peak_16: int = 0
    input_clipped_count: int = 0
    input_wav_bytes_len: int = 0
    timezone_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderStatus:
    available: bool
    detail: str


@dataclass
class HealthResponse:
    status: str = "ok"
    service: str = "jarvis-voice-bridge"
    version: str = "0.1.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReadyResponse:
    ready: bool
    service_ok: bool
    providers: Dict[str, ProviderStatus] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "service_ok": self.service_ok,
            "providers": {k: asdict(v) for k, v in self.providers.items()},
        }
