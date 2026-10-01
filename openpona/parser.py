"""normalize -> tokenize -> META fold -> structural parse -> skeleton rendering."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from itertools import product
from pathlib import Path
import re
import sys

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from . import TOKENS

_HERE = Path(__file__).resolve().parent
PARTICLES = ("li", "la", "e", "pi", "anu")  # structural only, never units
MAX_TOKENS = 256
_CASE_MSG = ("case: tokens are lowercase; a capitalised word is a name, "
             "and names never appear in the surface (SPEC 8.2)")


@dataclass
class ParseResult:
    status: str
    skeletons: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)


@lru_cache(maxsize=None)
def _lark() -> Lark:
    text = (_HERE / "grammar.lark").read_text(encoding="utf-8")
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
            if any(t in PARTICLES for t in p):
                continue  # META candidates are units: semantic tokens or tan only
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
    if data == "statement":
        return c[0] if len(c) == 1 else f"({c[0]} la {c[2]})"
    if data == "clause":
        return c[0] if len(c) == 1 else f"({c[0]}{c[1]})"
    if data == "lis":  # LI predicate [lis]
        return f" li {c[1]}" + (c[2] if len(c) > 2 else "")
    if data == "predicate":
        return c[0] + (c[1] if len(c) > 1 else "")
    if data == "parts":
        return c[0] + (c[1] if len(c) > 1 else "")
    if data == "part":  # E|TAN expression
        return f" {c[0]} {c[1]}"
    if data == "expression":
        return c[0] if len(c) == 1 else f"({c[0]} anu {c[2]})"
    if data == "phrase":
        return "{" + c[0] + (c[1] if len(c) > 1 else "") + "}"
    if data == "groups":
        return c[0] + (c[1] if len(c) > 1 else "")
    if data == "group":
        return f" pi {c[1]} {c[2]}"
    if data == "head":
        return " ".join(c)
    raise ValueError(f"unexpected rule {data}")


def _skeletons(text: str) -> set[str]:
    try:
        tree = _lark().parse(text)
    except LarkError:
        return set()
    if not isinstance(tree, Tree):
        return set()
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 20000))
    try:
        return _alts(tree, {})
    finally:
        sys.setrecursionlimit(old)


# ------------------------------------------------------------- diagnostics
def _diagnose(toks: list[str]) -> list[str]:
    """Located, rule-named hints for a token list with no structural parse."""
    out: list[str] = []

    def at(i: int) -> str:
        return f"(token {i + 1} '{toks[i]}')"

    n = len(toks)
    if toks[0] in PARTICLES:
        out.append(f"particle-first: a particle needs an expression before it {at(0)}")
    last = toks[-1]
    if last in PARTICLES or (last == "tan" and n > 1 and "li" in toks[:-1]):
        out.append(f"particle-last: a particle needs an expression after it {at(n - 1)}")
    for i in range(n - 1):
        if toks[i] in PARTICLES and toks[i + 1] in PARTICLES:
            out.append("particle-run: particles never repeat; META applies to "
                       f"semantic units only {at(i + 1)}")
    las = [i for i, t in enumerate(toks) if t == "la"]
    if len(las) > 1:
        out.append("la-count: one context (la) per statement; a choice between "
                   f"statements is two la statements on two lines {at(las[1])}")
    for i, t in enumerate(toks):
        if t != "pi":
            continue
        j = i + 1
        while j < n and toks[j] not in PARTICLES:
            j += 1
        k = j - i - 1
        if k != 2 and k != 0:
            out.append(f"pi-arity: pi introduces a group of exactly two units, found {k} {at(i)}")
    seg: list[int] = []
    segments: list[list[int]] = []
    for i, t in enumerate(toks):
        if t in ("li", "la", "e", "anu"):
            segments.append(seg)
            seg = []
        else:
            seg.append(i)
    segments.append(seg)
    for sg in segments:
        words = [toks[i] for i in sg]
        if len(sg) >= 3 and "pi" not in words:
            out.append("units-without-pi: a phrase has a head of 1-2 units; three or "
                       f"more units need pi (SPEC 5.3) {at(sg[2])}")
        if len(sg) == 3 and words[1] == "pi" and words[0] not in PARTICLES and words[2] not in PARTICLES:
            out.append("pi-after-one-unit: two-unit concepts take no pi; write "
                       f"`{words[0]} {words[2]}` {at(sg[1])}")
    return out


# --------------------------------------------------------------------- API
def parse(text: str) -> ParseResult:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) > 1:
        return ParseResult("INVALID", [], ["line: one statement per line"], [])
    line = lines[0] if lines else ""
    toks = [t for t in re.split(r"[ \t]+", line.strip(" \t")) if t]
    if not toks:
        return ParseResult("INVALID", [], ["empty input"], [])
    if any(ch.isupper() for ch in line):
        return ParseResult("INVALID", [], [_CASE_MSG], toks)
    if len(toks) > MAX_TOKENS:
        return ParseResult("INVALID", [], [
            f"length: reference parser accepts at most {MAX_TOKENS} tokens per statement"], toks)
    known = set(TOKENS)
    if any(t not in known for t in toks):
        errs = [f"unknown-token: {t!r} is not one of the 42 tokens (token {i + 1} '{t}')"
                for i, t in enumerate(toks) if t not in known]
        return ParseResult("INVALID", [], errs, toks)
    skels: set[str] = set()
    for cand in fold_candidates(toks):
        skels |= _skeletons(cand)
    out = sorted(skels)
    if not out:
        errs = _diagnose(toks) or ["no structural parse"]
        return ParseResult("INVALID", [], errs, toks)
    return ParseResult("RESOLVED" if len(out) == 1 else "AMBIGUOUS", out, [], toks)
