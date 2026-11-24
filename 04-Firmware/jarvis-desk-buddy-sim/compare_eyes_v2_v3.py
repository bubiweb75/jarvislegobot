"""Visual & quantitative comparison: JARVIS Eyes 2.0 vs Eyes 3.0.

Uses two genuinely distinct engine implementations:
- Left:  EyeEngineV2Baseline (Eyes 2.0 rounded-rect baseline)
- Right: EyeEngine (Eyes 3.0 Organic Visor Companion — real engine)

Both render strictly in 128x64 monochrome white-on-black (#FFFFFF on #000000)
at identical scale, state, and timestamp.

Usage:
    python compare_eyes_v2_v3.py --cli
    python compare_eyes_v2_v3.py --gui
    python compare_eyes_v2_v3.py --save-gallery path/to/gallery.png
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import sys
import tkinter as tk
from tkinter import ttk
from typing import List, Tuple

from eye_engine import ALL_EXPRESSIONS, Expression, EyeEngine, VisualProfile
from eye_engine_v2_baseline import EyeEngineV2Baseline
from monochrome_fb import HEIGHT, WIDTH


@dataclass
class ComparisonSample:
    label: str
    v2_lit: int
    v3_lit: int
    diff_pixels: int
    v3_render_us: int


def _step_pair(v2: EyeEngineV2Baseline, v3: EyeEngine, now_ms: int, steps: int, dt_ms: int = 33) -> int:
    for _ in range(steps):
        now_ms += dt_ms
        v2.update_step(now_ms)
        v3.update_step(now_ms)
    return now_ms


def _count_diff(buf_a: bytearray, buf_b: bytearray) -> int:
    return sum((a ^ b).bit_count() for a, b in zip(buf_a, buf_b))


def run_cli_comparison() -> List[ComparisonSample]:
    v2 = EyeEngineV2Baseline(fps=30, spacing_px=14, seed=2026)
    v3 = EyeEngine(fps=30, spacing_px=12, seed=2026)
    v2.auto_idle_gaze = False
    v3.auto_idle_gaze = False
    v3.set_micro_expressions_enabled(False)

    samples: List[ComparisonSample] = []
    now = 0
    for expr in ALL_EXPRESSIONS:
        v2.set_expression(expr, now_ms=now)
        v3.set_expression(expr, now_ms=now)
        now = _step_pair(v2, v3, now, 30)
        samples.append(
            ComparisonSample(
                label=expr.value,
                v2_lit=v2.fb.count_lit_pixels(),
                v3_lit=v3.fb.count_lit_pixels(),
                diff_pixels=_count_diff(v2.fb.buf, v3.fb.buf),
                v3_render_us=v3.last_render_us,
            )
        )

    # Synchronized Blink & Gaze checks
    v2.set_expression(Expression.IDLE, now_ms=now)
    v3.set_expression(Expression.IDLE, now_ms=now)
    now = _step_pair(v2, v3, now, 20)
    v2.trigger_blink(now)
    v3.trigger_blink(now)
    now = _step_pair(v2, v3, now, 4)
    samples.append(
        ComparisonSample(
            label="ANIM:BLINK",
            v2_lit=v2.fb.count_lit_pixels(),
            v3_lit=v3.fb.count_lit_pixels(),
            diff_pixels=_count_diff(v2.fb.buf, v3.fb.buf),
            v3_render_us=v3.last_render_us,
        )
    )
    now = _step_pair(v2, v3, now, 16)
    v2.set_gaze_offset(9, -4, 2000, now)
    v3.set_gaze_offset(9, -4, 2000, now)
    now = _step_pair(v2, v3, now, 18)
    samples.append(
        ComparisonSample(
            label="ANIM:LOOK(9,-4)",
            v2_lit=v2.fb.count_lit_pixels(),
            v3_lit=v3.fb.count_lit_pixels(),
            diff_pixels=_count_diff(v2.fb.buf, v3.fb.buf),
            v3_render_us=v3.last_render_us,
        )
    )
    return samples


def _write_png_rgb(path: str, width: int, height: int, rgb_bytes: bytearray) -> None:
    import struct
    import zlib

    def _chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw.extend(rgb_bytes[y * stride : (y + 1) * stride])

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def save_gallery_png(output_path: str) -> None:
    scale = 2
    pad_x = 12
    col_gap = 10
    row_gap = 12
    pair_w = WIDTH * scale * 2 + col_gap
    img_w = pad_x * 2 + 2 * pair_w + 20
    img_h = 20 + 7 * (HEIGHT * scale + row_gap)

    buf = bytearray([24, 26, 30] * (img_w * img_h))

    def _fill_rect(x0: int, y0: int, w: int, h: int, r: int, g: int, b: int) -> None:
        for yy in range(max(0, y0), min(img_h, y0 + h)):
            row_off = yy * img_w * 3
            for xx in range(max(0, x0), min(img_w, x0 + w)):
                idx = row_off + xx * 3
                buf[idx], buf[idx + 1], buf[idx + 2] = r, g, b

    v2 = EyeEngineV2Baseline(fps=30, spacing_px=14, seed=2026)
    v3 = EyeEngine(fps=30, spacing_px=12, seed=2026)
    v2.auto_idle_gaze = False
    v3.auto_idle_gaze = False
    v3.set_micro_expressions_enabled(False)

    now = 0
    for idx, expr in enumerate(ALL_EXPRESSIONS):
        v2.set_expression(expr, now_ms=now)
        v3.set_expression(expr, now_ms=now)
        now = _step_pair(v2, v3, now, 30)

        r = idx // 2
        c = idx % 2
        ox = pad_x + c * (pair_w + 20)
        oy = 12 + r * (HEIGHT * scale + row_gap)

        for side_idx, eng in enumerate((v2, v3)):
            bx = ox + side_idx * (WIDTH * scale + col_gap)
            by = oy
            _fill_rect(bx - 1, by - 1, WIDTH * scale + 2, HEIGHT * scale + 2, 70, 75, 85)
            _fill_rect(bx, by, WIDTH * scale, HEIGHT * scale, 0, 0, 0)
            for py in range(HEIGHT):
                for px in range(WIDTH):
                    if eng.fb.get_pixel(px, py):
                        _fill_rect(bx + px * scale, by + py * scale, scale, scale, 255, 255, 255)

    _write_png_rgb(output_path, img_w, img_h, buf)


def _draw_fb_tk(canvas: tk.Canvas, fb, scale: int) -> None:
    canvas.delete("all")
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if fb.get_pixel(x, y):
                x0 = x * scale
                y0 = y * scale
                canvas.create_rectangle(x0, y0, x0 + scale, y0 + scale, fill="#FFFFFF", outline="")


def run_gui_comparison() -> None:
    root = tk.Tk()
    root.title("JARVIS Eyes 2.0 vs Eyes 3.0 — Confronto Monocromatico 128x64")
    root.configure(bg="#14161a")

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=8, pady=8)

    # --- TAB 1: GALLERIA 14 ESPRESSIONI ---
    tab_gallery = tk.Frame(nb, bg="#14161a")
    nb.add(tab_gallery, text="Galleria 14 Espressioni")

    v2_g = EyeEngineV2Baseline(fps=30, spacing_px=14, seed=2026)
    v3_g = EyeEngine(fps=30, spacing_px=12, seed=2026)
    v2_g.auto_idle_gaze = False
    v3_g.auto_idle_gaze = False
    v3_g.set_micro_expressions_enabled(False)

    g_scale = 2
    now_g = 0
    for idx, expr in enumerate(ALL_EXPRESSIONS):
        v2_g.set_expression(expr, now_ms=now_g)
        v3_g.set_expression(expr, now_ms=now_g)
        now_g = _step_pair(v2_g, v3_g, now_g, 30)

        row = idx // 2
        col = idx % 2
        cell = tk.Frame(tab_gallery, bg="#1c2026", padx=6, pady=4, relief="groove", bd=1)
        cell.grid(row=row, column=col, padx=5, pady=4, sticky="nsew")
        tk.Label(cell, text=f"{expr.value}  (2.0 sx | 3.0 dx)", fg="#e2e8f0", bg="#1c2026", font=("Segoe UI", 9, "bold")).pack(anchor="w")

        pair_row = tk.Frame(cell, bg="#1c2026")
        pair_row.pack()
        c2 = tk.Canvas(pair_row, width=WIDTH * g_scale, height=HEIGHT * g_scale, bg="#000000", highlightthickness=1, highlightbackground="#3a414d")
        c2.pack(side="left", padx=(0, 6))
        c3 = tk.Canvas(pair_row, width=WIDTH * g_scale, height=HEIGHT * g_scale, bg="#000000", highlightthickness=1, highlightbackground="#3a414d")
        c3.pack(side="left")
        _draw_fb_tk(c2, v2_g.fb, g_scale)
        _draw_fb_tk(c3, v3_g.fb, g_scale)

    # --- TAB 2: DEMO ANIMATA LIVE ---
    tab_anim = tk.Frame(nb, bg="#14161a", padx=12, pady=12)
    nb.add(tab_anim, text="Demo Animata (Blink / Gaze / Transizioni)")

    v2 = EyeEngineV2Baseline(fps=30, spacing_px=14, seed=2026)
    v3 = EyeEngine(fps=30, spacing_px=12, seed=2026)
    v3.set_visual_profile(VisualProfile.LIVELY)

    scale = 4
    tk.Label(tab_anim, text="Eyes 2.0 (Baseline)", fg="#ffffff", bg="#14161a", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, pady=(0, 6))
    tk.Label(tab_anim, text="Eyes 3.0 (Organic Visor Companion)", fg="#ffffff", bg="#14161a", font=("Segoe UI", 11, "bold")).grid(row=0, column=1, pady=(0, 6))

    c_v2 = tk.Canvas(tab_anim, width=WIDTH * scale, height=HEIGHT * scale, bg="#000000", highlightthickness=1, highlightbackground="#3a414d")
    c_v2.grid(row=1, column=0, padx=8)
    c_v3 = tk.Canvas(tab_anim, width=WIDTH * scale, height=HEIGHT * scale, bg="#000000", highlightthickness=1, highlightbackground="#3a414d")
    c_v3.grid(row=1, column=1, padx=8)

    # 1:1 approximate 1.3" physical scale preview
    real_row = tk.Frame(tab_anim, bg="#14161a")
    real_row.grid(row=2, column=0, columnspan=2, pady=(8, 4))
    tk.Label(real_row, text="Anteprima 1:1 OLED (~1.3\"): ", fg="#9aa4b2", bg="#14161a", font=("Segoe UI", 9)).pack(side="left")
    c_real_2 = tk.Canvas(real_row, width=WIDTH, height=HEIGHT, bg="#000000", highlightthickness=1, highlightbackground="#3a414d")
    c_real_2.pack(side="left", padx=6)
    c_real_3 = tk.Canvas(real_row, width=WIDTH, height=HEIGHT, bg="#000000", highlightthickness=1, highlightbackground="#3a414d")
    c_real_3.pack(side="left", padx=6)

    status_var = tk.StringVar(value="IDLE (auto-ciclo attivo)")
    tk.Label(tab_anim, textvariable=status_var, fg="#e2e8f0", bg="#14161a", font=("Segoe UI", 10)).grid(row=3, column=0, columnspan=2, pady=6)

    ctrl = tk.Frame(tab_anim, bg="#14161a")
    ctrl.grid(row=4, column=0, columnspan=2, pady=4)
    state = {"now": 0, "idx": 0, "ticks": 0, "auto": True}

    def _set_expr(expr: Expression) -> None:
        state["auto"] = False
        v2.set_expression(expr, now_ms=state["now"])
        v3.set_expression(expr, now_ms=state["now"])
        status_var.set(f"Espressione: {expr.value} | Micro-expr 3.0: {v3.micro_expr.value}")

    for idx_e, expr in enumerate(ALL_EXPRESSIONS):
        tk.Button(ctrl, text=expr.value, width=11, command=lambda ex=expr: _set_expr(ex)).grid(row=idx_e // 7, column=idx_e % 7, padx=2, pady=2)

    actions = tk.Frame(tab_anim, bg="#14161a")
    actions.grid(row=5, column=0, columnspan=2, pady=6)
    tk.Button(actions, text="BLINK", command=lambda: (v2.trigger_blink(state["now"]), v3.trigger_blink(state["now"]))).pack(side="left", padx=4)
    tk.Button(actions, text="LOOK SX", command=lambda: (v2.set_gaze_offset(-9, 0, 2000, state["now"]), v3.set_gaze_offset(-9, 0, 2000, state["now"]))).pack(side="left", padx=4)
    tk.Button(actions, text="LOOK DX", command=lambda: (v2.set_gaze_offset(9, -2, 2000, state["now"]), v3.set_gaze_offset(9, -2, 2000, state["now"]))).pack(side="left", padx=4)
    tk.Button(actions, text="CENTRO", command=lambda: (v2.set_gaze_offset(0, 0, 1000, state["now"]), v3.set_gaze_offset(0, 0, 1000, state["now"]))).pack(side="left", padx=4)
    tk.Button(actions, text="AUTO CICLO", command=lambda: state.__setitem__("auto", True)).pack(side="left", padx=4)

    demo_order = [Expression.IDLE, Expression.HAPPY, Expression.CURIOUS, Expression.SURPRISED, Expression.THINKING, Expression.SLEEPY, Expression.MISCHIEVOUS, Expression.LOVE]

    def _tick() -> None:
        state["now"] += 33
        state["ticks"] += 1
        if state["auto"] and state["ticks"] % 75 == 0:
            state["idx"] = (state["idx"] + 1) % len(demo_order)
            nxt = demo_order[state["idx"]]
            v2.set_expression(nxt, now_ms=state["now"])
            v3.set_expression(nxt, now_ms=state["now"])
            status_var.set(f"Auto: {nxt.value} | Micro-expr 3.0: {v3.micro_expr.value}")
        v2.update_step(state["now"])
        v3.update_step(state["now"])
        _draw_fb_tk(c_v2, v2.fb, scale)
        _draw_fb_tk(c_v3, v3.fb, scale)
        _draw_fb_tk(c_real_2, v2.fb, 1)
        _draw_fb_tk(c_real_3, v3.fb, 1)
        root.after(33, _tick)

    root.after(33, _tick)
    root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser(description="JARVIS Eyes 2.0 vs 3.0 Monochrome Comparison")
    parser.add_argument("--gui", action="store_true", help="Launch 14-expression gallery & animated demo")
    parser.add_argument("--cli", action="store_true", help="Print pixel comparison table across all 14 expressions")
    parser.add_argument("--save-gallery", type=str, default="", help="Save 14-expression monochrome comparison PNG")
    args = parser.parse_args()

    if args.save_gallery:
        save_gallery_png(args.save_gallery)
        print(f"Saved gallery PNG to {args.save_gallery}")
        return 0

    if args.gui:
        run_gui_comparison()
        return 0

    samples = run_cli_comparison()
    print(f"{'Expression / Scenario':<20} | {'V2 lit':>6} | {'V3 lit':>6} | {'Diff px':>7} | {'V3 render us':>12}")
    print("-" * 66)
    for s in samples:
        print(f"{s.label:<20} | {s.v2_lit:>6} | {s.v3_lit:>6} | {s.diff_pixels:>7} | {s.v3_render_us:>12}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
