# Parser API and the typed syntax tree

Classification: **ENGINEERING** (reference-parser interface). Nothing here changes
canon: no token is added, the grammar is unchanged, and every conformance outcome
(status and skeleton set of the 96 baseline cases) is unchanged.

Ticket: TP-02 (OpenPona Improvement TZ v0.2). Depends on TP-01 (bounded parsing).

## Three identifiers, three meanings

| Identifier | Value | What it versions | Where it lives |
|---|---|---|---|
| Token inventory | `anu 1.1` | the 42 tokens and their arrangement | `MANIFEST.json` (`token_version`), `canon/` |
| Package | `0.2.0` | the distributed corpus + reference parser | `pyproject.toml` |
| **Parser API** | `1.0.0` | the *shape* of `ParseResult` and of the AST JSON | `openpona.PARSER_API_VERSION` |

They move independently. `PARSER_API_VERSION` changes only when the machine-readable
output changes shape (semantic versioning: patch = documentation or bug fix with
identical shape, minor = backward-compatible addition, major = anything a consumer
must adapt to). A token or grammar change is decided by the author and is not an API
version bump by itself; an API bump never implies a canon change.

## `parse()` result

`openpona.parse(text) -> ParseResult` keeps its fields and gains two:

| Field | Meaning |
|---|---|
| `status` | `RESOLVED`, `AMBIGUOUS`, `INVALID`, or the operational `RESOURCE_EXHAUSTED` (TP-01) |
| `skeletons` | legacy projection: sorted skeleton strings. Unchanged values. Stable until a versioned deprecation |
| `tokens`, `errors`, `reason` | unchanged |
| `alternatives` | **new.** `tuple` of typed trees (`openpona.ast`), one per skeleton, in the order of `skeletons`. `AMBIGUOUS`: every parse, never only the first. `RESOLVED`: exactly one. `INVALID` and `RESOURCE_EXHAUSTED`: empty |
| `api_version` | **new.** `PARSER_API_VERSION` (`"1.0.0"`), also on `INVALID` and `RESOURCE_EXHAUSTED` results |

`len(alternatives) == len(skeletons)` always, and `ast.to_skeleton(alternatives[i]) == skeletons[i]`.

### What is deliberately not a parse field

The parse result is a **syntax** result.

* `UNRESOLVED` (and binding-level `AMBIGUOUS` candidates) belong to entity binding,
  the step after parsing. A statement whose address has no candidate still parses
  `RESOLVED`; the tree has no slot for a bound entity.
* Truth status and speech act (`observed`, `asserted`, `requested`, ...) are not
  parse fields. A valid parse never means a true statement or an authorised action.

Existing artifact, not touched by TP-02: `schema/statement.schema.json` (a *bound*
statement record) lists `UNRESOLVED` in its `parse_status` enum. Whether that field
should be split into a syntax status and a binding status is
**PENDING AUTHOR REVIEW**; this ticket does not edit that schema.

## CLI

```text
python -m openpona parse --json "<surface>"
```

prints exactly one JSON object with three keys and sorted keys:

```json
{"alternatives": [ ...trees... ], "api_version": "1.0.0", "status": "AMBIGUOUS"}
```

Exit codes are unchanged: `0` for `RESOLVED`/`AMBIGUOUS`, `1` for `INVALID`, `3` for
`RESOURCE_EXHAUSTED`. Error messages go to stderr as `error: ...`, not into the JSON.
Behaviour change from before TP-02: `--json` used to print the raw `ParseResult`
fields (`skeletons`, `errors`, `tokens`, `reason`); consumers of that dump must read
`skeletons` from the library or call `parse()` directly. Plain `parse` (no `--json`)
is unchanged. The `RESOURCE_EXHAUSTED` name and exit code 3 remain
**PENDING AUTHOR REVIEW** (AUTHOR_REVIEW_QUEUE item 5).

## Tree variants (`openpona.ast`)

All nodes are frozen dataclasses (immutable, hashable, comparable). Each carries
`span = Span(start, end)`: a half-open range of indexes into `ParseResult.tokens`.
Spans nest and never overlap among siblings; particle tokens (`li la e anu tan pi`)
sit in the gaps and are covered by the enclosing node.

| Variant | Fields | Surface |
|---|---|---|
| `Unit` | `token` | one token |
| `Meta` | `depth`, `unit` (1-2 `Unit`, first copy) | `depth + 1` repetitions of the unit (`D<depth>(unit)`) |
| `Group` | `left`, `right` (`Unit`/`Meta`) | `pi left right` |
| `Phrase` | `head` (1-2 `Unit`/`Meta`), `groups` | head then explicit `pi` groups, order preserved |
| `Alternative` | `left` (`Phrase`), `right` (expression) | `left anu right`, right-nested as the grammar nests it |
| `ObjectList` | `items` | `e X e Y ...` |
| `SourceList` | `items` | `tan X tan Y ...` |
| `Predicate` | `head`, `objects`, `sources` | one predicate after `li`; `head is None` is the source predicate `li tan X` |
| `Predication` | `subject`, `predicates` | `subject li p1 li p2 ...` |
| `Context` | `context`, `body`, `source` | `clause la clause`; `source=True` is the source context `tan X la clause` |

A statement's tree is a `Phrase`, `Alternative`, `Predication` or `Context`.

Structural `tan` is never flattened: `tan` as a source phrase or source context
appears only as `SourceList` items / `Context(source=True)`. A `Unit("tan")` occurs
only where the parser's structure-beats-vector rule leaves a vector reading
(`jan tan li pali` -> `{jan tan}`) and inside `Meta` (`tan tan`).

### Functions

| Function | Result |
|---|---|
| `to_json(node, spans=True) -> dict` | canonical dict: `type` discriminator, keys sorted at every level, tuples as lists |
| `to_canonical_json(node)` | the same as byte-stable text (sorted keys, no whitespace) |
| `from_json(d) -> node` | strict inverse; unknown/missing keys, wrong types, bad arities and out-of-order spans raise `ValueError` |
| `to_surface(node) -> str` | one-line surface text (META expanded) |
| `to_skeleton(node) -> str` | the legacy skeleton string |
| `from_skeleton(skel, tokens=None)` | reads a skeleton into a tree; with `tokens`, verifies them and yields spans |
| `shape(node)` | `to_json(node, spans=False)`: tree meaning without locations |

`from_json(to_json(x)) == x` and `parse(to_surface(x)).alternatives` contains `x`
for every parse of every non-`INVALID` statement (tests: `tests/test_ast.py`).
The JSON shape is described by `schema/ast.schema.json`; it covers types, keys and
arities, while cross-field rules (span order, source predicate shape) are enforced by
`from_json`.

## How trees are built

The parser still produces skeleton strings (the TP-01 forest rendering and the
structure-beats-vector rule are untouched). `openpona.ast.from_skeleton` then reads
each skeleton, whose notation (`conformance/README.md`) is lossless and lists tokens
in surface order, into a tree and verifies every token against `ParseResult.tokens`.
Trees are therefore built under the same time budget, and a tree exists for exactly
the skeletons that exist. This is an adapter over the legacy projection, not an
independent second parser.

## Classification of claims

| Claim | Class |
|---|---|
| Tree variants, JSON shape, `alternatives`, `api_version`, CLI output | ENGINEERING |
| Which statements parse, their skeletons, the `tan` precedence rule | CANON (unchanged, from `canon/04_grammar.md` and the conformance corpus) |
| Status name `RESOURCE_EXHAUSTED`, exit code 3, splitting syntax and binding status in `statement.schema.json` | PENDING AUTHOR REVIEW |
| Dropping the `skeletons` field | not proposed; needs a versioned deprecation and a major API bump |

## Known limits

* The tree adapter is exercised against the 96 baseline cases, an exhaustive sweep of
  all sequences up to length 4 (8 tokens) and 6 (5 tokens), and random sequences; it
  is not formally proved total.
* `schema/ast.schema.json` has not been run through an external JSON Schema validator
  in this environment (`jsonschema` is not installed); a test checks that it lists
  the same node types and keys as `openpona.ast`.
* The module is named `openpona/ast.py`; inside the package it never shadows the
  standard library `ast` (imports are absolute), but do not run scripts with
  `openpona/` as the current directory.
