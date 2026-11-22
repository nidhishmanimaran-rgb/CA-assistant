"""Original, English CA-style question generator for experimental fine-tuning.

This is NOT ICAI material, an authoritative syllabus, or approved exam answers.
The numerical arithmetic is machine-checked; human technical review remains required.
Independent scenario families are split by design to avoid template leakage.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import random
import csv

D = Decimal
CENT = D('0.01')


def money(n: int | Decimal) -> str:
    return f"₹{D(n).quantize(CENT, rounding=ROUND_HALF_UP):,.2f}"


def pct(n: Decimal) -> str:
    return f"{n.quantize(CENT, rounding=ROUND_HALF_UP):,.2f}%"


def example(family: str, index: int, rng: random.Random) -> tuple[str, str, str, str]:
    marks = 10 if index % 2 == 0 else 16
    if family == 'ppe_schedule':
        subject, topic = 'Advanced Accounting', 'Property, plant and equipment — depreciation'
        life = rng.randint(4, 10)
        dep = rng.randint(7, 34) * 5000
        residual = rng.randint(2, 12) * 5000
        cost = dep * life + residual
        years = 2 if marks == 10 else 3
        balance = cost
        schedule = []
        for yr in range(1, years + 1):
            close = balance - dep
            schedule.append(f"| Year {yr} | {money(balance)} | {money(dep)} | {money(close)} |")
            balance = close
        assert cost - dep * years == balance and residual < balance
        question = (
            f"(Original {marks}-mark practice question) On 1 April, an entity buys machinery "
            f"for {money(cost)}. Estimated residual value is {money(residual)} and useful "
            f"life is {life} years. Using the straight-line method, prepare a depreciation "
            f"schedule for the first {years} full financial years ending 31 March; "
            f"calculate the carrying amount after year {years}; and show the annual "
            f"depreciation journal entries. Assume no revaluation or impairment."
        )
        answer = (
            f"**Working note 1 — Depreciable amount:** {money(cost)} − {money(residual)} "
            f"= {money(cost-residual)}.\n\n"
            f"**Working note 2 — Annual straight-line depreciation:** "
            f"{money(cost-residual)} ÷ {life} years = **{money(dep)}**.\n\n"
            f"**Depreciation schedule:**\n| Year | Opening carrying amount | Depreciation | Closing carrying amount |\n"
            f"|---|---:|---:|---:|\n" + "\n".join(schedule) + "\n\n"
            f"**Journal entry at each year-end:** Dr Depreciation expense {money(dep)}; "
            f"Cr Accumulated depreciation — machinery {money(dep)}. "
            f"Post depreciation expense to profit or loss.\n\n"
            f"**Carrying amount after {years} years:** {money(cost)} − "
            f"({years} × {money(dep)}) = **{money(balance)}**."
        )
    elif family == 'cvp':
        subject, topic = 'Cost and Management Accounting', 'CVP and break-even analysis'
        contribution = rng.randint(4, 16) * 25
        variable = rng.randint(4, 16) * 25
        price = contribution + variable
        be_units = rng.randint(6, 20) * 100
        fixed = contribution * be_units
        actual_units = be_units + rng.randint(3, 12) * 100
        profit = actual_units * contribution - fixed
        mos = actual_units - be_units
        pv = D(contribution) / D(price) * 100
        target_units = be_units + rng.randint(4, 13) * 100
        target_profit = (target_units - be_units) * contribution
        assert fixed == be_units * (price-variable)
        assert profit == mos * contribution
        question = (
            f"(Original {marks}-mark practice question) A company sells one product at "
            f"{money(price)} per unit. Variable cost is {money(variable)} per unit, "
            f"fixed operating costs total {money(fixed)}, and expected sales are "
            f"{actual_units:,} units. Compute (a) contribution per unit, (b) P/V ratio, "
            f"(c) break-even point in units, (d) expected profit and (e) margin of "
            f"safety in units. "
            + (f"Also compute sales units needed for a target profit of {money(target_profit)}." if marks == 16 else "")
        )
        answer = (
            f"**Working note 1 — Contribution:** Selling price − variable cost = "
            f"{money(price)} − {money(variable)} = **{money(contribution)} per unit**.\n\n"
            f"**P/V ratio:** ({money(contribution)} ÷ {money(price)}) × 100 = **{pct(pv)}**.\n\n"
            f"**Break-even units:** Fixed cost ÷ contribution per unit = "
            f"{money(fixed)} ÷ {money(contribution)} = **{be_units:,} units**.\n\n"
            f"**Expected profit:** ({actual_units:,} × {money(contribution)}) − "
            f"{money(fixed)} = **{money(profit)}**.\n\n"
            f"**Margin of safety:** {actual_units:,} − {be_units:,} = **{mos:,} units**."
        )
        if marks == 16:
            answer += (
                f"\n\n**Target profit sales:** (fixed cost + target profit) ÷ contribution "
                f"per unit = ({money(fixed)} + {money(target_profit)}) ÷ "
                f"{money(contribution)} = **{target_units:,} units**."
            )
    elif family == 'npv':
        subject, topic = 'Financial Management', 'Capital budgeting — NPV and PI'
        years = 4 if marks == 10 else 5
        investment = rng.randint(3, 11) * 100000
        annual_cf = rng.randint(1, 6) * 100000
        salvage = rng.randint(1, 5) * 10000
        rate = D(rng.choice([8, 10, 12, 15])) / D(100)
        pvs = []
        schedule = []
        for yr in range(1, years + 1):
            cash = annual_cf + (salvage if yr == years else 0)
            pv = (D(cash) / ((D(1) + rate) ** yr)).quantize(CENT, rounding=ROUND_HALF_UP)
            pvs.append(pv)
            schedule.append(f"| {yr} | {money(cash)} | {(D(1)/((D(1)+rate)**yr)):.5f} | {money(pv)} |")
        total_pv = sum(pvs, D(0))
        npv = total_pv - D(investment)
        decision = 'Accept' if npv > 0 else 'Reject' if npv < 0 else 'Indifferent'
        pi = total_pv / D(investment)
        assert total_pv - D(investment) == npv
        question = (
            f"(Original {marks}-mark practice question) A project needs an initial outlay "
            f"of {money(investment)} immediately. It generates year-end cash inflows of "
            f"{money(annual_cf)} annually for {years} years, with an additional "
            f"{money(salvage)} salvage receipt at the end of year {years}. The cost of "
            f"capital is {pct(rate*100)}. Assume cash flows are after tax. Compute "
            f"the NPV using discounted cash flows and advise whether to accept the project. "
            + ('Also compute the profitability index (PI).' if marks == 16 else '')
        )
        answer = (
            f"**Formula:** PV of cash flow at year t = CFₜ ÷ (1 + r)ᵗ; "
            f"r = {pct(rate*100)}. Add terminal salvage to the year-{years} inflow.\n\n"
            f"| Year | Total inflow | PV factor (approx.) | Discounted inflow |\n"
            f"|---|---:|---:|---:|\n" + '\n'.join(schedule) + '\n\n'
            f"**Total PV of inflows:** {money(total_pv)}.\n\n"
            f"**NPV:** {money(total_pv)} − {money(investment)} = "
            f"**{money(npv)}**.\n\n"
            f"**Decision:** {decision} the project based on the NPV rule "
            f"(positive NPV creates value, negative NPV does not)."
        )
        if marks == 16:
            answer += f"\n\n**Profitability index:** {money(total_pv)} ÷ {money(investment)} = **{pi:.4f}**."
    elif family == 'slm_wdv_theory':
        subject, topic = 'Advanced Accounting', 'SLM versus WDV — theory'
        cost = rng.randint(3, 14) * 100000
        useful = rng.choice([4,5,8,10])
        rate = D(rng.choice([15,20,25,30])) / D(100)
        slm = D(cost) / D(useful)
        wdv1 = D(cost) * rate
        wdv2 = (D(cost)-wdv1)*rate
        assert wdv1 > wdv2 > 0
        question = (
            f"(Original {marks}-mark theory practice question) Explain and compare the "
            f"straight-line method (SLM) and written-down-value method (WDV) of depreciation "
            f"with reference to the charge, computation base, pattern and carrying amount. "
            f"Illustrate the first two annual depreciation charges on an asset costing "
            f"{money(cost)}, with zero assumed residual value and useful life of "
            f"{useful} years for SLM, compared with {pct(rate*100)} annual WDV. "
            + ('Also discuss how a method should reflect the consumption of economic benefits.' if marks == 16 else '')
        )
        answer = (
            f"**SLM:** Depreciable amount (cost less residual value) is allocated "
            f"equally over the estimated useful life, assuming no revision or change in use. "
            f"A constant annual expense is recognized, so carrying amount generally "
            f"declines by equal amounts.\n\n"
            f"**WDV:** A fixed percentage is applied to opening carrying amount each "
            f"period; depreciation charges therefore generally decline as carrying "
            f"amount declines. A fixed percentage does not necessarily bring carrying "
            f"amount to zero at the end of a selected number of years.\n\n"
            f"**Illustration:**\n"
            f"- SLM annual charge = ({money(cost)} − {money(0)}) ÷ {useful} "
            f"= **{money(slm)}** in each of years 1 and 2.\n"
            f"- WDV year 1 = {money(cost)} × {pct(rate*100)} = **{money(wdv1)}**.\n"
            f"- WDV year 2 = ({money(cost)} − {money(wdv1)}) × "
            f"{pct(rate*100)} = **{money(wdv2)}**.\n\n"
            f"**Comparison:** SLM gives a constant charge; WDV normally gives higher "
            f"early-year charges and falling later charges. Choosing a depreciation "
            f"method should reflect the expected pattern of consumption of benefits. "
            f"Tax treatment depends on applicable tax law; neither method itself "
            f"guarantees a lower tax liability."
        )
    elif family == 'ppe_disposal':
        subject, topic = 'Advanced Accounting', 'Disposal of machinery'
        life = rng.randint(5,10)
        dep = rng.randint(6,30)*5000
        residual = rng.randint(1,10)*5000
        cost = dep*life+residual
        full_years = rng.randint(2,min(life-1,4))
        accumulated = dep*full_years
        nbv = cost-accumulated
        delta = rng.choice([-1,1])*rng.randint(1,10)*5000
        proceeds = nbv + delta
        assert proceeds > 0
        loss = max(nbv-proceeds,0)
        gain = max(proceeds-nbv,0)
        assert proceeds+accumulated+loss == cost+gain
        question = (
            f"(Original {marks}-mark held-out assessment) Machinery originally cost "
            f"{money(cost)}, with residual value {money(residual)} and estimated useful "
            f"life of {life} years. It was used for {full_years} complete years and "
            f"depreciated by SLM. It is then sold for {money(proceeds)} immediately after "
            f"the last full year's depreciation is recorded. Determine annual depreciation, "
            f"accumulated depreciation, carrying amount, and gain or loss on disposal. "
            f"Prepare the disposal journal entry, assuming no impairment."
        )
        result = f'gain of {money(gain)}' if gain else f'loss of {money(loss)}'
        answer = (
            f"**Annual depreciation:** ({money(cost)} − {money(residual)}) ÷ {life} "
            f"= **{money(dep)}**.\n\n"
            f"**Accumulated depreciation:** {full_years} × {money(dep)} "
            f"= **{money(accumulated)}**.\n\n"
            f"**Carrying amount before disposal:** {money(cost)} − {money(accumulated)} "
            f"= **{money(nbv)}**.\n\n"
            f"**Disposal result:** proceeds {money(proceeds)} less carrying amount "
            f"{money(nbv)} = **{result}**.\n\n"
            f"**Balanced disposal journal entry:**\n"
            f"- Dr Bank {money(proceeds)}\n"
            f"- Dr Accumulated depreciation {money(accumulated)}\n"
            + (f"- Dr Loss on disposal {money(loss)}\n" if loss else '')
            + f"- Cr Machinery (cost) {money(cost)}\n"
            + (f"- Cr Gain on disposal {money(gain)}\n" if gain else '')
            + f"Total debits = total credits = {money(cost+gain)}."
        )
    elif family == 'material_variance':
        subject, topic = 'Cost and Management Accounting', 'Material cost, price and usage variances'
        sq_per_unit = rng.randint(2,8)
        units = rng.randint(10,35)*10
        sq = units*sq_per_unit
        aq = sq + rng.choice([-1,1])*rng.randint(1,25)
        sp = rng.randint(10,40)*5
        ap = sp + rng.choice([-1,1])*rng.randint(1,6)
        std_cost, actual_cost = sq*sp,aq*ap
        price_var = aq*(sp-ap)
        usage_var = sp*(sq-aq)
        total_var = std_cost - actual_cost
        assert price_var+usage_var==total_var
        def fv(n): return f'{money(abs(n))} '+('Favourable' if n>=0 else 'Adverse')
        question = (
            f"(Original {marks}-mark held-out assessment) Standard material usage is "
            f"{sq_per_unit} kg per finished unit at {money(sp)} per kg. Actual production "
            f"was {units:,} units, using {aq:,} kg purchased/used at {money(ap)} per kg. "
            f"Calculate standard quantity for actual output, material price variance, "
            f"material usage variance and material cost variance, and reconcile the figures. "
            f"Use favourable/adverse labels."
        )
        answer = (
            f"**Standard quantity for actual output:** {units:,} × {sq_per_unit} "
            f"= **{sq:,} kg**.\n\n"
            f"**Material price variance:** AQ × (SP − AP) = {aq:,} × "
            f"({money(sp)} − {money(ap)}) = **{fv(price_var)}**.\n\n"
            f"**Material usage variance:** SP × (SQ − AQ) = {money(sp)} × "
            f"({sq:,} − {aq:,}) = **{fv(usage_var)}**.\n\n"
            f"**Material cost variance:** (SQ × SP) − (AQ × AP) = "
            f"{money(std_cost)} − {money(actual_cost)} = **{fv(total_var)}**.\n\n"
            f"**Reconciliation:** price variance ({money(price_var)}) + usage "
            f"variance ({money(usage_var)}) = total variance ({money(total_var)}), "
            f"using positive for favourable and negative for adverse."
        )
    elif family == 'wacc':
        subject, topic = 'Financial Management', 'Weighted average cost of capital'
        equity = rng.randint(4,16)*100000
        debt = rng.randint(2,12)*100000
        ke = D(rng.choice([12,14,16,18]))
        kd = D(rng.choice([8,9,10,11]))
        tax = D(rng.choice([20,25,30]))
        total = equity+debt
        eq_w = D(equity)/D(total)
        debt_w = D(debt)/D(total)
        debt_after = kd*(D(100)-tax)/D(100)
        wacc = eq_w*ke+debt_w*debt_after
        assert eq_w+debt_w==1
        question = (
            f"(Original {marks}-mark held-out assessment) A company has market value of "
            f"equity {money(equity)} and market value of interest-bearing debt "
            f"{money(debt)}. Cost of equity is {pct(ke)}, pre-tax cost of debt "
            f"{pct(kd)}, and assumed tax rate {pct(tax)}. Compute its after-tax WACC. "
            f"Explain the treatment of the debt tax shield and use market-value weights."
        )
        answer = (
            f"**Total market value:** {money(equity)} + {money(debt)} "
            f"= {money(total)}.\n\n"
            f"**Capital weights:** Equity = {money(equity)} ÷ {money(total)} "
            f"= {pct(eq_w*100)}; Debt = {money(debt)} ÷ {money(total)} "
            f"= {pct(debt_w*100)}.\n\n"
            f"**After-tax cost of debt:** {pct(kd)} × (1 − {pct(tax)}) "
            f"= **{pct(debt_after)}**.\n\n"
            f"**WACC:** (Equity weight × Ke) + (Debt weight × Kd × (1−T)) "
            f"= ({eq_w:.5f} × {pct(ke)}) + ({debt_w:.5f} × {pct(debt_after)}) "
            f"= **{pct(wacc)}**.\n\n"
            f"**Note:** The debt tax shield applies if the stated interest tax deduction "
            f"is available; cost of equity is not reduced by the corporate tax rate."
        )
    elif family == 'audit_evidence_theory':
        subject, topic = 'Auditing and Ethics', 'Sufficiency and appropriateness of audit evidence'
        company = rng.choice(['a manufacturing entity', 'a retailer', 'a service company'])
        question = (
            f"(Original {marks}-mark held-out theory assessment) An auditor of "
            f"{company} is planning work on trade receivables. Distinguish "
            f"sufficiency from appropriateness of audit evidence; discuss reliability, "
            f"give examples of audit procedures, and explain why more weak evidence "
            f"does not necessarily compensate for poor-quality evidence."
        )
        answer = (
            f"**Sufficiency** refers to the *quantity* of audit evidence obtained. "
            f"The amount needed depends partly on assessed risks and the quality of evidence.\n\n"
            f"**Appropriateness** refers to *quality*: relevance to the assertion "
            f"and reliability of the information. Quantity alone cannot repair "
            f"fundamentally unreliable evidence.\n\n"
            f"**Trade receivable examples:** external confirmations (existence), "
            f"inspection of subsequent receipts (evidence concerning existence and "
            f"recoverability, interpreted carefully), inspection of invoices and "
            f"dispatch records (occurrence/cut-off), and recalculation of the ageing "
            f"schedule (accuracy).\n\n"
            f"**Judgment:** Evidence from independent external sources may generally "
            f"be more reliable, although circumstances and controls matter; the auditor "
            f"should respond to assessed misstatement risks and resolve conflicting evidence."
        )
    else:
        raise ValueError(f'Unknown family: {family}')
    return subject, topic, question, answer


TRAIN_FAMILIES = ('ppe_schedule', 'cvp', 'npv', 'slm_wdv_theory')
TEST_FAMILIES = ('ppe_disposal', 'material_variance', 'wacc', 'audit_evidence_theory')
SYSTEM = (
    "You are an independent English-language CA-study practice tutor. "
    "Answer carefully with formulas, working notes, clear tables or journal entries "
    "where relevant. Do not invent legal applicability, and state assumptions. "
    "The questions are original practice problems, not official ICAI answers."
)


def generate(output: Path, train_per_family: int = 36, eval_per_family: int = 12, seed: int = 2027) -> dict:
    if not 2 <= train_per_family <= 500 or not 2 <= eval_per_family <= 100:
        raise ValueError('Counts must be 2–500 train per family and 2–100 eval per family')
    rng = random.Random(seed)
    output.mkdir(parents=True, exist_ok=True)
    rows = {'train': [], 'eval': []}
    for split, families, count in (
        ('train', TRAIN_FAMILIES, train_per_family),
        ('eval', TEST_FAMILIES, eval_per_family),
    ):
        for family in families:
            for i in range(count):
                subject, topic, question, answer = example(family, i, rng)
                row = {
                    'id': f'original-phase3-{family}-{i:04d}',
                    'source': 'original_programmatic_practice',
                    'subject': subject, 'topic': topic,
                    'marks': 10 if i % 2 == 0 else 16,
                    'question_type': 'theory' if 'theory' in family else 'practical',
                    'scenario_family': family,
                    'question': question, 'answer': answer,
                    'language': 'English',
                    'rights_basis': 'original_generated_not_source_copied',
                    'machine_calculated': 'theory' not in family,
                    'human_reviewed': False,
                    'review_status': 'Experimental only; subject-matter human review required',
                    'split': split,
                }
                rows[split].append(row)
    rng.shuffle(rows['train'])
    rng.shuffle(rows['eval'])
    assert not (set(TRAIN_FAMILIES) & set(TEST_FAMILIES))
    for split in ('train', 'eval'):
        with (output / f'{split}_records.jsonl').open('w', encoding='utf-8') as file:
            for row in rows[split]:
                file.write(json.dumps(row, ensure_ascii=False) + '\n')
        with (output / f'{split}_sft.jsonl').open('w', encoding='utf-8') as file:
            for row in rows[split]:
                sample = {
                    'prompt': [
                        {'role': 'system', 'content': SYSTEM},
                        {'role': 'user', 'content': row['question']}
                    ],
                    'completion': [{'role': 'assistant', 'content': row['answer']}],
                }
                file.write(json.dumps(sample, ensure_ascii=False) + '\n')
    with (output / 'review_sheet.csv').open('w', newline='', encoding='utf-8-sig') as file:
        fields = ['id', 'split', 'subject', 'topic', 'marks', 'scenario_family', 'question',
                  'answer', 'reviewer', 'answer_verified', 'approved_for_release']
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows['train']+rows['eval']:
            writer.writerow({field: row.get(field, '') for field in fields})
    manifest = {
        'version': 1,
        'training_records': len(rows['train']),
        'evaluation_records': len(rows['eval']),
        'train_families': list(TRAIN_FAMILIES),
        'held_out_families': list(TEST_FAMILIES),
        'train_subjects': dict(Counter(r['subject'] for r in rows['train'])),
        'eval_subjects': dict(Counter(r['subject'] for r in rows['eval'])),
        'human_review_completed': False,
        'exam_quality_validated': False,
        'official_icai_material_used': False,
        'benchmark_test_data_used': False,
        'experimental_training_allowed': True,
        'purpose': 'Original synthetic concept and exam-format pilot; not an official marks scheme',
        'sha256_train': hashlib.sha256((output/'train_sft.jsonl').read_bytes()).hexdigest(),
    }
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=Path('data/training/phase3'))
    p.add_argument('--train-per-family', type=int, default=36)
    p.add_argument('--eval-per-family', type=int, default=12)
    p.add_argument('--seed', type=int, default=2027)
    args = p.parse_args()
    print(json.dumps(generate(args.out, args.train_per_family, args.eval_per_family, args.seed), indent=2))


if __name__ == '__main__':
    main()

