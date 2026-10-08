"""TP-02: typed AST and the versioned parse API (parser API 1.0.0)."""
import dataclasses
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

import openpona
from openpona import PARSER_API_VERSION, ast, parse
from openpona.parser import _vector_tans

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "conformance"
CASES = [json.loads(ln) for p in sorted(CONF.glob("*.jsonl"))
         for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
NON_INVALID = [c for c in CASES if c["expect_status"] != "INVALID"]
INVALID = [c for c in CASES if c["expect_status"] == "INVALID"]
IDS = [c["id"] for c in CASES]


def _case(cid):
    return next(c for c in CASES if c["id"] == cid)


def _only(surface):
    res = parse(surface)
    assert len(res.alternatives) == 1, (surface, res.status)
    return res.alternatives[0]


# ------------------------------------------------------------ conformance
def test_all_96_baseline_cases_are_loaded():
    assert len(CASES) == 96


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_alternative_count_equals_expected_skeleton_count(case):
    res = parse(case["surface"])
    expect = 0 if case["expect_status"] == "INVALID" else len(case["expect_skeletons"])
    assert len(res.alternatives) == expect
    assert isinstance(res.alternatives, tuple)
    # status contract: RESOLVED one, AMBIGUOUS several, INVALID none
    assert {"RESOLVED": 1, "INVALID": 0}.get(res.status, 2) == len(res.alternatives) or (
        res.status == "AMBIGUOUS" and len(res.alternatives) >= 2)


@pytest.mark.parametrize("case", NON_INVALID, ids=[c["id"] for c in NON_INVALID])
def test_tree_meaning_matches_the_oracle_independent_of_pretty_printing(case):
    """The legacy skeleton is a projection of the tree: rendering each tree back
    gives exactly the oracle's skeleton set (compared as sets, not strings of a
    particular print format elsewhere)."""
    res = parse(case["surface"])
    assert {ast.to_skeleton(a) for a in res.alternatives} == set(case["expect_skeletons"])
    assert [ast.to_skeleton(a) for a in res.alternatives] == res.skeletons
    # and the oracle skeleton read independently builds the same tree
    for sk in case["expect_skeletons"]:
        tree = ast.from_skeleton(sk, res.tokens)
        assert tree in res.alternatives


@pytest.mark.parametrize("case", NON_INVALID, ids=[c["id"] for c in NON_INVALID])
def test_json_round_trip_equality(case):
    for a in parse(case["surface"]).alternatives:
        d = ast.to_json(a)
        assert ast.from_json(d) == a
        assert ast.from_json(json.loads(json.dumps(d))) == a
        assert ast.to_canonical_json(a) == json.dumps(
            d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        assert ast.to_json(ast.from_json(d)) == d


@pytest.mark.parametrize("case", NON_INVALID, ids=[c["id"] for c in NON_INVALID])
def test_surface_round_trip_structural_equality(case):
    res = parse(case["surface"])
    for a in res.alternatives:
        surface = ast.to_surface(a)
        assert surface == " ".join(res.tokens)
        again = parse(surface)
        assert again.status == res.status
        assert a in again.alternatives
        assert any(ast.shape(a) == ast.shape(b) for b in again.alternatives)
    assert [ast.to_json(a) for a in parse(ast.to_surface(res.alternatives[0])).alternatives] \
        == [ast.to_json(a) for a in res.alternatives]


@pytest.mark.parametrize("case", NON_INVALID, ids=[c["id"] for c in NON_INVALID])
def test_spans_cover_the_token_list_exactly(case):
    res = parse(case["surface"])
    for a in res.alternatives:
        assert (a.span.start, a.span.end) == (0, len(res.tokens))
        assert ast.to_tokens(a) == res.tokens
        for n in ast.walk(a):
            assert 0 <= n.span.start < n.span.end <= len(res.tokens)
            if isinstance(n, ast.Unit) and not isinstance(n, ast.Meta):
                assert res.tokens[n.span.start] == n.token


# --------------------------------------------------------- ambiguity / order
def test_ambiguous_keeps_every_parse_in_stable_order():
    res = parse("jan pali jan pali jan")
    assert res.status == "AMBIGUOUS"
    assert [ast.to_skeleton(a) for a in res.alternatives] == [
        "{D1(jan pali) jan}", "{jan D1(pali jan)}"]
    first, second = res.alternatives
    assert isinstance(first.head[0], ast.Meta) and isinstance(second.head[1], ast.Meta)
    assert first != second and ast.shape(first) != ast.shape(second)
    assert parse("jan pali jan pali jan").alternatives == res.alternatives  # deterministic


def test_operand_order_is_preserved():
    alt = _only("nasin open anu nasin awen")
    assert isinstance(alt, ast.Alternative)
    assert [h.token for h in alt.left.head] == ["nasin", "open"]
    assert [h.token for h in alt.right.head] == ["nasin", "awen"]
    swapped = _only("nasin awen anu nasin open")
    assert ast.shape(alt) != ast.shape(swapped)

    objs = _only("ilo li pana e ilo e sitelen").predicates[0].objects
    assert [o.head[0].token for o in objs.items] == ["ilo", "sitelen"]

    srcs = _only("jan li pali e ijo tan ma tan kute").predicates[0].sources
    assert [s.head[0].token for s in srcs.items] == ["ma", "kute"]

    chain = _only("jan li pali anu pali anu pali").predicates[0].head
    assert isinstance(chain, ast.Alternative) and isinstance(chain.right, ast.Alternative)
    preds = _only("jan li pali li awen").predicates
    assert [p.head.head[0].token for p in preds] == ["pali", "awen"]


def test_pi_grouping_survives_json_and_round_trip():
    p10 = _only("jan pi ilo sona pi sona lawa")
    assert [h.token for h in p10.head] == ["jan"]
    assert [(g.left.token, g.right.token) for g in p10.groups] == [
        ("ilo", "sona"), ("sona", "lawa")]
    assert ast.from_json(ast.to_json(p10)) == p10

    # same tokens, different grouping -> different trees (no flattening to a token list)
    p09 = _only("jan ilo pi sona lawa")
    assert [h.token for h in p09.head] == ["jan", "ilo"]
    assert [(g.left.token, g.right.token) for g in p09.groups] == [("sona", "lawa")]
    assert ast.to_tokens(p09) == ["jan", "ilo", "pi", "sona", "lawa"]
    assert ast.shape(p09) != ast.shape(_only("jan pi sona lawa"))
    for surface in ("sona pali pi ken pali", "jan ilo pi sona pali li pana e sitelen",
                    "sona pali pi ken pali anu ala"):
        for a in parse(surface).alternatives:
            assert parse(ast.to_surface(a)).alternatives == (a,)


def test_meta_depth_and_unit_are_explicit():
    m = _only("ilo sitelen ilo sitelen").head[0]
    assert isinstance(m, ast.Meta) and m.depth == 1
    assert [u.token for u in m.unit] == ["ilo", "sitelen"] and (m.span.start, m.span.end) == (0, 4)
    d3 = _only("ilo ilo ilo ilo").head[0]
    assert d3.depth == 3 and ast.to_surface(d3) == "ilo ilo ilo ilo"
    assert ast.shape(_only("ilo ilo ilo")) != ast.shape(d3)


# ----------------------------------------------------------- tan, not a vector
def _vector_tan_units(tree):
    """`tan` read as a unit inside phrases (outside META), counted from the tree."""
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Phrase):
            parts = list(node.head) + [x for g in node.groups for x in (g.left, g.right)]
            n += sum(1 for u in parts if isinstance(u, ast.Unit) and u.token == "tan")
    return n


@pytest.mark.parametrize("case", NON_INVALID, ids=[c["id"] for c in NON_INVALID])
def test_vector_tan_count_of_tree_equals_the_skeleton_rule(case):
    res = parse(case["surface"])
    for a, sk in zip(res.alternatives, res.skeletons):
        assert _vector_tan_units(a) == _vector_tans(sk)


def test_structural_tan_is_not_flattened_to_a_lexical_vector():
    # tan after `li` and after a head: structure, so no `tan` Unit in any phrase
    for cid in ("t07", "t08", "t09", "t11", "t12", "t13", "t15", "b04", "b16"):
        for a in parse(_case(cid)["surface"]).alternatives:
            assert _vector_tan_units(a) == 0, cid
    t07 = _only("jan li tan ma")
    pred = t07.predicates[0]
    assert pred.head is None and pred.objects is None
    assert [s.head[0].token for s in pred.sources.items] == ["ma"]
    ctx = _only("tan ni la jan li pali")
    assert isinstance(ctx, ast.Context) and ctx.source is True
    assert ctx.context.head[0].token == "ni"
    b4 = _only("sona ni li kama tan kute").predicates[0]
    assert [h.token for h in b4.head.head] == ["kama"] and b4.sources is not None
    # the vector reading stays exactly where the oracle says it does
    assert _vector_tan_units(_only("jan tan li pali")) == 1          # t01 {jan tan}
    assert _vector_tan_units(_only("jan li tan ma e ijo")) == 1      # t10 {tan ma}
    # a tan-initial context and a tan after the head never differ only by label
    assert ast.shape(_only("tan ma la ilo li awen")) != ast.shape(_only("jan tan la ilo li awen"))


# ------------------------------------------- syntax stays separate from the rest
def test_parse_api_has_no_binding_or_truth_fields():
    forbidden = re.compile(r"unresolved|truth|speech|resolution|bound|binding", re.I)
    for f in dataclasses.fields(openpona.ParseResult):
        assert not forbidden.search(f.name), f.name
    for cls in ast.NODE_TYPES.values():
        for f in dataclasses.fields(cls):
            assert not forbidden.search(f.name), (cls.__name__, f.name)
    res = parse("jan li pali")
    text = json.dumps(res.to_json())
    assert not forbidden.search(text.replace("RESOURCE_EXHAUSTED", ""))
    assert set(res.to_json()) == {"api_version", "status", "alternatives"}
    # a name with nothing to bind is still a syntax success, never a truth value
    assert parse("seme li tan e ni").status == "RESOLVED"


def test_invalid_and_exhausted_have_no_alternatives():
    inv = parse("jan li pali anu jan li awen")
    assert inv.status == "INVALID" and inv.alternatives == ()
    big = parse(" ".join(["ilo"] * 300))
    assert big.status == "RESOURCE_EXHAUSTED" and big.alternatives == ()
    for r in (inv, big):
        assert r.to_json() == {"api_version": PARSER_API_VERSION, "status": r.status,
                               "alternatives": []}


# --------------------------------------------------------------- versioning
def test_api_version_is_its_own_identifier():
    assert PARSER_API_VERSION == "1.0.0" == openpona.PARSER_API_VERSION
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    pkg = re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1)
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert pkg == "0.2.0" and manifest["token_version"] == "anu 1.1"
    assert PARSER_API_VERSION not in (pkg, manifest["token_version"])
    assert parse("jan li pali").api_version == PARSER_API_VERSION
    assert parse("").api_version == PARSER_API_VERSION  # also on INVALID


def test_api_docs_state_the_three_identifiers_separately():
    doc = (ROOT / "docs" / "parser-api.md").read_text(encoding="utf-8")
    assert "PARSER_API_VERSION" in doc and "1.0.0" in doc
    assert "anu 1.1" in doc and "0.2.0" in doc
    for word in ("skeletons", "UNRESOLVED", "PENDING AUTHOR REVIEW"):
        assert word in doc


# ------------------------------------------------------------------- CLI
def _cli(*args):
    return subprocess.run([sys.executable, "-m", "openpona", *args], cwd=ROOT,
                          capture_output=True, text=True, timeout=60)


def test_cli_json_for_the_ambiguous_baseline_case():
    amb = next(c for c in CASES if c["expect_status"] == "AMBIGUOUS")
    p = _cli("parse", "--json", amb["surface"])
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert set(out) == {"api_version", "status", "alternatives"}
    assert out["api_version"] == PARSER_API_VERSION and out["status"] == "AMBIGUOUS"
    assert len(out["alternatives"]) == len(amb["expect_skeletons"]) >= 2
    trees = [ast.from_json(d) for d in out["alternatives"]]
    assert {ast.to_skeleton(t) for t in trees} == set(amb["expect_skeletons"])
    assert out == json.loads(json.dumps(parse(amb["surface"]).to_json()))


def test_cli_json_exit_codes_and_empty_alternatives():
    inv = _cli("parse", "--json", "jan e")
    assert inv.returncode == 1 and json.loads(inv.stdout)["alternatives"] == []
    assert "error:" in inv.stderr
    big = _cli("parse", "--json", " ".join(["ilo"] * 300))
    assert big.returncode == 3 and json.loads(big.stdout)["status"] == "RESOURCE_EXHAUSTED"
    ok = _cli("parse", "--json", "jan li pali")
    assert ok.returncode == 0 and len(json.loads(ok.stdout)["alternatives"]) == 1
    plain = _cli("parse", "jan li pali")  # human output unchanged
    assert plain.stdout.splitlines() == ["RESOLVED", "({jan} li {pali})"]


# ------------------------------------------------- schema / strictness of JSON
def test_schema_file_matches_the_node_types():
    schema = json.loads((ROOT / "schema" / "ast.schema.json").read_text(encoding="utf-8"))
    defs = schema["$defs"]
    for name, cls in ast.NODE_TYPES.items():
        spec = ast._SPEC[cls]
        assert name in defs, name
        assert set(defs[name]["required"]) == set(spec) | {"type"}, name
        assert set(defs[name]["properties"]) == set(spec) | {"type"}, name
        assert defs[name]["additionalProperties"] is False
        assert defs[name]["properties"]["type"] == {"const": name}
    assert set(schema["required"]) == {"api_version", "status", "alternatives"}
    assert schema["additionalProperties"] is False


def _good():
    return ast.to_json(_only("jan li pali e ijo tan ma"))


def _break(path, fn):
    d = _good()
    node = d
    for k in path[:-1]:
        node = node[k]
    fn(node, path[-1])
    return d


BREAKERS = {
    "unknown type": lambda: {**_good(), "type": "sentence"},
    "extra key": lambda: {**_good(), "truth_status": "observed"},
    "missing key": lambda: {k: v for k, v in _good().items() if k != "subject"},
    "bad span order": lambda: _break(["span"], lambda n, k: n.__setitem__(k, {"start": 5, "end": 5})),
    "span outside parent": lambda: _break(["subject", "span"], lambda n, k: n.__setitem__(k, {"start": 0, "end": 99})),
    "head of three units": lambda: _break(["subject", "head"], lambda n, k: n.__setitem__(
        k, n[k] * 3)),
    "empty predicates": lambda: _break(["predicates"], lambda n, k: n.__setitem__(k, [])),
    "tuple as string": lambda: _break(["predicates"], lambda n, k: n.__setitem__(k, "li")),
    "particle as unit": lambda: _break(["subject", "head", 0, "token"], lambda n, k: n.__setitem__(k, "li")),
    "non-dict": lambda: ["jan"],
}


@pytest.mark.parametrize("name", sorted(BREAKERS))
def test_from_json_rejects_malformed_trees(name):
    with pytest.raises(ValueError):
        ast.from_json(BREAKERS[name]())


def test_nodes_are_immutable_and_hashable():
    a = _only("jan li pali")
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.span = ast.Span(0, 1)
    assert len({a, ast.from_json(ast.to_json(a))}) == 1
    with pytest.raises(ValueError):
        ast.Phrase((ast.Unit("jan", ast.Span(0, 1)),) * 3, (), ast.Span(0, 3))
    with pytest.raises(ValueError):
        ast.Predicate(None, None, None, ast.Span(0, 1))  # source predicate needs sources


def test_skeleton_reader_rejects_a_skeleton_that_does_not_match_the_tokens():
    with pytest.raises(ValueError):
        ast.from_skeleton("({jan} li {pali})", ["jan", "li", "awen"])
    with pytest.raises(ValueError):
        ast.from_skeleton("({jan} li {pali})", ["jan", "li", "pali", "pali"])
    with pytest.raises(ValueError):
        ast.from_skeleton("{jan pali ilo}")  # three units, no pi


# ---------------------------------------------------- scale and property tests
def test_long_statements_round_trip_without_deep_recursion():
    chain = "jan " + " ".join(["anu jan"] * 126)           # 253 tokens, right-nested anu
    res = parse(chain)
    assert res.status == "RESOLVED" and len(res.tokens) == 253
    a = res.alternatives[0]
    assert ast.from_json(json.loads(json.dumps(ast.to_json(a)))) == a
    assert ast.to_surface(a) == chain
    many = parse("jan li " + " li ".join(["pali"] * 120))
    assert ast.from_json(ast.to_json(many.alternatives[0])) == many.alternatives[0]


def _check_result(surface):
    res = parse(surface)
    assert len(res.alternatives) == len(res.skeletons)
    assert [ast.to_skeleton(a) for a in res.alternatives] == res.skeletons
    for a in res.alternatives:
        assert ast.from_json(json.loads(json.dumps(ast.to_json(a)))) == a
        assert ast.to_surface(a) == " ".join(res.tokens)
        assert a in parse(ast.to_surface(a)).alternatives
    return res


def test_exhaustive_short_sequences():
    seen = set()
    for alphabet, top in ((["jan", "ilo", "tan", "li", "e", "pi", "anu", "la"], 4),
                          (["jan", "pali", "tan", "li", "e"], 6)):
        for n in range(1, top + 1):
            for seq in itertools.product(alphabet, repeat=n):
                seen.add(_check_result(" ".join(seq)).status)
    assert {"RESOLVED", "AMBIGUOUS", "INVALID"} <= seen


@settings(max_examples=250, deadline=None)
@given(st.lists(st.sampled_from(["jan", "ilo", "tan", "li", "e", "pi", "anu", "la", "ala"]),
                min_size=5, max_size=11))
def test_random_sequences_keep_every_parse_and_round_trip(seq):
    _check_result(" ".join(seq))
