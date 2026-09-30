# Conformance corpus

Language-level test cases any OpenPona parser can run against. Each line of each `*.jsonl` file is one case:

| Field | Meaning |
|---|---|
| `id` | stable case id |
| `surface` | input sentence (Latin tokens, space separated) |
| `mode` | `dual` (default; SPEC invariant 11: structural tokens are also vectors) or `strict` |
| `expect_status` | `RESOLVED` (exactly one parse), `AMBIGUOUS` (more than one), `INVALID` (none) |
| `expect_skeletons` | the set of expected parses, order-independent (omitted for `INVALID`) |
| `note` | why the case exists; `GAP:` marks behaviour that records a missing rule, not a decision |

## Skeleton notation

```text
sentence  = clause | "(" clause " la " clause ")"
clause    = expr | "(" expr " li " predicate ")"
predicate = expr [" e " expr] [" tan " expr]
expr      = phrase | "(" phrase " anu " expr ")"
phrase    = "{" unit { " " unit | " pi " unit } "}"
unit      = token | "D" depth "(" token { " " token } ")"
```

`D<n>(P)` is the META derivative of depth n produced by n+1 repetitions of `P`.

Cases were written by hand before the reference parser existed. Status: the grammar they encode is **RESEARCH** (see `research/parser_probe/`); a case changes only with an explicit decision, recorded in the case `note`.
