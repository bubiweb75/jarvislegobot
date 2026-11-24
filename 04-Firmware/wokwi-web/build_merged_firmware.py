"""Generate a single merged ESP32-S3 binary for Wokwi Web ('Upload Firmware and Start Simulation...').

Combines bootloader.bin (0x0000), partitions.bin (0x8000), optional boot_app0.bin (0xE000),
and firmware.bin (0x10000) from 04-Firmware/wokwi-simulation/.pio/build/esp32s3_wokwi/.
"""

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
    build_dir = here.parent / "wokwi-simulation" / ".pio" / "build" / "esp32s3_wokwi"
    bootloader = build_dir / "bootloader.bin"
    partitions = build_dir / "partitions.bin"
    firmware = build_dir / "firmware.bin"
    output = here / "jarvis-esp32s3-wokwi-merged.bin"

    for required in (bootloader, partitions, firmware):
        if not required.exists():
            print(f"ERROR: Missing compiled binary: {required}", file=sys.stderr)
            print("Run: python -m platformio run -d 04-Firmware/wokwi-simulation -e esp32s3_wokwi", file=sys.stderr)
            return 1

    esptool = _find_esptool()
    cmd: list[str] = []
    if esptool.suffix == ".py":
        cmd.extend([sys.executable, str(esptool)])
    else:
        cmd.append(str(esptool))

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

    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd, check=False)
    if res.returncode != 0:
        return res.returncode

    print(f"Generated merged firmware: {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
