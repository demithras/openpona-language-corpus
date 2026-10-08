# Parser complexity and the resource-exhaustion policy

Classification: **ENGINEERING** (reference-parser implementation). Nothing here
changes canon: the grammar, the token inventory, META semantics and every
conformance outcome are unchanged. The 96 baseline conformance cases (`conformance/BASELINE.lock`) give byte-identical
`status`, `skeletons` and `errors` before and after this change.

Ticket: TP-01 (OpenPona Improvement TZ v0.2). Baseline: `97a9b9e`.

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

### META fold: overlap components and output-sensitive enumeration

* `_find_runs` is unchanged. It finds maximal runs of k >= 2 copies of a 1- or
  2-token unit, with no particles, in O(n) per unit size.
* `_components` splits the runs into **overlap components**: connected
  components of the interval-overlap graph, found in one pass over the runs
  sorted by start. Runs in different components never interact. So the maximal
  non-overlapping sets of all runs are exactly the **products** of per-component
  maximal sets. Independent runs therefore never multiply: *n* non-overlapping
  runs make *n* singleton components and **one** folded reading.
* `_component_sets` lists the maximal sets of one component with no dead
  branches. A chosen run `a` can be followed by run `b` only when
  `b.start >= a.end` and no run lies entirely in the gap `[a.end, b.start)`. The
  first chosen run must have no run entirely before it. If any run starts after
  `a`, the one that ends first is always a legal successor, so every search path
  ends in a maximal set. The cost is O(sets x m^2) for a component of *m* runs.
* The fold space stays **factorised**: a list of segments, each holding its
  alternatives. Its size (the product) is computed *before* any reading is built.
  If it exceeds `max_fold_candidates`, the parser stops at once.

### Structural parse: shape sharing over a shared forest

* **Shape signature.** The grammar tells apart only token classes: a unit
  (semantic token or `D<n>(...)`), `tan`, and each particle. Every folded reading
  with the same class string therefore has the same parse forest. The parser
  runs Earley once per distinct signature (`u li u e u ...`) and renders each
  reading through that forest by token position. The m12-style family has 2^n
  readings but only one signature, so it needs one Earley parse.
* **SPPF, not trees.** Lark runs with `ambiguity="forest"` and returns the
  shared packed parse forest (SPPF). Its size is polynomial in the input length.
  Lark never unpacks the readings.
* **Iterative rendering.** `_alts` walks the SPPF in post-order with an explicit
  stack and a memo per forest node. It uses no Python recursion and never touches
  the interpreter recursion limit. Complete symbol nodes give sets of rendered
  strings. Intermediate nodes (Lark's binarised partial rules) give sets of
  partial child tuples.
* **C8 (structure over vector `tan`) applied where the ambiguity sits.** The
  packed alternatives of one complete forest node derive the same symbol over the
  same span, so they can be swapped in every enclosing parse. The vector-tan
  count adds up over phrases. An alternative above the local minimum therefore
  can never survive the global `_prefer_structure`, and the parser drops it
  locally. The final skeleton set is the same, and the losing readings are never
  multiplied out. The global `_prefer_structure` still runs across fold
  candidates.

Precedence is preserved: META beats structure, and structure beats vector `tan`.
Genuine ambiguity is preserved too: m12 stays `AMBIGUOUS` with both parses, and
m11 stays `RESOLVED` because only one of its two folds parses. The parser never
silently picks one reading.

### Equivalence evidence

`tests/test_meta_complexity.py` includes a **reference oracle**: the
pre-TP-01 algorithm (brute-force maximal sets, explicit-ambiguity Lark trees,
full recursive expansion, global C8). Three tests compare the new parser with it:

* fold candidates: identical on every sequence of length <= 8 over
  `{jan, pali, tan}` (9840 sequences), plus 300 hypothesis examples;
* full `parse` (status + skeletons): 400 hypothesis examples of up to 9 tokens
  over units, `tan` and all particles;
* every conformance surface with at most 40 tokens.

Mutation probes run during development:

* dropping the gap condition, dropping the first-run condition, or keeping only
  one fold per component each turns at least one of these tests red;
* removing the local C8 pruning turns the `li tan` scaling test red;
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
| `max_fold_candidates` | 256 | parse count: folded readings | `max_fold_candidates` |
| `max_skeletons` | 4096 | parse count: distinct parses kept | `max_skeletons` |
| `max_forest_steps` | 2,000,000 | parse-forest expansion | `max_forest_steps` |
| `max_depth` | 4096 | explicit traversal depth (also catches a contained `RecursionError`) | `max_depth` |
| `max_seconds` | 10.0 | elapsed time, checked between steps | `max_seconds` |

The defaults are generous. The 203-token object chain uses 1 fold, 1 Earley
parse, 2445 forest steps and depth 110.

Memory has no counter of its own. It is bounded indirectly: the fold space is
counted before it is built, the SPPF is polynomial in `max_tokens`, and the
rendered sets are bounded by `max_forest_steps` and `max_skeletons`. Peak memory
is measured in the benchmark below.

`ParseStats` (pass `stats=ParseStats()`) exposes deterministic work counters:
`fold_steps`, `runs`, `components`, `fold_candidates`, `earley_parses`,
`earley_tokens`, `forest_steps`, `max_depth`, `skeletons`, plus `seconds`.
`work = fold_steps + earley_tokens + forest_steps` is the counter the scaling
test uses (not wall time).

## Benchmark: before and after

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

Reading the table:

* **nonoverlap / random:** the baseline grows about 16x for every +4 runs
  (2^n). The candidate's work counter grows linearly (281, 425, 569, 713).
* **overlap:** n m12-style components have 2^n *genuine* readings. That output
  really is exponential, so beyond `max_fold_candidates` = 256 the honest answer
  is `RESOURCE_EXHAUSTED`. At n = 8 the candidate returns all 256 parses about
  12x faster, because one Earley parse is shared across all readings.
* **long203:** the time is unchanged. Most of the remaining peak memory is
  Lark's Earley chart.

Families (`tools/bench_meta.py`): `nonoverlap` = `w0 w0 li w1 w1 e w2 w2 ...`;
`overlap` = n copies of `jan pali jan pali jan` joined by `li`/`e`; `random` =
seeded runs of 2-3 copies separated by random particles, ending in `li`
(INVALID by construction); `long203` = `jan li pali` + 100 x `e ilo`.

## Known limits

* **Not shared across components with different shapes.** n m11-style
  components (`ilo ilo sitelen ilo sitelen`, two folds each, only one valid) make
  2^n distinct signatures. For n <= 8 the result is `RESOLVED`. For n >= 9 it is
  `RESOURCE_EXHAUSTED` (`max_fold_candidates`), even though a single parse
  exists. The parser fails closed, never with a wrong verdict. Lattice parsing
  over the fold alternatives would remove this limit. It is not implemented.
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
