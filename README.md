# Multi-Agent Interview Coach

Multi-Agent Interview Coach — это мультиагентная система, которая проводит техническое интервью в формате **Вопрос - Ответ**, адаптирует сложность и (самое важное по ТЗ) имеет **скрытую рефлексию**: агенты принимают решения "за кулисами", а затем Interviewer формирует видимый ответ пользователю.

### 1) Архитектура
В проекте 4 роли:

- **RouterAgent** — маршрутизатор (chain-of-responsibility). Определяет, что происходит на текущем ходе:
  - остановка интервью (`Стоп интервью`, `Давай фидбэк`)
  - off-topic
  - hallucination test (уверенная “ерунда”)
  - role reversal (кандидат задаёт вопросы интервьюеру)
  - обычный режим (evaluate)
- **Observer** — скрытый аналитик:
  - оценивает ответ (correct/partial/wrong/unknown)
  - регулирует сложность (difficulty 1..5)
  - выбирает следующий вопрос из банка
  - формирует “план” (структурированный) для Interviewer
- **Interviewer** — единственный агент, который общается с кандидатом:
  - задаёт следующий вопрос
  - мягко возвращает к теме при off-topic
  - корректно реагирует на галлюцинации
  - отвечает на вопросы кандидата (role reversal) и возвращается к интервью
- **HiringManager** — скрытый агент финального решения:
  - формирует структурированный отчёт
  - grade + hiring recommendation + confidence
  - hard skills + пробелы (с правильными ответами)
  - soft skills
  - roadmap

Это "role specialization" в чистом виде: **каждая роль делает только своё**.

---

### 2) Hidden Reflection (внутренний диалог перед ответом)
На каждом ходе система работает так:

1. `RouterAgent.decide()` - определяет route (stop/offtopic/…)
2. `Observer.analyze_turn()` - **скрытый анализ** + выбор следующего вопроса
3. `Interviewer.respond()`  формирует **видимое сообщение** кандидату

Этот процесс записывается в лог в поле `internal_thoughts` в читаемом виде:


### 3) Context Awareness (память)
Система хранит:
- последние N реплик (`Memory.transcript`) — чтобы помнить, что было несколько сообщений назад
- список заданных вопросов (`asked_question_ids`) — чтобы не повторяться
- список тем (`asked_topics`) — чтобы не “долбить” одну тему подряд

---

### 4) Adaptability (динамическая сложность)
`Memory.difficulty` меняется в диапазоне **1..5** по серии ответов:
- 2 раза подряд `correct` → difficulty + 1
- 2 раза подряд `wrong/unknown` → difficulty - 1
- `partial` сбрасывает streak (не дергаем сложность резко)

Выбор следующего вопроса идет по правилу:
- берем вопросы уровня `difficulty ± 1` (плавно)
- избегаем повторов тем
- если кандидат “плывёт” — предпочтём вопрос той же темы

---

### 5) Robustness (off-topic, hallucinations, role reversal)
- **Off-topic**: RouterAgent помечает off-topic, Interviewer мягко возвращает в интервью.
- **Hallucination**: если кандидат говорит “Python 4.0 уберёт for…” — Interviewer не соглашается, аккуратно “приземляет” на проверяемые факты и продолжает интервью.
- **Role reversal**: если кандидат задаёт вопросы о работе — Interviewer отвечает (кратко) и возвращается к интервью.

---

### 6) Финальный фидбэк
После команды остановки (“Стоп интервью” / “Давай фидбэк”) формируется отчёт:

**A. Decision**
- Grade (Junior/Middle/Senior)
- Hiring Recommendation (No Hire / Hire / Strong Hire)
- Confidence Score (0–100)

**B. Technical Review**
- Confirmed Skills
- Knowledge Gaps
- что было не так
- **правильный ответ** (reference_answer из question_bank)

**C. Soft Skills**
- Clarity
- Honesty
- Engagement

**D. Roadmap**
- список конкретных тем на подтягивание
- + опциональные ссылки

---

## Структура проекта
```
multi_agent_interview_coach/
requirements.txt
README.md
interview_coach/
init.py
cli.py
orchestrator.py
schemas.py
logger.py
memory.py
scoring.py
question_bank.py
agents/
init.py
router.py
interviewer.py
observer.py
hiring_manager.py
llm/
base.py
openai_compatible.py
scripts/
init.py
run_scenario_alex.py
```
## Установка и запуск

### 1) Установка зависимостей
```
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
### 2) Запуск CLI-интервью
```
python -m interview_coach.cli
```
