"""TP-04 metamorphic and generator-driven properties (Hypothesis is REQUIRED).

Hypothesis is imported unconditionally: a missing dependency is a collection ERROR
(a setup failure), never a silent skip.  Properties run against BOTH the reference parser
and the independent oracle (tools/oracle/recognizer.py), so a property that only the
parser satisfies is visible.

Generator: statements are built from the grammar of SPEC 5-6 over DISTINCT semantic
tokens (no `tan`, no repetition), so the expected skeleton is known by construction and
is unique; the relations then hold between runs:
  1 constructive          the parse of a generated statement is the generated skeleton
  2 explicit grouping     appending `pi x y` to a phrase extends that phrase only;
                          three juxtaposed units in a phrase slot are INVALID
  3 alpha substitution    renaming semantic tokens injectively keeps status and shape
  4 stable token order    tokens/skeleton leaves/AST surface keep the surface order
  5 round trip            surface -> AST -> surface -> AST, JSON and skeleton readers
  6 boundary particles    a leading, trailing or doubled particle is INVALID
  7 whitespace/Unicode    spaces/tabs are free, other separators and look-alikes are not
  8 differential          oracle == parser unless a foldable run exists (known triage)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
import hypothesis
from hypothesis import HealthCheck, given, settings, strategies as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openpona import SEMANTIC, ast, parse  # noqa: E402
from tools.oracle import recognizer as oracle  # noqa: E402

PROFILE = dict(max_examples=120, deadline=None, derandomize=True, database=None,
               suppress_health_check=list(HealthCheck))
PARTICLES = ["li", "la", "e", "pi", "anu"]


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_hypothesis_is_installed_and_current():
    major = int(hypothesis.__version__.split(".")[0])
    assert major >= 6, "pyproject [test] extra requires hypothesis>=6 (setup failure, not a skip)"


def test_oracle_and_parser_agree_on_the_inventory():
    assert set(SEMANTIC) == set(oracle.SEMANTIC) and len(oracle.INVENTORY) == 42


# ------------------------------------------------------------------ generator
class Built:
    """A generated statement: surface text, expected skeleton, phrase list for edits."""

    def __init__(self, surface, skeleton, phrases):
        self.surface, self.skeleton, self.phrases = surface, skeleton, phrases


def _ph_surface(ph):
    head, groups = ph
    return " ".join(head + [x for g in groups for x in ("pi", *g)])


def _ph_skel(ph):
    return "{" + _ph_surface(ph) + "}"


def _expr_surface(ex):
    return " anu ".join(_ph_surface(p) for p in ex)


def _expr_skel(ex):
    out = _ph_skel(ex[-1])
    for p in reversed(ex[:-1]):
        out = "(" + _ph_skel(p) + " anu " + out + ")"
    return out


def _pred_surface(pr):
    head, objs, srcs = pr
    parts = [] if head is None else [_expr_surface(head)]
    parts += ["e " + _expr_surface(o) for o in objs]
    parts += ["tan " + _expr_surface(s) for s in srcs]
    return " ".join(parts)


def _pred_skel(pr):
    head, objs, srcs = pr
    parts = []
    if head is None:
        parts.append("tan " + _expr_skel(srcs[0]))
        srcs = srcs[1:]
    else:
        parts.append(_expr_skel(head))
    parts += ["e " + _expr_skel(o) for o in objs]
    parts += ["tan " + _expr_skel(s) for s in srcs]
    return " ".join(parts)


def _clause_surface(cl):
    subj, preds = cl
    return " li ".join([_expr_surface(subj)] + [_pred_surface(p) for p in preds])


def _clause_skel(cl):
    subj, preds = cl
    if not preds:
        return _expr_skel(subj)
    return "(" + " li ".join([_expr_skel(subj)] + [_pred_skel(p) for p in preds]) + ")"


def _all_phrases(stmt):
    kind, a, b, c = stmt
    exprs = []
    clauses = []
    if kind == "src":
        exprs.append(a)
        clauses.append(c)
    else:
        clauses.append(a)
        if b is not None:
            clauses.append(b)
    for cl in clauses:
        exprs.append(cl[0])
        for head, objs, srcs in cl[1]:
            if head is not None:
                exprs.append(head)
            exprs += list(objs) + list(srcs)
    return [p for ex in exprs for p in ex]


def _stmt_surface(stmt):
    kind, a, b, c = stmt
    if kind == "clause":
        return _clause_surface(a)
    if kind == "ctx":
        return _clause_surface(a) + " la " + _clause_surface(b)
    return "tan " + _expr_surface(a) + " la " + _clause_surface(c)


def _stmt_skel(stmt):
    kind, a, b, c = stmt
    if kind == "clause":
        return _clause_skel(a)
    if kind == "ctx":
        return "(" + _clause_skel(a) + " la " + _clause_skel(b) + ")"
    return "(tan " + _expr_skel(a) + " la " + _clause_skel(c) + ")"


@st.composite
def statements(draw, max_phrases=5):
    """-> stmt tuple whose phrases hold DISTINCT semantic tokens (mutable lists)."""
    pool = list(draw(st.permutations(SEMANTIC)))
    free = [max_phrases]

    def phrase():
        n_head = draw(st.integers(1, 2))
        n_groups = draw(st.integers(0, 2))
        head = [pool.pop() for _ in range(n_head)]
        groups = [[pool.pop(), pool.pop()] for _ in range(n_groups)]
        return [head, groups]

    def expr(alt_ok):
        k = 1
        if alt_ok and free[0] > 0:
            k += draw(st.integers(0, min(2, free[0])))
            free[0] -= k - 1
        return [phrase() for _ in range(k)]

    def clause():
        subj = expr(True)
        n_preds = draw(st.integers(0, min(2, free[0])))
        free[0] -= n_preds
        preds = []
        for i in range(n_preds):
            last = i == n_preds - 1
            source_pred = draw(st.booleans())
            nobj = 0 if source_pred else draw(st.integers(0, min(2, free[0])))
            free[0] -= nobj
            nsrc = draw(st.integers(1 if source_pred else 0, 1 if source_pred else min(2, free[0])))
            free[0] -= nsrc if not source_pred else nsrc - 1
            head = None if source_pred else expr(last)
            objs = [expr(last) for _ in range(nobj)]
            srcs = [expr(last) for _ in range(nsrc)]
            preds.append((head, objs, srcs))
        return (subj, preds)

    kind = draw(st.sampled_from(["clause", "ctx", "src"]))
    free[0] -= {"clause": 1, "ctx": 2, "src": 2}[kind]
    free[0] = max(free[0], 0)
    if kind == "clause":
        return (kind, clause(), None, None)
    if kind == "ctx":
        return (kind, clause(), clause(), None)
    return (kind, expr(False), None, clause())


def _build(stmt):
    return Built(_stmt_surface(stmt), _stmt_skel(stmt), _all_phrases(stmt))


# ------------------------------------------------------------------ 1 constructive
@settings(**PROFILE)
@given(statements())
def test_generated_statements_parse_to_the_generated_skeleton(stmt):
    b = _build(stmt)
    content = [t for t in b.surface.split() if t not in PARTICLES + ["tan"]]
    assert len(content) == len(set(content))             # the generator never repeats a token
    res = parse(b.surface)
    assert (res.status, res.skeletons) == ("RESOLVED", [b.skeleton]), b.surface
    ora = oracle.recognize(b.surface)
    assert (ora.status, ora.skeletons) == ("RESOLVED", [b.skeleton]), b.surface
    assert _canon(ast.shape(res.alternatives[0])) == _canon(ora.shapes[0])
    assert ast.to_surface(res.alternatives[0]) == b.surface


# ------------------------------------------------------------------ 2 explicit grouping
@settings(**PROFILE)
@given(statements(), st.data())
def test_adding_an_explicit_pi_group_extends_exactly_one_phrase(stmt, data):
    b = _build(stmt)
    used = set(b.surface.split())
    spare = [t for t in SEMANTIC if t not in used][:2]
    assert len(spare) == 2
    phrases = _all_phrases(stmt)
    k = data.draw(st.integers(0, len(phrases) - 1))
    before = _ph_skel(phrases[k])
    phrases[k][1].append(spare)          # the phrase object is shared with stmt
    after = _ph_skel(phrases[k])
    assert after == before[:-1] + " pi " + " ".join(spare) + "}"
    grouped = _build(stmt)
    for run in (lambda s: (parse(s).status, parse(s).skeletons),
                lambda s: (oracle.recognize(s).status, oracle.recognize(s).skeletons)):
        assert run(grouped.surface) == ("RESOLVED", [grouped.skeleton]), grouped.surface
    assert grouped.skeleton == b.skeleton.replace(before, after, 1)


@settings(**PROFILE)
@given(statements(), st.data())
def test_three_juxtaposed_units_in_any_phrase_slot_are_invalid(stmt, data):
    b = _build(stmt)
    used = set(b.surface.split())
    spare = [t for t in SEMANTIC if t not in used][:1]
    phrases = _all_phrases(stmt)
    k = data.draw(st.integers(0, len(phrases) - 1))
    ph = phrases[k]
    if len(ph[0]) == 1:
        ph[0].append(spare[0])           # head of two: still valid
        assert parse(_build(stmt).surface).status == "RESOLVED"
        ph[0].append([t for t in SEMANTIC if t not in used and t != spare[0]][0])
    else:
        ph[0].append(spare[0])
    bad = _build(stmt).surface            # a head of three units, no pi
    assert parse(bad).status == "INVALID", bad
    assert oracle.recognize(bad).status == "INVALID", bad


# ------------------------------------------------------------------ 3 alpha substitution
WORDS = ["jan", "ma", "ilo", "tan"] + PARTICLES
sequences = st.lists(st.sampled_from(WORDS), min_size=1, max_size=8)


def _rename_skeleton(skel, mapping):
    return re.sub(r"[a-z]+", lambda m: mapping.get(m.group(0), m.group(0)), skel)


@settings(**PROFILE)
@given(sequences, st.permutations(SEMANTIC))
def test_injective_renaming_of_semantic_tokens_keeps_status_and_shape(seq, perm):
    mapping = dict(zip(["jan", "ma", "ilo"], perm[:3]))      # `tan` and particles are fixed
    renamed = [mapping.get(t, t) for t in seq]
    for run in (parse, oracle.recognize):
        a, b = run(" ".join(seq)), run(" ".join(renamed))
        assert a.status == b.status
        assert sorted(_rename_skeleton(s, mapping) for s in a.skeletons) == sorted(b.skeletons)


# ------------------------------------------------------------------ 4 stable token order
def _leaves(skeleton):
    """Token sequence of a skeleton in surface order (D<n>(P) -> n+1 copies of P)."""
    def expand(m):
        return " ".join([m.group(2)] * (int(m.group(1)) + 1))
    s = re.sub(r"D(\d+)\(([^)]*)\)", expand, skeleton)
    return [t for t in re.findall(r"[a-z]+", s)]


@settings(**PROFILE)
@given(sequences)
def test_every_reading_keeps_the_surface_token_order(seq):
    surface = " ".join(seq)
    res = parse(surface)
    assert res.tokens == seq
    for s in res.skeletons:
        assert _leaves(s) == seq
    for a in res.alternatives:
        assert ast.to_surface(a).split() == seq
    for s in oracle.recognize(surface).skeletons:
        assert _leaves(s) == seq


# ------------------------------------------------------------------ 5 round trips
@settings(**PROFILE)
@given(sequences)
def test_surface_ast_round_trips(seq):
    res = parse(" ".join(seq))
    for alt in res.alternatives:
        again = parse(ast.to_surface(alt))
        assert alt in again.alternatives
        assert ast.from_json(ast.to_json(alt)) == alt
        assert ast.from_skeleton(ast.to_skeleton(alt), res.tokens) == alt


@settings(**PROFILE)
@given(statements())
def test_generated_statement_round_trip_through_json_and_skeleton(stmt):
    b = _build(stmt)
    res = parse(b.surface)
    alt = res.alternatives[0]
    assert ast.from_json(json.loads(ast.to_canonical_json(alt))) == alt
    assert ast.to_skeleton(alt) == b.skeleton


# ------------------------------------------------------------------ 6 boundary particles
@settings(**PROFILE)
@given(statements(), st.sampled_from(PARTICLES))
def test_a_leading_trailing_or_doubled_particle_is_invalid(stmt, particle):
    b = _build(stmt)
    toks = b.surface.split()
    variants = [particle + " " + b.surface, b.surface + " " + particle]
    present = [i for i, t in enumerate(toks) if t == particle]
    if present:
        i = present[0]
        variants.append(" ".join(toks[:i + 1] + [particle] + toks[i + 1:]))
    for v in variants:
        assert parse(v).status == "INVALID", v
        assert oracle.recognize(v).status == "INVALID", v


# ------------------------------------------------------------------ 7 whitespace / Unicode
SPACING = st.lists(st.sampled_from([" ", "  ", "\t", " \t ", "   "]), min_size=1, max_size=40)
LINE_SEPARATORS = ["\n", "\r", "\r\n", " ", " ", "\x85", "\x0b", "\x0c"]
LOOKALIKES = {"i": "і", "o": "о", "a": "а", "e": "е", "n": "ｎ", "l": "ӏ"}


@settings(**PROFILE)
@given(statements(), SPACING, SPACING, SPACING)
def test_spaces_and_tabs_are_free_between_and_around_tokens(stmt, gaps, lead, trail):
    toks = _build(stmt).surface.split()
    noisy = "".join(lead[:1]) + "".join(
        t + gaps[i % len(gaps)] for i, t in enumerate(toks[:-1])) + toks[-1] + "".join(trail[:1])
    clean = " ".join(toks)
    for run in (parse, oracle.recognize):
        a, b = run(noisy), run(clean)
        assert (a.status, a.skeletons) == (b.status, b.skeletons) == ("RESOLVED", [_build(stmt).skeleton])


@settings(**PROFILE)
@given(statements(), st.sampled_from(LINE_SEPARATORS), st.data())
def test_a_line_separator_between_tokens_is_invalid(stmt, sep, data):
    toks = _build(stmt).surface.split()
    if len(toks) < 2:
        return
    i = data.draw(st.integers(1, len(toks) - 1))
    s = " ".join(toks[:i]) + sep + " ".join(toks[i:])
    assert parse(s).status == "INVALID", repr(s)
    assert oracle.recognize(s).status == "INVALID", repr(s)


@settings(**PROFILE)
@given(statements(), st.data())
def test_lookalike_case_and_invisible_characters_inside_a_token_are_invalid(stmt, data):
    toks = _build(stmt).surface.split()
    i = data.draw(st.integers(0, len(toks) - 1))
    t = toks[i]
    forms = [t.upper(), t.capitalize(), t + "​", "​" + t, t + "́", t + "­",
             t[:1] + "‍" + t[1:], t + "﻿"]
    for ch, rep in LOOKALIKES.items():
        if ch in t:
            forms.append(t.replace(ch, rep, 1))
    nbsp = " ".join(toks[:i]) + ("\xa0" if i else "") + " ".join(toks[i:])
    if i:
        forms = [" ".join(toks[:i] + [f] + toks[i + 1:]) for f in forms] + [nbsp]
    else:
        forms = [" ".join([f] + toks[1:]) for f in forms]
    for s in forms:
        assert parse(s).status == "INVALID", repr(s)
        assert oracle.recognize(s).status == "INVALID", repr(s)


# ------------------------------------------------------------------ 8 differential
VECTORS = set(SEMANTIC) | {"tan"}


def _foldable_run(toks):
    """SPEC 7: some P (one vector token, or two different ones) occurs twice in a row."""
    for p in (1, 2):
        for i in range(len(toks) - 2 * p + 1):
            a, b = toks[i:i + p], toks[i + p:i + 2 * p]
            if a == b and all(x in VECTORS for x in a) and not (p == 2 and a[0] == a[1]):
                return True
    return False


@st.composite
def mutated(draw):
    """A generated statement with one token dropped, duplicated, swapped, replaced or added."""
    data = draw(statements())
    toks = _build(data).surface.split()
    return _mutate(toks, draw)


def _mutate(toks, draw):
    op = draw(st.sampled_from(["drop", "dup", "swap", "particle", "insert"]))
    i = draw(st.integers(0, len(toks) - 1))
    if op == "drop":
        toks = toks[:i] + toks[i + 1:]
    elif op == "dup":
        toks = toks[:i + 1] + toks[i:]
    elif op == "swap" and i + 1 < len(toks):
        toks[i], toks[i + 1] = toks[i + 1], toks[i]
    elif op == "particle":
        toks[i] = draw(st.sampled_from(PARTICLES + ["tan"]))
    else:
        toks = toks[:i] + [draw(st.sampled_from(WORDS))] + toks[i:]
    return toks


@settings(**PROFILE)
@given(st.one_of(sequences, mutated()))
def test_oracle_and_parser_agree_unless_a_triaged_family_applies(toks):
    """No foldable run: identical. Foldable run without `tan`: identical unless the parser
    folds unconditionally (it answers INVALID where the oracle has the unfolded reading:
    triage class meta-fold-fallback). Foldable run with `tan`: only 'never more permissive'
    is asserted (triage class priority-combination, see tools/oracle/triaged.json)."""
    if not toks:
        return
    surface = " ".join(toks)
    o, p = oracle.recognize(surface), parse(surface)
    if o.status == "INVALID":                       # the parser is never more permissive
        assert p.status == "INVALID", surface
    foldable = _foldable_run(toks)
    if foldable and "tan" in toks:
        return
    if foldable and p.status == "INVALID" and o.status != "INVALID":
        return                                      # meta-fold-fallback
    assert (o.status, o.skeletons) == (p.status, p.skeletons), surface
    assert sorted(_canon(s) for s in o.shapes) == \
        sorted(_canon(ast.shape(a)) for a in p.alternatives), surface


# ------------------------------------------------------------------ 9 anu-then-li (SPEC 6)
@st.composite
def anu_chains(draw):
    pool = list(draw(st.permutations(SEMANTIC)))
    t = [pool.pop() for _ in range(6)]
    return t


@settings(**PROFILE)
@given(anu_chains(), st.sampled_from(["plain", "object", "source"]))
def test_a_predicate_with_anu_must_be_the_last_predicate(t, shape):
    s, p, q, r, o, _x = t
    mid = {"plain": f"{p} anu {q}", "object": f"{p} e {o} anu {q}", "source": f"{p} tan {o} anu {q}"}[shape]
    bad = f"{s} li {mid} li {r}"
    ok_last = f"{s} li {r} li {mid}"
    ok_subject = f"{s} anu {q} li {p}"
    for run in (parse, oracle.recognize):
        assert run(bad).status == "INVALID", bad
        assert run(ok_last).status == "RESOLVED", ok_last
        assert run(ok_subject).status == "RESOLVED", ok_subject


# ------------------------------------------------------------------ 10 META depth (SPEC 7)
@settings(**PROFILE)
@given(st.permutations(SEMANTIC), st.integers(2, 7), st.integers(1, 2), st.booleans())
def test_n_consecutive_copies_are_one_meta_unit_of_depth_n_minus_1(perm, n, width, with_tail):
    unit = perm[:width]
    tail = perm[width] if with_tail else None
    surface = " ".join(unit * n + ([tail] if tail else []))
    skeleton = "{D%d(%s)%s}" % (n - 1, " ".join(unit), " " + tail if tail else "")
    for run in (parse, oracle.recognize):
        res = run(surface)
        assert (res.status, res.skeletons) == ("RESOLVED", [skeleton]), surface
    assert _leaves(skeleton) == surface.split()
