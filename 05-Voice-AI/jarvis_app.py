"""JARVIS AI Desk Buddy — Unified Windows 11 OLED Simulator + Voice & AI Hybrid App."""

import argparse
from pathlib import Path
import queue
import sys
import tkinter as tk
from tkinter import ttk

SIM_DIR = Path(__file__).resolve().parent.parent / "04-Firmware" / "jarvis-desk-buddy-sim"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from simulator_gui import JarvisSimulatorApp  # noqa: E402

from audio_input import list_microphones  # noqa: E402
from config import load_config  # noqa: E402
from eye_bridge import EyeBridge, SimulatorQueueTransport  # noqa: E402
from voice_controller import VoiceController, VoiceEvent, VoicePhase  # noqa: E402


class JarvisUnifiedApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("JARVIS AI Desk Buddy — OLED Simulator + Voice & AI Hybrid")
        self.root.configure(bg="#0B101B")
        self.root.resizable(False, False)

        self.config = load_config()
        self._event_queue: "queue.Queue[VoiceEvent]" = queue.Queue()
        self.eye_transport = SimulatorQueueTransport()
        self.eye_bridge = EyeBridge(transport=self.eye_transport)

        main_row = tk.Frame(self.root, bg="#0B101B")
        main_row.pack(fill="both", expand=True)

        # Left column: Existing OLED Simulator (no duplicate engine!)
        self.sim_container = tk.Frame(main_row, bg="#0B101B")
        self.sim_container.pack(side="left", fill="both")
        self.sim = JarvisSimulatorApp(self.root, container=self.sim_container, scale=5)
        self.sim.sm.handle_command("AUTO:OFF", self.sim._now_ms())
        self.sim.sm.handle_command("STATE:IDLE", self.sim._now_ms())
        self.sim._highlight_active_button()

        # Right column: JARVIS Voice & AI panel
        self.voice_panel = tk.Frame(main_row, bg="#0F172A", width=440, padx=12, pady=12)
        self.voice_panel.pack(side="right", fill="both", expand=True)

        self.controller = VoiceController(
            config=self.config,
            eye_bridge=self.eye_bridge,
            on_event=self._on_voice_event_bg,
            emotion_engine=self.sim.emotion_engine,
        )

        self._build_voice_ui()
        self._refresh_hardware_status()
        self._poll_queues()

    def _on_voice_event_bg(self, event: VoiceEvent) -> None:
        self._event_queue.put(event)

    def _build_voice_ui(self) -> None:
        title = tk.Label(
            self.voice_panel,
            text="JARVIS Voice & AI",
            fg="#F8FAFC",
            bg="#0F172A",
            font=("Segoe UI", 13, "bold"),
        )
        title.pack(anchor="w", pady=(0, 6))

        self.phase_var = tk.StringVar(value="Stato: IDLE | Pronto")
        tk.Label(
            self.voice_panel,
            textvariable=self.phase_var,
            fg="#38BDF8",
            bg="#0F172A",
            font=("Consolas", 9, "bold"),
            wraplength=415,
            justify="left",
        ).pack(anchor="w", pady=(0, 2))

        self.provider_badge_var = tk.StringVar(
            value=f"Provider: {self.controller.providers[self.controller.active_provider_id].display_name}"
        )
        tk.Label(
            self.voice_panel,
            textvariable=self.provider_badge_var,
            fg="#A7F3D0",
            bg="#0F172A",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        notebook = ttk.Notebook(self.voice_panel)
        notebook.pack(fill="both", expand=True)

        tab_chat = tk.Frame(notebook, bg="#0F172A", padx=8, pady=8)
        tab_cfg = tk.Frame(notebook, bg="#0F172A", padx=8, pady=8)
        notebook.add(tab_chat, text=" Conversazione ")
        notebook.add(tab_cfg, text=" Impostazioni & Audio ")

        # --- TAB 1: CONVERSAZIONE ---
        btn_row = tk.Frame(tab_chat, bg="#0F172A")
        btn_row.pack(fill="x", pady=(0, 8))

        self.talk_btn = tk.Button(
            btn_row,
            text="Parla (Avvia Ascolto)",
            bg="#0284C7",
            fg="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=6,
            command=self._on_toggle_talk,
        )
        self.talk_btn.pack(side="left", padx=(0, 6))

        tk.Button(
            btn_row,
            text="Interrompi",
            bg="#DC2626",
            fg="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=6,
            command=self._on_interrupt,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_row,
            text="Nuova Chat",
            bg="#334155",
            fg="#F8FAFC",
            relief="flat",
            font=("Segoe UI", 9),
            padx=8,
            pady=6,
            command=self._on_new_chat,
        ).pack(side="left")

        tk.Label(
            tab_chat,
            text="Domanda testuale (funziona anche senza microfono):",
            fg="#CBD5E1",
            bg="#0F172A",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        ask_row = tk.Frame(tab_chat, bg="#0F172A")
        ask_row.pack(fill="x", pady=(4, 8))

        self.text_entry = ttk.Entry(ask_row)
        self.text_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.text_entry.insert(0, "Ciao JARVIS, come stai?")
        self.text_entry.bind("<Return>", lambda _e: self._on_send_text())

        tk.Button(
            ask_row,
            text="Invia",
            bg="#4F46E5",
            fg="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            command=self._on_send_text,
        ).pack(side="right")

        tk.Label(
            tab_chat,
            text="Testo riconosciuto / Domanda:",
            fg="#94A3B8",
            bg="#0F172A",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        self.transcript_var = tk.StringVar(value="-")
        tk.Label(
            tab_chat,
            textvariable=self.transcript_var,
            fg="#E2E8F0",
            bg="#1E293B",
            anchor="nw",
            justify="left",
            wraplength=390,
            padx=8,
            pady=6,
            height=3,
        ).pack(fill="x", pady=(2, 8))

        tk.Label(
            tab_chat,
            text="Risposta JARVIS:",
            fg="#94A3B8",
            bg="#0F172A",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        self.reply_box = tk.Text(
            tab_chat,
            height=9,
            bg="#1E293B",
            fg="#F8FAFC",
            relief="flat",
            wrap="word",
            font=("Segoe UI", 9),
            padx=8,
            pady=6,
        )
        self.reply_box.pack(fill="both", expand=True, pady=(2, 0))
        self.reply_box.insert("1.0", "Modalità Demo pronta. Scrivi una domanda o premi Parla.")
        self.reply_box.configure(state="disabled")

        # --- TAB 2: IMPOSTAZIONI & AUDIO ---
        tk.Label(tab_cfg, text="Provider AI:", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.provider_var = tk.StringVar(value=self.controller.active_provider_id)
        prov_combo = ttk.Combobox(
            tab_cfg,
            textvariable=self.provider_var,
            values=["demo", "ollama", "openai"],
            state="readonly",
        )
        prov_combo.pack(fill="x", pady=(2, 6))
        prov_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_provider_changed())

        tk.Label(tab_cfg, text="Modello AI:", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        mod_row = tk.Frame(tab_cfg, bg="#0F172A")
        mod_row.pack(fill="x", pady=(2, 6))
        self.model_var = tk.StringVar(value=self.controller.active_model)
        self.model_combo = ttk.Combobox(mod_row, textvariable=self.model_var)
        self.model_combo.pack(side="left", fill="x", expand=True, padx=(0, 6))
        tk.Button(
            mod_row,
            text="Aggiorna",
            bg="#334155",
            fg="#F8FAFC",
            relief="flat",
            command=self._refresh_models,
        ).pack(side="right")

        self.cloud_confirm_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            tab_cfg,
            text="Confermo chiamate API online (OpenAI, possibili costi)",
            variable=self.cloud_confirm_var,
            command=self._on_cloud_confirm_toggle,
            fg="#FDE68A",
            bg="#0F172A",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#FDE68A",
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(tab_cfg, text="Microfono:", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.mic_var = tk.StringVar()
        self.mic_combo = ttk.Combobox(tab_cfg, textvariable=self.mic_var, state="readonly")
        self.mic_combo.pack(fill="x", pady=(2, 4))
        self.mic_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_mic_changed())

        self.stt_status_var = tk.StringVar(value="STT: verifica...")
        tk.Label(
            tab_cfg,
            textvariable=self.stt_status_var,
            fg="#94A3B8",
            bg="#0F172A",
            font=("Segoe UI", 8),
            wraplength=390,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(tab_cfg, text="Voce TTS (Locale Piper / Windows):", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        voice_row = tk.Frame(tab_cfg, bg="#0F172A")
        voice_row.pack(fill="x", pady=(2, 6))
        self.voice_var = tk.StringVar(value=self.config.tts_voice)
        self.voice_combo = ttk.Combobox(voice_row, textvariable=self.voice_var, state="readonly")
        self.voice_combo.pack(side="left", fill="x", expand=True)
        self.voice_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_tts_cfg_changed())
        self.preview_btn = tk.Button(
            voice_row,
            text="Anteprima",
            command=self._on_preview_voice,
            bg="#1E293B",
            fg="#38BDF8",
            activebackground="#334155",
            activeforeground="#E0F2FE",
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            padx=8,
        )
        self.preview_btn.pack(side="left", padx=(6, 0))

        sliders = tk.Frame(tab_cfg, bg="#0F172A")
        sliders.pack(fill="x")
        tk.Label(sliders, text="Velocità:", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 8)).pack(side="left")
        self.rate_scale = tk.Scale(
            sliders, from_=-6, to=6, orient="horizontal", bg="#0F172A", fg="#F8FAFC",
            highlightthickness=0, command=lambda _v: self._on_tts_cfg_changed()
        )
        self.rate_scale.set(self.config.tts_rate)
        self.rate_scale.pack(side="left", fill="x", expand=True, padx=4)

        tk.Label(sliders, text="Vol:", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 8)).pack(side="left")
        self.vol_scale = tk.Scale(
            sliders, from_=0, to=100, orient="horizontal", bg="#0F172A", fg="#F8FAFC",
            highlightthickness=0, command=lambda _v: self._on_tts_cfg_changed()
        )
        self.vol_scale.set(self.config.tts_volume)
        self.vol_scale.pack(side="left", fill="x", expand=True, padx=4)

    def _refresh_hardware_status(self) -> None:
        mics = list_microphones()
        mic_names = [f"[{m.index}] {m.name}" for m in mics] if mics else ["Nessun microfono rilevato"]
        self.mic_combo["values"] = mic_names
        self.mic_var.set(mic_names[0])

        _, stt_msg = self.controller.stt.is_available()
        self.stt_status_var.set(f"STT: {stt_msg}")

        voices = self.controller.tts.list_voices()
        if voices:
            self.voice_combo["values"] = voices
            if self.config.tts_voice not in voices:
                self.config.tts_voice = voices[0]
            self.voice_var.set(self.config.tts_voice)
        else:
            self.voice_combo["values"] = ["Nessuna voce TTS locale"]
            self.voice_var.set("Nessuna voce TTS locale")

        self._refresh_models()

    def _refresh_models(self) -> None:
        pid = self.provider_var.get()
        prov = self.controller.providers[pid]
        models = prov.list_models()
        self.model_combo["values"] = models
        if models and self.model_var.get() not in models:
            self.model_var.set(models[0])
            self.controller.select_provider(pid, models[0])

    def _on_provider_changed(self) -> None:
        pid = self.provider_var.get()
        self._refresh_models()
        self.controller.select_provider(pid, self.model_var.get())
        ok, status = self.controller.providers[pid].is_available()
        self.phase_var.set(f"Provider {pid}: {status}")
        if not ok and pid == "ollama":
            self._set_reply_text(
                f"Ollama non rilevato ({status}). Resto in attesa senza passare automaticamente al cloud."
            )

    def _on_cloud_confirm_toggle(self) -> None:
        self.controller.set_openai_confirmed(self.cloud_confirm_var.get())

    def _on_mic_changed(self) -> None:
        sel = self.mic_var.get()
        if sel.startswith("[") and "]" in sel:
            try:
                idx = int(sel[1:sel.index("]")])
                self.controller.recorder.set_device_index(idx)
            except ValueError:
                pass

    def _on_tts_cfg_changed(self) -> None:
        self.config.tts_voice = self.voice_var.get()
        self.config.tts_rate = int(self.rate_scale.get())
        self.config.tts_volume = int(self.vol_scale.get())

    def _on_preview_voice(self) -> None:
        self._on_tts_cfg_changed()
        self.eye_bridge.set_state("SPEAKING")

        def _done(_err: Optional[str]) -> None:
            try:
                self.root.after(0, lambda: self.eye_bridge.set_state("IDLE"))
            except Exception:
                pass

        self.controller.tts.speak(
            "Ciaooo! Sono JARVIS! Che bello vederti! Cosa facciamo oggi?",
            voice=self.config.tts_voice,
            rate=self.config.tts_rate,
            volume=self.config.tts_volume,
            on_done=_done,
        )

    def _on_toggle_talk(self) -> None:
        if self.controller.phase == VoicePhase.LISTENING:
            self.controller.stop_push_to_talk_and_process()
        else:
            self.controller.select_provider(self.provider_var.get(), self.model_var.get())
            self.controller.start_push_to_talk()

    def _on_send_text(self) -> None:
        text = self.text_entry.get().strip()
        if not text:
            return
        self.controller.select_provider(self.provider_var.get(), self.model_var.get())
        self.controller.submit_text(text)

    def _on_interrupt(self) -> None:
        self.controller.interrupt()

    def _on_new_chat(self) -> None:
        self.controller.reset_conversation()
        self.transcript_var.set("-")
        self._set_reply_text("Nuova conversazione avviata.")

    def _set_reply_text(self, text: str) -> None:
        self.reply_box.configure(state="normal")
        self.reply_box.delete("1.0", "end")
        self.reply_box.insert("1.0", text)
        self.reply_box.configure(state="disabled")

    def _poll_queues(self) -> None:
        now_ms = self.sim._now_ms()
        self.eye_transport.drain(lambda cmd: self._handle_eye_cmd(cmd, now_ms))

        while True:
            try:
                ev = self._event_queue.get_nowait()
            except queue.Empty:
                break
            self.phase_var.set(f"Stato: {ev.phase.value} | {ev.status_text}")
            if ev.provider_label:
                self.provider_badge_var.set(f"Provider: {ev.provider_label}")
            if ev.transcript:
                self.transcript_var.set(ev.transcript)
            if ev.reply:
                self._set_reply_text(ev.reply)
            if ev.error_text:
                self._set_reply_text(f"[Avviso] {ev.error_text}")

            if ev.phase == VoicePhase.LISTENING:
                self.talk_btn.configure(text="Ferma e Invia", bg="#059669")
            else:
                self.talk_btn.configure(text="Parla (Avvia Ascolto)", bg="#0284C7")

        self.root.after(25, self._poll_queues)

    def _handle_eye_cmd(self, cmd: str, now_ms: int) -> None:
        self.sim.sm.handle_command(cmd, now_ms)
        self.sim._highlight_active_button()


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS AI Desk Buddy — Simulator + Voice & AI")
    parser.add_argument("--smoke-ms", type=int, default=0, help="Auto-close after N ms for GUI smoke tests")
    args = parser.parse_args()

    root = tk.Tk()
    app = JarvisUnifiedApp(root)
    if args.smoke_ms > 0:
        root.after(args.smoke_ms, root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
