"""Pluggable Speech-to-Text (STT) Providers for JARVIS Voice & AI."""

from abc import ABC, abstractmethod
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Tuple
import wave


class STTError(RuntimeError):
    """Raised when transcription fails or no STT backend is available."""


class STTProvider(ABC):
    provider_id: str = "base"
    display_name: str = "Base STT"

    @abstractmethod
    def is_available(self) -> Tuple[bool, str]:
        """Returns (available, status_message)."""

    @abstractmethod
    def transcribe(self, wav_bytes: bytes, language: str = "it-IT", timeout_s: float = 10.0) -> str:
        """Transcribes WAV audio bytes into text."""


class FasterWhisperSTTProvider(STTProvider):
    """Local faster-whisper STT (CPU INT8, Italian, explicit model cache check)."""

    provider_id = "faster_whisper"
    display_name = "faster-whisper (Locale CPU INT8)"

    def __init__(self, model_size: str = "base", allow_download: bool = False) -> None:
        self.model_size = model_size
        self.allow_download = allow_download
        self._model = None

    def is_model_cached(self) -> bool:
        if importlib.util.find_spec("faster_whisper") is None:
            return False
        try:
            from faster_whisper.utils import download_model  # type: ignore

            download_model(self.model_size, local_files_only=True)
            return True
        except Exception:
            return False

    def is_available(self) -> Tuple[bool, str]:
        if importlib.util.find_spec("faster_whisper") is None:
            return False, "faster-whisper non installato nell'ambiente attivo"
        if not self.allow_download and not self.is_model_cached():
            return (
                False,
                f"faster-whisper installato; modello '{self.model_size}' non ancora scaricato (~145 MB)",
            )
        return True, f"faster-whisper pronto (modello '{self.model_size}', CPU int8)"

    def transcribe(self, wav_bytes: bytes, language: str = "it-IT", timeout_s: float = 10.0) -> str:
        ok, msg = self.is_available()
        if not ok:
            raise STTError(msg)

        from faster_whisper import WhisperModel  # type: ignore
        import numpy as np  # type: ignore

        if self._model is None:
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
                local_files_only=(not self.allow_download),
            )

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

        lang_code = language.split("-")[0].lower() or "it"
        segments, _ = self._model.transcribe(
            audio_f32,
            language=lang_code,
            beam_size=3,
            vad_filter=True,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        if not text:
            raise STTError("Nessuna parola riconosciuta nell'audio.")
        return text


class WindowsSpeechSTTProvider(STTProvider):
    """Zero-dependency Windows System.Speech.Recognition fallback (if it-IT recognizer exists)."""

    provider_id = "windows_sapi_stt"
    display_name = "Windows Speech Recognition"

    def is_available(self) -> Tuple[bool, str]:
        if os.name != "nt":
            return False, "Solo Windows"
        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$r = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() "
            "| Where-Object { $_.Culture.Name -like 'it*' }; "
            "if ($r) { Write-Output $r[0].Culture.Name } else { exit 1 }"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                capture_output=True,
                text=True,
                timeout=4.0,
            )
            if res.returncode == 0 and res.stdout.strip():
                return True, f"Windows Speech ({res.stdout.strip()}) disponibile"
        except Exception:
            pass
        return False, "Pacchetto riconoscimento vocale it-IT Windows non installato"

    def transcribe(self, wav_bytes: bytes, language: str = "it-IT", timeout_s: float = 10.0) -> str:
        ok, msg = self.is_available()
        if not ok:
            raise STTError(msg)

        fd, tmp_name = tempfile.mkstemp(prefix="jarvis_stt_", suffix=".wav")
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            tmp_path.write_bytes(wav_bytes)
            ps = f"""
Add-Type -AssemblyName System.Speech
$rec = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | Where-Object {{ $_.Culture.Name -like 'it*' }} | Select-Object -First 1
if (-not $rec) {{ exit 2 }}
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine($rec)
$engine.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$engine.SetInputToWaveFile("{str(tmp_path).replace('"', '')}")
$res = $engine.Recognize()
if ($res -and $res.Text) {{ Write-Output $res.Text }} else {{ exit 3 }}
"""
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            if proc.returncode != 0 or not proc.stdout.strip():
                raise STTError("Trascrizione Windows Speech vuota o non riconosciuta.")
            return proc.stdout.strip()
        except subprocess.TimeoutExpired as exc:
            raise STTError("Timeout trascrizione STT.") from exc
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass


class AutoLocalSTTProvider(STTProvider):
    """Selects best available local STT backend (faster-whisper -> Windows Speech)."""

    provider_id = "auto_local"
    display_name = "STT Locale Automatico"

    def __init__(self, whisper_model_size: str = "base") -> None:
        self._whisper = FasterWhisperSTTProvider(model_size=whisper_model_size)
        self._win = WindowsSpeechSTTProvider()

    def is_available(self) -> Tuple[bool, str]:
        ok_w, msg_w = self._whisper.is_available()
        if ok_w:
            return True, msg_w
        if importlib.util.find_spec("faster_whisper") is not None:
            return False, msg_w
        ok_s, msg_s = self._win.is_available()
        if ok_s:
            return True, msg_s
        return False, "Nessun motore STT locale installato (usa input testuale o installa faster-whisper)"

    def transcribe(self, wav_bytes: bytes, language: str = "it-IT", timeout_s: float = 10.0) -> str:
        ok_w, _ = self._whisper.is_available()
        if ok_w:
            return self._whisper.transcribe(wav_bytes, language=language, timeout_s=timeout_s)
        ok_s, _ = self._win.is_available()
        if ok_s:
            return self._win.transcribe(wav_bytes, language=language, timeout_s=timeout_s)
        raise STTError(
            "Nessun motore STT locale pronto. Usa il campo testo oppure approva l'installazione di faster-whisper."
        )


class MockSTTProvider(STTProvider):
    """Deterministic STT provider for unit tests."""

    provider_id = "mock_stt"
    display_name = "Mock STT"

    def __init__(self, canned_text: str = "Ciao JARVIS", should_fail: bool = False) -> None:
        self.canned_text = canned_text
        self.should_fail = should_fail

    def is_available(self) -> Tuple[bool, str]:
        return (not self.should_fail), ("Mock STT pronto" if not self.should_fail else "Mock STT errore")

    def transcribe(self, wav_bytes: bytes, language: str = "it-IT", timeout_s: float = 10.0) -> str:
        if self.should_fail:
            raise STTError("Errore STT simulato")
        return self.canned_text
