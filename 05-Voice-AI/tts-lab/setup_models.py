"""Downloads official Piper binary, Italian Piper models, and Kokoro-82M ONNX files into tts-lab/."""

from pathlib import Path
import zipfile

import httpx

LAB_DIR = Path(__file__).resolve().parent

DOWNLOADS = [
    (
        "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip",
        LAB_DIR / "bin" / "piper_windows_amd64.zip",
    ),
    (
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/it/it_IT/paola/medium/it_IT-paola-medium.onnx",
        LAB_DIR / "models" / "piper" / "it_IT-paola-medium.onnx",
    ),
    (
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/it/it_IT/paola/medium/it_IT-paola-medium.onnx.json",
        LAB_DIR / "models" / "piper" / "it_IT-paola-medium.onnx.json",
    ),
    (
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/it/it_IT/riccardo/x_low/it_IT-riccardo-x_low.onnx",
        LAB_DIR / "models" / "piper" / "it_IT-riccardo-x_low.onnx",
    ),
    (
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/it/it_IT/riccardo/x_low/it_IT-riccardo-x_low.onnx.json",
        LAB_DIR / "models" / "piper" / "it_IT-riccardo-x_low.onnx.json",
    ),
    (
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
        LAB_DIR / "models" / "kokoro" / "kokoro-v1.0.onnx",
    ),
    (
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
        LAB_DIR / "models" / "kokoro" / "voices-v1.0.bin",
    ),
]


def download_file(client: httpx.Client, url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 100:
        print(f"SKIP (exists): {dest.name} ({dest.stat().st_size} bytes)")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"Downloading {dest.name}...")
    with client.stream("GET", url) as resp:
        resp.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in resp.iter_bytes(chunk_size=1024 * 256):
                f.write(chunk)
    tmp.replace(dest)
    print(f"OK: {dest.name} ({dest.stat().st_size} bytes)")


def main() -> int:
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        for url, dest in DOWNLOADS:
            download_file(client, url, dest)

    zip_path = LAB_DIR / "bin" / "piper_windows_amd64.zip"
    piper_exe = LAB_DIR / "bin" / "piper" / "piper.exe"
    if not piper_exe.exists():
        print("Extracting piper_windows_amd64.zip...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(LAB_DIR / "bin")
    print("Piper ready:", piper_exe.exists(), piper_exe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
