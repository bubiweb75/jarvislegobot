"""Generates a crisp pixel-perfect SVG preview of all 7 JARVIS OLED expressions."""

from pathlib import Path

from eye_engine import ALL_EXPRESSIONS, EyeEngine
from monochrome_fb import HEIGHT, WIDTH


def render_7_expressions_svg(out_path: Path) -> None:
    scale = 3
    panel_w = WIDTH * scale   # 384
    panel_h = HEIGHT * scale  # 192
    cols = 2
    rows = 4
    pad = 20
    header_h = 28

    svg_w = pad + cols * (panel_w + pad)
    svg_h = pad + rows * (panel_h + header_h + pad)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}" style="background:#0B101B;font-family:Segoe UI,Arial,sans-serif">',
        f'<text x="{pad}" y="22" fill="#F8FAFC" font-size="16" font-weight="bold">'
        f'JARVIS AI Desk Buddy — Anteprima 7 Espressioni OLED (128x64, scala 3x)</text>',
    ]

    eyes = EyeEngine(fps=50, spacing_px=16, seed=42)
    eyes.auto_idle_gaze = False
    now = 0

    for idx, expr in enumerate(ALL_EXPRESSIONS):
        col = idx % cols
        row = idx // cols
        ox = pad + col * (panel_w + pad)
        oy = pad + 18 + row * (panel_h + header_h + pad)

        eyes.set_expression(expr, now_ms=now)
        for _ in range(45):
            now += 20
            eyes.update_step(now)

        lit = eyes.fb.count_lit_pixels()
        lines.append(
            f'<text x="{ox}" y="{oy + 16}" fill="#38BDF8" font-size="13" font-weight="bold">'
            f'{idx + 1}. {expr.value} ({lit} px)</text>'
        )
        screen_y = oy + header_h
        lines.append(
            f'<rect x="{ox - 2}" y="{screen_y - 2}" width="{panel_w + 4}" height="{panel_h + 4}" '
            f'rx="6" fill="#000000" stroke="#334155" stroke-width="2"/>'
        )

        # Run-length encode lit horizontal spans for compact, crisp SVG
        for y in range(HEIGHT):
            x = 0
            while x < WIDTH:
                if eyes.fb.get_pixel(x, y):
                    x_start = x
                    while x < WIDTH and eyes.fb.get_pixel(x, y):
                        x += 1
                    rw = (x - x_start) * scale
                    lines.append(
                        f'<rect x="{ox + x_start * scale}" y="{screen_y + y * scale}" '
                        f'width="{rw}" height="{scale}" fill="#FFFFFF"/>'
                    )
                else:
                    x += 1

    lines.append("</svg>")
    out_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    import os
    artifact_svg = Path(
        os.environ.get(
            "JARVIS_PREVIEW_OUT",
            Path(__file__).resolve().parent / "jarvis_7_expressions_preview.svg",
        )
    )
    render_7_expressions_svg(artifact_svg)
    print(f"Generated {artifact_svg}")
