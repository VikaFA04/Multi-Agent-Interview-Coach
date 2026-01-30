from __future__ import annotations

import os
import json
from dotenv import load_dotenv

from .schemas import CandidateProfile
from .logger import InterviewLogger
from .memory import Memory

from .agents.router import RouterAgent
from .agents.observer import ObserverAgent
from .agents.interviewer import InterviewerAgent
from .agents.hiring_manager import HiringManagerAgent

from .orchestrator import Orchestrator


def build_llm():
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()

    if provider == "openai_compat":
        from .llm.openai_compatible import OpenAICompatibleLLM
        return OpenAICompatibleLLM()

    # Можно добавить сюда другие провайдеры при желании.
    return None


def main():
    load_dotenv()

    print("=== Multi-Agent Interview Coach ===")

    # Вводные по ТЗ
    participant_name = input("Имя кандидата: ").strip() or "Без имени"
    position = input("Позиция: ").strip() or "Backend Developer"
    target_grade = input("Грейд (Junior/Middle/Senior): ").strip() or "Junior"
    experience = input("Опыт (кратко): ").strip() or "Нет данных"

    profile = CandidateProfile(
        participant_name=participant_name,
        position=position,
        target_grade=target_grade,  # type: ignore
        experience=experience,
    )

    # Лог по ТЗ
    log_path = os.getenv("LOG_PATH", "interview_log.json")
    logger = InterviewLogger(log_path)

    # Память и агенты
    memory = Memory()
    router = RouterAgent()

    llm = build_llm()
    observer = ObserverAgent(llm=llm)
    interviewer = InterviewerAgent()
    hiring_manager = HiringManagerAgent()

    orch = Orchestrator(
        router=router,
        observer=observer,
        interviewer=interviewer,
        hiring_manager=hiring_manager,
        logger=logger,
        memory=memory,
    )

    # Старт интервью
    interviewer_msg = orch.start(profile)
    print("\nInterviewer:", interviewer_msg)

    # Главный цикл
    while True:
        user_msg = input("\nТы: ").strip()

        next_msg = orch.handle_user_message(profile, interviewer_msg, user_msg)

        # stop - финальный отчет сохранен
        if next_msg is None:
            print("\nInterviewer: Спасибо! Интервью остановлено. Финальный фидбэк сохранён в", log_path)

            # Для удобства показываем итог в консоли
            try:
                data = json.loads(open(log_path, "r", encoding="utf-8").read())
                print("\n=== FINAL FEEDBACK (json) ===")
                print(json.dumps(data.get("final_feedback", {}), ensure_ascii=False, indent=2))
            except Exception:
                pass

            break

        interviewer_msg = next_msg
        print("\nInterviewer:", interviewer_msg)


if __name__ == "__main__":
    main()
