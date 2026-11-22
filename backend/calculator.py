"""Small, explicit financial procedures. No eval, exec, generated code, or statutory rates."""
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import re
from backend.errors import AppError

MAX_AMOUNT = Decimal("1000000000000000")


def number(value, name):
    if not isinstance(value, (str, int, Decimal)) or isinstance(value, bool):
        raise AppError(f"Provide {name} as a decimal string.", "calculation")
    value = str(value).strip().replace("₹", "").replace("INR", "").strip()
    # Accept ordinary/Indian thousands groups, never malformed grouping or expressions.
    if "," in value and not re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d+)?", value):
        raise AppError(f"Invalid comma grouping in {name}.", "calculation")
    value = value.replace(",", "")
    if len(value) > 32 or not re.fullmatch(r"\d+(?:\.\d{1,8})?", value):
        raise AppError(f"{name} must be a non-negative decimal with at most 8 decimal places.", "calculation")
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise AppError(f"Invalid {name}.", "calculation") from None
    if not result.is_finite() or result > MAX_AMOUNT:
        raise AppError(f"{name} is outside the supported range.", "calculation")
    return result


def money(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class Calculation:
    method: str
    inputs: dict
    annual: str
    depreciation: str
    closing: str
    workings: tuple[str, ...]
    assumptions: tuple[str, ...]

    def as_dict(self):
        return asdict(self)


def calculate(method: str, **values) -> Calculation:
    required = {
        "straight_line": {"cost", "residual", "life", "months"},
        "reducing_balance": {"opening", "residual", "rate", "months"},
        "revised_estimate": {"opening", "residual", "remaining_life", "months"},
    }
    if method not in required:
        raise AppError("Select straight-line, reducing-balance, or revised-estimate depreciation.", "calculation")
    missing = required[method] - values.keys()
    if missing or any(values.get(k) in ("", None) for k in required[method]):
        raise AppError("Missing values: " + ", ".join(sorted(k for k in required[method] if values.get(k) in ("", None))), "missing_input")
    if values.keys() - required[method]:
        raise AppError("Unexpected calculation inputs.", "calculation")
    data = {key: number(values[key], key) for key in required[method]}
    if not 0 < data["months"] <= 12:
        raise AppError("Months in use must be greater than 0 and no more than 12.", "calculation")
    with localcontext() as ctx:
        ctx.prec = 48
        opening = data.get("cost", data.get("opening"))
        residual = data["residual"]
        if residual > opening:
            raise AppError("Residual value cannot exceed cost or opening carrying amount.", "calculation")
        base = opening - residual
        assumptions = ["Explicit method and months supplied.", "No impairment, revaluation or disposal adjustments."]
        if method == "reducing_balance":
            if not 0 < data["rate"] <= 100:
                raise AppError("The annual rate must be greater than 0 and no more than 100 percent.", "calculation")
            annual = min(base, opening * data["rate"] / 100)
            period = min(base, opening * data["rate"] / 100 * data["months"] / 12)
            steps = (
                f"Opening carrying amount = INR {money(opening)}.",
                f"Uncapped annual charge = {opening} × {data['rate']} / 100.",
                f"Period charge = minimum of {base} and {opening} × {data['rate']} / 100 × {data['months']} / 12 = INR {money(period)}.",
            )
            assumptions.append("Rate is supplied by the student; it is not a tax rate.")
        else:
            life = data["life"] if method == "straight_line" else data["remaining_life"]
            if not 0 < life <= 100 or data["months"] > life * 12:
                raise AppError("Useful life must be within 0–100 years and cover the requested period.", "calculation")
            annual = base / life
            period = annual * data["months"] / 12
            steps = (
                f"Depreciable amount = {opening} − {residual} = INR {money(base)}.",
                f"Annual charge = {base} / {life} = INR {money(annual)}.",
                f"Period charge = {base} / {life} × {data['months']} / 12 = INR {money(period)}.",
            )
            if method == "revised_estimate":
                assumptions.append("Prospective allocation from the supplied revision-date carrying amount; no prior-period adjustment.")
        rounded_period = Decimal(money(period))
        rounded_opening = Decimal(money(opening))
        closing = rounded_opening - rounded_period
        if closing < Decimal(money(residual)) or rounded_period < 0:
            raise AppError("The calculation failed its carrying-amount check.", "calculation")
        return Calculation(
            method, {key: str(value) for key, value in data.items()},
            money(annual), money(period), money(closing),
            steps + (f"Closing carrying amount = {money(rounded_opening)} − {money(rounded_period)} = INR {money(closing)}.",),
            tuple(assumptions + ["Amounts rounded half up to two decimals; annual charge is not rounded before proration."]),
        )


def format_calculation(result, answer_format="Detailed solution"):
    heading = "Application and working notes" if answer_format == "Examination-style answer" else "Working notes"
    lines = [f"### {heading}", "", *[f"{i}. {step}" for i, step in enumerate(result.workings, 1)]]
    lines += ["", f"**Depreciation for the stated period: INR {result.depreciation}.**",
              f"Closing carrying amount: INR {result.closing}.", "", "**Assumptions**",
              *["- " + item for item in result.assumptions],
              "", "Calculated with Python Decimal. This verifies the arithmetic for the supplied inputs, not the legal or accounting applicability of the method."]
    return "\n".join(lines)
