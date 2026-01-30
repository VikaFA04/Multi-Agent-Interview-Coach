from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class Memory:
    """Memory = "состояние" интервью"""

    # последние n обменов, чтобы помнить контекст (включая "3 сообщения назад")
    transcript: List[Dict[str, str]] = field(default_factory=list)

    # id заданных вопросов (чтобы не повторяться)
    asked_question_ids: List[str] = field(default_factory=list)
    # темы заданных вопросов (помогает чередовать темы)
    asked_topics: List[str] = field(default_factory=list)

    # адаптивность: общий уровень сложности
    difficulty: int = 1  # 1..5
    correct_streak: int = 0
    incorrect_streak: int = 0

    # сигналы для устойчивости и soft skills
    signals: Dict[str, Any] = field(
        default_factory=lambda: {
            "offtopic_count": 0,
            "hallucination_flags": 0,
            "role_reversal_count": 0,
            "clarity_votes": [],
            "honesty_flags": 0,
            "engagement_flags": 0,
        }
    )

    # история оценок по хард-скиллам (по каждому вопросу)
    evaluations: List[Dict[str, Any]] = field(default_factory=list)

    def add_exchange(self, interviewer_msg: str, user_msg: str) -> None:
        self.transcript.append({"interviewer": interviewer_msg, "user": user_msg})

        # держим только последние 12, чтобы не раздувать состояние
        if len(self.transcript) > 12:
            self.transcript = self.transcript[-12:]

    def note_eval(self, item: Dict[str, Any]) -> None:
        """Сохраняем результат оценки ответа для финального отчёта"""
        self.evaluations.append(item)

    def bump_difficulty(self, delta: int) -> None:
        """Уровень сложности всегда в пределах от 1 до 5"""
        self.difficulty = max(1, min(5, self.difficulty + delta))
