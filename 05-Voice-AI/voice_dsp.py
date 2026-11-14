"""Lightweight numpy-only DSP for JARVIS Piper voice character (no scipy required)."""

import io
import wave
from typing import Tuple

import numpy as np


def _read_wav_mono_f32(wav_bytes: bytes) -> Tuple[np.ndarray, int]:
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


def _write_wav_mono_f32(samples: np.ndarray, sr: int) -> bytes:
    clipped = np.clip(samples, -0.98, 0.98)
    pcm = (clipped * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def _phase_vocoder_time_stretch(
    samples: np.ndarray, rate: float, n_fft: int = 1024, hop: int = 256
) -> np.ndarray:
    if len(samples) < n_fft or abs(rate - 1.0) < 1e-3:
        return samples
    window = np.hanning(n_fft).astype(np.float32)
    phase_acc = np.zeros(n_fft // 2 + 1, dtype=np.float64)
    omega = 2.0 * np.pi * np.arange(n_fft // 2 + 1) * hop / n_fft

    frames = []
    for pos in range(0, len(samples) - n_fft, hop):
        frames.append(np.fft.rfft(samples[pos : pos + n_fft] * window))
    if len(frames) < 2:
        return samples
    stft = np.array(frames)

    positions = np.arange(0, len(frames) - 1, rate)
    out_len = int(len(positions) * hop + n_fft)
    out = np.zeros(out_len, dtype=np.float32)
    win_sum = np.zeros(out_len, dtype=np.float32)

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

    nz = win_sum > 1e-6
    out[nz] /= win_sum[nz]
    return out


def shape_piper_wav(
    wav_bytes: bytes,
    pitch_semitones: float = 5.0,
    robot_mix: float = 0.0,
    volume: int = 90,
) -> Tuple[bytes, float]:
    """Applies pitch shift (preserving duration), optional subtle robot mix, and volume."""
    samples, sr = _read_wav_mono_f32(wav_bytes)
    if len(samples) == 0:
        return wav_bytes, 0.0

    if abs(pitch_semitones) >= 0.05 and len(samples) >= 1024:
        factor = 2.0 ** (pitch_semitones / 12.0)
        stretched = _phase_vocoder_time_stretch(samples, rate=1.0 / factor)
        new_len = max(1, int(round(len(stretched) / factor)))
        samples = np.interp(
            np.linspace(0.0, len(stretched) - 1, new_len, dtype=np.float32),
            np.arange(len(stretched), dtype=np.float32),
            stretched,
        ).astype(np.float32)

    if robot_mix > 0.005 and len(samples) >= 512:
        mix = float(np.clip(robot_mix, 0.0, 0.35))
        delay_samples = max(1, int(sr * 0.0055))
        comb = np.copy(samples)
        if delay_samples < len(samples):
            comb[delay_samples:] += 0.42 * samples[:-delay_samples]
        t = np.arange(len(samples), dtype=np.float32) / float(sr)
        fx = comb * (0.88 + 0.12 * np.sin(2.0 * np.pi * 95.0 * t))
        blended = (1.0 - mix) * samples + mix * fx
        orig_peak = float(np.max(np.abs(samples))) + 1e-6
        new_peak = float(np.max(np.abs(blended))) + 1e-6
        samples = (blended * (orig_peak / new_peak)).astype(np.float32)

    vol_scale = max(0.0, min(1.0, float(volume) / 100.0))
    samples = samples * vol_scale
    duration_s = len(samples) / float(sr) if sr > 0 else 0.0
    return _write_wav_mono_f32(samples, sr), duration_s
