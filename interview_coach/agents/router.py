from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import re


# команды остановки интервью
STOP_PATTERNS = [
    r"^стоп интервью\b",
    r"^стоп игра\.?\s*давай фидбэк\.?$",
    r"^давай фидбэк\.?$",
]


def is_stop(text: str) -> bool:
    """проверяем, попросил ли кандидат завершить интервью и дать фидбэк."""
    t = text.strip().lower()
    return any(re.search(p, t) for p in STOP_PATTERNS)


@dataclass
class RouteDecision:
    route: str  # stop | role_reversal | hallucination | offtopic | evaluate
    flags: Dict[str, bool]
    note: str


class RouterAgent:

    def decide(self, user_text: str) -> RouteDecision:
        t = user_text.strip().lower()

        # 1) стоп — сразу финальный отчёт
        if is_stop(user_text):
            return RouteDecision("stop", {"stop": True}, "User requested to stop interview.")

        # 2) простые эвристики для робастности
        flags = {
            "offtopic": any(k in t for k in ["погода", "дожд", "снег", "политик", "выбор", "котик", "мем", "анекдот"]),
            # ловушка: "Python 4.0 уберут for..."
            "hallucination": any(k in t for k in ["python 4.0", "уберут циклы for", "циклы for уберут", "заменят на нейронные связи"]),
            # role reversal — кандидат задаёт вопросы про работу/процессы/стек
            "role_reversal": ("?" in t) and any(k in t for k in ["какие задачи", "испытатель", "микросервис", "стек", "команда", "процессы"]),
        }

        # 3) приоритеты: сначала role reversal, потом галлюцинации, потом оффтоп
        if flags["role_reversal"]:
            return RouteDecision("role_reversal", flags, "Candidate asked about the job; answer briefly then resume interview.")
        if flags["hallucination"]:
            return RouteDecision("hallucination", flags, "Detected likely false/absurd claim; challenge politely and continue.")
        if flags["offtopic"]:
            return RouteDecision("offtopic", flags, "Off-topic detected; steer back to interview.")

        # 4) стандартный путь: техническая оценка + следующий вопрос
        return RouteDecision("evaluate", flags, "Proceed with evaluation & next question selection.")
