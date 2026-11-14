"""Windows Push-to-Talk Audio Input using native WinMM waveIn (in-memory, zero extra deps)."""

from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import io
import os
import struct
import threading
import time
import wave
from typing import List, Optional


class AudioInputError(RuntimeError):
    """Raised when microphone is missing or Push-to-Talk recording fails."""


@dataclass
class MicrophoneDevice:
    index: int
    name: str


def list_microphones() -> List[MicrophoneDevice]:
    """Enumerates Windows wave-in microphone devices via winmm.dll."""
    if os.name != "nt":
        return []
    try:
        winmm = ctypes.windll.winmm
        count = winmm.waveInGetNumDevs()
    except Exception:
        return []

    class WAVEINCAPSW(ctypes.Structure):
        _fields_ = [
            ("wMid", wintypes.WORD),
            ("wPid", wintypes.WORD),
            ("vDriverVersion", wintypes.UINT),
            ("szPname", wintypes.WCHAR * 32),
            ("dwFormats", wintypes.DWORD),
            ("wChannels", wintypes.WORD),
            ("wReserved1", wintypes.WORD),
        ]

    devices: List[MicrophoneDevice] = []
    for idx in range(count):
        caps = WAVEINCAPSW()
        res = winmm.waveInGetDevCapsW(idx, ctypes.byref(caps), ctypes.sizeof(caps))
        if res == 0:
            devices.append(MicrophoneDevice(index=idx, name=caps.szPname.strip()))
    return devices


def compute_wav_rms(wav_bytes: bytes) -> float:
    """Computes normalized RMS [0.0..1.0] of a 16-bit PCM WAV buffer."""
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            sampwidth = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())
    except Exception:
        return 0.0

    if sampwidth != 2 or len(frames) < 2:
        return 0.0
    sample_count = len(frames) // 2
    samples = struct.unpack(f"<{sample_count}h", frames[: sample_count * 2])
    mean_sq = sum(s * s for s in samples) / float(sample_count)
    return (mean_sq ** 0.5) / 32768.0


class _WAVEFORMATEX(ctypes.Structure):
    _fields_ = [
        ("wFormatTag", wintypes.WORD),
        ("nChannels", wintypes.WORD),
        ("nSamplesPerSec", wintypes.DWORD),
        ("nAvgBytesPerSec", wintypes.DWORD),
        ("nBlockAlign", wintypes.WORD),
        ("wBitsPerSample", wintypes.WORD),
        ("cbSize", wintypes.WORD),
    ]


class _WAVEHDR(ctypes.Structure):
    _fields_ = [
        ("lpData", ctypes.c_void_p),
        ("dwBufferLength", wintypes.DWORD),
        ("dwBytesRecorded", wintypes.DWORD),
        ("dwUser", ctypes.c_void_p),
        ("dwFlags", wintypes.DWORD),
        ("dwLoops", wintypes.DWORD),
        ("lpNext", ctypes.c_void_p),
        ("reserved", ctypes.c_void_p),
    ]


WHDR_DONE = 0x00000001
SAMPLE_RATE = 16000
CHANNELS = 1
BITS_PER_SAMPLE = 16
CHUNK_BYTES = 3200  # 100ms at 16kHz 16-bit mono
NUM_BUFFERS = 4


class WindowsWaveInRecorder:
    """Push-to-Talk recorder backed by Windows waveInOpen (shared mode, in-memory)."""

    def __init__(self, silence_rms_threshold: float = 0.002) -> None:
        self.silence_rms_threshold = silence_rms_threshold
        self.selected_device_index: int = 0
        self._lock = threading.Lock()
        self._recording = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._pcm_chunks: List[bytes] = []
        self._worker_error: Optional[str] = None

    def set_device_index(self, device_index: int) -> None:
        self.selected_device_index = max(0, int(device_index))

    def is_available(self) -> bool:
        return len(list_microphones()) > 0

    def start_recording(self) -> None:
        if os.name != "nt":
            raise AudioInputError("Registrazione WinMM disponibile solo su Windows.")
        devices = list_microphones()
        if not devices:
            raise AudioInputError("Nessun microfono rilevato su Windows.")

        with self._lock:
            if self._recording:
                return
            dev_id = self.selected_device_index
            if dev_id >= len(devices):
                dev_id = 0

            winmm = ctypes.windll.winmm
            fmt = _WAVEFORMATEX(
                1,
                CHANNELS,
                SAMPLE_RATE,
                SAMPLE_RATE * CHANNELS * (BITS_PER_SAMPLE // 8),
                CHANNELS * (BITS_PER_SAMPLE // 8),
                BITS_PER_SAMPLE,
                0,
            )
            handle = wintypes.HANDLE()
            res = winmm.waveInOpen(ctypes.byref(handle), dev_id, ctypes.byref(fmt), 0, 0, 0)
            if res != 0:
                raise AudioInputError(f"Impossibile aprire il microfono [{dev_id}] (codice WinMM {res}).")

            self._pcm_chunks = []
            self._worker_error = None
            self._stop_event.clear()
            self._recording = True

            self._thread = threading.Thread(
                target=self._record_loop,
                args=(winmm, handle),
                daemon=True,
                name="jarvis-wavein",
            )
            self._thread.start()

    def _record_loop(self, winmm, handle: wintypes.HANDLE) -> None:
        bufs = [ctypes.create_string_buffer(CHUNK_BYTES) for _ in range(NUM_BUFFERS)]
        hdrs = []
        try:
            for buf in bufs:
                hdr = _WAVEHDR()
                hdr.lpData = ctypes.addressof(buf)
                hdr.dwBufferLength = CHUNK_BYTES
                if winmm.waveInPrepareHeader(handle, ctypes.byref(hdr), ctypes.sizeof(hdr)) != 0:
                    raise AudioInputError("waveInPrepareHeader fallito")
                if winmm.waveInAddBuffer(handle, ctypes.byref(hdr), ctypes.sizeof(hdr)) != 0:
                    raise AudioInputError("waveInAddBuffer fallito")
                hdrs.append((hdr, buf))

            if winmm.waveInStart(handle) != 0:
                raise AudioInputError("waveInStart fallito")

            while not self._stop_event.is_set():
                any_done = False
                for hdr, buf in hdrs:
                    if hdr.dwFlags & WHDR_DONE:
                        any_done = True
                        if hdr.dwBytesRecorded > 0:
                            self._pcm_chunks.append(bytes(buf[: hdr.dwBytesRecorded]))
                        hdr.dwFlags &= ~WHDR_DONE
                        hdr.dwBytesRecorded = 0
                        winmm.waveInAddBuffer(handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
                if not any_done:
                    time.sleep(0.015)

            winmm.waveInStop(handle)
            winmm.waveInReset(handle)
            for hdr, buf in hdrs:
                if hdr.dwBytesRecorded > 0:
                    self._pcm_chunks.append(bytes(buf[: hdr.dwBytesRecorded]))
        except Exception as exc:
            self._worker_error = str(exc)
        finally:
            for hdr, _ in hdrs:
                try:
                    winmm.waveInUnprepareHeader(handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
                except Exception:
                    pass
            try:
                winmm.waveInClose(handle)
            except Exception:
                pass

    def stop_recording(self) -> bytes:
        with self._lock:
            if not self._recording:
                return b""
            self._recording = False
            self._stop_event.set()
            thread = self._thread
            self._thread = None

        if thread is not None:
            thread.join(timeout=2.0)

        if self._worker_error:
            raise AudioInputError(self._worker_error)

        pcm_data = b"".join(self._pcm_chunks)
        self._pcm_chunks = []
        if len(pcm_data) < 1600:
            raise AudioInputError("Registrazione vuota o troppo breve (parla per almeno mezzo secondo).")

        out = io.BytesIO()
        with wave.open(out, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(BITS_PER_SAMPLE // 8)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(pcm_data)
        wav_bytes = out.getvalue()

        if compute_wav_rms(wav_bytes) < self.silence_rms_threshold:
            raise AudioInputError("Nessuna voce rilevata (solo silenzio nel microfono).")
        return wav_bytes

    def cancel(self) -> None:
        with self._lock:
            if not self._recording:
                return
            self._recording = False
            self._stop_event.set()
            thread = self._thread
            self._thread = None
        if thread is not None:
            thread.join(timeout=1.5)
        self._pcm_chunks = []


# Alias for backward compatibility
WindowsMciAudioRecorder = WindowsWaveInRecorder
