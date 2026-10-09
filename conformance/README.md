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

## TP-04 additions (ENGINEERING; proposals pending author review)

Classification: nothing here changes canon, the 42-token inventory or any baseline expectation.

| File | What it is |
|---|---|
| `BASELINE.lock` | sha256 of the six original files. `tests/test_conformance_integrity.py` fails if any of them changes; changing one needs an author decision AND a deliberate edit of the lock. |
| `baseline_provenance.json` | mechanical index of the frozen baseline cases (file, line, status, decision references and note copied verbatim from the case). The `rule_family` per file is an implementer classification, PENDING AUTHOR REVIEW. |
| `ambiguity_v2.jsonl` | cases for META overlap, `tan` precedence (including cases that stay RESOLVED because the structural reading wins), `anu` right-association and nesting-looking `pi`. |
| `ambiguity_v2.digests.json` | digest of each v2 expectation; an expectation that changes needs a `decision` field in the record. |
| `canon_2026_10_09.jsonl` | cases of the author decisions of 2026-10-09: D3 META fold fallback, D4 lexicographic priority (fold set, then structural-`tan` set, each by inclusion), D5 line edges (one final LF or CR LF ignored; any other line boundary INVALID). Same fields as `ambiguity_v2.jsonl`; ids `canon-d3-*`, `canon-d4-*`, `canon-d5-*`. Line-edge characters are stored as JSON escapes (`\n`, `\r`, `\u2028`): every file is one physical line per record. |

### Fields of `ambiguity_v2.jsonl`

`id` (prefix `amb2-`), `surface`, `rationale`, `source_rule` (SPEC section), `expect_status`, `expect_skeletons`, `expect_asts` (when not INVALID: span-free trees in the N2 JSON of `docs/parser-api.md`, compared as a set), `review` (`PROPOSED - PENDING AUTHOR REVIEW`: a proposal, not an author decision; or `ACCEPTED - author decision 2026-10-09` for `amb2-meta-09`, `amb2-tan-01` and every record of `canon_2026_10_09.jsonl`, whose `source_rule` cites that decision), and optionally `triage`.

Expectations were written from SPEC 5-7 and `canon/` before the parser was run on them and are never edited to match the parser. `"triage": "open"` marks a record whose expectation the parser does not meet; `tests/test_conformance.py` skips only such records, with the `triage_note` as the reason, and the record must also be listed in `tools/oracle/triaged.json`.
The `expect_asts` trees were rendered from the reviewed skeletons by `tools/oracle` (a mechanical, lossless step), not typed by hand.

### Tools

```text
python tools/conformance_counts.py            # RESOLVED/INVALID/AMBIGUOUS per file and in total, generated from the cases
python tools/oracle/compare.py                # independent oracle vs parser over every case; exit 0 when every disagreement is triaged
                                              # (report: build/oracle/disagreements.md; no disagreement since 2026-10-09)
```

`tools/oracle/recognizer.py` is a separate structural recognizer written only from SPEC 5-7 and `canon/` (no `lark`, no `openpona` import). Counts in prose are not asserted by hand anywhere: `tests/test_conformance_integrity.py` fails on a stale "N cases" phrase in the current-state documents.
