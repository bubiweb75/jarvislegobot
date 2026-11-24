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


def _wsola_time_stretch(
    samples: np.ndarray,
    rate: float,
    sr: int = 16000,
    win_ms: float = 24.0,
    hop_ms: float = 6.0,
    search_ms: float = 8.0,
    cand_step: int = 2,
) -> np.ndarray:
    """Vectorized pure-NumPy time-domain WSOLA preserving consonant transients."""
    if abs(rate - 1.0) < 1e-4 or len(samples) < 1024:
        return samples
    samples = np.ascontiguousarray(samples, dtype=np.float32)
    win_len = int(round(sr * win_ms / 1000.0))
    if win_len % 2 == 1:
        win_len += 1
    syn_hop = int(round(sr * hop_ms / 1000.0))
    ana_hop = rate * syn_hop
    search_rad = int(round(sr * search_ms / 1000.0))

    hann = np.hanning(win_len).astype(np.float32)
    target_len = max(1, int(round(len(samples) / rate)))
    out_len = target_len + win_len
    out = np.zeros(out_len, dtype=np.float32)
    norm = np.zeros(out_len, dtype=np.float32)

    out[:win_len] = samples[:win_len] * hann
    norm[:win_len] = hann

    overlap = win_len - syn_hop
    n_frames = max(1, int((len(samples) - win_len) / max(ana_hop, 1.0)))

    sq_cumsum = np.empty(len(samples) + 1, dtype=np.float64)
    sq_cumsum[0] = 0.0
    np.cumsum(samples.astype(np.float64) ** 2, out=sq_cumsum[1:])
    ov_view = np.lib.stride_tricks.sliding_window_view(samples, overlap)

    for m in range(1, n_frames):
        syn_pos = m * syn_hop
        if syn_pos + win_len > out_len:
            break
        nominal_ana = int(round(m * ana_hop))
        if nominal_ana + win_len >= len(samples):
            break

        ref = out[syn_pos : syn_pos + overlap]
        lo = max(0, nominal_ana - search_rad)
        hi = min(len(samples) - win_len, nominal_ana + search_rad)

        best_pos = nominal_ana
        if hi > lo:
            cands = ov_view[lo : hi + 1 : cand_step]
            dots = cands @ ref
            starts = np.arange(lo, hi + 1, cand_step)
            cand_e = sq_cumsum[starts + overlap] - sq_cumsum[starts]
            denom = np.sqrt(np.maximum(cand_e, 1e-18))
            scores = dots / denom
            best_pos = int(starts[int(np.argmax(scores))])

        out[syn_pos : syn_pos + win_len] += samples[best_pos : best_pos + win_len] * hann
        norm[syn_pos : syn_pos + win_len] += hann

    res = out[:target_len]
    valid = norm[:target_len] > 1e-4
    res[valid] /= norm[:target_len][valid]
    return res


def _safe_linear_level(
    samples: np.ndarray,
    target_active_rms: float = 0.22,
    max_peak: float = 0.89,
) -> np.ndarray:
    """Linear gain to match listening level without tanh distortion or clipping."""
    abs_s = np.abs(samples)
    peak = float(np.max(abs_s)) if samples.size else 0.0
    if peak < 1e-6:
        return samples
    nz = abs_s > 0.01
    active_rms = float(np.sqrt(np.mean(samples[nz] ** 2))) if np.any(nz) else peak * 0.25
    gain_rms = target_active_rms / max(active_rms, 1e-6)
    gain_peak_cap = max_peak / peak
    gain = min(gain_rms, gain_peak_cap)
    return (samples * gain).astype(np.float32)


def shape_piper_wav(
    wav_bytes: bytes,
    pitch_semitones: float = 5.0,
    robot_mix: float = 0.0,
    volume: int = 90,
    method: str = "phase_vocoder",
    limiter_enabled: bool = True,
) -> Tuple[bytes, float]:
    """Applies pitch shift (preserving duration), optional subtle robot mix, and level shaping."""
    dsp_method = (method or "phase_vocoder").strip().lower()
    if dsp_method not in {"phase_vocoder", "wsola"}:
        raise ValueError(f"Metodo DSP non supportato: {method}")

    samples, sr = _read_wav_mono_f32(wav_bytes)
    if len(samples) == 0:
        return wav_bytes, 0.0

    if abs(pitch_semitones) >= 0.05 and len(samples) >= 1024:
        factor = 2.0 ** (pitch_semitones / 12.0)
        if dsp_method == "wsola":
            stretched = _wsola_time_stretch(samples, rate=1.0 / factor, sr=sr)
        else:
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

    if limiter_enabled:
        # Loudness maximizer + soft limiter so pitched speech matches normal PC app volume
        nz_mask = np.abs(samples) > 0.01
        if np.any(nz_mask):
            active_rms = float(np.sqrt(np.mean(samples[nz_mask] ** 2)))
            if active_rms > 1e-4:
                gain = min(5.0, 0.48 / active_rms)
                if gain > 1.0:
                    samples = np.tanh((samples * gain) / 0.96).astype(np.float32) * 0.96
    else:
        samples = _safe_linear_level(samples, target_active_rms=0.22, max_peak=0.89)

    if not np.all(np.isfinite(samples)):
        raise ValueError("DSP ha prodotto campioni non finiti")

    vol_scale = max(0.0, min(1.0, float(volume) / 100.0))
    samples = samples * vol_scale
    duration_s = len(samples) / float(sr) if sr > 0 else 0.0
    return _write_wav_mono_f32(samples, sr), duration_s
