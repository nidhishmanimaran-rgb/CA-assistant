"""Clean licensed examples and split connected scenario families without numerical leakage."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import re

ALLOWED_LICENSES={"CC0-1.0","CC-BY-4.0","owned","permission"}


def normalized_question(text):
    return re.sub(r"\s+"," ",re.sub(r"\d[\d,.]*","<number>",text.casefold())).strip()


def prepare(records, output: Path, seed=42):
    cleaned=[]
    seen=set()
    for record in records:
        if record.get("license") not in ALLOWED_LICENSES or record.get("rights_confirmed") is not True:
            raise ValueError("Every example needs a permitted license and confirmed processing/training rights.")
        if record.get("human_reviewed") is not True or not str(record.get("reviewer","")).strip():
            raise ValueError("Training examples need an identified human reviewer.")
        required=("id","question","answer","scenario_family","attempt","answer_format")
        if any(not isinstance(record.get(key),str) or not record[key].strip() for key in required):
            raise ValueError("A training example is missing required metadata.")
        record={key:value.strip() if isinstance(value,str) else value for key,value in record.items()}
        if len(record["question"])>4000 or len(record["answer"])>20000:
            raise ValueError("An example exceeds the text limit.")
        if re.search(r"sk-[A-Za-z0-9_-]{16,}|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",record["question"]+" "+record["answer"]):
            raise ValueError("Remove potential credentials or personal email addresses from training text.")
        digest=hashlib.sha256((record["question"]+"\0"+record["answer"]).encode()).hexdigest()
        if digest not in seen:
            seen.add(digest)
            cleaned.append(record)
    if len({record["id"] for record in cleaned})!=len(cleaned):
        raise ValueError("Example IDs must be unique.")
    # Union both explicit scenario families and prompts equivalent after removing values.
    parent=list(range(len(cleaned)))
    def find(index):
        while parent[index]!=index:
            parent[index]=parent[parent[index]]
            index=parent[index]
        return index
    owners={}
    for index,record in enumerate(cleaned):
        for key in (("family",record["scenario_family"]),("template",normalized_question(record["question"]))):
            if key in owners:
                parent[find(index)]=find(owners[key])
            else:
                owners[key]=index
    groups=defaultdict(list)
    for index,record in enumerate(cleaned):
        groups[find(index)].append(record)
    grouped=list(groups.values())
    if len(grouped)<3:
        raise ValueError("Provide at least three independent scenario families for train/validation/test splits.")
    random.Random(seed).shuffle(grouped)
    train_count=max(1,min(len(grouped)-2,int(len(grouped)*0.6)))
    validation_count=max(1,min(len(grouped)-train_count-1,int(len(grouped)*0.2)))
    allocations={"train":grouped[:train_count],
                 "validation":grouped[train_count:train_count+validation_count],
                 "test":grouped[train_count+validation_count:]}
    output.mkdir(parents=True,exist_ok=True)
    manifest={"seed":seed,"counts":{},"ids":{},"sha256":{},"reviewed":True,
              "licenses":sorted({row["license"] for row in cleaned})}
    for name,group_list in allocations.items():
        rows=[row for group in group_list for row in group]
        formatted=[{"contents":[
            {"role":"user","parts":[{"text":f"Attempt: {row['attempt']}\nStyle: {row['answer_format']}\n{row['question']}"}]},
            {"role":"model","parts":[{"text":row["answer"]}]},
        ]} for row in rows]
        data="".join(json.dumps(row,ensure_ascii=False)+"\n" for row in formatted)
        path=output/f"{name}.jsonl"
        path.write_text(data,encoding="utf-8")
        manifest["counts"][name]=len(rows)
        manifest["ids"][name]=[row["id"] for row in rows]
        manifest["sha256"][name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("input",type=Path)
    parser.add_argument("--output",type=Path,default=Path("data/training/prepared"))
    args=parser.parse_args()
    records=[json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(json.dumps(prepare(records,args.output),indent=2))
