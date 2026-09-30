"""OpenPona reference parser (RESEARCH grammar, see research/parser_probe/)."""
import csv
from pathlib import Path

_TOKENS_CSV = Path(__file__).resolve().parent.parent / "data" / "tokens.csv"


def _load():
    with open(_TOKENS_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    tokens = [r["token"] for r in rows]
    semantic = [r["token"] for r in rows if r["kind"] == "semantic"]
    structural = [r["token"] for r in rows if r["kind"] == "structural"]
    return tokens, semantic, structural


TOKENS, SEMANTIC, STRUCTURAL = _load()

from .parser import ParseResult, parse  # noqa: E402

__all__ = ["parse", "ParseResult", "TOKENS", "SEMANTIC", "STRUCTURAL"]
