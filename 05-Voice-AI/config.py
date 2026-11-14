"""Configuration Manager for JARVIS Voice & AI Hybrid."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SYSTEM_PROMPT = (
    "Sei JARVIS, un piccolo robot da compagnia da scrivania intelligente, "
    "amichevole, curioso e leggermente spiritoso. Rispondi in italiano in modo "
    "naturale e conciso."
)


@dataclass
class JarvisConfig:
    ai_provider: str = "ollama"  # "demo" | "ollama" | "openai"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout_s: float = 45.0

    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout_s: float = 25.0

    max_history_turns: int = 6

    tts_voice: str = "JARVIS Amichetto (Piper Riccardo)"
    tts_rate: int = 1
    tts_volume: int = 100
    piper_pitch_semitones: float = 5.0
    piper_speed: float = 1.21
    piper_noise_scale: float = 1.10
    piper_robot_mix: float = 0.0

    stt_language: str = "it-IT"
    stt_timeout_s: float = 10.0
    whisper_model_size: str = "base"

    system_prompt_file: str = "prompts/jarvis_system_it.txt"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT

    def get_openai_api_key(self) -> str:
        """Reads OpenAI API key strictly from environment (never persisted in config JSON)."""
        return os.environ.get("OPENAI_API_KEY", "").strip()

    def load_system_prompt(self, base_dir: Path = BASE_DIR) -> str:
        p = Path(self.system_prompt_file)
        if not p.is_absolute():
            p = base_dir / p
        if p.exists():
            text = p.read_text(encoding="utf-8").strip()
            if text:
                self.system_prompt = text
        return self.system_prompt


def load_config(config_path: Optional[Path] = None, env_path: Optional[Path] = None) -> JarvisConfig:
    if load_dotenv is not None:
        target_env = env_path or (BASE_DIR / ".env")
        if target_env.exists():
            load_dotenv(target_env, override=False)

    cfg = JarvisConfig()
    target_cfg = config_path or (BASE_DIR / "config.local.json")
    if not target_cfg.exists():
        fallback = BASE_DIR / "config.example.json"
        if fallback.exists():
            target_cfg = fallback

    if target_cfg.exists():
        try:
            raw = json.loads(target_cfg.read_text(encoding="utf-8"))
            for field_name in (
                "ai_provider",
                "ollama_url",
                "ollama_model",
                "ollama_timeout_s",
                "openai_model",
                "openai_base_url",
                "openai_timeout_s",
                "max_history_turns",
                "tts_voice",
                "tts_rate",
                "tts_volume",
                "piper_pitch_semitones",
                "piper_speed",
                "piper_noise_scale",
                "piper_robot_mix",
                "stt_language",
                "stt_timeout_s",
                "whisper_model_size",
                "system_prompt_file",
            ):
                if field_name in raw and raw[field_name] is not None:
                    setattr(cfg, field_name, raw[field_name])
        except (OSError, json.JSONDecodeError):
            pass

    if os.environ.get("JARVIS_AI_PROVIDER"):
        cfg.ai_provider = os.environ["JARVIS_AI_PROVIDER"].strip().lower()
    if os.environ.get("JARVIS_OLLAMA_URL"):
        cfg.ollama_url = os.environ["JARVIS_OLLAMA_URL"].strip()
    if os.environ.get("JARVIS_OLLAMA_MODEL"):
        cfg.ollama_model = os.environ["JARVIS_OLLAMA_MODEL"].strip()
    if os.environ.get("JARVIS_OPENAI_MODEL"):
        cfg.openai_model = os.environ["JARVIS_OPENAI_MODEL"].strip()
    if os.environ.get("JARVIS_OPENAI_BASE_URL"):
        cfg.openai_base_url = os.environ["JARVIS_OPENAI_BASE_URL"].strip()

    cfg.load_system_prompt()
    return cfg
