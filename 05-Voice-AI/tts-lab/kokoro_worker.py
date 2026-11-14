"""Isolated Kokoro-82M worker running inside .venv-kokoro (Python 3.12)."""

import json
from pathlib import Path
import sys
import time

import psutil
import soundfile as sf
from kokoro_onnx import Kokoro


def main() -> int:
    lab_dir = Path(__file__).resolve().parent
    model_path = lab_dir / "models" / "kokoro" / "kokoro-v1.0.onnx"
    voices_path = lab_dir / "models" / "kokoro" / "voices-v1.0.bin"

    t0 = time.perf_counter()
    kokoro = Kokoro(str(model_path), str(voices_path))
    load_ms = (time.perf_counter() - t0) * 1000.0

    proc = psutil.Process()
    proc.cpu_percent(interval=None)

    print(json.dumps({"ready": True, "load_ms": round(load_ms, 1)}), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            if req.get("cmd") == "quit":
                break
            text = req["text"]
            voice = req.get("voice", "if_sara")
            speed = float(req.get("speed", 1.0))
            out_wav = req["out_wav"]

            t_gen0 = time.perf_counter()
            samples, sr = kokoro.create(text, voice=voice, speed=speed, lang="it")
            gen_ms = (time.perf_counter() - t_gen0) * 1000.0
            sf.write(out_wav, samples, sr)

            ram_mb = proc.memory_info().rss / (1024.0 * 1024.0)
            cpu_pct = proc.cpu_percent(interval=None)
            print(
                json.dumps(
                    {
                        "ok": True,
                        "load_ms": round(load_ms, 1),
                        "gen_ms": round(gen_ms, 1),
                        "ram_mb": round(ram_mb, 1),
                        "cpu_pct": round(cpu_pct, 1),
                    }
                ),
                flush=True,
            )
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
