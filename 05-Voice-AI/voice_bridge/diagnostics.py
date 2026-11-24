"""Diagnostics, request correlation, and secret-safe logging."""

from __future__ import annotations

import logging
import threading
from typing import Dict, Iterable, List
import uuid

from .security import redact_secrets


class BridgeDiagnostics:
    """Collects non-sensitive timings, provider status, and anomalies."""

    def __init__(self, extra_secrets: Iterable[str] = ()) -> None:
        self._lock = threading.Lock()
        self._secrets = tuple(s for s in extra_secrets if s)
        self._logger = logging.getLogger("jarvis.voice_bridge")
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
            self._logger.addHandler(handler)
        if self._logger.level == logging.NOTSET:
            self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        self._total_requests = 0
        self._failed_requests = 0
        self._recent_events: List[Dict[str, object]] = []

    def new_request_id(self) -> str:
        return f"req_{uuid.uuid4().hex[:12]}"

    def log_event(self, level: int, request_id: str, message: str, **fields: object) -> None:
        safe_msg = redact_secrets(message, self._secrets)
        safe_fields = {
            k: redact_secrets(str(v), self._secrets) if isinstance(v, str) else v
            for k, v in fields.items()
        }
        entry = {"request_id": request_id, "message": safe_msg, **safe_fields}
        with self._lock:
            self._recent_events.append(entry)
            if len(self._recent_events) > 50:
                self._recent_events.pop(0)
        self._logger.log(level, "%s | %s", request_id, safe_msg)

    def record_outcome(self, success: bool) -> None:
        with self._lock:
            self._total_requests += 1
            if not success:
                self._failed_requests += 1

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            return {
                "total_requests": self._total_requests,
                "failed_requests": self._failed_requests,
                "recent_events": list(self._recent_events[-10:]),
            }
