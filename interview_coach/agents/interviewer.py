from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class InterviewerResponse:
    visible_message: str
    internal_note: str


class InterviewerAgent:

    def respond(self, plan: Dict[str, Any]) -> InterviewerResponse:
        route = plan.get("route", "next_question")
        next_q = plan.get("next_question", "")

        # 1) оффтоп: мягко возвращаем в интервью и задаём вопрос
        if route == "handle_offtopic":
            msg = "Понял! Давай вернемся к интервью. " + next_q
            return InterviewerResponse(
                visible_message=msg,
                internal_note="Redirected from off-topic and continued with next question.",
            )

        # 2) галлюцинация: не соглашаемся, мягко приземляем и продолжаем
        if route == "handle_hallucination":
            msg = (
                "Уточню: сейчас нет подтверждений такому утверждению. "
                "В интервью будем опираться на документацию и проверяемые факты. "
                + next_q
            )
            return InterviewerResponse(
                visible_message=msg,
                internal_note="Challenged hallucination politely; resumed interview.",
            )

        # 3) role reversal: кандидат задает вопрос интервьюеру — ответить + вернуть к интервью
        if route == "answer_role_reversal":
            # ответ формирует Observer (как часть плана)
            answer = plan.get(
                "role_reversal_answer",
                "Обычно на испытательном дают небольшие фичи/багфиксы и смотрят на качество кода и коммуникацию.",
            )
            msg = f"{answer} А теперь вернемся к интервью: {next_q}"
            return InterviewerResponse(
                visible_message=msg,
                internal_note="Answered candidate question (role reversal) and resumed interview.",
            )

        # 4) Обычный режим: просто задаём следующий вопрос
        return InterviewerResponse(
            visible_message=next_q,
            internal_note="Asked next planned question.",
        )
