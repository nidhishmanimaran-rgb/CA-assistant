"""Explicitly prewritten interface responses. No model, retrieval, or calculation API."""

from backend.session import StudyContext, validate_question
from config.catalog import ANSWER_FORMATS

SAMPLE_QUESTION = (
    "An asset costs ₹8,50,000, has a residual value of ₹50,000 and a useful "
    "life of 8 years. What is its annual straight-line depreciation? "
    "Assume a full year of use."
)

NOTICE = (
    "**Interface demo — no AI model is connected.**\n\n"
    "Your question is saved in this browser session. Phase 2 will connect the "
    "AI service. This response does not solve or verify your question."
)

SAMPLE_NOTICE = (
    "**Prepared example — not an AI-generated answer.**\n\n"
    "This fixed example demonstrates the answer layout. It does not recalculate "
    "other questions or changed assumptions."
)


def build_demo_response(question: str, context: StudyContext) -> str:
    """Validate a real prompt and acknowledge it without pretending to reason."""
    validate_question(question)
    if context.answer_format not in ANSWER_FORMATS:
        raise ValueError("Choose one of the supported answer formats.")

    if context.answer_format == "Simple explanation":
        layout = (
            "### Your explanation workspace\n\n"
            "A connected tutor will explain the concept in simple language, "
            "identify the facts it needs, and work through a relevant example."
        )
    elif context.answer_format == "Detailed solution":
        layout = (
            "### Given information\n\n"
            "Your question is recorded above; facts have not been extracted.\n\n"
            "### Principle and working notes\n\n"
            "These will be produced by the connected tutor, with a separate "
            "calculation tool added in Phase 4.\n\n"
            "### Final result\n\n"
            "No result has been calculated."
        )
    else:
        layout = (
            "### Relevant principle\n\n"
            "No accounting principle or statutory provision has been verified.\n\n"
            "### Application and working notes\n\n"
            "The connected tutor will structure its explanation around your facts.\n\n"
            "### Conclusion\n\n"
            "No conclusion has been generated. This is not an official ICAI solution."
        )
    return NOTICE + "\n\n" + layout


def prepared_example(answer_format: str) -> str:
    """Return a fixed, independently written presentation example for the supplied figures."""
    if answer_format not in ANSWER_FORMATS:
        raise ValueError("Choose one of the supported answer formats.")

    if answer_format == "Simple explanation":
        body = (
            "### Spread the depreciable amount over the useful life\n\n"
            "For this straight-line example, the amount to allocate is the asset's "
            "cost less its residual value: ₹8,50,000 − ₹50,000 = ₹8,00,000. "
            "Spread over 8 full years, this is **₹1,00,000 per year**."
        )
    else:
        principle_heading = (
            "Relevant principle" if answer_format == "Examination-style answer"
            else "Relevant concept"
        )
        body = (
            "### Given information\n\n"
            "| Particulars | Amount / period |\n"
            "| --- | ---: |\n"
            "| Cost | ₹8,50,000 |\n"
            "| Residual value | ₹50,000 |\n"
            "| Useful life | 8 years |\n"
            "| Time in use | One full year |\n\n"
            f"### {principle_heading}\n\n"
            "For the stated straight-line method, allocate the depreciable amount "
            "equally over the useful life.\n\n"
            "### Working notes\n\n"
            "1. Depreciable amount = ₹8,50,000 − ₹50,000 = ₹8,00,000.\n"
            "2. Annual depreciation = ₹8,00,000 ÷ 8 = ₹1,00,000.\n\n"
            r"$$\text{Annual depreciation} = \frac{850000 - 50000}{8} = 100000$$"
            "\n\n### Conclusion\n\n"
            "**Annual straight-line depreciation: ₹1,00,000.**"
        )
    return (
        SAMPLE_NOTICE + "\n\n" + body + "\n\n"
        "Assumptions: the stated straight-line method, a full year of use, and no "
        "changes to estimates, revaluation or impairment. This is an original "
        "illustrative example, not an official ICAI solution or a source-backed "
        "interpretation of an accounting standard."
    )
