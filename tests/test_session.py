import json

import pytest

from backend.demo import SAMPLE_QUESTION, build_demo_response, prepared_example
from backend.session import StudyContext, append_exchange, export_chat, validate_question
from config.catalog import ANSWER_FORMATS, MAX_QUESTION_CHARS, MAX_TURNS, MVP_CHAPTER


def context(answer_format="Detailed solution"):
    return StudyContext(
        "CA Intermediate", "Advanced Accounting", MVP_CHAPTER,
        "Student-selected attempt", "English", answer_format,
    )


@pytest.mark.parametrize("question", ["", " ", "\n\t"])
def test_empty_questions_are_rejected(question):
    with pytest.raises(ValueError, match="Type a question"):
        validate_question(question)


def test_long_questions_are_rejected_on_server():
    with pytest.raises(ValueError, match="within"):
        validate_question("a" * (MAX_QUESTION_CHARS + 1))


def test_question_limit_and_unicode():
    assert validate_question("x" * MAX_QUESTION_CHARS) == "x" * MAX_QUESTION_CHARS
    assert validate_question("  ₹8,50,000 தமிழ்  ") == "₹8,50,000 தமிழ்"


def test_history_retains_complete_turns_with_original_context():
    messages = []
    old_context = context()
    for number in range(MAX_TURNS + 3):
        messages = append_exchange(messages, f"Question {number}", "Demo", old_context)
    assert len(messages) == MAX_TURNS * 2
    assert messages[0]["content"] == "Question 3"
    assert all(message["context"]["attempt"] == old_context.attempt for message in messages)
    assert [message["role"] for message in messages] == ["user", "assistant"] * MAX_TURNS
    assert len({message["id"] for message in messages}) == len(messages)


def test_append_does_not_mutate_previous_history():
    original = []
    updated = append_exchange(original, "Question", "Demo", context())
    assert original == []
    assert len(updated) == 2


def test_export_roundtrips_unicode_and_excludes_unrelated_feedback():
    messages = append_exchange([], "₹8,50,000 தமிழ்", "Demo", context())
    answer_id = messages[1]["id"]
    exported = json.loads(export_chat(messages, {answer_id: "helpful", "old": "not_helpful"}))
    assert exported["mode"] == "interface_demo"
    assert exported["messages"][0]["content"] == "₹8,50,000 தமிழ்"
    assert exported["feedback"] == {answer_id: "helpful"}


@pytest.mark.parametrize("answer_format", ANSWER_FORMATS)
def test_arbitrary_questions_are_never_answered_with_the_fixed_example(answer_format):
    response = build_demo_response("Cost is ₹9,00,000. Calculate for six months.", context(answer_format))
    assert "no AI model is connected" in response
    assert "₹1,00,000" not in response
    assert "does not solve or verify" in response


@pytest.mark.parametrize("answer_format", ANSWER_FORMATS)
def test_prepared_example_is_labelled_and_has_no_invented_citation(answer_format):
    response = prepared_example(answer_format)
    assert "Prepared example" in response
    assert "₹1,00,000" in response
    assert "not an official ICAI solution" in response
    assert "₹8,50,000" in SAMPLE_QUESTION


def test_unknown_answer_format_is_rejected():
    with pytest.raises(ValueError):
        prepared_example("unknown")
    with pytest.raises(ValueError):
        build_demo_response("Question", context("unknown"))
