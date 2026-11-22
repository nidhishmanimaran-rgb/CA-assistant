from evaluation.build_cases import build
from evaluation.evaluate import check_case
import pytest

CASES=build()


@pytest.mark.parametrize("case",CASES,ids=lambda case:case["id"])
def test_original_evaluation_case(case):
    assert check_case(case)


def test_at_least_fifty_independently_verified_numerical_cases():
    numerical=[case for case in CASES if case["category"]=="numerical"]
    assert len(numerical)>=50
    assert all(case["verification"]=="independent_fraction_oracle" for case in numerical)
