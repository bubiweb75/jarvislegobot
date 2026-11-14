"""JARVIS AI Desk Buddy — Unified Windows 11 OLED Simulator + Voice & AI Hybrid App."""

import argparse
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional

SIM_DIR = Path(__file__).resolve().parent.parent / "04-Firmware" / "jarvis-desk-buddy-sim"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from simulator_gui import JarvisSimulatorApp  # noqa: E402

from audio_input import list_microphones  # noqa: E402
from config import load_config  # noqa: E402
from control_center_panels import (  # noqa: E402
    ACCENT_CYAN,
    BG_CARD,
    BG_DARK,
    BG_PANEL,
    TEXT_PRIMARY,
    DashboardPanel,
    DiagnosticsPanel,
    MemoryPanel,
    PersonalityPanel,
    SensorStatusPanel,
    SimulatorControlPanel,
    load_personality_config_json,
)
from conversation_engine import ConversationEngine2  # noqa: E402
from eye_bridge import EyeBridge, SimulatorQueueTransport  # noqa: E402
from memory_engine import MemoryConfig, MemoryEngine  # noqa: E402
from stt_providers import MockSTTProvider  # noqa: E402
from tts_providers import MockTTSProvider  # noqa: E402
from voice_controller import VoiceController, VoiceEvent, VoicePhase  # noqa: E402


class JarvisUnifiedApp:
    SPONTANEOUS_CHECK_INTERVAL_MS = 60_000
    STARTUP_GRACE_MS = 60_000

    def __init__(
        self,
        root: tk.Tk,
        data_dir: Optional[Path] = None,
        confirm_wipe_fn: Optional[Callable[[], bool]] = None,
        demo_mode: bool = False,
        no_spontaneous: bool = False,
    ) -> None:
        self.root = root
        self._demo_mode = bool(demo_mode)
        self._no_spontaneous = bool(no_spontaneous)
        self.root.title("JARVIS Control Center — BRAIN 2.0" + (" [DEMO LEGGERA]" if self._demo_mode else ""))
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)
        self.root.minsize(980, 620)
        self._apply_dark_theme()

        self._data_dir = data_dir or (Path(__file__).resolve().parent / "data")
        self._memory_cfg_path = self._data_dir / "memory_config.json"
        self._personality_cfg_path = self._data_dir / "personality_config.json"
        self._confirm_wipe_fn = confirm_wipe_fn

        self._closed = False
        self._last_error_text = ""
        self._poll_timer_id: Optional[str] = None
        self._spontaneous_timer_id: Optional[str] = None
        self._probe_timer_id: Optional[str] = None
        self._probe_running = False
        self._ui_tick_counter = 0

        self.config = load_config()
        if self._demo_mode:
            self.config.ai_provider = "demo"
        self._event_queue: "queue.Queue[VoiceEvent]" = queue.Queue()
        self._probe_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self.eye_transport = SimulatorQueueTransport()
        self.eye_bridge = EyeBridge(transport=self.eye_transport)

        main_row = tk.Frame(self.root, bg=BG_DARK)
        main_row.pack(fill="both", expand=True)

        # Left column: Existing OLED Simulator (no duplicate engine!)
        self.sim_container = tk.Frame(main_row, bg=BG_DARK)
        self.sim_container.pack(side="left", fill="both")
        self.sim = JarvisSimulatorApp(self.root, container=self.sim_container, scale=5)
        self.sim.sm.handle_command("AUTO:OFF", self.sim._now_ms())
        self.sim.sm.handle_command("STATE:IDLE", self.sim._now_ms())
        self.sim._highlight_active_button()

        # Load persisted PersonalityConfig onto shared PersonalityProfile
        loaded_pers = load_personality_config_json(self._personality_cfg_path)
        self.sim.personality.update_config(loaded_pers)

        # Right column: JARVIS Control Center
        self.voice_panel = tk.Frame(main_row, bg=BG_PANEL, width=470, padx=12, pady=12)
        self.voice_panel.pack(side="right", fill="both", expand=True)

        self.controller = VoiceController(
            config=self.config,
            eye_bridge=self.eye_bridge,
            on_event=self._on_voice_event_bg,
            emotion_engine=self.sim.emotion_engine,
            stt=MockSTTProvider("Ciao JARVIS (Demo)") if self._demo_mode else None,
            tts=MockTTSProvider(delay_s=0.02) if self._demo_mode else None,
        )
        mem_cfg = MemoryConfig.load_json(self._memory_cfg_path)
        self.memory_engine = MemoryEngine(
            db_path=self._data_dir / "jarvis_memory.sqlite3",
            config=mem_cfg,
        )
        self.conv_engine = ConversationEngine2(
            voice_controller=self.controller,
            memory_engine=self.memory_engine,
            behavior_engine=self.sim.behavior_engine,
        )
        self.conv_engine.start_session()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self._cached_services_summary = (
            "Modalità Demo leggera (STT/AI/TTS simulati)"
            if self._demo_mode
            else "Verifica servizi in background..."
        )
        self._cached_memory_health = self.memory_engine.health_status()

        self._tabs: Dict[str, tk.Frame] = {}
        self._build_voice_ui()
        if self._demo_mode:
            self.mic_combo["values"] = ["[Demo] Microfono simulato"]
            self.mic_var.set("[Demo] Microfono simulato")
            self.stt_status_var.set("STT: Modalità Demo leggera (nessun modello caricato)")
            self.voice_combo["values"] = ["Mock Voice (Demo)"]
            self.voice_var.set("Mock Voice (Demo)")
            self.model_combo["values"] = ["demo-local"]
            self.model_var.set("demo-local")
        else:
            self.mic_combo["values"] = ["Verifica microfono..."]
            self.mic_var.set("Verifica microfono...")
            self.stt_status_var.set("STT: verifica in background...")
            self.voice_combo["values"] = [self.config.tts_voice]
            self.voice_var.set(self.config.tts_voice)
            self._probe_timer_id = self.root.after(150, self.refresh_service_status_async)

        self._refresh_control_center()
        self._poll_queues()
        if not self._demo_mode and not self._no_spontaneous:
            self._schedule_spontaneous_check()

    def _apply_dark_theme(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background=BG_PANEL, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_PRIMARY, padding=[8, 4], font=("Segoe UI", 8, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#0284C7")], foreground=[("selected", "#FFFFFF")])

    def _on_voice_event_bg(self, event: VoiceEvent) -> None:
        self._event_queue.put(event)

    def _build_voice_ui(self) -> None:
        title = tk.Label(
            self.voice_panel,
            text="JARVIS Control Center",
            fg=TEXT_PRIMARY,
            bg=BG_PANEL,
            font=("Segoe UI", 13, "bold"),
        )
        title.pack(anchor="w", pady=(0, 4))

        self.phase_var = tk.StringVar(value="Stato: IDLE | Pronto")
        tk.Label(
            self.voice_panel,
            textvariable=self.phase_var,
            fg=ACCENT_CYAN,
            bg=BG_PANEL,
            font=("Consolas", 9, "bold"),
            wraplength=435,
            justify="left",
        ).pack(anchor="w", pady=(0, 2))

        self.provider_badge_var = tk.StringVar(
            value=f"Provider: {self.controller.providers[self.controller.active_provider_id].display_name}"
        )
        tk.Label(
            self.voice_panel,
            textvariable=self.provider_badge_var,
            fg="#A7F3D0",
            bg=BG_PANEL,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        notebook = ttk.Notebook(self.voice_panel)
        notebook.pack(fill="both", expand=True)
        self.control_notebook = notebook

        self.dashboard_panel = DashboardPanel(
            notebook,
            on_toggle_quiet=lambda val: self._on_toggle_quiet_mode(val),
            on_toggle_persistent_mem=lambda val: self._on_toggle_persistent_memory(val),
        )
        tab_chat = tk.Frame(notebook, bg=BG_PANEL, padx=8, pady=8)
        self.memory_panel = MemoryPanel(
            notebook,
            memory_engine=self.memory_engine,
            on_toggle_persistent=lambda val: self._on_toggle_persistent_memory(val),
            confirm_wipe_fn=self._confirm_wipe_fn,
            demo_mode=self._demo_mode,
        )
        self.personality_panel = PersonalityPanel(
            notebook,
            profile=self.sim.personality,
            config_path=self._personality_cfg_path,
            on_toggle_quiet=lambda val: self._on_toggle_quiet_mode(val),
        )
        self.simulator_panel = SimulatorControlPanel(notebook, sim_app=self.sim)
        self.sensor_panel = SensorStatusPanel(
            notebook,
            sim_app=self.sim,
            on_open_sensor_lab=lambda: self.sim.sim_notebook.select(1),
        )
        self.diagnostics_panel = DiagnosticsPanel(notebook)
        tab_cfg = tk.Frame(notebook, bg=BG_PANEL, padx=8, pady=8)

        notebook.add(self.dashboard_panel, text=" Dashboard ")
        notebook.add(tab_chat, text=" Chat ")
        notebook.add(self.memory_panel, text=" Memoria ")
        notebook.add(self.personality_panel, text=" Personalità ")
        notebook.add(self.simulator_panel, text=" Simulatore ")
        notebook.add(self.sensor_panel, text=" Sensori ")
        notebook.add(self.diagnostics_panel, text=" Diagnostica ")
        notebook.add(tab_cfg, text=" Audio & AI ")

        self._tabs = {
            "dashboard": self.dashboard_panel,
            "chat": tab_chat,
            "memoria": self.memory_panel,
            "personalita": self.personality_panel,
            "simulatore": self.simulator_panel,
            "sensori": self.sensor_panel,
            "diagnostica": self.diagnostics_panel,
            "audio": tab_cfg,
        }

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

        # FASE 9.3 compact memory & mode bar (non-blocking)
        ctrl_bar = tk.Frame(tab_chat, bg="#0F172A", pady=4)
        ctrl_bar.pack(fill="x", pady=(6, 0))

        self.persistent_mem_var = tk.BooleanVar(value=self.memory_engine.config.persistent_enabled)
        tk.Checkbutton(
            ctrl_bar,
            text="Memoria Persistente",
            variable=self.persistent_mem_var,
            command=self._on_toggle_persistent_memory,
            bg="#0F172A",
            fg="#CBD5E1",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#F8FAFC",
            font=("Segoe UI", 8),
        ).pack(side="left")

        self.quiet_mode_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            ctrl_bar,
            text="Quiet Mode",
            variable=self.quiet_mode_var,
            command=self._on_toggle_quiet_mode,
            bg="#0F172A",
            fg="#CBD5E1",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#F8FAFC",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(8, 0))

        prop_row = tk.Frame(tab_chat, bg="#0F172A", pady=2)
        prop_row.pack(fill="x", pady=(2, 0))
        self.memory_entry = tk.Entry(prop_row, bg="#1E293B", fg="#F8FAFC", insertbackground="#F8FAFC", relief="flat", font=("Segoe UI", 8))
        self.memory_entry.pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(prop_row, text="Proponi", command=self._on_propose_memory, bg="#334155", fg="#F8FAFC", relief="flat", padx=6, font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))
        tk.Button(prop_row, text="Conferma", command=self._on_confirm_memory, bg="#059669", fg="#FFFFFF", relief="flat", padx=6, font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))
        tk.Button(prop_row, text="Rifiuta", command=self._on_reject_memory, bg="#DC2626", fg="#FFFFFF", relief="flat", padx=6, font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))

        self.proposal_status_var = tk.StringVar(value="Nessuna proposta in attesa.")
        tk.Label(tab_chat, textvariable=self.proposal_status_var, bg="#0F172A", fg="#94A3B8", anchor="w", font=("Segoe UI", 8)).pack(fill="x")

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

    def refresh_service_status_async(self) -> None:
        self._probe_timer_id = None
        if self._closed or self._demo_mode or self._probe_running:
            return
        self._probe_running = True
        pid = self.provider_var.get()
        prov = self.controller.providers[pid]

        def _worker() -> None:
            try:
                mics = list_microphones()
                mic_names = [f"[{m.index}] {m.name}" for m in mics] if mics else ["Nessun microfono rilevato"]
                stt_ok, stt_msg = self.controller.stt.is_available()
                voices = self.controller.tts.list_voices()
                tts_ok = bool(voices)
                ai_ok, ai_status = prov.is_available()
                models = prov.list_models()
                self._probe_queue.put({
                    "mic_names": mic_names,
                    "stt_ok": stt_ok,
                    "stt_msg": stt_msg,
                    "voices": voices,
                    "tts_ok": tts_ok,
                    "pid": pid,
                    "ai_ok": ai_ok,
                    "ai_status": ai_status,
                    "models": models,
                })
            except Exception:
                pass
            finally:
                self._probe_running = False

        threading.Thread(target=_worker, daemon=True, name="jarvis-service-probe").start()

    def _refresh_models(self) -> None:
        if self._demo_mode:
            self.model_combo["values"] = ["demo-local"]
            self.model_var.set("demo-local")
            return
        self.refresh_service_status_async()

    def _on_provider_changed(self) -> None:
        pid = self.provider_var.get()
        self.controller.select_provider(pid, self.model_var.get())
        if self._demo_mode or pid == "demo":
            self._cached_services_summary = f"STT=DEMO | AI({pid})=OK | TTS=DEMO"
            self.phase_var.set(f"Provider {pid}: pronto")
            self._refresh_control_center()
            return
        self.phase_var.set(f"Provider {pid}: verifica in corso...")
        self.refresh_service_status_async()

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
            self.conv_engine.stop_listening_and_process()
        else:
            self.controller.select_provider(self.provider_var.get(), self.model_var.get())
            self.conv_engine.start_listening()

    def _on_send_text(self) -> None:
        text = self.text_entry.get().strip()
        if not text:
            return
        self.controller.select_provider(self.provider_var.get(), self.model_var.get())
        self.conv_engine.submit_text(text)

    def _on_interrupt(self) -> None:
        self.conv_engine.interrupt()

    def _on_new_chat(self) -> None:
        self.conv_engine.interrupt()
        self.controller.reset_conversation()
        self.conv_engine.start_session()
        self.transcript_var.set("-")
        self._set_reply_text("Nuova conversazione avviata.")

    def select_tab(self, tab_key: str) -> None:
        tab = self._tabs.get(tab_key.lower())
        if tab is not None:
            self.control_notebook.select(tab)

    def _on_toggle_persistent_memory(self, enabled: Optional[bool] = None) -> None:
        val = bool(self.persistent_mem_var.get()) if enabled is None else bool(enabled)
        self.persistent_mem_var.set(val)
        self.conv_engine.set_persistent_memory_enabled(val)
        self.memory_engine.config.save_json(self._memory_cfg_path)
        self._cached_memory_health = self.memory_engine.health_status()
        self.memory_panel.refresh_lists()
        self._refresh_control_center()

    def _on_toggle_quiet_mode(self, enabled: Optional[bool] = None) -> None:
        val = bool(self.quiet_mode_var.get()) if enabled is None else bool(enabled)
        self.quiet_mode_var.set(val)
        self.conv_engine.set_quiet_mode(val)
        self.personality_panel.sync_quiet(val)
        self._refresh_control_center()

    def _on_propose_memory(self) -> None:
        text = self.memory_entry.get().strip()
        if not text:
            return
        prop = self.conv_engine.propose_fact(text)
        if prop is not None:
            self.memory_entry.delete(0, "end")
        self._refresh_proposal_label()

    def _on_confirm_memory(self) -> None:
        pending = self.conv_engine.list_pending_proposals()
        if pending:
            self.conv_engine.confirm_memory(pending[-1].proposal_id)
        self._refresh_proposal_label()
        self.memory_panel.refresh_lists()

    def _on_reject_memory(self) -> None:
        pending = self.conv_engine.list_pending_proposals()
        if pending:
            self.conv_engine.reject_memory(pending[-1].proposal_id)
        self._refresh_proposal_label()

    def _refresh_proposal_label(self) -> None:
        pending = self.conv_engine.list_pending_proposals()
        if not pending:
            self.proposal_status_var.set("Nessuna proposta in attesa.")
        else:
            last = pending[-1]
            self.proposal_status_var.set(f"In attesa ({len(pending)}): {last.content[:60]}")

    def _schedule_spontaneous_check(self) -> None:
        if self._closed or self._spontaneous_timer_id is not None:
            return
        self._spontaneous_timer_id = self.root.after(
            self.SPONTANEOUS_CHECK_INTERVAL_MS,
            self._on_spontaneous_timer,
        )

    def _on_spontaneous_timer(self) -> None:
        self._spontaneous_timer_id = None
        if self._closed:
            return
        try:
            self.tick_spontaneous_initiatives()
        except Exception:
            pass
        self._schedule_spontaneous_check()

    def tick_spontaneous_initiatives(self, now_ms: Optional[int] = None) -> Optional[str]:
        if self._demo_mode or self._no_spontaneous:
            return None
        ts = self.sim._now_ms() if now_ms is None else now_ms
        if ts < self.STARTUP_GRACE_MS:
            return None
        return self.conv_engine.try_spontaneous_voice(category="IDLE_CHECKIN", now_ms=ts)

    def _refresh_control_center(self) -> None:
        if self._closed:
            return
        now_ms = self.sim._now_ms()
        can_spont, spont_reason = self.sim.behavior_engine.can_trigger_spontaneous_voice(now_ms)
        if self._demo_mode:
            spont_summary = "disabilitate (demo)"
        elif self._no_spontaneous:
            spont_summary = "disabilitate (--no-spontaneous)"
        else:
            spont_summary = "pronta" if can_spont else spont_reason

        self.dashboard_panel.refresh(
            mode=self.sim.behavior_engine.mode,
            expression=self.sim.eyes.expr.value,
            quiet_mode=self.sim.behavior_engine.quiet_mode,
            persistent_enabled=self.memory_engine.config.persistent_enabled,
            services_summary=self._cached_services_summary,
            spontaneous_summary=spont_summary,
            last_error=self._last_error_text,
            esp32_connected=False,
        )
        self.simulator_panel.refresh()
        self.sensor_panel.refresh()
        self.diagnostics_panel.refresh(
            behavior_engine=self.sim.behavior_engine,
            voice_phase=self.controller.phase.value,
            provider_id=self.controller.active_provider_id,
            memory_health=self._cached_memory_health,
            last_error=self._last_error_text,
            esp32_connected=False,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for attr in ("_poll_timer_id", "_spontaneous_timer_id", "_probe_timer_id"):
            tid = getattr(self, attr, None)
            if tid is not None:
                try:
                    self.root.after_cancel(tid)
                except Exception:
                    pass
                setattr(self, attr, None)
        try:
            self.conv_engine.end_session()
        except Exception:
            pass
        try:
            self.memory_engine.close_db()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _set_reply_text(self, text: str) -> None:
        self.reply_box.configure(state="normal")
        self.reply_box.delete("1.0", "end")
        self.reply_box.insert("1.0", text)
        self.reply_box.configure(state="disabled")

    def _poll_queues(self) -> None:
        if self._closed:
            return
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
                self._last_error_text = ev.error_text
                self._set_reply_text(f"[Avviso] {ev.error_text}")

            if ev.phase == VoicePhase.LISTENING:
                self.talk_btn.configure(text="Ferma e Invia", bg="#059669")
            else:
                self.talk_btn.configure(text="Parla (Avvia Ascolto)", bg="#0284C7")

        while True:
            try:
                probe = self._probe_queue.get_nowait()
            except queue.Empty:
                break
            self._apply_probe_result(probe)

        self._ui_tick_counter += 1
        if self._ui_tick_counter % 40 == 0:
            self._refresh_control_center()

        self._poll_timer_id = self.root.after(25, self._poll_queues)

    def _apply_probe_result(self, probe: Dict[str, Any]) -> None:
        mic_names = probe.get("mic_names") or ["Nessun microfono rilevato"]
        self.mic_combo["values"] = mic_names
        if self.mic_var.get() not in mic_names:
            self.mic_var.set(mic_names[0])

        self.stt_status_var.set(f"STT: {probe.get('stt_msg', '')}")
        voices = probe.get("voices") or []
        if voices:
            self.voice_combo["values"] = voices
            if self.config.tts_voice not in voices:
                self.config.tts_voice = voices[0]
            self.voice_var.set(self.config.tts_voice)
        else:
            self.voice_combo["values"] = ["Nessuna voce TTS locale"]
            self.voice_var.set("Nessuna voce TTS locale")

        pid = str(probe.get("pid", self.provider_var.get()))
        models = probe.get("models") or []
        self.model_combo["values"] = models
        if models and self.model_var.get() not in models:
            self.model_var.set(models[0])
            self.controller.select_provider(pid, models[0])

        stt_ok = bool(probe.get("stt_ok"))
        ai_ok = bool(probe.get("ai_ok"))
        tts_ok = bool(probe.get("tts_ok"))
        self._cached_services_summary = (
            f"STT={'OK' if stt_ok else 'NO'} | AI({pid})={'OK' if ai_ok else 'OFFLINE'} | TTS={'OK' if tts_ok else 'NO'}"
        )
        self._refresh_control_center()

    def _handle_eye_cmd(self, cmd: str, now_ms: int) -> None:
        self.sim.sm.handle_command(cmd, now_ms)
        self.sim._highlight_active_button()


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS Control Center — Simulator + Voice & AI")
    parser.add_argument("--smoke-ms", type=int, default=0, help="Auto-close after N ms for GUI smoke tests")
    parser.add_argument("--demo", action="store_true", help="Avvia in modalità demo leggera (senza STT/Ollama/Piper/spontanee)")
    parser.add_argument("--no-spontaneous", action="store_true", help="Disabilita le iniziative vocali spontanee in modalità normale")
    args = parser.parse_args()

    root = tk.Tk()
    app = JarvisUnifiedApp(root, demo_mode=args.demo, no_spontaneous=args.no_spontaneous)
    if args.smoke_ms > 0:
        root.after(args.smoke_ms, app.close)
    root.mainloop()


if __name__ == "__main__":
    main()
