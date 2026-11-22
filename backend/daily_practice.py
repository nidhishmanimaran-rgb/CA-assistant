"""Original, offline one-mark CA Intermediate practice questions.

These questions are authored for skill checks, are not ICAI past-paper content,
and have not undergone independent CA faculty review. Avoid treating them as
attempt-specific law or tax advice.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from random import Random


@dataclass(frozen=True)
class PracticeQuestion:
    id: str
    subject: str
    prompt: str
    options: tuple[str, str, str, str]
    answer_index: int
    explanation: str


# Format: subject | prompt | A | B | C | D | answer (0-3) | explanation
# The initial bank intentionally focuses on stable, introductory principles.
# Expansion should use reviewed/licensed questions with syllabus applicability.
_QUESTIONS = """
Advanced Accounting|Cost Rs 100000, residual value Rs 10000, useful life 5 years. Straight-line depreciation per year?|Rs 18000|Rs 20000|Rs 22000|Rs 9000|0|Depreciable amount is 90000; divide by 5 years.
Advanced Accounting|Asset cost Rs 90000, accumulated depreciation Rs 20000. Carrying amount?|Rs 90000|Rs 70000|Rs 110000|Rs 20000|1|Carrying amount equals cost minus accumulated depreciation.
Advanced Accounting|What is residual value?|The total original purchase cost|The asset's estimated end-of-life value|The annual depreciation rate|The accumulated depreciation|1|Residual value is the estimated amount recoverable on disposal at the end of useful life, after disposal costs.
Advanced Accounting|Which item is generally part of the cost of property, plant and equipment?|Unrelated advertising expense|Direct installation cost|General staff recreation expense|Abnormal wastage|1|Directly attributable costs to bring an asset to the required location and condition are included.
Advanced Accounting|Asset carrying value Rs 80000, depreciation for year Rs 15000; no other changes. Closing carrying value?|Rs 95000|Rs 80000|Rs 65000|Rs 15000|2|Subtract this year's depreciation from the opening carrying value.
Advanced Accounting|Depreciation of plant is usually recognized as?|A revenue receipt|An expense or part of another asset's cost|A cash inflow|A liability repayment|1|Depreciation allocates an asset's depreciable amount over its useful life.
Advanced Accounting|The straight-line method normally produces what annual depreciation pattern?|Equal amount each full year under unchanged estimates|A doubling amount each year|No expense until disposal|An amount equal to cash sales|0|Straight-line depreciation is a constant annual amount when cost, residual value and life estimates do not change.
Corporate and Other Laws|Which company document states its fundamental constitution and objects?|Memorandum of Association|Cash flow statement|Auditor's report|Purchase invoice|0|The Memorandum of Association defines the company's constitution and objects.
Corporate and Other Laws|The Articles of Association primarily concern?|Customer price lists|Internal governance rules|Income tax return computation|Stock valuation|1|Articles govern internal management and procedures subject to company law.
Corporate and Other Laws|Acceptance of an offer, when valid, turns the proposal into a?|Promise|Balance sheet|Share certificate|Debenture|0|Under basic contract terminology, an accepted proposal becomes a promise.
Corporate and Other Laws|Separate legal personality means a company is?|Identical to each director|A legal person distinct from its members|Always tax exempt|Not subject to any laws|1|Incorporation creates a company as a legal entity separate from shareholders.
Corporate and Other Laws|The board of directors is responsible primarily for?|Governing the company's affairs|Issuing the CA exam timetable|Collecting personal income tax|Preparing competitors' accounts|0|Directors exercise the management and oversight functions entrusted to the board.
Corporate and Other Laws|Which circumstance can affect free consent in contract formation?|Coercion|A written signature|Delivery of goods|A printed invoice|0|Consent is not free when caused by legally recognized vitiating factors, including coercion.
Corporate and Other Laws|Which document is generally used to set out the internal rules of a company?|Articles of Association|Bank passbook|Stock register|Receipt voucher|0|The Articles of Association set out the company's internal regulations.
Taxation|Income tax is normally classified as a?|Direct tax|Customs duty|Indirect sales tax|Excise duty|0|Income tax is imposed directly on the income of the person liable.
Taxation|GST in India is generally classified as a?|Direct tax on personal income|Indirect tax|Wealth tax|Property tax|1|GST is a tax on supplies, collected through the supply chain.
Taxation|An assessment year generally follows which period?|The previous financial year|The next five financial years|The calendar month only|The incorporation date only|0|Income of a previous year is generally assessed in its corresponding following assessment year.
Taxation|Input tax credit generally relates to?|Eligible GST paid on inward supplies, subject to conditions|Income tax paid by customers|Tax on personal salaries|Stamp duty on incorporation|0|ITC permits eligible input GST to be credited against output GST, subject to statutory restrictions.
Taxation|Which GST component is generally used for an inter-State supply?|IGST|Only SGST|Only CGST|No GST in all cases|0|IGST generally applies to inter-State taxable supplies, subject to relevant rules.
Taxation|A typical intra-State taxable supply may attract which pair?|CGST and SGST/UTGST|Only income tax|Only customs duty|Only stamp duty|0|Intra-State supplies generally have a Central and State/UT GST component, subject to the governing provisions.
Taxation|What does PAN stand for in Indian taxation?|Permanent Account Number|Public Audit Notice|Personal Asset Note|Payment Authority Number|0|PAN is the Permanent Account Number used for tax identification.
Cost and Management Accounting|Direct materials Rs 20000, direct labour Rs 15000, direct expenses Rs 5000. Prime cost?|Rs 35000|Rs 40000|Rs 20000|Rs 55000|1|Prime cost is total direct materials, labour and expenses.
Cost and Management Accounting|Selling price Rs 50 and variable cost Rs 30 per unit. Contribution per unit?|Rs 80|Rs 30|Rs 20|Rs 50|2|Contribution equals selling price less variable cost.
Cost and Management Accounting|Fixed cost Rs 100000, contribution Rs 20 per unit. Break-even units?|2000|4000|5000|10000|2|Break-even quantity is fixed costs divided by unit contribution.
Cost and Management Accounting|Conversion cost generally comprises?|Direct materials only|Direct labour and manufacturing overhead|Selling expenses only|Interest expense only|1|Conversion cost is incurred to convert raw material into finished output.
Cost and Management Accounting|Within a relevant range, total fixed costs are generally?|Constant|Proportional to units|Always zero|Equal to selling price|0|Fixed costs in total ordinarily remain constant within the relevant range.
Cost and Management Accounting|Actual sales Rs 120000; break-even sales Rs 90000. Margin of safety?|Rs 30000|Rs 210000|Rs 90000|Rs 120000|0|Margin of safety equals actual sales less break-even sales.
Cost and Management Accounting|Within the relevant range, total variable costs usually?|Remain constant regardless of output|Vary broadly with activity|Always decrease to zero|Equal fixed costs|1|Variable costs in total vary with activity when unit cost stays unchanged.
Auditing and Ethics|In audit evidence, sufficiency primarily refers to?|Quantity|Colour of documents|The client's size|Audit fee|0|Sufficiency concerns quantity; appropriateness concerns relevance and reliability.
Auditing and Ethics|Appropriateness of audit evidence primarily refers to?|Quantity alone|Quality including relevance and reliability|Length of the report|Age of auditor|1|Appropriateness measures the quality of evidence.
Auditing and Ethics|Professional skepticism requires?|A questioning mind and critical evaluation|Accepting all management claims|Avoiding audit evidence|Guaranteeing no fraud|0|Skepticism includes being alert to misstatement and critically assessing evidence.
Auditing and Ethics|Primary responsibility for preparing financial statements rests with?|Management|Only external auditors|All vendors|Stock exchange alone|0|Management prepares the financial statements; auditors express an opinion.
Auditing and Ethics|A financial statement audit ordinarily provides?|Absolute assurance|Reasonable assurance|No assurance|A guarantee of future profit|1|Audits aim at reasonable, not absolute, assurance.
Auditing and Ethics|An external confirmation is evidence obtained from?|An independent third party|Only the audit partner|The audit working paper template|A random newspaper|0|Confirmation is a direct response from an external party to the auditor.
Auditing and Ethics|Material misstatement in financial statements may result from?|Fraud or error|Only computational error|Only cash theft|Only depreciation|0|Misstatements may arise from either fraud or error.
Financial Management|Current assets Rs 80000 and current liabilities Rs 50000. Net working capital?|Rs 130000|Rs 30000|Rs 50000|Rs 80000|1|Net working capital equals current assets minus current liabilities.
Financial Management|Current assets Rs 120000 and current liabilities Rs 60000. Current ratio?|1:2|1:1|2:1|3:1|2|Current ratio is 120000 divided by 60000, or 2:1.
Financial Management|Principal Rs 10000, simple interest 10% per year for 1 year. Interest?|Rs 1000|Rs 10000|Rs 100|Rs 11000|0|Simple interest is principal times rate times time.
Financial Management|All else equal, a project with positive NPV generally?|Adds value|Destroys value necessarily|Has zero future cash flow|Is always illegal|0|Positive NPV indicates discounted benefits exceed discounted costs.
Financial Management|Investment Rs 60000, equal annual net cash inflow Rs 20000. Simple payback period?|2 years|3 years|4 years|6 years|1|Undiscounted payback is 60000 divided by 20000.
Financial Management|For a positive future cash inflow, a higher discount rate makes its present value?|Higher|Unchanged|Lower|Always negative|2|Higher discount rates lower the present value of a future positive receipt.
Financial Management|Which term means the cost of financing investment with debt and equity?|Cost of capital|Inventory cost only|Prime cost|Selling price|0|Cost of capital is the required return for capital providers.
Strategic Management|Which SWOT component is internal to an organization?|Strengths|Threats|Market regulation|Exchange rates|0|Strengths and weaknesses are internal; opportunities and threats are external.
Strategic Management|Which SWOT component usually represents an external risk?|Weakness|Threat|Strength|Core competency|1|Threats are external conditions that may harm strategy.
Strategic Management|In PESTLE, the letter E commonly stands for?|Economic|Equity shares|Efficiency ratio|Expenditure voucher|0|PESTLE examines Political, Economic, Social, Technological, Legal and Environmental factors.
Strategic Management|A BCG matrix business with high relative market share and high market growth is a?|Dog|Cash cow|Star|Question mark|2|Stars are high-share businesses in high-growth markets.
Strategic Management|Cost leadership aims to achieve advantage primarily through?|Lower relative costs|Only premium prices|Avoiding customers|Eliminating all competition|0|Cost leadership emphasizes an efficient cost position.
Strategic Management|Which force is included in Porter's Five Forces?|Threat of new entrants|Current ratio|Gross profit percentage|Depreciation policy|0|The threat of new entrants is one of the five industry forces.
Strategic Management|In the Ansoff matrix, diversification involves?|New products in new markets|Existing products in existing markets only|Existing products in current markets only|Selling only to suppliers|0|Diversification combines new products with new markets.
""".strip()


def load_questions() -> tuple[PracticeQuestion, ...]:
    questions: list[PracticeQuestion] = []
    seen: set[str] = set()
    for line in _QUESTIONS.splitlines():
        parts = [item.strip() for item in line.split("|")]
        if len(parts) != 8:
            raise ValueError("Malformed original practice bank entry")
        subject, prompt, a, b, c, d, raw_answer, explanation = parts
        answer = int(raw_answer)
        if answer not in range(4) or not all(parts):
            raise ValueError("Invalid one-mark question")
        qid = sha256((subject + "\0" + prompt).encode("utf-8")).hexdigest()[:16]
        if qid in seen:
            raise ValueError("Duplicate practice question")
        seen.add(qid)
        questions.append(PracticeQuestion(qid, subject, prompt, (a, b, c, d), answer, explanation))
    return tuple(questions)


QUESTION_BANK = load_questions()
DAILY_TARGET = 20


def daily_questions(day: date, count: int = DAILY_TARGET) -> tuple[PracticeQuestion, ...]:
    """Deterministic, balanced 20-question set per India-local calendar date."""
    if not isinstance(day, date) or count < 1 or count > len(QUESTION_BANK):
        raise ValueError("Invalid day or question count")
    rng = Random(int.from_bytes(sha256(day.isoformat().encode("ascii")).digest()[:8], "big"))
    grouped: dict[str, list[PracticeQuestion]] = {}
    for question in QUESTION_BANK:
        grouped.setdefault(question.subject, []).append(question)
    chosen: list[PracticeQuestion] = []
    for subject in sorted(grouped):
        pool = grouped[subject][:]
        rng.shuffle(pool)
        chosen.extend(pool[: min(2, len(pool), max(0, count - len(chosen)))])
    extras = [q for q in QUESTION_BANK if q not in chosen]
    rng.shuffle(extras)
    chosen.extend(extras[:count - len(chosen)])
    rng.shuffle(chosen)
    return tuple(chosen)


def count_correct(questions: tuple[PracticeQuestion, ...], answers: dict[str, int]) -> int:
    return sum(answers.get(q.id) == q.answer_index for q in questions if q.id in answers)
