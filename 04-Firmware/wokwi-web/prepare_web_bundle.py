"""Prepare a self-contained Wokwi Web project folder & ZIP from jarvis-desk-buddy sources.

Allows saving and sharing JARVIS LEGO BOT directly inside a wokwi.com account without
duplicating source logic permanently in git (re-generates from 04-Firmware/jarvis-desk-buddy).
"""

from __future__ import annotations

from pathlib import Path
import shutil
import zipfile


WEB_DEFINES = (
    "// Auto-added for Wokwi Web Arduino builder (no platformio.ini build_flags)\n"
    "#ifndef OLED_DRIVER_SSD1306\n"
    "#define OLED_DRIVER_SSD1306 1\n"
    "#endif\n"
    "#ifndef WOKWI_SIM\n"
    "#define WOKWI_SIM 1\n"
    "#endif\n\n"
)


def main() -> int:
    here = Path(__file__).resolve().parent
    fw_root = here.parent / "jarvis-desk-buddy"
    src_dir = fw_root / "src"
    inc_dir = fw_root / "include"
    out_dir = here / "web-project"
    zip_path = here / "jarvis-wokwi-web.zip"

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Copy diagram.json & create libraries.txt for Wokwi Web
    shutil.copy2(here / "diagram.json", out_dir / "diagram.json")
    (out_dir / "libraries.txt").write_text("U8g2\n", encoding="utf-8")

    # Copy headers, injecting SSD1306/WOKWI_SIM defines into display_driver.h & state_machine.h
    for hdr in sorted(inc_dir.glob("*.h")):
        text = hdr.read_text(encoding="utf-8")
        if hdr.name in ("display_driver.h", "state_machine.h"):
            text = WEB_DEFINES + text
        (out_dir / hdr.name).write_text(text, encoding="utf-8")

    # Copy C++ sources, converting main.cpp -> sketch.ino for Wokwi Web editor
    for cpp in sorted(src_dir.glob("*.cpp")):
        text = cpp.read_text(encoding="utf-8")
        if cpp.name == "main.cpp":
            (out_dir / "sketch.ino").write_text(WEB_DEFINES + text, encoding="utf-8")
        else:
            (out_dir / cpp.name).write_text(text, encoding="utf-8")

    # Create ZIP bundle for easy download/backup
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in sorted(out_dir.iterdir()):
            zf.write(item, arcname=item.name)

    files_list = ", ".join(p.name for p in sorted(out_dir.iterdir()))
    print(f"Prepared {out_dir} ({files_list})")
    print(f"Created ZIP bundle: {zip_path} ({zip_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
