"""STT Engine adapter reusing existing 05-Voice-AI/stt_providers.py."""

from __future__ import annotations

from abc import ABC, abstractmethod
import ctypes
from dataclasses import asdict, dataclass
import gc
import io
import os
from pathlib import Path
import re
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple
import wave

import numpy as np

_VOICE_AI_DIR = Path(__file__).resolve().parent.parent
if str(_VOICE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_VOICE_AI_DIR))

from stt_providers import FasterWhisperSTTProvider, STTError  # noqa: E402

from .schemas import BridgeError


ALLOWED_COMPARE_MODELS: Tuple[str, ...] = ("base", "small")
_WER_PUNCT_RE = re.compile(r"[?!.,;:\"'()«»—\-]+")


def validate_compare_models(models: Sequence[str]) -> Tuple[str, ...]:
    cleaned = tuple(m.strip().lower() for m in models if m and m.strip())
    if not cleaned:
        raise BridgeError("INVALID_STT_MODEL", "Nessun modello STT specificato", http_status=400, recoverable=False)
    for m in cleaned:
        if m not in ALLOWED_COMPARE_MODELS:
            raise BridgeError(
                "INVALID_STT_MODEL",
                f"Modello STT non autorizzato: '{m}'. Consentiti solo: base, small",
                http_status=400,
                recoverable=False,
            )
    return cleaned


def compute_wer(reference: str, hypothesis: str) -> Optional[float]:
    """Word Error Rate normalized for case and punctuation; returns None if reference is empty."""
    ref_norm = _WER_PUNCT_RE.sub(" ", (reference or "").lower()).split()
    if not ref_norm:
        return None
    hyp_norm = _WER_PUNCT_RE.sub(" ", (hypothesis or "").lower()).split()
    n, m = len(ref_norm), len(hyp_norm)
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, m + 1):
            cur = dp[j]
            cost = 0 if ref_norm[i - 1] == hyp_norm[j - 1] else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = cur
    return round(dp[m] / float(n), 4)


def get_process_rss_mb() -> Optional[float]:
    """Returns current process working set (RSS) in MB when reliably measurable."""
    if os.name == "nt":
        try:
            class _PMC(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.c_ulong),
                    ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            pmc = _PMC()
            pmc.cb = ctypes.sizeof(pmc)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.kernel32.K32GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
                return round(pmc.WorkingSetSize / (1024.0 * 1024.0), 2)
        except Exception:
            return None
    return None


@dataclass(frozen=True)
class STTOptions:
    vad_filter: bool = True
    speech_pad_ms: int = 0
    beam_size: int = 3
    condition_on_previous_text: bool = True
    initial_prompt: str = ""


COMPARE_PRESETS: List[Tuple[str, str, STTOptions]] = [
    ("A", "Baseline (vad=True, pad=0, beam=3)", STTOptions(vad_filter=True, speech_pad_ms=0, beam_size=3, condition_on_previous_text=True, initial_prompt="")),
    ("B", "Senza VAD (vad=False, beam=3)", STTOptions(vad_filter=False, speech_pad_ms=0, beam_size=3, condition_on_previous_text=True, initial_prompt="")),
    ("C", "VAD con padding (vad=True, pad=250ms, beam=3)", STTOptions(vad_filter=True, speech_pad_ms=250, beam_size=3, condition_on_previous_text=True, initial_prompt="")),
    ("D", "Beam 5 (vad=True, pad=0, beam=5)", STTOptions(vad_filter=True, speech_pad_ms=0, beam_size=5, condition_on_previous_text=True, initial_prompt="")),
    ("E", "Prompt JARVIS (vad=True, pad=250ms, beam=5, no_prev)", STTOptions(vad_filter=True, speech_pad_ms=250, beam_size=5, condition_on_previous_text=False, initial_prompt="JARVIS, assistente vocale in italiano.")),
]


class STTEngine(ABC):
    @abstractmethod
    def is_available(self) -> Tuple[bool, str]:
        """Returns (available, status_detail)."""

    @abstractmethod
    def transcribe(
        self,
        wav_bytes: bytes,
        language: str = "it",
        timeout_s: float = 12.0,
        options: Optional[STTOptions] = None,
    ) -> str:
        """Transcribes normalized 16 kHz mono WAV into Italian text."""

    def compare_configs(
        self,
        wav_bytes: bytes,
        language: str = "it",
        timeout_s: float = 12.0,
    ) -> List[Dict[str, Any]]:
        """Runs diagnostic presets A..E on the same WAV bytes without persisting audio."""
        results: List[Dict[str, Any]] = []
        for preset_id, label, opts in COMPARE_PRESETS:
            t0 = time.monotonic()
            transcript = ""
            error = ""
            try:
                transcript = self.transcribe(wav_bytes, language=language, timeout_s=timeout_s, options=opts)
            except BridgeError as exc:
                error = f"{exc.code}: {exc.message}"
            except Exception as exc:
                error = str(exc)
            latency_ms = int((time.monotonic() - t0) * 1000)
            results.append(
                {
                    "id": preset_id,
                    "label": label,
                    "options": asdict(opts),
                    "transcript": transcript,
                    "latency_ms": latency_ms,
                    "error": error,
                }
            )
        return results

    def compare_models(
        self,
        wav_bytes: bytes,
        models: Sequence[str] = ALLOWED_COMPARE_MODELS,
        language: str = "it",
        timeout_s: float = 25.0,
        options: Optional[STTOptions] = None,
        reference_text: str = "",
    ) -> List[Dict[str, Any]]:
        """Sequentially compares allowed Whisper models on the same WAV bytes."""
        validated_models = validate_compare_models(models)
        opts = options or STTOptions(vad_filter=True, speech_pad_ms=0, beam_size=3, condition_on_previous_text=True, initial_prompt="")
        results: List[Dict[str, Any]] = []
        for model_name in validated_models:
            t0 = time.monotonic()
            transcript = ""
            error = ""
            try:
                transcript = self.transcribe(wav_bytes, language=language, timeout_s=timeout_s, options=opts)
            except BridgeError as exc:
                error = f"{exc.code}: {exc.message}"
            except Exception as exc:
                error = str(exc)
            inf_ms = int((time.monotonic() - t0) * 1000)
            results.append(
                {
                    "model": model_name,
                    "transcript": transcript,
                    "wer": compute_wer(reference_text, transcript) if not error else None,
                    "load_ms": 0,
                    "inference_ms": inf_ms,
                    "rss_mb": get_process_rss_mb(),
                    "rss_delta_mb": 0.0,
                    "options": {**asdict(opts), "language": language},
                    "error": error,
                }
            )
        return results


class FasterWhisperEngine(STTEngine):
    """Thread-safe single-load-per-process wrapper around FasterWhisperSTTProvider."""

    def __init__(
        self,
        model_size: str = "base",
        allow_download: bool = False,
        default_options: Optional[STTOptions] = None,
    ) -> None:
        self._provider = FasterWhisperSTTProvider(model_size=model_size, allow_download=allow_download)
        self.default_options = default_options or STTOptions()
        self._lock = threading.Lock()

    def is_available(self) -> Tuple[bool, str]:
        return self._provider.is_available()

    def _ensure_model_loaded(self) -> Any:
        if self._provider._model is None:
            from faster_whisper import WhisperModel

            self._provider._model = WhisperModel(
                self._provider.model_size,
                device="cpu",
                compute_type="int8",
                local_files_only=(not self._provider.allow_download),
            )
        return self._provider._model

    @staticmethod
    def _wav_to_float32_16k(wav_bytes: bytes) -> np.ndarray:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())

        if sampwidth != 2 or not frames:
            raise STTError("Formato audio WAV non valido o vuoto.")

        audio_i16 = np.frombuffer(frames, dtype=np.int16)
        if n_channels > 1:
            audio_i16 = audio_i16.reshape(-1, n_channels).mean(axis=1)
        audio_f32 = (audio_i16.astype(np.float32)) / 32768.0

        if framerate != 16000 and len(audio_f32) > 1:
            target_len = max(1, int(len(audio_f32) * 16000 / framerate))
            audio_f32 = np.interp(
                np.linspace(0, len(audio_f32) - 1, target_len, dtype=np.float32),
                np.arange(len(audio_f32), dtype=np.float32),
                audio_f32,
            ).astype(np.float32)
        return audio_f32

    def transcribe(
        self,
        wav_bytes: bytes,
        language: str = "it",
        timeout_s: float = 12.0,
        options: Optional[STTOptions] = None,
    ) -> str:
        ok, msg = self._provider.is_available()
        if not ok:
            raise BridgeError("STT_UNAVAILABLE", msg, http_status=503, recoverable=True)

        opts = options or self.default_options
        lang_code = language.split("-")[0].lower() or "it"

        t0 = time.monotonic()
        with self._lock:
            try:
                model = self._ensure_model_loaded()
                audio_f32 = self._wav_to_float32_16k(wav_bytes)
                kwargs: Dict[str, Any] = {
                    "language": lang_code,
                    "beam_size": max(1, int(opts.beam_size)),
                    "vad_filter": bool(opts.vad_filter),
                    "condition_on_previous_text": bool(opts.condition_on_previous_text),
                }
                if opts.vad_filter and opts.speech_pad_ms > 0:
                    kwargs["vad_parameters"] = {"speech_pad_ms": int(opts.speech_pad_ms)}
                if opts.initial_prompt.strip():
                    kwargs["initial_prompt"] = opts.initial_prompt.strip()
                segments, _ = model.transcribe(audio_f32, **kwargs)
                text = " ".join(seg.text.strip() for seg in segments).strip()
            except STTError as exc:
                raise BridgeError("STT_FAILED", str(exc), http_status=500, recoverable=True) from exc
            except Exception as exc:
                raise BridgeError("STT_FAILED", f"Errore trascrizione STT: {exc}", http_status=500, recoverable=True) from exc
        elapsed = time.monotonic() - t0
        if elapsed > timeout_s:
            raise BridgeError("STT_TIMEOUT", f"Timeout STT ({elapsed:.1f}s > {timeout_s:.1f}s)", http_status=504, recoverable=True)
        if not text:
            raise BridgeError("EMPTY_TRANSCRIPT", "Nessun parlato riconosciuto nell'audio", http_status=422, recoverable=True)
        return text

    def compare_models(
        self,
        wav_bytes: bytes,
        models: Sequence[str] = ALLOWED_COMPARE_MODELS,
        language: str = "it",
        timeout_s: float = 25.0,
        options: Optional[STTOptions] = None,
        reference_text: str = "",
    ) -> List[Dict[str, Any]]:
        """Sequentially compares allowed Whisper models (base/small) on the same WAV bytes."""
        validated_models = validate_compare_models(models)
        opts = options or STTOptions(
            vad_filter=True,
            speech_pad_ms=self.default_options.speech_pad_ms,
            beam_size=3,
            condition_on_previous_text=self.default_options.condition_on_previous_text,
            initial_prompt="",
        )
        lang_code = language.split("-")[0].lower() or "it"
        results: List[Dict[str, Any]] = []

        with self._lock:
            audio_f32 = self._wav_to_float32_16k(wav_bytes)
            for model_name in validated_models:
                transcript = ""
                error = ""
                load_ms = 0
                inference_ms = 0
                rss_before = get_process_rss_mb()
                rss_after = rss_before
                temp_model = None
                try:
                    if model_name == self._provider.model_size:
                        ok, msg = self._provider.is_available()
                        if not ok:
                            raise BridgeError("STT_UNAVAILABLE", msg, http_status=503, recoverable=True)
                        t_load = time.monotonic()
                        model = self._ensure_model_loaded()
                        load_ms = int((time.monotonic() - t_load) * 1000)
                    else:
                        probe_provider = FasterWhisperSTTProvider(model_size=model_name, allow_download=False)
                        ok, msg = probe_provider.is_available()
                        if not ok:
                            raise BridgeError("STT_UNAVAILABLE", msg, http_status=503, recoverable=True)
                        from faster_whisper import WhisperModel

                        t_load = time.monotonic()
                        temp_model = WhisperModel(
                            model_name,
                            device="cpu",
                            compute_type="int8",
                            local_files_only=True,
                        )
                        load_ms = int((time.monotonic() - t_load) * 1000)
                        model = temp_model

                    kwargs: Dict[str, Any] = {
                        "language": lang_code,
                        "beam_size": max(1, int(opts.beam_size)),
                        "vad_filter": bool(opts.vad_filter),
                        "condition_on_previous_text": bool(opts.condition_on_previous_text),
                    }
                    if opts.vad_filter and opts.speech_pad_ms > 0:
                        kwargs["vad_parameters"] = {"speech_pad_ms": int(opts.speech_pad_ms)}
                    if opts.initial_prompt.strip():
                        kwargs["initial_prompt"] = opts.initial_prompt.strip()

                    t_inf = time.monotonic()
                    segments, _ = model.transcribe(audio_f32, **kwargs)
                    transcript = " ".join(seg.text.strip() for seg in segments).strip()
                    elapsed_s = time.monotonic() - t_inf
                    inference_ms = int(elapsed_s * 1000)
                    rss_after = get_process_rss_mb()
                    if elapsed_s > timeout_s:
                        raise BridgeError(
                            "STT_TIMEOUT",
                            f"Timeout STT ({elapsed_s:.1f}s > {timeout_s:.1f}s)",
                            http_status=504,
                            recoverable=True,
                        )
                    if not transcript:
                        raise BridgeError("EMPTY_TRANSCRIPT", "Nessun parlato riconosciuto nell'audio", http_status=422, recoverable=True)
                except BridgeError as exc:
                    error = f"{exc.code}: {exc.message}"
                except Exception as exc:
                    error = f"STT_FAILED: {exc}"
                finally:
                    if temp_model is not None:
                        del temp_model
                        gc.collect()

                rss_delta = (
                    round(rss_after - rss_before, 2)
                    if (rss_after is not None and rss_before is not None)
                    else None
                )
                results.append(
                    {
                        "model": model_name,
                        "transcript": transcript if not error else "",
                        "wer": compute_wer(reference_text, transcript) if not error else None,
                        "load_ms": load_ms,
                        "inference_ms": inference_ms,
                        "rss_mb": rss_after,
                        "rss_delta_mb": rss_delta,
                        "options": {**asdict(opts), "language": lang_code},
                        "error": error,
                    }
                )
        return results


class MockSTTEngine(STTEngine):
    """Deterministic mock STT for offline automated tests."""

    def __init__(
        self,
        transcript: str = "Ciao Jarvis come stai",
        available: bool = True,
        delay_s: float = 0.0,
        model_transcripts: Optional[Dict[str, str]] = None,
        missing_models: Sequence[str] = (),
        fail_models: Optional[Dict[str, str]] = None,
    ) -> None:
        self.transcript = transcript
        self.available = available
        self.delay_s = delay_s
        self.model_transcripts = dict(model_transcripts or {})
        self.missing_models = tuple(missing_models)
        self.fail_models = dict(fail_models or {})
        self.last_options: Optional[STTOptions] = None
        self.recorded_calls: List[Tuple[str, bytes]] = []

    def is_available(self) -> Tuple[bool, str]:
        if not self.available:
            return False, "Modello STT mock non disponibile"
        return True, "Mock STT pronto"

    def transcribe(
        self,
        wav_bytes: bytes,
        language: str = "it",
        timeout_s: float = 12.0,
        options: Optional[STTOptions] = None,
    ) -> str:
        self.last_options = options
        if not self.available:
            raise BridgeError("STT_UNAVAILABLE", "Modello STT mancante", http_status=503, recoverable=True)
        if self.delay_s > timeout_s:
            raise BridgeError("STT_TIMEOUT", "Timeout STT simulato", http_status=504, recoverable=True)
        if self.delay_s > 0:
            time.sleep(self.delay_s)
        if not self.transcript.strip():
            raise BridgeError("EMPTY_TRANSCRIPT", "Trascrizione vuota", http_status=422, recoverable=True)
        return self.transcript.strip()

    def compare_models(
        self,
        wav_bytes: bytes,
        models: Sequence[str] = ALLOWED_COMPARE_MODELS,
        language: str = "it",
        timeout_s: float = 25.0,
        options: Optional[STTOptions] = None,
        reference_text: str = "",
    ) -> List[Dict[str, Any]]:
        validated_models = validate_compare_models(models)
        opts = options or STTOptions(vad_filter=True, speech_pad_ms=0, beam_size=3, condition_on_previous_text=True, initial_prompt="")
        results: List[Dict[str, Any]] = []
        for model_name in validated_models:
            self.recorded_calls.append((model_name, wav_bytes))
            t0 = time.monotonic()
            transcript = ""
            error = ""
            try:
                if not self.available or model_name in self.missing_models:
                    raise BridgeError("STT_UNAVAILABLE", f"Modello STT '{model_name}' mancante", http_status=503, recoverable=True)
                if model_name in self.fail_models:
                    raise BridgeError("STT_FAILED", self.fail_models[model_name], http_status=500, recoverable=True)
                if self.delay_s > timeout_s:
                    raise BridgeError("STT_TIMEOUT", "Timeout STT simulato", http_status=504, recoverable=True)
                if self.delay_s > 0:
                    time.sleep(self.delay_s)
                transcript = self.model_transcripts.get(model_name, self.transcript).strip()
                if not transcript:
                    raise BridgeError("EMPTY_TRANSCRIPT", "Trascrizione vuota", http_status=422, recoverable=True)
            except BridgeError as exc:
                error = f"{exc.code}: {exc.message}"
            inf_ms = int((time.monotonic() - t0) * 1000)
            results.append(
                {
                    "model": model_name,
                    "transcript": transcript if not error else "",
                    "wer": compute_wer(reference_text, transcript) if not error else None,
                    "load_ms": 0,
                    "inference_ms": inf_ms,
                    "rss_mb": get_process_rss_mb(),
                    "rss_delta_mb": 0.0,
                    "options": {**asdict(opts), "language": language},
                    "error": error,
                }
            )
        return results
