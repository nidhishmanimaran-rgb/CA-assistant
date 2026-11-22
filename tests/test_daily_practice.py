"""Deterministic daily practice checks: no network or model credentials needed."""
from datetime import date, timedelta

from backend.daily_practice import DAILY_TARGET, QUESTION_BANK, count_correct, daily_questions


def test_bank_is_well_formed_and_covers_all_intermediate_subjects():
    assert len(QUESTION_BANK) >= 40
    assert len({q.id for q in QUESTION_BANK}) == len(QUESTION_BANK)
    assert {q.subject for q in QUESTION_BANK} == {
        "Advanced Accounting", "Corporate and Other Laws", "Taxation",
        "Cost and Management Accounting", "Auditing and Ethics",
        "Financial Management", "Strategic Management",
    }
    assert all(len(q.options) == 4 and q.answer_index in range(4) for q in QUESTION_BANK)


def test_same_day_is_stable_balanced_and_20_marks():
    chosen = daily_questions(date(2026, 11, 22))
    assert len(chosen) == DAILY_TARGET == 20
    assert len({q.id for q in chosen}) == DAILY_TARGET
    assert chosen == daily_questions(date(2026, 11, 22))
    subjects = {q.subject for q in chosen}
    assert len(subjects) == 7


def test_scoring_does_not_count_unanswered_questions_as_correct():
    questions = daily_questions(date(2026, 11, 22))
    assert count_correct(questions, {}) == 0
    answers = {q.id: q.answer_index for q in questions[:5]}
    assert count_correct(questions, answers) == 5
    answers[questions[5].id] = (questions[5].answer_index + 1) % 4
    assert count_correct(questions, answers) == 5


def test_date_rotation_and_question_variation():
    first = daily_questions(date(2026, 11, 22))
    later = daily_questions(date(2026, 11, 22) + timedelta(days=1))
    assert [q.id for q in first] != [q.id for q in later]
