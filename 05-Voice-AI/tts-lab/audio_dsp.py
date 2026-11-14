"""Clean DSP post-processing for JARVIS Voice Personality Lab (no harsh robotic distortion)."""

from dataclasses import dataclass
import io
import wave
from typing import Tuple

import numpy as np


@dataclass
class VoiceProfileParams:
    name: str
    pitch_semitones: float
    speed: float
    expressiveness: float  # Piper noise_scale
    robot_mix: float       # 0.0 (none) .. 0.25 (subtle companion resonance)


PROFILES = {
    "Originale (Neutro)": VoiceProfileParams("Originale (Neutro)", 0.0, 1.00, 0.667, 0.0),
    "1. Amichetto Dolce": VoiceProfileParams("1. Amichetto Dolce", 1.2, 0.98, 0.65, 0.0),
    "2. Amichetto Vivace": VoiceProfileParams("2. Amichetto Vivace", 2.4, 1.06, 0.80, 0.0),
    "3. Amichetto Robotico": VoiceProfileParams("3. Amichetto Robotico", 2.2, 1.04, 0.78, 0.14),
}


def read_wav_mono_f32(wav_bytes: bytes) -> Tuple[np.ndarray, int]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())
    if sw != 2 or not raw:
        return np.zeros(0, dtype=np.float32), sr
    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    return data, sr


def write_wav_mono_f32(samples: np.ndarray, sr: int) -> bytes:
    clipped = np.clip(samples, -0.98, 0.98)
    pcm = (clipped * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def _phase_vocoder_time_stretch(samples: np.ndarray, rate: float, n_fft: int = 1024, hop: int = 256) -> np.ndarray:
    """Time-stretches audio by `rate` (>1.0 = shorter, <1.0 = longer) without changing pitch."""
    if len(samples) < n_fft or abs(rate - 1.0) < 1e-3:
        return samples
    window = np.hanning(n_fft).astype(np.float32)
    phase_acc = np.zeros(n_fft // 2 + 1, dtype=np.float64)
    omega = 2.0 * np.pi * np.arange(n_fft // 2 + 1) * hop / n_fft

    # Build STFT frames
    frames = []
    for pos in range(0, len(samples) - n_fft, hop):
        seg = samples[pos : pos + n_fft] * window
        frames.append(np.fft.rfft(seg))
    if len(frames) < 2:
        return samples
    stft = np.array(frames)

    positions = np.arange(0, len(frames) - 1, rate)
    out_len = int(len(positions) * hop + n_fft)
    out = np.zeros(out_len, dtype=np.float32)
    win_sum = np.zeros(out_len, dtype=np.float32)

    prev_phase = np.angle(stft[0])
    for idx, t in enumerate(positions):
        i0 = int(np.floor(t))
        frac = t - i0
        i1 = min(i0 + 1, len(frames) - 1)
        mag = (1.0 - frac) * np.abs(stft[i0]) + frac * np.abs(stft[i1])
        dphi = np.angle(stft[i1]) - np.angle(stft[i0]) - omega
        dphi -= 2.0 * np.pi * np.round(dphi / (2.0 * np.pi))
        phase_acc += omega + dphi
        spec = mag * np.exp(1j * phase_acc)
        grain = np.fft.irfft(spec, n=n_fft).astype(np.float32) * window
        p = idx * hop
        out[p : p + n_fft] += grain
        win_sum[p : p + n_fft] += window * window
        prev_phase = np.angle(stft[i0])  # noqa: F841

    nz = win_sum > 1e-6
    out[nz] /= win_sum[nz]
    return out


def pitch_shift_preserve_duration(samples: np.ndarray, sr: int, semitones: float) -> np.ndarray:
    """Shifts pitch by `semitones` while preserving original speech duration."""
    if abs(semitones) < 0.05 or len(samples) < 1024:
        return samples
    factor = 2.0 ** (semitones / 12.0)
    # Time-stretch by 1/factor, then resample by factor -> pitch shifts, duration preserved!
    stretched = _phase_vocoder_time_stretch(samples, rate=1.0 / factor)
    new_len = max(1, int(round(len(stretched) / factor)))
    shifted = np.interp(
        np.linspace(0.0, len(stretched) - 1, new_len, dtype=np.float32),
        np.arange(len(stretched), dtype=np.float32),
        stretched,
    ).astype(np.float32)
    return shifted


def apply_subtle_robot_character(samples: np.ndarray, sr: int, mix: float) -> np.ndarray:
    """Adds a very light, warm robotic companion resonance without hurting clarity."""
    if mix <= 0.005 or len(samples) < 512:
        return samples
    mix = float(np.clip(mix, 0.0, 0.35))

    # Gentle short comb resonance (~5.5 ms) + very subtle 95 Hz warmth modulation
    delay_samples = max(1, int(sr * 0.0055))
    comb = np.copy(samples)
    if delay_samples < len(samples):
        comb[delay_samples:] += 0.42 * samples[:-delay_samples]

    t = np.arange(len(samples), dtype=np.float32) / float(sr)
    mod = 0.88 + 0.12 * np.sin(2.0 * np.pi * 95.0 * t)
    fx = comb * mod

    blended = (1.0 - mix) * samples + mix * fx
    # Normalize peak to match original loudness
    orig_peak = float(np.max(np.abs(samples))) + 1e-6
    new_peak = float(np.max(np.abs(blended))) + 1e-6
    return (blended * (orig_peak / new_peak)).astype(np.float32)


def process_voice_audio(
    wav_bytes: bytes,
    pitch_semitones: float = 0.0,
    robot_mix: float = 0.0,
) -> Tuple[bytes, float]:
    """Applies pitch shift + optional subtle robotic character; returns (wav_bytes, duration_s)."""
    samples, sr = read_wav_mono_f32(wav_bytes)
    if len(samples) == 0:
        return wav_bytes, 0.0
    if abs(pitch_semitones) >= 0.05:
        samples = pitch_shift_preserve_duration(samples, sr, pitch_semitones)
    if robot_mix > 0.005:
        samples = apply_subtle_robot_character(samples, sr, robot_mix)
    duration_s = len(samples) / float(sr)
    return write_wav_mono_f32(samples, sr), duration_s
