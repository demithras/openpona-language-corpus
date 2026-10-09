# 10 — Versioning

**Status: CANON / HISTORY**

## Pre-canon

Earlier artifacts used 42 content words and several different matrix/structural arrangements. They are not current canon.

## `anu 1.0`

The 36 semantic + 6 structural architecture was accepted. Sprint 5 used an earlier ordering.

## `anu 1.1`

The canonical Sprint 5 became:

```text
sitelen linja pana toki tenpo pini pi
```

The complete canonical matrix is recorded in `03_matrix.md`.

## Post-1.1 grammar consolidation

Later accepted rules added or clarified:

- every semantic token (and `tan`) is first a vector/operator;
- META/repetition priority;
- `li la e pi anu` are particles only; `tan` is also a vector (this replaced the earlier "otherwise remain vectors" rule on 2026-09-30, see `history/supersession_ledger.md`);
- explicit `pi` grouping for 3+ semantic units in one concept;
- derivative/repetition algebra;
- stronger separation between language, grounding, authority, judgment and execution;
- 2026-10-09: META fold fallback, lexicographic priority combination, line edges (SPEC §7, invariants 12, 17, 18).

These changes do not alter the 42-token inventory, so this repository does not fabricate a new token-version number. A future version bump should be an explicit author decision.

## Four things with four names (author decision 2026-10-09)

| What | Name | Where it lives |
|---|---|---|
| Token inventory | `anu 1.1` | `canon/02_tokens.md`, `canon/03_matrix.md`, `data/matrix.csv` |
| Grammar | the specification as of its last change | `SPEC.md`, `canon/04`–`canon/07`; no grammar identifier is invented, grammar changes are listed by date in `history/supersession_ledger.md` |
| Parser API | `1.0.0` | `openpona.PARSER_API_VERSION` |
| Python package | `0.2.0` | `pyproject.toml` |

The Lift axis names (2026-10-09, `canon/03_matrix.md`) and the 2026-10-09 grammar decisions (META fold fallback, lexicographic priority, line edges) change none of the token inventory; there is no token-version bump.

## `RESOURCE_EXHAUSTED` is not a syntax status

The language has three syntax outcomes: RESOLVED, AMBIGUOUS and INVALID. `RESOURCE_EXHAUSTED` is an operational outcome of the reference parser (a work budget was hit before the parser could decide); it claims none of the three syntax outcomes and says nothing about whether the statement is well-formed. The name is accepted as is (author decision 2026-10-09). Other implementations may budget differently; the conformance corpus contains no case that expects it.
