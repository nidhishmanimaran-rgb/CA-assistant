from pathlib import Path
import subprocess
import tomllib
from scripts.check_release import check

ROOT=Path(__file__).resolve().parents[1]


def test_security_sensitive_files_are_ignored():
    paths=[".env",".streamlit/secrets.toml","data/knowledge.sqlite","uploads/private.pdf",
           "knowledge_base/book.pdf","data/training/train.jsonl","ca-chat-session.json"]
    result=subprocess.run(["git","check-ignore","-z","--stdin"],input=("\0".join(paths)+"\0").encode(),
                          capture_output=True,cwd=ROOT,check=True)
    assert set(result.stdout.decode().strip("\0").split("\0"))==set(paths)


def test_release_configuration_is_valid():
    result=check(ROOT)
    assert result["python_files_parsed"]>15
    assert not result["cloud_deployed"]
    config=tomllib.loads((ROOT/".streamlit/secrets.example.toml").read_text())
    assert config["REQUIRE_PASSWORD"] is True and config["ALLOW_PAID_API"] is False
    workflow=(ROOT/".github/workflows/tests.yml").read_text()
    assert "contents: read" in workflow and "pull_request_target" not in workflow
    assert "secrets." not in workflow
    docker=(ROOT/"Dockerfile").read_text()
    assert "USER appuser" in docker and "HEALTHCHECK" in docker
