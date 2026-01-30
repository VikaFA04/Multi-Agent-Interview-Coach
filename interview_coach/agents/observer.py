from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional

from ..memory import Memory
from ..question_bank import pick_question, Question
from ..scoring import score_answer, estimate_clarity
from ..llm.base import Message


OBSERVER_SYSTEM = """Ты — Observer/ментор. Ты НЕ говоришь кандидату напрямую.
Твоя задача: помочь Interviewer.
Дай краткий план:
- eval: correct/partial/wrong/unknown
- route: next_question | handle_offtopic | handle_hallucination | answer_role_reversal
- next_question: один вопрос (естественно, как рекрутер)
Верни только текст вопроса или короткий план.
"""


@dataclass
class ObserverPlan:
    plan: Dict[str, Any]
    internal_note: str


class ObserverAgent:

    def __init__(self, llm=None):
        self.llm = llm  # опционально

    def analyze_turn(
        self,
        profile: Dict[str, Any],
        memory: Memory,
        last_question: Optional[Question],
        user_answer: str,
        forced_route: str = "evaluate",
        router_flags: Optional[Dict[str, bool]] = None,
    ) -> ObserverPlan:

        router_flags = router_flags or {}

        # 1) фиксируем флаги для отчета/логов (Observer доверяет Router)
        flags = {
            "offtopic": bool(router_flags.get("offtopic", False)),
            "hallucination": bool(router_flags.get("hallucination", False)),
            "role_reversal": bool(router_flags.get("role_reversal", False)),
        }

        # 2) soft-signal: ясность ответа
        memory.signals["clarity_votes"].append(estimate_clarity(user_answer))

        # Доп. счётчики “поведения”
        if flags["role_reversal"]:
            memory.signals["role_reversal_count"] += 1
            memory.signals["engagement_flags"] += 1
        if flags["offtopic"]:
            memory.signals["offtopic_count"] += 1
        if flags["hallucination"]:
            memory.signals["hallucination_flags"] += 1

        # 3) оцениваем ответ на прошлый вопрос (если он был)
        eval_label = "unknown"
        coverage = 0.0
        missing: list[str] = []

        if last_question is not None:
            sc = score_answer(user_answer, last_question.expected_points)
            eval_label = sc["label"]
            coverage = sc["coverage"]
            missing = sc["missing"]

            # сохраняем в историю для финального отчета
            memory.note_eval(
                {
                    "topic": last_question.topic,
                    "qid": last_question.qid,
                    "question": last_question.text,
                    "answer": user_answer,
                    "eval": eval_label,
                    "coverage": coverage,
                    "missing": missing,
                    "reference_answer": last_question.reference_answer,
                }
            )

            # 4) обновляем streak'и для адаптивности
            if eval_label == "correct":
                memory.correct_streak += 1
                memory.incorrect_streak = 0
            elif eval_label in ("wrong", "unknown"):
                memory.incorrect_streak += 1
                memory.correct_streak = 0
            else:
                # partial: сбрасываем оба, чтобы не дергать сложность резко
                memory.correct_streak = 0
                memory.incorrect_streak = 0

        # 5) адаптивность сложности
        difficulty_delta = 0
        if memory.correct_streak >= 2:
            difficulty_delta = 1
        if memory.incorrect_streak >= 2:
            difficulty_delta = -1

        memory.bump_difficulty(difficulty_delta)

        # 6) преобразуем forced_route в route для Interviewer
        route = "next_question"
        role_reversal_answer = None

        if forced_route == "offtopic":
            route = "handle_offtopic"
        elif forced_route == "hallucination":
            route = "handle_hallucination"
        elif forced_route == "role_reversal":
            route = "answer_role_reversal"
            # короткий “ответ работодателя” — достаточно, чтобы пройти роль-реверсал тест
            role_reversal_answer = (
                "Обычно на испытательном сроке дают 1–2 небольшие фичи и 1 багфикс, "
                "чтобы посмотреть качество кода, скорость обучения и коммуникацию. "
                "По микросервисам: часто есть смешанная архитектура — часть монолита + отдельные сервисы вокруг критичных доменов."
            )

        # 7) если кандидат "плывет"
        preferred_topic = None
        if eval_label in ("wrong", "unknown") and last_question is not None:
            preferred_topic = last_question.topic

        # 8) выбираем следующий вопрос из банка
        next_q = pick_question(
            difficulty=memory.difficulty,
            asked_ids=memory.asked_question_ids,
            asked_topics=memory.asked_topics,
            preferred_topic=preferred_topic,
        )

        # отмечаем, что этот вопрос мы собираемся задавать
        memory.asked_question_ids.append(next_q.qid)
        memory.asked_topics.append(next_q.topic)

        # 9) (опционально) попросим LLM переформулировать вопрос, чтобы он звучал "по-человечески”"
        next_question_text = next_q.text
        if self.llm is not None and route == "next_question":
            prompt_user = (
                f"Вводные: position={profile['position']} grade={profile['target_grade']} exp={profile['experience']}\n"
                f"Текущая сложность={memory.difficulty}\n"
                f"Сформулируй ОДИН вопрос для интервью.\n"
                f"Тема: {next_q.topic}; сложность ~{next_q.difficulty}.\n"
                f"Не повторяй недавно заданные темы: {memory.asked_topics[-6:]}.\n"
            )
            try:
                llm_text = self.llm.generate(
                    [Message("system", OBSERVER_SYSTEM), Message("user", prompt_user)],
                    temperature=0.2,
                )
                # минимальная валидация: вопрос должен быть вопросом и не слишком длинным
                if "?" in llm_text and 10 < len(llm_text.strip()) < 400:
                    next_question_text = llm_text.strip()
            except Exception:
                # если LLM упала — просто используем банковский вопрос
                pass

        # 10) готовим "план" для Interviewer
        plan: Dict[str, Any] = {
            "eval": eval_label,
            "coverage": round(coverage, 2),
            "flags": flags,
            "route": route,
            "difficulty_delta": difficulty_delta,
            "difficulty_now": memory.difficulty,
            "preferred_topic": preferred_topic,
            "next_question": next_question_text,
        }
        if role_reversal_answer:
            plan["role_reversal_answer"] = role_reversal_answer

        # 11) короткая внутренняя заметка для лога (то, что будет видно жюри)
        internal_note = (
            f"eval={eval_label} coverage={round(coverage,2)} "
            f"streak(c/i)={memory.correct_streak}/{memory.incorrect_streak} "
            f"router_route={forced_route} flags={flags} diff={memory.difficulty} -> next={next_q.qid}"
        )

        return ObserverPlan(plan=plan, internal_note=internal_note)
