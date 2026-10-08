"""OpenPona reference parser (RESEARCH grammar, see research/parser_probe/)."""
import csv
from importlib.resources import files

_TOKENS_CSV = files("openpona") / "tokens.csv"

# Parse-API compatibility identifier (docs/parser-api.md).  Deliberately separate
# from the token inventory ("anu 1.1") and from the package version (0.2.0):
# bump it only when the shape of ParseResult / the AST JSON changes.
PARSER_API_VERSION = "1.0.0"


def _load():
    with _TOKENS_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    tokens = [r["token"] for r in rows]
    semantic = [r["token"] for r in rows if r["kind"] == "semantic"]
    structural = [r["token"] for r in rows if r["kind"] == "structural"]
    return tokens, semantic, structural


TOKENS, SEMANTIC, STRUCTURAL = _load()

from .parser import (  # noqa: E402
    RESOURCE_EXHAUSTED, Budget, ParseResult, ParseStats, parse,
)
from . import ast  # noqa: E402,F401  (typed trees: openpona.ast)

__all__ = ["parse", "ParseResult", "Budget", "ParseStats", "RESOURCE_EXHAUSTED",
           "PARSER_API_VERSION", "TOKENS", "SEMANTIC", "STRUCTURAL", "ast"]
