"""Build original cases with a separate rational-arithmetic oracle. Never imports the calculator."""
from fractions import Fraction
import json
from pathlib import Path


def rounded(value):
    cents = (value.numerator * 200 + value.denominator) // (2 * value.denominator)
    return f"{cents // 100}.{cents % 100:02d}"


def numeric_cases():
    cases = []
    assets = [(850000,50000,8),(100000,10000,5),(240000,0,6),(135000,15000,4),
              (99999,999,3),(50000,5000,10),(720000,120000,12),(123456,3456,7),
              (1000,1000,5),(100,0,3)]
    revised = [(450000,30000,6),(850000,50000,8),(100000,10000,3),
               (240000,0,4),(99999,999,5),(12000,2000,2)]
    reducing = [(100000,10000,20),(120000,110000,25),(850000,50000,10),
                (1000,0,100),(12000,2000,15),(99999,999,12)]
    for method, rows, periods in [
        ("straight_line",assets,(12,6,3)), ("reducing_balance",reducing,(12,6)),
        ("revised_estimate",revised,(12,6,3)),
    ]:
        for opening, residual, factor in rows:
            for months in periods:
                base = Fraction(opening - residual)
                if method == "straight_line":
                    inputs = {"cost":str(opening),"residual":str(residual),"life":str(factor),"months":str(months)}
                    annual = base / factor
                    period = annual * Fraction(months,12)
                    question = f"Compute straight-line depreciation for {months} months: cost {opening}, residual value {residual}, useful life {factor} years."
                elif method == "reducing_balance":
                    inputs = {"opening":str(opening),"residual":str(residual),"rate":str(factor),"months":str(months)}
                    raw = Fraction(opening * factor,100)
                    annual, period = min(base,raw), min(base,raw * Fraction(months,12))
                    question = f"Compute reducing-balance depreciation for {months} months: opening carrying amount {opening}, residual value {residual}, annual rate {factor}%."
                else:
                    inputs = {"opening":str(opening),"residual":str(residual),"remaining_life":str(factor),"months":str(months)}
                    annual = base / factor
                    period = annual * Fraction(months,12)
                    question = f"Compute revised-estimate depreciation for {months} months: carrying amount {opening}, residual value {residual}, remaining useful life {factor} years."
                expected = {"annual":rounded(annual),"depreciation":rounded(period),
                            "closing":rounded(Fraction(opening) - Fraction(rounded(period)))}
                cases.append({"id":f"N{len(cases)+1:03}","category":"numerical","method":method,
                              "scenario_family":method + ("_full" if months==12 else "_partial"),
                              "question":question,"inputs":inputs,"expected":expected,
                              "verification":"independent_fraction_oracle","license":"CC0-1.0"})
    assert len(cases)==60
    assert cases[0]["expected"]["depreciation"]=="100000.00"
    assert cases[3]["expected"]["depreciation"]=="18000.00"
    return cases


def build():
    cases = numeric_cases()
    incomplete = [
        "Annual straight-line depreciation: cost 100000, useful life 5 years.",
        "Annual depreciation: cost 100000, residual 10000, useful life 5 years.",
        "Straight-line depreciation: cost 100000, residual 10000, useful life 5 years.",
        "Annual straight-line depreciation after impairment: cost 100000, residual 10000, useful life 5 years.",
        "Annual straight-line depreciation: cost 100000, residual 10000, useful life 0 years.",
        "Annual reducing-balance depreciation: opening carrying amount 100000, residual 10000.",
        "Annual straight-line depreciation: cost 100000, residual 200000, useful life 5 years.",
        "Annual straight-line depreciation: cost 100000, cost 200000, residual 10000, useful life 5 years.",
    ]
    for index, question in enumerate(incomplete,1):
        cases.append({"id":f"B{index:03}","category":"missing_information","question":question,
                      "expected":"clarification","verification":"explicit_input_contract","license":"CC0-1.0"})
    concepts = [
        ("What does residual value mean?","Residual value is the estimated amount recoverable at the end of an asset's useful life, after expected disposal costs.","residual value"),
        ("What is the depreciable amount?","Depreciable amount is the asset's cost less its residual value in this simplified example.","depreciable amount"),
        ("Explain the straight-line method.","The straight-line method allocates the depreciable amount equally across the useful life when estimates are unchanged.","straight-line"),
        ("Explain reducing-balance depreciation.","Reducing-balance depreciation applies a stated rate to the opening carrying amount, subject to the specified residual floor.","reducing-balance"),
        ("How do I prorate a charge for months in use?","With an explicitly agreed monthly convention, multiply the unrounded annual charge by months in use divided by twelve.","months in use"),
        ("What is the opening carrying amount?","The opening carrying amount is the amount recorded for the asset at the start of the period being calculated.","opening carrying amount"),
        ("How is a revised useful life used in this tool?","The revised useful life tool allocates the supplied current carrying amount less revised residual value over the remaining useful life.","revised useful life"),
        ("Does arithmetic verify the chosen accounting treatment?","Arithmetic verification checks numerical operations. It does not by itself establish that an accounting treatment is applicable to the facts.","accounting treatment"),
    ]
    for index,(question,evidence,keyword) in enumerate(concepts,1):
        cases.append({"id":f"C{index:03}","category":"concept_retrieval","question":question,
                      "evidence":evidence,"expected_keyword":keyword,
                      "verification":"original_reference_note; specialist_review_pending","license":"CC0-1.0"})
    for index, variant in enumerate(["valid","unknown_id","wrong_quote","missing_citation",
                                    "matching_attempt","wrong_attempt","wrong_subject","wrong_year"],1):
        cases.append({"id":f"G{index:03}","category":"source_grounding","variant":variant,
                      "question":"Use only applicable, verifiable source references.",
                      "verification":"independent_scope_or_citation_contract","license":"CC0-1.0"})
    return cases


if __name__ == "__main__":
    target = Path(__file__).with_name("test_questions.json")
    target.write_text(json.dumps(build(),ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Wrote {len(build())} original evaluation cases to {target}")
