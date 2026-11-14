"""Thread-safe Eye Bridge between VoiceController, tkinter Simulator, and future ESP32 Serial."""

from abc import ABC, abstractmethod
import queue
from typing import Callable, Optional


class EyeTransport(ABC):
    """Abstract transport for eye state commands (Simulator GUI or ESP32-S3 Serial/Network)."""

    @abstractmethod
    def send_command(self, cmd: str) -> None:
        """Queues or sends a protocol command such as 'STATE:THINKING' or 'BLINK'."""

    def set_audio_level(self, level: float) -> None:
        """Future hook for audio-reactive speaking intensity [0.0..1.0]."""


class SimulatorQueueTransport(EyeTransport):
    """Thread-safe queue consumed on the tkinter main thread (never touches Tk from worker threads)."""

    def __init__(self) -> None:
        self._queue: "queue.Queue[str]" = queue.Queue()

    def send_command(self, cmd: str) -> None:
        cleaned = cmd.strip()
        if cleaned:
            self._queue.put(cleaned)

    def drain(self, handler: Callable[[str], None]) -> None:
        while True:
            try:
                cmd = self._queue.get_nowait()
            except queue.Empty:
                break
            handler(cmd)


class SerialEyeTransport(EyeTransport):
    """Future USB-Serial transport to ESP32-S3 / Raspberry Pi using existing serial protocol."""

    def __init__(self, port: str, baudrate: int = 115200) -> None:
        self.port = port
        self.baudrate = baudrate
        self._ser = None

    def connect(self) -> None:
        import serial  # pyserial

        self._ser = serial.Serial(self.port, self.baudrate, timeout=0.5)

    def send_command(self, cmd: str) -> None:
        if self._ser is not None and getattr(self._ser, "is_open", False):
            self._ser.write((cmd.strip() + "\n").encode("ascii", errors="ignore"))

    def close(self) -> None:
        if self._ser is not None:
            self._ser.close()
            self._ser = None


class EyeBridge:
    """High-level eye state bridge translating conversation events to serial/simulator commands."""

    def __init__(self, transport: Optional[EyeTransport] = None) -> None:
        self.transport = transport or SimulatorQueueTransport()

    def set_state(self, state_name: str) -> None:
        self.transport.send_command(f"STATE:{state_name.upper()}")

    def blink(self) -> None:
        self.transport.send_command("BLINK")

    def look(self, dx: int, dy: int) -> None:
        self.transport.send_command(f"LOOK:{dx},{dy}")

    def set_auto_demo(self, enabled: bool) -> None:
        self.transport.send_command("AUTO:ON" if enabled else "AUTO:OFF")

    def on_audio_level(self, level: float) -> None:
        self.transport.set_audio_level(max(0.0, min(1.0, level)))
