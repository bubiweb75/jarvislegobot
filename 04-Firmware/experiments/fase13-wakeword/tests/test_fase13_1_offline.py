"""Offline verification tests for FASE 13.1 microWakeWord prototype."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import unittest

PROTO_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = PROTO_DIR / "model"
REPO_ROOT = PROTO_DIR.parent.parent.parent


class Fase131OfflineTests(unittest.TestCase):
    def test_official_hey_jarvis_model_and_manifest(self) -> None:
        manifest = json.loads((MODEL_DIR / "hey_jarvis.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["wake_word"], "Hey Jarvis")
        self.assertEqual(manifest["version"], 2)
        self.assertEqual(manifest["micro"]["probability_cutoff"], 0.97)
        self.assertEqual(manifest["micro"]["sliding_window_size"], 5)
        self.assertEqual(manifest["micro"]["feature_step_size"], 10)
        self.assertEqual(manifest["micro"]["tensor_arena_size"], 22860)

        tflite_bytes = (MODEL_DIR / "hey_jarvis.tflite").read_bytes()
        self.assertEqual(len(tflite_bytes), 52272)
        self.assertEqual(
            hashlib.sha256(tflite_bytes).hexdigest().upper(),
            "21A7976ADD39EE24EC96C63D96B7AAA18E24D1D9824B963E451DA8FEB4B78B77",
        )
        self.assertTrue((MODEL_DIR / "LICENSE").is_file())

    def test_c_header_matches_tflite_binary(self) -> None:
        tflite_bytes = (MODEL_DIR / "hey_jarvis.tflite").read_bytes()
        header_txt = (PROTO_DIR / "hey_jarvis_model.h").read_text(encoding="utf-8")
        hex_vals = [int(h, 16) for h in re.findall(r"0x([0-9a-fA-F]{2})", header_txt)]
        self.assertEqual(len(hex_vals), len(tflite_bytes))
        self.assertEqual(bytes(hex_vals), tflite_bytes)

    def test_detector_and_state_machine_invariants(self) -> None:
        hdr = (PROTO_DIR / "wakeword_engine.h").read_text(encoding="utf-8")
        cpp = (PROTO_DIR / "wakeword_engine.cpp").read_text(encoding="utf-8")
        ino = (PROTO_DIR / "fase13-wakeword.ino").read_text(encoding="utf-8")

        self.assertIn("class MicroWakeWordDetector final : public IWakeWordDetector", hdr)
        self.assertIn("kTensorArenaBytes = 32768U", hdr)
        self.assertIn("kSlidingWindowSize = 5U", hdr)
        self.assertIn("kProbabilityCutoff = 0.97f", hdr)
        self.assertIn("kCapacitySamples = 8000U", hdr)  # 500 ms @ 16 kHz

        for op in (
            "AddAssignVariable()",
            "AddCallOnce()",
            "AddConcatenation()",
            "AddConv2D()",
            "AddDepthwiseConv2D()",
            "AddFullyConnected()",
            "AddLogistic()",
            "AddQuantize()",
            "AddReadVariable()",
            "AddReshape()",
            "AddStridedSlice()",
            "AddVarHandle()",
        ):
            self.assertIn(op, cpp)

        for state in (
            "WakeState::kBoot",
            "WakeState::kIdle",
            "WakeState::kWakeDetected",
            "WakeState::kCommandListening",
            "WakeState::kProcessing",
            "WakeState::kSpeaking",
            "WakeState::kError",
            "WakeState::kRecovery",
        ):
            self.assertIn(state, cpp)
        self.assertIn("kPostCycleGuardMs = 1000U", ino)
        self.assertIn("kButtonPin = 47", ino)
        self.assertIn("I2S_NUM_1", ino)
        self.assertIn("FlushSpeakerSilence", ino)
        self.assertNotIn("ResetAll()", cpp)

    def test_stable_firmware_unmodified(self) -> None:
        stable_ino = REPO_ROOT / "04-Firmware" / "arduino-hw-test" / "jarvis_wifi_voice_client" / "jarvis_wifi_voice_client.ino"
        txt = stable_ino.read_text(encoding="utf-8")
        self.assertIn("kMaxRecordMs = 8000U", txt)
        self.assertNotIn("Chirale_TensorFlowLite", txt)


if __name__ == "__main__":
    unittest.main()
