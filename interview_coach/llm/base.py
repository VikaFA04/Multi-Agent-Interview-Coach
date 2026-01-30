from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol


@dataclass
class Message:
    role: str
    content: str


class LLM(Protocol):

    def generate(self, messages: List[Message], temperature: float = 0.2) -> str:
        ...
