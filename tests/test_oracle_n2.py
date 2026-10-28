"""N2 (phrase length by position) against the independent oracle alone."""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.oracle import recognizer as oracle  # noqa: E402

I = "INVALID"
R = "RESOLVED"
EXAMPLES = [
    ("ilo li awen", I, None),
    ("ilo pali li awen", R, "({ilo pali} li {awen})"),
    ("pali", R, "{pali}"),
    ("ilo pali", R, "{ilo pali}"),
    ("jan pali li pali e ilo", I, None),
    ("jan pali li pali e ilo sitelen", R, "({jan pali} li {pali} e {ilo sitelen})"),
    ("jan pali li pali e ilo sitelen anu ijo", I, None),
    ("ilo pali li pona anu seme", R, "({ilo pali} li ({pona} anu {seme}))"),
    ("ilo pali li pona ala", R, "({ilo pali} li {pona ala})"),
    ("jan ni li lukin e ilo ilo", R, "({jan ni} li {lukin} e {D1(ilo)})"),
    ("jan pali li tan ma", I, None),
    ("jan pali li tan ma pali", R, "({jan pali} li tan {ma pali})"),
    ("tan ni la jan pali li pali", I, None),
    ("tan toki ni la jan pali li pali", R, "(tan {toki ni} la ({jan pali} li {pali}))"),
    ("ma la ilo pali li awen", I, None),
    ("ma pali la ilo pali li awen", R, "({ma pali} la ({ilo pali} li {awen}))"),
    ("jan pali li kama tan ma", I, None),
    ("ilo ilo li awen", R, "({D1(ilo)} li {awen})"),
    ("jan pali li lukin lukin", R, "({jan pali} li {D1(lukin)})"),
]


@pytest.mark.parametrize("surface,status,skeleton", EXAMPLES, ids=[e[0] for e in EXAMPLES])
def test_worked_example(surface, status, skeleton):
    res = oracle.recognize(surface)
    assert res.status == status, (surface, res.status, res.skeletons)
    if skeleton is not None:
        assert res.skeletons == [skeleton]


SAMPLE = "ilo pali jan ma li e tan anu".split()


def test_no_resolved_reading_has_one_token_nominal_phrase():
    checked = resolved = 0
    for n in range(1, 5):
        for toks in itertools.product(SAMPLE, repeat=n):
            res = oracle.recognize(" ".join(toks))
            checked += 1
            if res.status == "RESOLVED":
                resolved += 1
                assert oracle.n2_valid(res.trees[0]), toks
    assert checked == sum(8 ** n for n in range(1, 5))
    assert resolved > 0
