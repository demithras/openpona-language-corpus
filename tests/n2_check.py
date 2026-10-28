"""Independent N2 checker on skeleton strings (rule N2, SPEC invariant 19).

Written from the skeleton notation of conformance/README.md and the position table of
SPEC 6.1 alone; it uses nothing from `openpona`.  `violations(skeleton)` lists
(position, phrase) for every phrase of ONE token in a nominal position.
"""
from __future__ import annotations

import re

_ITEM = re.compile(r"\{([^}]*)\}|([()])|([a-z]+)")
_META = re.compile(r"D(\d+)\(([^)]*)\)")


class Phrase:
    def __init__(self, text: str):
        self.text = text
        flat = _META.sub(lambda m: " ".join([m.group(2)] * (int(m.group(1)) + 1)), text)
        self.size = len(flat.split())

    def __repr__(self):
        return "{" + self.text + "}"


def _tokenize(skel: str) -> list:
    # a META unit D1(ilo pali) holds spaces and parentheses INSIDE a phrase, so protect it
    out, i = [], 0
    while i < len(skel):
        ch = skel[i]
        if ch == "{":
            j = skel.index("}", i)
            out.append(Phrase(skel[i + 1:j]))
            i = j + 1
        elif ch in "()":
            out.append(ch)
            i += 1
        elif ch == " ":
            i += 1
        else:
            m = re.match(r"[a-z]+", skel[i:])
            out.append(m.group(0))
            i += len(m.group(0))
    return out


def _tree(items: list, i: int = 0):
    """-> (node, next index); a node is a Phrase or a list of nodes and words."""
    tok = items[i]
    if isinstance(tok, Phrase):
        return tok, i + 1
    if tok == "(":
        kids, i = [], i + 1
        while items[i] != ")":
            kid, i = _tree(items, i)
            kids.append(kid)
        return kids, i + 1
    return tok, i + 1


def _is_alt(n) -> bool:
    return isinstance(n, list) and len(n) == 3 and n[1] == "anu"


def _leaves(n) -> list:
    if isinstance(n, Phrase):
        return [n]
    assert _is_alt(n), n
    return _leaves(n[0]) + _leaves(n[2])


def _nominal(n, pos: str, out: list) -> None:
    for ph in _leaves(n):
        if ph.size == 1:
            out.append((pos, ph.text))


def _clause(n, out: list, bare_pos: str) -> None:
    """A node that is a clause: a predication, or an expression with no `li`."""
    if isinstance(n, list) and "li" in n and not _is_alt(n):
        _nominal(n[0], "subject", out)
        segs, cur = [], []
        for x in n[2:]:
            if x == "li":
                segs.append(cur)
                cur = []
            else:
                cur.append(x)
        segs.append(cur)
        for seg in segs:
            k = 0
            if seg[0] != "tan":                 # the main expression: predicate position
                k = 1
            while k < len(seg):
                word, operand = seg[k], seg[k + 1]
                _nominal(operand, "object" if word == "e" else "source", out)
                k += 2
    else:
        _nominal(n, bare_pos, out)


def violations(skel: str) -> list:
    items = _tokenize(skel)
    node, end = _tree(items)
    assert end == len(items), skel
    out: list = []
    if isinstance(node, Phrase) or _is_alt(node):
        return out                              # P2: a bare statement is a predicate
    if "la" in node:
        if node[0] == "tan":
            _nominal(node[1], "source context", out)
            _clause(node[3], out, "clause after la")
        else:
            _clause(node[0], out, "context")
            _clause(node[2], out, "clause after la")
    else:
        _clause(node, out, "subject")
    return out
