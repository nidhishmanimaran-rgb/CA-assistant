"""Google Vertex supervised-tuning REST pipeline. Dry-run is the default; submission is gated."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re


def build_request(config):
    project,location=config.get("project_id",""),config.get("location","")
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]",project):
        raise ValueError("Set a valid Google Cloud project_id.")
    if location!="us-central1" or config.get("model")!="gemini-2.5-flash":
        raise ValueError("This tested configuration uses gemini-2.5-flash in us-central1. Revalidate provider support before changing it.")
    for key in ("training_uri","validation_uri"):
        if not re.fullmatch(r"gs://[a-z0-9][a-z0-9._-]+/[^\s]+\.jsonl",config.get(key,"")):
            raise ValueError(f"Set {key} to the authorized GCS JSONL dataset.")
    epochs=config.get("epoch_count",2)
    adapter=config.get("adapter_size",4)
    if type(epochs) is not int or not 1<=epochs<=5 or adapter not in (1,2,4,8,16):
        raise ValueError("Use 1–5 epochs and a supported adapter size.")
    body={"baseModel":config["model"],"supervisedTuningSpec":{
        "trainingDatasetUri":config["training_uri"],"validationDatasetUri":config["validation_uri"],
        "hyperParameters":{"epochCount":epochs,"adapterSize":adapter,"learningRateMultiplier":1},
        "exportLastCheckpointOnly":False,
    },"tunedModelDisplayName":"ca-tutor-reviewed"}
    url=f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/tuningJobs"
    return url,body


def verify_submission(config, manifest_path, approved_budget):
    if config.get("dataset_reviewed") is not True:
        raise ValueError("Review the licensed dataset and set dataset_reviewed before submitting.")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest.get("reviewed") or manifest["counts"]["train"]<100:
        raise ValueError("This project requires at least 100 reviewed training examples before a paid run.")
    for name in ("train","validation","test"):
        path=manifest_path.parent/f"{name}.jsonl"
        if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest["sha256"][name]:
            raise ValueError("The prepared dataset changed after validation.")
    price=Decimal(str(config.get("training_price_per_million") or 0))
    tokens=int(config.get("estimated_training_tokens",0))
    budget=Decimal(str(approved_budget))
    if not price.is_finite() or not budget.is_finite() or price<=0 or tokens<=0 or budget<=0:
        raise ValueError("Provide a current training price, token estimate and explicitly approved positive budget.")
    estimate=Decimal(tokens)*config.get("epoch_count",2)*price/Decimal(1_000_000)
    if estimate>budget:
        raise ValueError("The estimated training charge exceeds the approved budget.")
    return estimate


def submit(config, manifest_path, approved_budget, session):
    url,body=build_request(config)
    estimate=verify_submission(config,manifest_path,approved_budget)
    # No automatic POST retry: a timeout may already have created a paid job.
    response=session.post(url,json=body,timeout=60)
    response.raise_for_status()
    result=response.json()
    if not result.get("name"):
        raise ValueError("No job identity returned. Inspect the cloud console before retrying.")
    return {"job":result,"estimated_training_usd":str(estimate),
            "warning":"Estimate is not a provider-enforced spending cap. Check cloud billing alerts and job status."}


def cloud_session():
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    credentials,_=google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return AuthorizedSession(credentials)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",type=Path,default=Path("training/config.example.json"))
    parser.add_argument("--manifest",type=Path,default=Path("data/training/prepared/manifest.json"))
    parser.add_argument("--submit",action="store_true")
    parser.add_argument("--approve-budget-usd",default="0")
    parser.add_argument("--status",help="Exact projects/.../locations/us-central1/tuningJobs/... name")
    parser.add_argument("--output",type=Path,default=Path("data/training/job.json"))
    args=parser.parse_args()
    config=json.loads(args.config.read_text(encoding="utf-8"))
    try:
        url,body=build_request(config)
        if args.status:
            prefix=f"projects/{config['project_id']}/locations/{config['location']}/tuningJobs/"
            if not args.status.startswith(prefix) or not re.fullmatch(r"[A-Za-z0-9_-]+",args.status[len(prefix):]):
                raise ValueError("Status requires a job belonging to the configured project and location.")
            response=cloud_session().get("https://us-central1-aiplatform.googleapis.com/v1/"+args.status,timeout=30)
            response.raise_for_status()
            result=response.json()
        elif args.submit:
            verify_submission(config,args.manifest,args.approve_budget_usd)
            result=submit(config,args.manifest,args.approve_budget_usd,cloud_session())
        else:
            print(json.dumps({"mode":"dry_run","url":url,"request":body,"submitted":False},indent=2))
            return
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2),encoding="utf-8")
        print(f"Saved provider result to {args.output}. Inspect the status; submission is not completion.")
    except Exception as error:
        if isinstance(error,ValueError):
            print("Blocked: "+str(error))
        else:
            print("Cloud operation failed. No credentials were printed. For an uncertain POST result, inspect the console before retrying.")
        raise SystemExit(2)


if __name__=="__main__":
    main()
