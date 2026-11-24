"""Hybrid AI Router supporting DISABLED, LOCAL_ONLY, CLOUD_ONLY, LOCAL_FIRST, and CLOUD_FIRST."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import re
import sys
import threading
import time
from typing import Callable, Deque, Dict, List, Optional, Tuple

import httpx

_VOICE_AI_DIR = Path(__file__).resolve().parent.parent
if str(_VOICE_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_VOICE_AI_DIR))

from ai_providers import AIProvider, AIProviderError  # noqa: E402

from .config import BridgeConfig, VALID_AI_MODES
from .conversation import estimate_tokens
from .local_intents import LocalIntentHandler
from .offline_fallback import OfflineFallbackProvider
from .security import validate_cloud_url, validate_provider_url


@dataclass(frozen=True)
class AIRouteResult:
    text: str
    provider_used: str
    fallback_used: bool
    reason: str
    latency_ms: float
    timezone_note: str = ""


class OllamaRouterClient:
    """Local Ollama client with separate probe, connect, and generation timeouts."""

    def __init__(
        self,
        base_url: str,
        model: str,
        probe_timeout_s: float = 1.5,
        connect_timeout_s: float = 2.0,
        generate_timeout_s: float = 20.0,
        max_tokens: int = 120,
        temperature: float = 0.5,
        num_ctx: int = 2048,
        keep_alive: str = "10m",
        probe_cache_ttl_s: Optional[float] = None,
        allowed_hosts: Tuple[str, ...] = (),
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.base_url = validate_provider_url(base_url, allowed_hosts=allowed_hosts, allow_public=False)
        self.model = model.strip()
        self.probe_timeout_s = max(0.2, probe_timeout_s)
        self.connect_timeout_s = max(0.2, connect_timeout_s)
        self.generate_timeout_s = max(0.5, generate_timeout_s)
        self.max_tokens = max(32, max_tokens)
        self.temperature = max(0.0, min(2.0, temperature))
        self.num_ctx = max(512, num_ctx)
        self.keep_alive = keep_alive.strip() or "10m"
        self._transport = transport
        self._probe_cache_ttl_s = (0.0 if transport is not None else 60.0) if probe_cache_ttl_s is None else max(0.0, probe_cache_ttl_s)
        self._probe_lock = threading.Lock()
        self._last_probe_ok_at: float = 0.0
        self._last_probe_msg: str = ""
        self._prewarm_lock = threading.Lock()
        self._prewarm_started = False
        self._client = httpx.Client(transport=self._transport)

    def close(self) -> None:
        self._client.close()

    def prewarm(self) -> bool:
        """Non-duplicating best-effort model preload (returns True if preload succeeded)."""
        with self._prewarm_lock:
            if self._prewarm_started:
                return False
            self._prewarm_started = True
        try:
            ok, _ = self.probe(use_cache=False)
            if not ok:
                return False
            resp = self._client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [],
                    "stream": False,
                    "keep_alive": self.keep_alive,
                    "options": {"num_ctx": self.num_ctx},
                },
                timeout=httpx.Timeout(connect=self.connect_timeout_s, read=max(10.0, self.generate_timeout_s), write=5.0, pool=self.connect_timeout_s),
            )
            resp.raise_for_status()
            return True
        except Exception:
            return False

    def probe(self, use_cache: bool = False) -> Tuple[bool, str]:
        if not self.model:
            return False, "Modello Ollama non configurato"
        if use_cache and self._probe_cache_ttl_s > 0:
            with self._probe_lock:
                if (time.monotonic() - self._last_probe_ok_at) < self._probe_cache_ttl_s and self._last_probe_msg:
                    return True, self._last_probe_msg
        try:
            resp = self._client.get(f"{self.base_url}/api/tags", timeout=self.probe_timeout_s)
            resp.raise_for_status()
            models = [m.get("name", "") for m in resp.json().get("models", []) if m.get("name")]
            if not models:
                return False, "Ollama attivo ma nessun modello installato"
            target = self.model
            if target not in models and f"{target}:latest" not in models:
                return False, f"Modello Ollama '{target}' non installato localmente"
            msg = f"Ollama attivo ({len(models)} modelli, selezionato {target})"
            with self._probe_lock:
                self._last_probe_ok_at = time.monotonic()
                self._last_probe_msg = msg
            return True, msg
        except httpx.TimeoutException:
            return False, "Ollama timeout probe"
        except httpx.HTTPError as exc:
            return False, f"Ollama non raggiungibile ({exc.__class__.__name__})"
        except ValueError:
            return False, "Risposta Ollama non valida"

    def generate(
        self,
        messages: List[Dict[str, str]],
        timeout_override_s: Optional[float] = None,
        max_tokens_override: Optional[int] = None,
    ) -> str:
        ok, status = self.probe(use_cache=True)
        if not ok:
            raise AIProviderError(status)

        read_timeout = self.generate_timeout_s
        if timeout_override_s is not None:
            read_timeout = max(0.2, min(read_timeout, timeout_override_s))

        timeout = httpx.Timeout(
            connect=min(self.connect_timeout_s, read_timeout),
            read=read_timeout,
            write=min(5.0, read_timeout),
            pool=min(self.connect_timeout_s, read_timeout),
        )
        num_predict = max(32, max_tokens_override) if max_tokens_override is not None else self.max_tokens
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "num_predict": num_predict,
                "num_ctx": self.num_ctx,
                "temperature": self.temperature,
            },
        }
        try:
            resp = self._client.post(f"{self.base_url}/api/chat", json=payload, timeout=timeout)
            if resp.status_code == 404:
                with self._probe_lock:
                    self._last_probe_ok_at = 0.0
                raise AIProviderError(f"Modello Ollama '{self.model}' non trovato")
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException as exc:
            with self._probe_lock:
                self._last_probe_ok_at = 0.0
            raise AIProviderError("Ollama timeout generazione") from exc
        except httpx.HTTPError as exc:
            with self._probe_lock:
                self._last_probe_ok_at = 0.0
            raise AIProviderError(f"Ollama errore HTTP: {exc.__class__.__name__}") from exc
        except ValueError as exc:
            raise AIProviderError("Ollama risposta JSON non valida") from exc

        text = str(data.get("message", {}).get("content", "")).strip()
        if not text:
            raise AIProviderError("Ollama risposta vuota")
        if data.get("done_reason") == "length" and text[-1] not in ".!?":
            matches = list(re.finditer(r"[.!?](?=\s|$)", text))
            if matches:
                last_end = matches[-1].start()
                if last_end >= len(text) // 3:
                    trimmed = text[: last_end + 1].strip()
                    if trimmed:
                        text = trimmed
        return text


class CloudAIClient:
    """OpenAI-compatible remote Cloud AI client with HTTPS/SSRF guards and usage limits."""

    def __init__(
        self,
        config: BridgeConfig,
        custom_provider: Optional[AIProvider] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.enabled = config.cloud_enabled
        self.provider_name = (config.cloud_provider or "openai").strip().lower()
        self.model = config.cloud_model.strip()
        self._api_key = config.cloud_api_key.strip()
        self.timeout_s = max(0.5, config.cloud_timeout_s)
        self.max_tokens = max(32, config.cloud_max_tokens)
        self.temperature = config.cloud_temperature
        self.max_requests_per_hour = max(0, config.cloud_max_requests_per_hour)
        self.max_daily_tokens = max(0, config.cloud_max_daily_tokens)
        self._transport = transport
        self._custom_provider = custom_provider
        self._url_error: Optional[str] = None
        self.base_url = config.cloud_base_url.strip().rstrip("/")

        self._usage_lock = threading.Lock()
        self._request_timestamps: Deque[float] = deque()
        self._token_records: Deque[Tuple[float, int]] = deque()
        self._total_requests = 0
        self._total_tokens = 0

        if custom_provider is None:
            try:
                self.base_url = validate_cloud_url(
                    config.cloud_base_url,
                    allowed_hosts=config.allowed_provider_hosts,
                )
            except Exception as exc:
                self._url_error = str(exc)

    def _prune_usage_locked(self, now: float) -> None:
        hour_ago = now - 3600.0
        while self._request_timestamps and self._request_timestamps[0] < hour_ago:
            self._request_timestamps.popleft()
        day_ago = now - 86400.0
        while self._token_records and self._token_records[0][0] < day_ago:
            self._token_records.popleft()

    def _check_usage_limits(self) -> Optional[str]:
        now = time.time()
        with self._usage_lock:
            self._prune_usage_locked(now)
            if self.max_requests_per_hour > 0 and len(self._request_timestamps) >= self.max_requests_per_hour:
                return "Limite orario richieste Cloud raggiunto"
            if self.max_daily_tokens > 0:
                daily_tokens = sum(tok for _, tok in self._token_records)
                if daily_tokens >= self.max_daily_tokens:
                    return "Limite giornaliero token Cloud raggiunto"
        return None

    def _record_usage(self, tokens_used: int) -> None:
        now = time.time()
        with self._usage_lock:
            self._prune_usage_locked(now)
            self._request_timestamps.append(now)
            self._token_records.append((now, max(0, tokens_used)))
            self._total_requests += 1
            self._total_tokens += max(0, tokens_used)

    def get_usage_metrics(self) -> Dict[str, int]:
        now = time.time()
        with self._usage_lock:
            self._prune_usage_locked(now)
            return {
                "requests_last_hour": len(self._request_timestamps),
                "tokens_last_24h": sum(tok for _, tok in self._token_records),
                "total_requests": self._total_requests,
                "total_tokens": self._total_tokens,
            }

    def is_configured_and_enabled(self) -> Tuple[bool, str]:
        if not self.enabled:
            return False, "Cloud disabilitato da configurazione"
        if self._url_error:
            return False, self._url_error
        if self._custom_provider is not None:
            return self._custom_provider.is_available()
        if not self._api_key:
            return False, "API key Cloud non configurata"
        if not self.model:
            return False, "Modello Cloud non configurato"
        limit_err = self._check_usage_limits()
        if limit_err:
            return False, limit_err
        return True, f"Cloud {self.provider_name} pronto ({self.model})"

    def generate(self, messages: List[Dict[str, str]], timeout_override_s: Optional[float] = None) -> str:
        ok, reason = self.is_configured_and_enabled()
        if not ok:
            raise AIProviderError(reason)

        if self._custom_provider is not None:
            resp = self._custom_provider.generate(messages, model=self.model)
            text = (resp.text or "").strip()
            if not text:
                raise AIProviderError("Cloud risposta vuota")
            est = sum(estimate_tokens(m.get("content", "")) for m in messages) + estimate_tokens(text)
            self._record_usage(est)
            return text

        eff_timeout = self.timeout_s
        if timeout_override_s is not None:
            eff_timeout = max(0.2, min(eff_timeout, timeout_override_s))

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, object] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature

        try:
            with httpx.Client(timeout=eff_timeout, transport=self._transport) as client:
                resp = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if resp.status_code in (401, 403):
                    raise AIProviderError(f"Autenticazione Cloud rifiutata (HTTP {resp.status_code})")
                if resp.status_code == 404:
                    raise AIProviderError(f"Endpoint o modello Cloud '{self.model}' non trovato (HTTP 404)")
                if resp.status_code == 429:
                    raise AIProviderError("Rate limit o quota Cloud superata (HTTP 429)")
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise AIProviderError(f"Timeout Cloud API ({eff_timeout:.1f}s)") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError(f"Errore HTTP Cloud: {exc.__class__.__name__}") from exc
        except ValueError as exc:
            raise AIProviderError("Risposta JSON Cloud non valida") from exc

        choices = data.get("choices") or []
        text = str(choices[0].get("message", {}).get("content", "")).strip() if choices else ""
        if not text:
            raise AIProviderError("Cloud risposta vuota")

        usage = data.get("usage") or {}
        total_tok = usage.get("total_tokens")
        if not isinstance(total_tok, int) or total_tok <= 0:
            total_tok = sum(estimate_tokens(m.get("content", "")) for m in messages) + estimate_tokens(text)
        self._record_usage(total_tok)
        return text


class AIRouter:
    """Selects AI provider strictly by configured ai_mode with optional explicit fallback."""

    def __init__(
        self,
        config: BridgeConfig,
        ollama_client: Optional[OllamaRouterClient] = None,
        cloud_client: Optional[CloudAIClient] = None,
        offline_provider: Optional[OfflineFallbackProvider] = None,
        local_intents: Optional[LocalIntentHandler] = None,
    ) -> None:
        self.config = config
        mode = (config.ai_mode or "DISABLED").strip().upper()
        self.ai_mode = mode if mode in VALID_AI_MODES else "DISABLED"
        self.fallback_enabled = bool(config.ai_fallback_enabled)
        self.ai_timeout_s = max(1.0, float(config.ai_timeout_s))
        self.local_intents = local_intents or LocalIntentHandler(timezone_name=config.timezone)

        ollama_allowed_by_mode = self.ai_mode in {"LOCAL_ONLY", "LOCAL_FIRST"} or (
            self.ai_mode == "CLOUD_FIRST" and self.fallback_enabled
        )
        if ollama_client is not None:
            self.ollama: Optional[OllamaRouterClient] = ollama_client
        elif ollama_allowed_by_mode and (config.ollama_enabled or self.ai_mode in {"LOCAL_ONLY", "LOCAL_FIRST"}):
            self.ollama = OllamaRouterClient(
                base_url=config.ollama_url,
                model=config.ollama_model,
                probe_timeout_s=config.ollama_probe_timeout_s,
                connect_timeout_s=config.ollama_connect_timeout_s,
                generate_timeout_s=config.ollama_generate_timeout_s,
                max_tokens=config.ollama_max_tokens,
                temperature=config.ollama_temperature,
                num_ctx=config.ollama_num_ctx,
                keep_alive=config.ollama_keep_alive,
                allowed_hosts=config.allowed_provider_hosts,
            )
        else:
            self.ollama = None

        self.cloud = cloud_client or CloudAIClient(config)
        self.offline = offline_provider or OfflineFallbackProvider()

    def close(self) -> None:
        if self.ollama is not None:
            self.ollama.close()

    def _try_ollama(
        self,
        messages: List[Dict[str, str]],
        reasons: List[str],
        remaining_s: float,
        max_tokens_override: Optional[int] = None,
    ) -> Optional[str]:
        if self.ollama is None:
            reasons.append("ollama:disabled")
            return None
        if remaining_s <= 0.1:
            reasons.append("ollama:budget_exceeded")
            return None
        try:
            return self.ollama.generate(
                messages,
                timeout_override_s=remaining_s,
                max_tokens_override=max_tokens_override,
            )
        except AIProviderError as exc:
            reasons.append(f"ollama:{exc}")
            return None

    def _try_cloud(
        self,
        messages: List[Dict[str, str]],
        reasons: List[str],
        remaining_s: float,
    ) -> Optional[str]:
        ok_cloud, cloud_msg = self.cloud.is_configured_and_enabled()
        if not ok_cloud:
            reasons.append(f"cloud:{cloud_msg}")
            return None
        if remaining_s <= 0.1:
            reasons.append("cloud:budget_exceeded")
            return None
        try:
            return self.cloud.generate(messages, timeout_override_s=remaining_s)
        except AIProviderError as exc:
            reasons.append(f"cloud:{exc}")
            return None

    def route(
        self,
        messages: List[Dict[str, str]],
        transcript: str,
        cancel_check: Optional[Callable[[], None]] = None,
        max_tokens_override: Optional[int] = None,
    ) -> AIRouteResult:
        t0 = time.monotonic()
        deadline = t0 + self.ai_timeout_s
        reasons: List[str] = []

        # Priority 0: Deterministic Local Intents (always active)
        local_res = self.local_intents.try_handle(transcript)
        if local_res is not None:
            return AIRouteResult(
                text=local_res.reply_text,
                provider_used=local_res.provider_used,
                fallback_used=False,
                reason=f"local_intent:{local_res.intent_id}",
                latency_ms=(time.monotonic() - t0) * 1000.0,
                timezone_note=local_res.timezone_note,
            )

        if cancel_check:
            cancel_check()

        if self.ai_mode == "DISABLED":
            reasons.append("ai_mode:DISABLED")
        elif self.ai_mode == "LOCAL_ONLY":
            reply = self._try_ollama(messages, reasons, deadline - time.monotonic(), max_tokens_override=max_tokens_override)
            if cancel_check:
                cancel_check()
            if reply is not None:
                return AIRouteResult(
                    text=reply,
                    provider_used=f"ollama:{self.ollama.model}",  # type: ignore[union-attr]
                    fallback_used=False,
                    reason="primary_ollama",
                    latency_ms=(time.monotonic() - t0) * 1000.0,
                )
        elif self.ai_mode == "CLOUD_ONLY":
            reply = self._try_cloud(messages, reasons, deadline - time.monotonic())
            if cancel_check:
                cancel_check()
            if reply is not None:
                return AIRouteResult(
                    text=reply,
                    provider_used=f"cloud:{self.cloud.provider_name}",
                    fallback_used=False,
                    reason="primary_cloud",
                    latency_ms=(time.monotonic() - t0) * 1000.0,
                )
        elif self.ai_mode == "LOCAL_FIRST":
            reply = self._try_ollama(messages, reasons, deadline - time.monotonic(), max_tokens_override=max_tokens_override)
            if cancel_check:
                cancel_check()
            if reply is not None:
                return AIRouteResult(
                    text=reply,
                    provider_used=f"ollama:{self.ollama.model}",  # type: ignore[union-attr]
                    fallback_used=False,
                    reason="primary_ollama",
                    latency_ms=(time.monotonic() - t0) * 1000.0,
                )
            if self.fallback_enabled:
                reply = self._try_cloud(messages, reasons, deadline - time.monotonic())
                if cancel_check:
                    cancel_check()
                if reply is not None:
                    return AIRouteResult(
                        text=reply,
                        provider_used=f"cloud:{self.cloud.provider_name}",
                        fallback_used=True,
                        reason=";".join(reasons),
                        latency_ms=(time.monotonic() - t0) * 1000.0,
                    )
            else:
                reasons.append("fallback:disabled")
        elif self.ai_mode == "CLOUD_FIRST":
            reply = self._try_cloud(messages, reasons, deadline - time.monotonic())
            if cancel_check:
                cancel_check()
            if reply is not None:
                return AIRouteResult(
                    text=reply,
                    provider_used=f"cloud:{self.cloud.provider_name}",
                    fallback_used=False,
                    reason="primary_cloud",
                    latency_ms=(time.monotonic() - t0) * 1000.0,
                )
            if self.fallback_enabled:
                reply = self._try_ollama(messages, reasons, deadline - time.monotonic(), max_tokens_override=max_tokens_override)
                if cancel_check:
                    cancel_check()
                if reply is not None:
                    return AIRouteResult(
                        text=reply,
                        provider_used=f"ollama:{self.ollama.model}",  # type: ignore[union-attr]
                        fallback_used=True,
                        reason=";".join(reasons),
                        latency_ms=(time.monotonic() - t0) * 1000.0,
                    )
            else:
                reasons.append("fallback:disabled")

        # Priority 3: Offline Fallback (always available)
        reply, prov = self.offline.generate_reply(transcript, reason=";".join(reasons))
        return AIRouteResult(
            text=reply,
            provider_used=prov,
            fallback_used=True,
            reason=";".join(reasons),
            latency_ms=(time.monotonic() - t0) * 1000.0,
        )
