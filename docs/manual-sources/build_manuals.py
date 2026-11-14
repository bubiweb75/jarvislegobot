"""Repeatable PDF generator for JARVIS LEGO BOT manuals using Chrome headless."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT.parent / "manuals"

CHROME_CANDIDATES = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]

MANUALS = [
    ("01_Presentazione_Generale_JARVIS.html", "01_Presentazione_Generale_JARVIS.pdf"),
    ("02_Elettronica_e_Collegamenti.html", "02_Elettronica_e_Collegamenti.pdf"),
    ("03_Costruzione_LEGO_Companion_v2.html", "03_Costruzione_LEGO_Companion_v2.pdf"),
    ("04_Software_e_Utilizzo_Windows.html", "04_Software_e_Utilizzo_Windows.pdf"),
    ("05_Collaudo_e_Manutenzione.html", "05_Collaudo_e_Manutenzione.pdf"),
    ("06_Personalita_Emozioni_e_Reazioni.html", "06_Personalita_Emozioni_e_Reazioni.pdf"),
]


def find_browser() -> Path:
    for p in CHROME_CANDIDATES:
        if p.is_file():
            return p
    raise FileNotFoundError("Neither Google Chrome nor Microsoft Edge was found.")


def main() -> int:
    browser = find_browser()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Using browser: {browser}")

    for html_name, pdf_name in MANUALS:
        html_path = ROOT / html_name
        pdf_path = OUT_DIR / pdf_name
        if not html_path.is_file():
            raise FileNotFoundError(f"Missing HTML source: {html_path}")

        cmd = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--allow-file-access-from-files",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if res.returncode != 0 or not pdf_path.is_file() or pdf_path.stat().st_size < 1000:
            print(f"FAILED {pdf_name}: rc={res.returncode} stderr={res.stderr}")
            return 1
        print(f"OK: {pdf_name} ({pdf_path.stat().st_size // 1024} KB)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
