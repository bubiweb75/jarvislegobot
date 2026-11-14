"""JARVIS AI Desk Buddy — Windows 11 Desktop OLED Simulator (128x64 crisp zoom)."""

import argparse
import time
import tkinter as tk
from tkinter import ttk

from eye_engine import ALL_EXPRESSIONS, EyeEngine, Expression, SimulatorStateMachine
from monochrome_fb import HEIGHT, WIDTH


class JarvisSimulatorApp:
    SCALE = 6  # 128x64 -> 768x384 px integer nearest-neighbor zoom (zero blur!)

    def __init__(self, root: tk.Tk, container: tk.Widget | None = None, scale: int | None = None) -> None:
        self.root = root
        self.container = container if container is not None else root
        if scale is not None:
            self.SCALE = scale
        if container is None:
            self.root.title("JARVIS AI Desk Buddy — OLED 128×64 Simulator (Windows 11)")
            self.root.configure(bg="#0B101B")
            self.root.resizable(False, False)

        self.start_monotonic = time.monotonic()
        self.eyes = EyeEngine(fps=50, spacing_px=16)
        self.sm = SimulatorStateMachine(self.eyes, auto_demo=True)

        self.fps_frames = 0
        self.fps_last_time = time.monotonic()
        self.measured_fps = 50.0

        self._build_ui()
        self._refresh_oled_image()
        self._tick()

    def _now_ms(self) -> int:
        return int((time.monotonic() - self.start_monotonic) * 1000.0)

    def _build_ui(self) -> None:
        header = tk.Frame(self.container, bg="#0B101B")
        header.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(
            header,
            text="JARVIS AI Desk Buddy — Simulatore OLED 1,3\" (128×64 Monocromatico)",
            fg="#F8FAFC",
            bg="#0B101B",
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")

        self.status_var = tk.StringVar(value="STATO: IDLE | 50.0 FPS | 128×64 | AUTO: ON")
        tk.Label(
            header,
            textvariable=self.status_var,
            fg="#38BDF8",
            bg="#0B101B",
            font=("Consolas", 10, "bold"),
        ).pack(side="right")

        # Simulated LEGO Visor Bezel Frame around crisp 128x64 OLED
        bezel = tk.Frame(self.container, bg="#161F33", bd=4, relief="ridge", padx=18, pady=18)
        bezel.pack(padx=16, pady=6)

        self.base_img = tk.PhotoImage(width=WIDTH, height=HEIGHT)
        self.zoom_img = tk.PhotoImage(width=WIDTH * self.SCALE, height=HEIGHT * self.SCALE)

        self.oled_label = tk.Label(bezel, image=self.zoom_img, bg="#000000", bd=2, relief="sunken")
        self.oled_label.pack()

        # Expression buttons
        expr_frame = tk.LabelFrame(
            self.container,
            text=" Espressioni (Clicca per testare) ",
            fg="#94A3B8",
            bg="#0B101B",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=8,
        )
        expr_frame.pack(fill="x", padx=16, pady=(6, 4))

        self.expr_buttons = {}
        for expr in ALL_EXPRESSIONS:
            btn = tk.Button(
                expr_frame,
                text=expr.value,
                width=11,
                fg="#F8FAFC",
                bg="#1E293B",
                activebackground="#0284C7",
                activeforeground="#FFFFFF",
                relief="flat",
                font=("Segoe UI", 9, "bold"),
                command=lambda e=expr: self._on_select_expr(e),
            )
            btn.pack(side="left", padx=4, pady=2)
            self.expr_buttons[expr] = btn

        # Action & Gaze Controls
        ctrl_frame = tk.LabelFrame(
            self.container,
            text=" Controlli Animazione, Sguardo & Protocollo Seriale Raspberry Pi ",
            fg="#94A3B8",
            bg="#0B101B",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=8,
        )
        ctrl_frame.pack(fill="x", padx=16, pady=(4, 12))

        row1 = tk.Frame(ctrl_frame, bg="#0B101B")
        row1.pack(fill="x", pady=(0, 6))

        tk.Button(
            row1, text="Blink", width=9, bg="#0F766E", fg="#FFFFFF", relief="flat",
            font=("Segoe UI", 9, "bold"), command=self._on_blink
        ).pack(side="left", padx=4)

        self.auto_btn = tk.Button(
            row1, text="Auto-Demo: ON", width=14, bg="#0369A1", fg="#FFFFFF", relief="flat",
            font=("Segoe UI", 9, "bold"), command=self._on_toggle_auto
        )
        self.auto_btn.pack(side="left", padx=4)

        for lbl, dx, dy in [
            ("◄ Sguardo SX", -11, 0),
            ("● Centro", 0, 0),
            ("► Sguardo DX", 11, 0),
            ("▲ Su", 0, -6),
            ("▼ Giù", 0, 6),
        ]:
            tk.Button(
                row1, text=lbl, bg="#334155", fg="#E2E8F0", relief="flat",
                font=("Segoe UI", 9),
                command=lambda x=dx, y=dy: self.eyes.set_gaze_offset(x, y, 2000, self._now_ms()),
            ).pack(side="left", padx=3)

        row2 = tk.Frame(ctrl_frame, bg="#0B101B")
        row2.pack(fill="x")

        tk.Label(row2, text="Comando Serial:", fg="#94A3B8", bg="#0B101B", font=("Consolas", 9)).pack(side="left", padx=(4, 6))
        self.cmd_entry = ttk.Entry(row2, width=32)
        self.cmd_entry.insert(0, "STATE:CURIOUS")
        self.cmd_entry.pack(side="left", padx=(0, 6))
        self.cmd_entry.bind("<Return>", lambda _evt: self._on_send_cmd())

        tk.Button(
            row2, text="Invia", width=8, bg="#4F46E5", fg="#FFFFFF", relief="flat",
            font=("Segoe UI", 9, "bold"), command=self._on_send_cmd
        ).pack(side="left", padx=(0, 10))

        self.cmd_resp_var = tk.StringVar(value="Risposta: pronto (es. STATE:HAPPY, BLINK, LOOK:10,-5, STATUS)")
        tk.Label(row2, textvariable=self.cmd_resp_var, fg="#A7F3D0", bg="#0B101B", font=("Consolas", 9)).pack(side="left")

        self._highlight_active_button()

    def _highlight_active_button(self) -> None:
        for expr, btn in self.expr_buttons.items():
            if expr == self.eyes.expr:
                btn.configure(bg="#0284C7", fg="#FFFFFF")
            else:
                btn.configure(bg="#1E293B", fg="#CBD5E1")
        self.auto_btn.configure(
            text=f"Auto-Demo: {'ON' if self.sm.auto_demo else 'OFF'}",
            bg="#0369A1" if self.sm.auto_demo else "#475569",
        )

    def _on_select_expr(self, expr: Expression) -> None:
        self.sm.set_expression(expr, self._now_ms(), disable_auto=True)
        self._highlight_active_button()

    def _on_blink(self) -> None:
        self.eyes.trigger_blink(self._now_ms())

    def _on_toggle_auto(self) -> None:
        self.sm.auto_demo = not self.sm.auto_demo
        self.sm.last_demo_switch_ms = self._now_ms()
        self._highlight_active_button()

    def _on_send_cmd(self) -> None:
        resp = self.sm.handle_command(self.cmd_entry.get(), self._now_ms())
        self.cmd_resp_var.set(f"Risposta: {resp}")
        self._highlight_active_button()

    def _refresh_oled_image(self) -> None:
        # Build crisp 128x64 monochrome PPM (P6) and integer-zoom 6x with zero blur!
        fb = self.eyes.fb
        rows = []
        for y in range(HEIGHT):
            row_cols = []
            for x in range(WIDTH):
                row_cols.append("#F8FAFC" if fb.get_pixel(x, y) else "#03060B")
            rows.append("{" + " ".join(row_cols) + "}")
        self.base_img.put(" ".join(rows))
        # Nearest-neighbor integer zoom onto zoom_img
        self.zoom_img.tk.call(self.zoom_img, "copy", self.base_img, "-zoom", self.SCALE, self.SCALE)

    def _tick(self) -> None:
        now_ms = self._now_ms()
        changed = self.sm.update(now_ms)
        if changed is not None:
            self._highlight_active_button()

        if self.eyes.update(now_ms):
            self._refresh_oled_image()
            self.fps_frames += 1

        now_t = time.monotonic()
        if (now_t - self.fps_last_time) >= 0.5:
            self.measured_fps = self.fps_frames / (now_t - self.fps_last_time)
            self.fps_frames = 0
            self.fps_last_time = now_t
            self.status_var.set(
                f"STATO: {self.eyes.expr.value} | {self.measured_fps:.1f} FPS | 128×64 | AUTO: {'ON' if self.sm.auto_demo else 'OFF'}"
            )

        self.root.after(15, self._tick)


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS AI Desk Buddy Windows 11 OLED Simulator")
    parser.add_argument("--smoke-ms", type=int, default=0, help="Auto-close after N ms (for automated GUI smoke verification)")
    args = parser.parse_args()

    root = tk.Tk()
    app = JarvisSimulatorApp(root)
    if args.smoke_ms > 0:
        root.after(args.smoke_ms, root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
