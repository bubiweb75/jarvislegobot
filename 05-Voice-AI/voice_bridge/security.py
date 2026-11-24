"""Security helpers: token auth, secret redaction, URL validation, temp store."""

from __future__ import annotations

import hmac
import ipaddress
import os
from pathlib import Path
import re
import secrets
import threading
import time
from typing import Dict, Iterable, Optional, Tuple
from urllib.parse import urlparse
import uuid

from .schemas import BridgeError


_BEARER_RE = re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/=]+", re.IGNORECASE)
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9\-_]{8,}|AIza[A-Za-z0-9\-_]{12,})")
_SAFE_ID_RE = re.compile(r"^[a-f0-9]{16,32}$")


def redact_secrets(text: str, extra_secrets: Iterable[str] = ()) -> str:
    """Masks known secrets and Bearer/API tokens before logging."""
    masked = _BEARER_RE.sub(r"\1[REDACTED]", text)
    masked = _KEY_RE.sub("[REDACTED_KEY]", masked)
    for secret in extra_secrets:
        if secret and len(secret) >= 4:
            masked = masked.replace(secret, "[REDACTED]")
    return masked


def verify_bearer_token(auth_header: Optional[str], expected_token: str, require_auth: bool) -> None:
    if not require_auth:
        return
    if not expected_token:
        raise BridgeError("AUTH_MISCONFIGURED", "Token bridge non configurato", http_status=503, recoverable=False)
    if not auth_header:
        raise BridgeError("UNAUTHORIZED", "Header Authorization mancante", http_status=401, recoverable=False)
    parts = auth_header.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise BridgeError("UNAUTHORIZED", "Formato Authorization non valido", http_status=401, recoverable=False)
    if not hmac.compare_digest(parts[1].strip(), expected_token):
        raise BridgeError("UNAUTHORIZED", "Token non valido", http_status=401, recoverable=False)


def validate_provider_url(url: str, allowed_hosts: Tuple[str, ...] = (), allow_public: bool = False) -> str:
    """Validates outbound provider URLs to block unauthorized destinations."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise BridgeError("INVALID_PROVIDER_URL", "URL provider non valido", http_status=500, recoverable=False)

    host = parsed.hostname.lower()
    if allowed_hosts:
        if host not in allowed_hosts:
            raise BridgeError(
                "DISALLOWED_PROVIDER_HOST",
                f"Host provider '{host}' non presente nella allowlist",
                http_status=500,
                recoverable=False,
            )
        return url.rstrip("/")

    if allow_public:
        return url.rstrip("/")

    # Local/LAN only by default for local Ollama
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        return url.rstrip("/")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback:
            return url.rstrip("/")
    except ValueError:
        pass

    raise BridgeError(
        "DISALLOWED_PROVIDER_HOST",
        f"Host locale non autorizzato '{host}' (solo LAN/localhost)",
        http_status=500,
        recoverable=False,
    )


def validate_cloud_url(url: str, allowed_hosts: Tuple[str, ...] = ()) -> str:
    """Validates remote Cloud AI URLs: requires HTTPS and blocks private/LAN targets (SSRF guard)."""
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise BridgeError(
            "INVALID_CLOUD_URL",
            "URL provider Cloud non valido: HTTPS obbligatorio",
            http_status=500,
            recoverable=False,
        )

    host = parsed.hostname.lower()
    if allowed_hosts:
        if host not in allowed_hosts:
            raise BridgeError(
                "DISALLOWED_CLOUD_HOST",
                f"Host Cloud '{host}' non presente nella allowlist",
                http_status=500,
                recoverable=False,
            )
        return url.rstrip("/")

    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith((".local", ".internal", ".lan", ".home")):
        raise BridgeError(
            "DISALLOWED_CLOUD_HOST",
            f"Host locale non consentito per provider Cloud: '{host}'",
            http_status=500,
            recoverable=False,
        )

    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            raise BridgeError(
                "DISALLOWED_CLOUD_HOST",
                f"Indirizzo IP privato/riservato non consentito per provider Cloud: '{host}'",
                http_status=500,
                recoverable=False,
            )
    except ValueError:
        pass

    return url.rstrip("/")


def safe_temp_path(base_dir: Path, filename: str) -> Path:
    """Prevents path traversal when resolving temporary audio files."""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise BridgeError("INVALID_PATH", "Nome file non valido", http_status=400, recoverable=False)
    base_resolved = base_dir.resolve()
    target = (base_resolved / filename).resolve()
    if target.parent != base_resolved:
        raise BridgeError("INVALID_PATH", "Percorso file non consentito", http_status=400, recoverable=False)
    return target


class TempAudioStore:
    """Thread-safe temporary WAV storage with TTL expiration and cleanup."""

    def __init__(self, base_dir: Path, ttl_s: float = 120.0) -> None:
        self.base_dir = base_dir
        self.ttl_s = ttl_s
        self._lock = threading.Lock()
        self._entries: Dict[str, Tuple[Path, float]] = {}
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def put(self, wav_bytes: bytes) -> str:
        self.cleanup_expired()
        audio_id = uuid.uuid4().hex
        path = safe_temp_path(self.base_dir, f"{audio_id}.wav")
        path.write_bytes(wav_bytes)
        with self._lock:
            self._entries[audio_id] = (path, time.monotonic() + self.ttl_s)
        return audio_id

    def get(self, audio_id: str, consume: bool = False) -> bytes:
        if not _SAFE_ID_RE.match(audio_id):
            raise BridgeError("INVALID_AUDIO_ID", "Identificativo audio non valido", http_status=400, recoverable=False)
        self.cleanup_expired()
        with self._lock:
            item = self._entries.get(audio_id)
            if item is None:
                raise BridgeError("AUDIO_NOT_FOUND", "Audio temporaneo scaduto o inesistente", http_status=404, recoverable=False)
            path, expires_at = item
            if time.monotonic() > expires_at or not path.exists():
                self._entries.pop(audio_id, None)
                if path.exists():
                    path.unlink(missing_ok=True)
                raise BridgeError("AUDIO_EXPIRED", "Audio temporaneo scaduto", http_status=404, recoverable=False)
            data = path.read_bytes()
            if consume:
                self._entries.pop(audio_id, None)
                path.unlink(missing_ok=True)
            return data

    def cleanup_expired(self) -> int:
        now = time.monotonic()
        removed = 0
        with self._lock:
            expired_ids = [aid for aid, (p, exp) in self._entries.items() if now > exp or not p.exists()]
            for aid in expired_ids:
                p, _ = self._entries.pop(aid)
                p.unlink(missing_ok=True)
                removed += 1
        return removed

    def clear_all(self) -> None:
        with self._lock:
            for p, _ in self._entries.values():
                p.unlink(missing_ok=True)
            self._entries.clear()


class ConcurrencyLimiter:
    """Non-blocking concurrency guard to protect RAM on Raspberry Pi 5."""

    def __init__(self, max_concurrent: int) -> None:
        self._sem = threading.BoundedSemaphore(max(1, max_concurrent))

    def acquire(self) -> bool:
        return self._sem.acquire(blocking=False)

    def release(self) -> None:
        try:
            self._sem.release()
        except ValueError:
            pass


class BrowserSessionStore:
    """In-memory HttpOnly cookie + CSRF token store for local Voice Lab UI."""

    def __init__(self, ttl_s: float = 3600.0) -> None:
        self.ttl_s = ttl_s
        self._lock = threading.Lock()
        self._sessions: Dict[str, Tuple[str, float]] = {}

    def create(self) -> Tuple[str, str]:
        self._cleanup()
        sid = secrets.token_urlsafe(24)
        csrf = secrets.token_urlsafe(24)
        with self._lock:
            self._sessions[sid] = (csrf, time.monotonic() + self.ttl_s)
        return sid, csrf

    def verify(self, sid: Optional[str], csrf_header: Optional[str], require_csrf: bool) -> bool:
        if not sid:
            return False
        self._cleanup()
        with self._lock:
            item = self._sessions.get(sid)
            if item is None:
                return False
            csrf_expected, exp = item
            if time.monotonic() > exp:
                self._sessions.pop(sid, None)
                return False
        if require_csrf:
            if not csrf_header or not hmac.compare_digest(csrf_header.strip(), csrf_expected):
                return False
        return True

    def revoke(self, sid: Optional[str]) -> None:
        if not sid:
            return
        with self._lock:
            self._sessions.pop(sid, None)

    def _cleanup(self) -> None:
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (_, exp) in self._sessions.items() if now > exp]
            for k in expired:
                self._sessions.pop(k, None)
