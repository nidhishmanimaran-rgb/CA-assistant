"""Offline system evaluation. Reports do not claim measured live-model reasoning quality."""
import argparse
from collections import defaultdict
from dataclasses import replace
import hashlib
import json
from pathlib import Path

from backend.calculator import calculate
from backend.citations import validate_answer
from backend.embeddings import LocalEmbeddings
from backend.errors import AppError
from backend.session import StudyContext
from backend.solver import solve_question
from backend.syllabus_versions import DocumentMeta, applicable
from config.catalog import MVP_CHAPTER

DATASET = Path(__file__).with_name("test_questions.json")


def check_case(case):
    category = case["category"]
    if category == "numerical":
        result = calculate(case["method"], **case["inputs"])
        parsed, clarification = solve_question(case["question"])
        return (all(getattr(result,key)==value for key,value in case["expected"].items())
                and parsed is not None and parsed.depreciation==case["expected"]["depreciation"]
                and clarification is None)
    if category == "missing_information":
        result, clarification = solve_question(case["question"])
        return result is None and bool(clarification)
    if category == "concept_retrieval":
        texts = [case["evidence"], "An unrelated discussion about crop irrigation and rainfall."]
        vectors = LocalEmbeddings().encode([case["question"], *texts])
        scores = [sum(x*y for x,y in zip(vectors[0],vector)) for vector in vectors[1:]]
        return scores[0] > scores[1] and case["expected_keyword"] in case["evidence"].lower()
    variant = case["variant"]
    context = StudyContext("CA Intermediate","Advanced Accounting",MVP_CHAPTER,"May 2027","English","Detailed solution")
    metadata = DocumentMeta("Original note",context.level,context.subject,context.chapter,context.attempt,"1","2026-11-21")
    if variant in ("matching_attempt","wrong_attempt","wrong_subject","wrong_year"):
        if variant=="wrong_attempt":
            return not applicable(metadata,replace(context,attempt="September 2027"))
        if variant=="wrong_subject":
            return not applicable(metadata,replace(context,subject="Taxation"))
        if variant=="wrong_year":
            legal=replace(metadata,subject="Taxation",assessment_year="2027-28",effective_from="2026-04-01")
            return not applicable(legal,replace(context,subject="Taxation",assessment_year="2026-27",as_of="2026-11-22"))
        return applicable(metadata,context)
    quote="Straight-line depreciation allocates cost less residual value over useful life."
    sources=[{"source_id":"S1","text":quote}]
    claim={"statement":"Allocate the depreciable amount over useful life.","source_id":"S1","quote":quote}
    if variant=="unknown_id":
        claim["source_id"]="S99"
    if variant=="wrong_quote":
        claim["quote"]="This quotation was invented and is absent from the source."
    payload={"status":"answer","answer":"","claims":[] if variant=="missing_citation" else [claim]}
    try:
        validate_answer(payload,sources,True)
        return variant=="valid"
    except AppError:
        return variant!="valid"


def evaluate(path=DATASET):
    cases=json.loads(path.read_text(encoding="utf-8"))
    records=[]
    scores=defaultdict(lambda: {"passed":0,"total":0})
    for case in cases:
        try:
            passed=bool(check_case(case))
            error=None
        except Exception as exception:
            passed=False
            error=type(exception).__name__
        records.append({"id":case["id"],"category":case["category"],"passed":passed,"error_type":error})
        scores[case["category"]]["total"]+=1
        scores[case["category"]]["passed"]+=int(passed)
    return {"mode":"offline_system_checks","dataset_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "scores":dict(scores),"records":records,"live_model_evaluation":"not_run",
            "limits":"Concept scores measure reference-note retrieval, not model reasoning. Citation checks establish identity and quotes, not semantic entailment. Numeric expectations use an independent Fraction oracle."}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path("data/evaluation/baseline.json"))
    args=parser.parse_args()
    result=evaluate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result["scores"],indent=2))
    raise SystemExit(0 if all(row["passed"] for row in result["records"]) else 1)


if __name__=="__main__":
    main()
