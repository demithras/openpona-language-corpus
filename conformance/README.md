# Conformance corpus

Language-level test cases any OpenPona parser can run against. Each line of each `*.jsonl` file is one case:

| Field | Meaning |
|---|---|
| `id` | stable case id |
| `surface` | input sentence (Latin tokens, space separated) |
| `expect_status` | `RESOLVED` (exactly one parse), `AMBIGUOUS` (more than one), `INVALID` (none) |
| `expect_skeletons` | the set of expected parses, order-independent (omitted for `INVALID`) |
| `note` | why the case exists; `GAP:` marks behaviour that records a missing rule, not a decision |

## Skeleton notation

```text
statement = clause | "(" clause " la " clause ")" | "(tan " expr " la " clause ")"   -- source context (2026-10-01)
clause    = expr | "(" expr { " li " predicate } ")"
predicate = ( expr | "tan " expr ) { " e " expr } { " tan " expr }   -- objects before source phrases (2026-10-01)
expr      = phrase | "(" phrase " anu " expr ")"
phrase    = "{" unit [ " " unit ] { " pi " unit " " unit } "}"
unit      = token | "D" depth "(" token [ " " token ] ")"
```

`D<n>(P)` is the META derivative of depth n produced by n+1 repetitions of `P`.

Cases were written by hand before the reference parser existed and re-written on 2026-09-30 after the author's grammar decisions (`canon/11_toki_pona_compatibility.md`, `history/review_checklist_2026-09-30.md`); `toki_pona_compat.jsonl` holds sentences OpenPona must reject — because Toki Pona rejects them or as declared strictness over valid Toki Pona (marked per case); 18 cases added 2026-10-01 after the independent review (particles never fold, uppercase and line separators, chains of `e`/`li`/`anu`). A case changes only with an explicit decision, recorded in the case `note`.
