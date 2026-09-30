# Changelog

## 2026-09-30 — Toki Pona compatibility and grammar decisions

- definition: OpenPona is a 42-token Executable Operational Language (EOL);
- canon principle: OpenPona does not contradict Toki Pona (`canon/11_toki_pona_compatibility.md`);
- invariant 11 narrowed: only `tan` is both structural and semantic;
- operator precedence, `pi` shape (head 1–2, groups of exactly 2), one statement per line, META depth `n-1` fixed (SPEC §7 pair-regrouping sentence removed);
- multiple `e`/`li`, `e`/`tan` in any order accepted; clause-level `anu` left open;
- reference parser, CLI and conformance corpus added (`openpona/`, `conformance/`).

## 2026-09-29 — consolidated corpus

- consolidated `anu 1.1` token inventory;
- incorporated later grammar decisions: vector-first semantics, META priority, structural-position rule, explicit `pi` grouping for 3+ unit concepts, repetition algebra;
- separated canon from matrix-coordinate research;
- recorded OpenPona/EOO dependency hypotheses as weakened/unsupported rather than canonical architecture;
- added Ontology-Language candidate test boundary;
- added executable corpus integrity checks and learning path.
