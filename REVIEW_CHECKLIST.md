# Author review checklist before public release

Review these items explicitly:

- [ ] The canonical 42-token sequence and `anu 1.1` Sprint 5 ordering are correct.
- [ ] The operational gloss of every token feels faithful; glosses are anchors, not exhaustive definitions.
- [ ] META/repetition is intended as canon, not only research.
- [ ] Structural-position rule is stated correctly: `li la e tan pi anu` are structural in grammatical position and still vectors otherwise.
- [ ] The 3+ semantic-unit `pi` grouping rule is intended as canon.
- [ ] Matrix coordinate H7-W/H7-S results are described with the right strength.
- [ ] OpenPona/EOO dependency hypotheses are correctly marked unsupported rather than erased.
- [ ] Authority/judgment boundary is correct.
- [ ] No older Core42 artifact silently overrides later canon.
- [ ] Choose and add explicit public licenses before calling the repository open source.

## Grammar decisions surfaced by the reference parser (2026-09-30)

The parser in `openpona/` implements these as **defaults pending decision**; see `research/parser_probe/README.md`.

- [ ] L1 — Operator precedence, loosest to tightest: `la` → `li` → `e`/`tan` → `anu` → `pi` (Toki Pona convention).
- [ ] L2 — `pi` placement: a concept is at most `u u pi u u`; nested `pi` is currently INVALID.
- [ ] L3 — Statement boundary: one statement per line (no in-line separator).
- [ ] META depth contradiction: `examples/meta.md` says `P P P P` = `D^3(P)`; SPEC §7 says four repetitions regroup as two pairs "without changing depth", but `(P P)(P P)` = `D(D(P))` = `D^2(P)`. Parser follows `examples/meta.md` (n repetitions → depth n−1).
- [ ] META beats structure: `sona li kama tan tan` parses as `kama D1(tan)`, not "comes from `tan`". Intended?
- [ ] Rule 11 is not always positional: `jan pi li pali` is AMBIGUOUS (2 parses) in dual mode.
- [ ] Fixed predicate order (`e` before `tan`), a single `e` per predicate, and no clause-level `anu` are current gaps (`conformance/invalid_and_gaps.jsonl`).
