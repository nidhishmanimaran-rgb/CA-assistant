import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from training.prepare import prepare
from training.run import build_request, submit, verify_submission
from evaluation.compare import compare


def records():
    topics=["residual amount","straight line","reducing balance","remaining life","rounding policy","partial year"]
    return [{"id":str(index),"question":f"Explain {topic}.","answer":f"Verified test fixture for {topic}.",
             "scenario_family":topic,"attempt":"May 2027","answer_format":"Detailed solution",
             "license":"owned","rights_confirmed":True,"human_reviewed":True,"reviewer":"test-fixture-reviewer"}
            for index,topic in enumerate(topics)]


def test_dataset_splits_and_license_guards(tmp_path):
    data=records()
    manifest=prepare(data,tmp_path)
    assert sum(manifest["counts"].values())==6
    sets=[set(values) for values in manifest["ids"].values()]
    assert not sets[0]&sets[1] and not sets[0]&sets[2] and not sets[1]&sets[2]
    with pytest.raises(ValueError,match="rights"):
        prepare([{**data[0],"rights_confirmed":False}],tmp_path/"bad")
    with pytest.raises(ValueError,match="reviewer"):
        prepare([{**data[0],"human_reviewed":False}],tmp_path/"bad")


def test_changed_numbers_cannot_cross_splits(tmp_path):
    data=records()+[
        {**records()[0],"id":"variant1","question":"Asset costs 100000 over 5 years.","scenario_family":"one"},
        {**records()[0],"id":"variant2","question":"Asset costs 850000 over 8 years.","scenario_family":"two"},
    ]
    manifest=prepare(data,tmp_path)
    locations={name for name,ids in manifest["ids"].items() if "variant1" in ids or "variant2" in ids}
    assert len(locations)==1


def configuration():
    return {"project_id":"ca-tutor-test","location":"us-central1","model":"gemini-2.5-flash",
            "training_uri":"gs://private-test-bucket/train.jsonl","validation_uri":"gs://private-test-bucket/validation.jsonl",
            "epoch_count":2,"adapter_size":4,"estimated_training_tokens":100000,"training_price_per_million":5,
            "dataset_reviewed":True}


def test_training_payload_matches_provider_contract():
    url,body=build_request(configuration())
    assert url.endswith("/tuningJobs")
    assert body["supervisedTuningSpec"]["hyperParameters"]["epochCount"]==2
    assert body["supervisedTuningSpec"]["exportLastCheckpointOnly"] is False


def test_submission_requires_budget_and_reviewed_dataset(tmp_path):
    data=[]
    for family in range(10):
        for index in range(20):
            data.append({**records()[0],"id":f"{family}-{index}",
                         "question":f"Explain scenario {chr(97+family)}: asset {index}.",
                         "scenario_family":f"family-{family}"})
    prepare(data,tmp_path)
    config=configuration()
    with pytest.raises(ValueError,match="budget"):
        verify_submission(config,tmp_path/"manifest.json","0")
    session=Mock()
    session.post.return_value=Mock(json=lambda:{"name":"projects/ca-tutor-test/locations/us-central1/tuningJobs/test-job"})
    result=submit(config,tmp_path/"manifest.json","2",session)
    assert result["job"]["name"].endswith("test-job")
    session.post.assert_called_once()
    (tmp_path/"train.jsonl").write_text("tampered",encoding="utf-8")
    with pytest.raises(ValueError,match="changed"):
        verify_submission(config,tmp_path/"manifest.json","2")


def test_comparison_rejects_different_datasets():
    baseline={"dataset_sha256":"a","mode":"offline_system_checks","records":[],"scores":{}}
    with pytest.raises(ValueError):
        compare(baseline,{**baseline,"dataset_sha256":"b"})
