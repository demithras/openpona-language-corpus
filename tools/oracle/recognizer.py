"""Independent structural recognizer for OpenPona statements (TP-04 oracle).

Written ONLY from SPEC.md sections 5-7 and canon/ (04 grammar, 07 META, 11
Toki Pona compatibility).  It shares no code with the reference parser: it does not
read the Lark grammar and imports nothing from the `openpona` package nor from
any parsing library.  It enumerates every structural reading by plain span
recursion with memoisation and then applies the three priority rules of
SPEC invariant 18 as explicit set filters.

Reading of the spec (each line names where it comes from):

* Tokens: the 42 of data/matrix.csv; surface is tokens separated by spaces/tabs
  (SPEC 8.2, 11, 17).  Anything else is INVALID.
* Line edges (SPEC 17, author decision 2026-10-09): spaces/tabs before and after
  the statement are ignored, and so is exactly one final LF or CR LF.  Any other
  character around or inside the statement (a second newline, a leading newline,
  lone CR, U+2028 ...) is not a token character, so the line is INVALID.
* Units (SPEC 5, 7): a vector token (36 semantic + `tan`), or a META unit: n >= 2
  consecutive copies of a primitive P (one vector token, or two DIFFERENT vector
  tokens), covering the whole run of copies (SPEC 7, canon/04 5: "n consecutive
  copies"; no separate form for nested derivative, so P is never itself a run).
* Phrase (SPEC 5.3): head of one or two units, then any number of `pi A B`.
* Expression (SPEC 6): phrase | phrase `anu` expression.
* Predicate (SPEC 6): expression {`e` expression} {`tan` expression}
  | `tan` expression {`tan` expression}  (source predicate; no objects).
* Clause: expression {`li` predicate}; a predicate containing `anu` is the last
  one (SPEC 6).
* Statement: clause | clause `la` clause | `tan` expression `la` clause.
* Priority (SPEC 2.18, canon/04 5): META -> structure -> vector.  Operational
  reading used here (an interpretation, listed in the disagreement report):
    1. among all readings drop one whose set of folded token positions is a
       strict subset of another reading's ("META has priority");
    2. among the rest drop one whose set of structural `tan` positions is a
       strict subset of another reading's ("where a structural reading exists
       it wins").
  Readings that stay incomparable are all kept, which is what AMBIGUOUS means.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def _load_inventory():
    with (_ROOT / "data" / "matrix.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    semantic = [r["token"] for r in rows if r["kind"] == "semantic"]
    structural = [r["token"] for r in rows if r["kind"] == "structural"]
    return semantic, structural


SEMANTIC, STRUCTURAL = _load_inventory()
INVENTORY = frozenset(SEMANTIC) | frozenset(STRUCTURAL)
VECTORS = frozenset(SEMANTIC) | {"tan"}
assert len(INVENTORY) == 42


# ------------------------------------------------------------------ tokenising
_SPLIT = re.compile(r"[ \t]+")


def tokenize(text: str):
    """Tokens of `text`, or None when the surface is not made of the 42 tokens
    separated by spaces/tabs (empty, other whitespace, punctuation, capitals ...).
    One final LF or CR LF is dropped first (SPEC 17, decision 2026-10-09)."""
    if text.endswith("\r\n"):
        text = text[:-2]
    elif text.endswith("\n"):
        text = text[:-1]
    stripped = text.strip(" \t")
    if not stripped:
        return None
    toks = _SPLIT.split(stripped)
    if any(t not in INVENTORY for t in toks):
        return None
    return toks


# ---------------------------------------------------------------- tree encoding
# unit   ('U', token, i)             meta ('M', depth, (tokens), i, j)
# phrase ('P', (units), ((u,u),...)) alt  ('A', phrase, expr)
# pred   ('R', head|None, (objects), ((tan_index, expr), ...))
# clause expr | ('C', subject, (preds))
# stmt   clause | ('X', ctx_clause, body_clause) | ('S', tan_index, expr, body_clause)


class _Rec:
    def __init__(self, toks):
        self.t = toks
        self.n = len(toks)
        self.unit = lru_cache(None)(self._unit)
        self.head = lru_cache(None)(self._head)
        self.groups = lru_cache(None)(self._groups)
        self.phrase = lru_cache(None)(self._phrase)
        self.expr = lru_cache(None)(self._expr)
        self.objs = lru_cache(None)(self._objs)
        self.srcs = lru_cache(None)(self._srcs)
        self.pred = lru_cache(None)(self._pred)
        self.lis = lru_cache(None)(self._lis)
        self.clause = lru_cache(None)(self._clause)

    # unit(i, j): readings of tokens [i, j) as one unit
    def _unit(self, i, j):
        t = self.t
        out = set()
        if j == i + 1 and t[i] in VECTORS:
            out.add(("U", t[i], i))
        for p in (1, 2):
            width = j - i
            if width % p or width // p < 2:
                continue
            base = tuple(t[i:i + p])
            if any(x not in VECTORS for x in base):
                continue
            if p == 2 and base[0] == base[1]:
                continue
            if tuple(t[i:j]) != base * (width // p):
                continue
            if i - p >= 0 and tuple(t[i - p:i]) == base:
                continue
            if j + p <= self.n and tuple(t[j:j + p]) == base:
                continue
            out.add(("M", width // p - 1, base, i, j))
        return frozenset(out)

    def _head(self, i, j):
        out = {(u,) for u in self.unit(i, j)}
        for k in range(i + 1, j):
            for a in self.unit(i, k):
                for b in self.unit(k, j):
                    out.add((a, b))
        return frozenset(out)

    def _groups(self, k, j):
        if k == j:
            return frozenset({()})
        out = set()
        if self.t[k] == "pi":
            for m in range(k + 2, j):
                for a in self.unit(k + 1, m):
                    for q in range(m + 1, j + 1):
                        for b in self.unit(m, q):
                            for rest in self.groups(q, j):
                                out.add(((a, b),) + rest)
        return frozenset(out)

    def _phrase(self, i, j):
        out = set()
        for k in range(i + 1, j + 1):
            heads = self.head(i, k)
            if not heads:
                continue
            for gs in self.groups(k, j):
                for h in heads:
                    out.add(("P", h, gs))
        return frozenset(out)

    def _expr(self, i, j):
        out = set(self.phrase(i, j))
        for k in range(i + 1, j - 1):
            if self.t[k] == "anu":
                lefts = self.phrase(i, k)
                if not lefts:
                    continue
                for right in self.expr(k + 1, j):
                    for left in lefts:
                        out.add(("A", left, right))
        return frozenset(out)

    def _srcs(self, k, j):
        """`tan` expression {`tan` expression} covering [k, j) exactly; () when empty."""
        if k == j:
            return frozenset({()})
        out = set()
        if self.t[k] == "tan":
            for m in range(k + 2, j + 1):
                for ex in self.expr(k + 1, m):
                    for rest in self.srcs(m, j):
                        out.add(((k, ex),) + rest)
        return frozenset(out)

    def _objs(self, k, j):
        """{`e` expression} {`tan` expression} covering [k, j): (objects, sources)."""
        if k == j:
            return frozenset({((), ())})
        out = set()
        if self.t[k] == "e":
            for m in range(k + 2, j + 1):
                for ex in self.expr(k + 1, m):
                    for o, s in self.objs(m, j):
                        out.add(((ex,) + o, s))
        elif self.t[k] == "tan":
            for s in self.srcs(k, j):
                out.add(((), s))
        return frozenset(out)

    def _pred(self, i, j):
        out = set()
        for k in range(i + 1, j + 1):
            for head in self.expr(i, k):
                for o, s in self.objs(k, j):
                    out.add(("R", head, o, s))
        if self.t[i] == "tan":
            for s in self.srcs(i, j):
                out.add(("R", None, (), s))
        return frozenset(out)

    def _lis(self, k, j):
        """{`li` predicate} covering [k, j); a predicate holding `anu` is the last."""
        if k == j:
            return frozenset({()})
        out = set()
        if self.t[k] == "li":
            for m in range(k + 2, j + 1):
                for pr in self.pred(k + 1, m):
                    if _has_anu(pr):
                        if m == j:
                            out.add((pr,))
                    else:
                        for rest in self.lis(m, j):
                            out.add((pr,) + rest)
        return frozenset(out)

    def _clause(self, i, j):
        out = set(self.expr(i, j))
        for k in range(i + 1, j):
            for subj in self.expr(i, k):
                for ps in self.lis(k, j):
                    out.add(("C", subj, ps))
        return frozenset(out)

    def statement(self):
        n, t = self.n, self.t
        out = set(self.clause(0, n))
        for k in range(1, n - 1):
            if t[k] == "la":
                for a in self.clause(0, k):
                    for b in self.clause(k + 1, n):
                        out.add(("X", a, b))
        if t[0] == "tan":
            for k in range(2, n - 1):
                if t[k] == "la":
                    for ex in self.expr(1, k):
                        for b in self.clause(k + 1, n):
                            out.add(("S", 0, ex, b))
        return out


def _has_anu(node):
    if isinstance(node, tuple):
        if node and node[0] == "A":
            return True
        return any(_has_anu(x) for x in node)
    return False


def _walk(node, kind, acc):
    if isinstance(node, tuple):
        if node and node[0] == kind:
            acc.append(node)
        for x in node:
            _walk(x, kind, acc)


def folded_positions(tree) -> frozenset:
    ms = []
    _walk(tree, "M", ms)
    pos = set()
    for m in ms:
        pos.update(range(m[3], m[4]))
    return frozenset(pos)


def structural_tan_positions(tree) -> frozenset:
    pos = set()
    rs = []
    _walk(tree, "R", rs)
    for r in rs:
        for idx, _ex in r[3]:
            pos.add(idx)
    if isinstance(tree, tuple) and tree and tree[0] == "S":
        pos.add(tree[1])
    return frozenset(pos)


def _maximal(trees, key):
    keyed = [(t, key(t)) for t in trees]
    return [t for t, k in keyed if not any(k < k2 for _t, k2 in keyed)]


# ------------------------------------------------------------------- rendering
# Notation of conformance/README.md ("Skeleton notation"), re-implemented here.
def _r_unit(u):
    if u[0] == "U":
        return u[1]
    return "D%d(%s)" % (u[1], " ".join(u[2]))


def _r_phrase(p):
    s = " ".join(_r_unit(u) for u in p[1])
    for a, b in p[2]:
        s += " pi %s %s" % (_r_unit(a), _r_unit(b))
    return "{" + s + "}"


def _r_expr(e):
    if e[0] == "P":
        return _r_phrase(e)
    return "(%s anu %s)" % (_r_phrase(e[1]), _r_expr(e[2]))


def _r_pred(r):
    parts = []
    if r[1] is None:
        first, rest = r[3][0][1], r[3][1:]
        parts.append("tan " + _r_expr(first))
        srcs = rest
    else:
        parts.append(_r_expr(r[1]))
        srcs = r[3]
    for o in r[2]:
        parts.append("e " + _r_expr(o))
    for _i, ex in srcs:
        parts.append("tan " + _r_expr(ex))
    return " ".join(parts)


def _r_clause(c):
    if c[0] == "C":
        return "(" + " li ".join([_r_expr(c[1])] + [_r_pred(p) for p in c[2]]) + ")"
    return _r_expr(c)


def render(tree) -> str:
    if tree[0] == "X":
        return "(%s la %s)" % (_r_clause(tree[1]), _r_clause(tree[2]))
    if tree[0] == "S":
        return "(tan %s la %s)" % (_r_expr(tree[2]), _r_clause(tree[3]))
    return _r_clause(tree)


# ----------------------------------------------------------- N2 JSON (no spans)
def _j_unit(u):
    return {"token": u[1], "type": "unit"} if u[0] == "U" else {
        "depth": u[1], "type": "meta",
        "unit": [{"token": x, "type": "unit"} for x in u[2]]}


def _j_phrase(p):
    return {"groups": [{"left": _j_unit(a), "right": _j_unit(b), "type": "group"}
                       for a, b in p[2]],
            "head": [_j_unit(u) for u in p[1]], "type": "phrase"}


def _j_expr(e):
    if e[0] == "P":
        return _j_phrase(e)
    return {"left": _j_phrase(e[1]), "right": _j_expr(e[2]), "type": "alternative"}


def _j_pred(r):
    return {"head": None if r[1] is None else _j_expr(r[1]),
            "objects": {"items": [_j_expr(o) for o in r[2]], "type": "object_list"} if r[2] else None,
            "sources": {"items": [_j_expr(ex) for _i, ex in r[3]], "type": "source_list"} if r[3] else None,
            "type": "predicate"}


def _j_clause(c):
    if c[0] == "C":
        return {"predicates": [_j_pred(p) for p in c[2]], "subject": _j_expr(c[1]),
                "type": "predication"}
    return _j_expr(c)


def to_shape(tree) -> dict:
    """The tree as `type`-discriminated JSON without spans (docs/parser-api.md)."""
    if tree[0] == "X":
        return {"body": _j_clause(tree[2]), "context": _j_clause(tree[1]),
                "source": False, "type": "context"}
    if tree[0] == "S":
        return {"body": _j_clause(tree[3]), "context": _j_expr(tree[2]),
                "source": True, "type": "context"}
    return _j_clause(tree)


# ---------------------------------------------------------------------- result
@dataclass
class OracleResult:
    status: str                       # RESOLVED | AMBIGUOUS | INVALID
    skeletons: list = field(default_factory=list)
    trees: list = field(default_factory=list)
    reason: str = ""

    @property
    def shapes(self):
        return [to_shape(t) for t in self.trees]


def recognize(text: str) -> OracleResult:
    toks = tokenize(text)
    if toks is None:
        return OracleResult("INVALID", reason="not a space-separated sequence of the 42 tokens")
    rec = _Rec(toks)
    readings = list(rec.statement())
    if not readings:
        return OracleResult("INVALID", reason="no structural reading")
    readings = _maximal(readings, folded_positions)            # META first
    readings = _maximal(readings, structural_tan_positions)    # then structure over vector
    pairs = sorted((render(t), t) for t in readings)
    trees = [t for _s, t in pairs]
    return OracleResult("RESOLVED" if len(trees) == 1 else "AMBIGUOUS",
                        [s for s, _t in pairs], trees)
