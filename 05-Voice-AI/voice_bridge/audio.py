"""WAV audio validation, resampling, and 16 kHz mono PCM16 normalization."""

from __future__ import annotations

import array
from dataclasses import dataclass
import io
import json
import math
from pathlib import Path
from typing import List, Optional
import wave

from .schemas import BridgeError


@dataclass(frozen=True)
class ValidatedAudio:
    wav_bytes_16k_mono: bytes
    sample_rate: int
    channels: int
    sample_width: int
    num_frames: int
    duration_s: float
    rms_16: int
    input_sample_rate: int = 16000
    peak_16: int = 0
    clipped_count: int = 0
    input_wav_bytes_len: int = 0


@dataclass(frozen=True)
class GainResult:
    wav_bytes: bytes
    sample_rate: int
    num_frames: int
    duration_s: float
    requested_gain: float
    effective_gain: float
    rms_16: int
    peak_16: int
    clipped_count: int


def read_piper_model_sample_rate(model_path: str) -> Optional[int]:
    """Reads native sample_rate from Piper <model>.onnx.json metadata if present."""
    if not model_path:
        return None
    meta_path = Path(f"{model_path}.json")
    if not meta_path.exists():
        return None
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        sr = data.get("audio", {}).get("sample_rate")
        if isinstance(sr, int) and sr > 0:
            return sr
    except Exception:
        return None
    return None


def resample_pcm16_linear(samples: List[int], src_sr: int, dst_sr: int) -> List[int]:
    """Resamples mono 16-bit PCM using linear interpolation (never header-only)."""
    if src_sr <= 0 or dst_sr <= 0:
        raise BridgeError("INVALID_SAMPLE_RATE", "Frequenza di campionamento non valida", http_status=400, recoverable=False)
    if src_sr == dst_sr or len(samples) < 2:
        return list(samples)

    ratio = src_sr / float(dst_sr)
    out_len = max(1, int(round(len(samples) * dst_sr / float(src_sr))))
    out: List[int] = []
    max_idx = len(samples) - 1
    for i in range(out_len):
        pos = i * ratio
        idx = int(pos)
        if idx >= max_idx:
            out.append(samples[max_idx])
        else:
            frac = pos - idx
            val = samples[idx] * (1.0 - frac) + samples[idx + 1] * frac
            ival = int(round(val))
            if ival > 32767:
                ival = 32767
            elif ival < -32768:
                ival = -32768
            out.append(ival)
    return out


def encode_wav_mono_16bit(samples: List[int], sample_rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    arr = array.array("h", samples)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(arr.tobytes())
    return buf.getvalue()


def _decode_to_mono_pcm16(raw_frames: bytes, channels: int, sampwidth: int) -> List[int]:
    if sampwidth == 2:
        arr = array.array("h")
        arr.frombytes(raw_frames)
        raw_list = list(arr)
    elif sampwidth == 1:
        # 8-bit unsigned PCM -> signed 16-bit
        raw_list = [(b - 128) << 8 for b in raw_frames]
    else:
        raise BridgeError(
            "UNSUPPORTED_AUDIO_FORMAT",
            f"Profondità audio non supportata ({sampwidth * 8} bit; atteso 8 o 16 bit PCM)",
            http_status=400,
            recoverable=False,
        )

    if channels == 1:
        return raw_list
    if channels == 2:
        return [(raw_list[i] + raw_list[i + 1]) // 2 for i in range(0, len(raw_list) - 1, 2)]
    raise BridgeError(
        "UNSUPPORTED_CHANNELS",
        f"Numero canali non supportato ({channels}; atteso mono o stereo)",
        http_status=400,
        recoverable=False,
    )


def validate_and_normalize_wav(
    wav_bytes: bytes,
    max_bytes: int,
    max_duration_s: float,
    target_sr: int = 16000,
    silence_rms_threshold: int = 80,
    reject_silence: bool = True,
) -> ValidatedAudio:
    """Validates RIFF/WAVE PCM payload and normalizes to 16 kHz mono 16-bit WAV."""
    if not wav_bytes:
        raise BridgeError("EMPTY_AUDIO", "File audio vuoto", http_status=400, recoverable=False)
    if len(wav_bytes) > max_bytes:
        raise BridgeError(
            "PAYLOAD_TOO_LARGE",
            f"File audio troppo grande ({len(wav_bytes)} B > {max_bytes} B)",
            http_status=413,
            recoverable=False,
        )
    if len(wav_bytes) < 44 or wav_bytes[:4] != b"RIFF" or wav_bytes[8:12] != b"WAVE":
        raise BridgeError("INVALID_WAV", "Header RIFF/WAVE non valido", http_status=400, recoverable=False)

    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            comptype = wf.getcomptype()
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            nframes = wf.getnframes()
            raw_frames = wf.readframes(nframes)
    except wave.Error as exc:
        raise BridgeError("INVALID_WAV", f"File WAV corrotto: {exc}", http_status=400, recoverable=False) from exc

    if comptype != "NONE":
        raise BridgeError("UNSUPPORTED_WAV_CODEC", "Richiesto WAV PCM non compresso", http_status=400, recoverable=False)
    if framerate < 8000 or framerate > 48000 or nframes == 0 or not raw_frames:
        raise BridgeError("EMPTY_OR_INVALID_AUDIO", "Audio WAV privo di campioni o frequenza non valida", http_status=400, recoverable=False)

    duration_s = nframes / float(framerate)
    if duration_s > max_duration_s:
        raise BridgeError(
            "AUDIO_TOO_LONG",
            f"Durata audio eccessiva ({duration_s:.2f}s > {max_duration_s:.2f}s)",
            http_status=413,
            recoverable=False,
        )

    mono = _decode_to_mono_pcm16(raw_frames, channels, sampwidth)
    if not mono:
        raise BridgeError("EMPTY_AUDIO", "Nessun campione audio estratto", http_status=400, recoverable=False)

    mean = sum(mono) / float(len(mono))
    rms = int(round(math.sqrt(sum((x - mean) ** 2 for x in mono) / float(len(mono)))))
    peak_16 = max(abs(x) for x in mono)
    clipped_count = sum(1 for x in mono if abs(x) >= 32767)
    if reject_silence and rms < silence_rms_threshold:
        raise BridgeError("SILENT_AUDIO", "Audio silenzioso o livello insufficiente", http_status=422, recoverable=True)

    normalized = resample_pcm16_linear(mono, framerate, target_sr)
    out_wav = encode_wav_mono_16bit(normalized, target_sr)
    return ValidatedAudio(
        wav_bytes_16k_mono=out_wav,
        sample_rate=target_sr,
        channels=1,
        sample_width=2,
        num_frames=len(normalized),
        duration_s=duration_s,
        rms_16=rms,
        input_sample_rate=framerate,
        peak_16=peak_16,
        clipped_count=clipped_count,
        input_wav_bytes_len=len(wav_bytes),
    )


def apply_safe_gain_wav(
    wav_bytes: bytes,
    requested_gain: float,
    safety_headroom: float = 0.95,
) -> GainResult:
    """Applies software gain to PCM16 mono WAV with automatic anti-clipping headroom."""
    if requested_gain <= 0.0:
        raise BridgeError("INVALID_GAIN", "Guadagno non valido", http_status=400, recoverable=False)
    if not (0.5 <= safety_headroom < 1.0):
        raise BridgeError("INVALID_HEADROOM", "Margine di sicurezza non valido", http_status=400, recoverable=False)

    validated = validate_and_normalize_wav(
        wav_bytes,
        max_bytes=max(len(wav_bytes), 204800),
        max_duration_s=10.0,
        target_sr=16000,
        silence_rms_threshold=0,
        reject_silence=False,
    )
    with wave.open(io.BytesIO(validated.wav_bytes_16k_mono), "rb") as wf:
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        raw_frames = wf.readframes(nframes)

    arr = array.array("h")
    arr.frombytes(raw_frames)
    samples = list(arr)
    peak_in = max((abs(x) for x in samples), default=0)
    max_safe_peak = int(32767 * safety_headroom)

    if peak_in == 0:
        effective_gain = float(requested_gain)
        scaled = samples
    else:
        max_allowed = max_safe_peak / float(peak_in)
        effective_gain = min(float(requested_gain), max_allowed)
        scaled = []
        for x in samples:
            v = int(round(x * effective_gain))
            if v > 32767:
                v = 32767
            elif v < -32768:
                v = -32768
            scaled.append(v)

    mean = sum(scaled) / float(len(scaled))
    rms_out = int(round(math.sqrt(sum((x - mean) ** 2 for x in scaled) / float(len(scaled)))))
    peak_out = max((abs(x) for x in scaled), default=0)
    clipped_out = sum(1 for x in scaled if abs(x) >= 32767)
    out_wav = encode_wav_mono_16bit(scaled, framerate)

    return GainResult(
        wav_bytes=out_wav,
        sample_rate=framerate,
        num_frames=len(scaled),
        duration_s=len(scaled) / float(framerate),
        requested_gain=float(requested_gain),
        effective_gain=round(effective_gain, 4),
        rms_16=rms_out,
        peak_16=peak_out,
        clipped_count=clipped_out,
    )
