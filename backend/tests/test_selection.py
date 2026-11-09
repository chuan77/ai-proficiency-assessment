"""Tests for choosing questions per session."""

import random

from app.models import Question
from app.services.selection import select_questions


def _bank() -> list[Question]:
    topics = ["A", "B", "C", "D"]
    bank = [
        Question(id=f"m{i:02d}", type="mcq", topic=topics[i % 4], difficulty="x", text="t")
        for i in range(13)
    ]
    bank += [
        Question(id=f"o{i:02d}", type="open", topic=topics[i % 4], difficulty="x", text="t")
        for i in range(7)
    ]
    return bank


def test_returns_requested_count_with_mix_and_no_duplicates() -> None:
    for seed in range(20):
        chosen = select_questions(_bank(), 10, random.Random(seed))
        assert len(chosen) == 10 == len({q.id for q in chosen})
        assert {"mcq", "open"} <= {q.type for q in chosen}
        assert {q.topic for q in chosen} == {"A", "B", "C", "D"}


def test_small_bank_returns_everything() -> None:
    assert len(select_questions(_bank(), 50)) == 20


def test_keeps_bank_order() -> None:
    chosen = select_questions(_bank(), 10, random.Random(1))
    ids = [q.id for q in chosen]
    assert ids == sorted(ids, key=[q.id for q in _bank()].index)


def test_selection_varies_between_runs() -> None:
    picks = {
        tuple(q.id for q in select_questions(_bank(), 10, random.Random(s))) for s in range(10)
    }
    assert len(picks) > 1


def test_code_question_always_included() -> None:
    bank = _bank() + [
        Question(id=f"c{i}", type="code", topic="A", difficulty="x", text="t") for i in range(3)
    ]
    for seed in range(30):
        chosen = select_questions(bank, 10, random.Random(seed))
        assert len(chosen) == 10
        assert any(q.type == "code" for q in chosen)
        assert any(q.type == "open" for q in chosen) and any(q.type == "mcq" for q in chosen)
