"""Validate citation identity and exact evidence quotes; this is not an entailment proof."""
import html
import re
from backend.errors import AppError

ANSWER_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "status": {"type": "string", "enum": ["answer", "clarification", "insufficient_evidence"]},
        "answer": {"type": "string"},
        "claims": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {"statement": {"type": "string"}, "source_id": {"type": "string"},
                           "quote": {"type": "string"}},
            "required": ["statement", "source_id", "quote"],
        }},
    }, "required": ["status", "answer", "claims"],
}


def normalized(text):
    return " ".join(text.split()).casefold()


def safe_markdown(text):
    # Remove external links/images; escape raw HTML. The server owns source links.
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "[image removed]", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return html.escape(text, quote=False)


def validate_answer(payload, sources, require_sources=False):
    import jsonschema
    try:
        jsonschema.validate(payload, ANSWER_SCHEMA)
    except jsonschema.ValidationError:
        raise AppError("The model returned an invalid answer structure. Please retry.", "invalid_response") from None
    if len(payload["answer"]) > 20000 or len(payload["claims"]) > 12:
        raise AppError("The model response exceeded its limits.", "invalid_response")
    if payload["status"] != "answer":
        if payload["claims"] or re.search(r"\[S\d+\]|\bpage\s+\d", payload["answer"], re.I):
            raise AppError("Unsupported citations in a clarification were rejected.", "citation")
        return safe_markdown(payload["answer"]), [], payload["status"]
    lookup = {source["source_id"]: source for source in sources}
    if require_sources:
        if not payload["claims"]:
            raise AppError("There is not enough cited evidence for this answer.", "insufficient_evidence")
        rendered, used = [], []
        for claim in payload["claims"]:
            source = lookup.get(claim["source_id"])
            quote, statement = claim["quote"], claim["statement"]
            if not source or not 20 <= len(quote) <= 800 or not 1 <= len(statement) <= 3000:
                raise AppError("An unsupported source reference was rejected.", "citation")
            if normalized(quote) not in normalized(source["text"]):
                raise AppError("A quotation does not match its retrieved source.", "citation")
            if re.search(r"\[[^\]]*\]|https?://|\bpage\s+\d", statement, re.I):
                raise AppError("Unexpected citations inside a model statement were rejected.", "citation")
            rendered.append(safe_markdown(statement) + f" [{claim['source_id']}]")
            if source["source_id"] not in {item["source_id"] for item in used}:
                used.append({**source, "evidence_quote": quote})
        return "\n\n".join(rendered), used, "source_linked"
    if payload["claims"] or re.search(r"\[S\d+\]|\bpage\s+\d", payload["answer"], re.I):
        raise AppError("The answer cites material that was not supplied.", "citation")
    return safe_markdown(payload["answer"]), [], "model_unverified"
