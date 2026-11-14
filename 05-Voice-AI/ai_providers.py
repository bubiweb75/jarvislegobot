"""Hybrid AI Providers (Demo, Ollama Local, OpenAI-Compatible Online)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple

import httpx


class AIProviderError(RuntimeError):
    """Recoverable or configuration error raised by an AI provider."""


@dataclass
class AIResponse:
    text: str
    provider_name: str
    sentiment: str = "neutral"  # "neutral" | "happy"


class AIProvider(ABC):
    provider_id: str = "base"
    display_name: str = "Base"

    @abstractmethod
    def is_available(self) -> Tuple[bool, str]:
        """Returns (available, human_readable_status)."""

    @abstractmethod
    def list_models(self) -> List[str]:
        """Returns available model identifiers."""

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], model: str = "") -> AIResponse:
        """Generates an assistant response from conversation messages."""


class DemoAIProvider(AIProvider):
    """Offline rule-based Italian companion provider for immediate Demo Mode testing."""

    provider_id = "demo"
    display_name = "Demo Mode (Locale Offline)"

    def is_available(self) -> Tuple[bool, str]:
        return True, "Demo Mode pronta (nessuna rete o chiave richiesta)"

    def list_models(self) -> List[str]:
        return ["jarvis-demo-it"]

    def generate(self, messages: List[Dict[str, str]], model: str = "") -> AIResponse:
        last_user = ""
        prev_user = ""
        for msg in messages:
            if msg.get("role") == "user":
                prev_user = last_user
                last_user = msg.get("content", "").strip()

        q = last_user.lower()
        if any(w in q for w in ("ciao", "buongiorno", "buonasera", "salve", "ehi")):
            return AIResponse(
                text="Ciao! Sono JARVIS, il tuo compagno da scrivania. Come posso aiutarti oggi?",
                provider_name=self.display_name,
                sentiment="happy",
            )
        if any(w in q for w in ("grazie", "bravo", "ottimo", "fantastico", "perfetto")):
            return AIResponse(
                text="Mi fa davvero piacere! Sono qui sulla scrivania ogni volta che ti serve una mano.",
                provider_name=self.display_name,
                sentiment="happy",
            )
        if "come stai" in q or "tutto bene" in q:
            return AIResponse(
                text="I miei pixel sono belli carichi e gli occhi OLED funzionano alla grande. Tu come stai?",
                provider_name=self.display_name,
                sentiment="happy",
            )
        if "chi sei" in q or "come ti chiami" in q:
            return AIResponse(
                text="Sono JARVIS AI Desk Buddy, un piccolo robot da scrivania in modalità demo locale.",
                provider_name=self.display_name,
                sentiment="neutral",
            )
        if any(w in q for w in ("prima", "precedente", "ricordi", "detto")) and prev_user:
            return AIResponse(
                text=f"Certo, poco fa mi hai chiesto: \"{prev_user}\". Sto conservando il contesto di questa sessione!",
                provider_name=self.display_name,
                sentiment="neutral",
            )
        if "?" in q:
            return AIResponse(
                text=(
                    f"Ottima domanda su \"{last_user}\"! In Demo Mode simulo la risposta localmente; "
                    "quando collegherai Ollama o un'API potremo approfondirla insieme."
                ),
                provider_name=self.display_name,
                sentiment="neutral",
            )
        return AIResponse(
            text=f"Ho ricevuto: \"{last_user}\". Tutto il flusso voce, occhi e contesto sta rispondendo correttamente!",
            provider_name=self.display_name,
            sentiment="neutral",
        )


class OllamaProvider(AIProvider):
    """Local Ollama HTTP API provider (default http://localhost:11434)."""

    provider_id = "ollama"
    display_name = "Ollama (Locale)"

    def __init__(self, base_url: str = "http://localhost:11434", timeout_s: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def is_available(self) -> Tuple[bool, str]:
        try:
            with httpx.Client(timeout=min(2.5, self.timeout_s)) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = [m.get("name", "") for m in resp.json().get("models", []) if m.get("name")]
                if not models:
                    return True, "Ollama attivo ma nessun modello installato"
                return True, f"Ollama attivo ({len(models)} modelli disponibili)"
        except httpx.TimeoutException:
            return False, f"Ollama non raggiungibile su {self.base_url} (timeout)"
        except httpx.HTTPError as exc:
            return False, f"Ollama non disponibile su {self.base_url} ({exc.__class__.__name__})"

    def list_models(self) -> List[str]:
        try:
            with httpx.Client(timeout=min(3.0, self.timeout_s)) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                return [m.get("name", "") for m in resp.json().get("models", []) if m.get("name")]
        except httpx.HTTPError:
            return []

    def generate(self, messages: List[Dict[str, str]], model: str = "") -> AIResponse:
        chosen_model = model.strip()
        if not chosen_model:
            models = self.list_models()
            if not models:
                raise AIProviderError(
                    f"Ollama non raggiungibile o nessun modello installato su {self.base_url}. "
                    "Non passo al cloud automaticamente."
                )
            chosen_model = models[0]

        payload = {
            "model": chosen_model,
            "messages": messages,
            "stream": False,
        }
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code == 404:
                    raise AIProviderError(f"Modello Ollama '{chosen_model}' non trovato localmente.")
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise AIProviderError(f"Timeout Ollama ({self.timeout_s:.0f}s) durante la risposta.") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError(
                f"Errore connessione Ollama su {self.base_url}: {exc.__class__.__name__}"
            ) from exc

        text = data.get("message", {}).get("content", "").strip()
        if not text:
            raise AIProviderError("Ollama ha restituito una risposta vuota.")
        return AIResponse(text=text, provider_name=f"Ollama ({chosen_model})", sentiment="neutral")


class OpenAIProvider(AIProvider):
    """Online OpenAI-compatible Chat Completions provider (requires explicit confirmation)."""

    provider_id = "openai"
    display_name = "OpenAI API (Online)"

    def __init__(
        self,
        api_key_getter,
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4o-mini",
        timeout_s: float = 25.0,
    ) -> None:
        self._api_key_getter = api_key_getter
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout_s = timeout_s
        self.cloud_confirmed = False

    def set_cloud_confirmed(self, confirmed: bool) -> None:
        self.cloud_confirmed = confirmed

    def is_available(self) -> Tuple[bool, str]:
        key = self._api_key_getter()
        if not key:
            return False, "OPENAI_API_KEY non configurata"
        if not self.cloud_confirmed:
            return False, "Conferma esplicita richiesta prima di usare l'API online"
        return True, "OpenAI API pronta e confermata"

    def list_models(self) -> List[str]:
        return [self.default_model, "gpt-4o-mini", "gpt-4.1-mini"]

    def generate(self, messages: List[Dict[str, str]], model: str = "") -> AIResponse:
        key = self._api_key_getter()
        if not key:
            raise AIProviderError("API key OpenAI assente (imposta OPENAI_API_KEY nel file .env).")
        if not self.cloud_confirmed:
            raise AIProviderError("Chiamata cloud bloccata: attiva la conferma esplicita API online nella GUI.")

        chosen_model = model.strip() or self.default_model
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": chosen_model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 220,
        }
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                resp = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if resp.status_code == 401:
                    raise AIProviderError("API key OpenAI non valida o scaduta (HTTP 401).")
                if resp.status_code == 429:
                    raise AIProviderError("Limite richieste o quota OpenAI superata (HTTP 429).")
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise AIProviderError(f"Timeout API OpenAI ({self.timeout_s:.0f}s).") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError(f"Errore HTTP API OpenAI: {exc.__class__.__name__}") from exc

        choices = data.get("choices") or []
        text = choices[0].get("message", {}).get("content", "").strip() if choices else ""
        if not text:
            raise AIProviderError("Risposta vuota ricevuta dall'API online.")
        return AIResponse(text=text, provider_name=f"OpenAI ({chosen_model})", sentiment="neutral")
