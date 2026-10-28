"""Rule N2 (SPEC invariant 19, canon/04 3.1, author decision 2026-10-28): a phrase of exactly
one token is allowed only in predicate position; every nominal phrase has >= 2 tokens.

N2 is checked AFTER the META -> structure -> vector selection, on the readings that selection
keeps; it never revives a reading the selection removed.
"""
from __future__ import annotations

import itertools

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from n2_check import violations
from openpona import ast, parse

# --------------------------------------------------------------- the checker itself
KNOWN_NEGATIVES = [
    ("({ilo} li {awen})", "subject"),
    ("({jan pali} li {pali} e {ilo})", "object"),
    ("({jan pali} li {pali} e ({ilo sitelen} anu {ijo}))", "object"),
    ("({jan pali} li tan {ma})", "source"),
    ("(tan {ni} la ({jan pali} li {pali}))", "source context"),
    ("({ma} la ({ilo pali} li {awen}))", "context"),
    ("(({ilo} anu {jan pali}) li {awen})", "subject"),
]


@pytest.mark.parametrize("skel,pos", KNOWN_NEGATIVES)
def test_the_checker_flags_known_negatives(skel, pos):
    # a checker is proven on a known-negative before it is trusted on parser output
    assert [p for p, _ in violations(skel)] == [pos]


@pytest.mark.parametrize("skel", ["{pali}", "({ilo pali} li {awen})", "({D1(ilo)} li {awen})",
                                  "({jan pali} li ({pona} anu {seme}))", "{ilo}"])
def test_the_checker_accepts_known_positives(skel):
    assert violations(skel) == []


# --------------------------------------------------------------- the 19 worked examples
EXAMPLES = [
    ("ilo li awen", "INVALID", None),
    ("ilo pali li awen", "RESOLVED", "({ilo pali} li {awen})"),
    ("pali", "RESOLVED", "{pali}"),
    ("ilo pali", "RESOLVED", "{ilo pali}"),
    ("jan pali li pali e ilo", "INVALID", None),
    ("jan pali li pali e ilo sitelen", "RESOLVED", "({jan pali} li {pali} e {ilo sitelen})"),
    ("jan pali li pali e ilo sitelen anu ijo", "INVALID", None),
    ("ilo pali li pona anu seme", "RESOLVED", "({ilo pali} li ({pona} anu {seme}))"),
    ("ilo pali li pona ala", "RESOLVED", "({ilo pali} li {pona ala})"),
    ("jan ni li lukin e ilo ilo", "RESOLVED", "({jan ni} li {lukin} e {D1(ilo)})"),
    ("jan pali li tan ma", "INVALID", None),
    ("jan pali li tan ma pali", "RESOLVED", "({jan pali} li tan {ma pali})"),
    ("tan ni la jan pali li pali", "INVALID", None),
    ("tan toki ni la jan pali li pali", "RESOLVED", "(tan {toki ni} la ({jan pali} li {pali}))"),
    ("ma la ilo pali li awen", "INVALID", None),
    ("ma pali la ilo pali li awen", "RESOLVED", "({ma pali} la ({ilo pali} li {awen}))"),
    ("jan pali li kama tan ma", "INVALID", None),
    ("ilo ilo li awen", "RESOLVED", "({D1(ilo)} li {awen})"),
    ("jan pali li lukin lukin", "RESOLVED", "({jan pali} li {D1(lukin)})"),
]


@pytest.mark.parametrize("surface,status,skeleton", EXAMPLES, ids=[f"ex{i + 1}" for i in range(19)])
def test_worked_example(surface, status, skeleton):
    res = parse(surface)
    assert res.status == status, (res.status, res.skeletons, res.errors)
    assert res.skeletons == ([skeleton] if skeleton else [])
    assert (res.alternatives == ()) == (skeleton is None)


# --------------------------------------------------------------- one test per position
def test_p1_main_expression_after_li_may_have_one_token_with_every_anu_alternative():
    for s in ("ilo pali li awen", "ilo pali li pona anu seme", "ilo pali li pona anu seme anu ala"):
        assert parse(s).status == "RESOLVED", s
    # P1 is the main expression only: the objects after it are nominal
    assert parse("ilo pali li pona anu seme e ilo").status == "INVALID"


def test_p2_a_bare_statement_is_a_predicate_of_any_length():
    for s in ("pali", "ilo", "ilo pali", "nasin open anu nasin awen", "ilo anu jan", "tan"):
        assert parse(s).status == "RESOLVED", s
    # a bare statement stops being bare as soon as it has `la`
    assert parse("ilo la jan pali li awen").status == "INVALID"


def test_n_a_the_subject_needs_two_tokens_also_in_every_anu_alternative():
    assert parse("ilo li awen").status == "INVALID"
    assert parse("ilo pali anu jan li awen").status == "INVALID"      # alternative `jan`
    assert parse("ilo pali anu jan pali li awen").status == "RESOLVED"
    assert parse("ilo ilo li awen").status == "RESOLVED"              # META counts its tokens
    assert parse("ilo pi sona lawa li awen").status == "RESOLVED"     # pi always passes


def test_n_b_every_object_needs_two_tokens():
    assert parse("jan pali li pali e ilo").status == "INVALID"
    assert parse("jan pali li pali e ilo sitelen e ijo").status == "INVALID"   # the 2nd object
    assert parse("jan pali li pali e ilo sitelen e ijo ante").status == "RESOLVED"
    assert parse("jan pali li pali e ilo ilo").status == "RESOLVED"
    assert parse("jan pali li pali e ilo pi sona lawa").status == "RESOLVED"


def test_n_c_source_phrases_source_predicates_and_source_contexts_need_two_tokens():
    assert parse("jan pali li pali e ilo sitelen tan ma").status == "INVALID"     # source phrase
    assert parse("jan pali li pali e ilo sitelen tan ma pali").status == "RESOLVED"
    assert parse("jan pali li tan ma").status == "INVALID"                         # source predicate
    assert parse("jan pali li tan ma pali tan kute").status == "INVALID"           # the 2nd source
    assert parse("tan ni la jan pali li pali").status == "INVALID"                 # source context
    assert parse("tan toki ni la jan pali li pali").status == "RESOLVED"


def test_n_d_a_context_without_li_needs_two_tokens_and_a_context_with_li_follows_the_table():
    assert parse("ma la ilo pali li awen").status == "INVALID"
    assert parse("ma pali la ilo pali li awen").status == "RESOLVED"
    # a context clause WITH its own li: subject nominal, predicate free
    assert parse("ma pali li awen la ilo pali li pona").status == "RESOLVED"
    assert parse("ma li awen la ilo pali li pona").status == "INVALID"             # subject `ma`
    # the clause after `la` has no `li`: it is nominal too
    assert parse("ma pali la ilo").status == "INVALID"
    assert parse("ma pali la ilo pali").status == "RESOLVED"


# --------------------------------------------------------------- order: after the selection
def test_n2_never_revives_a_reading_the_selection_removed():
    # the structural `tan` wins the selection, N2 drops it, the vector reading `{tan ma}` stays dead
    r = parse("jan pali li tan ma")
    assert r.status == "INVALID" and r.skeletons == [] and r.alternatives == ()
    # the META-maximal reading is selected, N2 drops it (source `ma`), the unfolded one stays dead
    assert parse("jan pali li ma pi ni ni tan tan ma").status == "INVALID"
    # same fold with a two-token source: N2 accepts the selected reading
    r = parse("jan pali li ma pi ni ni tan tan ma pali")
    assert r.skeletons == ["({jan pali} li {ma pi D1(ni) tan} tan {ma pali})"]


def test_n2_can_turn_an_ambiguous_selection_into_resolved():
    r = parse("jan pali li ilo tan tan ma")      # two structural readings; the 2nd has source `ma`
    assert r.status == "RESOLVED"
    assert r.skeletons == ["({jan pali} li {ilo} tan {tan ma})"]
    r = parse("jan pali li ilo tan tan ma pi ijo ante")   # both sources have >= 2 tokens
    assert r.status == "AMBIGUOUS" and len(r.skeletons) == 2


def test_meta_folding_never_changes_the_token_count():
    assert parse("ilo ilo li awen").skeletons == ["({D1(ilo)} li {awen})"]
    assert parse("ilo ilo ilo li awen").skeletons == ["({D2(ilo)} li {awen})"]
    assert parse("ilo ilo ilo ilo li awen").status == "RESOLVED"


# --------------------------------------------------------------- diagnostics
@pytest.mark.parametrize("surface,pos,tok,idx", [
    ("ilo li awen", "subject", "ilo", 1),
    ("jan pali li pali e ilo", "object", "ilo", 6),
    ("jan pali li tan ma", "source", "ma", 5),
    ("tan ni la jan pali li pali", "source context", "ni", 2),
    ("ma la ilo pali li awen", "context", "ma", 1),
    ("ma pali la ilo", "clause after la", "ilo", 4),
])
def test_diagnostic_names_the_position_and_the_token(surface, pos, tok, idx):
    res = parse(surface)
    assert res.status == "INVALID"
    msg = f"n2: {pos} '{tok}' has one token; a one-token phrase is allowed only as a predicate (N2)"
    assert any(e.startswith(msg) and e.endswith(f"(token {idx} '{tok}')") for e in res.errors), res.errors


def test_every_violation_is_reported_not_only_the_first():
    res = parse("ilo li pali e jan")
    assert [e.split("'")[1] for e in res.errors if e.startswith("n2:")] == ["ilo", "jan"]


# --------------------------------------------------------------- property: no 1-token nominal
def _nominal_phrase_sizes(tree) -> list:
    """Token counts of every nominal phrase of a typed tree (rule N2 positions)."""
    sizes = []

    def expr(e):
        if isinstance(e, ast.Alternative):
            expr(e.left)
            expr(e.right)
        else:
            sizes.append(e.span.end - e.span.start)

    def clause(c):
        if isinstance(c, ast.Predication):
            expr(c.subject)
            for p in c.predicates:
                for x in (p.objects.items if p.objects else ()):
                    expr(x)
                for x in (p.sources.items if p.sources else ()):
                    expr(x)
        else:
            expr(c)

    if isinstance(tree, ast.Context):
        (expr if tree.source else clause)(tree.context)
        clause(tree.body)
    elif isinstance(tree, ast.Predication):
        clause(tree)
    return sizes


def _check_reading(surface):
    res = parse(surface)
    for sk, tree in zip(res.skeletons, res.alternatives):
        assert violations(sk) == [], (surface, sk)
        assert all(n >= 2 for n in _nominal_phrase_sizes(tree)), (surface, sk)
    return res


SAMPLE = ["ilo", "pali", "jan", "ma", "li", "e", "tan", "anu"]


def test_no_resolved_reading_has_a_one_token_nominal_phrase_exhaustive():
    resolved = 0
    for n in range(1, 5):
        for seq in itertools.product(SAMPLE + ["la", "pi"], repeat=n):
            res = _check_reading(" ".join(seq))
            resolved += res.status != "INVALID"
    assert resolved > 100          # the sweep did reach readings (it is not vacuously empty)


@settings(max_examples=400, deadline=None, suppress_health_check=list(HealthCheck))
@given(st.lists(st.sampled_from(SAMPLE + ["la", "pi", "lukin", "seme"]), min_size=1, max_size=9))
def test_no_resolved_reading_has_a_one_token_nominal_phrase_random(toks):
    _check_reading(" ".join(toks))


def test_the_property_checks_would_catch_a_violation():
    # known-negative for the AST-side measurement used above
    tree = ast.from_skeleton("({ilo} li {awen})", ["ilo", "li", "awen"])
    assert _nominal_phrase_sizes(tree) == [1]
