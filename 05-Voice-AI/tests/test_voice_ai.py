"""Automated tests for JARVIS Voice & AI Hybrid (FASE 5)."""

import os
from pathlib import Path
import sys
import time
import unittest

VOICE_DIR = Path(__file__).resolve().parent.parent
SIM_DIR = VOICE_DIR.parent / "04-Firmware" / "jarvis-desk-buddy-sim"
for p in (VOICE_DIR, SIM_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from ai_providers import AIProvider, AIProviderError, AIResponse, OllamaProvider, OpenAIProvider  # noqa: E402
from audio_input import AudioInputError  # noqa: E402
from config import JarvisConfig  # noqa: E402
from eye_bridge import EyeBridge, SimulatorQueueTransport  # noqa: E402
from eye_engine import EyeEngine, Expression, SimulatorStateMachine  # noqa: E402
from stt_providers import MockSTTProvider  # noqa: E402
from tts_providers import (  # noqa: E402
    MockTTSProvider,
    PiperWithFallbackTTSProvider,
    VOICE_JARVIS_RICCARDO,
    WindowsSapiTTSProvider,
)
from voice_dsp import shape_piper_wav  # noqa: E402
from voice_controller import VoiceController, VoicePhase  # noqa: E402


class FakeRecorder:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.started = False
        self.cancelled = False

    def start_recording(self) -> None:
        if self.should_fail:
            raise AudioInputError("Microfono assente")
        self.started = True

    def stop_recording(self) -> bytes:
        self.started = False
        return b"RIFFfakewav"

    def cancel(self) -> None:
        self.started = False
        self.cancelled = True


class SlowMockProvider(AIProvider):
    provider_id = "slow"
    display_name = "Slow Mock"

    def is_available(self):
        return True, "ok"

    def list_models(self):
        return ["slow-1"]

    def generate(self, messages, model=""):
        time.sleep(0.15)
        return AIResponse(text="Risposta lenta", provider_name="Slow Mock")


class TestVoiceAndAI(unittest.TestCase):
    def _make_controller(self, stt=None, tts=None, recorder=None, providers=None):
        cfg = JarvisConfig(ai_provider="demo")
        transport = SimulatorQueueTransport()
        bridge = EyeBridge(transport=transport)
        ctrl = VoiceController(
            config=cfg,
            eye_bridge=bridge,
            recorder=recorder or FakeRecorder(),
            stt=stt or MockSTTProvider("Ciao JARVIS"),
            tts=tts or MockTTSProvider(delay_s=0.04),
            providers=providers,
        )
        return ctrl, transport

    def test_1_provider_selection_and_invalid(self) -> None:
        ctrl, _ = self._make_controller()
        self.assertEqual(ctrl.active_provider_id, "demo")
        ctrl.select_provider("ollama", "llama3.2:3b")
        self.assertEqual(ctrl.active_provider_id, "ollama")
        self.assertEqual(ctrl.active_model, "llama3.2:3b")
        with self.assertRaises(ValueError):
            ctrl.select_provider("non_existent")

    def test_2_simulated_provider_and_session_context(self) -> None:
        ctrl, transport = self._make_controller()
        ctrl.submit_text("Come ti chiami?")
        time.sleep(0.18)
        ctrl.submit_text("Cosa ti ho chiesto prima?")
        time.sleep(0.18)
        msgs = ctrl.conversation.get_messages_for_model()
        self.assertGreaterEqual(len(msgs), 5)  # system + 2 turns
        self.assertIn("Come ti chiami?", msgs[-1]["content"])

    def test_3_ollama_unavailable_no_cloud_fallback(self) -> None:
        ollama = OllamaProvider(base_url="http://127.0.0.1:19999", timeout_s=0.5)
        ok, msg = ollama.is_available()
        self.assertFalse(ok)
        self.assertIn("non", msg.lower())

        ctrl, transport = self._make_controller()
        ctrl.providers["ollama"] = ollama
        ctrl.select_provider("ollama", "llama3.2:3b")
        ctrl.submit_text("Ciao")
        deadline = time.monotonic() + 3.0
        while ctrl.phase == VoicePhase.THINKING and time.monotonic() < deadline:
            time.sleep(0.05)

        cmds = []
        transport.drain(cmds.append)
        self.assertIn("STATE:THINKING", cmds)
        self.assertIn("STATE:CURIOUS", cmds)
        self.assertEqual(ctrl.active_provider_id, "ollama")  # never switched to cloud

    def test_4_openai_missing_key_and_unconfirmed(self) -> None:
        prov = OpenAIProvider(api_key_getter=lambda: "")
        ok, _ = prov.is_available()
        self.assertFalse(ok)
        with self.assertRaises(AIProviderError):
            prov.generate([{"role": "user", "content": "ciao"}])

        prov_with_key = OpenAIProvider(api_key_getter=lambda: "sk-test-fake")
        ok2, msg2 = prov_with_key.is_available()
        self.assertFalse(ok2)
        self.assertIn("conferma", msg2.lower())
        with self.assertRaises(AIProviderError):
            prov_with_key.generate([{"role": "user", "content": "ciao"}])

    def test_5_and_6_full_voice_transitions_idle_listening_thinking_speaking_idle(self) -> None:
        ctrl, transport = self._make_controller(stt=MockSTTProvider("Dimmi qualcosa di breve"))
        ctrl.start_push_to_talk()
        self.assertEqual(ctrl.phase, VoicePhase.LISTENING)
        ctrl.stop_push_to_talk_and_process()
        time.sleep(0.22)

        cmds = []
        transport.drain(cmds.append)
        self.assertEqual(cmds, ["STATE:LISTENING", "STATE:THINKING", "STATE:SPEAKING", "STATE:IDLE"])
        self.assertEqual(ctrl.phase, VoicePhase.IDLE)

    def test_7_interrupt_stops_tts_and_returns_idle(self) -> None:
        tts = MockTTSProvider(delay_s=1.0)
        ctrl, transport = self._make_controller(tts=tts)
        ctrl.submit_text("Ciao")
        time.sleep(0.08)
        ctrl.interrupt()
        self.assertEqual(ctrl.phase, VoicePhase.IDLE)
        self.assertFalse(tts.is_speaking())
        cmds = []
        transport.drain(cmds.append)
        self.assertEqual(cmds[-1], "STATE:IDLE")

    def test_8_stt_and_tts_error_handling(self) -> None:
        ctrl_stt, tr_stt = self._make_controller(stt=MockSTTProvider(should_fail=True))
        ctrl_stt.start_push_to_talk()
        ctrl_stt.stop_push_to_talk_and_process()
        time.sleep(0.15)
        cmds_stt = []
        tr_stt.drain(cmds_stt.append)
        self.assertIn("STATE:CURIOUS", cmds_stt)

        ctrl_tts, tr_tts = self._make_controller(tts=MockTTSProvider(should_fail=True, delay_s=0.02))
        ctrl_tts.submit_text("Dimmi qualcosa")
        time.sleep(0.15)
        cmds_tts = []
        tr_tts.drain(cmds_tts.append)
        self.assertIn("STATE:CURIOUS", cmds_tts)

    def test_9_oled_simulator_compatibility(self) -> None:
        eyes = EyeEngine(fps=50, spacing_px=16)
        sm = SimulatorStateMachine(eyes, auto_demo=False)
        ctrl, transport = self._make_controller()
        ctrl.submit_text("Chi sei?")
        time.sleep(0.20)

        cmds = []
        transport.drain(lambda c: (cmds.append(c), sm.handle_command(c, 100)))
        self.assertIn("STATE:THINKING", cmds)
        self.assertIn("STATE:SPEAKING", cmds)
        self.assertIn("STATE:IDLE", cmds)
        self.assertEqual(eyes.expr, Expression.IDLE)

    def test_10_windows_local_tts_voices_present(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows only")
        tts = WindowsSapiTTSProvider()
        voices = tts.list_voices()
        self.assertGreater(len(voices), 0, "Expected at least one local Windows SAPI TTS voice")

    def test_11_piper_tts_list_voices_and_fallback(self) -> None:
        mock_fb = MockTTSProvider(delay_s=0.02)
        tts = PiperWithFallbackTTSProvider(fallback=mock_fb)
        voices = tts.list_voices()
        if (VOICE_DIR / "tts-lab" / "bin" / "piper" / "piper.exe").is_file():
            self.assertIn(VOICE_JARVIS_RICCARDO, voices)
            self.assertEqual(voices[0], VOICE_JARVIS_RICCARDO)
        self.assertIn("Microsoft Elsa Desktop", voices)

        missing_piper = PiperWithFallbackTTSProvider(
            piper_exe=VOICE_DIR / "nonexistent_piper.exe",
            fallback=mock_fb,
        )
        done_errs = []
        missing_piper.speak("Ciao prova fallback", voice=VOICE_JARVIS_RICCARDO, on_done=done_errs.append)
        time.sleep(0.08)
        self.assertEqual(mock_fb.spoken_texts, ["Ciao prova fallback"])
        self.assertEqual(done_errs, [None])

    def test_12_voice_dsp_shape_piper_wav(self) -> None:
        import io
        import wave
        import numpy as np

        sr = 16000
        t = np.linspace(0, 0.2, int(sr * 0.2), endpoint=False)
        samples = (np.sin(2 * np.pi * 220 * t) * 12000).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(samples.tobytes())

        shaped, dur = shape_piper_wav(buf.getvalue(), pitch_semitones=5.0, robot_mix=0.0, volume=90)
        self.assertGreater(len(shaped), 44)
        self.assertAlmostEqual(dur, 0.2, delta=0.05)


if __name__ == "__main__":
    unittest.main(verbosity=2)
