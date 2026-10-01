"""Packaging: the token table ships inside the package."""
from pathlib import Path

import openpona
from openpona import TOKENS

ROOT = Path(__file__).resolve().parent.parent


def test_packaged_tokens_match_canonical_copy():
    assert (ROOT / "openpona" / "tokens.csv").read_bytes() == (ROOT / "data" / "tokens.csv").read_bytes()


def test_loader_stays_inside_the_package():
    assert len(TOKENS) == 42
    src = Path(openpona.__file__).read_text(encoding="utf-8")
    assert "parent.parent" not in src
