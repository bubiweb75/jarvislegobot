"""Deterministic offline fallback responder (Priority 3, never pretends to be an LLM)."""

from __future__ import annotations

from datetime import datetime
from typing import Tuple


class OfflineFallbackProvider:
    """Always-available local Italian fallback when Ollama and Cloud are unavailable."""

    provider_id = "offline_fallback"

    def generate_reply(self, transcript: str, reason: str = "") -> Tuple[str, str]:
        q = " ".join(transcript.lower().split())
        if "che ore sono" in q or "che ora è" in q or "che ora e" in q:
            now = datetime.now().strftime("%H:%M")
            return f"Sono le {now}. Il motore AI è attualmente offline.", self.provider_id
        if any(w in q for w in ("ciao", "buongiorno", "buonasera", "salve")):
            return (
                "Ciao! Al momento il motore AI non è raggiungibile, ma sono operativo in modalità locale.",
                self.provider_id,
            )
        if any(w in q for w in ("stato", "come stai", "ci sei")):
            return (
                "Sono pronto e il sistema locale funziona, ma il motore AI principale non è al momento disponibile.",
                self.provider_id,
            )
        return (
            "Al momento non riesco a contattare il motore AI. Riprova quando il servizio sarà disponibile.",
            self.provider_id,
        )
