"""Typed syntax trees for OpenPona statements (parser API 1.0.0, TP-02).

ENGINEERING module.  It adds a typed, immutable, serialisable form of a parse;
it changes no grammar, no token and no conformance outcome.  See
docs/parser-api.md for the API contract.

Scope boundary (CHANGE_GATES 4 and 5): a tree is a SYNTAX result only.  It has
no field for entity binding (`UNRESOLVED` / `AMBIGUOUS` candidates belong to the
binding step) and none for truth, speech act or authorisation.

Node variants (every node carries `span`, a half-open range of token indexes
into `ParseResult.tokens`):

    Unit         one token (`ilo`, or `tan` read as a vector unit)
    Meta         META derivative D<depth>(unit): depth+1 repetitions of a 1-2 token unit
    Group        `pi a b`
    Phrase       head of 1-2 units plus explicit pi groups
    Alternative  `phrase anu expression`, right-nested exactly as the grammar nests it
    ObjectList   `e X e Y ...`
    SourceList   `tan X tan Y ...`
    Predicate    head (or None for a source predicate `li tan X`), objects, sources
    Predication  subject plus one or more `li` predicates
    Context      `clause la clause`, or the source context `tan X la clause`

`to_skeleton` renders the legacy skeleton string of a tree and `from_skeleton`
reads one back; the skeleton notation of conformance/README.md is lossless, which
is how the reference parser builds its trees.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re

__all__ = [
    "Span", "Unit", "Meta", "Group", "Phrase", "Alternative", "ObjectList",
    "SourceList", "Predicate", "Predication", "Context", "Node",
    "to_json", "from_json", "to_canonical_json", "to_surface", "to_tokens",
    "to_skeleton", "from_skeleton", "shape", "walk", "NODE_TYPES",
]


class Node:
    """Common base of every tree node (not itself instantiated)."""
    __slots__ = ()


def _fail(msg: str):
    raise ValueError(msg)


def _isint(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


@dataclass(frozen=True)
class Span:
    """Half-open token range [start, end) into the statement's token list."""
    start: int
    end: int

    def __post_init__(self):
        if not (_isint(self.start) and _isint(self.end)):
            _fail("span: start and end must be integers")
        if self.start < 0 or self.end <= self.start:
            _fail(f"span: need 0 <= start < end, got [{self.start}, {self.end})")


def _need(value, types, what: str):
    if not isinstance(value, types):
        names = types.__name__ if isinstance(types, type) else "/".join(t.__name__ for t in types)
        _fail(f"{what}: expected {names}, got {type(value).__name__}")


def _order(parent: Node, kids) -> None:
    """Children lie inside the parent span and in surface order, without overlap."""
    pos = parent.span.start
    for k in kids:
        if k.span.start < pos or k.span.end > parent.span.end:
            _fail(f"{type(parent).__name__}: child {type(k).__name__} span "
                  f"[{k.span.start}, {k.span.end}) is out of order or outside "
                  f"[{parent.span.start}, {parent.span.end})")
        pos = k.span.end


@dataclass(frozen=True)
class Unit(Node):
    token: str
    span: Span

    def __post_init__(self):
        _need(self.token, str, "Unit.token")
        _need(self.span, Span, "Unit.span")
        if not re.fullmatch(r"[a-z]+", self.token):
            _fail(f"Unit.token: {self.token!r} is not a lowercase token")
        if self.span.end - self.span.start != 1:
            _fail("Unit: a unit covers exactly one token")


@dataclass(frozen=True)
class Meta(Node):
    """D<depth>(unit): depth+1 consecutive copies of `unit` (1-2 units).
    `unit` carries the spans of the FIRST copy; `span` covers all copies."""
    depth: int
    unit: tuple
    span: Span

    def __post_init__(self):
        _need(self.depth, int, "Meta.depth")
        _need(self.unit, tuple, "Meta.unit")
        _need(self.span, Span, "Meta.span")
        if not _isint(self.depth) or self.depth < 1:
            _fail("Meta.depth: must be an integer >= 1")
        if len(self.unit) not in (1, 2):
            _fail("Meta.unit: 1 or 2 units")
        for u in self.unit:
            _need(u, Unit, "Meta.unit item")
            if u.token in _STRUCTURAL:
                _fail(f"Meta.unit: {u.token!r} is a particle and never folds")
        if self.span.end - self.span.start != (self.depth + 1) * len(self.unit):
            _fail("Meta: span length must be (depth + 1) * len(unit)")
        _order(self, self.unit)


_STRUCTURAL = frozenset({"li", "la", "e", "pi", "anu"})  # `tan` is a unit as well
UnitLike = (Unit, Meta)


@dataclass(frozen=True)
class Group(Node):
    left: Node
    right: Node
    span: Span

    def __post_init__(self):
        _need(self.left, UnitLike, "Group.left")
        _need(self.right, UnitLike, "Group.right")
        _need(self.span, Span, "Group.span")
        _order(self, (self.left, self.right))
        if self.left.span.start <= self.span.start:  # the `pi` token comes first
            _fail("Group: span must start at the `pi` token before the left unit")


@dataclass(frozen=True)
class Phrase(Node):
    head: tuple
    groups: tuple
    span: Span

    def __post_init__(self):
        _need(self.head, tuple, "Phrase.head")
        _need(self.groups, tuple, "Phrase.groups")
        _need(self.span, Span, "Phrase.span")
        if len(self.head) not in (1, 2):
            _fail("Phrase.head: 1 or 2 units")
        for h in self.head:
            _need(h, UnitLike, "Phrase.head item")
            if isinstance(h, Unit) and h.token in _STRUCTURAL:
                _fail(f"Phrase.head: particle {h.token!r} is never a unit")
        for g in self.groups:
            _need(g, Group, "Phrase.groups item")
        _order(self, self.head + self.groups)


@dataclass(frozen=True)
class Alternative(Node):
    """`left anu right`; left is a phrase, right any expression (right-nested)."""
    left: Node
    right: Node
    span: Span

    def __post_init__(self):
        _need(self.left, Phrase, "Alternative.left")
        _need(self.right, (Phrase, Alternative), "Alternative.right")
        _need(self.span, Span, "Alternative.span")
        _order(self, (self.left, self.right))
        if self.right.span.start <= self.left.span.end:  # the `anu` token between
            _fail("Alternative: the `anu` token must lie between the operands")


Expr = (Phrase, Alternative)


@dataclass(frozen=True)
class ObjectList(Node):
    """`e X e Y`; item spans exclude their `e` tokens, the list span includes them."""
    items: tuple
    span: Span

    def __post_init__(self):
        _need(self.items, tuple, "ObjectList.items")
        _need(self.span, Span, "ObjectList.span")
        if not self.items:
            _fail("ObjectList: at least one object")
        for x in self.items:
            _need(x, Expr, "ObjectList item")
        _order(self, self.items)
        if self.items[0].span.start <= self.span.start:
            _fail("ObjectList: span must start at the first `e` token")


@dataclass(frozen=True)
class SourceList(Node):
    """`tan X tan Y`; item spans exclude their `tan` tokens, the list span includes them."""
    items: tuple
    span: Span

    def __post_init__(self):
        _need(self.items, tuple, "SourceList.items")
        _need(self.span, Span, "SourceList.span")
        if not self.items:
            _fail("SourceList: at least one source")
        for x in self.items:
            _need(x, Expr, "SourceList item")
        _order(self, self.items)
        if self.items[0].span.start <= self.span.start:
            _fail("SourceList: span must start at the first `tan` token")


@dataclass(frozen=True)
class Predicate(Node):
    """One predicate after `li`.  `head is None` is the source predicate
    (`li tan X [tan Y]`): then `objects` is None and `sources` is required.
    Structural `tan` lives here, never as a Unit inside a Phrase."""
    head: Node | None
    objects: Node | None
    sources: Node | None
    span: Span

    def __post_init__(self):
        _need(self.span, Span, "Predicate.span")
        if self.head is None:
            if self.objects is not None or self.sources is None:
                _fail("Predicate: a source predicate has sources and no head or objects")
        else:
            _need(self.head, Expr, "Predicate.head")
        if self.objects is not None:
            _need(self.objects, ObjectList, "Predicate.objects")
        if self.sources is not None:
            _need(self.sources, SourceList, "Predicate.sources")
        _order(self, [k for k in (self.head, self.objects, self.sources) if k is not None])


@dataclass(frozen=True)
class Predication(Node):
    subject: Node
    predicates: tuple
    span: Span

    def __post_init__(self):
        _need(self.subject, Expr, "Predication.subject")
        _need(self.predicates, tuple, "Predication.predicates")
        _need(self.span, Span, "Predication.span")
        if not self.predicates:
            _fail("Predication: at least one predicate")
        for p in self.predicates:
            _need(p, Predicate, "Predication.predicates item")
        _order(self, (self.subject,) + self.predicates)


Clause = (Phrase, Alternative, Predication)


@dataclass(frozen=True)
class Context(Node):
    """`context la body`.  `source` is True for the source context `tan X la body`
    (then `context` is an expression and the span starts at the `tan` token)."""
    context: Node
    body: Node
    source: bool
    span: Span

    def __post_init__(self):
        _need(self.source, bool, "Context.source")
        _need(self.context, Expr if self.source else Clause, "Context.context")
        _need(self.body, Clause, "Context.body")
        _need(self.span, Span, "Context.span")
        _order(self, (self.context, self.body))
        if self.source and self.context.span.start <= self.span.start:
            _fail("Context: a source context starts at its `tan` token")


NODE_TYPES = {
    "unit": Unit, "meta": Meta, "group": Group, "phrase": Phrase,
    "alternative": Alternative, "object_list": ObjectList, "source_list": SourceList,
    "predicate": Predicate, "predication": Predication, "context": Context,
}
_NAME = {cls: name for name, cls in NODE_TYPES.items()}

# field -> kind; the order here is only documentation, JSON keys are sorted.
_SPEC = {
    Unit: {"token": "str", "span": "span"},
    Meta: {"depth": "int", "unit": "nodes", "span": "span"},
    Group: {"left": "node", "right": "node", "span": "span"},
    Phrase: {"head": "nodes", "groups": "nodes", "span": "span"},
    Alternative: {"left": "node", "right": "node", "span": "span"},
    ObjectList: {"items": "nodes", "span": "span"},
    SourceList: {"items": "nodes", "span": "span"},
    Predicate: {"head": "node?", "objects": "node?", "sources": "node?", "span": "span"},
    Predication: {"subject": "node", "predicates": "nodes", "span": "span"},
    Context: {"context": "node", "body": "node", "source": "bool", "span": "span"},
}


# ------------------------------------------------------------------ JSON
def to_json(node: Node, spans: bool = True) -> dict:
    """Canonical dict form (keys sorted at every level, tuples as lists).
    `spans=False` drops every `span` key: the pure tree shape."""
    cls = type(node)
    if cls not in _NAME:
        _fail(f"to_json: not an OpenPona node: {cls.__name__}")
    out: dict = {"type": _NAME[cls]}
    for name, kind in _SPEC[cls].items():
        v = getattr(node, name)
        if kind == "span":
            if spans:
                out[name] = {"start": v.start, "end": v.end}
        elif kind in ("node", "node?"):
            out[name] = None if v is None else to_json(v, spans)
        elif kind == "nodes":
            out[name] = [to_json(x, spans) for x in v]
        else:
            out[name] = v
    return dict(sorted(out.items()))


def to_canonical_json(node: Node, spans: bool = True) -> str:
    """Byte-stable JSON text: sorted keys, no whitespace."""
    return json.dumps(to_json(node, spans), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def shape(node: Node) -> dict:
    """Tree meaning without source locations."""
    return to_json(node, spans=False)


def _decode(d, path: str) -> Node:
    if not isinstance(d, dict):
        _fail(f"{path}: object expected")
    t = d.get("type")
    cls = NODE_TYPES.get(t) if isinstance(t, str) else None
    if cls is None:
        _fail(f"{path}: unknown node type {t!r}")
    spec = _SPEC[cls]
    keys = set(d) - {"type"}
    if keys != set(spec):
        _fail(f"{path}: {t} needs exactly {sorted(spec)}; "
              f"missing {sorted(set(spec) - keys)}, unexpected {sorted(keys - set(spec))}")
    kw: dict = {}
    for name, kind in spec.items():
        v, here = d[name], f"{path}.{name}"
        if kind == "span":
            if not (isinstance(v, dict) and set(v) == {"start", "end"}):
                _fail(f"{here}: span object {{start, end}} expected")
            kw[name] = Span(v["start"], v["end"])
        elif kind == "str":
            _need(v, str, here)
            kw[name] = v
        elif kind == "int":
            if not _isint(v):
                _fail(f"{here}: integer expected")
            kw[name] = v
        elif kind == "bool":
            _need(v, bool, here)
            kw[name] = v
        elif kind == "node":
            kw[name] = _decode(v, here)
        elif kind == "node?":
            kw[name] = None if v is None else _decode(v, here)
        else:  # nodes
            _need(v, list, here)
            kw[name] = tuple(_decode(x, f"{here}[{i}]") for i, x in enumerate(v))
    return cls(**kw)


def from_json(d: dict) -> Node:
    """Inverse of `to_json`; strict (unknown or missing keys, wrong types, spans
    out of order and arity violations raise ValueError)."""
    return _decode(d, "$")


# --------------------------------------------------------------- rendering
def to_tokens(node: Node) -> list[str]:
    """The surface token list of a tree (META expanded to its repetitions)."""
    if isinstance(node, Unit):
        return [node.token]
    if isinstance(node, Meta):
        return [t for _ in range(node.depth + 1) for u in node.unit for t in to_tokens(u)]
    if isinstance(node, Group):
        return ["pi", *to_tokens(node.left), *to_tokens(node.right)]
    if isinstance(node, Phrase):
        return [t for k in node.head + node.groups for t in to_tokens(k)]
    if isinstance(node, Alternative):
        return [*to_tokens(node.left), "anu", *to_tokens(node.right)]
    if isinstance(node, ObjectList):
        return [t for x in node.items for t in ("e", *to_tokens(x))]
    if isinstance(node, SourceList):
        return [t for x in node.items for t in ("tan", *to_tokens(x))]
    if isinstance(node, Predicate):
        parts = [node.head, node.objects, node.sources]
        return [t for k in parts if k is not None for t in to_tokens(k)]
    if isinstance(node, Predication):
        return [*to_tokens(node.subject),
                *[t for p in node.predicates for t in ("li", *to_tokens(p))]]
    if isinstance(node, Context):
        lead = ["tan"] if node.source else []
        return [*lead, *to_tokens(node.context), "la", *to_tokens(node.body)]
    _fail(f"to_tokens: not an OpenPona node: {type(node).__name__}")


def to_surface(node: Node) -> str:
    """Canonical one-line surface text of a tree."""
    return " ".join(to_tokens(node))


def to_skeleton(node: Node) -> str:
    """The legacy skeleton string (conformance/README.md notation)."""
    if isinstance(node, Unit):
        return node.token
    if isinstance(node, Meta):
        return f"D{node.depth}({' '.join(u.token for u in node.unit)})"
    if isinstance(node, Group):
        return f"pi {to_skeleton(node.left)} {to_skeleton(node.right)}"
    if isinstance(node, Phrase):
        return "{" + " ".join(to_skeleton(k) for k in node.head + node.groups) + "}"
    if isinstance(node, Alternative):
        return f"({to_skeleton(node.left)} anu {to_skeleton(node.right)})"
    if isinstance(node, Predicate):
        if node.head is None:
            return "tan " + " tan ".join(to_skeleton(x) for x in node.sources.items)
        s = to_skeleton(node.head)
        if node.objects is not None:
            s += "".join(f" e {to_skeleton(x)}" for x in node.objects.items)
        if node.sources is not None:
            s += "".join(f" tan {to_skeleton(x)}" for x in node.sources.items)
        return s
    if isinstance(node, Predication):
        return ("(" + to_skeleton(node.subject)
                + "".join(f" li {to_skeleton(p)}" for p in node.predicates) + ")")
    if isinstance(node, Context):
        lead = "tan " if node.source else ""
        return f"({lead}{to_skeleton(node.context)} la {to_skeleton(node.body)})"
    _fail(f"to_skeleton: not a skeleton-level node: {type(node).__name__}")


def walk(node: Node):
    """Pre-order iterator over a tree."""
    yield node
    cls = type(node)
    for name, kind in _SPEC[cls].items():
        v = getattr(node, name)
        if kind in ("node", "node?") and v is not None:
            yield from walk(v)
        elif kind == "nodes":
            for x in v:
                yield from walk(x)


# --------------------------------------------------------- skeleton reader
_WORD = re.compile(r"D(\d+)\(([a-z]+(?: [a-z]+)?)\)|[a-z]+")


class _Reader:
    """Recursive-descent reader of the skeleton notation.  Every skeleton token
    appears in surface order, so one running token index yields exact spans; if
    `tokens` is given, each consumed token is checked against it."""

    def __init__(self, skel: str, tokens: list[str] | None):
        self.s, self.i, self.toks, self.pos = skel, 0, tokens, 0

    def err(self, msg: str):
        _fail(f"skeleton: {msg} at offset {self.i} of {self.s!r}")

    def lit(self, text: str) -> None:
        if not self.s.startswith(text, self.i):
            self.err(f"expected {text!r}")
        self.i += len(text)

    def at(self, text: str) -> bool:
        return self.s.startswith(text, self.i)

    def eat(self, word: str) -> int:
        """Consume one surface token `word`; return its index."""
        k = self.pos
        if self.toks is not None and (k >= len(self.toks) or self.toks[k] != word):
            got = self.toks[k] if k < len(self.toks) else "<end>"
            self.err(f"token {k + 1} is {got!r}, skeleton has {word!r}")
        self.pos += 1
        return k

    def unit(self, text: str) -> Node:
        m = _WORD.fullmatch(text)
        if not m:
            self.err(f"bad unit {text!r}")
        if m.group(1) is None:
            k = self.eat(text)
            return Unit(text, Span(k, k + 1))
        depth, words = int(m.group(1)), m.group(2).split(" ")
        first = self.pos
        units = tuple(Unit(w, Span(self.eat(w), self.pos)) for w in words)
        for _ in range(depth):
            for w in words:
                self.eat(w)
        return Meta(depth, units, Span(first, self.pos))

    def phrase(self) -> Node:
        self.lit("{")
        end = self.s.find("}", self.i)
        if end < 0:
            self.err("unterminated phrase")
        inner = self.s[self.i:end]
        words, p = [], 0
        while p < len(inner):
            m = _WORD.match(inner, p)
            if not m:
                self.err(f"bad phrase content {inner[p:]!r}")
            words.append(m.group(0))
            p = m.end()
            if p < len(inner):
                if inner[p] != " ":
                    self.err("phrase units must be space separated")
                p += 1
        self.i = end + 1
        start = self.pos
        head, groups = [], []
        j = 0
        while j < len(words) and words[j] != "pi":
            head.append(self.unit(words[j]))
            j += 1
        while j < len(words):
            if words[j] != "pi" or j + 2 >= len(words):
                self.err("a pi group is `pi unit unit`")
            gs = self.eat("pi")
            left, right = self.unit(words[j + 1]), self.unit(words[j + 2])
            groups.append(Group(left, right, Span(gs, self.pos)))
            j += 3
        return Phrase(tuple(head), tuple(groups), Span(start, self.pos))

    def node(self) -> Node:
        if self.at("{"):
            return self.phrase()
        if not self.at("("):
            self.err("expected '{' or '('")
        self.i += 1
        start = self.pos
        if self.at("tan "):
            self.eat("tan")
            self.i += 4
            ctx = self.node()
            self.lit(" la ")
            self.eat("la")
            body = self.node()
            self.lit(")")
            return Context(ctx, body, True, Span(start, self.pos))
        first = self.node()
        if self.at(" li "):
            preds = []
            while self.at(" li "):
                self.i += 4
                self.eat("li")
                preds.append(self.predicate())
            self.lit(")")
            return Predication(first, tuple(preds), Span(start, self.pos))
        if self.at(" la "):
            self.i += 4
            self.eat("la")
            body = self.node()
            self.lit(")")
            return Context(first, body, False, Span(start, self.pos))
        if self.at(" anu "):
            self.i += 5
            self.eat("anu")
            right = self.node()
            self.lit(")")
            return Alternative(first, right, Span(start, self.pos))
        self.err("expected ' li ', ' la ' or ' anu '")

    def sources(self) -> Node:
        start = self.pos
        items = []
        while self.at("tan ") or self.at(" tan "):
            self.i += 4 if self.at("tan ") else 5
            self.eat("tan")
            items.append(self.node())
        return SourceList(tuple(items), Span(start, self.pos))

    def predicate(self) -> Node:
        start = self.pos
        if self.at("tan "):
            return Predicate(None, None, self.sources(), Span(start, self.pos))
        head = self.node()
        objects = None
        if self.at(" e "):
            ostart, items = self.pos, []
            while self.at(" e "):
                self.i += 3
                self.eat("e")
                items.append(self.node())
            objects = ObjectList(tuple(items), Span(ostart, self.pos))
        sources = self.sources() if self.at(" tan ") else None
        return Predicate(head, objects, sources, Span(start, self.pos))


def from_skeleton(skel: str, tokens: list[str] | None = None) -> Node:
    """Read a skeleton string into a tree.  With `tokens` (the surface token
    list) every token is verified and the spans index into it; the whole token
    list must be consumed."""
    r = _Reader(skel, tokens)
    node = r.node()
    if r.i != len(skel):
        r.err("trailing text")
    if tokens is not None and r.pos != len(tokens):
        r.err(f"skeleton covers {r.pos} of {len(tokens)} tokens")
    return node
