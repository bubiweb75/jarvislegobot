"""Automated tests for FASE 11.3A ESP32-S3 WebSocket protocol (/ws/v1/esp32)."""

from __future__ import annotations

import array
import json
from pathlib import Path
import sys
import tempfile
import unittest

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

_VOICE_AI_DIR = Path(__file__).resolve().parent.parent
if str(_VOICE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_VOICE_AI_DIR))

from voice_bridge.api import create_app  # noqa: E402
from voice_bridge.config import BridgeConfig  # noqa: E402
from voice_bridge.pipeline import VoiceBridgeService  # noqa: E402
from voice_bridge.stt_engine import MockSTTEngine  # noqa: E402
from voice_bridge.tts_engine import MockTTSEngine  # noqa: E402


def _make_pcm16_bytes(dur_s: float = 0.25, sr: int = 16000, amp: int = 3000) -> bytes:
    n = int(sr * dur_s)
    samples = [amp if (i % 16) < 8 else -amp for i in range(n)]
    return array.array("h", samples).tobytes()


class TestEsp32WebSocketProtocol(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory(prefix="jarvis_esp_ws_")
        self.browser_token = "browser-secret-token-123456"
        self.esp_token = "esp32-device-token-abcdef"
        self.cfg = BridgeConfig(
            host="127.0.0.1",
            port=8765,
            device_token=self.browser_token,
            esp_device_token=self.esp_token,
            require_auth=True,
            ollama_enabled=False,
            cloud_enabled=False,
            temp_dir=Path(self.tmp_dir.name),
            esp_max_input_bytes=160000,
            esp_max_tts_bytes=640000,
            esp_ws_chunk_bytes=2048,
            esp_ws_idle_timeout_s=5.0,
        )
        self.svc = VoiceBridgeService(
            config=self.cfg,
            stt_engine=MockSTTEngine(transcript="Ciao Jarvis, che ore sono?"),
            tts_engine=MockTTSEngine(),
        )
        self.client = TestClient(create_app(self.svc))

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_01_02_auth_bearer_json_rejects_wrong_and_browser_token(self) -> None:
        # Wrong token in JSON auth
        with self.client.websocket_connect("/ws/v1/esp32") as ws:
            ws.send_text(json.dumps({"v": "1.0", "type": "auth", "device_id": "esp1", "token": "wrong"}))
            err = json.loads(ws.receive_text())
            self.assertEqual(err["type"], "error")
            self.assertEqual(err["code"], "UNAUTHORIZED")

        # Browser token must NOT authenticate ESP32 endpoint
        with self.client.websocket_connect("/ws/v1/esp32") as ws:
            ws.send_text(json.dumps({"v": "1.0", "type": "auth", "device_id": "esp1", "token": self.browser_token}))
            err = json.loads(ws.receive_text())
            self.assertEqual(err["code"], "UNAUTHORIZED")

        # Valid Bearer header
        with self.client.websocket_connect(
            "/ws/v1/esp32",
            headers={"Authorization": f"Bearer {self.esp_token}"},
        ) as ws:
            ok = json.loads(ws.receive_text())
            self.assertEqual(ok["type"], "auth_ok")
            self.assertEqual(ok["max_audio_bytes"], 160000)

        # Secret must never leak into diagnostics/logs
        from voice_bridge.security import redact_secrets
        self.assertNotIn(self.esp_token, redact_secrets(f"tok={self.esp_token}", self.svc.diagnostics._secrets))

    def test_03_04_05_10_full_audio_turn_ping_and_tts_binary_integrity(self) -> None:
        pcm_in = _make_pcm16_bytes(dur_s=0.3, amp=3500)
        with self.client.websocket_connect("/ws/v1/esp32") as ws:
            ws.send_text(json.dumps({"v": "1.0", "type": "auth", "device_id": "jarvis-01", "token": self.esp_token}))
            auth_ok = json.loads(ws.receive_text())
            self.assertEqual(auth_ok["type"], "auth_ok")

            ws.send_text(json.dumps({"v": "1.0", "type": "ping", "ts": 1234}))
            pong = json.loads(ws.receive_text())
            self.assertEqual(pong["type"], "pong")
            self.assertEqual(pong["ts"], 1234)

            ws.send_text(
                json.dumps(
                    {
                        "v": "1.0",
                        "type": "audio_start",
                        "request_id": "req-1",
                        "sr": 16000,
                        "ch": 1,
                        "bits": 16,
                    }
                )
            )
            ack = json.loads(ws.receive_text())
            self.assertEqual(ack["type"], "ack")
            self.assertEqual(ack["request_id"], "req-1")

            for off in range(0, len(pcm_in), 2048):
                ws.send_bytes(pcm_in[off : off + 2048])

            ws.send_text(json.dumps({"v": "1.0", "type": "audio_end", "request_id": "req-1", "samples": len(pcm_in) // 2}))

            tts_start = json.loads(ws.receive_text())
            self.assertEqual(tts_start["type"], "tts_start")
            self.assertEqual(tts_start["provider_used"], "Local Intent")
            self.assertEqual(tts_start["sr"], 16000)
            self.assertEqual(tts_start["ch"], 1)
            self.assertEqual(tts_start["bits"], 16)
            expected_bytes = tts_start["total_bytes"]
            self.assertGreater(expected_bytes, 0)

            received_pcm = bytearray()
            while len(received_pcm) < expected_bytes:
                received_pcm.extend(ws.receive_bytes())
            self.assertEqual(len(received_pcm), expected_bytes)

            tts_end = json.loads(ws.receive_text())
            self.assertEqual(tts_end["type"], "tts_end")
            self.assertEqual(tts_end["total_bytes"], expected_bytes)

    def test_06_07_idle_timeout_and_reconnect(self) -> None:
        cfg_to = BridgeConfig(
            device_token=self.browser_token,
            esp_device_token=self.esp_token,
            require_auth=True,
            ollama_enabled=False,
            cloud_enabled=False,
            temp_dir=Path(self.tmp_dir.name),
            esp_ws_idle_timeout_s=0.1,
        )
        svc_to = VoiceBridgeService(config=cfg_to, stt_engine=MockSTTEngine(), tts_engine=MockTTSEngine())
        client_to = TestClient(create_app(svc_to))

        with client_to.websocket_connect(
            "/ws/v1/esp32",
            headers={"Authorization": f"Bearer {self.esp_token}"},
        ) as ws:
            _ = json.loads(ws.receive_text())
            err = json.loads(ws.receive_text())
            self.assertEqual(err["code"], "SESSION_TIMEOUT")

        # Reconnect after timeout works cleanly
        with client_to.websocket_connect(
            "/ws/v1/esp32",
            headers={"Authorization": f"Bearer {self.esp_token}"},
        ) as ws2:
            ok = json.loads(ws2.receive_text())
            self.assertEqual(ok["type"], "auth_ok")

    def test_08_09_disconnect_mid_upload_and_cancel(self) -> None:
        pcm_in = _make_pcm16_bytes(dur_s=0.1)
        # Mid-upload disconnect
        with self.client.websocket_connect(
            "/ws/v1/esp32",
            headers={"Authorization": f"Bearer {self.esp_token}"},
        ) as ws:
            _ = json.loads(ws.receive_text())
            ws.send_text(json.dumps({"v": "1.0", "type": "audio_start", "request_id": "req-drop", "sr": 16000, "ch": 1, "bits": 16}))
            _ = json.loads(ws.receive_text())
            ws.send_bytes(pcm_in[:1024])

        # Next session works + CANCEL discards buffer
        with self.client.websocket_connect(
            "/ws/v1/esp32",
            headers={"Authorization": f"Bearer {self.esp_token}"},
        ) as ws:
            _ = json.loads(ws.receive_text())
            ws.send_text(json.dumps({"v": "1.0", "type": "audio_start", "request_id": "req-cancel", "sr": 16000, "ch": 1, "bits": 16}))
            _ = json.loads(ws.receive_text())
            ws.send_bytes(pcm_in)
            ws.send_text(json.dumps({"v": "1.0", "type": "cancel", "request_id": "req-cancel"}))
            c = json.loads(ws.receive_text())
            self.assertEqual(c["type"], "cancelled")
            self.assertEqual(c["request_id"], "req-cancel")

    def test_11_12_13_14_tts_too_long_payload_limit_malformed_and_duplicate(self) -> None:
        pcm_in = _make_pcm16_bytes(dur_s=0.25)
        # 11. TTS too long
        cfg_small_tts = BridgeConfig(
            device_token=self.browser_token,
            esp_device_token=self.esp_token,
            require_auth=True,
            ollama_enabled=False,
            cloud_enabled=False,
            temp_dir=Path(self.tmp_dir.name),
            esp_max_tts_bytes=64,
        )
        svc_small = VoiceBridgeService(
            config=cfg_small_tts,
            stt_engine=MockSTTEngine(transcript="Ciao"),
            tts_engine=MockTTSEngine(),
        )
        c_small = TestClient(create_app(svc_small))
        with c_small.websocket_connect(
            "/ws/v1/esp32",
            headers={"Authorization": f"Bearer {self.esp_token}"},
        ) as ws:
            _ = json.loads(ws.receive_text())
            ws.send_text(json.dumps({"v": "1.0", "type": "audio_start", "request_id": "r-long", "sr": 16000, "ch": 1, "bits": 16}))
            _ = json.loads(ws.receive_text())
            for off in range(0, len(pcm_in), 2048):
                ws.send_bytes(pcm_in[off : off + 2048])
            ws.send_text(json.dumps({"v": "1.0", "type": "audio_end", "request_id": "r-long"}))
            err = json.loads(ws.receive_text())
            self.assertEqual(err["code"], "TTS_TOO_LONG")

        # 12, 13, 14: Malformed JSON, unexpected binary, duplicate request, oversized payload
        with self.client.websocket_connect(
            "/ws/v1/esp32",
            headers={"Authorization": f"Bearer {self.esp_token}"},
        ) as ws:
            _ = json.loads(ws.receive_text())
            ws.send_text("{bad-json")
            self.assertEqual(json.loads(ws.receive_text())["code"], "MALFORMED_JSON")

            ws.send_bytes(b"\x01\x02")
            self.assertEqual(json.loads(ws.receive_text())["code"], "UNEXPECTED_BINARY")

            ws.send_text(json.dumps({"v": "1.0", "type": "audio_start", "request_id": "r1", "sr": 44100, "ch": 1, "bits": 16}))
            self.assertEqual(json.loads(ws.receive_text())["code"], "UNSUPPORTED_AUDIO_FORMAT")

            ws.send_text(json.dumps({"v": "1.0", "type": "audio_start", "request_id": "r-dup", "sr": 16000, "ch": 1, "bits": 16}))
            self.assertEqual(json.loads(ws.receive_text())["type"], "ack")

            ws.send_text(json.dumps({"v": "1.0", "type": "audio_start", "request_id": "r-dup", "sr": 16000, "ch": 1, "bits": 16}))
            self.assertEqual(json.loads(ws.receive_text())["code"], "DUPLICATE_REQUEST")

            # Exceed 160,000 B using 4096 B chunks
            for _ in range(40):
                ws.send_bytes(b"\x00" * 4096)
            self.assertEqual(json.loads(ws.receive_text())["code"], "PAYLOAD_TOO_LARGE")

    def test_15_voice_lab_http_remains_compatible(self) -> None:
        r_http = self.client.get("/")
        self.assertEqual(r_http.status_code, 200)
        # Browser token works on HTTP session endpoint, ESP token does NOT
        r_bad = self.client.post("/api/v1/auth/session", json={"token": self.esp_token})
        self.assertEqual(r_bad.status_code, 401)
        r_ok = self.client.post("/api/v1/auth/session", json={"token": self.browser_token})
        self.assertEqual(r_ok.status_code, 200)


if __name__ == "__main__":
    unittest.main()
