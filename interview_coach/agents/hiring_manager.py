from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

from ..memory import Memory
from ..schemas import FinalFeedback, SoftSkills, GapItem


@dataclass
class HiringManagerAgent:

    def summarize(self, profile: Dict[str, Any], memory: Memory) -> FinalFeedback:
        # 1) Hard skills aggregation
        per_topic: Dict[str, List[Dict[str, Any]]] = {}
        for e in memory.evaluations:
            per_topic.setdefault(e["topic"], []).append(e)

        confirmed: List[str] = []
        gaps: List[GapItem] = []

        for topic, items in per_topic.items():
            # если по теме хотя бы раз был correct — считаем тему подтвержденной
            if any(i["eval"] == "correct" for i in items):
                confirmed.append(topic)

            # если были wrong/unknown — добавим gap (берем последний провал)
            wrongs = [i for i in items if i["eval"] in ("wrong", "unknown")]
            if wrongs:
                last = wrongs[-1]
                gaps.append(
                    GapItem(
                        topic=topic,
                        what_went_wrong=(
                            f"Ответ оценен как {last['eval']} (coverage={last['coverage']}). "
                            f"Не хватило пунктов: {last['missing']}"
                        ),
                        correct_answer=last["reference_answer"],
                    )
                )

        confirmed = sorted(set(confirmed))

        # 2) Soft skills
        clarity_avg = 0.0
        votes = memory.signals.get("clarity_votes", [])
        if votes:
            clarity_avg = sum(votes) / len(votes)

        if clarity_avg < 0.8:
            clarity = "Низкая: ответы короткие/неструктурированные; стоит проговаривать ход мысли и приводить примеры."
        elif clarity_avg < 1.5:
            clarity = "Средняя: в целом понятно, но иногда не хватает структуры и примеров."
        else:
            clarity = "Высокая: отвечает развернуто и структурированно."

        # Честность: если были "галлюцинации" — отмечаем риск
        if memory.signals.get("hallucination_flags", 0) > 0:
            honesty = "Под вопросом: были уверенные утверждения без подтверждений (сомнительные факты/слухи)."
        else:
            honesty = "Хорошая: признавал(а) незнание и не пытался(ась) выкрутиться."

        # Engagement: role reversal трактуем как “задавал вопросы”
        if memory.signals.get("engagement_flags", 0) > 0:
            engagement = "Хорошая: задавал(а) вопросы о задачах/процессах и уточнял(а) требования."
        else:
            engagement = "Средняя: встречные вопросы задавал(а) редко."

        soft = SoftSkills(clarity=clarity, honesty=honesty, engagement=engagement)

        # 3) Decision (grade + recommendation + confidence)
        target_grade = profile["target_grade"]

        total = len(memory.evaluations)
        correct = sum(1 for e in memory.evaluations if e["eval"] == "correct")
        wrong = sum(1 for e in memory.evaluations if e["eval"] in ("wrong", "unknown"))

        ratio = (correct / total) if total else 0.0

        # penalties: оффтоп и галлюцинации снижают доверие
        penalty = (memory.signals.get("offtopic_count", 0) * 0.05) + (memory.signals.get("hallucination_flags", 0) * 0.15)
        confidence = max(25, min(95, int((ratio * 100) - penalty * 100 + 40)))

        # очень простая оценка "уровня" (можно усложнить банком вопросов)
        inferred_grade = target_grade
        if ratio >= 0.75 and memory.difficulty >= 3:
            # если человек уверенно тянет уровень 3+ — можно поднять оценку
            if target_grade == "Junior":
                inferred_grade = "Middle"
        if ratio < 0.35:
            inferred_grade = "Junior"

        # рекомендация найма
        if memory.signals.get("hallucination_flags", 0) > 0 and wrong >= 2:
            recommendation = "No Hire"
        elif ratio >= 0.75 and confidence >= 70:
            recommendation = "Strong Hire"
        elif ratio >= 0.5 and confidence >= 60:
            recommendation = "Hire"
        else:
            recommendation = "No Hire"

        # 4) Roadmap (на основе gaps)
        roadmap: List[str] = []
        if gaps:
            for g in gaps[:6]:
                roadmap.append(
                    f"Подтянуть тему: {g.topic}. Повтори базовые определения и сделай 10 практических задач/примеров."
                )
        else:
            roadmap.append("Продолжать практику: решать задачи и объяснять решения вслух (структура ответа).")

        if memory.signals.get("hallucination_flags", 0) > 0:
            roadmap.append(
                "Перед интервью: проверять сомнительные утверждения по официальной документации/PEP и фиксировать источники."
            )

        optional_links = [
            "Python docs: Built-in Types, Iterators",
            "PostgreSQL docs: JOIN, Indexes, EXPLAIN",
            "MDN: HTTP Methods, Status Codes, Idempotency",
            "Django docs: QuerySet (lazy evaluation), select_related/prefetch_related",
        ]

        return FinalFeedback(
            grade=inferred_grade,  # type: ignore
            hiring_recommendation=recommendation,  # type: ignore
            confidence_score=confidence,
            confirmed_skills=confirmed,
            knowledge_gaps=gaps,
            soft_skills=soft,
            roadmap=roadmap,
            optional_links=optional_links,
        )
