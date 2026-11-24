"""Automated tests for JARVIS Control Center (FASE 9.4)."""

from pathlib import Path
import sys
import tempfile
import time
import tkinter as tk
import unittest

VOICE_DIR = Path(__file__).resolve().parent.parent
SIM_DIR = VOICE_DIR.parent / "04-Firmware" / "jarvis-desk-buddy-sim"
for p in (VOICE_DIR, SIM_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from behavior_engine import RobotMode  # noqa: E402
from eye_engine import ALL_EXPRESSIONS, Expression  # noqa: E402
from jarvis_app import JarvisUnifiedApp  # noqa: E402
from stt_providers import MockSTTProvider  # noqa: E402
from tts_providers import MockTTSProvider  # noqa: E402


class TestControlCenter(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.wipe_confirmed = False
        self.root = tk.Tk()
        self.root.withdraw()
        try:
            self.app = JarvisUnifiedApp(
                self.root,
                data_dir=self.data_dir,
                confirm_wipe_fn=lambda: self.wipe_confirmed,
            )
        except Exception:
            try:
                self.root.destroy()
            except Exception:
                pass
            raise
        # Swap TTS to MockTTSProvider so spontaneous voice tests never spawn audio
        self.app.controller.tts = MockTTSProvider(delay_s=0.01)
        self.app.conv_engine.speech_queue.tts = self.app.controller.tts

    def tearDown(self) -> None:
        if not self.app._closed:
            self.app.close()
        self._tmp.cleanup()

    def test_01_tab_navigation_and_single_engine_instances(self) -> None:
        for key in ("dashboard", "chat", "memoria", "personalita", "simulatore", "sensori", "diagnostica", "audio"):
            self.app.select_tab(key)
            self.root.update_idletasks()
        # Verify no duplicate engines
        self.assertIs(self.app.conv_engine.behavior, self.app.sim.behavior_engine)
        self.assertIs(self.app.conv_engine.memory, self.app.memory_engine)
        self.assertIs(self.app.personality_panel.profile, self.app.sim.personality)

    def test_02_memory_panel_crud_excludes_unconfirmed_and_wipe_confirmation(self) -> None:
        # Unconfirmed proposal must NOT appear in MemoryPanel saved list
        prop = self.app.conv_engine.propose_fact("Segreto non confermato", category="note")
        self.assertIsNotNone(prop)
        self.app.memory_panel.refresh_lists()
        self.assertEqual(self.app.memory_panel.mem_list.size(), 0)

        # Confirming makes it visible, editable, and searchable
        self.app.conv_engine.confirm_memory(prop.proposal_id)
        self.app.memory_panel.refresh_lists()
        self.assertEqual(self.app.memory_panel.mem_list.size(), 1)

        # L2 preference add & delete
        self.app.memory_panel.pref_key_entry.insert(0, "citta")
        self.app.memory_panel.pref_val_entry.insert(0, "Torino")
        self.assertTrue(self.app.memory_panel.save_preference())
        self.assertEqual(self.app.memory_panel.pref_list.size(), 1)

        # Wipe aborted when confirmation returns False
        self.wipe_confirmed = False
        self.assertFalse(self.app.memory_panel.wipe_all_with_confirmation())
        self.assertEqual(self.app.memory_panel.mem_list.size(), 1)

        # Wipe executed when confirmation returns True
        self.wipe_confirmed = True
        self.assertTrue(self.app.memory_panel.wipe_all_with_confirmation())
        self.assertEqual(self.app.memory_panel.mem_list.size(), 0)
        self.assertEqual(self.app.memory_panel.pref_list.size(), 0)

    def test_03_settings_persistence_across_restart(self) -> None:
        self.app.personality_panel._scales["curiosity_bias"].set(0.95)
        self.app.personality_panel.initiatives_var.set(False)
        self.app.personality_panel.apply_and_save()
        self.app._on_toggle_persistent_memory(False)
        self.app.close()

        # Reopen with same data_dir
        root2 = tk.Tk()
        root2.withdraw()
        app2 = JarvisUnifiedApp(root2, data_dir=self.data_dir)
        try:
            self.assertAlmostEqual(app2.sim.personality.config.curiosity_bias, 0.95, places=2)
            self.assertFalse(app2.sim.personality.config.initiatives_enabled)
            self.assertFalse(app2.memory_engine.config.persistent_enabled)
        finally:
            app2.close()

    def test_04_quiet_mode_sync_and_spontaneous_initiatives_rules(self) -> None:
        # Never fires immediately at startup (grace period)
        self.assertIsNone(self.app.tick_spontaneous_initiatives(now_ms=100))

        # Quiet Mode suppresses spontaneous voice and syncs UI
        self.app._on_toggle_quiet_mode(True)
        self.assertTrue(self.app.sim.behavior_engine.quiet_mode)
        self.assertTrue(self.app.dashboard_panel.quiet_var.get())
        self.assertTrue(self.app.personality_panel.quiet_var.get())
        self.assertIsNone(self.app.tick_spontaneous_initiatives(now_ms=120_000))
        self.app._on_toggle_quiet_mode(False)

        # SLEEPING mode suppresses spontaneous voice
        self.app.sim.behavior_engine.set_mode(RobotMode.SLEEPING, 125_000)
        self.assertIsNone(self.app.tick_spontaneous_initiatives(now_ms=130_000))
        self.app.sim.behavior_engine.set_mode(RobotMode.IDLE, 135_000)

        # Respects 2/hour & 20 min interval after startup grace
        cue1 = self.app.tick_spontaneous_initiatives(now_ms=150_000)
        self.assertIsNotNone(cue1)
        time.sleep(0.04)  # wait for mock TTS of cue1 to finish before next simulated slot
        self.assertIsNone(self.app.tick_spontaneous_initiatives(now_ms=150_000 + 5 * 60 * 1000))
        cue2 = self.app.tick_spontaneous_initiatives(now_ms=150_000 + 21 * 60 * 1000)
        self.assertIsNotNone(cue2)
        time.sleep(0.04)
        self.assertIsNone(self.app.tick_spontaneous_initiatives(now_ms=150_000 + 42 * 60 * 1000))

    def test_05_no_duplicate_timers_state_updates_and_unavailable_services(self) -> None:
        first_tid = self.app._spontaneous_timer_id
        self.assertIsNotNone(first_tid)
        self.app._schedule_spontaneous_check()
        self.assertEqual(self.app._spontaneous_timer_id, first_tid)

        # Simulator control & state refresh
        self.app.simulator_panel.set_expression(Expression.CURIOUS)
        self.app.simulator_panel.look_at(5, -2)
        self.app._refresh_control_center()
        self.assertIn("CURIOUS", self.app.dashboard_panel.expr_var.get())
        self.assertIn("non connesso", self.app.dashboard_panel.hw_var.get())

        # Simulate unavailable Ollama in diagnostics/dashboard without crashing
        self.app.controller.select_provider("ollama", "llama3.2:3b")
        self.app._apply_probe_result({
            "pid": "ollama",
            "ai_ok": False,
            "ai_status": "offline",
            "stt_ok": True,
            "stt_msg": "ok",
            "tts_ok": True,
            "voices": ["Mock"],
            "models": [],
            "mic_names": ["Mic"],
        })
        self.assertIn("AI(ollama)=OFFLINE", self.app.dashboard_panel.services_var.get())
        self.assertIn("provider=ollama", self.app.diagnostics_panel.voice_var.get())

        # Clean shutdown cancels timer and closes DB
        self.app.close()
        self.assertTrue(self.app._closed)
        self.assertIsNone(self.app._spontaneous_timer_id)

    def test_06_personality_sliders_update_behavior_engine_and_spontaneous_overlap(self) -> None:
        self.app.personality_panel._scales["curiosity_bias"].set(0.95)
        self.app.personality_panel.initiatives_var.set(False)
        self.app.personality_panel.apply_and_save()
        self.assertAlmostEqual(self.app.sim.behavior_engine.personality.config.curiosity_bias, 0.95, places=2)
        self.assertIsNone(self.app.tick_spontaneous_initiatives(now_ms=150_000))

        # Re-enable initiatives, but simulate audio already playing -> must NOT overlap
        self.app.personality_panel.initiatives_var.set(True)
        self.app.personality_panel.apply_and_save()
        self.app.controller.tts.is_speaking = lambda: True  # type: ignore[method-assign]
        self.assertIsNone(self.app.tick_spontaneous_initiatives(now_ms=160_000))

    def test_07_corrupt_json_configs_and_diagnostics_no_personal_data(self) -> None:
        self.app.close()
        with tempfile.TemporaryDirectory() as corrupt_dir:
            cpath = Path(corrupt_dir)
            (cpath / "personality_config.json").write_text("{not valid json", encoding="utf-8")
            (cpath / "memory_config.json").write_text("{not valid json", encoding="utf-8")
            root_c = tk.Tk()
            root_c.withdraw()
            app_c = JarvisUnifiedApp(root_c, data_dir=cpath)
            try:
                self.assertTrue(app_c.memory_engine.config.persistent_enabled)
                self.assertTrue(app_c.sim.personality.config.initiatives_enabled)
                prop = app_c.conv_engine.propose_fact("Segreto personale Marco XYZ", category="note")
                app_c.conv_engine.confirm_memory(prop.proposal_id)
                app_c._refresh_control_center()
                diag_text = app_c.diagnostics_panel.events_box.get("1.0", "end")
                self.assertNotIn("Segreto personale Marco XYZ", diag_text)
                self.assertNotIn("Segreto personale Marco XYZ", app_c.diagnostics_panel.mem_var.get())
            finally:
                app_c.close()

    def test_08_close_during_active_conversation_clean(self) -> None:
        self.app.controller.select_provider("demo")
        self.app.conv_engine.submit_text("Ciao JARVIS")
        time.sleep(0.02)
        self.app.close()
        time.sleep(0.05)
        self.assertTrue(self.app._closed)
        self.assertIsNone(self.app._spontaneous_timer_id)

    def test_09_simulator_14_expressions_look_blink_and_fast_refresh(self) -> None:
        for expr in ALL_EXPRESSIONS:
            self.app.simulator_panel.set_expression(expr)
            # Run >15ms of Tk loop to prove _tick() does NOT revert expression to IDLE
            deadline = time.monotonic() + 0.03
            while time.monotonic() < deadline:
                self.root.update()
                time.sleep(0.005)
            self.assertEqual(self.app.sim.eyes.expr, expr)

        self.app.simulator_panel.look_at(8, -4)
        self.assertAlmostEqual(
            self.app.sim.eyes.left.target_x + self.app.sim.eyes.left.target_pupil_dx,
            self.app.sim.eyes.left.base_x + 8,
            places=5,
        )
        self.assertAlmostEqual(self.app.sim.eyes.left.target_y, self.app.sim.eyes.left.base_y - 1.6, places=5)
        self.assertAlmostEqual(self.app.sim.eyes.left.target_pupil_dy, -1.8, places=5)
        self.app.simulator_panel.trigger_blink()
        self.assertNotEqual(self.app.sim.eyes.blink_phase, "OPEN")

        t0 = time.perf_counter()
        self.app._refresh_control_center()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self.assertLess(elapsed_ms, 50.0)

    def test_10_lightweight_demo_mode_and_repeated_open_close(self) -> None:
        self.app.close()
        for _ in range(3):
            with tempfile.TemporaryDirectory() as d:
                r = tk.Tk()
                r.withdraw()
                a = JarvisUnifiedApp(r, data_dir=Path(d), demo_mode=True)
                try:
                    self.assertIsInstance(a.controller.stt, MockSTTProvider)
                    self.assertIsInstance(a.controller.tts, MockTTSProvider)
                    self.assertEqual(a.controller.active_provider_id, "demo")
                    self.assertIsNone(a.tick_spontaneous_initiatives(now_ms=200_000))
                    a.simulator_panel.set_expression(Expression.HAPPY)
                    r.update()
                    self.assertEqual(a.sim.eyes.expr, Expression.HAPPY)
                finally:
                    a.close()

    def test_11_memory_panel_empty_add_consent_edit_delete_filter_demo_and_disabled(self) -> None:
        self.app.close()
        with tempfile.TemporaryDirectory() as d:
            dpath = Path(d)
            r = tk.Tk()
            r.withdraw()
            a = JarvisUnifiedApp(r, data_dir=dpath, demo_mode=True)
            allow_add = [False]
            allow_del = [False]
            a.memory_panel._confirm_add_fn = lambda _lvl, _summary: allow_add[0]
            a.memory_panel._confirm_delete_fn = lambda _target: allow_del[0]
            try:
                # Initially empty DB -> explanatory message & '+ Aggiungi ricordo' button present
                self.assertIn("Nessun ricordo salvato", a.memory_panel.empty_info_var.get())
                self.assertTrue(a.memory_panel.add_btn.winfo_exists())

                # Unconfirmed L3/L4 must NOT be persisted
                allow_add[0] = False
                self.assertFalse(a.memory_panel.add_memory_with_consent("L3", "Fatto rifiutato"))
                self.assertFalse(a.memory_panel.add_memory_with_consent("L4", "Episodio rifiutato"))
                self.assertEqual(a.memory_panel.mem_list.size(), 0)

                # Confirmed L2, L3, L4 are persisted even in --demo mode
                allow_add[0] = True
                self.assertTrue(a.memory_panel.add_memory_with_consent("L2", "espresso", key="caffe"))
                self.assertTrue(a.memory_panel.add_memory_with_consent("L3", "Marco costruisce LEGO", category="hobby"))
                self.assertTrue(a.memory_panel.add_memory_with_consent("L4", "Collaudo Control Center", category="sessione"))

                # Filter by L2, L3, L4, Tutti + search
                a.memory_panel.level_filter_var.set("L2")
                a.memory_panel.refresh_lists()
                self.assertEqual(a.memory_panel.pref_list.size(), 1)
                self.assertEqual(a.memory_panel.mem_list.size(), 0)

                a.memory_panel.level_filter_var.set("L3")
                a.memory_panel.refresh_lists()
                self.assertEqual(a.memory_panel.mem_list.size(), 1)
                self.assertIn("LEGO", a.memory_panel.mem_list.get(0))

                a.memory_panel.level_filter_var.set("L4")
                a.memory_panel.refresh_lists()
                self.assertEqual(a.memory_panel.mem_list.size(), 1)
                self.assertIn("scade", a.memory_panel.mem_list.get(0))

                a.memory_panel.level_filter_var.set("Tutti")
                a.memory_panel.refresh_lists()
                self.assertEqual(a.memory_panel.mem_list.size(), 2)

                # Edit selected L3 memory
                a.memory_panel.mem_list.selection_set(0)
                a.memory_panel._on_select_memory()
                a.memory_panel.edit_entry.delete(0, "end")
                a.memory_panel.edit_entry.insert(0, "Marco costruisce LEGO Technic")
                self.assertTrue(a.memory_panel.update_selected_memory())
                self.assertTrue(any("Technic" in x.content for x in a.memory_engine.search_memories("Technic")))

                # Single delete requires confirmation
                a.memory_panel.mem_list.selection_set(0)
                allow_del[0] = False
                self.assertFalse(a.memory_panel.delete_selected_memory())
                allow_del[0] = True
                self.assertTrue(a.memory_panel.delete_selected_memory())

                # Disabled persistent memory shows explanation and blocks writes
                a._on_toggle_persistent_memory(False)
                self.assertIn("disabilitata", a.memory_panel.empty_info_var.get().lower())
                self.assertFalse(a.memory_panel.add_memory_with_consent("L3", "Non deve salvarsi"))
                a._on_toggle_persistent_memory(True)
            finally:
                a.close()

            # Persistence across restart
            r2 = tk.Tk()
            r2.withdraw()
            a2 = JarvisUnifiedApp(r2, data_dir=dpath, demo_mode=True)
            try:
                self.assertEqual(a2.memory_engine.get_preference("caffe"), "espresso")
                self.assertEqual(a2.memory_panel.pref_list.size(), 1)
            finally:
                a2.close()


if __name__ == "__main__":
    unittest.main()
