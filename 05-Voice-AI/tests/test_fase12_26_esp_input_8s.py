"""FASE 12.26 tests: 8s ESP32 microphone input (256000 B), TTS 640000 B invariant, and WebSocket edge cases."""

from __future__ import annotations

import logging
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

_VOICE_AI_DIR = Path(__file__).resolve().parent.parent
if str(_VOICE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_VOICE_AI_DIR))

from voice_bridge.api import create_app  # noqa: E402
from voice_bridge.audio import encode_wav_mono_16bit  # noqa: E402
from voice_bridge.config import BridgeConfig  # noqa: E402
from voice_bridge.pipeline import VoiceBridgeService  # noqa: E402
from voice_bridge.stt_engine import STTEngine, STTOptions  # noqa: E402
from voice_bridge.tts_engine import TTSEngine  # noqa: E402


class _FastSTT(STTEngine):
    def is_available(self) -> tuple[bool, str]:
        return True, "OK"

    def transcribe(
        self,
        wav_bytes_16k_mono: bytes,
        language: str = "it",
        timeout_s: float = 12.0,
        options: STTOptions | None = None,
    ) -> str:
        return "che ore sono"


class _FastTTS(TTSEngine):
    def is_available(self) -> tuple[bool, str]:
        return True, "OK"

    def synthesize(self, text: str, timeout_s: float = 10.0) -> bytes:
        return encode_wav_mono_16bit([100, -100] * 1600, 16000)


class Fase1226EspInput8sTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = BridgeConfig(
            temp_dir=Path(self.tmp.name),
            require_auth=True,
            device_token="browser-tok",
            esp_device_token="esp-tok",
            ai_mode="DISABLED",
            timezone="Europe/Rome",
            esp_max_input_bytes=256000,
            esp_max_tts_bytes=640000,
            esp_ws_chunk_bytes=2048,
        )
        self.svc = VoiceBridgeService(self.cfg, stt_engine=_FastSTT(), tts_engine=_FastTTS())
        self.client = TestClient(create_app(service=self.svc))

    def tearDown(self) -> None:
        self.svc.close()
        self.tmp.cleanup()

    def test_config_8s_input_and_profile08_tts_unchanged(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            cfg = BridgeConfig.from_env()
        self.assertEqual(cfg.esp_max_input_bytes, 256000)
        self.assertEqual(cfg.esp_max_tts_bytes, 640000)
        self.assertEqual(cfg.tts_max_chars, 270)
        self.assertEqual(cfg.tts_piper_speed, 1.00)
        self.assertAlmostEqual(cfg.tts_piper_noise_scale, 0.60, places=2)
        self.assertAlmostEqual(cfg.tts_piper_pitch_semitones, 5.0, places=2)
        self.assertEqual(cfg.tts_piper_dsp_method, "wsola")
        self.assertFalse(cfg.tts_piper_limiter_enabled)

    def _ws_upload_pcm(self, ws, req_id: str, total_bytes: int) -> list[dict]:
        ws.send_json(
            {
                "type": "audio_start",
                "request_id": req_id,
                "sr": 16000,
                "ch": 1,
                "bits": 16,
            }
        )
        ack = ws.receive_json()
        self.assertEqual(ack["type"], "ack")

        import struct

        chunk = b"".join(
            struct.pack("<h", int(3000.0 * math.sin(2.0 * math.pi * 500.0 * i / 16000.0)))
            for i in range(1024)
        )  # 2048 B non-silent PCM16
        sent = 0
        while sent < total_bytes:
            n = min(len(chunk), total_bytes - sent)
            ws.send_bytes(chunk[:n])
            sent += n

        ws.send_json({"type": "audio_end", "request_id": req_id, "samples": total_bytes // 2})
        events: list[dict] = []
        while True:
            msg = ws.receive()
            if "text" in msg and msg["text"] is not None:
                import json

                data = json.loads(msg["text"])
                events.append(data)
                if data.get("type") in {"tts_end", "error", "cancelled"}:
                    break
        return events

    def test_durations_1s_3s_5s_7s_8s_exact_and_over_8s_rejected(self) -> None:
        with self.client.websocket_connect("/ws/v1/esp32") as ws:
            ws.send_json({"type": "auth", "device_id": "jarvis-lego-01", "token": "esp-tok"})
            auth_ok = ws.receive_json()
            self.assertEqual(auth_ok["type"], "auth_ok")
            self.assertEqual(auth_ok["max_audio_bytes"], 256000)
            self.assertEqual(auth_ok["max_tts_bytes"], 640000)

            for idx, secs in enumerate((1, 3, 5, 7, 8), start=1):
                evs = self._ws_upload_pcm(ws, f"req-{secs}s", secs * 32000)
                self.assertEqual(evs[-1]["type"], "tts_end", f"Failed for {secs}s")

            # Exceeding 8s (256000 B + 2048 B) must fail cleanly with PAYLOAD_TOO_LARGE
            ws.send_json(
                {"type": "audio_start", "request_id": "req-over8s", "sr": 16000, "ch": 1, "bits": 16}
            )
            self.assertEqual(ws.receive_json()["type"], "ack")
            chunk = b"\x01\x00" * 1024
            for _ in range(125):
                ws.send_bytes(chunk)
            ws.send_bytes(chunk)  # 126th chunk -> 258048 B > 256000 B
            err = ws.receive_json()
            self.assertEqual(err["type"], "error")
            self.assertEqual(err["code"], "PAYLOAD_TOO_LARGE")

    def test_empty_invalid_and_early_disconnect(self) -> None:
        with self.client.websocket_connect("/ws/v1/esp32") as ws:
            ws.send_json({"type": "auth", "device_id": "jarvis-lego-01", "token": "esp-tok"})
            self.assertEqual(ws.receive_json()["type"], "auth_ok")

            # Empty buffer
            ws.send_json({"type": "audio_start", "request_id": "req-empty", "sr": 16000, "ch": 1, "bits": 16})
            self.assertEqual(ws.receive_json()["type"], "ack")
            ws.send_json({"type": "audio_end", "request_id": "req-empty", "samples": 0})
            err_empty = ws.receive_json()
            self.assertEqual(err_empty["code"], "INVALID_AUDIO_PAYLOAD")

            # Odd byte count (invalid PCM16)
            ws.send_json({"type": "audio_start", "request_id": "req-odd", "sr": 16000, "ch": 1, "bits": 16})
            self.assertEqual(ws.receive_json()["type"], "ack")
            ws.send_bytes(b"\x01" * 101)
            ws.send_json({"type": "audio_end", "request_id": "req-odd", "samples": 50})
            err_odd = ws.receive_json()
            self.assertEqual(err_odd["code"], "INVALID_AUDIO_PAYLOAD")

        # Early disconnect mid-upload (no audio_end)
        with self.client.websocket_connect("/ws/v1/esp32") as ws:
            ws.send_json({"type": "auth", "device_id": "jarvis-lego-01", "token": "esp-tok"})
            self.assertEqual(ws.receive_json()["type"], "auth_ok")
            ws.send_json({"type": "audio_start", "request_id": "req-drop", "sr": 16000, "ch": 1, "bits": 16})
            self.assertEqual(ws.receive_json()["type"], "ack")
            ws.send_bytes(b"\x00\x01" * 512)

    def test_esp_audio_rx_diagnostic_log_limit_flag(self) -> None:
        with self.assertLogs("jarvis.voice_bridge", level=logging.INFO) as logs:
            with self.client.websocket_connect("/ws/v1/esp32") as ws:
                ws.send_json({"type": "auth", "device_id": "jarvis-lego-01", "token": "esp-tok"})
                self.assertEqual(ws.receive_json()["type"], "auth_ok")
                self._ws_upload_pcm(ws, "req-diag-8s", 256000)
        joined = "\n".join(logs.output)
        self.assertIn("ESP_AUDIO_RX pcm_bytes=256000 dur_s=8.00 max_bytes=256000 limit_reached=True", joined)


if __name__ == "__main__":
    unittest.main()
