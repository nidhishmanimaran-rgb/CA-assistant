"""Opt-in inference against a returned tuned Vertex endpoint, for evaluation before promotion."""
import argparse
import json
import re
from training.run import cloud_session


def predict(endpoint,question,session):
    if not re.fullmatch(r"projects/[a-zA-Z0-9-]+/locations/us-central1/endpoints/[a-zA-Z0-9_-]+",endpoint):
        raise ValueError("Use the exact tuned endpoint name returned by Vertex.")
    if not question.strip() or len(question)>4000:
        raise ValueError("Supply a question of 1–4000 characters.")
    response=session.post("https://us-central1-aiplatform.googleapis.com/v1/"+endpoint+":generateContent",
        json={"contents":[{"role":"user","parts":[{"text":question}]}],
              "generationConfig":{"maxOutputTokens":1024}},timeout=40)
    response.raise_for_status()
    return response.json()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--endpoint",required=True)
    parser.add_argument("--question",required=True)
    parser.add_argument("--allow-paid-inference",action="store_true")
    args=parser.parse_args()
    if not args.allow_paid_inference:
        parser.error("Paid inference requires --allow-paid-inference.")
    print(json.dumps(predict(args.endpoint,args.question,cloud_session()),ensure_ascii=False,indent=2))
