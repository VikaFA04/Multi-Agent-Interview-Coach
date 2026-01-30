from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import random


@dataclass(frozen=True)
class Question:
    qid: str
    topic: str
    difficulty: int  # 1..5
    text: str
    expected_points: List[str]
    reference_answer: str


# небольшой банк вопросов
QUESTIONS: List[Question] = [
    Question(
        qid="py_types_1",
        topic="Python basics",
        difficulty=1,
        text="Расскажи про основные типы данных в Python (list/dict/set/tuple) и когда какой использовать.",
        expected_points=["list", "dict", "set", "tuple", "изменяем", "неизменяем", "ключ", "уникаль"],
        reference_answer=(
            "list — изменяемая последовательность; tuple — неизменяемая; "
            "dict — отображение ключ→значение; set — множество уникальных элементов. "
            "Выбор зависит от операций: индексирование, уникальность, быстрый доступ по ключу."
        ),
    ),
    Question(
        qid="py_for_1",
        topic="Python basics",
        difficulty=1,
        text="Как работает цикл for в Python и что такое итератор/итерируемый объект?",
        expected_points=["for", "iter", "iterator", "iterable", "__iter__", "__next__", "StopIteration"],
        reference_answer=(
            "for итерируется по iterable: вызывает iter(obj) чтобы получить iterator, "
            "затем repeatedly вызывает next() до StopIteration. "
            "Iterable реализует __iter__, iterator — __next__."
        ),
    ),
    Question(
        qid="py_exceptions_2",
        topic="Python exceptions",
        difficulty=2,
        text="Объясни try/except/else/finally. Когда выполняется else и зачем finally?",
        expected_points=["try", "except", "else", "finally", "без исключений", "всегда"],
        reference_answer=(
            "else выполняется, если в try не было исключений. "
            "finally выполняется всегда (даже при исключении/return) — для освобождения ресурсов."
        ),
    ),
    Question(
        qid="sql_join_1",
        topic="SQL",
        difficulty=1,
        text="В чем разница между INNER JOIN и LEFT JOIN? Приведи пример, когда нужен LEFT JOIN.",
        expected_points=["inner", "left", "null", "все строки", "совпад"],
        reference_answer=(
            "INNER JOIN возвращает только совпавшие строки. "
            "LEFT JOIN возвращает все строки из левой таблицы + совпадения справа (иначе NULL). "
            "Например: показать всех пользователей и их заказы, включая пользователей без заказов."
        ),
    ),
    Question(
        qid="sql_index_3",
        topic="SQL",
        difficulty=3,
        text="Что такое индекс в БД и какие у него плюсы/минусы? Когда индекс может навредить?",
        expected_points=["индекс", "ускор", "поиск", "b-tree", "запись", "обнов", "место", "селектив"],
        reference_answer=(
            "Индекс (часто B-tree) ускоряет поиск/сортировку/джойны по ключам, "
            "но занимает место и замедляет INSERT/UPDATE/DELETE из-за обслуживания. "
            "Может навредить при низкой селективности, частых обновлениях или неверном выборе индекса."
        ),
    ),
    Question(
        qid="http_methods_1",
        topic="HTTP",
        difficulty=1,
        text="Какие HTTP методы знаешь? Чем отличаются POST и PUT? Что такое идемпотентность?",
        expected_points=["get", "post", "put", "delete", "patch", "идемпотент", "повтор"],
        reference_answer=(
            "GET/POST/PUT/DELETE/PATCH. PUT обычно идемпотентен: повтор запроса приводит к тому же состоянию ресурса. "
            "POST чаще не идемпотентен. Идемпотентность — повторяемость без изменения результата."
        ),
    ),
    Question(
        qid="django_orm_2",
        topic="Django",
        difficulty=2,
        text="Как Django ORM строит запросы и что такое QuerySet? Когда запрос реально выполняется?",
        expected_points=["QuerySet", "lazy", "ленив", "eval", "sql", "filter", "select_related", "prefetch_related"],
        reference_answer=(
            "QuerySet — ленивое описание запроса; SQL строится при вызовах filter/annotate "
            "и выполняется при итерации/len/list/exists и т.п. "
            "select_related/prefetch_related помогают с проблемой N+1."
        ),
    ),
    Question(
        qid="testing_2",
        topic="Testing",
        difficulty=2,
        text="Чем отличаются unit и integration тесты? Как бы ты тестировал(а) API эндпоинт?",
        expected_points=["unit", "integration", "mock", "контракт", "http", "fixtures"],
        reference_answer=(
            "Unit — изолированная проверка маленькой части (часто с моками). "
            "Integration — проверка взаимодействия компонентов (БД/HTTP). "
            "API эндпоинт: статус-коды, body, авторизация, негативные кейсы; интеграционно с тестовой БД/fixtures."
        ),
    ),
    Question(
        qid="design_4",
        topic="System design",
        difficulty=4,
        text="Как бы ты спроектировал(а) сервис сокращения ссылок (URL shortener)? Какие компоненты нужны?",
        expected_points=["id", "hash", "db", "cache", "rate", "redirect", "unique", "scale"],
        reference_answer=(
            "Компоненты: API для создания/редиректа, генерация уникального ключа (ID/хэш), "
            "БД соответствий, кэш для популярных ссылок, rate limiting, аналитика. "
            "Для масштабирования — шардирование/репликация, CDN для редиректов."
        ),
    ),
]


def pick_question(
    difficulty: int,
    asked_ids: List[str],
    asked_topics: List[str],
    preferred_topic: Optional[str] = None,
) -> Question:
    """
    выбор следующего вопроса:
    - берем вопросы близкого уровня сложности (±1), чтобы изменения были плавные
    - не повторяем уже заданные qid
    - стараемся не долбить одну тему подряд
    """
    # плавная адаптация: берем рядом по сложности
    candidates = [q for q in QUESTIONS if q.qid not in asked_ids and abs(q.difficulty - difficulty) <= 1]

    # если нужно "дожать" конкретную тему - пробуем ту же тему
    if preferred_topic:
        same_topic = [q for q in candidates if q.topic == preferred_topic]
        if same_topic:
            return random.choice(same_topic)

    # иначе — избегаем повторов темы последних 2 вопросов
    not_recent_topics = [q for q in candidates if q.topic not in asked_topics[-2:]]
    if not_recent_topics:
        return random.choice(not_recent_topics)

    if candidates:
        return random.choice(candidates)

    # если вдруг все близкие вопросы кончились, берем любой оставшийся
    remaining = [q for q in QUESTIONS if q.qid not in asked_ids]
    return random.choice(remaining) if remaining else random.choice(QUESTIONS)
