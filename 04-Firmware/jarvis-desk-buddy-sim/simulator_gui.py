"""JARVIS AI Desk Buddy — Windows 11 Desktop OLED Simulator (128x64 crisp zoom)."""

import argparse
import time
import tkinter as tk
from tkinter import ttk

from emotion_engine import EmotionEngine, ReactionDecision, StimulusType
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
        self.sm = SimulatorStateMachine(self.eyes, auto_demo=False)
        self.emotion_engine = EmotionEngine(seed=2026)
        self.emotion_enabled = True

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
        for idx, expr in enumerate(ALL_EXPRESSIONS):
            row_idx = idx // 7
            col_idx = idx % 7
            btn = tk.Button(
                expr_frame,
                text=expr.value,
                width=11,
                fg="#F8FAFC",
                bg="#1E293B",
                activebackground="#0284C7",
                activeforeground="#FFFFFF",
                relief="flat",
                font=("Segoe UI", 8, "bold"),
                command=lambda e=expr: self._on_select_expr(e),
            )
            btn.grid(row=row_idx, column=col_idx, padx=3, pady=2, sticky="ew")
            self.expr_buttons[expr] = btn
        for col_idx in range(7):
            expr_frame.columnconfigure(col_idx, weight=1)

        # Emotion & Reaction Engine (Personalità C)
        emo_frame = tk.LabelFrame(
            self.container,
            text=" Emotion & Reaction Engine — Personalità C (Molto espressivo) ",
            fg="#94A3B8",
            bg="#0B101B",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=6,
        )
        emo_frame.pack(fill="x", padx=16, pady=(2, 4))

        stim_row = tk.Frame(emo_frame, bg="#0B101B")
        stim_row.pack(fill="x", pady=(0, 4))
        stimuli_buttons = [
            ("Saluto", StimulusType.GREETING, "manual"),
            ("Complimento", StimulusType.COMPLIMENT, "manual"),
            ("Rumore", StimulusType.SUDDEN_NOISE, "mic_sim"),
            ("Pulsante", StimulusType.BUTTON_PRESS, "button_sim"),
            ("Battuta", StimulusType.JOKE, "manual"),
            ("Inattività", StimulusType.INACTIVITY, "manual"),
            ("Risveglio", StimulusType.WAKE_UP, "manual"),
            ("Errore", StimulusType.TEMP_ERROR, "manual"),
        ]
        for label, stim, src in stimuli_buttons:
            tk.Button(
                stim_row,
                text=label,
                bg="#1E293B",
                fg="#E2E8F0",
                activebackground="#0284C7",
                activeforeground="#FFFFFF",
                relief="flat",
                font=("Segoe UI", 8, "bold"),
                padx=7,
                pady=3,
                command=lambda s=stim, sr=src: self._on_trigger_stimulus(s, sr),
            ).pack(side="left", padx=2)

        cfg_row = tk.Frame(emo_frame, bg="#0B101B")
        cfg_row.pack(fill="x", pady=(2, 2))
        self.spont_var = tk.BooleanVar(value=self.emotion_engine.config.spontaneous_enabled)
        self.silent_var = tk.BooleanVar(value=self.emotion_engine.config.silent_mode)
        tk.Checkbutton(
            cfg_row,
            text="Comportamenti spontanei",
            variable=self.spont_var,
            command=self._on_toggle_emotion_cfg,
            fg="#CBD5E1",
            bg="#0B101B",
            selectcolor="#1E293B",
            activebackground="#0B101B",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(0, 10))
        tk.Checkbutton(
            cfg_row,
            text="Modalità silenziosa",
            variable=self.silent_var,
            command=self._on_toggle_emotion_cfg,
            fg="#CBD5E1",
            bg="#0B101B",
            selectcolor="#1E293B",
            activebackground="#0B101B",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(0, 10))
        tk.Button(
            cfg_row,
            text="Ripristina Default",
            bg="#334155",
            fg="#F8FAFC",
            relief="flat",
            font=("Segoe UI", 8),
            padx=8,
            command=self._on_reset_emotion_defaults,
        ).pack(side="right")

        self.emo_telemetry_var = tk.StringVar(
            value="Evento: Nessuno | Emozione: IDLE | Priorità: 0 | Durata: 0ms | Cooldown: 0ms"
        )
        tk.Label(
            emo_frame,
            textvariable=self.emo_telemetry_var,
            fg="#7DD3FC",
            bg="#0B101B",
            font=("Consolas", 8),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

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
        now_ms = self._now_ms()
        self.emotion_enabled = False
        self.sm.set_expression(expr, now_ms, disable_auto=True)
        self._highlight_active_button()

    def _on_blink(self) -> None:
        self.eyes.trigger_blink(self._now_ms())

    def _on_toggle_auto(self) -> None:
        self.sm.auto_demo = not self.sm.auto_demo
        self.sm.last_demo_switch_ms = self._now_ms()
        self.emotion_enabled = not self.sm.auto_demo
        self._highlight_active_button()

    def _on_send_cmd(self) -> None:
        self.emotion_enabled = False
        resp = self.sm.handle_command(self.cmd_entry.get(), self._now_ms())
        self.cmd_resp_var.set(f"Risposta: {resp}")
        self._highlight_active_button()

    def apply_reaction_decision(self, decision: ReactionDecision, now_ms: int) -> None:
        if decision.expression != self.eyes.expr:
            self.eyes.set_expression(decision.expression, now_ms=now_ms)
        if decision.gaze_dx is not None and decision.gaze_dy is not None:
            self.eyes.set_gaze_offset(decision.gaze_dx, decision.gaze_dy, 1500, now_ms)
        if decision.trigger_blink:
            self.eyes.trigger_blink(now_ms)
        self._highlight_active_button()

    def _on_trigger_stimulus(self, stimulus: StimulusType, source: str) -> None:
        now_ms = self._now_ms()
        self.sm.auto_demo = False
        self.emotion_enabled = True
        payload = "SLEEPY" if stimulus == StimulusType.INACTIVITY else ""
        decision = self.emotion_engine.push_stimulus(stimulus, now_ms, source=source, payload=payload)
        if decision is not None:
            self.apply_reaction_decision(decision, now_ms)
        self._update_emotion_telemetry(now_ms)

    def _on_toggle_emotion_cfg(self) -> None:
        self.emotion_engine.config.spontaneous_enabled = self.spont_var.get()
        self.emotion_engine.config.silent_mode = self.silent_var.get()
        self._update_emotion_telemetry(self._now_ms())

    def _on_reset_emotion_defaults(self) -> None:
        now_ms = self._now_ms()
        self.emotion_engine.reset_defaults(now_ms)
        self.spont_var.set(self.emotion_engine.config.spontaneous_enabled)
        self.silent_var.set(self.emotion_engine.config.silent_mode)
        self.emotion_enabled = True
        self.sm.auto_demo = False
        self.eyes.set_expression(Expression.IDLE, now_ms=now_ms)
        self._highlight_active_button()
        self._update_emotion_telemetry(now_ms)

    def _update_emotion_telemetry(self, now_ms: int) -> None:
        t = self.emotion_engine.get_telemetry(now_ms)
        self.emo_telemetry_var.set(
            f"Evento: {t['last_event']} | Emozione: {t['active_emotion']} | "
            f"Priorità: {t['priority']} | Durata: {t['remaining_ms']}ms | Cooldown: {t['cooldown_ms']}ms"
        )

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
        elif self.emotion_enabled and not self.sm.auto_demo:
            decision = self.emotion_engine.tick(now_ms)
            if decision is not None:
                self.apply_reaction_decision(decision, now_ms)
            elif self.emotion_engine.current_expression != self.eyes.expr:
                self.eyes.set_expression(self.emotion_engine.current_expression, now_ms=now_ms)
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
            self._update_emotion_telemetry(now_ms)

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
