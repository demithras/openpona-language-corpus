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

**Rule N2 (phrase length by position, author decision 2026-10-28; not to be confused with the "N2 JSON" tree format of `docs/parser-api.md`).** A phrase of exactly one surface token is allowed only in predicate position (the main expression after `li`, or a bare statement). Every nominal phrase (subject, object after `e`, source after `tan`, context before `la`, and each `anu` alternative there) needs at least two tokens; a META unit counts its surface tokens (`ilo ilo` = 2) and a phrase with a `pi` group always passes. Every case written before that date was re-checked: a case N2 broke had its surface rewritten minimally (usually a one-token nominal became two tokens) and its expectation re-derived by hand from the notation above; a case whose status N2 changes by design kept its surface. Each changed record carries `"decision": "author decision 2026-10-28 (N2 phrase length)"` and a sentence in its `note`/`rationale` that names the old surface and the reason. `tests/test_conformance_integrity.py` holds a skeleton checker that fails on any one-token nominal phrase in an expected skeleton (proved on known negatives).

## TP-04 additions (ENGINEERING; proposals pending author review)

Classification: nothing here changes canon or the 42-token inventory. Baseline expectations changed only by the N2 decision of 2026-10-28 (see above); `BASELINE.lock`, `baseline_provenance.json` and `ambiguity_v2.digests.json` were re-generated for it.

| File | What it is |
|---|---|
| `BASELINE.lock` | sha256 of the six original files (amended 2026-10-28 for N2, plus the declared-strictness cases `k20`, `k21` in `toki_pona_compat.jsonl`). `tests/test_conformance_integrity.py` fails if any of them changes; changing one needs an author decision AND a deliberate edit of the lock. |
| `baseline_provenance.json` | mechanical index of the frozen baseline cases (file, line, status, decision references and note copied verbatim from the case). The `rule_family` per file is an implementer classification, PENDING AUTHOR REVIEW. |
| `ambiguity_v2.jsonl` | cases for META overlap, `tan` precedence (including cases that stay RESOLVED because the structural reading wins), `anu` right-association and nesting-looking `pi`. |
| `ambiguity_v2.digests.json` | digest of each v2 expectation; an expectation that changes needs a `decision` field in the record. |
| `canon_2026_10_09.jsonl` | cases of the author decisions of 2026-10-09: D3 META fold fallback, D4 lexicographic priority (fold set, then structural-`tan` set, each by inclusion), D5 line edges (one final LF or CR LF ignored; any other line boundary INVALID). Same fields as `ambiguity_v2.jsonl`; ids `canon-d3-*`, `canon-d4-*`, `canon-d5-*`. Line-edge characters are stored as JSON escapes (`\n`, `\r`, `\u2028`): every file is one physical line per record. |
| `canon_2026_10_28.jsonl` | cases of rule N2 (phrase length by position), author decision 2026-10-28: the 19 worked examples of the decision (`canon-n2-01`..`canon-n2-19`) and 12 more (`canon-n2-20`..): `anu` alternative in a subject and in a source, META in an object, `pi` phrases, a former AMBIGUOUS `tan` case that N2 resolves (`canon-n2-25`), context clauses with their own `li`, the D3 fold fallback interacting with N2 (`canon-n2-28`), a vector `tan` subject, a bare `anu` statement. Same fields as `canon_2026_10_09.jsonl`; `review` is `ACCEPTED - author decision 2026-10-28`. The `expect_asts` were rendered from the skeletons by a small skeleton-to-JSON converter that first reproduced all 40 trees that existed before (no import of `openpona`). |

### Fields of `ambiguity_v2.jsonl`

`id` (prefix `amb2-`), `surface`, `rationale`, `source_rule` (SPEC section), `expect_status`, `expect_skeletons`, `expect_asts` (when not INVALID: span-free trees in the N2 JSON of `docs/parser-api.md`, compared as a set), `review` (`PROPOSED - PENDING AUTHOR REVIEW`: a proposal, not an author decision; or `ACCEPTED - author decision 2026-10-09` for `amb2-meta-09`, `amb2-tan-01` and every record of `canon_2026_10_09.jsonl`, whose `source_rule` cites that decision; or `ACCEPTED - author decision 2026-10-28` for every record of `canon_2026_10_28.jsonl`), optionally `decision` (set on every record that N2 rewrote), and optionally `triage`.

Expectations were written from SPEC 5-7 and `canon/` before the parser was run on them and are never edited to match the parser. `"triage": "open"` marks a record whose expectation the parser does not meet; `tests/test_conformance.py` skips only such records, with the `triage_note` as the reason, and the record must also be listed in `tools/oracle/triaged.json`.
The `expect_asts` trees were rendered from the reviewed skeletons by `tools/oracle` (a mechanical, lossless step), not typed by hand.

### Tools

```text
python tools/conformance_counts.py            # RESOLVED/INVALID/AMBIGUOUS per file and in total, generated from the cases
python tools/oracle/compare.py                # independent oracle vs parser over every case; exit 0 when every disagreement is triaged
                                              # (report: build/oracle/disagreements.md; no disagreement since 2026-10-09)
```

`tools/oracle/recognizer.py` is a separate structural recognizer written only from SPEC 5-7 and `canon/` (no `lark`, no `openpona` import). Counts in prose are not asserted by hand anywhere: `tests/test_conformance_integrity.py` fails on a stale "N cases" phrase in the current-state documents.
