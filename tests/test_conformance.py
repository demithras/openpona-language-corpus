"""Run every conformance case (the hand-written oracle) against the reference parser.

A record may carry `expect_asts` (span-free N2 JSON, see docs/parser-api.md): the set of
trees must then match as well as the skeletons.  The only way a record is skipped is
`"triage": "open"` (a recorded, unresolved disagreement between the spec-derived
expectation and the parser); it is skipped WITH its reason, never silently, and
tests/test_conformance_integrity.py checks that every such record is also listed in the
oracle disagreement triage.  Expectations are never edited to match the parser.
"""
import json
from pathlib import Path

import pytest

from openpona import ast, parse

CONF = Path(__file__).resolve().parent.parent / "conformance"


def _cases():
    out = []
    for path in sorted(CONF.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


CASES = _cases()


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_oracle_is_loaded():
    assert len(CASES) >= 63


def test_triage_field_only_takes_the_value_open():
    odd = {c["id"]: c["triage"] for c in CASES if "triage" in c and c["triage"] != "open"}
    assert not odd, odd


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_conformance_case(case):
    if case.get("triage") == "open":
        pytest.skip("triage open: " + case.get("triage_note", "(no triage_note)"))
    res = parse(case["surface"])
    assert res.status == case["expect_status"]
    if case["expect_status"] != "INVALID":
        assert set(res.skeletons) == set(case["expect_skeletons"])
        if "expect_asts" in case:
            got = sorted(_canon(ast.shape(a)) for a in res.alternatives)
            want = sorted(_canon(a) for a in case["expect_asts"])
            assert got == want
    else:
        assert res.skeletons == []
