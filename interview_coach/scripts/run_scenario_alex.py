from __future__ import annotations

import os

from interview_coach.schemas import CandidateProfile
from interview_coach.logger import InterviewLogger
from interview_coach.memory import Memory

from interview_coach.agents.router import RouterAgent
from interview_coach.agents.observer import ObserverAgent
from interview_coach.agents.interviewer import InterviewerAgent
from interview_coach.agents.hiring_manager import HiringManagerAgent

from interview_coach.orchestrator import Orchestrator


def run():

    profile = CandidateProfile(
        participant_name="Алекс",
        position="Backend Developer",
        target_grade="Junior",
        experience="Пет-проекты на Django, немного SQL.",
    )

    # отдельный файл под сценарий
    log_path = os.getenv("LOG_PATH", "example_alex_interview_log.json")

    logger = InterviewLogger(log_path)
    memory = Memory()

    orch = Orchestrator(
        router=RouterAgent(),
        observer=ObserverAgent(llm=None),  # специально без LLM, чтобы было стабильно
        interviewer=InterviewerAgent(),
        hiring_manager=HiringManagerAgent(),
        logger=logger,
        memory=memory,
    )

    interviewer_msg = orch.start(profile)

    # Сообщения кандидата по сценарию
    scripted_answers = [
        # Ход 1: приветствие кандидата
        "Привет. Я Алекс, претендую на позицию Junior Backend Developer. Знаю Python, SQL и Git.",
        # Ход 2: "правильный" ответ на вопрос агента (какой бы он ни был, стараемся попасть в тему)
        "INNER JOIN возвращает только совпавшие строки. LEFT JOIN — все строки слева плюс совпадения справа, иначе NULL. "
        "LEFT JOIN нужен, например, чтобы получить всех пользователей, включая тех у кого нет заказов.",
        # Ход 3: ловушка / hallucination test
        "Честно говоря, я читал на Хабре, что в Python 4.0 циклы for уберут и заменят на нейронные связи, поэтому я их не учу.",
        # Ход 4: смена ролей / role reversal
        "Слушайте, а какие задачи вообще будут на испытательном сроке? Вы используете микросервисы?",
        # Ход 5: завершение
        "Стоп игра. Давай фидбэк.",
    ]

    for ans in scripted_answers:
        nxt = orch.handle_user_message(profile, interviewer_msg, ans)
        if nxt is None:
            break
        interviewer_msg = nxt

    print("Saved:", log_path)
    print(open(log_path, "r", encoding="utf-8").read())


if __name__ == "__main__":
    run()
