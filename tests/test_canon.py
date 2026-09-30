import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANON = [
    "open", "lon", "tawa", "wile", "pali", "pilin", "li",
    "seme", "ma", "lukin", "sona", "ni", "kute", "la",
    "nasin", "sijelo", "ilo", "lawa", "awen", "ken", "e",
    "jan", "ante", "kama", "sama", "ijo", "selo", "tan",
    "sitelen", "linja", "pana", "toki", "tenpo", "pini", "pi",
    "sike", "ale", "weka", "ala", "kulupu", "pona", "anu",
]
STRUCTURAL = ["li", "la", "e", "tan", "pi", "anu"]


def rows():
    with (ROOT / "data" / "matrix.csv").open() as f:
        return list(csv.DictReader(f))


def test_exactly_42_unique_tokens():
    tokens = [r["token"] for r in rows()]
    assert tokens == CANON
    assert len(tokens) == 42
    assert len(set(tokens)) == 42


def test_36_plus_6_split():
    data = rows()
    assert sum(r["kind"] == "semantic" for r in data) == 36
    assert sum(r["kind"] == "structural" for r in data) == 6
    assert [r["token"] for r in data if r["kind"] == "structural"] == STRUCTURAL


def test_structure_column_is_structural_set():
    structure = [r["token"] for r in rows() if r["column"] == "7"]
    assert structure == STRUCTURAL


def test_sprint5_anu_1_1_order():
    sprint5 = [r["token"] for r in rows() if r["row"] == "5"]
    assert sprint5 == ["sitelen", "linja", "pana", "toki", "tenpo", "pini", "pi"]


def test_explicit_noncanonical_tokens_absent():
    tokens = {r["token"] for r in rows()}
    assert not ({"mute", "kalama", "nimi"} & tokens)
