# Author review checklist (closed 2026-09-30; moved to history/ on 2026-10-01)

This is the author's sign-off record, kept as an audit trail. It is not a review by anyone else; the independent reviews of 2026-10-01 are summarised in `CHANGELOG.md` and `canon/11`.

Review these items explicitly. **All ten confirmed by the author on 2026-09-30 (interview, items shown with canon excerpts).**

- [x] The canonical 42-token sequence and `anu 1.1` Sprint 5 ordering are correct.
- [x] The operational gloss of every token feels faithful; glosses are anchors, not exhaustive definitions.
- [x] META/repetition is intended as canon, not only research.
- [x] Structural-position rule — SUPERSEDED 2026-09-30: only `tan` is dual; `li la e pi anu` are particles only (Toki Pona compatibility).
- [x] The 3+ semantic-unit `pi` grouping rule is intended as canon.
- [x] Matrix coordinate MX3-W/MX3-S (formerly H7-W/H7-S) results are described with the right strength. (2026-10-01 review: the labels stand, with an evidence-status banner added to `research/` noting that the experiments are unpublished.)
- [x] OpenPona/EOO dependency hypotheses are correctly marked unsupported rather than erased.
- [x] Authority/judgment boundary is correct.
- [x] No older Core42 artifact silently overrides later canon.
- [x] Licenses decided 2026-09-30: CC BY 4.0 for specification/text, MIT for code, tests and schemas (`LICENSE-CC-BY-4.0.txt`, `LICENSE-MIT.txt`, root `LICENSE`).

## Grammar decisions (author, 2026-09-30) — now in canon

Principle: **OpenPona does not contradict Toki Pona** (`canon/11_toki_pona_compatibility.md`). Definition: **42-token Executable Operational Language (EOL)**.

- [x] L1 — Precedence as in Toki Pona: `la` → `li` → `e`/`tan` → `anu` → `pi`.
- [x] L2 — `pi`: head 1–2 units, each `pi` group exactly 2 units, several groups each modify the head. `sona pi lawa`, `ilo sona pi lawa` INVALID.
- [x] L3 — One statement per line.
- [x] META depth — `n` repetitions = `D^(n-1)`; only depth matters (`D^2(D^2) = D^4`). SPEC §7 pair sentence replaced.
- [x] META beats structure — `sona li kama tan tan` = `kama D1(tan)`.
- [x] Only `tan` is dual (invariant 11 narrowed); `li la e pi anu` outside position → INVALID. `jan pi li pali` → INVALID.
- [x] Multiple `e`, `e`/`tan` any order, multiple `li` accepted.
- [x] Clause-level `anu` — DECIDED: not a rule; `anu` joins phrases only. A choice between whole statements is written as two `la` statements (`X la A` / `Y la B`). `jan li pali anu jan li awen` has exactly one parse (phrase-level `anu`, second `li`).
- [x] Multiple `pi` groups — DECIDED: accepted; each group modifies the head (Toki Pona reading). Grey-zone note stays in canon/11.

## Language decisions (author interview, 2026-09-30, round 2)

- [x] Self-reference: no `mi`/`sina`. **`jan ni` denotes the speaker/author of the statement**, bound to the statement's `actor` like any other contextual address.
- [x] External values (PR numbers, UUIDs, strings): **never in the surface text**. The surface is 42 tokens only; the value lives in the bound statement (`bound_ref`, literals) and the surface points at it by address (`ijo ni`, `ilo pali`).
- [x] Truth/speech-act status inside the language (`lukin la X` = observed, `wile la X` = intended, `seme la X` = unknown): **research hypothesis**, not canon; zero new tokens; falsifier to be written in `research/`.
- [x] Negation and tense follow Toki Pona (`X ala`, `tenpo pini la …`) by the compatibility principle.
- [x] Matrix headers for public readers: **functional label first, planet as mnemonic** (`Seed (Sun)`).

## Publication decisions (2026-09-30)

- Repository name: **`demithras/openpona-language-corpus`**.
- Licenses: CC BY 4.0 (specification/text) + MIT (code, tests, schemas).
- Gate — all of the following before the repository goes public:
  - [x] license files + Toki Pona / Sonja Lang acknowledgement in README (`LICENSE-CC-BY-4.0.txt`, `LICENSE-MIT.txt`, README "Acknowledgement")
  - [x] one end-to-end worked example + one-page cheat sheet (`examples/walkthrough_ci_failure.md`, `CHEATSHEET.md`)
  - [x] agent guide + copy-pasteable system prompt (`docs/for-agents.md`, `prompts/openpona_system.md`)
  - [x] this checklist fully closed
- Housekeeping (all done 2026-09-30): delete `FILE_INDEX.sha256` (git is the integrity layer), resolve hypothesis-id collisions (ledger H5/H6 vs matrix H5-S/H6), add a glossary (EOO, EOL, IR, HDD, Sprint/Day naming), fix schema `$id` placeholder, link `demithras/operational-ontology-poc`.
