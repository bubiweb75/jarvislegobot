"""Generate merged ESP32-S3 binary for Wokwi Web (FASE 11.1 Touch simulation)."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys


def _find_esptool() -> Path:
    pio_esptool = Path.home() / ".platformio" / "packages" / "tool-esptool" / "esptool.exe"
    if pio_esptool.exists():
        return pio_esptool
    pio_esptool_py = Path.home() / ".platformio" / "packages" / "tool-esptoolpy" / "esptool.py"
    if pio_esptool_py.exists():
        return pio_esptool_py
    which_tool = shutil.which("esptool") or shutil.which("esptool.py")
    if which_tool:
        return Path(which_tool)
    raise FileNotFoundError("Could not find esptool in PlatformIO packages or PATH.")


def _find_boot_app0() -> Path | None:
    candidate = (
        Path.home()
        / ".platformio"
        / "packages"
        / "framework-arduinoespressif32"
        / "tools"
        / "partitions"
        / "boot_app0.bin"
    )
    return candidate if candidate.exists() else None


def main() -> int:
    here = Path(__file__).resolve().parent
    build_dir = here / ".pio" / "build" / "esp32s3_wokwi_touch"
    bootloader = build_dir / "bootloader.bin"
    partitions = build_dir / "partitions.bin"
    firmware = build_dir / "firmware.bin"
    output = here / "jarvis-esp32s3-wokwi-touch-merged.bin"

    for required in (bootloader, partitions, firmware):
        if not required.exists():
            print(f"ERROR: Missing compiled binary: {required}", file=sys.stderr)
            print("Run: python -m platformio run -d 04-Firmware/wokwi-touch -e esp32s3_wokwi_touch", file=sys.stderr)
            return 1

    esptool = _find_esptool()
    cmd: list[str] = [sys.executable, str(esptool)] if esptool.suffix == ".py" else [str(esptool)]
    cmd.extend([
        "--chip", "esp32s3",
        "merge-bin",
        "-o", str(output),
        "--flash-mode", "qio",
        "--flash-freq", "80m",
        "--flash-size", "16MB",
        "0x0000", str(bootloader),
        "0x8000", str(partitions),
    ])
    boot_app0 = _find_boot_app0()
    if boot_app0 is not None:
        cmd.extend(["0xe000", str(boot_app0)])
    cmd.extend(["0x10000", str(firmware)])

    res = subprocess.run(cmd, check=False)
    if res.returncode != 0:
        return res.returncode

    print(f"Generated merged firmware: {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
