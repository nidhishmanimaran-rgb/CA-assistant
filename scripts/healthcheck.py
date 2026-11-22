"""Check an explicitly selected Streamlit health endpoint without exposing configuration."""
import argparse
import json
from urllib.request import urlopen


def health(url):
    with urlopen(url.rstrip("/")+"/_stcore/health",timeout=5) as response:
        return response.status==200 and response.read().strip()==b"ok"


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",default="http://127.0.0.1:8501")
    args=parser.parse_args()
    try:
        healthy=health(args.url)
    except Exception:
        healthy=False
    print(json.dumps({"healthy":healthy}))
    raise SystemExit(0 if healthy else 1)
