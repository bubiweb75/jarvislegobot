"""JARVIS LEGO BOT — Control Center Reusable GUI Panels (FASE 9.4).

Dark-themed, non-blocking Tkinter panels for:
  - DashboardPanel
  - MemoryPanel
  - PersonalityPanel
  - SimulatorControlPanel
  - SensorStatusPanel
  - DiagnosticsPanel

All panels reuse the single shared instances of BehaviorEngine, MemoryEngine,
VoiceController, ConversationEngine2, and JarvisSimulatorApp.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, Optional

from behavior_engine import BehaviorEngine, RobotMode
from eye_engine import ALL_EXPRESSIONS, Expression
from personality import PersonalityConfig, PersonalityProfile
from sensor_manager import SensorManager, SensorType


BG_DARK = "#0B101B"
BG_PANEL = "#0F172A"
BG_CARD = "#1E293B"
ACCENT_CYAN = "#38BDF8"
ACCENT_GREEN = "#10B981"
ACCENT_AMBER = "#F59E0B"
ACCENT_RED = "#EF4444"
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#CBD5E1"
TEXT_MUTED = "#94A3B8"

APP_VERSION = "JARVIS BRAIN 2.0 — FASE 9.4 Control Center"


def load_personality_config_json(path: Path) -> PersonalityConfig:
    """Load PersonalityConfig from JSON safely, returning defaults on error."""
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return PersonalityConfig(
                    playfulness_bias=data.get("playfulness_bias", 0.75),
                    affection_bias=data.get("affection_bias", 0.75),
                    curiosity_bias=data.get("curiosity_bias", 0.80),
                    mischief_bias=data.get("mischief_bias", 0.45),
                    expressive_intensity=data.get("expressive_intensity", 1.0),
                    initiative_frequency=data.get("initiative_frequency", 1.0),
                    behavior_variation=data.get("behavior_variation", 1.0),
                    initiatives_enabled=data.get("initiatives_enabled", True),
                ).normalized()
    except Exception:
        pass
    return PersonalityConfig().normalized()


def save_personality_config_json(path: Path, cfg: PersonalityConfig) -> bool:
    """Persist PersonalityConfig to JSON safely."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        norm = cfg.normalized()
        payload = {
            "playfulness_bias": norm.playfulness_bias,
            "affection_bias": norm.affection_bias,
            "curiosity_bias": norm.curiosity_bias,
            "mischief_bias": norm.mischief_bias,
            "expressive_intensity": norm.expressive_intensity,
            "initiative_frequency": norm.initiative_frequency,
            "behavior_variation": norm.behavior_variation,
            "initiatives_enabled": norm.initiatives_enabled,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def _card(parent: tk.Misc, title: str) -> tk.LabelFrame:
    return tk.LabelFrame(
        parent,
        text=f" {title} ",
        bg=BG_PANEL,
        fg=ACCENT_CYAN,
        font=("Segoe UI", 9, "bold"),
        bd=1,
        relief="groove",
        padx=8,
        pady=6,
    )


class DashboardPanel(tk.Frame):
    """Overview of JARVIS status, mode, services, Quiet Mode, memory, and expression."""

    def __init__(
        self,
        parent: tk.Misc,
        on_toggle_quiet: Callable[[bool], None],
        on_toggle_persistent_mem: Callable[[bool], None],
    ) -> None:
        super().__init__(parent, bg=BG_PANEL, padx=8, pady=8)
        self._on_toggle_quiet = on_toggle_quiet
        self._on_toggle_persistent_mem = on_toggle_persistent_mem

        status_card = _card(self, "Stato Generale JARVIS")
        status_card.pack(fill="x", pady=(0, 8))

        self.mode_var = tk.StringVar(value="Modalità: IDLE")
        self.expr_var = tk.StringVar(value="Ultima espressione: IDLE")
        self.hw_var = tk.StringVar(value="Hardware ESP32: Simulatore locale (non connesso)")
        self.services_var = tk.StringVar(value="Servizi vocali: verifica...")
        self.spont_var = tk.StringVar(value="Iniziative spontanee: in attesa")
        self.error_var = tk.StringVar(value="Errori recenti: nessuno")

        for var, fg in (
            (self.mode_var, ACCENT_CYAN),
            (self.expr_var, TEXT_PRIMARY),
            (self.hw_var, ACCENT_AMBER),
            (self.services_var, TEXT_SECONDARY),
            (self.spont_var, TEXT_MUTED),
            (self.error_var, TEXT_MUTED),
        ):
            tk.Label(
                status_card,
                textvariable=var,
                bg=BG_PANEL,
                fg=fg,
                anchor="w",
                justify="left",
                wraplength=400,
                font=("Segoe UI", 9),
            ).pack(fill="x", pady=1)

        ctrl_card = _card(self, "Controlli Rapidi")
        ctrl_card.pack(fill="x")

        self.quiet_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            ctrl_card,
            text="Quiet Mode (silenzia iniziative spontanee, mantiene OLED)",
            variable=self.quiet_var,
            command=lambda: self._on_toggle_quiet(bool(self.quiet_var.get())),
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            selectcolor=BG_CARD,
            activebackground=BG_PANEL,
            activeforeground=TEXT_PRIMARY,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        self.persistent_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            ctrl_card,
            text="Memoria Persistente (L2 preferenze + L3/L4 confermati)",
            variable=self.persistent_var,
            command=lambda: self._on_toggle_persistent_mem(bool(self.persistent_var.get())),
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            selectcolor=BG_CARD,
            activebackground=BG_PANEL,
            activeforeground=TEXT_PRIMARY,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

    def refresh(
        self,
        mode: RobotMode,
        expression: str,
        quiet_mode: bool,
        persistent_enabled: bool,
        services_summary: str,
        spontaneous_summary: str,
        last_error: str,
        esp32_connected: bool = False,
    ) -> None:
        self.mode_var.set(f"Modalità corrente: {mode.value}")
        self.expr_var.set(f"Ultima espressione OLED: {expression}")
        self.hw_var.set(
            "Hardware ESP32: Connesso" if esp32_connected else "Hardware ESP32: Simulatore locale (non connesso)"
        )
        self.services_var.set(f"Servizi vocali: {services_summary}")
        self.spont_var.set(f"Iniziative spontanee: {spontaneous_summary}")
        self.error_var.set(f"Ultimo avviso/errore: {last_error or 'nessuno'}")
        if self.quiet_var.get() != quiet_mode:
            self.quiet_var.set(quiet_mode)
        if self.persistent_var.get() != persistent_enabled:
            self.persistent_var.set(persistent_enabled)


class MemoryPanel(tk.Frame):
    """Manage L2 preferences and confirmed L3/L4 memories with explicit wipe confirmation."""

    def __init__(
        self,
        parent: tk.Misc,
        memory_engine: Any,
        on_toggle_persistent: Callable[[bool], None],
        confirm_wipe_fn: Optional[Callable[[], bool]] = None,
    ) -> None:
        super().__init__(parent, bg=BG_PANEL, padx=8, pady=8)
        self.memory = memory_engine
        self._on_toggle_persistent = on_toggle_persistent
        self._confirm_wipe_fn = confirm_wipe_fn
        self._record_map: Dict[str, tuple[str, int, str]] = {}

        top = tk.Frame(self, bg=BG_PANEL)
        top.pack(fill="x", pady=(0, 6))
        self.persistent_var = tk.BooleanVar(value=self.memory.config.persistent_enabled)
        tk.Checkbutton(
            top,
            text="Persistenza attiva",
            variable=self.persistent_var,
            command=lambda: self._on_toggle_persistent(bool(self.persistent_var.get())),
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            selectcolor=BG_CARD,
            activebackground=BG_PANEL,
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left")

        self.status_var = tk.StringVar(value="")
        tk.Label(top, textvariable=self.status_var, bg=BG_PANEL, fg=ACCENT_CYAN, font=("Segoe UI", 8)).pack(side="right")

        # Search + Refresh
        search_row = tk.Frame(self, bg=BG_PANEL)
        search_row.pack(fill="x", pady=(0, 6))
        self.search_entry = tk.Entry(search_row, bg=BG_CARD, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat")
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(search_row, text="Cerca", command=self.refresh_lists, bg="#0284C7", fg="#FFFFFF", relief="flat", padx=8).pack(side="left", padx=(4, 0))
        tk.Button(search_row, text="Aggiorna", command=self.refresh_lists, bg="#334155", fg=TEXT_PRIMARY, relief="flat", padx=8).pack(side="left", padx=(4, 0))

        # L2 Preferences
        pref_card = _card(self, "Preferenze L2")
        pref_card.pack(fill="x", pady=(0, 6))
        self.pref_list = tk.Listbox(pref_card, height=4, bg=BG_CARD, fg=TEXT_PRIMARY, selectbackground="#0284C7", relief="flat", font=("Consolas", 8))
        self.pref_list.pack(fill="x")

        pref_add = tk.Frame(pref_card, bg=BG_PANEL)
        pref_add.pack(fill="x", pady=(4, 0))
        self.pref_key_entry = tk.Entry(pref_add, width=14, bg=BG_CARD, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", font=("Segoe UI", 8))
        self.pref_key_entry.pack(side="left", padx=(0, 4), ipady=2)
        self.pref_val_entry = tk.Entry(pref_add, bg=BG_CARD, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", font=("Segoe UI", 8))
        self.pref_val_entry.pack(side="left", fill="x", expand=True, ipady=2)
        tk.Button(pref_add, text="Salva L2", command=self.save_preference, bg=ACCENT_GREEN, fg="#FFFFFF", relief="flat", padx=6, font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))
        tk.Button(pref_add, text="Elimina L2", command=self.delete_selected_preference, bg=ACCENT_RED, fg="#FFFFFF", relief="flat", padx=6, font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))

        # L3/L4 Confirmed Memories
        mem_card = _card(self, "Ricordi Confermati L3 / L4 (con scadenze L4)")
        mem_card.pack(fill="both", expand=True, pady=(0, 6))
        self.mem_list = tk.Listbox(mem_card, height=6, bg=BG_CARD, fg=TEXT_PRIMARY, selectbackground="#0284C7", relief="flat", font=("Consolas", 8))
        self.mem_list.pack(fill="both", expand=True)
        self.mem_list.bind("<<ListboxSelect>>", lambda _e: self._on_select_memory())

        edit_row = tk.Frame(mem_card, bg=BG_PANEL)
        edit_row.pack(fill="x", pady=(4, 0))
        self.edit_entry = tk.Entry(edit_row, bg=BG_CARD, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", font=("Segoe UI", 8))
        self.edit_entry.pack(side="left", fill="x", expand=True, ipady=2)
        tk.Button(edit_row, text="Modifica", command=self.update_selected_memory, bg="#0284C7", fg="#FFFFFF", relief="flat", padx=6, font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))
        tk.Button(edit_row, text="Elimina", command=self.delete_selected_memory, bg=ACCENT_RED, fg="#FFFFFF", relief="flat", padx=6, font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))

        wipe_row = tk.Frame(self, bg=BG_PANEL)
        wipe_row.pack(fill="x")
        tk.Button(
            wipe_row,
            text="Cancella TUTTA la Memoria Persistente...",
            command=self.wipe_all_with_confirmation,
            bg="#991B1B",
            fg="#FFFFFF",
            relief="flat",
            padx=8,
            font=("Segoe UI", 8, "bold"),
        ).pack(side="right")

        self.refresh_lists()

    def refresh_lists(self) -> None:
        self.persistent_var.set(bool(self.memory.config.persistent_enabled))
        self.pref_list.delete(0, "end")
        for k, v in self.memory.list_preferences().items():
            self.pref_list.insert("end", f"{k} = {v}")

        self.mem_list.delete(0, "end")
        self._record_map.clear()
        query = self.search_entry.get().strip()
        records = self.memory.search_memories(query=query, limit=50)
        for idx, rec in enumerate(records):
            exp = ""
            if rec.level == "L4" and rec.expires_at:
                dt = datetime.fromtimestamp(rec.expires_at).strftime("%Y-%m-%d")
                exp = f" | scade {dt}"
            label = f"[{rec.level}#{rec.record_id}:{rec.category}{exp}] {rec.content}"
            self.mem_list.insert("end", label)
            self._record_map[str(idx)] = (rec.level, rec.record_id, rec.content)

        health = self.memory.health_status()
        self.status_var.set(f"L2: {self.pref_list.size()} | L3/L4: {len(records)} | DB: {health.get('status')}")

    def _on_select_memory(self) -> None:
        sel = self.mem_list.curselection()
        if not sel:
            return
        info = self._record_map.get(str(sel[0]))
        if info:
            self.edit_entry.delete(0, "end")
            self.edit_entry.insert(0, info[2])

    def save_preference(self) -> bool:
        k = self.pref_key_entry.get().strip()
        v = self.pref_val_entry.get().strip()
        if not k or not v:
            return False
        ok = self.memory.set_preference(k, v)
        if ok:
            self.pref_key_entry.delete(0, "end")
            self.pref_val_entry.delete(0, "end")
        self.refresh_lists()
        return ok

    def delete_selected_preference(self) -> bool:
        sel = self.pref_list.curselection()
        if not sel:
            return False
        item = self.pref_list.get(sel[0])
        key = item.split(" = ", 1)[0]
        ok = self.memory.delete_preference(key)
        self.refresh_lists()
        return ok

    def update_selected_memory(self) -> bool:
        sel = self.mem_list.curselection()
        if not sel:
            return False
        info = self._record_map.get(str(sel[0]))
        new_text = self.edit_entry.get().strip()
        if not info or not new_text:
            return False
        ok = self.memory.update_memory(info[0], info[1], new_text)
        self.refresh_lists()
        return ok

    def delete_selected_memory(self) -> bool:
        sel = self.mem_list.curselection()
        if not sel:
            return False
        info = self._record_map.get(str(sel[0]))
        if not info:
            return False
        ok = self.memory.delete_memory(info[0], info[1])
        self.refresh_lists()
        return ok

    def wipe_all_with_confirmation(self) -> bool:
        if self._confirm_wipe_fn is not None:
            confirmed = bool(self._confirm_wipe_fn())
        else:
            confirmed = messagebox.askyesno(
                "Conferma cancellazione totale",
                "Vuoi cancellare definitivamente tutte le preferenze L2 e i ricordi L3/L4?",
            )
        if not confirmed:
            return False
        ok = self.memory.wipe_all_persistent_data()
        self.refresh_lists()
        return ok


class PersonalityPanel(tk.Frame):
    """Manage Personality C traits, initiative frequency, and Quiet Mode."""

    def __init__(
        self,
        parent: tk.Misc,
        profile: PersonalityProfile,
        config_path: Path,
        on_toggle_quiet: Callable[[bool], None],
    ) -> None:
        super().__init__(parent, bg=BG_PANEL, padx=8, pady=8)
        self.profile = profile
        self.config_path = config_path
        self._on_toggle_quiet = on_toggle_quiet

        card = _card(self, "Profilo Personalità C")
        card.pack(fill="x", pady=(0, 8))

        self._scales: Dict[str, tk.Scale] = {}
        specs = [
            ("expressive_intensity", "Intensità espressiva", 0.3, 1.5, 0.05),
            ("curiosity_bias", "Curiosità", 0.0, 1.0, 0.05),
            ("playfulness_bias", "Giocosità", 0.0, 1.0, 0.05),
            ("affection_bias", "Affettuosità", 0.0, 1.0, 0.05),
            ("mischief_bias", "Birichineria", 0.0, 1.0, 0.05),
            ("initiative_frequency", "Frequenza iniziative", 0.0, 1.5, 0.05),
        ]
        cfg = self.profile.config
        for field_name, label, lo, hi, res in specs:
            row = tk.Frame(card, bg=BG_PANEL)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, width=18, anchor="w", bg=BG_PANEL, fg=TEXT_SECONDARY, font=("Segoe UI", 8)).pack(side="left")
            scale = tk.Scale(
                row,
                from_=lo,
                to=hi,
                resolution=res,
                orient="horizontal",
                bg=BG_PANEL,
                fg=TEXT_PRIMARY,
                troughcolor=BG_CARD,
                highlightthickness=0,
                command=lambda _v: self.apply_and_save(),
            )
            scale.set(getattr(cfg, field_name))
            scale.pack(side="left", fill="x", expand=True)
            self._scales[field_name] = scale

        opts = _card(self, "Iniziative e Silenzio")
        opts.pack(fill="x")
        self.initiatives_var = tk.BooleanVar(value=cfg.initiatives_enabled)
        tk.Checkbutton(
            opts,
            text="Abilita iniziative vocali spontanee (max 2/ora, min 20 min)",
            variable=self.initiatives_var,
            command=self.apply_and_save,
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            selectcolor=BG_CARD,
            activebackground=BG_PANEL,
            font=("Segoe UI", 8),
        ).pack(anchor="w")

        self.quiet_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            opts,
            text="Quiet Mode",
            variable=self.quiet_var,
            command=lambda: self._on_toggle_quiet(bool(self.quiet_var.get())),
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            selectcolor=BG_CARD,
            activebackground=BG_PANEL,
            font=("Segoe UI", 8),
        ).pack(anchor="w")

    def apply_and_save(self) -> PersonalityConfig:
        new_cfg = PersonalityConfig(
            expressive_intensity=float(self._scales["expressive_intensity"].get()),
            curiosity_bias=float(self._scales["curiosity_bias"].get()),
            playfulness_bias=float(self._scales["playfulness_bias"].get()),
            affection_bias=float(self._scales["affection_bias"].get()),
            mischief_bias=float(self._scales["mischief_bias"].get()),
            initiative_frequency=float(self._scales["initiative_frequency"].get()),
            behavior_variation=self.profile.config.behavior_variation,
            initiatives_enabled=bool(self.initiatives_var.get()),
        ).normalized()
        self.profile.update_config(new_cfg)
        save_personality_config_json(self.config_path, new_cfg)
        return new_cfg

    def sync_quiet(self, quiet_mode: bool) -> None:
        if self.quiet_var.get() != quiet_mode:
            self.quiet_var.set(quiet_mode)


class SimulatorControlPanel(tk.Frame):
    """Control 14 OLED expressions, EyeEngine2 sequences, and gaze offsets."""

    def __init__(self, parent: tk.Misc, sim_app: Any) -> None:
        super().__init__(parent, bg=BG_PANEL, padx=8, pady=8)
        self.sim = sim_app

        info = _card(self, "Compatibilità Firmware & Simulatore OLED")
        info.pack(fill="x", pady=(0, 8))
        self.expr_label_var = tk.StringVar(value="Espressione corrente: IDLE")
        tk.Label(info, textvariable=self.expr_label_var, bg=BG_PANEL, fg=ACCENT_CYAN, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(
            info,
            text="Compatibile FASE 8.2A: 14 espressioni OLED, STATE:*, LOOK:dx,dy (-11..11, -6..6), BLINK",
            bg=BG_PANEL,
            fg=TEXT_MUTED,
            wraplength=390,
            justify="left",
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(2, 0))

        grid_card = _card(self, "Selezione 14 Espressioni")
        grid_card.pack(fill="x", pady=(0, 8))
        for idx, expr in enumerate(ALL_EXPRESSIONS):
            btn = tk.Button(
                grid_card,
                text=expr.value,
                width=12,
                bg=BG_CARD,
                fg=TEXT_PRIMARY,
                activebackground="#0284C7",
                relief="flat",
                font=("Segoe UI", 8),
                command=lambda e=expr: self.set_expression(e),
            )
            btn.grid(row=idx // 3, column=idx % 3, padx=3, pady=3, sticky="ew")

        gaze_card = _card(self, "Sguardo & Sequenze EyeEngine2")
        gaze_card.pack(fill="x")
        gaze_btns = tk.Frame(gaze_card, bg=BG_PANEL)
        gaze_btns.pack(fill="x", pady=(0, 4))
        for label, dx, dy in (("Sinistra", -8, 0), ("Centro", 0, 0), ("Destra", 8, 0), ("Su", 0, -5), ("Giù", 0, 5)):
            tk.Button(
                gaze_btns,
                text=label,
                bg=BG_CARD,
                fg=TEXT_PRIMARY,
                relief="flat",
                padx=6,
                font=("Segoe UI", 8),
                command=lambda x=dx, y=dy: self.look_at(x, y),
            ).pack(side="left", padx=2)
        tk.Button(
            gaze_btns,
            text="Blink",
            bg="#0284C7",
            fg="#FFFFFF",
            relief="flat",
            padx=8,
            font=("Segoe UI", 8),
            command=self.trigger_blink,
        ).pack(side="right")

        seq_row = tk.Frame(gaze_card, bg=BG_PANEL)
        seq_row.pack(fill="x")
        for label, seq_name in (("Saluto", "GREETING"), ("Curioso", "CURIOUS_SCAN"), ("Affetto", "AFFECTION"), ("Birichino", "MISCHIEVOUS")):
            tk.Button(
                seq_row,
                text=f"Seq: {label}",
                bg="#334155",
                fg=TEXT_PRIMARY,
                relief="flat",
                padx=6,
                font=("Segoe UI", 8),
                command=lambda s=seq_name: self.start_sequence(s),
            ).pack(side="left", padx=2)

    def set_expression(self, expr: Expression) -> None:
        self.sim.sm.handle_command(f"STATE:{expr.value}", self.sim._now_ms())
        self.sim._highlight_active_button()
        self.refresh()

    def look_at(self, dx: int, dy: int) -> None:
        self.sim.sm.handle_command(f"LOOK:{dx},{dy}", self.sim._now_ms())
        self.refresh()

    def trigger_blink(self) -> None:
        self.sim.sm.handle_command("BLINK", self.sim._now_ms())

    def start_sequence(self, name: str) -> None:
        now_ms = self.sim._now_ms()
        if name == "GREETING":
            self.sim.eye_v2.play_greeting(now_ms)
        elif name == "CURIOUS_SCAN":
            self.sim.eye_v2.play_curious_scan(now_ms)
        elif name == "AFFECTION":
            self.sim.eye_v2.play_affection(now_ms)
        elif name == "MISCHIEVOUS":
            self.sim.eye_v2.play_mischievous(now_ms)

    def refresh(self) -> None:
        self.expr_label_var.set(f"Espressione corrente: {self.sim.eyes.expr.value}")


class SensorStatusPanel(tk.Frame):
    """Display simulated vs real sensor state and quick Sensor Lab access."""

    def __init__(self, parent: tk.Misc, sim_app: Any, on_open_sensor_lab: Callable[[], None]) -> None:
        super().__init__(parent, bg=BG_PANEL, padx=8, pady=8)
        self.sim = sim_app
        self.manager: SensorManager = sim_app.sensor_manager

        hdr = _card(self, "Stato Sensori Reali vs Simulazione")
        hdr.pack(fill="x", pady=(0, 8))
        tk.Label(
            hdr,
            text="Hardware fisico: NON collegato (attiva la simulazione locale tramite Sensor Lab).",
            bg=BG_PANEL,
            fg=ACCENT_AMBER,
            wraplength=390,
            justify="left",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")

        self.sensor_vars: Dict[SensorType, tk.StringVar] = {}
        for stype, desc in (
            (SensorType.VL53L0X, "VL53L0X (Distanza ToF)"),
            (SensorType.TTP223, "TTP223 (Touch capacitivo)"),
            (SensorType.MPU6050, "MPU6050 (IMU / Movimento)"),
            (SensorType.BH1750, "BH1750 (Luce ambientale)"),
        ):
            var = tk.StringVar(value=f"{desc}: SIMULATO")
            self.sensor_vars[stype] = var
            tk.Label(hdr, textvariable=var, bg=BG_PANEL, fg=TEXT_SECONDARY, anchor="w", font=("Consolas", 8)).pack(fill="x", pady=1)

        actions = _card(self, "Eventi Simulati Rapidi")
        actions.pack(fill="x")
        tk.Button(
            actions,
            text="Apri Sensor Lab completo (pannello sinistro)",
            command=on_open_sensor_lab,
            bg="#0284C7",
            fg="#FFFFFF",
            relief="flat",
            padx=8,
            pady=4,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")

    def refresh(self) -> None:
        prov = self.sim.sensor_provider
        self.sensor_vars[SensorType.VL53L0X].set(f"VL53L0X (Distanza): SIMULATO | {prov.distance_cm:.1f} cm")
        self.sensor_vars[SensorType.TTP223].set(f"TTP223 (Touch):     SIMULATO | {'PREMUTO' if prov.touch_pressed else 'rilasciato'}")
        self.sensor_vars[SensorType.MPU6050].set(f"MPU6050 (IMU):      SIMULATO | pitch {prov.pitch_deg:.1f}° roll {prov.roll_deg:.1f}°")
        self.sensor_vars[SensorType.BH1750].set(f"BH1750 (Luce):      SIMULATO | {prov.lux:.0f} lux")


class DiagnosticsPanel(tk.Frame):
    """Display BehaviorEngine, VoiceController, MemoryEngine, events, errors, and version."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, bg=BG_PANEL, padx=8, pady=8)

        info_card = _card(self, "Stato Sottosistemi")
        info_card.pack(fill="x", pady=(0, 8))

        self.version_var = tk.StringVar(value=f"Versione: {APP_VERSION}")
        self.esp_var = tk.StringVar(value="Connessione ESP32: non connesso (simulatore attivo)")
        self.beh_var = tk.StringVar(value="BehaviorEngine: IDLE")
        self.voice_var = tk.StringVar(value="VoiceController: IDLE")
        self.mem_var = tk.StringVar(value="MemoryEngine: ok")
        self.err_var = tk.StringVar(value="Errori: nessuno")

        for var, fg in (
            (self.version_var, ACCENT_CYAN),
            (self.esp_var, ACCENT_AMBER),
            (self.beh_var, TEXT_PRIMARY),
            (self.voice_var, TEXT_PRIMARY),
            (self.mem_var, TEXT_PRIMARY),
            (self.err_var, TEXT_MUTED),
        ):
            tk.Label(info_card, textvariable=var, bg=BG_PANEL, fg=fg, anchor="w", justify="left", wraplength=400, font=("Consolas", 8)).pack(fill="x", pady=1)

        ev_card = _card(self, "Ultimi Eventi Diagnostici (non sensibili)")
        ev_card.pack(fill="both", expand=True)
        self.events_box = tk.Text(ev_card, height=10, bg=BG_CARD, fg=TEXT_SECONDARY, relief="flat", wrap="word", font=("Consolas", 8))
        self.events_box.pack(fill="both", expand=True)
        self.events_box.configure(state="disabled")

    def refresh(
        self,
        behavior_engine: BehaviorEngine,
        voice_phase: str,
        provider_id: str,
        memory_health: Dict[str, Any],
        last_error: str,
        esp32_connected: bool = False,
    ) -> None:
        self.esp_var.set("Connessione ESP32: connesso" if esp32_connected else "Connessione ESP32: non connesso (simulatore attivo)")
        self.beh_var.set(
            f"BehaviorEngine: mode={behavior_engine.mode.value} | quiet={behavior_engine.quiet_mode} | "
            f"spont_hour={behavior_engine.spontaneous_voice_count}"
        )
        self.voice_var.set(f"VoiceController: phase={voice_phase} | provider={provider_id}")
        self.mem_var.set(
            f"MemoryEngine: status={memory_health.get('status')} | schema=v{memory_health.get('schema_version')} | "
            f"persistent={memory_health.get('persistent_enabled')}"
        )
        self.err_var.set(f"Ultimo errore non sensibile: {last_error or 'nessuno'}")

        lines = []
        for diag in list(behavior_engine.diagnostics)[-12:]:
            lines.append(f"[{diag.timestamp_ms}ms] {diag.mode.value} | {diag.source}:{diag.event_type} -> {diag.outcome}")
        text = "\n".join(lines) if lines else "Nessun evento diagnostico registrato."
        self.events_box.configure(state="normal")
        self.events_box.delete("1.0", "end")
        self.events_box.insert("1.0", text)
        self.events_box.configure(state="disabled")
