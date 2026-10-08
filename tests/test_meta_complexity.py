"""TP-01: bounded META parsing - complexity, budgets, and output equivalence.

Every check here is bounded: budgets cap the parser, the benchmark runs each
case in a subprocess with a hard timeout, and wall-clock assertions are loose.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from functools import lru_cache
from itertools import product
from pathlib import Path

import pytest

from hypothesis import given, settings, strategies as st  # noqa: E402
from lark import Lark, Token, Tree  # noqa: E402
from lark.exceptions import LarkError  # noqa: E402

from openpona import RESOURCE_EXHAUSTED, Budget, ParseStats, parse  # noqa: E402
from openpona import parser as P  # noqa: E402
from openpona.__main__ import main as cli_main  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _load_bench():
    spec = importlib.util.spec_from_file_location("bench_meta", ROOT / "tools" / "bench_meta.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BENCH = _load_bench()
make_case = BENCH.make_case
LONG203 = make_case("long203", 203)


def _meta_case(cid: str) -> dict:
    for line in (ROOT / "conformance" / "meta.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            case = json.loads(line)
            if case["id"] == cid:
                return case
    raise KeyError(cid)


# ------------------------------------------------------------ scaling
def test_nonoverlap_n20_completes_under_2s():
    text = make_case("nonoverlap", 20)
    t0 = time.perf_counter()
    res = parse(text)
    assert time.perf_counter() - t0 < 2.0
    assert res.status == "RESOLVED"
    assert res.skeletons[0].count("D1(") == 20


def test_nonoverlap_work_grows_at_most_cubically():
    work = {}
    for n in (8, 12, 16, 20):
        st_ = ParseStats()
        res = parse(make_case("nonoverlap", n), stats=st_)
        assert res.status == "RESOLVED"
        assert st_.runs == n and st_.components == n
        assert st_.fold_candidates == 1  # independent runs never multiply
        work[n] = st_.work
    assert work[8] < work[12] < work[16] < work[20]
    assert work[20] / work[8] <= (20 / 8) ** 3, work


def test_work_counter_is_deterministic():
    a, b = ParseStats(), ParseStats()
    parse(make_case("random", 16), stats=a)
    parse(make_case("random", 16), stats=b)
    assert a.work == b.work and a.work > 0


def test_long_203_token_statement_within_default_budget():
    st_ = ParseStats()
    res = parse(LONG203, stats=st_)
    assert len(LONG203.split()) == 203
    assert res.status == "RESOLVED"
    assert res.skeletons == ["({jan} li {pali}" + " e {ilo}" * 100 + ")"]
    b = P.DEFAULT_BUDGET
    assert st_.max_depth < b.max_depth and st_.forest_steps < b.max_forest_steps


def test_parse_does_not_depend_on_the_recursion_limit():
    depth, f = 0, sys._getframe()
    while f is not None:
        depth, f = depth + 1, f.f_back
    before = sys.getrecursionlimit()
    sys.setrecursionlimit(depth + 150)  # test-only: the parser itself never touches it
    try:
        res = parse(LONG203)
    finally:
        sys.setrecursionlimit(before)
    assert res.status == "RESOLVED"
    assert sys.getrecursionlimit() == before


def test_repeated_source_predicates_do_not_multiply():
    # `jan li tan X li tan Y ...`: each predicate has a structural and a vector-tan
    # reading (2^84 raw readings); C8 keeps one, and the forest is never unpacked.
    words = ["ilo", "sona", "ma", "kama", "pali", "jan"]
    text = "jan " + " ".join(f"li tan {words[i % 6]}" for i in range(84))
    assert len(text.split()) == 253
    t0 = time.perf_counter()
    res = parse(text)
    assert time.perf_counter() - t0 < 2.0
    assert res.status == "RESOLVED" and len(res.skeletons) == 1
    assert "{tan" not in res.skeletons[0]


def test_overlap_family_beyond_budget_is_exhausted_fast():
    ok = parse(make_case("overlap", 8))
    assert ok.status == "AMBIGUOUS" and len(ok.skeletons) == 2 ** 8
    t0 = time.perf_counter()
    res = parse(make_case("overlap", 12))
    assert time.perf_counter() - t0 < 1.0
    assert res.status == RESOURCE_EXHAUSTED and res.reason == "max_fold_candidates"
    assert res.skeletons == []


# ------------------------------------------------------- m11 / m12 kept
@pytest.mark.parametrize("cid", ["m11", "m12"])
def test_m11_m12_outcomes_kept_with_all_parses(cid):
    case = _meta_case(cid)
    res = parse(case["surface"])
    assert res.status == case["expect_status"]
    assert sorted(res.skeletons) == sorted(case["expect_skeletons"])


def test_m12_is_ambiguous_not_silently_resolved():
    res = parse(_meta_case("m12")["surface"])
    assert res.status == "AMBIGUOUS" and len(res.skeletons) == 2


# ---------------------------------------------------- resource budgets
EXHAUST = [
    ("max_tokens", LONG203, Budget(max_tokens=10)),
    ("max_fold_candidates", "jan pali jan pali jan", Budget(max_fold_candidates=1)),
    ("max_skeletons", "jan pali jan pali jan", Budget(max_skeletons=1)),
    ("max_forest_steps", LONG203, Budget(max_forest_steps=50)),
    ("max_depth", LONG203, Budget(max_depth=20)),
    ("max_seconds", LONG203, Budget(max_seconds=0.0)),
]


@pytest.mark.parametrize("name,text,budget", EXHAUST, ids=[e[0] for e in EXHAUST])
def test_tiny_budget_yields_resource_exhausted(name, text, budget):
    full = parse(text)
    assert full.status in ("RESOLVED", "AMBIGUOUS")  # the input does have a verdict
    res = parse(text, budget=budget)
    assert res.status == RESOURCE_EXHAUSTED
    assert res.status not in ("INVALID", "RESOLVED", "AMBIGUOUS")
    assert res.skeletons == []
    assert res.reason == name
    assert name in res.errors[0]


def test_invalid_input_with_budget_is_never_reported_resolved():
    # an INVALID input stays INVALID or becomes RESOURCE_EXHAUSTED, never RESOLVED
    text = make_case("random", 20)
    assert parse(text).status == "INVALID"
    res = parse(text, budget=Budget(max_forest_steps=1, max_depth=1))
    assert res.status in ("INVALID", RESOURCE_EXHAUSTED)


def test_unknown_token_beats_the_length_budget():
    # a definite syntax verdict is cheap and is reported before any budget
    res = parse(" ".join(["jan"] * 300 + ["xyz"]))
    assert res.status == "INVALID" and res.reason is None


def test_cli_exit_code_for_resource_exhausted(capsys):
    assert cli_main(["parse", " ".join(["jan"] * 257)]) == 3
    assert cli_main(["parse", "jan li pali"]) == 0
    assert cli_main(["parse", "li li"]) == 1
    capsys.readouterr()


_alpha = st.sampled_from(["jan", "pali", "ilo", "tan", "li", "e", "pi", "anu", "la"])
_budgets = st.builds(
    Budget,
    max_tokens=st.integers(1, 12),
    max_fold_candidates=st.integers(1, 4),
    max_skeletons=st.integers(1, 4),
    max_forest_steps=st.integers(1, 400),
    max_depth=st.integers(1, 15),
)


@settings(deadline=None, max_examples=300)
@given(st.lists(_alpha, min_size=1, max_size=10), _budgets)
def test_a_budget_never_changes_a_verdict(toks, budget):
    """No fail-open: any budget either reproduces the unbounded verdict exactly
    or answers RESOURCE_EXHAUSTED with no skeletons."""
    text = " ".join(toks)
    full = parse(text)
    res = parse(text, budget=budget)
    if res.status == RESOURCE_EXHAUSTED:
        assert res.skeletons == [] and res.reason
    else:
        assert (res.status, res.skeletons, res.errors) == (full.status, full.skeletons, full.errors)


# ------------------------------------------- equivalence with the baseline
# Reference oracle = the pre-TP-01 algorithm: brute-force maximal run sets, a
# Lark tree with explicit ambiguity, full recursive expansion, global C8.
def _ref_maximal_sets(runs):
    def overlap(a, b):
        return a[0] < b[1] and b[0] < a[1]

    found = []

    def rec(idx, chosen):
        if idx == len(runs):
            if all(r in chosen or any(overlap(r, c) for c in chosen) for r in runs):
                found.append(list(chosen))
            return
        r = runs[idx]
        if not any(overlap(r, c) for c in chosen):
            chosen.append(r)
            rec(idx + 1, chosen)
            chosen.pop()
        rec(idx + 1, chosen)

    rec(0, [])
    return found


def _ref_fold_candidates(toks):
    runs = P._find_runs(toks)
    if not runs:
        return {" ".join(toks)}
    out = set()
    for chosen in _ref_maximal_sets(runs):
        by_start = {r[0]: r for r in chosen}
        parts, i = [], 0
        while i < len(toks):
            if i in by_start:
                s, e, k, p = by_start[i]
                parts.append(f"D{k - 1}({' '.join(p)})")
                i = e
            else:
                parts.append(toks[i])
                i += 1
        out.add(" ".join(parts))
    return out


@lru_cache(maxsize=None)
def _ref_lark():
    text = (ROOT / "openpona" / "grammar.lark").read_text(encoding="utf-8")
    return Lark(text, parser="earley", lexer="dynamic", ambiguity="explicit",
                keep_all_tokens=True, start="start")


def _ref_alts(node, memo):
    if isinstance(node, Token):
        return {str(node)}
    if id(node) in memo:
        return memo[id(node)]
    if node.data == "_ambig":
        res = set().union(*(_ref_alts(c, memo) for c in node.children))
    else:
        res = {P._fmt(node.data, combo)
               for combo in product(*[sorted(_ref_alts(c, memo)) for c in node.children])}
    memo[id(node)] = res
    return res


def _ref_parse(toks):
    skels = set()
    for cand in _ref_fold_candidates(toks):
        try:
            tree = _ref_lark().parse(cand)
        except LarkError:
            continue
        if isinstance(tree, Tree):
            skels |= _ref_alts(tree, {})
    out = sorted(P._prefer_structure(skels))
    if not out:
        return "INVALID", []
    return ("RESOLVED" if len(out) == 1 else "AMBIGUOUS"), out


_rep_alpha = st.sampled_from(["jan", "pali", "ilo", "tan", "li", "e"])


@settings(deadline=None, max_examples=300)
@given(st.lists(_rep_alpha, min_size=1, max_size=12))
def test_fold_candidates_equal_bruteforce_maximal_sets(toks):
    assert set(P.fold_candidates(toks)) == _ref_fold_candidates(toks)


def test_fold_candidates_exhaustive_small_alphabet():
    # every sequence of length <= 8 over three units; includes components where a
    # run lies entirely in the gap between two chosen runs, e.g.
    # `jan jan pali jan pali jan pali pali` (a successor must not skip it)
    n = 0
    for length in range(1, 9):
        for toks in product(["jan", "pali", "tan"], repeat=length):
            assert set(P.fold_candidates(list(toks))) == _ref_fold_candidates(list(toks)), toks
            n += 1
    assert n == sum(3 ** k for k in range(1, 9))


@settings(deadline=None, max_examples=400)
@given(st.lists(st.sampled_from(["jan", "pali", "ilo", "tan", "li", "e", "pi", "anu", "la"]),
                min_size=1, max_size=9))
def test_parse_equals_reference_algorithm(toks):
    res = parse(" ".join(toks))
    status, skels = _ref_parse(toks)
    assert res.status == status
    assert res.skeletons == skels


def test_parse_equals_reference_on_every_conformance_surface():
    seen = 0
    for path in sorted((ROOT / "conformance").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            surface = json.loads(line)["surface"]
            toks = surface.split()
            if (len(surface.splitlines()) != 1 or any(c.isupper() for c in surface)
                    or len(toks) > 40 or not set(toks) <= set(P.TOKENS)):
                continue
            res = parse(surface)
            status, skels = _ref_parse(toks)
            assert (res.status, res.skeletons) == (status, skels), surface
            seen += 1
    assert seen >= 80


# ------------------------------------------------- bounded CI benchmark
def test_bounded_adversarial_benchmark_cannot_hang(monkeypatch):
    """Runs the published fixture families in subprocesses with a hard cap:
    a regression to exponential folding shows up as TIMEOUT, never as a hang."""
    monkeypatch.setenv("PYTHONPATH", str(ROOT))  # measure this tree
    t0 = time.perf_counter()
    rows = BENCH.bench([8, 20], cap=15.0, seed=0)
    assert time.perf_counter() - t0 < 50
    by = {(r["family"], r["n"]): r for r in rows}
    assert not [r for r in rows if r["status"] in ("TIMEOUT", "ERROR")], rows
    assert by[("nonoverlap", 20)]["status"] == "RESOLVED"
    assert by[("nonoverlap", 20)]["seconds"] < 2.0
    assert by[("overlap", 20)]["status"] == RESOURCE_EXHAUSTED
    assert by[("random", 20)]["status"] == "INVALID"
    assert by[("long203", 203)]["status"] == "RESOLVED"
    assert all(Path(r["module"]).resolve() == ROOT / "openpona" / "__init__.py" for r in rows)
