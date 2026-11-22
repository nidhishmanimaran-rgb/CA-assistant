"""Compare evaluations only when the case set and evaluation mode are identical."""
import argparse
import json
from pathlib import Path


def compare(baseline,candidate):
    if baseline["dataset_sha256"]!=candidate["dataset_sha256"] or baseline["mode"]!=candidate["mode"]:
        raise ValueError("Compare the same dataset and evaluation mode.")
    before={item["id"]:item for item in baseline["records"]}
    after={item["id"]:item for item in candidate["records"]}
    if before.keys()!=after.keys():
        raise ValueError("Evaluation case IDs differ.")
    return {"regressions":[key for key in before if before[key]["passed"] and not after[key]["passed"]],
            "improvements":[key for key in before if not before[key]["passed"] and after[key]["passed"]],
            "baseline_scores":baseline["scores"],"candidate_scores":candidate["scores"]}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("baseline",type=Path)
    parser.add_argument("candidate",type=Path)
    args=parser.parse_args()
    print(json.dumps(compare(json.loads(args.baseline.read_text()),json.loads(args.candidate.read_text())),indent=2))
