"""Bounded, session-local chat records and portable exports."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from uuid import uuid4

from config.catalog import MAX_QUESTION_CHARS, MAX_TURNS


@dataclass(frozen=True)
class StudyContext:
    level: str
    subject: str
    chapter: str
    attempt: str
    language: str
    answer_format: str
    assessment_year: str = ""
    fiscal_year: str = ""
    as_of: str = ""


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_question(question: str) -> str:
    cleaned = question.strip()
    if not cleaned:
        raise ValueError("Type a question before sending it.")
    if len(cleaned) > MAX_QUESTION_CHARS:
        raise ValueError(f"Keep your question within {MAX_QUESTION_CHARS:,} characters.")
    return cleaned


def append_exchange(
    messages: list[dict],
    question: str,
    answer: str,
    context: StudyContext,
    *,
    kind: str = "demo",
) -> list[dict]:
    """Return a new bounded history; freeze context on both sides of each turn."""
    cleaned = validate_question(question)
    created_at = timestamp()
    added = [
        {
            "id": uuid4().hex,
            "role": role,
            "content": content,
            "context": asdict(context),
            "created_at": created_at,
            "kind": kind if role == "assistant" else "question",
        }
        for role, content in (("user", cleaned), ("assistant", answer))
    ]
    return (messages + added)[-(MAX_TURNS * 2):]


def export_chat(messages: list[dict], feedback: dict) -> str:
    """Export only explicit session fields, never environment variables or secrets."""
    message_ids = {message["id"] for message in messages}
    return json.dumps(
        {
            "schema_version": 1,
            "app": "CA AI Assistant",
            "phase": 8 if any(m.get("kind") not in ("question", "demo", "prepared_example") for m in messages) else 1,
            "mode": "tutor" if any(m.get("kind") not in ("question", "demo", "prepared_example") for m in messages) else "interface_demo",
            "exported_at": timestamp(),
            "messages": messages,
            "feedback": {
                key: value for key, value in feedback.items() if key in message_ids
            },
        },
        ensure_ascii=False,
        indent=2,
    )
