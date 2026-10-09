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


# ---- Lift axis names (author decision 2026-10-09) ----------------------------------------

import json
import re

LIFT = ROOT / "research" / "lift" / "coordinates.v0.1.json"


def _canon_table():
    lines = (ROOT / "canon" / "03_matrix.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("| Row |"))
    table = []
    for l in lines[start:]:
        if not l.startswith("|"):
            break
        table.append([c.strip() for c in l.strip().strip("|").split("|")])
    return table[0], table[2:]  # header, body (row 1 is the |---| separator)


def test_matrix_table_lift_labels_equal_coordinates_json():
    profile = json.loads(LIFT.read_text(encoding="utf-8"))
    header, body = _canon_table()
    assert header[:3] == ["Row", "Lift (R)", "Narrative role"]
    row_labels = []
    for cells in body:
        m = re.fullmatch(r"(\w+) \((R\d)\)", cells[1])
        assert m, cells[1]
        row_labels.append({"id": m.group(2), "label": m.group(1)})
    col_labels = []
    for h in header[3:]:
        m = re.fullmatch(r"(\w+) · (\w+) \((C\d)\)", h)
        assert m, h
        col_labels.append({"id": m.group(3), "label": m.group(2)})
    assert row_labels == profile["row_archetypes"]
    assert col_labels == profile["column_operations"]
    assert [r["id"] for r in row_labels] == [f"R{i}" for i in range(1, 7)]
    assert [c["id"] for c in col_labels] == [f"C{i}" for i in range(1, 8)]


def test_matrix_table_tokens_equal_data_matrix_csv():
    header, body = _canon_table()
    table_tokens = [t.strip("`") for cells in body for t in cells[3:]]
    assert len(table_tokens) == 42
    assert table_tokens == [r["token"] for r in rows()]
    # placement, not only inventory: each token sits at the (row, column) data/matrix.csv gives it
    for r in rows():
        cells = body[int(r["row"]) - 1]
        assert cells[2 + int(r["column"])].strip("`") == r["token"]
        assert header[2 + int(r["column"])].startswith(r["column_role"] + " · ")


def test_lift_profile_cells_equal_data_matrix_csv():
    profile = json.loads(LIFT.read_text(encoding="utf-8"))
    assert [c["token"] for c in profile["cells"]] == [r["token"] for r in rows()]


def test_axis_names_are_not_tokens():
    names = {c["label"].lower() for c in json.loads(LIFT.read_text(encoding="utf-8"))["row_archetypes"]}
    names |= {c["label"].lower() for c in json.loads(LIFT.read_text(encoding="utf-8"))["column_operations"]}
    assert not names & {r["token"] for r in rows()}
