from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .schemas import CandidateProfile
from .logger import InterviewLogger
from .memory import Memory
from .question_bank import Question

from .agents.router import RouterAgent
from .agents.observer import ObserverAgent
from .agents.interviewer import InterviewerAgent
from .agents.hiring_manager import HiringManagerAgent


@dataclass
class Orchestrator:

    router: RouterAgent
    observer: ObserverAgent
    interviewer: InterviewerAgent
    hiring_manager: HiringManagerAgent
    logger: InterviewLogger
    memory: Memory

    # last_question нужен, чтобы оценивать именно ответ на последний заданный вопрос
    last_question: Optional[Question] = None
    turn_id: int = 0

    def start(self, profile: CandidateProfile) -> str:
        """Стартовая реплика и инициализация сессии/памяти."""
        # стартовая сложность можно привязать к грейду
        self.memory.difficulty = {"Junior": 1, "Middle": 2, "Senior": 3}.get(profile.target_grade, 1)

        # логгер по ТЗ: сохраняем вводные как meta
        self.logger.start(profile.participant_name, meta=profile.model_dump())

        greeting = (
            f"Привет, {profile.participant_name}! Ты претендуешь на позицию {profile.target_grade} {profile.position}. "
            "Расскажи коротко про свой опыт и последний проект/задачу."
        )

        # На первом ходе еще нечего оценивать (пока только знакомство)
        self.last_question = None
        self.turn_id = 1
        return greeting

    def handle_user_message(self, profile: CandidateProfile, interviewer_msg: str, user_msg: str) -> Optional[str]:
        # 0) контекст: помним "что спросили" и "что ответили"
        self.memory.add_exchange(interviewer_msg, user_msg)

        # 1) Router решает, что за ситуация
        decision = self.router.decide(user_msg)

        # 2) Если stop — формируем финальный отчет и заканчиваем
        if decision.route == "stop":
            feedback = self.hiring_manager.summarize(profile.model_dump(), self.memory)
            self.logger.finalize(feedback)
            return None

        # 3) Hidden Reflection: Observer оценивает и строит план (включая след. вопрос)
        plan_obj = self.observer.analyze_turn(
            profile=profile.model_dump(),
            memory=self.memory,
            last_question=self.last_question,
            user_answer=user_msg,
            forced_route=decision.route,
            router_flags=decision.flags,
        )

        # 4) Interviewer превращает план в человеческий ответ кандидату
        resp = self.interviewer.respond(plan_obj.plan)

        # 5) Логируем turn в формате ТЗ
        internal = (
            f"[Router]: route={decision.route} flags={decision.flags} note={decision.note}\n"
            f"[Observer]: {plan_obj.internal_note}\n"
            f"[Interviewer]: {resp.internal_note}"
        )
        self.logger.add_turn(self.turn_id, interviewer_msg, user_msg, internal)

        # 6) Готовим следующий ход
        self.turn_id += 1

        from .question_bank import QUESTIONS

        if self.memory.asked_question_ids:
            last_qid = self.memory.asked_question_ids[-1]
            self.last_question = next((q for q in QUESTIONS if q.qid == last_qid), None)

        return resp.visible_message
