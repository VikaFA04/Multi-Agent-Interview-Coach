from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .schemas import InterviewLog, TurnLog, FinalFeedback


class InterviewLogger:

    def __init__(self, path: str = "interview_log.json"):
        self.path = Path(path)
        self.log: Optional[InterviewLog] = None

    def start(self, participant_name: str, meta: Dict[str, Any]) -> None:
        """Создаем новую сессию."""
        self.log = InterviewLog(participant_name=participant_name, meta=meta)
        self.flush()

    def add_turn(
        self,
        turn_id: int,
        agent_visible_message: str,
        user_message: str,
        internal_thoughts: str,
    ) -> None:

        assert self.log is not None, "Logger not started: call start() first"

        self.log.turns.append(
            TurnLog(
                turn_id=turn_id,
                agent_visible_message=agent_visible_message,
                user_message=user_message,
                internal_thoughts=internal_thoughts,
            )
        )
        self.flush()

    def finalize(self, final_feedback: FinalFeedback) -> None:
        """Фиксируем финальный отчёт и сохраняем"""
        assert self.log is not None, "Logger not started: call start() first"
        self.log.final_feedback = final_feedback
        self.flush()

    def flush(self) -> None:
        """Физически пишем json на диск"""
        assert self.log is not None, "Logger not started: call start() first"

        self.path.write_text(
            json.dumps(self.log.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
