from __future__ import annotations

import os
import requests
from typing import List, Optional

from .base import Message


class OpenAICompatibleLLM:

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_s: int = 60,
    ):
        # примеры:
        # base_url="http://localhost:8000/v1"
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL", "local-model")
        # Многие локальные сервера игнорят ключ, но пусть будет единый интерфейс
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.timeout_s = timeout_s

    def generate(self, messages: List[Message], temperature: float = 0.2) -> str:
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout_s)
        resp.raise_for_status()

        data = resp.json()
        # ожидаем стандартный формат: choices[0].message.content
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            # если сервер вернул чуть другой формат
            return str(data)
