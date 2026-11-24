"""Convert WAV audio to 16 kHz mono 16-bit PCM WAV and C header for ESP32-S3 flash."""

from __future__ import annotations

import array
from pathlib import Path
import wave


TARGET_SR = 16000


def load_wav_mono_16bit(path: Path) -> tuple[int, list[int]]:
    with wave.open(str(path), "rb") as wf:
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    if sw != 2:
        raise ValueError(f"Unsupported sample width {sw} bytes (expected 16-bit PCM)")

    samples = array.array("h")
    samples.frombytes(raw)
    if ch == 1:
        mono = list(samples)
    elif ch == 2:
        mono = [(samples[i] + samples[i + 1]) // 2 for i in range(0, len(samples), 2)]
    else:
        raise ValueError(f"Unsupported channel count {ch}")
    return sr, mono


def resample_linear(samples: list[int], src_sr: int, dst_sr: int) -> list[int]:
    if src_sr == dst_sr or len(samples) < 2:
        return samples
    ratio = src_sr / float(dst_sr)
    out_len = int(round(len(samples) * dst_sr / float(src_sr)))
    out: list[int] = []
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


def write_wav_mono_16bit(path: Path, sr: int, samples: list[int]) -> None:
    arr = array.array("h", samples)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(arr.tobytes())


def write_c_header(path: Path, sr: int, samples: list[int], source_desc: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "#pragma once",
        "",
        "#include <pgmspace.h>",
        "#include <stddef.h>",
        "#include <stdint.h>",
        "",
        f"// Source: {source_desc}",
        f"constexpr uint32_t kJarvisVoiceSampleRateHz = {sr}U;",
        f"constexpr size_t kJarvisVoiceNumSamples = {len(samples)}U;",
        "",
        "const int16_t kJarvisVoicePcm[] PROGMEM = {",
    ]
    for i in range(0, len(samples), 12):
        chunk = ", ".join(str(v) for v in samples[i : i + 12])
        lines.append(f"    {chunk},")
    lines.append("};")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    raw_wav = root / "audio" / "jarvis_intro_raw.wav"
    clean_wav = root / "audio" / "jarvis_intro_it.wav"
    header_path = root / "generated" / "jarvis_voice_pcm.h"

    src_path = raw_wav if raw_wav.exists() else clean_wav
    sr, mono = load_wav_mono_16bit(src_path)
    print(f"Input: {src_path.name} -> sr={sr} Hz, samples={len(mono)}, dur={len(mono)/sr:.3f}s")

    mono_16k = resample_linear(mono, sr, TARGET_SR)
    write_wav_mono_16bit(clean_wav, TARGET_SR, mono_16k)
    if raw_wav.exists() and raw_wav != clean_wav:
        raw_wav.unlink()

    write_c_header(
        header_path,
        TARGET_SR,
        mono_16k,
        "Piper TTS local offline (it_IT-riccardo-x_low.onnx) -> 16kHz mono 16-bit PCM",
    )
    print(
        f"Output: {clean_wav.name} ({clean_wav.stat().st_size} bytes) & "
        f"{header_path.name} ({len(mono_16k)} samples, {len(mono_16k)*2} PCM bytes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
