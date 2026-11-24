"""Deterministic local Italian time/date intent handler (no LLM/cloud required)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Callable, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


_ITALIAN_DAYS = (
    "lunedì",
    "martedì",
    "mercoledì",
    "giovedì",
    "venerdì",
    "sabato",
    "domenica",
)

_ITALIAN_MONTHS = (
    "",
    "gennaio",
    "febbraio",
    "marzo",
    "aprile",
    "maggio",
    "giugno",
    "luglio",
    "agosto",
    "settembre",
    "ottobre",
    "novembre",
    "dicembre",
)

_PREFIX_RE = re.compile(
    r"^(?:(?:ciao|ehi|hey|salve|ok|buongiorno|buonasera|scusa|scusami|senti)\s+)*(?:(?:jarvis|gervis|giarvis|charvis)\s+)?",
    re.IGNORECASE,
)
_SUFFIX_RE = re.compile(
    r"(?:\s+(?:per favore|per piacere|grazie|adesso|subito|scusa))+$",
    re.IGNORECASE,
)
_PUNCT_RE = re.compile(r"[?!.,;:\"'()«»—\-]+")
_TIME_CORE_RE = re.compile(r"\b(?:che ore sono|che ora sono|che ora [eè]|dimmi l ora|mi dici l ora)\b")
_NON_LOCAL_TIME_HINTS = ("fuso", "treno", "volo", "aereo", "negozio", "apre", "chiude", "inizia", "finisce", "ieri", "domani", "londra", "new york", "tokyo")


@dataclass(frozen=True)
class TimezoneResolution:
    now: datetime
    timezone_label: str
    fallback_used: bool
    diagnostic_note: str


@dataclass(frozen=True)
class LocalIntentResult:
    intent_id: str
    reply_text: str
    provider_used: str = "Local Intent"
    timezone_note: str = ""


def resolve_current_datetime(
    requested_tz: str = "",
    now_provider: Optional[Callable[[Optional[ZoneInfo]], datetime]] = None,
) -> TimezoneResolution:
    """Resolves real system time using ZoneInfo when available, never silently substituting a different TZ."""
    tz_clean = requested_tz.strip()
    if not tz_clean:
        local_now = now_provider(None) if now_provider else datetime.now().astimezone()
        tz_name = str(local_now.tzname() or "OS_LOCAL")
        return TimezoneResolution(
            now=local_now,
            timezone_label=tz_name,
            fallback_used=False,
            diagnostic_note=f"Fuso orario locale OS ({tz_name})",
        )

    if tz_clean.upper() == "UTC":
        utc_now = now_provider(timezone.utc) if now_provider else datetime.now(timezone.utc)
        return TimezoneResolution(
            now=utc_now,
            timezone_label="UTC",
            fallback_used=False,
            diagnostic_note="UTC (datetime.timezone.utc)",
        )

    try:
        zi = ZoneInfo(tz_clean)
        dt = now_provider(zi) if now_provider else datetime.now(zi)
        return TimezoneResolution(
            now=dt,
            timezone_label=tz_clean,
            fallback_used=False,
            diagnostic_note=f"ZoneInfo({tz_clean})",
        )
    except ZoneInfoNotFoundError as exc:
        local_now = now_provider(None) if now_provider else datetime.now().astimezone()
        local_tz_name = str(local_now.tzname() or "")
        # Explicit fallback allowed only if local OS timezone matches or no IANA db exists on Windows
        # and we report explicitly instead of pretending requested_tz was resolved via IANA.
        if tz_clean.lower() in {"europe/rome", "rome", "cet", "cest"} and local_tz_name.upper() in {
            "CET",
            "CEST",
            "W. EUROPE STANDARD TIME",
            "W. EUROPE DAYLIGHT TIME",
            "ORA SOLARE EUROPA OCCIDENTALE",
            "ORA LEGALE EUROPA OCCIDENTALE",
        }:
            return TimezoneResolution(
                now=local_now,
                timezone_label=f"OS_LOCAL({local_tz_name})",
                fallback_used=True,
                diagnostic_note=(
                    f"Database IANA non disponibile per '{tz_clean}'; "
                    f"usato fuso locale OS ({local_tz_name}) equivalente"
                ),
            )
        raise ValueError(
            f"Fuso orario '{tz_clean}' non risolvibile (tzdata assente e fuso OS '{local_tz_name}' diverso)"
        ) from exc


def _normalize_for_intent(text: str) -> str:
    cleaned = _PUNCT_RE.sub(" ", text.strip().lower())
    cleaned = " ".join(cleaned.split())
    cleaned = _PREFIX_RE.sub("", cleaned).strip()
    cleaned = _SUFFIX_RE.sub("", cleaned).strip()
    return " ".join(cleaned.split()).strip()


def _format_time_it(dt: datetime) -> str:
    if dt.minute == 0:
        return f"Sono le {dt.hour} in punto."
    return f"Sono le {dt.hour} e {dt.minute:02d}."


def _format_day_it(dt: datetime) -> str:
    day_name = _ITALIAN_DAYS[dt.weekday()]
    month_name = _ITALIAN_MONTHS[dt.month]
    return f"Oggi è {day_name} {dt.day} {month_name} {dt.year}."


def _format_date_it(dt: datetime) -> str:
    month_name = _ITALIAN_MONTHS[dt.month]
    return f"Oggi è il {dt.day} {month_name} {dt.year}."


class LocalIntentHandler:
    """Matches clear, unambiguous Italian time/date requests."""

    def __init__(
        self,
        timezone_name: str = "",
        now_provider: Optional[Callable[[Optional[ZoneInfo]], datetime]] = None,
    ) -> None:
        self.timezone_name = timezone_name
        self._now_provider = now_provider

    def try_handle(self, transcript: str) -> Optional[LocalIntentResult]:
        q = _normalize_for_intent(transcript)
        if not q:
            return None

        intent_id: Optional[str] = None
        if q in {
            "che ore sono",
            "che ora sono",
            "che ora e",
            "che ora è",
            "dimmi l ora",
            "dimmi che ore sono",
            "dimmi che ora sono",
            "mi dici l ora",
            "mi dici che ore sono",
            "mi dici che ora sono",
            "sai dirmi che ore sono",
            "sai che ore sono",
            "sai dirmi l ora",
            "puoi dirmi che ore sono",
            "puoi dirmi l ora",
        }:
            intent_id = "time"
        elif _TIME_CORE_RE.search(q) and len(q.split()) <= 7 and not any(h in q for h in _NON_LOCAL_TIME_HINTS):
            intent_id = "time"
        elif q in {
            "che giorno e",
            "che giorno è",
            "che giorno e oggi",
            "che giorno è oggi",
            "mi dici che giorno e",
            "mi dici che giorno è",
            "mi dici che giorno e oggi",
            "mi dici che giorno è oggi",
            "dimmi che giorno e",
            "dimmi che giorno è",
            "dimmi che giorno e oggi",
            "dimmi che giorno è oggi",
        }:
            intent_id = "day"
        elif q in {
            "che data e",
            "che data è",
            "che data e oggi",
            "che data è oggi",
            "qual e la data",
            "qual è la data",
            "qual e la data di oggi",
            "qual è la data di oggi",
            "che data abbiamo oggi",
            "quanti ne abbiamo oggi",
            "mi dici la data",
            "mi dici la data di oggi",
            "dimmi la data",
            "dimmi la data di oggi",
        }:
            intent_id = "date"

        if intent_id is None:
            return None

        try:
            tz_res = resolve_current_datetime(self.timezone_name, now_provider=self._now_provider)
        except ValueError as exc:
            return LocalIntentResult(
                intent_id=intent_id,
                reply_text=f"Non riesco a verificare il fuso orario configurato: {exc}.",
                timezone_note=str(exc),
            )

        if intent_id == "time":
            reply = _format_time_it(tz_res.now)
        elif intent_id == "day":
            reply = _format_day_it(tz_res.now)
        else:
            reply = _format_date_it(tz_res.now)

        return LocalIntentResult(
            intent_id=intent_id,
            reply_text=reply,
            provider_used="Local Intent",
            timezone_note=tz_res.diagnostic_note,
        )
