"""Pluggable Text-to-Speech (TTS) Providers for JARVIS Voice & AI."""

from abc import ABC, abstractmethod
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from typing import Callable, Dict, List, Optional
import uuid

try:
    import winsound
except ImportError:  # pragma: no cover - non-Windows
    winsound = None  # type: ignore[assignment]

from config import JarvisConfig
from voice_dsp import shape_piper_wav


class TTSError(RuntimeError):
    """Raised when local TTS synthesis fails."""


class TTSProvider(ABC):
    @abstractmethod
    def list_voices(self) -> List[str]:
        """Returns installed voice names."""

    @abstractmethod
    def speak(
        self,
        text: str,
        voice: str = "",
        rate: int = 1,
        volume: int = 90,
        on_done: Optional[Callable[[Optional[str]], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
    ) -> None:
        """Starts non-blocking speech playback."""

    @abstractmethod
    def stop(self) -> None:
        """Immediately interrupts any active speech playback."""

    @abstractmethod
    def is_speaking(self) -> bool:
        """Returns True if speech is currently playing."""


class WindowsSapiTTSProvider(TTSProvider):
    """Local Windows 11 TTS via System.Speech.Synthesis (zero external pip deps)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._proc: Optional[subprocess.Popen] = None
        self._speaking = False

    def list_voices(self) -> List[str]:
        if os.name != "nt":
            return []
        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                capture_output=True,
                text=True,
                timeout=4.0,
            )
            if res.returncode == 0:
                return [line.strip() for line in res.stdout.splitlines() if line.strip()]
        except Exception:
            pass
        return []

    def is_speaking(self) -> bool:
        with self._lock:
            return self._speaking

    def speak(
        self,
        text: str,
        voice: str = "",
        rate: int = 1,
        volume: int = 90,
        on_done: Optional[Callable[[Optional[str]], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.stop()
        if os.name != "nt":
            if on_done:
                on_done("TTS Windows SAPI disponibile solo su Windows.")
            return

        cleaned = text.strip()
        if not cleaned:
            if on_done:
                on_done(None)
            return

        clamped_rate = max(-10, min(10, int(rate)))
        clamped_vol = max(0, min(100, int(volume)))
        safe_voice = voice.replace('"', "").strip()

        ps = f"""
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.Rate = {clamped_rate}
$s.Volume = {clamped_vol}
$targetVoice = "{safe_voice}"
if ($targetVoice -ne "") {{
    try {{ $s.SelectVoice($targetVoice) }} catch {{ }}
}}
$txt = [Console]::In.ReadToEnd()
if ($txt.Trim().Length -gt 0) {{
    $s.Speak($txt)
}}
"""
        with self._lock:
            self._speaking = True

        def _worker() -> None:
            err_msg: Optional[str] = None
            try:
                proc = subprocess.Popen(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                with self._lock:
                    self._proc = proc
                _, stderr_data = proc.communicate(input=cleaned.encode("utf-8"))
                if proc.returncode not in (0, None, -15, 1):
                    err_msg = stderr_data.decode("utf-8", errors="replace").strip() or "Errore TTS Windows"
            except Exception as exc:
                err_msg = str(exc)
            finally:
                with self._lock:
                    self._proc = None
                    self._speaking = False
                if on_done:
                    on_done(err_msg)

        threading.Thread(target=_worker, daemon=True, name="jarvis-tts").start()

    def stop(self) -> None:
        with self._lock:
            proc = self._proc
            self._speaking = False
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=1.0)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


VOICE_JARVIS_RICCARDO = "JARVIS Amichetto (Piper Riccardo)"
VOICE_PIPER_PAOLA = "Piper: Paola (it_IT-paola-medium)"

PIPER_VOICE_MODELS: Dict[str, str] = {
    VOICE_JARVIS_RICCARDO: "it_IT-riccardo-x_low.onnx",
    VOICE_PIPER_PAOLA: "it_IT-paola-medium.onnx",
}


class PiperWithFallbackTTSProvider(TTSProvider):
    """Local Piper TTS with Amichetto Vivace DSP shaping and Windows SAPI fallback."""

    def __init__(
        self,
        config: Optional[JarvisConfig] = None,
        piper_exe: Optional[Path] = None,
        models_dir: Optional[Path] = None,
        fallback: Optional[TTSProvider] = None,
        on_audio_bytes: Optional[Callable[[bytes], None]] = None,
    ) -> None:
        base_dir = Path(__file__).resolve().parent
        self.config = config or JarvisConfig()
        self.piper_exe = piper_exe or (base_dir / "tts-lab" / "bin" / "piper" / "piper.exe")
        self.models_dir = models_dir or (base_dir / "tts-lab" / "models" / "piper")
        self.fallback = fallback or WindowsSapiTTSProvider()
        self.on_audio_bytes = on_audio_bytes

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._proc: Optional[subprocess.Popen] = None
        self._speaking = False

    def _resolve_piper_model(self, voice: str) -> Optional[Path]:
        target = voice.strip() or self.config.tts_voice.strip()
        model_name = PIPER_VOICE_MODELS.get(target)
        if not model_name:
            return None
        if not self.piper_exe.is_file():
            return None
        model_path = self.models_dir / model_name
        if not model_path.is_file():
            return None
        return model_path

    def list_voices(self) -> List[str]:
        voices: List[str] = []
        if self.piper_exe.is_file():
            for label, model_name in PIPER_VOICE_MODELS.items():
                if (self.models_dir / model_name).is_file():
                    voices.append(label)
        for v in self.fallback.list_voices():
            if v not in voices:
                voices.append(v)
        return voices

    def is_speaking(self) -> bool:
        with self._lock:
            speaking = self._speaking
        return speaking or self.fallback.is_speaking()

    def speak(
        self,
        text: str,
        voice: str = "",
        rate: int = 1,
        volume: int = 90,
        on_done: Optional[Callable[[Optional[str]], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.stop()
        cleaned = text.strip()
        if not cleaned:
            if on_done:
                on_done(None)
            return

        target_voice = voice.strip() or self.config.tts_voice.strip()
        model_path = self._resolve_piper_model(target_voice)
        if model_path is None or winsound is None:
            fallback_voice = "" if target_voice in PIPER_VOICE_MODELS else target_voice
            self.fallback.speak(
                cleaned,
                voice=fallback_voice,
                rate=rate,
                volume=volume,
                on_done=on_done,
                on_audio_level=on_audio_level,
            )
            return

        self._stop_event.clear()
        with self._lock:
            self._speaking = True

        def _worker() -> None:
            tmp_dir = Path(tempfile.gettempdir())
            tag = uuid.uuid4().hex[:10]
            raw_wav = tmp_dir / f"jarvis_piper_raw_{tag}.wav"
            play_wav = tmp_dir / f"jarvis_piper_play_{tag}.wav"
            fallback_invoked = False
            err_msg: Optional[str] = None
            try:
                speed = max(0.75, min(1.50, self.config.piper_speed + (int(rate) - 1) * 0.05))
                length_scale = 1.0 / speed
                noise_scale = max(0.2, min(1.5, float(self.config.piper_noise_scale)))
                is_riccardo = target_voice == VOICE_JARVIS_RICCARDO
                pitch = float(self.config.piper_pitch_semitones) if is_riccardo else 0.0
                robot_mix = float(self.config.piper_robot_mix) if is_riccardo else 0.0

                cmd = [
                    str(self.piper_exe),
                    "--model",
                    str(model_path),
                    "--length_scale",
                    f"{length_scale:.3f}",
                    "--noise_scale",
                    f"{noise_scale:.3f}",
                    "--output_file",
                    str(raw_wav),
                ]
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    cwd=str(self.piper_exe.parent),
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                with self._lock:
                    self._proc = proc
                _, stderr_data = proc.communicate(input=(cleaned + "\n").encode("utf-8"), timeout=30.0)
                with self._lock:
                    self._proc = None

                if self._stop_event.is_set():
                    return
                if proc.returncode != 0 or not raw_wav.is_file():
                    detail = stderr_data.decode("utf-8", errors="replace").strip()
                    raise TTSError(detail or f"Piper exited with {proc.returncode}")

                raw_bytes = raw_wav.read_bytes()
                shaped_bytes, duration_s = shape_piper_wav(
                    raw_bytes,
                    pitch_semitones=pitch,
                    robot_mix=robot_mix,
                    volume=int(volume),
                )
                if self.on_audio_bytes:
                    self.on_audio_bytes(shaped_bytes)
                if self._stop_event.is_set():
                    return

                play_wav.write_bytes(shaped_bytes)
                winsound.PlaySound(str(play_wav), winsound.SND_FILENAME | winsound.SND_ASYNC)
                self._stop_event.wait(timeout=max(0.05, duration_s + 0.08))
            except Exception:
                if not self._stop_event.is_set():
                    fallback_invoked = True
                    with self._lock:
                        self._speaking = False
                    self.fallback.speak(
                        cleaned,
                        voice="",
                        rate=rate,
                        volume=volume,
                        on_done=on_done,
                        on_audio_level=on_audio_level,
                    )
            finally:
                with self._lock:
                    self._proc = None
                    if not fallback_invoked:
                        self._speaking = False
                for p in (raw_wav, play_wav):
                    try:
                        if p.exists():
                            p.unlink()
                    except Exception:
                        pass
                if not fallback_invoked and on_done:
                    on_done(err_msg)

        threading.Thread(target=_worker, daemon=True, name="jarvis-piper-tts").start()

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            proc = self._proc
            self._speaking = False
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=1.0)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        if winsound is not None:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
        self.fallback.stop()


class MockTTSProvider(TTSProvider):
    """Non-blocking controllable TTS provider for automated tests."""

    def __init__(self, should_fail: bool = False, delay_s: float = 0.05) -> None:
        self.should_fail = should_fail
        self.delay_s = delay_s
        self.spoken_texts: List[str] = []
        self._stop_event = threading.Event()
        self._speaking = False

    def list_voices(self) -> List[str]:
        return ["Microsoft Elsa Desktop", "Mock Voice"]

    def is_speaking(self) -> bool:
        return self._speaking

    def speak(
        self,
        text: str,
        voice: str = "",
        rate: int = 1,
        volume: int = 90,
        on_done: Optional[Callable[[Optional[str]], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
    ) -> None:
        self._stop_event.clear()
        self._speaking = True
        self.spoken_texts.append(text)

        def _worker() -> None:
            self._stop_event.wait(self.delay_s)
            self._speaking = False
            if on_done:
                on_done("Errore TTS simulato" if self.should_fail else None)

        threading.Thread(target=_worker, daemon=True).start()

    def stop(self) -> None:
        self._stop_event.set()
        self._speaking = False
