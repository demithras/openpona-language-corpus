"""Run every conformance case (the hand-written oracle) against the reference parser."""
import json
from pathlib import Path

import pytest

from openpona import parse

CONF = Path(__file__).resolve().parent.parent / "conformance"


def _cases():
    out = []
    for path in sorted(CONF.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


CASES = _cases()


def test_oracle_is_loaded():
    assert len(CASES) >= 46


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_conformance_case(case):
    res = parse(case["surface"], case.get("mode", "dual"))
    assert res.status == case["expect_status"]
    if case["expect_status"] != "INVALID":
        assert set(res.skeletons) == set(case["expect_skeletons"])
    else:
        assert res.skeletons == []
