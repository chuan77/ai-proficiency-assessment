"""Choose which questions go into a session."""

import random
from collections import defaultdict

from app.models import Question


def _spread_by_topic(questions: list[Question], count: int, rng: random.Random) -> list[Question]:
    """Pick `count` questions, cycling through topics so coverage stays even."""
    by_topic: dict[str, list[Question]] = defaultdict(list)
    for question in questions:
        by_topic[question.topic].append(question)
    for pool in by_topic.values():
        rng.shuffle(pool)
    topics = list(by_topic)
    rng.shuffle(topics)
    picked: list[Question] = []
    while len(picked) < count and any(by_topic.values()):
        for topic in topics:
            if by_topic[topic] and len(picked) < count:
                picked.append(by_topic[topic].pop())
    return picked


def _quotas(bank: list[Question], count: int) -> dict[str, int]:
    """How many questions of each type to draw; at least one code question if any exist."""
    pools = {kind: [q for q in bank if q.type == kind] for kind in ("mcq", "open", "code")}
    code = min(len(pools["code"]), max(1, round(count * len(pools["code"]) / len(bank))))
    code = code if pools["code"] else 0
    rest = count - code
    prose = len(pools["mcq"]) + len(pools["open"])
    open_q = min(len(pools["open"]), round(rest * len(pools["open"]) / prose)) if prose else 0
    mcq = min(len(pools["mcq"]), rest - open_q)
    open_q = min(len(pools["open"]), rest - mcq)
    return {"mcq": mcq, "open": open_q, "code": code}


def select_questions(
    bank: list[Question], count: int, rng: random.Random | None = None
) -> list[Question]:
    """Return `count` questions keeping the bank's type mix and topic spread.

    Every session gets at least one code question when the bank has one. If the bank has
    `count` or fewer questions, all of them are returned. The result keeps the bank's
    original order so topics stay grouped for the user.
    """
    if count >= len(bank):
        return list(bank)
    rng = rng or random.Random()
    chosen: list[Question] = []
    for kind, quota in _quotas(bank, count).items():
        chosen += _spread_by_topic([q for q in bank if q.type == kind], quota, rng)
    chosen_ids = {q.id for q in chosen}
    return [q for q in bank if q.id in chosen_ids]
