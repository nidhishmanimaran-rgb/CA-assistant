from decimal import Decimal
from fractions import Fraction
import pytest
from backend.calculator import calculate, number
from backend.errors import AppError
from backend.solver import solve_question


def test_user_changed_value_example():
    result = calculate("straight_line", cost="850000", residual="50000", life="8", months="12")
    assert result.depreciation == "100000.00"
    assert result.closing == "750000.00"


@pytest.mark.parametrize("months", ["1", "3", "6", "9", "12", "0.5"])
def test_partial_year_against_independent_fraction_arithmetic(months):
    result = calculate("straight_line", cost="100000", residual="10000", life="5", months=months)
    expected = Fraction(90000, 5) * Fraction(months) / 12
    assert Decimal(result.depreciation) == Decimal(expected.numerator) / Decimal(expected.denominator)
    assert Decimal(result.depreciation) + Decimal(result.closing) == Decimal("100000")


def test_reducing_balance_uses_opening_amount_and_residual_floor():
    result = calculate("reducing_balance", opening="120000", residual="110000", rate="25", months="6")
    assert result.depreciation == "10000.00"
    assert result.closing == "110000.00"


def test_revised_estimate_uses_remaining_life():
    result = calculate("revised_estimate", opening="450000", residual="30000", remaining_life="6", months="12")
    assert result.annual == "70000.00"


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-1", "1e9", "1+1", "__import__('os')", "8,500,00", True, 0.1])
def test_invalid_numbers_are_not_executed_or_coerced(value):
    with pytest.raises(AppError):
        number(value, "cost")


@pytest.mark.parametrize("changes", [
    {"life": "0"}, {"life": "101"}, {"months": "0"}, {"months": "13"},
    {"residual": "200000"}, {"life": None}, {"extra": "5"},
])
def test_invalid_or_missing_calculation_facts(changes):
    values = {"cost": "100000", "residual": "10000", "life": "5", "months": "12"}
    values.update(changes)
    with pytest.raises(AppError):
        calculate("straight_line", **values)


def test_natural_question_uses_its_own_values():
    result, clarification = solve_question(
        "Calculate annual straight-line depreciation: cost INR 8,50,000, residual value INR 50,000, useful life 8 years."
    )
    assert clarification is None
    assert result.depreciation == "100000.00"


@pytest.mark.parametrize("question", [
    "Annual straight-line depreciation: cost 100000, useful life 5 years.",
    "Annual depreciation: cost 100000, residual value 10000, useful life 5 years.",
    "Straight-line depreciation: cost 100000, residual value 10000, useful life 5 years.",
    "Annual straight-line depreciation after impairment: cost 100000, residual 10000, useful life 5 years.",
    "Annual straight-line depreciation: cost 100000, cost 200000, residual 10000, useful life 5 years.",
])
def test_missing_or_changed_assumptions_require_clarification(question):
    result, clarification = solve_question(question)
    assert result is None
    assert clarification
