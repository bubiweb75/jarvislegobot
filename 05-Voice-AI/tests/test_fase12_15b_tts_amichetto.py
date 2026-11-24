"""FASE 12.15B tests: JARVIS Amichetto Piper DSP parameters & TTS_TOO_LONG PCM protection."""

from __future__ import annotations

import io
import math
from pathlib import Path
import sys
import tempfile
import unittest
import wave

import numpy as np

_VOICE_AI_DIR = Path(__file__).resolve().parent.parent
if str(_VOICE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_VOICE_AI_DIR))

from voice_bridge.audio import encode_wav_mono_16bit  # noqa: E402
from voice_bridge.config import BridgeConfig  # noqa: E402
from voice_bridge.pipeline import VoiceBridgeService, _measure_wav_pcm, _reduce_tts_text_for_limit  # noqa: E402
from voice_bridge.schemas import BridgeError  # noqa: E402
from voice_bridge.stt_engine import STTEngine, STTOptions  # noqa: E402
from voice_bridge.tts_engine import PiperTTSEngine, TTSEngine  # noqa: E402


def _make_wav_bytes_for_pcm_len(pcm_bytes: int, sr: int = 16000) -> bytes:
    n_samples = max(1, pcm_bytes // 2)
    samples = [int(1000.0 * math.sin(2.0 * math.pi * 440.0 * i / sr)) for i in range(n_samples)]
    return encode_wav_mono_16bit(samples, sr)


class _FixedSTT(STTEngine):
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


class _LengthScaledTTS(TTSEngine):
    """Simulates TTS where PCM byte length is proportional to text length (e.g., 2800 B/char)."""

    def __init__(self, bytes_per_char: int = 2800, force_empty: bool = False, always_oversize: bool = False) -> None:
        self.bytes_per_char = bytes_per_char
        self.force_empty = force_empty
        self.always_oversize = always_oversize
        self.calls: list[str] = []

    def is_available(self) -> tuple[bool, str]:
        return True, "OK"

    def synthesize(self, text: str, timeout_s: float = 10.0) -> bytes:
        self.calls.append(text)
        if self.force_empty:
            return b""
        if self.always_oversize:
            return _make_wav_bytes_for_pcm_len(640002)
        target_pcm = max(3200, len(text) * self.bytes_per_char)
        if target_pcm % 2 == 1:
            target_pcm += 1
        return _make_wav_bytes_for_pcm_len(target_pcm)


class TestFase1215BJarvisAmichettoTTS(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.cfg = BridgeConfig(
            device_token="tok-bridge-1234",
            esp_device_token="tok-esp-5678",
            require_auth=True,
            temp_dir=Path(self.tmp_dir.name),
            ai_mode="DISABLED",
            tts_max_chars=270,
            tts_piper_noise_scale=1.10,
            tts_piper_dsp_method="phase_vocoder",
            tts_piper_limiter_enabled=True,
        )

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_01_02_03_04_05_config_and_piper_amichetto_real_short_synthesis(self) -> None:
        self.assertEqual(self.cfg.tts_piper_speed, 1.00)
        self.assertEqual(self.cfg.tts_piper_noise_scale, 1.10)
        self.assertEqual(self.cfg.tts_piper_pitch_semitones, 5.0)
        self.assertEqual(self.cfg.tts_piper_robot_mix, 0.0)
        self.assertTrue(self.cfg.tts_piper_dsp_enabled)
        self.assertEqual(self.cfg.tts_max_chars, 270)

        piper_bin = _VOICE_AI_DIR / "tts-lab" / "bin" / "piper" / "piper.exe"
        model_path = _VOICE_AI_DIR / "tts-lab" / "models" / "piper" / "it_IT-riccardo-x_low.onnx"
        if not (piper_bin.is_file() and model_path.is_file()):
            self.skipTest("Piper binary/model not present")

        engine = PiperTTSEngine(
            piper_bin=str(piper_bin),
            model_path=str(model_path),
            target_sr=16000,
            speed=self.cfg.tts_piper_speed,
            noise_scale=self.cfg.tts_piper_noise_scale,
            pitch_semitones=self.cfg.tts_piper_pitch_semitones,
            robot_mix=self.cfg.tts_piper_robot_mix,
            dsp_enabled=self.cfg.tts_piper_dsp_enabled,
        )
        self.assertAlmostEqual(engine.length_scale, 1.000, places=4)
        ok, detail = engine.is_available()
        self.assertTrue(ok)
        self.assertIn("speed=1.00x", detail)
        self.assertIn("pitch=+5.0st", detail)

        wav_out = engine.synthesize("Dodici per otto fa novantasei.")
        with wave.open(io.BytesIO(wav_out), "rb") as wf:
            self.assertEqual(wf.getframerate(), 16000)
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            raw = wf.readframes(wf.getnframes())
        arr = np.frombuffer(raw, dtype=np.int16)
        self.assertGreater(len(raw), 16000)
        self.assertLessEqual(len(raw), 640000)
        self.assertEqual(int(np.sum(np.abs(arr) >= 32767)), 0)
        # Verify clean trailing silence (no end-of-sentence truncation)
        last_50ms = arr[-800:]
        self.assertLess(int(np.max(np.abs(last_50ms))), 200)

        # Also verify ~250-char scientific explanation at 1.00x stays <= 640000 B with 0 clipping
        long_wav = engine.synthesize(
            "Un vulcano è un'apertura della crosta terrestre da cui risalgono magma, gas e ceneri. "
            "Quando la pressione interna aumenta, il magma sale lungo il condotto ed esce come lava, "
            "che raffreddandosi forma il cono vulcanico."
        )
        pcm_b, _ = _measure_wav_pcm(long_wav)
        self.assertLessEqual(pcm_b, 640000)

    def test_06_07_08_09_pcm_bounds_exact_640000_and_empty_audio(self) -> None:
        wav_in = _make_wav_bytes_for_pcm_len(8000)

        # Exactly 640000 bytes -> accepted without retry
        class _ExactLimitTTS(TTSEngine):
            def __init__(self, n_bytes: int) -> None:
                self.n_bytes = n_bytes
                self.calls = 0

            def is_available(self) -> tuple[bool, str]:
                return True, "OK"

            def synthesize(self, text: str, timeout_s: float = 10.0) -> bytes:
                self.calls += 1
                return _make_wav_bytes_for_pcm_len(self.n_bytes)

        tts_exact = _ExactLimitTTS(640000)
        svc_exact = VoiceBridgeService(config=self.cfg, stt_engine=_FixedSTT("che ore sono"), tts_engine=tts_exact)
        res = svc_exact.process_voice(wav_in)
        self.assertEqual(tts_exact.calls, 1)
        pcm_b, _ = _measure_wav_pcm(svc_exact.temp_store.get(res.audio_id, consume=True))
        self.assertEqual(pcm_b, 640000)

        # Empty WAV -> BridgeError TTS_FAILED
        tts_empty = _LengthScaledTTS(force_empty=True)
        svc_empty = VoiceBridgeService(config=self.cfg, stt_engine=_FixedSTT("che ore sono"), tts_engine=tts_empty)
        with self.assertRaises(BridgeError) as ctx:
            svc_empty.process_voice(wav_in)
        self.assertEqual(ctx.exception.code, "TTS_FAILED")

    def test_10_11_12_14_15_oversize_reduction_no_punct_and_bounded_fallback(self) -> None:
        wav_in = _make_wav_bytes_for_pcm_len(8000)

        # 300-char text with 3 sentences that exceeds 640000 B at 2800 B/char -> reduced on sentence boundary
        three_sentences = (
            "Prima frase chiara sul funzionamento del vulcano. "
            "Seconda frase aggiuntiva con dettagli sul magma caldo. "
            "Terza frase molto lunga che fa superare il limite massimo consentito."
        )
        self.assertLessEqual(len(three_sentences), 300)
        reduced = _reduce_tts_text_for_limit(three_sentences, pcm_bytes=800000, max_pcm_bytes=640000)
        self.assertTrue(reduced.endswith("."))
        self.assertLess(len(reduced), len(three_sentences))

        # No-punctuation text reduction
        no_punct = "parola " * 40
        reduced_np = _reduce_tts_text_for_limit(no_punct, pcm_bytes=800000, max_pcm_bytes=640000)
        self.assertTrue(reduced_np.endswith("."))
        self.assertLess(len(reduced_np), len(no_punct))

        # Bounded retry + short Italian fallback when even reduced text stays oversize
        class _FallbackTriggerTTS(TTSEngine):
            def __init__(self) -> None:
                self.calls: list[str] = []

            def is_available(self) -> tuple[bool, str]:
                return True, "OK"

            def synthesize(self, text: str, timeout_s: float = 10.0) -> bytes:
                self.calls.append(text)
                if text == "La risposta è troppo lunga. Chiedimi una versione più breve.":
                    return _make_wav_bytes_for_pcm_len(32000)
                return _make_wav_bytes_for_pcm_len(650000)

        tts_scaled = _FallbackTriggerTTS()
        svc = VoiceBridgeService(config=self.cfg, stt_engine=_FixedSTT("spiegami tutto"), tts_engine=tts_scaled)
        svc.ai_router.offline.generate_reply = lambda _t, reason="": (
            "Prima frase lunga per testare il superamento del limite PCM dispositivo. "
            "Seconda frase lunga per testare la riduzione automatica del testo parlato. "
            "Terza frase lunga per forzare infine il fallback breve.",
            "offline_fallback",
        )
        res = svc.process_voice(wav_in)
        self.assertLessEqual(len(tts_scaled.calls), 4)  # max 1 initial + 2 reductions + 1 short fallback
        self.assertEqual(tts_scaled.calls[-1], "La risposta è troppo lunga. Chiedimi una versione più breve.")
        pcm_final, _ = _measure_wav_pcm(svc.temp_store.get(res.audio_id, consume=True))
        self.assertLessEqual(pcm_final, 640000)

        # Always-oversize even on fallback -> raises TTS_TOO_LONG without infinite loop
        tts_always = _LengthScaledTTS(always_oversize=True)
        svc2 = VoiceBridgeService(config=self.cfg, stt_engine=_FixedSTT("che ore sono"), tts_engine=tts_always)
        with self.assertRaises(BridgeError) as ctx2:
            svc2.process_voice(wav_in)
        self.assertEqual(ctx2.exception.code, "TTS_TOO_LONG")
        self.assertLessEqual(len(tts_always.calls), 4)


if __name__ == "__main__":
    unittest.main()
