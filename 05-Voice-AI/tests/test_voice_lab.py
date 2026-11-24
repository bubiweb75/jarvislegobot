"""Automated tests for JARVIS Voice Lab Web UI & HttpOnly/CSRF session (FASE 11.2C)."""

from __future__ import annotations

import base64
import io
import math
from pathlib import Path
import sys
import tempfile
import unittest
import wave

from fastapi.testclient import TestClient

_VOICE_AI_DIR = Path(__file__).resolve().parent.parent
if str(_VOICE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_VOICE_AI_DIR))

from voice_bridge.api import create_app  # noqa: E402
from voice_bridge.audio import encode_wav_mono_16bit  # noqa: E402
from voice_bridge.config import BridgeConfig  # noqa: E402
from voice_bridge.pipeline import VoiceBridgeService  # noqa: E402
from voice_bridge.stt_engine import MockSTTEngine  # noqa: E402
from voice_bridge.tts_engine import MockTTSEngine  # noqa: E402


def _make_wav(sr: int = 16000, dur_s: float = 0.25, amp: int = 3000) -> bytes:
    n = int(round(sr * dur_s))
    samples = [int(round(amp * math.sin(2.0 * math.pi * 440.0 * i / float(sr)))) for i in range(n)]
    return encode_wav_mono_16bit(samples, sr)


class TestVoiceLab(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.token = "voice-lab-local-secret-9876"
        self.cfg = BridgeConfig(
            device_token=self.token,
            require_auth=True,
            max_wav_bytes=512 * 1024,
            max_audio_duration_s=5.0,
            temp_dir=Path(self.tmp_dir.name),
            ollama_enabled=False,
            cloud_enabled=False,
        )

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_01_13_14_web_page_static_assets_no_secrets_no_cdn(self) -> None:
        svc = VoiceBridgeService(config=self.cfg, stt_engine=MockSTTEngine(), tts_engine=MockTTSEngine())
        client = TestClient(create_app(svc))

        r_idx = client.get("/")
        self.assertEqual(r_idx.status_code, 200)
        self.assertIn("JARVIS Voice Lab", r_idx.text)

        r_css = client.get("/static/style.css")
        self.assertEqual(r_css.status_code, 200)

        r_js = client.get("/static/app.js")
        self.assertEqual(r_js.status_code, 200)

        for body in (r_idx.text, r_css.text, r_js.text):
            self.assertNotIn(self.token, body)
            self.assertNotIn("localStorage", body)
            self.assertNotIn("https://", body)
            self.assertNotIn("http://", body)

    def test_02_03_12_httponly_cookie_csrf_and_no_permissive_cors(self) -> None:
        svc = VoiceBridgeService(config=self.cfg, stt_engine=MockSTTEngine(), tts_engine=MockTTSEngine())
        client = TestClient(create_app(svc))

        # Unauthorized before login
        self.assertEqual(client.get("/ready").status_code, 401)
        self.assertEqual(
            client.post("/api/v1/voice/process", files={"file": ("a.wav", _make_wav(), "audio/wav")}).status_code,
            401,
        )

        # Wrong token rejected
        self.assertEqual(client.post("/api/v1/auth/session", json={"token": "bad"}).status_code, 401)

        # Valid login sets HttpOnly SameSite=strict cookie + returns CSRF
        r_login = client.post("/api/v1/auth/session", json={"token": self.token})
        self.assertEqual(r_login.status_code, 200)
        set_cookie = r_login.headers.get("set-cookie", "").lower()
        self.assertIn("httponly", set_cookie)
        self.assertIn("samesite=strict", set_cookie)
        self.assertNotIn("access-control-allow-origin", {k.lower() for k in r_login.headers.keys()})
        csrf = r_login.json()["csrf_token"]
        self.assertTrue(len(csrf) >= 16)

        # Cookie alone works for GET /ready
        self.assertEqual(client.get("/ready").status_code, 200)

        # Mutating POST with cookie MUST include X-CSRF-Token
        r_no_csrf = client.post("/api/v1/voice/process", files={"file": ("a.wav", _make_wav(), "audio/wav")})
        self.assertEqual(r_no_csrf.status_code, 401)

        # With X-CSRF-Token succeeds
        r_ok = client.post(
            "/api/v1/voice/process",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("a.wav", _make_wav(), "audio/wav")},
        )
        self.assertEqual(r_ok.status_code, 200)

        # Logout revokes session
        self.assertEqual(client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf}).status_code, 200)
        self.assertEqual(client.get("/ready").status_code, 401)

    def test_04_05_06_09_15_wav_upload_offline_audio_and_schema(self) -> None:
        svc = VoiceBridgeService(
            config=self.cfg,
            stt_engine=MockSTTEngine(transcript="Ciao Jarvis"),
            tts_engine=MockTTSEngine(sample_rate=16000, duration_s=0.2),
        )
        client = TestClient(create_app(svc))
        csrf = client.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]

        # Invalid WAV rejected
        r_bad = client.post(
            "/api/v1/voice/process",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("bad.wav", b"not-a-wav" * 10, "audio/wav")},
        )
        self.assertEqual(r_bad.status_code, 400)

        # 48 kHz WAV accepted, normalized, offline reply + valid 16 kHz output WAV + full schema
        r_ok = client.post(
            "/api/v1/voice/process",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("q.wav", _make_wav(sr=48000, dur_s=0.3), "audio/wav")},
        )
        self.assertEqual(r_ok.status_code, 200)
        d = r_ok.json()
        for key in (
            "request_id",
            "transcript",
            "reply_text",
            "provider_used",
            "timings",
            "audio_sample_rate",
            "audio_channels",
            "audio_bits",
            "audio_bytes_len",
            "audio_wav_base64",
            "audio_url",
        ):
            self.assertIn(key, d)
        self.assertEqual(d["provider_used"], "offline_fallback")
        self.assertEqual(d["audio_sample_rate"], 16000)

        out_wav = base64.b64decode(d["audio_wav_base64"])
        with wave.open(io.BytesIO(out_wav), "rb") as wf:
            self.assertEqual(wf.getframerate(), 16000)
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)

    def test_07_08_10_11_stt_tts_errors_duration_limit_and_timeout(self) -> None:
        # 10. Duration > max_audio_duration_s (5.0 s)
        svc = VoiceBridgeService(config=self.cfg, stt_engine=MockSTTEngine(), tts_engine=MockTTSEngine())
        client = TestClient(create_app(svc))
        csrf = client.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]
        r_long = client.post(
            "/api/v1/voice/process",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("long.wav", _make_wav(sr=16000, dur_s=5.5), "audio/wav")},
        )
        self.assertEqual(r_long.status_code, 413)
        self.assertEqual(r_long.json()["error"]["code"], "AUDIO_TOO_LONG")

        # 7. STT error
        svc_stt_err = VoiceBridgeService(
            config=self.cfg,
            stt_engine=MockSTTEngine(available=False),
            tts_engine=MockTTSEngine(),
        )
        c_stt = TestClient(create_app(svc_stt_err))
        csrf2 = c_stt.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]
        r_stt = c_stt.post(
            "/api/v1/voice/process",
            headers={"X-CSRF-Token": csrf2},
            files={"file": ("q.wav", _make_wav(), "audio/wav")},
        )
        self.assertEqual(r_stt.status_code, 503)
        self.assertEqual(r_stt.json()["error"]["code"], "STT_UNAVAILABLE")

        # 8. TTS error
        svc_tts_err = VoiceBridgeService(
            config=self.cfg,
            stt_engine=MockSTTEngine(),
            tts_engine=MockTTSEngine(available=False),
        )
        c_tts = TestClient(create_app(svc_tts_err))
        csrf3 = c_tts.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]
        r_tts = c_tts.post(
            "/api/v1/voice/process",
            headers={"X-CSRF-Token": csrf3},
            files={"file": ("q.wav", _make_wav(), "audio/wav")},
        )
        self.assertEqual(r_tts.status_code, 503)
        self.assertEqual(r_tts.json()["error"]["code"], "TTS_UNAVAILABLE")

        # 11. Timeout handling
        cfg_to = BridgeConfig(
            device_token=self.token,
            require_auth=True,
            stt_timeout_s=0.05,
            temp_dir=Path(self.tmp_dir.name),
        )
        svc_to = VoiceBridgeService(
            config=cfg_to,
            stt_engine=MockSTTEngine(delay_s=0.15),
            tts_engine=MockTTSEngine(),
        )
        c_to = TestClient(create_app(svc_to))
        csrf4 = c_to.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]
        r_to = c_to.post(
            "/api/v1/voice/process",
            headers={"X-CSRF-Token": csrf4},
            files={"file": ("q.wav", _make_wav(), "audio/wav")},
        )
        self.assertEqual(r_to.status_code, 504)
        self.assertEqual(r_to.json()["error"]["code"], "STT_TIMEOUT")

    def test_12_audio_diagnostics_and_clipping_metrics(self) -> None:
        from voice_bridge.audio import encode_wav_mono_16bit, validate_and_normalize_wav

        samples = [32767, -32768, 12000, -12000] * 400  # 1600 samples = 0.1 s at 16 kHz
        raw_wav = encode_wav_mono_16bit(samples, 16000)
        val = validate_and_normalize_wav(raw_wav, max_bytes=1_000_000, max_duration_s=5.0)
        self.assertAlmostEqual(val.duration_s, 0.1, places=3)
        self.assertEqual(val.input_sample_rate, 16000)
        self.assertEqual(val.peak_16, 32768)
        self.assertEqual(val.clipped_count, 800)
        self.assertGreater(val.rms_16, 15000)
        self.assertEqual(val.input_wav_bytes_len, len(raw_wav))

    def test_13_local_intents_time_day_date_and_garbled_rejection(self) -> None:
        from datetime import datetime, timezone
        from voice_bridge.local_intents import LocalIntentHandler

        fixed_dt = datetime(2026, 11, 17, 22, 15, 0, tzinfo=timezone.utc)
        handler = LocalIntentHandler(timezone_name="UTC", now_provider=lambda _tz: fixed_dt)

        for phrase in ("Che ore sono?", "Ciao Jarvis, che ore sono?", "Ehi Jarvis, che ora è", "Dimmi l'ora"):
            res = handler.try_handle(phrase)
            self.assertIsNotNone(res, f"Expected match for {phrase!r}")
            self.assertEqual(res.provider_used, "Local Intent")
            self.assertIn("22 e 15", res.reply_text)

        res_day = handler.try_handle("Jarvis, che giorno è oggi?")
        self.assertIsNotNone(res_day)
        self.assertIn("martedì", res_day.reply_text)
        self.assertIn("17 novembre 2026", res_day.reply_text)

        res_date = handler.try_handle("Che data è oggi")
        self.assertIsNotNone(res_date)
        self.assertIn("17 novembre 2026", res_date.reply_text)

        # Garbled STT output from 11.2C.1 must NOT be forced into a time intent
        self.assertIsNone(handler.try_handle("C'è un giarbice che ho riso o no?"))
        self.assertIsNone(handler.try_handle("Raccontami una storia su Marte"))

    def test_14_local_intent_priority_over_ollama_and_pipeline_response(self) -> None:
        svc = VoiceBridgeService(
            config=self.cfg,
            stt_engine=MockSTTEngine(transcript="Ciao Jarvis, che ore sono?"),
            tts_engine=MockTTSEngine(),
        )
        client = TestClient(create_app(svc))
        csrf = client.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]
        resp = client.post(
            "/api/v1/voice/process?include_base64=true",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("ora.wav", _make_wav(sr=48000, dur_s=0.4), "audio/wav")},
        )
        self.assertEqual(resp.status_code, 200)
        d = resp.json()
        self.assertEqual(d["provider_used"], "Local Intent")
        self.assertFalse(d["fallback_used"])
        self.assertRegex(d["reply_text"], r"Sono le \d{1,2} e \d{2}")
        self.assertEqual(d["input_sample_rate"], 48000)
        self.assertAlmostEqual(d["input_duration_s"], 0.4, places=2)
        self.assertGreater(d["input_rms_16"], 0)
        self.assertGreater(d["input_peak_16"], 0)
        self.assertEqual(d["input_clipped_count"], 0)
        self.assertGreater(d["input_wav_bytes_len"], 44)
        self.assertTrue(d["timezone_note"])

    def test_15_stt_compare_diag_endpoint_and_auth_and_flag(self) -> None:
        # 1. Disabled diag -> 403
        cfg_no_diag = BridgeConfig(
            device_token=self.token,
            require_auth=True,
            enable_stt_diag=False,
            temp_dir=Path(self.tmp_dir.name),
        )
        svc_off = VoiceBridgeService(config=cfg_no_diag, stt_engine=MockSTTEngine(), tts_engine=MockTTSEngine())
        c_off = TestClient(create_app(svc_off))
        csrf_off = c_off.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]
        self.assertEqual(c_off.post("/api/v1/stt/compare", headers={"X-CSRF-Token": csrf_off}).status_code, 403)

        # 2. Enabled diag: 404 before any audio, 200 with 5 presets A..E after /voice/process
        cfg_diag = BridgeConfig(
            device_token=self.token,
            require_auth=True,
            enable_stt_diag=True,
            temp_dir=Path(self.tmp_dir.name),
        )
        svc = VoiceBridgeService(
            config=cfg_diag,
            stt_engine=MockSTTEngine(transcript="Ciao Jarvis"),
            tts_engine=MockTTSEngine(),
        )
        c = TestClient(create_app(svc))
        self.assertEqual(c.post("/api/v1/stt/compare").status_code, 401)
        csrf = c.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]
        self.assertEqual(c.post("/api/v1/stt/compare", headers={"X-CSRF-Token": csrf}).status_code, 404)

        r_proc = c.post(
            "/api/v1/voice/process",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("q.wav", _make_wav(), "audio/wav")},
        )
        self.assertEqual(r_proc.status_code, 200)

        r_cmp = c.post("/api/v1/stt/compare", headers={"X-CSRF-Token": csrf})
        self.assertEqual(r_cmp.status_code, 200)
        comps = r_cmp.json()["comparisons"]
        self.assertEqual([x["id"] for x in comps], ["A", "B", "C", "D", "E"])
        self.assertTrue(all(x["transcript"] == "Ciao Jarvis" for x in comps))

    def test_16_voice_lab_ui_contains_offline_audio_context_and_diag_fields(self) -> None:
        svc = VoiceBridgeService(config=self.cfg, stt_engine=MockSTTEngine(), tts_engine=MockTTSEngine())
        client = TestClient(create_app(svc))
        js = client.get("/static/app.js").text
        html = client.get("/").text
        self.assertIn("OfflineAudioContext", js)
        self.assertNotIn("resampleLinear", js)
        self.assertIn("diag-rms-peak", html)
        self.assertIn("diag-clipping", html)
        self.assertIn("btn-compare-stt", html)

    def test_17_original_audio_player_uses_exact_uploaded_wav_and_configurable_mic_options(self) -> None:
        svc = VoiceBridgeService(config=self.cfg, stt_engine=MockSTTEngine(), tts_engine=MockTTSEngine())
        client = TestClient(create_app(svc))
        html = client.get("/").text
        js = client.get("/static/app.js").text

        self.assertIn("Ascolta registrazione originale", html)
        self.assertIn('id="original-audio-player"', html)
        self.assertIn('id="opt-echo"', html)
        self.assertIn('id="opt-noise"', html)
        self.assertIn('id="opt-agc"', html)

        # Exact same wavBlob is used for both browser playback and FormData upload
        self.assertIn("currentOriginalAudioUrl = URL.createObjectURL(wavBlob);", js)
        self.assertIn("el.originalAudioPlayer.src = currentOriginalAudioUrl;", js)
        self.assertIn('form.append("file", wavBlob, "voice_lab.wav");', js)
        self.assertIn("URL.revokeObjectURL(currentOriginalAudioUrl);", js)

        # Configurable mic processing options (default checked=true, not blindly disabled)
        self.assertIn("echoCancellation: el.optEcho ? el.optEcho.checked : true", js)
        self.assertIn("noiseSuppression: el.optNoise ? el.optNoise.checked : true", js)
        self.assertIn("autoGainControl: el.optAgc ? el.optAgc.checked : true", js)

        # OfflineAudioContext duration/pitch parity
        self.assertIn("const targetLen = Math.max(1, Math.round(floatSamples.length * (dstRate / srcRate)));", js)
        self.assertIn("const buffer = offline.createBuffer(1, floatSamples.length, srcRate);", js)

    def test_18_safe_gain_anti_clipping_wav_integrity_and_silence(self) -> None:
        from voice_bridge.audio import apply_safe_gain_wav, encode_wav_mono_16bit
        from voice_bridge.schemas import BridgeError

        # 1. Low-level audio (peak=4000) -> 1x, 2x, 3x apply exact gain with 0 clipping and identical duration/SR
        low_samples = [4000, -4000, 2000, -2000] * 400  # 0.1 s at 16 kHz
        low_wav = encode_wav_mono_16bit(low_samples, 16000)

        g1 = apply_safe_gain_wav(low_wav, 1.0)
        g2 = apply_safe_gain_wav(low_wav, 2.0)
        g3 = apply_safe_gain_wav(low_wav, 3.0)

        self.assertAlmostEqual(g1.effective_gain, 1.0, places=3)
        self.assertAlmostEqual(g2.effective_gain, 2.0, places=3)
        self.assertAlmostEqual(g3.effective_gain, 3.0, places=3)
        self.assertEqual(g1.clipped_count, 0)
        self.assertEqual(g2.clipped_count, 0)
        self.assertEqual(g3.clipped_count, 0)
        self.assertEqual(g1.sample_rate, 16000)
        self.assertEqual(g2.sample_rate, 16000)
        self.assertEqual(g3.sample_rate, 16000)
        self.assertEqual(g1.num_frames, 1600)
        self.assertEqual(g2.num_frames, 1600)
        self.assertEqual(g3.num_frames, 1600)
        self.assertGreater(g2.rms_16, g1.rms_16)
        self.assertGreater(g3.rms_16, g2.rms_16)

        with wave.open(io.BytesIO(g3.wav_bytes), "rb") as wf:
            self.assertEqual(wf.getframerate(), 16000)
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(wf.getnframes(), 1600)

        # 2. High-peak audio (peak=20000) with requested 3x -> effective gain automatically reduced below 0.95*32767
        loud_samples = [20000, -20000, 5000, -5000] * 400
        loud_wav = encode_wav_mono_16bit(loud_samples, 16000)
        g_clamped = apply_safe_gain_wav(loud_wav, 3.0, safety_headroom=0.95)
        self.assertLess(g_clamped.effective_gain, 1.6)
        self.assertLessEqual(g_clamped.peak_16, int(32767 * 0.95) + 1)
        self.assertEqual(g_clamped.clipped_count, 0)

        # 3. Silence -> 0 RMS, 0 peak, 0 clipping
        silent_wav = encode_wav_mono_16bit([0] * 1600, 16000)
        g_sil = apply_safe_gain_wav(silent_wav, 3.0)
        self.assertEqual(g_sil.rms_16, 0)
        self.assertEqual(g_sil.peak_16, 0)
        self.assertEqual(g_sil.clipped_count, 0)

        # 4. Invalid gain -> BridgeError
        with self.assertRaises(BridgeError):
            apply_safe_gain_wav(low_wav, 0.0)

    def test_19_gain_comparison_sequential_stt_and_ui_controls(self) -> None:
        from voice_bridge.audio import apply_safe_gain_wav, encode_wav_mono_16bit

        svc = VoiceBridgeService(
            config=self.cfg,
            stt_engine=MockSTTEngine(transcript="Ciao Jarvis, che ore sono?"),
            tts_engine=MockTTSEngine(),
        )
        client = TestClient(create_app(svc))
        html = client.get("/").text
        js = client.get("/static/app.js").text

        self.assertIn('id="gain-select"', html)
        self.assertIn('<option value="1" selected>Originale (1×)</option>', html)
        self.assertIn('id="btn-compare-gain"', html)
        self.assertIn('id="diag-gain"', html)
        self.assertIn("aumenta anche il rumore di fondo", html)
        self.assertIn("applySafeGain", js)
        self.assertIn("for (const reqGain of [1, 2, 3])", js)

        # Sequential /api/v1/stt check on 1x, 2x, 3x of the same low-level WAV
        csrf = client.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]
        base_wav = _make_wav(sr=16000, dur_s=0.3, amp=2500)
        rms_list = []
        for g in (1.0, 2.0, 3.0):
            gained = apply_safe_gain_wav(base_wav, g)
            resp = client.post(
                "/api/v1/stt",
                headers={"X-CSRF-Token": csrf},
                files={"file": (f"g{int(g)}.wav", gained.wav_bytes, "audio/wav")},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["transcript"], "Ciao Jarvis, che ore sono?")
            self.assertEqual(data["input_clipped_count"], 0)
            rms_list.append(data["input_rms_16"])
        self.assertLess(rms_list[0], rms_list[1])
        self.assertLess(rms_list[1], rms_list[2])

        # Silence remains rejected with 422 SILENT_AUDIO
        silent_wav = encode_wav_mono_16bit([0] * 3200, 16000)
        r_sil = client.post(
            "/api/v1/stt",
            headers={"X-CSRF-Token": csrf},
            files={"file": ("sil.wav", silent_wav, "audio/wav")},
        )
        self.assertEqual(r_sil.status_code, 422)
        self.assertEqual(r_sil.json()["error"]["code"], "SILENT_AUDIO")

    def test_20_small_model_cached_and_wer_calculation(self) -> None:
        from stt_providers import FasterWhisperSTTProvider
        from voice_bridge.stt_engine import compute_wer, validate_compare_models

        ok, detail = FasterWhisperSTTProvider(model_size="small", allow_download=False).is_available()
        self.assertTrue(ok, f"Whisper small non disponibile in cache locale: {detail}")

        self.assertEqual(validate_compare_models(["base", "small"]), ("base", "small"))
        with self.assertRaises(Exception):
            validate_compare_models(["medium"])

        self.assertEqual(compute_wer("Ciao Jarvis, che ore sono?", "ciao jarvis che ore sono"), 0.0)
        self.assertIsNone(compute_wer("", "ciao"))
        wer_bad = compute_wer("Ciao Jarvis, che ore sono?", "Ciao, c'è Armis, ghiore se o no?")
        self.assertIsNotNone(wer_bad)
        self.assertGreater(wer_bad, 0.5)

    def test_21_compare_models_endpoint_security_limits_errors_and_default_preserved(self) -> None:
        wav_in = _make_wav(sr=16000, dur_s=0.35, amp=2500)
        stt = MockSTTEngine(
            model_transcripts={
                "base": "Ciao c'è Armis ghiore se o no",
                "small": "Ciao Jarvis, che ore sono?",
            }
        )
        svc = VoiceBridgeService(config=self.cfg, stt_engine=stt, tts_engine=MockTTSEngine())
        client = TestClient(create_app(svc))

        # Auth & CSRF
        self.assertEqual(client.post("/api/v1/stt/compare-models").status_code, 401)
        csrf = client.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]
        self.assertIn(client.post("/api/v1/stt/compare-models").status_code, (401, 403))

        # Reject unauthorized models (medium, large, path traversal)
        for bad_models in ("medium", "base,large", "../small", "tiny"):
            r_bad = client.post(
                "/api/v1/stt/compare-models",
                headers={"X-CSRF-Token": csrf},
                data={"models": bad_models, "reference_text": "Ciao Jarvis, che ore sono?"},
                files={"file": ("orig.wav", wav_in, "audio/wav")},
            )
            self.assertEqual(r_bad.status_code, 400)
            self.assertEqual(r_bad.json()["error"]["code"], "INVALID_STT_MODEL")

        # Size & duration limits
        r_long = client.post(
            "/api/v1/stt/compare-models",
            headers={"X-CSRF-Token": csrf},
            data={"models": "base,small"},
            files={"file": ("long.wav", _make_wav(sr=16000, dur_s=5.5), "audio/wav")},
        )
        self.assertEqual(r_long.status_code, 413)
        self.assertEqual(r_long.json()["error"]["code"], "AUDIO_TOO_LONG")

        r_big = client.post(
            "/api/v1/stt/compare-models",
            headers={"X-CSRF-Token": csrf},
            data={"models": "base,small"},
            files={"file": ("big.wav", b"RIFF" + b"\x00" * (self.cfg.max_wav_bytes + 10), "audio/wav")},
        )
        self.assertEqual(r_big.status_code, 413)
        self.assertEqual(r_big.json()["error"]["code"], "PAYLOAD_TOO_LARGE")

        # Valid sequential comparison on identical WAV bytes
        r_ok = client.post(
            "/api/v1/stt/compare-models",
            headers={"X-CSRF-Token": csrf},
            data={"models": "base,small", "reference_text": "Ciao Jarvis, che ore sono?"},
            files={"file": ("orig.wav", wav_in, "audio/wav")},
        )
        self.assertEqual(r_ok.status_code, 200)
        d = r_ok.json()
        self.assertEqual(d["default_model"], "base")
        self.assertEqual(svc.config.stt_model, "base")
        self.assertEqual([c["model"] for c in d["comparisons"]], ["base", "small"])
        self.assertGreater(d["comparisons"][0]["wer"], 0.5)
        self.assertEqual(d["comparisons"][1]["wer"], 0.0)
        self.assertEqual([m for m, _ in stt.recorded_calls], ["base", "small"])
        self.assertEqual(stt.recorded_calls[0][1], stt.recorded_calls[1][1])

        # Missing model & STT failure handled per-model without crashing
        stt_err = MockSTTEngine(
            transcript="Ciao",
            missing_models=("small",),
        )
        svc_err = VoiceBridgeService(config=self.cfg, stt_engine=stt_err, tts_engine=MockTTSEngine())
        c_err = TestClient(create_app(svc_err))
        csrf_err = c_err.post("/api/v1/auth/session", json={"token": self.token}).json()["csrf_token"]
        r_miss = c_err.post(
            "/api/v1/stt/compare-models",
            headers={"X-CSRF-Token": csrf_err},
            data={"models": "base,small"},
            files={"file": ("orig.wav", wav_in, "audio/wav")},
        )
        self.assertEqual(r_miss.status_code, 200)
        comps = r_miss.json()["comparisons"]
        self.assertEqual(comps[0]["error"], "")
        self.assertIn("STT_UNAVAILABLE", comps[1]["error"])

        # Timeout & STT_FAILED in compare_models
        stt_to = MockSTTEngine(delay_s=0.1, fail_models={"base": "errore simulato"})
        res_to = stt_to.compare_models(wav_in, models=("base", "small"), timeout_s=0.05)
        self.assertIn("STT_FAILED", res_to[0]["error"])
        self.assertIn("STT_TIMEOUT", res_to[1]["error"])

        # UI controls
        html = client.get("/").text
        js = client.get("/static/app.js").text
        self.assertIn("Confronta Whisper Base / Small", html)
        self.assertIn('id="btn-compare-models"', html)
        self.assertIn('id="stt-ref-input"', html)
        self.assertIn("/api/v1/stt/compare-models", js)

    def test_22_local_intent_paraphrases_offline_order_and_safe_diagnostics(self) -> None:
        from datetime import datetime, timezone
        import logging
        from voice_bridge.ai_router import AIRouter
        from voice_bridge.local_intents import LocalIntentHandler
        from voice_bridge.offline_fallback import OfflineFallbackProvider

        fixed_dt = datetime(2026, 11, 18, 19, 5, 0, tzinfo=timezone.utc)
        handler = LocalIntentHandler(timezone_name="UTC", now_provider=lambda _tz: fixed_dt)

        time_phrases = (
            "Che ore sono?",
            "Ciao Jarvis, che ore sono?",
            "Ciao, che ore sono?",
            "Mi dici che ore sono?",
            "Dimmi che ore sono",
            "Che ore sono adesso?",
            "Mi dici l'ora per favore?",
        )
        for p in time_phrases:
            res = handler.try_handle(p)
            self.assertIsNotNone(res, f"Expected time intent for {p!r}")
            self.assertEqual(res.provider_used, "Local Intent")
            self.assertIn("19 e 05", res.reply_text)

        res_day = handler.try_handle("Che giorno è oggi?")
        self.assertIsNotNone(res_day)
        self.assertIn("mercoledì 18 novembre 2026", res_day.reply_text)

        res_date = handler.try_handle("Qual è la data di oggi?")
        self.assertIsNotNone(res_date)
        self.assertIn("18 novembre 2026", res_date.reply_text)

        # Generic & negative cases must NOT match LocalIntentHandler
        for neg in (
            "Raccontami una barzelletta",
            "Che tempo fa oggi?",
            "A che ora parte il treno?",
            "Ciao, c'è Armis, ghiore se o no?",
            "Come stai?",
        ):
            self.assertIsNone(handler.try_handle(neg), f"Unexpected local intent for {neg!r}")

        # OfflineFallbackProvider must evaluate time before greetings
        fb = OfflineFallbackProvider()
        reply, prov = fb.generate_reply("Ciao, che ore sono?")
        self.assertEqual(prov, "offline_fallback")
        self.assertIn("Sono le", reply)

        # Generic question falls through AIRouter to offline_fallback without inventing answers
        router = AIRouter(self.cfg)
        gen = router.route([{"role": "user", "content": "Spiegami i buchi neri"}], "Spiegami i buchi neri")
        self.assertEqual(gen.provider_used, "offline_fallback")
        self.assertIn("motore AI", gen.text)

        # Diagnostics: no duplicate handlers across multiple instances & no transcript in log event
        svc1 = VoiceBridgeService(config=self.cfg, stt_engine=MockSTTEngine(transcript="Segreto utente"), tts_engine=MockTTSEngine())
        svc2 = VoiceBridgeService(config=self.cfg, stt_engine=MockSTTEngine(), tts_engine=MockTTSEngine())
        logger = logging.getLogger("jarvis.voice_bridge")
        self.assertEqual(len(logger.handlers), 1)
        svc1.process_voice(_make_wav(), include_base64_audio=False)
        last_msg = svc1.diagnostics.snapshot()["recent_events"][-1]["message"]
        self.assertIn("dur=", last_msg)
        self.assertIn("rms=", last_msg)
        self.assertIn("peak=", last_msg)
        self.assertNotIn("Segreto utente", last_msg)

    def test_23_stt_diag_text_flag_default_off_and_opt_in_bounded(self) -> None:
        long_text = "ParolaSegreta " * 30  # > 200 chars
        cfg_default = BridgeConfig(
            device_token=self.token,
            require_auth=True,
            temp_dir=Path(self.tmp_dir.name),
        )
        self.assertFalse(cfg_default.log_stt_diag_text)
        svc_off = VoiceBridgeService(
            config=cfg_default,
            stt_engine=MockSTTEngine(transcript=long_text),
            tts_engine=MockTTSEngine(),
        )
        svc_off.process_voice(_make_wav(), include_base64_audio=False)
        events_off = [str(e["message"]) for e in svc_off.diagnostics.snapshot()["recent_events"]]
        self.assertFalse(any("ParolaSegreta" in m for m in events_off))

        cfg_on = BridgeConfig(
            device_token=self.token,
            require_auth=True,
            log_stt_diag_text=True,
            temp_dir=Path(self.tmp_dir.name),
        )
        svc_on = VoiceBridgeService(
            config=cfg_on,
            stt_engine=MockSTTEngine(transcript=long_text),
            tts_engine=MockTTSEngine(),
        )
        svc_on.process_voice(_make_wav(), include_base64_audio=False)
        events_on = [str(e["message"]) for e in svc_on.diagnostics.snapshot()["recent_events"]]
        diag_lines = [m for m in events_on if m.startswith("STT diag text=")]
        self.assertEqual(len(diag_lines), 1)
        self.assertLessEqual(len(diag_lines[0]), 220)

    def test_24_local_intent_che_ora_sono_and_no_false_positives(self) -> None:
        from datetime import datetime, timezone
        from voice_bridge.local_intents import LocalIntentHandler

        fixed_dt = datetime(2026, 11, 18, 19, 15, 0, tzinfo=timezone.utc)
        handler = LocalIntentHandler(timezone_name="UTC", now_provider=lambda _tz: fixed_dt)

        for phrase in ("Ciao Jarvis che ora sono", "Che ora sono", "Mi dici che ora sono?"):
            res = handler.try_handle(phrase)
            self.assertIsNotNone(res, f"Expected time intent for {phrase!r}")
            self.assertEqual(res.intent_id, "time")
            self.assertEqual(res.provider_used, "Local Intent")
            self.assertIn("19 e 15", res.reply_text)

        for neg in ("Medici che è rsono", "Che ora parte il treno?", "Ora ti spiego tutto", "Qualcuno è in casa?"):
            self.assertIsNone(handler.try_handle(neg), f"Unexpected match for {neg!r}")


if __name__ == "__main__":
    unittest.main()
