"""Automated unit & simulated integration tests for JARVIS Voice Bridge (FASE 11.2B)."""

from __future__ import annotations

import base64
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
import wave

import httpx
from fastapi.testclient import TestClient

_VOICE_AI_DIR = Path(__file__).resolve().parent.parent
if str(_VOICE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_VOICE_AI_DIR))

from ai_providers import AIProvider, AIProviderError, AIResponse  # noqa: E402
from voice_bridge.ai_router import AIRouter, CloudAIClient, OllamaRouterClient  # noqa: E402
from voice_bridge.api import create_app  # noqa: E402
from voice_bridge.audio import encode_wav_mono_16bit, read_piper_model_sample_rate, validate_and_normalize_wav  # noqa: E402
from voice_bridge.config import BridgeConfig  # noqa: E402
from voice_bridge.pipeline import CancellationToken, VoiceBridgeService  # noqa: E402
from voice_bridge.schemas import BridgeError  # noqa: E402
from voice_bridge.security import safe_temp_path  # noqa: E402
from voice_bridge.stt_engine import MockSTTEngine  # noqa: E402
from voice_bridge.tts_engine import MockTTSEngine  # noqa: E402


def _make_sine_wav(sr: int = 16000, dur_s: float = 0.25, amp: int = 3000) -> bytes:
    n = int(round(sr * dur_s))
    samples = [int(round(amp * math.sin(2.0 * math.pi * 440.0 * i / float(sr)))) for i in range(n)]
    return encode_wav_mono_16bit(samples, sr)


class _FakeCloudAI(AIProvider):
    provider_id = "fake_cloud"
    display_name = "Fake Cloud"

    def __init__(self, should_fail: bool = False, reply: str = "Risposta dal cloud simulato.") -> None:
        self.should_fail = should_fail
        self.reply = reply

    def is_available(self):
        return True, "ok"

    def list_models(self):
        return ["fake-model"]

    def generate(self, messages, model: str = "") -> AIResponse:
        if self.should_fail:
            raise AIProviderError("Cloud non raggiungibile")
        return AIResponse(text=self.reply, provider_name=self.display_name)


class TestVoiceBridge(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.cfg = BridgeConfig(
            device_token="secret-bridge-token-1234",
            require_auth=True,
            max_wav_bytes=200 * 1024,
            max_audio_duration_s=10.0,
            temp_dir=Path(self.tmp_dir.name),
            audio_ttl_s=60.0,
            ollama_enabled=False,
            cloud_enabled=False,
            cloud_api_key="sk-testsecret99999999",
        )

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def _headers(self, token: str = "secret-bridge-token-1234") -> dict:
        return {"Authorization": f"Bearer {token}"}

    def test_01_02_app_startup_and_health_and_ready(self) -> None:
        svc = VoiceBridgeService(
            config=self.cfg,
            stt_engine=MockSTTEngine(),
            tts_engine=MockTTSEngine(),
        )
        client = TestClient(create_app(svc))
        r = client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")
        self.assertNotIn("secret", r.text)

        rr = client.get("/ready", headers=self._headers())
        self.assertEqual(rr.status_code, 200)
        self.assertTrue(rr.json()["ready"])
        self.assertTrue(rr.json()["providers"]["offline_fallback"]["available"])

    def test_03_04_05_wav_validation_rejects_invalid_and_oversized(self) -> None:
        wav_22k = _make_sine_wav(sr=22050, dur_s=0.2)
        norm = validate_and_normalize_wav(wav_22k, max_bytes=100_000, max_duration_s=5.0, target_sr=16000)
        self.assertEqual(norm.sample_rate, 16000)
        self.assertEqual(norm.channels, 1)
        self.assertEqual(norm.sample_width, 2)

        with self.assertRaises(BridgeError) as ctx_bad:
            validate_and_normalize_wav(b"NOT_A_WAV_FILE" * 5, max_bytes=100_000, max_duration_s=5.0)
        self.assertEqual(ctx_bad.exception.code, "INVALID_WAV")

        svc = VoiceBridgeService(config=self.cfg, stt_engine=MockSTTEngine(), tts_engine=MockTTSEngine())
        client = TestClient(create_app(svc))
        huge = b"RIFF" + b"\x00" * (self.cfg.max_wav_bytes + 10)
        r = client.post(
            "/api/v1/voice/process",
            headers=self._headers(),
            files={"file": ("big.wav", huge, "audio/wav")},
        )
        self.assertEqual(r.status_code, 413)
        self.assertEqual(r.json()["error"]["code"], "PAYLOAD_TOO_LARGE")

    def test_06_07_stt_and_tts_mocks_and_piper_metadata(self) -> None:
        meta_file = Path(self.tmp_dir.name) / "it_IT-test.onnx.json"
        meta_file.write_text(json.dumps({"audio": {"sample_rate": 22050}}), encoding="utf-8")
        self.assertEqual(read_piper_model_sample_rate(str(Path(self.tmp_dir.name) / "it_IT-test.onnx")), 22050)

        svc = VoiceBridgeService(
            config=self.cfg,
            stt_engine=MockSTTEngine(transcript="Ciao Jarvis"),
            tts_engine=MockTTSEngine(sample_rate=22050),
        )
        client = TestClient(create_app(svc))
        wav_in = _make_sine_wav()

        r_stt = client.post("/api/v1/stt", headers=self._headers(), files={"file": ("q.wav", wav_in, "audio/wav")})
        self.assertEqual(r_stt.status_code, 200)
        self.assertEqual(r_stt.json()["transcript"], "Ciao Jarvis")

        r_tts = client.post("/api/v1/tts", headers=self._headers(), json={"text": "Ciao utente"})
        self.assertEqual(r_tts.status_code, 200)
        with wave.open(io.BytesIO(r_tts.content), "rb") as wf:
            self.assertEqual(wf.getframerate(), 16000)
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)

    def test_08_09_10_11_12_13_ai_router_priorities_and_fallbacks(self) -> None:
        def ollama_ok_handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/tags":
                return httpx.Response(200, json={"models": [{"name": "qwen2.5:7b"}]})
            return httpx.Response(200, json={"message": {"content": "Risposta da Ollama!"}})

        def ollama_down_handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        # 8. Ollama available
        cfg_local = BridgeConfig(
            device_token=self.cfg.device_token,
            ai_mode="LOCAL_FIRST",
            ai_fallback_enabled=True,
            ollama_enabled=True,
        )
        ol_ok = OllamaRouterClient("http://127.0.0.1:11434", "qwen2.5:7b", transport=httpx.MockTransport(ollama_ok_handler))
        router1 = AIRouter(cfg_local, ollama_client=ol_ok)
        res1 = router1.route([{"role": "user", "content": "ciao"}], "ciao")
        self.assertTrue(res1.provider_used.startswith("ollama:"))
        self.assertFalse(res1.fallback_used)

        # 9 & 10. Ollama unavailable -> Cloud fallback
        ol_down = OllamaRouterClient("http://127.0.0.1:11434", "qwen2.5:7b", transport=httpx.MockTransport(ollama_down_handler))
        cfg_cloud = BridgeConfig(
            device_token=self.cfg.device_token,
            ai_mode="LOCAL_FIRST",
            ai_fallback_enabled=True,
            ollama_enabled=True,
            cloud_enabled=True,
            cloud_provider="openai",
            cloud_api_key="sk-testsecret99999999",
        )
        cloud_ok = CloudAIClient(cfg_cloud, custom_provider=_FakeCloudAI(should_fail=False))
        router2 = AIRouter(cfg_cloud, ollama_client=ol_down, cloud_client=cloud_ok)
        res2 = router2.route([{"role": "user", "content": "ciao"}], "ciao")
        self.assertEqual(res2.provider_used, "cloud:openai")
        self.assertTrue(res2.fallback_used)

        # 11. Cloud not configured -> Offline fallback
        router3 = AIRouter(self.cfg, ollama_client=ol_down)
        res3 = router3.route([{"role": "user", "content": "ciao"}], "ciao")
        self.assertEqual(res3.provider_used, "offline_fallback")
        self.assertTrue(res3.fallback_used)

        # 12 & 13. Cloud unavailable -> Offline fallback (for non-local-intent queries)
        cloud_fail = CloudAIClient(cfg_cloud, custom_provider=_FakeCloudAI(should_fail=True))
        router4 = AIRouter(cfg_cloud, ollama_client=ol_down, cloud_client=cloud_fail)
        res4 = router4.route([{"role": "user", "content": "come ti chiami"}], "come ti chiami")
        self.assertEqual(res4.provider_used, "offline_fallback")
        self.assertIn("motore AI", res4.text)

        # Local intent takes priority over Ollama/Cloud
        res_local = router4.route([{"role": "user", "content": "che ore sono"}], "che ore sono")
        self.assertEqual(res_local.provider_used, "Local Intent")
        self.assertIn("Sono le", res_local.text)

    def test_14_15_16_auth_timeout_and_structured_errors(self) -> None:
        svc = VoiceBridgeService(
            config=self.cfg,
            stt_engine=MockSTTEngine(delay_s=0.15),
            tts_engine=MockTTSEngine(),
        )
        # Force tiny STT timeout to verify timeout handling
        svc.config = BridgeConfig(
            device_token=self.cfg.device_token,
            require_auth=True,
            stt_timeout_s=0.05,
            temp_dir=Path(self.tmp_dir.name),
        )
        client = TestClient(create_app(svc))
        wav_in = _make_sine_wav()

        # Missing & wrong token
        r_no_auth = client.post("/api/v1/voice/process", files={"file": ("a.wav", wav_in, "audio/wav")})
        self.assertEqual(r_no_auth.status_code, 401)
        r_bad_auth = client.post("/api/v1/voice/process", headers=self._headers("wrong"), files={"file": ("a.wav", wav_in, "audio/wav")})
        self.assertEqual(r_bad_auth.status_code, 401)

        # Timeout structured error
        r_to = client.post("/api/v1/voice/process", headers=self._headers(), files={"file": ("a.wav", wav_in, "audio/wav")})
        self.assertEqual(r_to.status_code, 504)
        body = r_to.json()
        self.assertEqual(body["error"]["code"], "STT_TIMEOUT")
        self.assertTrue(body["error"]["recoverable"])

    def test_17_18_19_20_cancel_cleanup_output_wav_and_no_secrets_in_logs(self) -> None:
        svc = VoiceBridgeService(
            config=self.cfg,
            stt_engine=MockSTTEngine(transcript="Ciao Jarvis"),
            tts_engine=MockTTSEngine(sample_rate=22050, duration_s=0.2),
        )

        # 17. Cancellation
        tok = CancellationToken()
        tok.cancel()
        with self.assertRaises(BridgeError) as ctx_cancel:
            svc.process_voice(_make_sine_wav(), cancel_token=tok)
        self.assertEqual(ctx_cancel.exception.code, "REQUEST_CANCELLED")

        # 19. Full pipeline + output WAV 16kHz mono 16-bit
        client = TestClient(create_app(svc))
        r = client.post(
            "/api/v1/voice/process",
            headers=self._headers(),
            files={"file": ("q.wav", _make_sine_wav(), "audio/wav")},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["provider_used"], "offline_fallback")
        out_wav = base64.b64decode(data["audio_wav_base64"])
        with wave.open(io.BytesIO(out_wav), "rb") as wf:
            self.assertEqual(wf.getframerate(), 16000)
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)

        # 18. Temp file retrieval with consume=True + cleanup + traversal check
        r_audio = client.get(f"{data['audio_url']}?consume=true", headers=self._headers())
        self.assertEqual(r_audio.status_code, 200)
        r_audio_gone = client.get(data["audio_url"], headers=self._headers())
        self.assertEqual(r_audio_gone.status_code, 404)
        with self.assertRaises(BridgeError):
            safe_temp_path(Path(self.tmp_dir.name), "../evil.wav")

        # 20. No credentials in logs/diagnostics
        svc.diagnostics.log_event(20, "req_test", f"Authorization: Bearer {self.cfg.device_token} key={self.cfg.cloud_api_key}")
        snap = json.dumps(svc.diagnostics.snapshot())
        self.assertNotIn(self.cfg.device_token, snap)
        self.assertNotIn(self.cfg.cloud_api_key, snap)
        self.assertIn("[REDACTED]", snap)


if __name__ == "__main__":
    unittest.main()
