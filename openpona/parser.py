"""normalize -> tokenize -> META runs -> one structural parse -> skeleton rendering.

Priority (SPEC invariant 18, author decision 2026-10-09): a META fold applies only
where the resulting reading is valid (fold fallback, D3); among the valid readings
the fold set is compared first and the structural-`tan` set second, each by
inclusion (lexicographic, D4).  Every repetition run reaches the Earley parser as
an optional multi-token unit, so ONE parse holds every fold choice.

Every stage runs under an explicit `Budget`; running out of budget yields the
operational status RESOURCE_EXHAUSTED (never INVALID, never RESOLVED/AMBIGUOUS
from a partial enumeration).  See docs/parser-complexity.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from itertools import product
from pathlib import Path
import re
import time

from lark import Lark, Token
from lark.exceptions import LarkError
from lark.parsers.earley_forest import TokenNode

from . import PARSER_API_VERSION, TOKENS
from . import ast as _ast

_HERE = Path(__file__).resolve().parent
PARTICLES = ("li", "la", "e", "pi", "anu")  # structural only, never units
MAX_TOKENS = 256
_CASE_MSG = ("case: tokens are lowercase; a capitalised word is a name, "
             "and names never appear in the surface (SPEC 8.2)")

# Operational outcome of the reference parser (a budget ran out), distinct from
# the three syntax outcomes RESOLVED / AMBIGUOUS / INVALID and claiming none of
# them.  Name accepted by the author 2026-10-09 (D2).
RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"


@dataclass
class ParseResult:
    status: str
    skeletons: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)
    reason: str | None = None  # set only for RESOURCE_EXHAUSTED: the budget that ran out
    # Typed parses (openpona.ast), one per skeleton, in sorted-skeleton order:
    # all of them for AMBIGUOUS, one for RESOLVED, none otherwise.  `skeletons`
    # is the stable legacy projection of the same parses.  Syntax only: entity
    # binding (UNRESOLVED) and truth/speech-act are not parse fields.
    alternatives: tuple = ()
    api_version: str = PARSER_API_VERSION

    def to_json(self) -> dict:
        """The versioned, machine-readable result (docs/parser-api.md)."""
        return {"api_version": self.api_version, "status": self.status,
                "alternatives": [_ast.to_json(a) for a in self.alternatives]}


@dataclass(frozen=True)
class Budget:
    """Compute limits for one `parse` call.  Defaults are generous: every
    conformance case and the 203-token object chain stay far inside them."""
    max_tokens: int = MAX_TOKENS          # token count
    max_fold_candidates: int = 256        # fold ambiguity: maximal META fold sets PER overlap component
    max_skeletons: int = 4096             # parse count: distinct skeletons kept
    max_forest_steps: int = 2_000_000     # parse-forest expansion (rendered combinations)
    max_depth: int = 4096                 # depth of the explicit forest traversal
    max_seconds: float = 10.0             # elapsed wall-clock time, checked between steps


DEFAULT_BUDGET = Budget()


@dataclass
class ParseStats:
    """Deterministic work counters (not wall time), filled by `parse(..., stats=)`."""
    fold_steps: int = 0        # run detection + fold enumeration steps
    runs: int = 0
    components: int = 0        # overlap components of the runs
    fold_candidates: int = 0   # maximal META fold sets (the budget gate on fold ambiguity)
    earley_parses: int = 0     # Earley parses (one per statement since 2026-10-09)
    earley_tokens: int = 0     # sum of token counts over those parses
    forest_steps: int = 0      # forest nodes visited + combinations rendered
    max_depth: int = 0         # deepest explicit traversal frame
    skeletons: int = 0         # distinct skeletons before the global priority filter
    seconds: float = 0.0

    @property
    def work(self) -> int:
        return self.fold_steps + self.earley_tokens + self.forest_steps


class _Exhausted(Exception):
    def __init__(self, budget: str, detail: str):
        super().__init__(budget)
        self.budget = budget
        self.detail = detail


class _Ctx:
    def __init__(self, budget: Budget, stats: ParseStats):
        self.b = budget
        self.st = stats
        self.t0 = time.monotonic()

    def tick(self) -> None:
        if time.monotonic() - self.t0 >= self.b.max_seconds:
            raise _Exhausted("max_seconds", f"elapsed time exceeded {self.b.max_seconds} s")


@lru_cache(maxsize=None)
def _lark() -> Lark:
    text = (_HERE / "grammar.lark").read_text(encoding="utf-8")
    return Lark(text, parser="earley", lexer="dynamic", ambiguity="forest",
                keep_all_tokens=True, start="start")


# ---------------------------------------------------------------- META fold
def _find_runs(toks: list[str], st: ParseStats | None = None
               ) -> list[tuple[int, int, int, tuple[str, ...]]]:
    """Maximal runs of k>=2 copies of a 1- or 2-token unit: (start, end, k, P).

    O(n) per unit size: each run is extended once from its leftmost start."""
    runs = []
    n = len(toks)
    steps = 0
    for size in (1, 2):
        for i in range(n - size + 1):
            steps += 1
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
                steps += 1
            if k >= 2:
                runs.append((i, i + k * size, k, p))
    if st is not None:
        st.fold_steps += steps
    return runs


def _components(runs):
    """Split runs into overlap components (connected components of the interval
    overlap graph).  Runs in different components never interact, so the maximal
    non-overlapping sets of all runs are exactly the products of per-component sets."""
    comps: list[list] = []
    end = -1
    for r in sorted(runs):
        if comps and r[0] < end:
            comps[-1].append(r)
            end = max(end, r[1])
        else:
            comps.append([r])
            end = r[1]
    return comps


def _component_sets(comp, limit: int, st: ParseStats | None = None):
    """All maximal sets of pairwise non-overlapping runs of one component.

    Output-sensitive: a chosen run `a` may be followed by `b` (b.start >= a.end)
    only if no run lies entirely inside the gap [a.end, b.start); the first
    chosen run has no run entirely before it and the last none entirely after.
    If any run starts at or after a.end, the one ending first is a legal
    successor, so every path of this search ends in a maximal set: no dead
    branches are explored.
    Stops (returns None) once more than `limit` sets exist."""
    rs = sorted(comp)
    m = len(rs)
    lo = min(r[0] for r in rs)

    def nothing_inside(a_end: int, b_start: int) -> bool:
        return not any(x[0] >= a_end and x[1] <= b_start for x in rs)

    out: list[list] = []
    stack = [[r] for r in reversed(rs) if nothing_inside(lo, r[0])]
    steps = 0
    while stack:
        chosen = stack.pop()
        steps += 1
        last = chosen[-1]
        nxt = [b for b in rs if b[0] >= last[1] and nothing_inside(last[1], b[0])]
        steps += m * m  # successor scan x gap test
        if not nxt:  # no run starts after `last`, so none lies entirely after it
            out.append(chosen)
            if len(out) > limit:
                break
            continue
        for b in reversed(nxt):
            stack.append(chosen + [b])
    if st is not None:
        st.fold_steps += steps
    return None if len(out) > limit else out


def _render_fold(toks: list[str], chosen, lo: int, hi: int) -> list[str]:
    by_start = {r[0]: r for r in chosen}
    parts, i = [], lo
    while i < hi:
        if i in by_start:
            s, e, k, p = by_start[i]
            parts.append(f"D{k - 1}({' '.join(p)})")
            i = e
        else:
            parts.append(toks[i])
            i += 1
    return parts


def _fold_space(toks: list[str], ctx: _Ctx | None):
    """Factorised space of the MAXIMAL fold sets: a list of segments, each a list
    of alternative token lists.  Plain stretches have one alternative; each overlap
    component has one alternative per distinct maximal run set.  Returns
    (segments, count, runs).  `count` (product over components) is statistics only;
    max_fold_candidates gates each overlap component separately;
    the fold choices themselves, maximal or not, are read by the single Earley
    parse (`_tagged`)."""
    st = ctx.st if ctx else None
    limit = ctx.b.max_fold_candidates if ctx else 1 << 62
    runs = _find_runs(toks, st)
    comps = _components(runs)
    if st is not None:
        st.runs, st.components = len(runs), len(comps)
    segments: list[list[list[str]]] = []
    count = 1
    i = 0
    for comp in comps:
        lo = min(r[0] for r in comp)
        hi = max(r[1] for r in comp)
        if i < lo:
            segments.append([toks[i:lo]])
        sets = _component_sets(comp, limit, st)
        if sets is None:
            raise _Exhausted("max_fold_candidates",
                             f"one META overlap component alone has more than {limit} folds")
        alts: list[list[str]] = []
        for chosen in sets:
            parts = _render_fold(toks, chosen, lo, hi)
            if parts not in alts:
                alts.append(parts)
        segments.append(alts)
        count *= len(alts)
        i = hi
    if i < len(toks):
        segments.append([toks[i:]])
    return segments, count, runs


def _iter_folds(segments):
    for combo in product(*segments):
        out: list[str] = []
        for part in combo:
            out += part
        yield out


def fold_candidates(toks: list[str]) -> list[str]:
    """Folded token sequences (space-joined text), one per maximal run set
    (unbounded helper; `parse` applies the budget)."""
    segments, _, _ = _fold_space(toks, None)
    out: list[str] = []
    for folded in _iter_folds(segments):
        text = " ".join(folded)
        if text not in out:
            out.append(text)
    return out


# ------------------------------------------------------- skeleton rendering
_LABELS = "ABCDEF"  # RUN_<L> terminals of grammar.lark


def _tagged(toks: list[str], runs) -> tuple[str, dict[int, tuple]]:
    """The class string the Earley parser reads, and {start index: run}.

    The grammar distinguishes only token classes (unit `u` / `tan` / each particle).
    A repetition run [s, e) additionally gets a label L: `<L` on its first word and
    `>L` on its last, and the terminal RUN_L reads the whole run as ONE META unit,
    while SEM / TAN still read its words one by one.  So the fold and no-fold
    readings of every run are alternatives of the same parse forest (D3), and the
    priority filter (D4) chooses among them.  Labels are reused only after a run
    ends, so the nearest `>L` after `<L` always closes the same run; overlapping
    runs never exceed three at one token (one 1-token run and two 2-token runs)."""
    words = [t if t in PARTICLES or t == "tan" else "u" for t in toks]
    run_at: dict[int, tuple] = {}
    free = list(_LABELS)
    active: list[tuple[int, str]] = []
    for r in sorted(runs):
        s, e = r[0], r[1]
        for end, lab in [a for a in active if a[0] <= s]:
            active.remove((end, lab))
            free.append(lab)
        if not free:  # unreachable for 1- and 2-token units; kept as a hard stop
            raise _Exhausted("max_fold_candidates",
                             f"more than {len(_LABELS)} META runs overlap at token {s + 1}")
        free.sort()
        lab = free.pop(0)
        active.append((e, lab))
        words[s] += "<" + lab
        words[e - 1] += ">" + lab
        run_at[s] = r
    return " ".join(words), run_at


def _alts(root, toks: list[str], run_at: dict, pos_index: dict[int, int],
          ctx: _Ctx) -> set[str]:
    """Skeleton strings of an Earley SPPF (shared packed parse forest).

    Explicit post-order traversal with a memo per forest node - no Python
    recursion; depth, node visits and rendered combinations are all budgeted.
    Complete symbol nodes yield sets of rendered strings; intermediate nodes
    (Lark's binarised partial rules) yield sets of partial child tuples.
    At every complete node with alternatives, an alternative DOMINATED by another
    (`_prune_local`: fewer folded tokens by inclusion, or the same folds and fewer
    structural `tan` by inclusion) is dropped: alternatives of one node derive the
    same symbol over the same span, so they can be swapped in every enclosing
    parse, and the swap that keeps the dominating one dominates the whole reading
    under the global filter `_prefer`.  Same final skeleton set, without
    multiplying out losing readings."""
    b, st = ctx.b, ctx.st
    memo: dict[int, set] = {}
    active: set[int] = set()

    def value(node, as_tuple: bool):
        if isinstance(node, (Token, TokenNode)):
            tok = node.token if isinstance(node, TokenNode) else node
            i = pos_index[tok.start_pos]
            if tok.type.startswith("RUN_"):
                _s, _e, k, p = run_at[i]
                w = f"D{k - 1}({' '.join(p)})"
            else:
                w = toks[i]
            return {(w,)} if as_tuple else {w}
        v = memo[id(node)]
        if node.is_intermediate or not as_tuple:
            return v
        return {(s,) for s in v}

    def bump(n: int = 1) -> None:
        st.forest_steps += n
        if st.forest_steps > b.max_forest_steps:
            raise _Exhausted("max_forest_steps",
                             f"parse-forest expansion exceeded {b.max_forest_steps} steps")
        if not st.forest_steps & 1023:
            ctx.tick()

    if isinstance(root, (Token, TokenNode)):
        return value(root, False)
    stack: list[tuple[object, int, bool]] = [(root, 1, False)]
    while stack:
        node, depth, expanded = stack.pop()
        key = id(node)
        if key in memo:
            continue
        if not expanded:
            if key in active:
                raise _Exhausted("max_depth", "cyclic parse forest")
            if depth > b.max_depth:
                raise _Exhausted("max_depth", f"parse forest deeper than {b.max_depth}")
            if depth > st.max_depth:
                st.max_depth = depth
            active.add(key)
            stack.append((node, depth, True))
            for packed in node.children:
                for ch in packed.children:
                    if not isinstance(ch, (Token, TokenNode)) and id(ch) not in memo:
                        stack.append((ch, depth + 1, False))
            continue
        active.discard(key)
        bump()
        res: set = set()
        for packed in node.children:
            bump()
            seqs = [value(ch, True) for ch in packed.children]
            for combo in product(*seqs):
                bump()
                flat = tuple(x for part in combo for x in part)
                if node.is_intermediate:
                    res.add(flat)
                else:
                    res.add(_fmt(packed.rule.origin.name, flat))
        if not node.is_intermediate and len(res) > 1:
            res = _prune_local(res, ctx.tick)
        memo[key] = res
    return memo[id(root)]


def _fmt(data: str, c) -> str:
    if data in ("start", "unit", "phrase_na"):
        return c[0]
    if data == "statement":
        if len(c) == 4:  # TAN expression LA clause: source context
            return f"(tan {c[1]} la {c[3]})"
        return c[0] if len(c) == 1 else f"({c[0]} la {c[2]})"
    if data == "clause":
        return c[0] if len(c) == 1 else f"({c[0]}{c[1]})"
    if data == "lis":  # LI predicate [lis]
        return f" li {c[1]}" + (c[2] if len(c) > 2 else "")
    if data in ("predicate", "predicate_na", "objs", "objs_na", "tans", "tans_na"):
        return "".join(c)
    if data in ("tanpred", "tanpred_na"):  # TAN expression [tans]
        return f"tan {c[1]}" + (c[2] if len(c) > 2 else "")
    if data in ("obj", "obj_na", "tanp", "tanp_na"):  # E|TAN expression
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


_NO_PARSE = object()


def _forest(sig: str, ctx: _Ctx, cache: dict):
    """Earley forest of a class string (cached per call), or _NO_PARSE."""
    if sig in cache:
        return cache[sig]
    ctx.tick()
    ctx.st.earley_parses += 1
    ctx.st.earley_tokens += sig.count(" ") + 1
    try:
        tree = _lark().parse(sig)
    except LarkError:
        tree = _NO_PARSE
    except RecursionError:  # contained: never a syntax verdict
        raise _Exhausted("max_depth", "parser recursion limit reached") from None
    cache[sig] = tree
    return tree


def _skeletons(toks: list[str], runs, ctx: _Ctx, cache: dict) -> set[str]:
    sig, run_at = _tagged(toks, runs)
    tree = _forest(sig, ctx, cache)
    if tree is _NO_PARSE:
        return set()
    pos_index, pos = {}, 0
    for i, t in enumerate(sig.split(" ")):
        pos_index[pos] = i
        pos += len(t) + 1
    return _alts(tree, toks, run_at, pos_index, ctx)


_SKEL_ITEM = re.compile(r"D(\d+)\(([^)]*)\)|([{}])|[()]|([a-z]+)")


def _reading_key(skel: str) -> tuple[frozenset, frozenset]:
    """(folded token positions, structural `tan` positions) of a skeleton string,
    counted from its first token.  A `tan` is structural when it stands outside
    every {...} phrase; D<n>(P) covers (n+1)*len(P) tokens."""
    folded: set[int] = set()
    structural: set[int] = set()
    pos = depth = 0
    for m in _SKEL_ITEM.finditer(skel):
        if m.group(1) is not None:
            width = (int(m.group(1)) + 1) * len(m.group(2).split())
            folded.update(range(pos, pos + width))
            pos += width
        elif m.group(3):
            depth += 1 if m.group(3) == "{" else -1
        elif m.group(4):
            if m.group(4) == "tan" and depth == 0:
                structural.add(pos)
            pos += 1
    return frozenset(folded), frozenset(structural)


def _maximal(values, tick=None) -> set:
    """The values not strictly included in another one.  `tick` (optional) is the
    time-budget check, called per candidate: the scan is quadratic."""
    vals = set(values)
    out = set()
    for v in vals:
        if tick:
            tick()
        if not any(v < w for w in vals):
            out.add(v)
    return out


def _prune_local(skels: set[str], tick=None) -> set[str]:
    """Alternatives of ONE forest node (same symbol, same span): drop those whose
    folded positions are strictly included in another's, then, among equal
    folds, those whose structural-tan positions are strictly included in
    another's.  Sound for the global filter `_prefer` (see `_alts`)."""
    keyed = [(k, _reading_key(k)) for k in skels]
    best_folds = _maximal((f for _k, (f, _s) in keyed), tick)
    out = set()
    for f in best_folds:
        if tick:
            tick()
        group = [(k, s_) for k, (f2, s_) in keyed if f2 == f]
        best_s = _maximal((s_ for _k, s_ in group), tick)
        out.update(k for k, s_ in group if s_ in best_s)
    return out


def _prefer(skels: set[str]) -> set[str]:
    """SPEC invariant 18 (author decision 2026-10-09, lexicographic):
    1. keep the readings whose set of folded positions is maximal by inclusion
       (META has priority; a fold applies only where the reading is valid);
    2. among those, keep the readings whose set of structural `tan` positions is
       maximal by inclusion (structure over vector where structure exists).
    Several survivors = AMBIGUOUS."""
    if len(skels) < 2:
        return set(skels)
    keyed = [(k, _reading_key(k)) for k in skels]
    best_folds = _maximal(f for _k, (f, _s) in keyed)
    keyed = [(k, (f, s_)) for k, (f, s_) in keyed if f in best_folds]
    best_s = _maximal(s_ for _k, (_f, s_) in keyed)
    return {k for k, (_f, s_) in keyed if s_ in best_s}


def _vector_tans(skel: str) -> int:
    """`tan` tokens read as units: inside {...} but not inside D<n>(...)."""
    flat = re.sub(r"D\d+\([^)]*\)", "", skel)
    return sum(m.split().count("tan") for m in re.findall(r"\{([^}]*)\}", flat))


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
    clause_start = 0
    for i, t in enumerate(toks + ["la"]):
        if t != "la":
            continue
        seg = range(clause_start, i)
        clause_start = i + 1
        lis_ = [j for j in seg if toks[j] == "li"]
        if not lis_:
            continue
        tan_seen = False
        anu_at = None
        for j in seg:
            if j <= lis_[0]:
                continue
            if toks[j] == "li":
                if anu_at is not None:
                    out.append("anu-then-li: a predicate with anu must be the last one; a choice "
                               f"between statements is two la statements on two lines {at(j)}")
                    break
                tan_seen = False
            elif toks[j] == "anu":
                anu_at = j
            elif toks[j] == "tan":
                tan_seen = True
            elif toks[j] == "e" and tan_seen:
                out.append("e-after-tan: objects (e) come before source phrases (tan) "
                           f"{at(j)}")
                break
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
        if t in ("li", "la", "e", "anu", "tan"):  # tan phrases bound a segment too; hint only
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
def _exhausted(e: _Exhausted, toks: list[str]) -> ParseResult:
    return ParseResult(RESOURCE_EXHAUSTED, [], [
        f"resource: budget {e.budget} ran out ({e.detail}); this is not a syntax verdict"],
        toks, e.budget)


def parse(text: str, budget: Budget | None = None, stats: ParseStats | None = None
          ) -> ParseResult:
    """Parse one statement.  Status is RESOLVED / AMBIGUOUS / INVALID, or the
    operational RESOURCE_EXHAUSTED when a `Budget` limit runs out first."""
    b = budget or DEFAULT_BUDGET
    st = stats if stats is not None else ParseStats()
    ctx = _Ctx(b, st)
    try:
        return _parse(text, ctx)
    finally:
        st.seconds = time.monotonic() - ctx.t0


# SPEC invariant 17 (author decision 2026-10-09): spaces and tabs around the
# statement are ignored, and so is exactly ONE final line boundary (LF or CR LF).
# Any other line or paragraph separator, anywhere, makes the line INVALID.
_LINE_BREAKS = frozenset("\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029")


def _line(text: str) -> tuple[str | None, str]:
    """-> (the statement line without its one optional final LF / CR LF, or None
    when another line boundary remains; the error message for None)."""
    if text.endswith("\r\n"):
        text = text[:-2]
    elif text.endswith("\n"):
        text = text[:-1]
    if not any(ch in _LINE_BREAKS for ch in text):
        return text, ""
    if len([ln for ln in text.splitlines() if ln.strip(" \t")]) > 1:
        return None, "line: one statement per line"
    return None, ("line: only spaces/tabs around the statement and one final LF or "
                  "CR LF are ignored; any other line boundary is not (SPEC 17)")


def _parse(text: str, ctx: _Ctx) -> ParseResult:
    line, msg = _line(text)
    if line is None:
        return ParseResult("INVALID", [], [msg], [])
    toks = [t for t in re.split(r"[ \t]+", line.strip(" \t")) if t]
    if not toks:
        return ParseResult("INVALID", [], ["empty input"], [])
    if any(ch.isupper() for ch in line):
        return ParseResult("INVALID", [], [_CASE_MSG], toks)
    known = set(TOKENS)
    if any(t not in known for t in toks):
        errs = [f"unknown-token: {t!r} is not one of the 42 tokens (token {i + 1} '{t}')"
                for i, t in enumerate(toks) if t not in known]
        return ParseResult("INVALID", [], errs, toks)
    if len(toks) > ctx.b.max_tokens:
        return ParseResult(RESOURCE_EXHAUSTED, [], [
            f"length: reference parser accepts at most {ctx.b.max_tokens} tokens per "
            "statement (budget max_tokens; not a syntax verdict)"], toks, "max_tokens")
    try:
        _segments, count, runs = _fold_space(toks, ctx)
        ctx.st.fold_candidates = count
        skels = _skeletons(toks, runs, ctx, {})
        if len(skels) > ctx.b.max_skeletons:
            raise _Exhausted("max_skeletons",
                             f"more than {ctx.b.max_skeletons} distinct parses")
        ctx.st.skeletons = len(skels)
        out = sorted(_prefer(skels))
        alternatives = []
        for skel in out:  # typed trees are built under the same time budget
            ctx.tick()
            alternatives.append(_ast.from_skeleton(skel, toks))
    except _Exhausted as e:
        return _exhausted(e, toks)
    if not out:
        errs = _diagnose(toks) or ["no structural parse"]
        return ParseResult("INVALID", [], errs, toks)
    return ParseResult("RESOLVED" if len(out) == 1 else "AMBIGUOUS", out, [], toks,
                       alternatives=tuple(alternatives))
