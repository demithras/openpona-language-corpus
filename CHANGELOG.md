# Changelog

## 2026-09-30 — Toki Pona compatibility and grammar decisions

- definition: OpenPona is a 42-token Executable Operational Language (EOL);
- canon principle: OpenPona does not contradict Toki Pona (`canon/11_toki_pona_compatibility.md`);
- invariant 11 narrowed: only `tan` is both structural and semantic;
- operator precedence, `pi` shape (head 1–2, groups of exactly 2), one statement per line, META depth `n-1` fixed (SPEC §7 pair-regrouping sentence removed);
- multiple `e`/`li`, `e`/`tan` in any order accepted; clause-level `anu` left open;
- reference parser, CLI and conformance corpus added (`openpona/`, `conformance/`);
- `jan ni` = speaker; external values never in the surface (`literals` in the statement schema); clause-level `anu` replaced by two `la` statements;
- matrix column names functional-first (`Seed (Sun)`); matrix experiment ids renamed `MX*`; `H-TS` (truth status in the surface) opened as research;
- licenses added (CC BY 4.0 text, MIT code); Toki Pona / Sonja Lang acknowledgement; `GLOSSARY.md`; `FILE_INDEX.sha256` removed (git is the integrity layer);
- `CHEATSHEET.md`, `examples/walkthrough_ci_failure.md`, `docs/for-agents.md`, `prompts/openpona_system.md`; every ```openpona line in every `.md` is parsed by `tests/test_docs_examples.py` (`make docs`).

## 2026-09-29 — consolidated corpus

- consolidated `anu 1.1` token inventory;
- incorporated later grammar decisions: vector-first semantics, META priority, structural-position rule, explicit `pi` grouping for 3+ unit concepts, repetition algebra;
- separated canon from matrix-coordinate research;
- recorded OpenPona/EOO dependency hypotheses as weakened/unsupported rather than canonical architecture;
- added Ontology-Language candidate test boundary;
- added executable corpus integrity checks and learning path.
