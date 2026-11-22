"""English-first, licence-aware staging of finance datasets for CA research.

No source is automatically approved for model fine-tuning. Downloaded content
remains under the ignored data/ directory; a public Streamlit deployment only
displays registry metadata or a locally uploaded, sanitized status manifest.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class DatasetSource:
    key: str
    title: str
    role: str
    access: str
    license_note: str
    url: str
    caution: str


SOURCES = (
    DatasetSource(
        "finqa", "FinQA", "training_candidate", "public",
        "MIT-labelled repository; review underlying report rights",
        "https://github.com/czyssrs/FinQA",
        "Financial reasoning examples are not ICAI exam answers."
    ),
    DatasetSource(
        "tatqa", "TAT-QA", "training_candidate", "public",
        "CC BY 4.0; preserve attribution and review report rights",
        "https://github.com/NExTplusplus/TAT-QA",
        "Table and text questions require review before training."
    ),
    DatasetSource(
        "financemath", "FinanceMath", "evaluation_only", "public_hub",
        "Verify the dataset card and underlying source conditions",
        "https://huggingface.co/datasets/yale-nlp/FinanceMath",
        "Keep independent benchmark questions out of fine-tuning."
    ),
    DatasetSource(
        "bhasha", "BhashaBench-Finance", "evaluation_only", "gated",
        "Accept the upstream Hugging Face access terms first",
        "https://huggingface.co/datasets/bharatgenai/BhashaBench-Finance",
        "Never train on held-out benchmark test questions."
    ),
    DatasetSource(
        "indfin", "IndFin-Bench", "evaluation_only", "noncommercial",
        "CC BY-NC 4.0 plus explicit prohibition on model training and synthetic data generation",
        "https://huggingface.co/datasets/cofacto/IndFin-Bench",
        "Not licensed for unrestricted commercial use."
    ),
)
SOURCE_MAP = {source.key: source for source in SOURCES}
SUBJECTS = (
    "Advanced Accounting", "Corporate and Other Laws", "Taxation",
    "Cost and Management Accounting", "Auditing and Ethics",
    "Financial Management", "Strategic Management",
)
RULES = (
    ("Taxation", ("gst ", "taxable", "income tax", "assessment year", "tax liability")),
    ("Corporate and Other Laws", ("companies act", "company law", "contract law", "articles of association")),
    ("Auditing and Ethics", ("audit evidence", "auditor", "audit opinion", "audit risk")),
    ("Strategic Management", ("swot", "pestle", "five forces", "competitive strategy")),
    ("Cost and Management Accounting", ("break-even", "marginal costing", "overhead", "prime cost", "contribution per")),
    ("Advanced Accounting", ("depreciation", "amalgamation", "consolidated accounts", "journal entry", "accounting standard")),
    ("Financial Management", ("net present value", "npv", "discount rate", "working capital", "cost of capital", "cash flows")),
)
CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")


def classify_topic(question: str, context: str = "") -> tuple[str, str]:
    """Suggest a subject only when an explicit relevant term is present."""
    text = (question + " " + context[:900]).casefold()
    for subject, terms in RULES:
        for term in terms:
            if term in text:
                return subject, term.strip()
    return "Unclassified", "Manual CA syllabus mapping needed"


def _str(value: Any, limit: int = 4500) -> str:
    if isinstance(value, (list, tuple)):
        value = " | ".join(map(str, value))
    return str(value if value is not None else "").strip()[:limit]


def _record(source: DatasetSource, key: Any, question: Any, answer: Any,
            context: Any = "", derivation: Any = "") -> dict | None:
    q, a = _str(question), _str(answer, 15000)
    if not q or not a or CJK.search(q + a):
        return None
    background = _str(context, 7000)
    subject, topic = classify_topic(q, background)
    return {
        "id": source.key + ":" + _str(key, 120),
        "source": source.key, "role": source.role,
        "subject": subject, "topic_hint": topic,
        "question": q, "answer": a, "context": background,
        "derivation": _str(derivation, 2500),
        "language": "English candidate (requires validation)",
        "licence_note": source.license_note,
        "human_reviewed": False,
        "rights_confirmed_for_training": False,
        "approved_for_training": False,
    }


def parse_finqa(data: list[dict], limit: int = 200) -> list[dict]:
    rows = []
    for entry in data:
        qa = entry.get("qa") or {}
        context = " ".join(_str(s, 900) for s in (entry.get("pre_text") or [])[:4])
        context += " " + _str((entry.get("table") or [])[:12], 3500)
        row = _record(SOURCE_MAP["finqa"], entry.get("id", len(rows)),
                      qa.get("question"), qa.get("exe_ans") or qa.get("answer"),
                      context, qa.get("program"))
        if row:
            rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def parse_tatqa(data: list[dict], limit: int = 200) -> list[dict]:
    rows = []
    for document in data:
        paragraphs = document.get("paragraphs") or []
        text = " ".join(_str(p.get("text"), 850) for p in paragraphs[:5] if isinstance(p, dict))
        table = document.get("table") or {}
        context = text + " " + _str(table.get("table") if isinstance(table, dict) else table, 3500)
        for qa in document.get("questions") or []:
            row = _record(SOURCE_MAP["tatqa"], qa.get("uid", len(rows)),
                          qa.get("question"), qa.get("answer"), context, qa.get("derivation"))
            if row:
                rows.append(row)
            if len(rows) >= limit:
                return rows
    return rows


def parse_hub(data: Any, source: DatasetSource, limit: int = 200) -> list[dict]:
    """Normalize multiple benchmark schemas for evaluation ONLY."""
    rows = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if source.key == "financemath":
            question = item.get("question")
            answer = item.get("ground_truth")
            context = item.get("tables") or []
            derivation = item.get("python_solution") or ""
            identifier = item.get("question_id", len(rows))
        elif source.key == "bhasha":
            question = item.get("question")
            answer = item.get("correct_answer")
            if answer is None:
                answer = item.get("answer")
            options = {letter: item.get("option_" + letter.lower())
                       for letter in "ABCD" if item.get("option_" + letter.lower())}
            context = {"options": options, "topic": item.get("topic"),
                       "domain": item.get("subject_domain")}
            derivation = ""
            identifier = item.get("id", len(rows))
        elif source.key == "indfin":
            question = item.get("Question")
            answer = item.get("Atomic_Fact")
            context = item.get("Complexity_Category") or ""
            derivation = ""
            identifier = item.get("Question_Num", len(rows))
        else:
            question = item.get("question") or item.get("query") or item.get("problem")
            answer = item.get("answer") or item.get("response")
            context = item.get("context") or item.get("text") or ""
            derivation = ""
            identifier = item.get("id", len(rows))
        row = _record(source, identifier, question, answer, context, derivation)
        if row:
            rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def _download_json(url: str, max_bytes: int = 100_000_000) -> Any:
    request = Request(url, headers={"User-Agent": "CA-AI-Assistant-DatasetReview/1.0"})
    with urlopen(request, timeout=90) as response:
        payload = response.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError("Dataset exceeds bounded download size")
    return json.loads(payload)


def _load_hub(key: str, token: str | None, limit: int) -> list[dict]:
    from datasets import load_dataset

    dataset_ids = {
        "financemath": "yale-nlp/FinanceMath",
        "bhasha": "bharatgenai/BhashaBench-Finance",
        "indfin": "Cofacto/IndFin-Bench",
    }
    kwargs = {"token": token} if token else {}
    if key == "bhasha":
        kwargs["data_dir"] = "English"
    dataset = load_dataset(dataset_ids[key], **kwargs)
    if key == "indfin":
        # Upstream names its *sole evaluation benchmark* split "train".
        # Do not EVER use this split for fine-tuning or synthetic data.
        split = "train" if "train" in dataset else None
    else:
        split = next((name for name in ("test", "validation", "dev") if name in dataset), None)
    if not split:
        raise ValueError("An expected benchmark split is unavailable")
    return parse_hub(dataset[split], SOURCE_MAP[key], limit)


def public_manifest(report: dict) -> dict:
    """A strictly limited public status summary; no sample questions or answers."""
    safe = {"schema": 1, "model_trained": False, "training_ready": False, "sources": []}
    for item in report.get("sources", []):
        if item.get("source") not in SOURCE_MAP:
            continue
        safe["sources"].append({
            "source": item["source"], "status": item.get("status", "unknown"),
            "records": max(0, min(int(item.get("records", 0)), 10_000_000)),
            "subject_distribution": {
                k: max(0, min(int(v), 10_000_000))
                for k, v in (item.get("subject_distribution") or {}).items()
                if k in (*SUBJECTS, "Unclassified")
            },
        })
    return safe


def integrate(output: Path, *, limit: int = 200,
              include: tuple[str, ...] = tuple(SOURCE_MAP),
              download: bool = False, hf_token: str | None = None,
              allow_noncommercial: bool = False) -> dict:
    """Stage source records locally, not in GitHub and not as approved training data."""
    if not 1 <= limit <= 10000:
        raise ValueError("limit must be 1-10000 per source")
    if set(include) - SOURCE_MAP.keys():
        raise ValueError("Unknown source")
    output.mkdir(parents=True, exist_ok=True)
    previous = {}
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        try:
            old = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous = {x["source"]: x for x in old.get("sources", []) if x.get("source") in SOURCE_MAP}
        except (OSError, ValueError, TypeError, KeyError):
            previous = {}
    summaries = []
    for key in include:
        source = SOURCE_MAP[key]
        rows: list[dict] = []
        status, note = "registered", "Metadata only. Use --download to stage locally."
        if download:
            if key in ("bhasha", "financemath") and not hf_token:
                status, note = "access_required", "Gated dataset: accept conditions and supply HF_TOKEN privately"
            elif key == "indfin" and not allow_noncommercial:
                status, note = "restricted", "Opt-in to noncommercial benchmark use is required"
            else:
                try:
                    if key == "finqa":
                        rows = parse_finqa(_download_json(
                            "https://raw.githubusercontent.com/czyssrs/FinQA/main/dataset/train.json"), limit)
                    elif key == "tatqa":
                        rows = parse_tatqa(_download_json(
                            "https://raw.githubusercontent.com/NExTplusplus/TAT-QA/master/dataset_raw/tatqa_dataset_train.json"), limit)
                    else:
                        rows = _load_hub(key, hf_token, limit)
                    status = "staged_for_review" if rows else "no_compatible_records"
                    note = ("Not reviewed or approved for fine-tuning."
                            if rows else "No compatible question/answer rows parsed from this source.")
                except Exception as error:
                    # Show the exception type only: avoid leaking access tokens or private paths.
                    status = "failed"
                    note = "Access, network or schema issue: " + type(error).__name__
        if rows:
            with (output / f"{key}.jsonl").open("w", encoding="utf-8") as file:
                for row in rows:
                    file.write(json.dumps(row, ensure_ascii=False) + "\n")
        summaries.append({
            "source": key, "name": source.title, "url": source.url,
            "role": source.role, "access": source.access,
            "license": source.license_note,
            "status": status, "notes": note, "records": len(rows),
            "subject_distribution": dict(Counter(row["subject"] for row in rows)),
        })
    # Preserve earlier successful FinQA/TAT-QA records and statuses when
    # staging only the three extra sources. Never delete prior data files.
    combined = dict(previous)
    combined.update({x["source"]: x for x in summaries})
    summaries = [combined[key] for key in SOURCE_MAP if key in combined]
    report = {"schema": 1, "model_trained": False, "training_ready": False, "sources": summaries}
    (output / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "public_manifest.json").write_text(
        json.dumps(public_manifest(report), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage external datasets for private CA research and human review")
    parser.add_argument("--output", type=Path, default=Path("data/datasets/unified"))
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--sources", nargs="+", choices=("all", *SOURCE_MAP), default=("all",))
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--allow-noncommercial", action="store_true")
    options = parser.parse_args()
    import os
    include = tuple(SOURCE_MAP) if "all" in options.sources else tuple(dict.fromkeys(options.sources))
    result = integrate(options.output, limit=options.limit, include=include,
                       download=options.download, hf_token=os.getenv("HF_TOKEN"),
                       allow_noncommercial=options.allow_noncommercial)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
