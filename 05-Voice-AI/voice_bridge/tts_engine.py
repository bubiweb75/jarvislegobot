"""TTS Engine: Piper synthesis with JARVIS Amichetto DSP and 16 kHz mono PCM16 normalization."""

from __future__ import annotations

from abc import ABC, abstractmethod
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import List, Tuple

_VOICE_AI_DIR = Path(__file__).resolve().parent.parent
if str(_VOICE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_VOICE_AI_DIR))

from voice_dsp import shape_piper_wav  # noqa: E402

from .audio import (
    encode_wav_mono_16bit,
    read_piper_model_sample_rate,
    validate_and_normalize_wav,
)
from .schemas import BridgeError


class TTSEngine(ABC):
    @abstractmethod
    def is_available(self) -> Tuple[bool, str]:
        """Returns (available, status_detail)."""

    @abstractmethod
    def synthesize(self, text: str, timeout_s: float = 10.0) -> bytes:
        """Synthesizes Italian text into 16 kHz mono 16-bit PCM WAV bytes."""


class PiperTTSEngine(TTSEngine):
    """Synthesizes Italian speech via Piper CLI + optional JARVIS Amichetto DSP shaping."""

    def __init__(
        self,
        piper_bin: str,
        model_path: str,
        target_sr: int = 16000,
        speed: float = 1.00,
        noise_scale: float = 0.60,
        pitch_semitones: float = 5.0,
        robot_mix: float = 0.0,
        dsp_enabled: bool = True,
        dsp_method: str = "wsola",
        limiter_enabled: bool = False,
    ) -> None:
        self.piper_bin = piper_bin
        self.model_path = model_path
        self.target_sr = target_sr
        self.speed = max(0.75, min(1.50, float(speed)))
        self.noise_scale = max(0.2, min(1.5, float(noise_scale)))
        self.pitch_semitones = max(-12.0, min(12.0, float(pitch_semitones)))
        self.robot_mix = max(0.0, min(0.35, float(robot_mix)))
        self.dsp_enabled = bool(dsp_enabled)
        method_norm = (dsp_method or "wsola").strip().lower()
        self.dsp_method = method_norm if method_norm in {"wsola", "phase_vocoder"} else "wsola"
        self.limiter_enabled = bool(limiter_enabled)

    @property
    def length_scale(self) -> float:
        return 1.0 / self.speed

    def _resolve_bin(self) -> str:
        p = Path(self.piper_bin)
        if p.exists():
            return str(p)
        found = shutil.which(self.piper_bin)
        return found or ""

    def is_available(self) -> Tuple[bool, str]:
        resolved = self._resolve_bin()
        if not resolved:
            return False, f"Eseguibile Piper non trovato ({self.piper_bin})"
        if not Path(self.model_path).exists():
            return False, f"Modello Piper mancante ({self.model_path})"
        meta_sr = read_piper_model_sample_rate(self.model_path)
        sr_note = f"{meta_sr} Hz" if meta_sr else "SR da header WAV"
        dsp_note = (
            f"speed={self.speed:.2f}x, noise_scale={self.noise_scale:.2f}, "
            f"pitch={self.pitch_semitones:+.1f}st, dsp={'on' if self.dsp_enabled else 'off'}, "
            f"method={self.dsp_method}, tanh={'on' if self.limiter_enabled else 'off'}"
        )
        return True, f"Piper pronto ({Path(self.model_path).name}, {sr_note}, {dsp_note})"

    def synthesize(self, text: str, timeout_s: float = 10.0) -> bytes:
        ok, msg = self.is_available()
        if not ok:
            raise BridgeError("TTS_UNAVAILABLE", msg, http_status=503, recoverable=True)

        cleaned = " ".join(text.split()).strip()
        if not cleaned:
            raise BridgeError("TTS_EMPTY_TEXT", "Testo vuoto per sintesi vocale", http_status=400, recoverable=False)

        resolved_bin = self._resolve_bin()
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(prefix="jarvis_tts_", suffix=".wav", delete=False) as tf:
                tmp_path = Path(tf.name)

            cmd = [
                resolved_bin,
                "--model",
                self.model_path,
                "--length_scale",
                f"{self.length_scale:.3f}",
                "--noise_scale",
                f"{self.noise_scale:.3f}",
                "--output_file",
                str(tmp_path),
            ]
            proc = subprocess.run(
                cmd,
                input=cleaned,
                text=True,
                capture_output=True,
                timeout=timeout_s,
                encoding="utf-8",
            )
            if proc.returncode != 0 or not tmp_path.exists():
                raise BridgeError("TTS_FAILED", f"Errore sintesi Piper (exit={proc.returncode})", http_status=500, recoverable=True)

            raw_wav = tmp_path.read_bytes()
        except subprocess.TimeoutExpired as exc:
            raise BridgeError("TTS_TIMEOUT", f"Timeout sintesi TTS ({timeout_s:.1f}s)", http_status=504, recoverable=True) from exc
        finally:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

        if self.dsp_enabled:
            try:
                raw_wav, _ = shape_piper_wav(
                    raw_wav,
                    pitch_semitones=self.pitch_semitones,
                    robot_mix=self.robot_mix,
                    volume=100,
                    method=self.dsp_method,
                    limiter_enabled=self.limiter_enabled,
                )
            except Exception as exc:
                raise BridgeError(
                    "TTS_DSP_FAILED",
                    f"Errore elaborazione DSP ({self.dsp_method}): {exc}",
                    http_status=500,
                    recoverable=True,
                ) from exc

        # Normalizza a 16 kHz mono PCM16 usando la frequenza reale letta dal WAV
        normalized = validate_and_normalize_wav(
            raw_wav,
            max_bytes=8 * 1024 * 1024,
            max_duration_s=60.0,
            target_sr=self.target_sr,
            silence_rms_threshold=0,
            reject_silence=False,
        )
        return normalized.wav_bytes_16k_mono


class MockTTSEngine(TTSEngine):
    """Deterministic synthetic sine WAV TTS for offline automated tests."""

    def __init__(self, available: bool = True, duration_s: float = 0.25, sample_rate: int = 16000) -> None:
        self.available = available
        self.duration_s = duration_s
        self.sample_rate = sample_rate

    def is_available(self) -> Tuple[bool, str]:
        if not self.available:
            return False, "Modello TTS mock non disponibile"
        return True, "Mock TTS pronto"

    def synthesize(self, text: str, timeout_s: float = 10.0) -> bytes:
        if not self.available:
            raise BridgeError("TTS_UNAVAILABLE", "Modello TTS mancante", http_status=503, recoverable=True)
        if not text.strip():
            raise BridgeError("TTS_EMPTY_TEXT", "Testo vuoto", http_status=400, recoverable=False)

        n = max(160, int(round(self.sample_rate * self.duration_s)))
        samples: List[int] = [
            int(round(1200.0 * math.sin(2.0 * math.pi * 440.0 * i / float(self.sample_rate))))
            for i in range(n)
        ]
        raw = encode_wav_mono_16bit(samples, self.sample_rate)
        normalized = validate_and_normalize_wav(
            raw,
            max_bytes=2 * 1024 * 1024,
            max_duration_s=30.0,
            target_sr=16000,
            silence_rms_threshold=0,
            reject_silence=False,
        )
        return normalized.wav_bytes_16k_mono
