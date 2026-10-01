"""Property tests of the reference parser (hypothesis)."""
import pytest

pytest.importorskip("hypothesis")
from hypothesis import assume, given, settings, strategies as st  # noqa: E402

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
    assume(a != b)
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


distinct4 = st.lists(sem, min_size=4, max_size=4, unique=True)
distinct3 = st.lists(sem, min_size=3, max_size=3, unique=True)


def test_tan_alone_is_a_unit():
    res = parse("tan")
    assert res.status == "RESOLVED"
    assert res.skeletons == ["{tan}"]


@given(distinct4)
def test_pi_group_is_exactly_two_units(t):
    a, b, c, d = t
    res = parse(f"{a} {b} pi {c} {d}")
    assert res.status == "RESOLVED"
    assert res.skeletons == ["{" + f"{a} {b} pi {c} {d}" + "}"]


@given(distinct3)
def test_pi_with_wrong_group_sizes_is_invalid(t):
    a, b, c = t
    for text in (f"{a} pi {b}", f"{a} {b} pi {c}"):
        res = parse(text)
        assert res.status == "INVALID" and res.skeletons == []


@given(st.sampled_from(STRUCTURAL).filter(lambda x: x != "tan"), distinct3.map(lambda t: t[:2]))
def test_structural_token_at_clause_start_is_invalid(s, t):
    a, b = t
    assert parse(f"{s} {a} li {b}").status == "INVALID"


@settings(deadline=None)
@given(distinct3)
def test_several_li_form_one_group(t):
    a, b, c = t
    res = parse(f"{a} li {b} li {c}")
    assert res.status == "RESOLVED"
    assert res.skeletons == ["({" + a + "} li {" + b + "} li {" + c + "})"]


PARTICLES = ("li", "la", "e", "pi", "anu")
all_tokens = st.sampled_from(TOKENS)


@settings(deadline=None, max_examples=300)
@given(st.lists(all_tokens, min_size=1, max_size=10))
def test_any_token_sequence_returns_a_known_status(toks):
    res = parse(" ".join(toks))
    assert res.status in {"RESOLVED", "AMBIGUOUS", "INVALID"}


# runs of a semantic unit separated by particles: forces D(...) to appear in every skeleton,
# and puts repeated particles next to them so a fold across a particle would be visible
_sem = st.sampled_from(SEMANTIC)
_run = st.tuples(_sem, st.integers(min_value=2, max_value=4)).map(lambda t: " ".join([t[0]] * t[1]))


@settings(deadline=None, max_examples=300)
@given(_run, _run, st.sampled_from(PARTICLES))
def test_meta_units_never_contain_a_particle(run_a, run_b, p):
    import re
    a, b = run_a.split()[0], run_b.split()[0]
    assume(a != b)
    # `A A li B B` is valid and must fold both runs; `A A p p B B` must be INVALID (particle run)
    ok = parse(f"{run_a} li {run_b}")
    assert ok.status == "RESOLVED", ok.errors
    assert ok.skeletons == [f"({{D{len(run_a.split()) - 1}({a})}} li {{D{len(run_b.split()) - 1}({b})}})"]
    bad = parse(f"{run_a} {p} {p} {run_b}")
    assert bad.status == "INVALID"
    for sk in ok.skeletons + bad.skeletons:
        for inner in re.findall(r"D\d+\(([^)]*)\)", sk):
            assert not set(inner.split()) & set(PARTICLES), sk


@given(st.sampled_from(PARTICLES), distinct3.map(lambda t: t[:2]))
def test_particle_at_position_zero_is_invalid(p, t):
    a, b = t
    assert parse(f"{p} {a} li {b}").status == "INVALID"


@given(distinct3)
def test_uppercase_variant_is_invalid(t):
    a, b, c = t
    text = f"{a} li {b} e {c}"
    assert parse(text).status == "RESOLVED"
    res = parse(text.upper())
    assert res.status == "INVALID" and res.skeletons == []
    assert res.errors[0].startswith("case:")


@settings(deadline=None)
@given(distinct3)
def test_tan_after_li_is_a_source_predicate(t):
    a, b, _ = t
    res = parse(f"{a} li tan {b}")
    assert res.status == "RESOLVED", res.errors
    assert res.skeletons == ["({" + a + "} li tan {" + b + "})"]


@settings(deadline=None)
@given(distinct3)
def test_e_after_tan_is_invalid(t):
    a, b, c = t
    res = parse(f"{a} li {b} tan {c} e {a}")
    assert res.status == "INVALID" and res.skeletons == []
    assert any(e.startswith("e-after-tan:") for e in res.errors), res.errors


@settings(deadline=None)
@given(distinct3)
def test_anu_predicate_must_be_last(t):
    a, b, c = t
    bad = parse(f"{a} li {b} anu {c} li {a}")
    assert bad.status == "INVALID" and bad.skeletons == []
    assert any(e.startswith("anu-then-li:") for e in bad.errors), bad.errors
    ok = parse(f"{a} anu {b} li {c}")
    assert ok.status == "RESOLVED", ok.errors


@settings(deadline=None)
@given(distinct3)
def test_tan_initial_is_source_context_else_vector(t):
    a, b, c = t
    ctx = parse(f"tan {a} la {b} li {c}")
    assert ctx.status == "RESOLVED", ctx.errors
    assert ctx.skeletons == [f"(tan {{{a}}} la ({{{b}}} li {{{c}}}))"]
    vec = parse(f"{a} tan la {b} li {c}")
    assert vec.status == "RESOLVED", vec.errors
    assert vec.skeletons == [f"({{{a} tan}} la ({{{b}}} li {{{c}}}))"]
