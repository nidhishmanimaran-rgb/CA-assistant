"""Opt-in live model/tool evaluation. Saves responses for human review; never runs in CI."""
import argparse
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from backend.ai_engine import SYSTEM_PROMPT, execute_calculation_tool
from backend.citations import validate_answer
from backend.errors import AppError
from backend.providers import OpenAIProvider
from backend.session import StudyContext
from backend.usage import UsageLedger
from config.catalog import MVP_CHAPTER
from config.settings import load_settings
from evaluation.evaluate import DATASET


def run_model(provider,cases,context):
    rows=[]
    for case in cases:
        sources=[]
        if case["category"]=="concept_retrieval":
            sources=[{"source_id":"S1","text":case["evidence"]}]
        payload={"question":case["question"],"study_context":asdict(context),
                 "require_sources":bool(sources),"evidence":sources}
        try:
            output=provider.answer(SYSTEM_PROMPT,[{"role":"user","content":json.dumps(payload)}],allow_tools=True)
            if "tool" in output:
                result=execute_calculation_tool(output["tool"],case["question"])
                passed=case["category"]=="numerical" and result.depreciation==case["expected"]["depreciation"]
                answer=result.as_dict()
            else:
                answer=output["answer"]
                validate_answer(answer,sources,bool(sources))
                passed=(case["category"]=="concept_retrieval" and bool(answer["claims"])) or (
                    case["category"]=="missing_information" and answer["status"]=="clarification")
            rows.append({"id":case["id"],"category":case["category"],"passed":bool(passed),"response":answer})
        except AppError as error:
            rows.append({"id":case["id"],"category":case["category"],"passed":False,"error":str(error)})
    return rows


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--allow-paid-api",action="store_true")
    parser.add_argument("--limit",type=int,default=5)
    parser.add_argument("--output",type=Path,default=Path("data/evaluation/model.json"))
    args=parser.parse_args()
    settings=load_settings()
    if not args.allow_paid_api or not settings.api_enabled:
        parser.error("Configure API access and pass --allow-paid-api for a paid live evaluation.")
    if not 1<=args.limit<=76:
        parser.error("--limit must be 1–76. Rate and cost limits still apply.")
    cases=[case for case in json.loads(DATASET.read_text(encoding="utf-8")) if case["category"]!="source_grounding"][:args.limit]
    provider=OpenAIProvider(settings,UsageLedger(),"evaluation")
    context=StudyContext("CA Intermediate","Advanced Accounting",MVP_CHAPTER,"May 2027","English","Detailed solution")
    rows=run_model(provider,cases,context)
    scores=defaultdict(lambda:{"passed":0,"total":0})
    for row in rows:
        scores[row["category"]]["total"]+=1
        scores[row["category"]]["passed"]+=int(row["passed"])
    report={"mode":"model_contract_eval","model":settings.model,"dataset_sha256":hashlib.sha256(DATASET.read_bytes()).hexdigest(),
            "records":rows,"scores":dict(scores),"human_review":"required",
            "limits":"Passes check tool use, clarification or quotation contracts; they do not prove conceptual correctness or entailment."}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["scores"],indent=2))
