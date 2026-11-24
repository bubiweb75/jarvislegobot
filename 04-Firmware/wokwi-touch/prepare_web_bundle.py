"""Prepare a self-contained Wokwi Web project folder & ZIP for FASE 11.1 Touch."""

from __future__ import annotations

from pathlib import Path
import shutil
import zipfile


WEB_DEFINES = (
    "// Auto-added for Wokwi Web Arduino builder (FASE 11.1 Touch)\n"
    "#ifndef OLED_DRIVER_SSD1306\n"
    "#define OLED_DRIVER_SSD1306 1\n"
    "#endif\n"
    "#ifndef WOKWI_SIM\n"
    "#define WOKWI_SIM 1\n"
    "#endif\n"
    "#ifndef JARVIS_ENABLE_TOUCH\n"
    "#define JARVIS_ENABLE_TOUCH 1\n"
    "#endif\n\n"
)


def main() -> int:
    here = Path(__file__).resolve().parent
    fw_root = here.parent / "jarvis-desk-buddy"
    src_dir = fw_root / "src"
    inc_dir = fw_root / "include"
    out_dir = here / "web-project"
    zip_path = here / "jarvis-wokwi-touch-web.zip"

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(here / "diagram.json", out_dir / "diagram.json")
    (out_dir / "libraries.txt").write_text("U8g2\n", encoding="utf-8")

    for hdr in sorted(inc_dir.glob("*.h")):
        text = hdr.read_text(encoding="utf-8")
        if hdr.name in ("display_driver.h", "state_machine.h"):
            text = WEB_DEFINES + text
        (out_dir / hdr.name).write_text(text, encoding="utf-8")

    for cpp in sorted(src_dir.glob("*.cpp")):
        text = cpp.read_text(encoding="utf-8")
        if cpp.name == "main.cpp":
            (out_dir / "sketch.ino").write_text(WEB_DEFINES + text, encoding="utf-8")
        else:
            (out_dir / cpp.name).write_text(text, encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in sorted(out_dir.iterdir()):
            zf.write(item, arcname=item.name)

    print(f"Prepared {out_dir} and {zip_path} ({zip_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
