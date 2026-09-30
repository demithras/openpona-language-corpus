"""normalize -> tokenize -> META fold -> structural parse -> skeleton rendering."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from itertools import product
from pathlib import Path

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from . import TOKENS

_HERE = Path(__file__).resolve().parent
_GRAMMARS = {"dual": "grammar.lark", "strict": "grammar_strict.lark"}


@dataclass
class ParseResult:
    status: str
    skeletons: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)


@lru_cache(maxsize=None)
def _lark(mode: str) -> Lark:
    if mode not in _GRAMMARS:
        raise ValueError(f"unknown mode {mode!r}; expected 'strict' or 'dual'")
    text = (_HERE / _GRAMMARS[mode]).read_text(encoding="utf-8")
    return Lark(text, parser="earley", lexer="dynamic", ambiguity="explicit",
                keep_all_tokens=True, start="start")


# ---------------------------------------------------------------- META fold
def _find_runs(toks: list[str]) -> list[tuple[int, int, int, tuple[str, ...]]]:
    """Maximal runs of k>=2 copies of a 1- or 2-token unit: (start, end, k, P)."""
    runs = []
    n = len(toks)
    for size in (1, 2):
        for i in range(n - size + 1):
            p = tuple(toks[i:i + size])
            if size == 2 and p[0] == p[1]:
                continue  # itself a repetition of a shorter unit
            if i - size >= 0 and tuple(toks[i - size:i]) == p:
                continue  # extendable to the left: not the run start
            k = 0
            while tuple(toks[i + k * size:i + (k + 1) * size]) == p:
                k += 1
            if k >= 2:
                runs.append((i, i + k * size, k, p))
    return runs


def _maximal_sets(runs):
    """All maximal sets of pairwise non-overlapping runs."""
    def overlap(a, b):
        return a[0] < b[1] and b[0] < a[1]

    found = []

    def rec(idx, chosen):
        if idx == len(runs):
            if all(r in chosen or any(overlap(r, c) for c in chosen) for r in runs):
                found.append(list(chosen))
            return
        r = runs[idx]
        if not any(overlap(r, c) for c in chosen):
            chosen.append(r)
            rec(idx + 1, chosen)
            chosen.pop()
        rec(idx + 1, chosen)

    rec(0, [])
    return found


def fold_candidates(toks: list[str]) -> list[str]:
    """Folded token sequences (space-joined text), one per maximal run set."""
    runs = _find_runs(toks)
    if not runs:
        return [" ".join(toks)]
    out = []
    for chosen in _maximal_sets(runs):
        by_start = {r[0]: r for r in chosen}
        parts, i = [], 0
        while i < len(toks):
            if i in by_start:
                s, e, k, p = by_start[i]
                parts.append(f"D{k - 1}({' '.join(p)})")
                i = e
            else:
                parts.append(toks[i])
                i += 1
        text = " ".join(parts)
        if text not in out:
            out.append(text)
    return out


# ------------------------------------------------------- skeleton rendering
def _alts(node, memo) -> set[str]:
    if isinstance(node, Token):
        return {str(node)}
    key = id(node)
    if key in memo:
        return memo[key]
    if node.data == "_ambig":
        res: set[str] = set()
        for ch in node.children:
            res |= _alts(ch, memo)
    else:
        res = set()
        choices = [sorted(_alts(c, memo)) for c in node.children]
        for combo in product(*choices):
            res.add(_fmt(node.data, combo))
    memo[key] = res
    return res


def _fmt(data: str, c) -> str:
    if data in ("start", "unit"):
        return c[0]
    if data == "sentence":
        return c[0] if len(c) == 1 else f"({c[0]} la {c[2]})"
    if data == "clause":
        return c[0] if len(c) == 1 else f"({c[0]} li {c[2]})"
    if data == "predicate":
        return " ".join(c)
    if data in ("object", "source"):
        return f"{c[0]} {c[1]}"
    if data == "expression":
        return c[0] if len(c) == 1 else f"({c[0]} anu {c[2]})"
    if data == "phrase":
        return "{" + " ".join(c) + "}"
    raise ValueError(f"unexpected rule {data}")


def _skeletons(text: str, mode: str) -> set[str]:
    try:
        tree = _lark(mode).parse(text)
    except LarkError:
        return set()
    if not isinstance(tree, Tree):
        return set()
    return _alts(tree, {})


# --------------------------------------------------------------------- API
def parse(text: str, mode: str = "dual") -> ParseResult:
    if mode not in _GRAMMARS:
        raise ValueError(f"unknown mode {mode!r}; expected 'strict' or 'dual'")
    toks = text.lower().strip().split()
    if not toks:
        return ParseResult("INVALID", [], ["empty input"], [])
    known = set(TOKENS)
    bad = [t for t in toks if t not in known]
    if bad:
        errs = [f"unknown token: {t!r}" for t in dict.fromkeys(bad)]
        return ParseResult("INVALID", [], errs, toks)
    skels: set[str] = set()
    for cand in fold_candidates(toks):
        skels |= _skeletons(cand, mode)
    out = sorted(skels)
    if not out:
        return ParseResult("INVALID", [], ["no structural parse"], toks)
    return ParseResult("RESOLVED" if len(out) == 1 else "AMBIGUOUS", out, [], toks)
