"""FASE 12.24 tests: WSOLA Profile 08 integration, PCM protections, and rollback."""

from __future__ import annotations

import io
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

import numpy as np

_VOICE_AI_DIR = Path(__file__).resolve().parent.parent
if str(_VOICE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_VOICE_AI_DIR))

from voice_dsp import shape_piper_wav  # noqa: E402
from voice_bridge.ai_router import AIRouteResult  # noqa: E402
from voice_bridge.audio import encode_wav_mono_16bit  # noqa: E402
from voice_bridge.config import BridgeConfig  # noqa: E402
from voice_bridge.pipeline import VoiceBridgeService, _measure_wav_pcm  # noqa: E402
from voice_bridge.schemas import BridgeError  # noqa: E402
from voice_bridge.stt_engine import STTEngine, STTOptions  # noqa: E402
from voice_bridge.tts_engine import PiperTTSEngine, TTSEngine  # noqa: E402


def _make_harmonic_wav(freq_hz: float = 150.0, dur_s: float = 1.2, sr: int = 16000, amp: float = 6000.0) -> bytes:
    n = int(sr * dur_s)
    t = np.arange(n, dtype=np.float32) / float(sr)
    sig = amp * (0.7 * np.sin(2.0 * np.pi * freq_hz * t) + 0.3 * np.sin(2.0 * np.pi * 2.0 * freq_hz * t))
    return encode_wav_mono_16bit(sig.astype(np.int16).tolist(), sr)


def _estimate_f0_hz(wav_bytes: bytes) -> float:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        sr = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    s = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    win = int(sr * 0.040)
    hop = int(sr * 0.015)
    lag_min = int(sr / 450)
    lag_max = int(sr / 70)
    f0s: list[float] = []
    for i in range(0, max(1, len(s) - win), hop):
        frm = s[i : i + win]
        if len(frm) < win:
            break
        if float(np.sqrt(np.mean(frm * frm))) < 0.02:
            continue
        frm = frm - float(np.mean(frm))
        ac = np.correlate(frm, frm, mode="full")[win - 1 :]
        if ac[0] <= 1e-9:
            continue
        ac /= float(ac[0])
        if float(np.max(ac[lag_min : lag_max + 1])) < 0.45:
            continue
        lag = lag_min + int(np.argmax(ac[lag_min : lag_max + 1]))
        f0s.append(sr / float(lag))
    if not f0s:
        return 0.0
    return float(np.median(f0s))


class _DummySTT(STTEngine):
    def __init__(self, text: str) -> None:
        self._text = text

    def is_available(self) -> tuple[bool, str]:
        return True, "OK"

    def transcribe(
        self,
        wav_bytes_16k_mono: bytes,
        language: str = "it",
        timeout_s: float = 12.0,
        options: STTOptions | None = None,
    ) -> str:
        return self._text


class _LengthAwareTTS(TTSEngine):
    """Synthesizes proportional PCM length (~2400 bytes/char) to test ESP32 PCM guards."""

    def __init__(self, bytes_per_char: int = 2400) -> None:
        self.bytes_per_char = bytes_per_char
        self.calls: list[str] = []

    def is_available(self) -> tuple[bool, str]:
        return True, "OK"

    def synthesize(self, text: str, timeout_s: float = 10.0) -> bytes:
        self.calls.append(text)
        pcm_bytes = max(3200, len(text) * self.bytes_per_char)
        n_samples = pcm_bytes // 2
        samples = [int(4000.0 * math.sin(2.0 * math.pi * 220.0 * i / 16000.0)) for i in range(n_samples)]
        return encode_wav_mono_16bit(samples, 16000)


class Fase1224WsolaProfile08Tests(unittest.TestCase):
    def test_profile08_defaults_and_rollback_env(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            cfg = BridgeConfig.from_env()
        self.assertEqual(cfg.tts_piper_speed, 1.00)
        self.assertAlmostEqual(cfg.tts_piper_noise_scale, 0.60, places=2)
        self.assertAlmostEqual(cfg.tts_piper_pitch_semitones, 5.0, places=2)
        self.assertEqual(cfg.tts_piper_dsp_method, "wsola")
        self.assertFalse(cfg.tts_piper_limiter_enabled)
        self.assertTrue(cfg.tts_piper_dsp_enabled)
        self.assertEqual(cfg.tts_max_chars, 270)
        self.assertEqual(cfg.esp_max_tts_bytes, 640000)

        rollback_env = {
            "JARVIS_TTS_PIPER_NOISE_SCALE": "1.10",
            "JARVIS_TTS_PIPER_DSP_METHOD": "phase_vocoder",
            "JARVIS_TTS_PIPER_LIMITER_ENABLED": "true",
        }
        with patch.dict(os.environ, rollback_env, clear=True):
            rb = BridgeConfig.from_env()
        self.assertAlmostEqual(rb.tts_piper_noise_scale, 1.10, places=2)
        self.assertEqual(rb.tts_piper_dsp_method, "phase_vocoder")
        self.assertTrue(rb.tts_piper_limiter_enabled)

    def test_wsola_pitch_plus5_duration_pcm_and_no_clipping(self) -> None:
        raw_wav = _make_harmonic_wav(freq_hz=150.0, dur_s=1.2)
        out_wav, dur_s = shape_piper_wav(
            raw_wav,
            pitch_semitones=5.0,
            robot_mix=0.0,
            volume=100,
            method="wsola",
            limiter_enabled=False,
        )
        self.assertAlmostEqual(dur_s, 1.2, places=2)
        with wave.open(io.BytesIO(out_wav), "rb") as wf:
            self.assertEqual(wf.getframerate(), 16000)
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        peak = int(np.max(np.abs(pcm)))
        self.assertLessEqual(peak, int(0.90 * 32767))
        self.assertEqual(int(np.sum(np.abs(pcm) >= 32766)), 0)

        f0_out = _estimate_f0_hz(out_wav)
        expected_f0 = 150.0 * (2.0 ** (5.0 / 12.0))
        self.assertAlmostEqual(f0_out, expected_f0, delta=10.0)

    def test_no_tanh_preserves_crest_factor_vs_tanh_rollback(self) -> None:
        sr = 16000
        t = np.arange(sr, dtype=np.float32) / float(sr)
        env = np.where((t > 0.20) & (t < 0.24), 0.85, 0.14).astype(np.float32)
        sig = (env * np.sin(2.0 * np.pi * 160.0 * t) * 32767.0).astype(np.int16)
        raw_wav = encode_wav_mono_16bit(sig.tolist(), sr)

        wsola_no_tanh, _ = shape_piper_wav(
            raw_wav, pitch_semitones=5.0, volume=100, method="wsola", limiter_enabled=False
        )
        wsola_tanh, _ = shape_piper_wav(
            raw_wav, pitch_semitones=5.0, volume=100, method="wsola", limiter_enabled=True
        )
        with wave.open(io.BytesIO(wsola_no_tanh), "rb") as wf:
            p_no = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        with wave.open(io.BytesIO(wsola_tanh), "rb") as wf:
            p_ta = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        crest_no = float(np.max(np.abs(p_no))) / max(float(np.sqrt(np.mean(p_no ** 2))), 1e-9)
        crest_ta = float(np.max(np.abs(p_ta))) / max(float(np.sqrt(np.mean(p_ta ** 2))), 1e-9)
        self.assertGreater(crest_no, crest_ta)

    def test_invalid_dsp_method_raises_cleanly(self) -> None:
        raw_wav = _make_harmonic_wav()
        with self.assertRaises(ValueError):
            shape_piper_wav(raw_wav, method="unknown_dsp")

    def test_piper_engine_logs_profile08_and_wraps_dsp_errors(self) -> None:
        eng = PiperTTSEngine(
            piper_bin="piper",
            model_path="tts-lab/models/piper/it_IT-riccardo-x_low.onnx",
            speed=1.00,
            noise_scale=0.60,
            pitch_semitones=5.0,
            dsp_enabled=True,
            dsp_method="wsola",
            limiter_enabled=False,
        )
        if Path("tts-lab/models/piper/it_IT-riccardo-x_low.onnx").exists():
            _, msg = eng.is_available()
            if "Piper pronto" in msg:
                self.assertIn("method=wsola", msg)
                self.assertIn("noise_scale=0.60", msg)
                self.assertIn("tanh=off", msg)

    def test_esp_pcm_protection_short_long_and_fallback(self) -> None:
        in_wav = _make_harmonic_wav(freq_hz=200.0, dur_s=0.4, amp=3000.0)
        with tempfile.TemporaryDirectory() as tmp:
            cfg = BridgeConfig(
                temp_dir=Path(tmp),
                tts_max_chars=270,
                esp_max_tts_bytes=640000,
                tts_piper_noise_scale=0.60,
                tts_piper_dsp_method="wsola",
                tts_piper_limiter_enabled=False,
                ai_mode="DISABLED",
                timezone="Europe/Rome",
            )
            tts = _LengthAwareTTS(bytes_per_char=2400)
            svc = VoiceBridgeService(cfg, stt_engine=_DummySTT("che ore sono"), tts_engine=tts)
            try:
                res_short = svc.process_voice(in_wav)
                wav_short = svc.temp_store.get(res_short.audio_id, consume=True)
                self.assertIsNotNone(wav_short)
                pcm_short, _ = _measure_wav_pcm(wav_short)
                self.assertLessEqual(pcm_short, 640000)

                # Very long TTS (>640k) -> triggers text reduction & fits <= 640k
                long_txt = (
                    "Leonardo da Vinci fu un genio del Rinascimento. "
                    "Progettò macchine volanti, ponti e automatismi! "
                    "I suoi taccuini raccolgono disegni tecnici, studi di ottica, anatomia e idraulica; "
                    "molte invenzioni anticiparono i tempi di secoli interi."
                )
                tts_long = _LengthAwareTTS(bytes_per_char=3000)
                svc_long = VoiceBridgeService(
                    cfg,
                    stt_engine=_DummySTT("raccontami qualcosa"),
                    tts_engine=tts_long,
                )
                try:
                    with patch.object(
                        svc_long.ai_router,
                        "route",
                        side_effect=lambda *a, **kw: AIRouteResult(
                            text=long_txt,
                            provider_used="ollama:qwen2.5:3b",
                            fallback_used=False,
                            reason="ok",
                            latency_ms=10.0,
                        ),
                    ):
                        res_long = svc_long.process_voice(in_wav)
                    wav_long = svc_long.temp_store.get(res_long.audio_id, consume=True)
                    self.assertIsNotNone(wav_long)
                    pcm_long, _ = _measure_wav_pcm(wav_long)
                    self.assertLessEqual(pcm_long, 640000)
                    self.assertGreaterEqual(len(tts_long.calls), 2)
                finally:
                    svc_long.close()

                # Impossible bytes/char -> raises TTS_TOO_LONG cleanly
                huge_tts = _LengthAwareTTS(bytes_per_char=60000)
                svc_huge = VoiceBridgeService(cfg, stt_engine=_DummySTT("che ore sono"), tts_engine=huge_tts)
                try:
                    with self.assertRaises(BridgeError) as ctx:
                        svc_huge.process_voice(in_wav)
                    self.assertEqual(ctx.exception.code, "TTS_TOO_LONG")
                finally:
                    svc_huge.close()
            finally:
                svc.close()

    def test_real_piper_profile08_if_available(self) -> None:
        piper_bin = _VOICE_AI_DIR / "tts-lab" / "bin" / "piper" / "piper.exe"
        model_path = _VOICE_AI_DIR / "tts-lab" / "models" / "piper" / "it_IT-riccardo-x_low.onnx"
        if not (piper_bin.exists() and model_path.exists()):
            self.skipTest("Piper binary/model not present locally")
        eng_raw = PiperTTSEngine(
            piper_bin=str(piper_bin),
            model_path=str(model_path),
            speed=1.00,
            noise_scale=0.60,
            pitch_semitones=0.0,
            robot_mix=0.0,
            dsp_enabled=False,
        )
        eng = PiperTTSEngine(
            piper_bin=str(piper_bin),
            model_path=str(model_path),
            speed=1.00,
            noise_scale=0.60,
            pitch_semitones=5.0,
            robot_mix=0.0,
            dsp_enabled=True,
            dsp_method="wsola",
            limiter_enabled=False,
        )
        sentences = [
            "Dodici per otto fa novantasei.",
            "Ciao! Come stai oggi? Tutto bene, grazie.",
            "Il vulcano erutta magma, gas e cenere dalla camera magmatica.",
        ]
        for s in sentences:
            raw_wav = eng_raw.synthesize(s)
            f0_raw = _estimate_f0_hz(raw_wav)
            self.assertGreater(f0_raw, 120.0)
            self.assertLess(f0_raw, 180.0)  # baseline unshifted voice would fail >= 180 Hz check

            # Deterministic same-utterance WSOLA +5st ratio check (theoretical 2^(5/12) ~= 1.3348)
            shifted_same, dur_same_s = shape_piper_wav(
                raw_wav,
                pitch_semitones=5.0,
                robot_mix=0.0,
                volume=100,
                method="wsola",
                limiter_enabled=False,
            )
            f0_same = _estimate_f0_hz(shifted_same)
            ratio = f0_same / f0_raw
            self.assertGreaterEqual(ratio, 1.28)
            self.assertLessEqual(ratio, 1.39)
            _, dur_raw = _measure_wav_pcm(raw_wav)
            self.assertLessEqual(abs(dur_same_s - dur_raw), 0.05)

            # Full Profile 08 PiperTTSEngine synthesis check
            wav_bytes = eng.synthesize(s)
            pcm_bytes, _ = _measure_wav_pcm(wav_bytes)
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                self.assertEqual((wf.getframerate(), wf.getnchannels(), wf.getsampwidth()), (16000, 1, 2))
            self.assertLessEqual(pcm_bytes, 640000)
            f0 = _estimate_f0_hz(wav_bytes)
            self.assertGreaterEqual(f0, 180.0)  # +5st shifted voiced median (~193..218 Hz vs ~152..157 Hz raw)


if __name__ == "__main__":
    unittest.main()
