from __future__ import annotations

import re
from typing import Dict, Any, List


I_DONT_KNOW_PATTERNS = [
    r"не знаю",
    r"не уверен",
    r"затрудняюсь",
    r"без понятия",
]


def _norm(s: str) -> str:
    """нормализация текста под простую проверку ключевых слов"""
    return re.sub(r"\s+", " ", s.strip().lower())


def score_answer(answer: str, expected_points: List[str]) -> Dict[str, Any]:
    """
    Идея: у каждого вопроса есть expected_points (ключевые признаки хорошего ответа).
    Смотрим, сколько пунктов встретилось в тексте.

    Возвращаем:
    - label: correct/partial/wrong/unknown
    - coverage: доля покрытых пунктов
    - matched/missing: какие пункты нашли/не нашли
    """
    t = _norm(answer)

    if any(re.search(p, t) for p in I_DONT_KNOW_PATTERNS):
        return {
            "label": "unknown",
            "coverage": 0.0,
            "matched": [],
            "missing": expected_points,
        }

    matched = [p for p in expected_points if p.lower() in t]
    coverage = 0.0 if not expected_points else len(matched) / len(expected_points)

    # Простая шкала: можно потом настроить
    if coverage >= 0.65:
        label = "correct"
    elif coverage >= 0.30:
        label = "partial"
    else:
        label = "wrong"

    missing = [p for p in expected_points if p not in matched]

    return {
        "label": label,
        "coverage": coverage,
        "matched": matched,
        "missing": missing,
    }


def estimate_clarity(answer: str) -> int:
    """
    оценка ясности (0..2) чисто по размеру ответа:
    - 0: слишком коротко
    - 1: нормально
    - 2: достаточно развернуто
    """
    t = answer.strip()
    if len(t) < 25:
        return 0
    if len(t) < 120:
        return 1
    return 2
