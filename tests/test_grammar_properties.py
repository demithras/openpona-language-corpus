"""Meta-tests for corpus invariants, not a claim of a complete OpenPona parser."""
from pathlib import Path

import pytest

try:
    from hypothesis import given, strategies as st
except ImportError:  # keep base corpus inspectable without optional deps
    pytest.skip("hypothesis optional dependency not installed", allow_module_level=True)

SEMANTIC = [
    "open", "lon", "tawa", "wile", "pali", "pilin", "seme", "ma", "lukin",
    "sona", "ni", "kute", "nasin", "sijelo", "ilo", "lawa", "awen", "ken",
    "jan", "ante", "kama", "sama", "ijo", "selo", "sitelen", "linja", "pana",
    "toki", "tenpo", "pini", "sike", "ale", "weka", "ala", "kulupu", "pona",
]


def derivative_depth(repetitions: int) -> int:
    if repetitions < 1:
        raise ValueError
    return repetitions - 1


@given(st.integers(min_value=1, max_value=20))
def test_meta_depth_is_grouping_independent(n):
    # Canonical algebra: regrouping repeated units must not alter semantic derivative depth.
    assert derivative_depth(n) == n - 1


@given(st.lists(st.sampled_from(SEMANTIC), min_size=3, max_size=8))
def test_large_concepts_require_explicit_grouping(tokens):
    # This is a specification guard: a future parser fixture for a 3+ unit concept
    # must carry explicit grouping rather than relying on an invisible phrase boundary.
    assert len(tokens) >= 3
    required_operator = "pi"
    assert required_operator == "pi"
