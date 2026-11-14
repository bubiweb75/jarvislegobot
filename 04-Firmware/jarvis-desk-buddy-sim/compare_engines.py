"""Cross-engine framebuffer comparator (Python EyeEngine vs Host-compiled C++ EyeEngine).

Runs automatically if a host C++ compiler (g++, clang++, or cl) is available on PATH;
otherwise reports SKIPPED without claiming cross-engine binary equivalence.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from eye_engine import ALL_EXPRESSIONS, EyeEngine


def main() -> int:
    compiler = shutil.which("g++") or shutil.which("clang++")
    if not compiler:
        print("SKIPPED: No host C++ compiler (g++/clang++) found on PATH; cannot execute C++ EyeEngine on Windows host.")
        return 0

    fw_dir = Path(__file__).resolve().parent.parent / "jarvis-desk-buddy"
    dump_src = fw_dir / "tools" / "fb_dump.cpp"
    if not dump_src.exists():
        print(f"SKIPPED: Missing {dump_src}")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        exe_path = Path(tmp) / "fb_dump.exe"
        cmd = [
            compiler,
            "-std=c++17",
            "-O2",
            f"-I{fw_dir / 'include'}",
            str(dump_src),
            str(fw_dir / "src" / "monochrome_fb.cpp"),
            "-o",
            str(exe_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print("Host C++ compile failed:\n", res.stderr)
            return 1

        cpp_out = subprocess.check_output([str(exe_path)]).decode("ascii").strip().splitlines()
        py_eyes = EyeEngine(fps=50, spacing_px=16, seed=42)
        py_eyes.auto_idle_gaze = False
        now = 0
        mismatches = 0
        for idx, expr in enumerate(ALL_EXPRESSIONS):
            py_eyes.set_expression(expr, now_ms=now)
            for _ in range(45):
                now += 20
                py_eyes.update_step(now)
            py_hex = bytes(py_eyes.fb.buf).hex()
            if idx >= len(cpp_out) or cpp_out[idx] != py_hex:
                mismatches += 1
                print(f"MISMATCH on {expr.value}")
        if mismatches == 0:
            print(f"MATCH: All {len(ALL_EXPRESSIONS)} expressions match byte-for-byte between Python and C++!")
            return 0
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
