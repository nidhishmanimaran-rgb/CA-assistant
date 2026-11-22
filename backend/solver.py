"""Conservative offline recognition; ambiguous scenarios ask for facts instead of guessing."""
from dataclasses import dataclass
import re
from backend.calculator import calculate
from backend.errors import AppError

AMOUNT = r"(?:₹\s*|INR\s*|Rs\.?\s*)?(\d(?:[\d,]*\d)?(?:\.\d+)?)"


@dataclass(frozen=True)
class Plan:
    method: str | None
    values: dict
    missing: tuple[str, ...] = ()
    reason: str = ""


def plan_question(question: str) -> Plan | None:
    text = question.lower()
    if not re.search(r"depreciat|straight[- ]line|reducing[- ]balance|\bwdv\b|\bslm\b", text):
        return None
    if not re.search(r"\d", text):
        return None
    if re.search(r"revalu|impair|dispos|sell|sold|units? of production|double declining|tax|section|schedule ii", text):
        return Plan(None, {}, reason="This scenario needs accounting treatment outside the validated depreciation tools. Supply the applicable source and clarify the treatment before calculating.")
    method = ("revised_estimate" if re.search(r"revis|remaining (?:useful )?life", text)
              else "reducing_balance" if re.search(r"reducing[- ]balance|\bwdv\b|written[- ]down", text)
              else "straight_line" if re.search(r"straight[- ]line|\bslm\b", text) else None)
    if method is None:
        return Plan(None, {}, missing=("depreciation method",))
    patterns = {
        "cost": rf"(?:asset\s+)?cost(?:s)?(?:\s+of\s+(?:the\s+)?asset)?\s*(?:is|of|:|=)?\s*{AMOUNT}",
        "residual": rf"(?:residual|salvage)(?:\s+value)?\s*(?:is|of|:|=)?\s*{AMOUNT}",
        "opening": rf"(?:opening(?:\s+carrying)?\s+(?:amount|value|balance)|carrying\s+amount)\s*(?:is|of|:|=)?\s*{AMOUNT}",
        "life": r"useful\s+life\s*(?:is|of|:|=)?\s*(\d+(?:\.\d+)?)\s*years?",
        "remaining_life": r"remaining\s+(?:useful\s+)?life\s*(?:is|of|:|=)?\s*(\d+(?:\.\d+)?)\s*years?",
        "rate": r"(?:rate\s*(?:is|of|:|=)?\s*)?(\d+(?:\.\d+)?)\s*%",
        "months": r"(\d+(?:\.\d+)?)\s*months?",
    }
    keys = {"straight_line": ("cost", "residual", "life", "months"),
            "reducing_balance": ("opening", "residual", "rate", "months"),
            "revised_estimate": ("opening", "residual", "remaining_life", "months")}[method]
    values = {}
    for key in keys:
        matches = re.findall(patterns[key], question, re.IGNORECASE)
        if len(matches) == 1:
            values[key] = matches[0]
        elif len(matches) > 1:
            return Plan(method, {}, reason="Multiple values were supplied for the same input. Clarify which values apply.")
    if "months" not in values and re.search(r"\bannual\b|full[- ]year|full year|one year", text):
        values["months"] = "12"
    if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b", text):
        return Plan(method, {}, reason="Dates require a day-count or month convention. Enter the agreed months in the calculation workbench.")
    return Plan(method, values, tuple(key for key in keys if key not in values))


def solve_question(question):
    plan = plan_question(question)
    if plan is None:
        return None, None
    if plan.reason or plan.missing:
        return None, plan.reason or ("Please supply: " + ", ".join(plan.missing) + ".")
    try:
        return calculate(plan.method, **plan.values), None
    except AppError as error:
        return None, str(error)
