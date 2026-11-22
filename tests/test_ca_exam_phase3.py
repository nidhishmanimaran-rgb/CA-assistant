import json
import re
from decimal import Decimal
from pathlib import Path
from ca_exam_phase3 import example, generate, TRAIN_FAMILIES, TEST_FAMILIES
import random


def test_generate_all_families_have_10_16_and_answers(tmp_path):
    for family in (*TRAIN_FAMILIES, *TEST_FAMILIES):
        for n in range(14):
            subj, topic, q, a = example(family, n, random.Random(1000+n))
            assert len(q) > 120
            assert len(a) > 270
            assert 'Original ' in q
            assert '₹' in a or family == 'audit_evidence_theory'
            assert 'NaN' not in a


def test_splits_are_family_disjoint_and_reproducible(tmp_path):
    p = tmp_path/'one'
    manifest = generate(p, 8, 4)
    assert manifest['training_records'] == 32
    assert manifest['evaluation_records'] == 16
    assert set(manifest['train_families']).isdisjoint(manifest['held_out_families'])
    assert not manifest['human_review_completed']
    first = (p/'train_sft.jsonl').read_bytes()
    assert first == (p/'train_sft.jsonl').read_bytes()
    with (p/'train_records.jsonl').open() as file:
        for row in map(json.loads,file):
            assert row['human_reviewed'] is False
            assert row['split'] == 'train'
            assert row['marks'] in (10,16)
            assert row['scenario_family'] in TRAIN_FAMILIES
    assert (p/'review_sheet.csv').exists()


def test_ppe_disposal_balanced():
    for i in range(50):
        _, _, _, answer = example('ppe_disposal',i,random.Random(i))
        assert 'Total debits = total credits' in answer


def test_material_variance_reconcile():
    for i in range(50):
        _, _, _, answer = example('material_variance',i,random.Random(i))
        assert 'Reconciliation' in answer

