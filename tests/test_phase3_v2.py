import hashlib
import json
import random
import tempfile
from decimal import Decimal
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from training.phase3_v2 import (make_example, create, TRAIN_FAMILIES, TEST_FAMILIES)


def test_phase3_v2_split_reproducibility():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'data'
        m=create(p,train_per_family=8,eval_per_family=4)
        assert m['training_records']==32
        assert m['evaluation_records']==16
        assert not m['human_review_completed']
        assert set(TRAIN_FAMILIES).isdisjoint(TEST_FAMILIES)
        assert hashlib.sha256((p/'train_sft.jsonl').read_bytes()).hexdigest()==m['sha256_train']
        a=(p/'train_sft.jsonl').read_bytes()
        create(p,8,4)
        assert (p/'train_sft.jsonl').read_bytes()==a
        tr=[json.loads(s) for s in (p/'train_records.jsonl').read_text().splitlines()]
        ev=[json.loads(s) for s in (p/'eval_records.jsonl').read_text().splitlines()]
        assert not ({r['question'] for r in tr}&{r['question'] for r in ev})
        assert all(r['marks'] in (10,16) and r['human_reviewed'] is False for r in tr+ev)
        assert (p/'review_sheet.csv').exists()


def test_all_numerical_invariants():
    for family in TRAIN_FAMILIES+TEST_FAMILIES:
        for i in range(80):
            sub,topic,marks,q,a,checks=make_example(family,i,random.Random(10000+i))
            assert len(q)>140 and len(a)>260
            assert marks in (10,16)
            if checks['domain']=='disposal':
                assert checks['debits']==checks['credits']
                assert checks['gain']*checks['loss']==0
                assert 'Dr Bank' in a and 'Cr Machinery' in a
            elif checks['domain']=='variance':
                assert checks['price']+checks['usage']==checks['total']
                assert 'Favourable' in a or 'Adverse' in a or 'Nil' in a
            elif checks['domain']=='wacc':
                assert Decimal(checks['wacc'])>0
                assert 'After-tax cost of debt' in a
            elif checks['domain']=='audit':
                assert 'quantity' in a and 'quality' in a
                assert 'SA 505' in a
                assert 'management' in a
                assert '**Case-specific response:**' in a
                assert 'physical inventory' not in a.lower()
            else:
                raise AssertionError(checks)


def test_every_family_has_both_marks():
    with tempfile.TemporaryDirectory() as d:
        create(Path(d), 8, 4)
        for split in ('train','eval'):
            data=[json.loads(x) for x in (Path(d)/f'{split}_records.jsonl').read_text().splitlines()]
            families={r['scenario_family'] for r in data}
            for family in families:
                assert {r['marks'] for r in data if r['scenario_family']==family} == {10,16}


def test_phase4_flags_do_not_claim_auto_accuracy():
    from training.phase4_flagged_review import find_flags, make_review
    q='Audit trade receivables and explain sufficiency and appropriateness'
    bad='Sufficiency is enough evidence. Physical inventory counting and vendor statements.'
    assert len(find_flags(q,bad)) >= 3
    good='Sufficiency means quantity; appropriateness concerns relevance and reliability; obtain debtor confirmations.'
    assert not find_flags(q,good)
    assumption = 'Sufficiency is quantity, appropriateness is relevance and reliability. The auditee has adequate internal controls.'
    assert any('internal controls' in flag for flag in find_flags(q,assumption))
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)
        (p/'comparison.json').write_text(json.dumps([{'question': q,'phase3_answer':bad}]))
        assert make_review(p/'comparison.json',p/'review.csv') == 1
        assert (p/'review.csv').exists()


def test_comparison_review_rows_are_not_auto_scored():
    from training.phase3_v2_compare import create_review_rows
    from training.phase4_flagged_review import find_flags
    question = 'Audit trade receivables, sufficiency, appropriateness and evidence quality'
    cases = [{
        'question': question,
        'phase3_answer': 'Physical inventory counting is sufficient.',
        'phase3_v2_answer': 'Sufficiency is quantity; appropriateness is relevance and reliability. Confirm receivables.',
    }]
    review = create_review_rows(cases, find_flags)
    assert len(review) == 1
    assert review[0]['phase3_score'] == ''
    assert review[0]['phase3_v2_score'] == ''
    assert 'physical inventory' in review[0]['potential_issues_for_review'].lower() or 'receivables' in review[0]['potential_issues_for_review'].lower()
