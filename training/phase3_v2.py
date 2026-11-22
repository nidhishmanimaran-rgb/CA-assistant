"""Original remediation data for experimental CA-tutor QLoRA training.

NOT an ICAI answer key. Subject-matter review is required. This generator
creates new variants; earlier Phase 4 diagnostic cases must not be reused for
claiming unbiased model accuracy once these topics are fine-tuned.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import random

D = Decimal
CENTS = D('0.01')


def rupees(value):
    return f"₹{D(value).quantize(CENTS, rounding=ROUND_HALF_UP):,.2f}"


def percentage(value):
    return f"{D(value).quantize(CENTS, rounding=ROUND_HALF_UP):,.2f}%"


SYSTEM = (
    "You are an independent English-language CA study tutor. Answer the specific "
    "question only; never pad a 10- or 16-mark answer with unrelated procedures. "
    "For calculations give formula, substitutions, balanced entries and a conclusion. "
    "For audit questions distinguish sufficient (quantity) from appropriate "
    "(relevant and reliable); link procedures to the assertion, and do not "
    "presume effective controls. Mention uncertainty where applicable."
)

TRAIN_FAMILIES = (
    'audit_receivables_teaching', 'disposal_journals_teaching',
    'material_variance_teaching', 'wacc_teaching',
)
TEST_FAMILIES = (
    'audit_receivables_new_cases', 'disposal_journals_new_cases',
    'material_variance_new_cases', 'wacc_new_cases',
)


def make_example(family: str, index: int, rng: random.Random):
    marks = 10 if index % 2 == 0 else 16
    family_key = family.replace('_teaching', '').replace('_new_cases', '')
    if family_key == 'audit_receivables':
        subject, topic = 'Auditing and Ethics', 'SA 500/505: trade receivables evidence'
        fact = rng.choice([
            'the largest customer has not replied to an external confirmation',
            'the receivables ageing lists several overdue customers',
            'management says sales invoices alone are sufficient',
            'customer balances differ from confirmation responses',
            'a large receivable was recorded immediately before year-end',
            'management considers its own oral explanations conclusive',
        ])
        customer_balance = rng.randint(45, 900) * 10000
        question = (
            f'(Original {marks}-mark practice scenario) While auditing trade receivables '
            f'of {rupees(customer_balance)}, {fact}. Explain sufficiency and appropriateness of audit evidence, '
            'distinguish relevance from reliability, and propose procedures linked to '
            'existence, valuation and cut-off. Explain why adding more unreliable '
            'documents cannot necessarily overcome poor-quality evidence.'
        )
        if marks == 16:
            question += (' Address non-responses/discrepancies and describe how risk '
                         'assessment affects the quantity of evidence needed.')
        answer = (
            '**1. Core concepts (SA 500):** Sufficiency means **quantity** of audit '
            'evidence; the quantity required depends on assessed risk and evidence '
            'quality. Appropriateness means **quality**: relevance to the assertion '
            'and reliability of the information. More low-quality evidence does not '
            'necessarily replace persuasive, relevant independent evidence.\n\n'
            '**2. Procedures relevant to trade receivables:**\n'
            '- **Existence:** Select customer balances and obtain direct written '
            'confirmations under SA 505, retaining auditor control over requests '
            'and responses. Investigate exceptions and non-responses; apply '
            'alternative procedures such as inspecting subsequent collections and '
            'underlying sales/shipping records where appropriate.\n'
            '- **Valuation:** Examine ageing, subsequent receipts, credit histories '
            'and disputes; assess expected credit losses or impairment under the '
            'applicable accounting framework.\n'
            '- **Cut-off:** Test transactions near year-end against dispatch/delivery '
            'evidence, invoices, dates and credit notes.\n\n'
            '**3. Reliability judgment:** Independent external confirmations may be '
            'more reliable than uncorroborated management inquiries; reliability '
            'depends on circumstances. Subsequent receipts must be traced to '
            'the individual customer and invoice; unsupported management '
            'explanations are not conclusive evidence. Procedures should be '
            'selected for the specific receivable assertion.\n\n'
            f'**4. Apply to facts:** Here, {fact}. The auditor should investigate '
            'the stated risk, evaluate the relevant assertion, and corroborate '
            'management representations with more persuasive evidence.'
        )
        if marks == 16:
            answer += (
                '\n\n**5. Extent and exceptions:** Higher assessed risk can require '
                'more persuasive evidence or larger appropriate samples. Follow up '
                'on non-responses, discrepancies and contradictory information; '
                'consider implications if sufficient appropriate evidence cannot '
                'be obtained. Do not conclude controls are effective without testing.'
            )
        # The response must deal with the actual scenario, not merely recite a list.
        case_actions = {
            'the largest customer has not replied to an external confirmation':
                'Because the largest customer did not respond, verify the address and request, '
                'consider follow-up where appropriate, and perform alternative procedures '
                'such as tracing later payments and invoices/delivery evidence; reassess '
                'whether sufficient appropriate evidence has been obtained.',
            'the receivables ageing lists several overdue customers':
                'For overdue balances, inspect subsequent receipts, correspondence and '
                'customer disputes, and challenge assumptions in the impairment allowance.',
            'management says sales invoices alone are sufficient':
                'An invoice issued internally does not alone establish collectability or '
                'even that the recorded debtor owes the amount; corroborate with external '
                'confirmations, delivery evidence and subsequent receipts as appropriate.',
            'customer balances differ from confirmation responses':
                'Reconcile confirmation discrepancies to cash in transit, credit notes, '
                'returns or cut-off errors using source documents; assess misstatement risk.',
            'a large receivable was recorded immediately before year-end':
                'Inspect dispatch and acceptance evidence, contractual terms, invoices and '
                'post-year-end credits or returns to assess existence and period cut-off.',
            'management considers its own oral explanations conclusive':
                'Inquiries alone provide less persuasive support; corroborate with '
                'independent confirmations, documentary evidence and subsequent receipts.',
        }
        answer += '\n\n**Case-specific response:** ' + case_actions[fact]
        checks = {'domain': 'audit', 'fact': fact}


    elif family_key == 'disposal_journals':
        subject, topic = 'Advanced Accounting', 'Machinery disposal and journal entries'
        life = rng.choice([5, 6, 7, 8, 10])
        dep = rng.randint(4, 20) * 10000
        residual = rng.randint(1, 9) * 5000
        cost = dep * life + residual
        years = rng.randint(2, min(life - 1, 4))
        accumulated = dep * years
        carrying = cost - accumulated
        delta = rng.randint(1, 8) * 5000 * rng.choice([-1, 1])
        proceeds = carrying + delta
        gain = max(delta, 0)
        loss = max(-delta, 0)
        debit_total = proceeds + accumulated + loss
        credit_total = cost + gain
        assert debit_total == credit_total and carrying > 0 and proceeds > 0
        question = (
            f'(Original {marks}-mark practice scenario) Machinery cost {rupees(cost)}; '
            f'its expected residual value was {rupees(residual)} and its useful life '
            f'{life} years. After {years} **complete years** of straight-line '
            f'depreciation, it is sold for {rupees(proceeds)}. Assume no impairment '
            'or revaluation. Calculate annual depreciation, accumulated depreciation, '
            'carrying amount and gain/loss on disposal. Prepare a balanced disposal '
            'journal entry with working notes.'
        )
        if marks == 16:
            question += ' Also explain treatment of the disposed asset and its accumulated depreciation.'
        outcome = f'gain {rupees(gain)}' if gain else f'loss {rupees(loss)}'
        answer = (
            f'**Working 1 — Annual depreciation:** ({rupees(cost)} − {rupees(residual)}) '
            f'÷ {life} = **{rupees(dep)}**.\n\n'
            f'**Working 2 — Accumulated depreciation:** {years} × {rupees(dep)} '
            f'= **{rupees(accumulated)}**.\n\n'
            f'**Working 3 — Carrying amount:** {rupees(cost)} − {rupees(accumulated)} '
            f'= **{rupees(carrying)}**.\n\n'
            f'**Working 4 — Disposal:** Proceeds {rupees(proceeds)} minus carrying '
            f'amount {rupees(carrying)} gives **{outcome}**.\n\n'
            '**Disposal journal entry:**\n'
            f'- Dr Bank {rupees(proceeds)}\n'
            f'- Dr Accumulated depreciation {rupees(accumulated)}\n'
            + (f'- Dr Loss on disposal {rupees(loss)}\n' if loss else '')
            + f'- Cr Machinery (historical cost) {rupees(cost)}\n'
            + (f'- Cr Gain on disposal {rupees(gain)}\n' if gain else '')
            + f'**Check:** Total debits = total credits = {rupees(debit_total)}.'
        )
        if marks == 16:
            answer += ('\n\n**Explanation:** Remove the asset at historical cost and '
                       'reverse accumulated depreciation; recognize proceeds and the '
                       'difference from carrying amount as a gain or loss in profit or loss.')
        checks = {'domain': 'disposal', 'debits': debit_total, 'credits': credit_total,
                  'annual_depreciation': dep, 'carrying': carrying, 'gain': gain, 'loss': loss}

    elif family_key == 'material_variance':
        subject, topic = 'Cost and Management Accounting', 'Material price and usage variances'
        production = rng.randint(100, 450)
        standard_per_unit = rng.randint(2, 7)
        sq = production * standard_per_unit
        aq = sq + rng.randint(-50, 50)
        sp = rng.randint(20, 60) * 5
        ap = sp + rng.randint(-12, 12)
        std = sq * sp
        actual = aq * ap
        price_v = aq * (sp - ap)
        usage_v = sp * (sq - aq)
        cost_v = std - actual
        assert price_v + usage_v == cost_v and ap > 0 and aq > 0
        label = lambda n: 'Nil (neither favourable nor adverse)' if n == 0 else (f'{rupees(abs(n))} ' + ('Favourable' if n > 0 else 'Adverse'))
        question = (
            f'(Original {marks}-mark practice scenario) Standard material use is '
            f'{standard_per_unit} kg per finished unit at {rupees(sp)} per kg. '
            f'Actual output: {production} units; material purchased and used: '
            f'{aq} kg at {rupees(ap)} per kg. Compute standard quantity allowed, '
            'material price variance, usage variance, total material cost variance, '
            'label each Favourable/Adverse and reconcile the components.'
        )
        if marks == 16:
            question += ' Explain one possible operational reason for price and usage variances.'
        answer = (
            f'**Standard quantity (SQ):** {production} × {standard_per_unit} '
            f'= **{sq} kg**.\n\n'
            f'**Material price variance:** AQ × (SP − AP) = {aq} × '
            f'({rupees(sp)} − {rupees(ap)}) = **{label(price_v)}**.\n\n'
            f'**Material usage variance:** SP × (SQ − AQ) = {rupees(sp)} × '
            f'({sq} − {aq}) = **{label(usage_v)}**.\n\n'
            f'**Material cost variance:** SQ×SP − AQ×AP = {rupees(std)} − '
            f'{rupees(actual)} = **{label(cost_v)}**.\n\n'
            f'**Reconciliation (signed, favourable positive):** {price_v:+,} '
            f'+ ({usage_v:+,}) = {cost_v:+,}. '
            'The two components agree exactly with total cost variance.'
        )
        if marks == 16:
            answer += ('\n\n**Interpretation:** Price differences may arise from '
                       'purchase price or supplier changes; usage differences may '
                       'arise from waste, quality or efficiency. These are possible '
                       'causes, not established facts from the question.')
        checks = {'domain': 'variance', 'sq': sq, 'price': price_v,
                  'usage': usage_v, 'total': cost_v}

    elif family_key == 'wacc':
        subject, topic = 'Financial Management', 'Market-value after-tax WACC'
        eq = rng.randint(3, 18) * 100000
        debt = rng.randint(2, 12) * 100000
        ke = D(rng.choice([11, 12, 14, 16, 18]))
        kd = D(rng.choice([7, 8, 9, 10, 11]))
        tax = D(rng.choice([20, 25, 30]))
        total = eq + debt
        tax_adjusted = kd * (D(100) - tax) / D(100)
        wacc = (D(eq) * ke + D(debt) * tax_adjusted) / D(total)
        assert (D(eq) / D(total)) + (D(debt) / D(total)) == 1
        question = (
            f'(Original {marks}-mark practice scenario) Market value of equity '
            f'{rupees(eq)}, market value of interest-bearing debt {rupees(debt)}; '
            f'cost of equity {percentage(ke)}, pre-tax cost of debt '
            f'{percentage(kd)} and applicable tax rate {percentage(tax)}. '
            'Assume interest deductibility is available and ignore other financing. '
            'Calculate after-tax WACC using market-value weights and show workings.'
        )
        if marks == 16:
            question += ' Explain why the cost of equity is not reduced by the debt tax shield.'
        answer = (
            f'**Total market value:** {rupees(eq)} + {rupees(debt)} '
            f'= **{rupees(total)}**.\n\n'
            f'**Weights:** Equity {eq}/{total} = {D(eq)/D(total):.6f}; '
            f'debt {debt}/{total} = {D(debt)/D(total):.6f}.\n\n'
            f'**After-tax cost of debt:** {percentage(kd)} × (1 − '
            f'{percentage(tax)}) = **{percentage(tax_adjusted)}**.\n\n'
            '**Formula:** WACC = E/(E + D) × Ke + D/(E + D) × Kd × (1 − T).\n'
            f'**Substitution (unrounded weights):** ({eq}/{total} × '
            f'{percentage(ke)}) + ({debt}/{total} × '
            f'{percentage(tax_adjusted)}) = **{percentage(wacc)}**.'
        )
        if marks == 16:
            answer += ('\n\n**Explanation:** The tax adjustment reflects the '
                       'assumed income-tax deduction for qualifying interest. '
                       'It applies to debt costs, not to the cost of equity. '
                       'Use market rather than book values as stated.')
        checks = {'domain': 'wacc', 'equity': eq, 'debt': debt, 'wacc': str(wacc)}

    else:
        raise ValueError(f'Unknown scenario family: {family}')

    assert len(question) > 140 and len(answer) > 260
    return subject, topic, marks, question, answer, checks


def create(output: Path, train_per_family: int = 36, eval_per_family: int = 8, seed: int = 2028):
    if not (2 <= train_per_family <= 100 and 2 <= eval_per_family <= 50):
        raise ValueError('train-per-family: 2..100; eval-per-family: 2..50')
    output.mkdir(parents=True, exist_ok=True)
    rows_by_split = {}
    sample_hashes = set()
    for split, families, count, split_seed in (
        ('train', TRAIN_FAMILIES, train_per_family, seed),
        ('eval', TEST_FAMILIES, eval_per_family, seed + 11111),
    ):
        rng = random.Random(split_seed)
        rows = []
        for family in families:
            for i in range(count):
                subject, topic, marks, q, a, checks = make_example(family, i, rng)
                q_hash = hashlib.sha256(q.encode('utf-8')).hexdigest()
                if q_hash in sample_hashes:
                    raise ValueError('Duplicate question generated')
                sample_hashes.add(q_hash)
                rows.append({
                    'id': f'phase3v2-{family}-{i:03d}',
                    'source': 'original_programmatic_practice',
                    'subject': subject, 'topic': topic,
                    'marks': marks, 'question': q, 'answer': a,
                    'scenario_family': family, 'split': split,
                    'language': 'English', 'human_reviewed': False,
                    'machine_checks': checks,
                    'review_status': 'Unreviewed experimental generated practice',
                })
        rng.shuffle(rows)
        rows_by_split[split] = rows
        with (output / f'{split}_records.jsonl').open('w', encoding='utf-8') as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
        with (output / f'{split}_sft.jsonl').open('w', encoding='utf-8') as f:
            for row in rows:
                f.write(json.dumps({
                    'prompt': [{'role': 'system', 'content': SYSTEM},
                               {'role': 'user', 'content': row['question']}],
                    'completion': [{'role': 'assistant', 'content': row['answer']}]
                }, ensure_ascii=False) + '\n')
    with (output/'review_sheet.csv').open('w', newline='', encoding='utf-8-sig') as f:
        fields = ('id', 'split', 'subject', 'topic', 'marks', 'question', 'answer',
                  'reviewer', 'answer_verified', 'release_approved', 'notes')
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows_by_split['train'] + rows_by_split['eval']:
            writer.writerow({key: row.get(key, '') for key in fields})
    manifest = {
        'version': 2, 'training_records': len(rows_by_split['train']),
        'evaluation_records': len(rows_by_split['eval']),
        'train_families': list(TRAIN_FAMILIES),
        'held_out_families': list(TEST_FAMILIES),
        'comparison_note': 'Fresh parameterized cases; concept families overlap. '
            'Phase 4 original cases are retired as a pristine benchmark after remediation.',
        'official_icai_material_used': False,
        'benchmark_test_data_used': False,
        'human_review_completed': False,
        'exam_quality_validated': False,
        'sha256_train': hashlib.sha256((output/'train_sft.jsonl').read_bytes()).hexdigest(),
    }
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path('data/training/phase3-v2'))
    parser.add_argument('--train-per-family', type=int, default=36)
    parser.add_argument('--eval-per-family', type=int, default=8)
    parser.add_argument('--seed', type=int, default=2028)
    args = parser.parse_args()
    print(json.dumps(create(args.out, args.train_per_family, args.eval_per_family, args.seed), indent=2))


if __name__ == '__main__':
    main()
