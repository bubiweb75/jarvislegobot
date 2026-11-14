"""Session-scoped Conversation Manager (no disk persistence by default)."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class ConversationManager:
    """Maintains bounded in-memory conversation history for the active session."""

    def __init__(self, system_prompt: str, max_turns: int = 6) -> None:
        self.system_prompt = system_prompt.strip()
        self.max_turns = max(1, max_turns)
        self._history: List[ChatMessage] = []

    def set_system_prompt(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt.strip()

    def set_max_turns(self, max_turns: int) -> None:
        self.max_turns = max(1, max_turns)
        self._trim()

    def add_user_message(self, text: str) -> None:
        cleaned = text.strip()
        if cleaned:
            self._history.append(ChatMessage(role="user", content=cleaned))
            self._trim()

    def add_assistant_message(self, text: str) -> None:
        cleaned = text.strip()
        if cleaned:
            self._history.append(ChatMessage(role="assistant", content=cleaned))
            self._trim()

    def clear(self) -> None:
        self._history.clear()

    def get_messages_for_model(self) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})
        return messages

    def turn_count(self) -> int:
        return sum(1 for m in self._history if m.role == "user")

    def _trim(self) -> None:
        max_msgs = self.max_turns * 2
        if len(self._history) > max_msgs:
            self._history = self._history[-max_msgs:]
