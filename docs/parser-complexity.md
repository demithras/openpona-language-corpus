# Parser complexity and the resource-exhaustion policy

Classification: **ENGINEERING** (reference-parser implementation). Nothing here
changes canon: the grammar, the token inventory, META semantics and every
conformance outcome are unchanged. The 96 baseline conformance cases (`conformance/BASELINE.lock`) give byte-identical
`status`, `skeletons` and `errors` before and after this change.

Ticket: TP-01 (OpenPona Improvement TZ v0.2). Baseline: `97a9b9e`.

**Revision 2026-10-09 (commit `e78be09`, author decisions D3-D5).** The fold and
structure stages were redesigned: one Earley parse now holds the folded and the
unfolded reading of every repetition run (fold fallback, D3), priority is
lexicographic (D4), and line edges are fixed (D5). Sections below describe the
CURRENT design; the "What was slow" analysis and the benchmark table are kept as
the TP-01 history (the table is labelled with the commit it was measured at).
The 96 baseline conformance cases still give identical `status` and `skeletons`;
only the cases decided on 2026-10-09 changed (see `conformance/canon_2026_10_09.jsonl`).

## What was slow

The baseline pipeline had three avoidable exponential steps:

1. **META fold (`_maximal_sets`).** Every subset of repetition runs was explored
   (choose or skip each run), and maximality was checked only at the leaves. With
   *n* independent, non-overlapping runs there is exactly one maximal set, but the
   search visited 2^n leaves. Measured: 1.8 s at n = 20 and about 16x slower for
   every 4 more runs.
2. **Explicit-ambiguity trees.** Lark's `ambiguity="explicit"` turns the shared
   Earley forest into a tree with `_ambig` nodes at the top, one full copy per
   reading. A legal statement with *k* source predicates (`jan li tan ilo li tan
   sona ...`) has 2^k raw readings (structural `tan X` against vector `{tan X}`).
   Lark built all of them *inside* `parse()`, which cannot be interrupted: 4.4 s
   at k = 20, and much longer as k grows.
3. **Recursive rendering.** `_alts` recursed once per tree level. The baseline
   raised the global interpreter recursion limit to 20000 while rendering. That
   setting is process-wide and is not safe in code that serves requests.

## Design

The pipeline is still normalize, tokenize, META fold, structural parse, render.
Each stage now does less work, and every stage runs under a `Budget`.

### META runs: overlap components and one labelled parse

* `_find_runs` is unchanged. It finds maximal runs of k >= 2 copies of a 1- or
  2-token unit, with no particles, in O(n) per unit size.
* `_components` splits the runs into **overlap components** (connected components
  of the interval-overlap graph, one pass over the runs sorted by start).
  `_component_sets` lists the maximal non-overlapping run sets of one component
  without dead branches (O(sets x m^2) for *m* runs). The size of the
  factorised fold space (the product over components of the number of maximal
  sets) is computed *before* anything is built, as a statistic
  (`fold_candidates`). The **fold-ambiguity budget gate** works **per overlap
  component** (author decision 2026-10-09): if ONE component alone has more than
  `max_fold_candidates` maximal fold sets, `parse` stops at once. The product
  over components is not gated, so many components with a few folds each no
  longer exhaust the budget. *n* independent runs make *n* singleton components.
* The fold sets are **no longer parsed one by one.** The maximal sets only
  measure the ambiguity.

### Fold fallback (D3): runs as optional units in one parse

A META fold applies only where the resulting reading is valid. So a fold must not
be forced, and a non-maximal fold must stay reachable (`jan pi jan jan` is
RESOLVED with the repetition left unfolded).

* `_tagged` builds the class string the Earley parser reads. The grammar tells
  apart only token classes (unit `u`, `tan`, each particle). Every run gets a
  label L in `A`-`F`: `<L` is appended to its first word and `>L` to its last.
  Labels are reused only after a run ends, so the nearest `>L` after `<L` always
  closes the same run. At most three runs overlap at one token (one 1-token run
  and two 2-token runs), so six labels suffice. If they ever do not, the parser
  raises `RESOURCE_EXHAUSTED` (`max_fold_candidates`).
* `grammar.lark` reads each labelled span two ways: `SEM` / `TAN` accept the
  words one by one (no fold), and the terminals `RUN_A` ... `RUN_F` accept the
  whole span as **one META unit** (fold). A fold that makes the reading invalid
  simply has no parse. All fold choices, maximal or not, are therefore
  alternatives of **one** SPPF. There is no subset enumeration and no
  per-signature parsing: `earley_parses` is 1 per statement.
* A `RUN_<L>` token renders as `D<k-1>(P)` for a run of *k* copies of unit *P*.

### Structural parse: shared forest, iterative rendering

* **SPPF, not trees.** Lark runs with `ambiguity="forest"` and returns the shared
  packed parse forest. Its size is polynomial in the input length; Lark never
  unpacks the readings.
* **Iterative rendering.** `_alts` walks the SPPF in post-order with an explicit
  stack and a memo per forest node. It uses no Python recursion and never touches
  the interpreter recursion limit. Complete symbol nodes give sets of rendered
  strings; intermediate nodes (Lark's binarised partial rules) give sets of
  partial child tuples.

### Priority (D4): lexicographic, by inclusion

`_prefer` (global filter, SPEC invariant 18) reads two keys from each skeleton
string (`_reading_key`): the set of **folded token positions** (`D<n>(P)` covers
(n+1) x len(P) tokens) and the set of **structural `tan` positions** (a `tan`
outside every `{...}` phrase).

1. Keep the readings whose set of token positions covered by META folds
   (the folded-position set) is **maximal by inclusion**
   (META has priority, but only where the reading is valid).
2. Among those, keep the readings whose structural-`tan` set is maximal by
   inclusion (structure over vector `tan` where structure exists).

Several survivors mean `AMBIGUOUS`; the parser never silently picks one reading.
Positions are token positions, not run identities. The two differ only when a run
lies strictly inside an overlapping run of another unit; this is recorded for the
author in `tools/oracle/triaged.json`.

`_prune_local` applies the same order **at each complete forest node**: the packed
alternatives of one node derive the same symbol over the same span, so they are
interchangeable in every enclosing parse. An alternative with strictly fewer
folded positions, or equal folds and strictly fewer structural `tan`, can never
survive `_prefer`, so it is dropped locally. The final skeleton set is the same,
and losing readings are never multiplied out. (This replaces the TP-01 count-based
local C8 and the global `_prefer_structure`.)

Examples: `jan li tan tan ma` is `({jan} li {D1(tan) ma})` (META beats structure);
`jan li tan tan ma tan ma` stays `AMBIGUOUS` (incomparable under both keys).

### Line edges (D5)

`_line` removes exactly one final `\n` or `\r\n`. Spaces and tabs around the
statement are ignored. Any remaining LF, CR, VT, FF, FS, GS, RS, NEL, U+2028 or
U+2029 makes the line `INVALID` (`line: one statement per line` for two
non-blank lines, otherwise a `line:` message). Other whitespace such as NBSP is
an unknown token, as before. The `tools/oracle` tokenizer is aligned with this.

### Equivalence evidence

`tests/test_meta_complexity.py` includes a **reference oracle**: the
pre-TP-01 algorithm (brute-force maximal sets, explicit-ambiguity Lark trees,
full recursive expansion, global C8). Three tests compare the new parser with it:

* fold candidates (`_fold_space` maximal sets): identical on every sequence of
  length <= 8 over `{jan, pali, tan}` (9840 sequences), plus 300 hypothesis examples;
* full `parse` (status + skeletons): 400 hypothesis examples of up to 9 tokens
  over units, `tan` and all particles;
* every conformance surface with at most 40 tokens.

Since 2026-10-09 the reference algorithm in that file brute-forces **every**
non-overlapping run subset and computes D4 independently of `_prefer`. Added
bounded tests: 40 fallback runs in one 203-token statement finish in under 2 s,
and `earley_parses == 1`. A second, independent check is the TP-04 oracle
(`tools/oracle`): `tools/oracle/compare.py` reports 147 of 147 cases agreeing and
0 triaged disagreements, and a property test requires strict equality with the
parser.

Mutation probes run during TP-01 (against the design of that time):

* dropping the gap condition, dropping the first-run condition, or keeping only
  one fold per component each turns at least one of these tests red;
* returning `INVALID` on exhaustion turns the budget tests red.

## Resource-exhaustion API policy

> **PENDING AUTHOR REVIEW** (spec pack `AUTHOR_REVIEW_QUEUE` item 5): the
> status name `RESOURCE_EXHAUSTED`, the `reason` field, the CLI exit code 3, and
> the move of the 256-token guard from `INVALID` to `RESOURCE_EXHAUSTED`. The
> semantics below are what TP-01 requires; the names are this implementation's
> proposal, not an author decision.

`parse(text, budget=None, stats=None) -> ParseResult`

| status | meaning | `skeletons` | `reason` |
|---|---|---|---|
| `RESOLVED` | exactly one parse (syntax verdict) | 1 | `None` |
| `AMBIGUOUS` | several parses, all returned (syntax verdict) | >= 2 | `None` |
| `INVALID` | no parse (syntax verdict) | `[]` | `None` |
| `RESOURCE_EXHAUSTED` | a compute budget ran out first: **no verdict** | `[]` | budget name |

Rules:

1. `RESOURCE_EXHAUSTED` is operational. It never means "invalid", and it never
   carries a partial result. A budget can only *replace* a verdict, never
   change it (property test `test_a_budget_never_changes_a_verdict`).
2. Cheap, definite verdicts come first: line count, empty input, case and
   unknown tokens are checked before any budget. An input with an unknown token
   is `INVALID` even when it is too long.
3. `errors[0]` names the budget and says it is not a syntax verdict. The prefix
   is `resource:`, or `length:` for the token budget, which keeps the existing
   message.
4. CLI `python -m openpona parse` exits 0 for RESOLVED/AMBIGUOUS, 1 for INVALID,
   and **3** for RESOURCE_EXHAUSTED.
5. Callers must not cache or store `RESOURCE_EXHAUSTED` as a parse status of the
   statement. They should retry with a larger `Budget`, or report the statement
   as unprocessed. (`schema/statement.schema.json` `parse_status` is unchanged.)

`Budget` fields and defaults:

| field | default | guards | `reason` |
|---|---|---|---|
| `max_tokens` | 256 | token count | `max_tokens` |
| `max_fold_candidates` | 256 | fold ambiguity: number of **maximal META fold sets of ONE overlap component** (not the product over components; the product is only the `fold_candidates` statistic). Since 2026-10-09 fold choices are not separate parses, so this no longer counts parses | `max_fold_candidates` |
| `max_skeletons` | 4096 | parse count: distinct parses kept; also an upper bound on the forest's readings, checked before rendering | `max_skeletons` |
| `max_forest_steps` | 2,000,000 | parse-forest expansion | `max_forest_steps` |
| `max_depth` | 4096 | explicit traversal depth (also catches a contained `RecursionError`) | `max_depth` |
| `max_seconds` | 10.0 | elapsed time, checked between steps | `max_seconds` |

The defaults are generous. The 203-token object chain uses 1 maximal fold set,
1 Earley parse, and 3155 work units (`bench_meta.py` `long203`).

Memory has no counter of its own. It is bounded indirectly: the fold space is
counted before it is built, the SPPF is polynomial in `max_tokens`, and the
rendered sets are bounded by `max_forest_steps` and `max_skeletons`. Peak memory
is measured in the benchmark below.

`ParseStats` (pass `stats=ParseStats()`) exposes deterministic work counters:
`fold_steps`, `runs`, `components`, `fold_candidates` (maximal fold sets),
`earley_parses` (1 per statement), `earley_tokens`, `forest_steps`, `max_depth`,
`skeletons` (distinct skeletons before the global priority filter), plus `seconds`.
`work = fold_steps + earley_tokens + forest_steps` is the counter the scaling
test uses (not wall time).

## Benchmark: before and after

The first table is the TP-01 result, **measured at commit `d5c84dd`** (baseline
`97a9b9e` against the TP-01 candidate). It is kept as history and not
overwritten. The current-code table follows it.

Reproduce with `python tools/bench_meta.py --cap 20`. Point `PYTHONPATH` at a
`git archive` of the baseline to measure it. Each case runs in a fresh
subprocess with a 20 s wall-clock cap; TIMEOUT means the cap was hit and the
process was killed. Peak memory comes from `tracemalloc` in a separate
subprocess. Environment: macOS (Darwin 25.6), CPython 3.14.6, lark 1.3.1, one
run per case.

| family | n | tokens | baseline status | baseline time s | baseline peak KiB | candidate status | candidate time s | candidate peak KiB | candidate work |
|---|---|---|---|---|---|---|---|---|---|
| nonoverlap | 8 | 23 | RESOLVED | 0.0026 | 322 | RESOLVED | 0.0021 | 269 | 281 |
| nonoverlap | 12 | 35 | RESOLVED | 0.0082 | 534 | RESOLVED | 0.0031 | 447 | 425 |
| nonoverlap | 16 | 47 | RESOLVED | 0.1034 | 769 | RESOLVED | 0.0045 | 668 | 569 |
| nonoverlap | 20 | 59 | RESOLVED | 1.7683 | 1072 | RESOLVED | 0.0059 | 918 | 713 |
| overlap | 8 | 47 | AMBIGUOUS (256) | 0.9453 | 5438 | AMBIGUOUS (256) | 0.0768 | 473 | 60940 |
| overlap | 12 | 71 | TIMEOUT | TIMEOUT | - | RESOURCE_EXHAUSTED | 0.0001 | 11 | 339 |
| overlap | 16 | 95 | TIMEOUT | TIMEOUT | - | RESOURCE_EXHAUSTED | 0.0002 | 13 | 423 |
| overlap | 20 | 119 | TIMEOUT | TIMEOUT | - | RESOURCE_EXHAUSTED | 0.0002 | 15 | 507 |
| random | 8 | 29 | INVALID | 0.0008 | 72 | INVALID | 0.0005 | 67 | 110 |
| random | 12 | 41 | INVALID | 0.0060 | 107 | INVALID | 0.0009 | 97 | 158 |
| random | 16 | 57 | INVALID | 0.0979 | 40 | INVALID | 0.0003 | 39 | 218 |
| random | 20 | 68 | INVALID | 1.7348 | 306 | INVALID | 0.0023 | 299 | 263 |
| long203 | 203 | 203 | RESOLVED | 0.0830 | 13985 | RESOLVED | 0.0845 | 13478 | 3155 |

Reading the table (TP-01, commit `d5c84dd`):

* **nonoverlap / random:** the baseline grows about 16x for every +4 runs
  (2^n). The candidate's work counter grows linearly (281, 425, 569, 713).
* **overlap:** n m12-style components have 2^n *genuine* readings. That output
  really is exponential, so beyond `max_fold_candidates` = 256 the honest answer
  is `RESOURCE_EXHAUSTED` (at the time of this table; since 2026-10-09 the gate is per
  component, a 256-reading overlap component alone still trips it, and the n >= 12
  rows of the `overlap` family end through `max_seconds`, see below). At n = 8 the candidate returns all 256 parses about
  12x faster, because one Earley parse is shared across all readings.
* **long203:** the time is unchanged. Most of the remaining peak memory is
  Lark's Earley chart.

### Current code (fold fallback, D3-D5)

Measured on the parser code of `e78be09` (worktree HEAD `43ff366`, which only
changes canon text on top), same command (`tools/bench_meta.py --cap 20`), same
machine, CPython 3.14, lark 1.3.1, one run per case. Peak memory from
`tracemalloc`. "work" is `fold_steps + earley_tokens + forest_steps`.

| family | n | tokens | status | time s | peak KiB | work |
|---|---|---|---|---|---|---|
| nonoverlap | 8 | 23 | RESOLVED | 0.0048 | 507 | 377 |
| nonoverlap | 12 | 35 | RESOLVED | 0.0072 | 865 | 569 |
| nonoverlap | 16 | 47 | RESOLVED | 0.0106 | 1290 | 761 |
| nonoverlap | 20 | 59 | RESOLVED | 0.0150 | 1780 | 953 |
| overlap | 8 | 47 | AMBIGUOUS (256) | 0.0614 | 2580 | 1785 |
| overlap | 12 | 71 | RESOURCE_EXHAUSTED | 0.0002 | 11 | 339 |
| overlap | 16 | 95 | RESOURCE_EXHAUSTED | 0.0002 | 13 | 423 |
| overlap | 20 | 119 | RESOURCE_EXHAUSTED | 0.0002 | 15 | 507 |
| random | 8 | 29 | INVALID | 0.0013 | 160 | 123 |
| random | 12 | 41 | INVALID | 0.0017 | 223 | 175 |
| random | 16 | 57 | INVALID | 0.0008 | 74 | 243 |
| random | 20 | 68 | INVALID | 0.0055 | 715 | 291 |
| long203 | 203 | 203 | RESOLVED | 0.0865 | 13479 | 3155 |

Compared with the `d5c84dd` candidate columns: statuses are identical in every
row. Work is still linear in n for `nonoverlap` (377, 569, 761, 953) and now a
bit higher (about 1.3x) because every run is also an optional unit in the
parse; wall time is about 2-3x and peak memory about 1.9x the old values (still milliseconds and about 1.8 MiB at n = 20), since the one
forest carries both the folded and the unfolded reading. `overlap` n = 8 has the
same 256 parses and the same 0.06 s; its work counter fell (60940 to 1785)
because the 256 readings are no longer parsed one signature at a time. The
`overlap` n >= 12 rows are rejected by the fold-ambiguity gate before any parse.

Families (`tools/bench_meta.py`): `nonoverlap` = `w0 w0 li w1 w1 e w2 w2 ...`;
`overlap` = n copies of `jan pali jan pali jan` joined by `li`/`e`; `random` =
seeded runs of 2-3 copies separated by random particles, ending in `li`
(INVALID by construction); `long203` = `jan li pali` + 100 x `e ilo`.

## Known limits

* **The fold-ambiguity gate is a count of maximal fold sets per overlap
  component, not of valid parses.** Each `ilo ilo sitelen ilo sitelen` (m11-style)
  is its own component with two maximal folds, only one valid. Since 2026-10-09
  the gate looks at one component at a time, so it does not see the 2^n product.
  Measured on `jan li` followed by n copies of `ilo ilo sitelen ilo sitelen`
  joined by `e` (n = 8..14): all `RESOLVED` with one skeleton, each under
  0.03 s (the previous product gate gave `RESOURCE_EXHAUSTED` from n = 9).
  Where every per-component fold choice is *valid*, readings really multiply:
  `jan li` followed by n copies of `jan pali jan pali jan` joined by `e` gives
  `AMBIGUOUS` with 2^n skeletons for n = 8 (256, 0.11 s), n = 11 (2048, 1.0 s),
  n = 12 (4096, 4.0 s: exactly the budget). From n = 13 the parse ends in
  `RESOURCE_EXHAUSTED` through `max_skeletons` after about 0.5 s (n = 13: 0.46 s,
  n = 16: 0.42 s, n = 30: 0.51 s, default budget). In `_alts`, before the
  combinations of a forest node are built, an upper bound on its readings is
  computed by dynamic programming from its already-pruned children (sum over
  packed alternatives, product over children, saturated at `max_skeletons` + 1);
  a bound above the budget raises at once, so the 4096-skeleton set is never
  built. (A bound over the raw forest, ignoring pruning, was tried and rejected:
  it flipped the `nonoverlap` family from `RESOLVED` to `RESOURCE_EXHAUSTED`.)
  The bound ignores only the pruning of the node itself. Same pass: `_maximal`
  compares a value only with the maximal ones found so far and `_prune_local`
  groups by fold set once, which cut the node-pruning cost. No conformance
  record changed status. Never a hang, never `RESOLVED` or `INVALID`.
* **A single Earley parse cannot be interrupted.** `max_seconds` is checked
  between folds and during rendering, not inside Lark. One parse is bounded by
  `max_tokens` (Earley is at most cubic). The slowest input seen at 253-255 tokens
  is about 0.15 s.
* Timings are single runs on one machine, so they are indicative. The
  deterministic `work` counter is what the CI test asserts.

## CI

`tests/test_meta_complexity.py` is collected by the standard
`python -m pytest -q` run. It runs the scaling, budget and equivalence tests,
plus a bounded adversarial benchmark (`bench([8, 20], cap=15)` in subprocesses).
A regression back to exponential folding shows up as a failing TIMEOUT row and
cannot hang the pipeline. The whole file runs in about 5 s.
