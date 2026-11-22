"""Read-only release checks. No live AI requests, training, or credential output."""
import argparse
import ast
import importlib.metadata
import json
from pathlib import Path
import tomllib


def check(root):
    files=[root/"app.py"]
    for folder in ("backend","config","ui","scripts","training","evaluation"):
        files.extend((root/folder).glob("*.py"))
    for path in files:
        ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
    for path in (root/"training").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    configuration=tomllib.loads((root/".streamlit/config.toml").read_text(encoding="utf-8"))
    assert configuration["server"]["enableCORS"] and configuration["server"]["enableXsrfProtection"]
    assert configuration["browser"]["gatherUsageStats"] is False
    packages={name:importlib.metadata.version(name) for name in (
        "streamlit","openai","pypdf","faiss-cpu","numpy","python-dotenv","jsonschema"
    )}
    native_faiss=True
    try:
        import faiss
        index=faiss.IndexFlatIP(2)
        import numpy as np
        index.add(np.array([[1.,0.],[0.,1.]],dtype="float32"))
        scores,indices=index.search(np.array([[1.,0.]],dtype="float32"),1)
        assert int(indices[0][0])==0
    except (ImportError,OSError):
        native_faiss=False
    return {"python_files_parsed":len(files),"packages":packages,"native_faiss":native_faiss,
            "retrieval_fallback":"available","cloud_deployed":False,
            "note":"This is local verification, not a Docker build or cloud deployment."}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--require-faiss",action="store_true")
    args=parser.parse_args()
    result=check(Path(__file__).resolve().parents[1])
    print(json.dumps(result,indent=2))
    raise SystemExit(1 if args.require_faiss and not result["native_faiss"] else 0)
