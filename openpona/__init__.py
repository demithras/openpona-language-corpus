"""OpenPona reference parser (RESEARCH grammar, see research/parser_probe/)."""
import csv
from importlib.resources import files

_TOKENS_CSV = files("openpona") / "tokens.csv"


def _load():
    with _TOKENS_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    tokens = [r["token"] for r in rows]
    semantic = [r["token"] for r in rows if r["kind"] == "semantic"]
    structural = [r["token"] for r in rows if r["kind"] == "structural"]
    return tokens, semantic, structural


TOKENS, SEMANTIC, STRUCTURAL = _load()

from .parser import ParseResult, parse  # noqa: E402

__all__ = ["parse", "ParseResult", "TOKENS", "SEMANTIC", "STRUCTURAL"]
