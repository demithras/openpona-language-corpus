"""Property tests of the reference parser (hypothesis)."""
import pytest

pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st  # noqa: E402

from openpona import SEMANTIC, STRUCTURAL, TOKENS, parse  # noqa: E402

sem = st.sampled_from(SEMANTIC)


def _no_adjacent_equal(seq):
    return all(a != b for a, b in zip(seq, seq[1:]))


def test_token_lists_come_from_csv():
    assert len(TOKENS) == 42
    assert len(SEMANTIC) == 36
    assert STRUCTURAL == ["li", "la", "e", "tan", "pi", "anu"]


@given(sem)
def test_single_semantic_token_is_resolved(tok):
    res = parse(tok)
    assert res.status == "RESOLVED"
    assert res.skeletons == ["{" + tok + "}"]


@given(sem, sem)
def test_two_distinct_semantic_tokens_form_a_phrase(a, b):
    if a == b:
        return
    res = parse(f"{a} {b}")
    assert res.status == "RESOLVED"
    assert res.skeletons == ["{" + f"{a} {b}" + "}"]


@given(st.lists(sem, min_size=3, max_size=3).filter(_no_adjacent_equal))
def test_three_semantic_tokens_without_pi_are_invalid(toks):
    res = parse(" ".join(toks))
    assert res.status == "INVALID"
    assert res.skeletons == []


@given(sem, st.integers(min_value=2, max_value=8))
def test_repetition_is_a_meta_derivative(p, n):
    res = parse(" ".join([p] * n))
    assert res.status == "RESOLVED"
    assert res.skeletons == ["{" + f"D{n - 1}({p})" + "}"]


phrase = st.lists(sem, min_size=1, max_size=2).filter(_no_adjacent_equal)


@settings(deadline=None)
@given(phrase, st.one_of(st.none(), phrase))
def test_strict_mode_is_never_ambiguous_with_at_most_one_li(subj, pred):
    toks = list(subj) + (["li"] + list(pred) if pred is not None else [])
    res = parse(" ".join(toks), mode="strict")
    assert res.status != "AMBIGUOUS"
    assert res.status == "RESOLVED"
