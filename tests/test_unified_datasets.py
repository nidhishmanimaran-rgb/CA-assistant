"""Offline tests: no source download or network access required."""
import json

from training.unified_datasets import (
    SOURCES, classify_topic, integrate, parse_finqa, parse_tatqa, public_manifest,
)


def test_registry_has_five_sources_and_separate_roles():
    assert len(SOURCES) == 5
    assert sum(s.role == "training_candidate" for s in SOURCES) == 2
    assert sum(s.role == "evaluation_only" for s in SOURCES) == 3


def test_en_qa_normalization_and_chinese_filter():
    rows = parse_finqa([
        {"id": "a", "qa": {"question": "Calculate NPV.", "exe_ans": "42",
                            "program": "subtract(43,1)"}},
        {"id": "b", "qa": {"question": "你好", "exe_ans": "42"}},
    ])
    assert len(rows) == 1
    assert rows[0]["subject"] == "Financial Management"
    assert rows[0]["approved_for_training"] is False


def test_tatqa_question_extraction():
    rows = parse_tatqa([
        {"paragraphs": [{"text": "A cash flow statement"}],
         "questions": [{"uid": "1", "question": "What is the cash flow?",
                         "answer": 125}]}
    ])
    assert len(rows) == 1
    assert rows[0]["answer"] == "125"
    assert rows[0]["human_reviewed"] is False


def test_classifier_is_conservative():
    assert classify_topic("Calculate depreciation on machinery")[0] == "Advanced Accounting"
    assert classify_topic("What happened yesterday?")[0] == "Unclassified"


def test_default_metadata_only_and_public_redaction(tmp_path):
    output = tmp_path / "private"
    report = integrate(output)
    assert all(x["status"] == "registered" for x in report["sources"])
    assert not list(output.glob("*.jsonl"))
    saved = json.loads((output / "public_manifest.json").read_text())
    assert "license" not in saved["sources"][0]
    assert saved == public_manifest(report)
    assert not saved["training_ready"]
