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

## Grammar decisions (author, 2026-09-30) — now in canon

Principle: **OpenPona does not contradict Toki Pona** (`canon/11_toki_pona_compatibility.md`). Definition: **42-token Executable Operational Language (EOL)**.

- [x] L1 — Precedence as in Toki Pona: `la` → `li` → `e`/`tan` → `anu` → `pi`.
- [x] L2 — `pi`: head 1–2 units, each `pi` group exactly 2 units, several groups each modify the head. `sona pi lawa`, `ilo sona pi lawa` INVALID.
- [x] L3 — One statement per line.
- [x] META depth — `n` repetitions = `D^(n-1)`; only depth matters (`D^2(D^2) = D^4`). SPEC §7 pair sentence replaced.
- [x] META beats structure — `sona li kama tan tan` = `kama D1(tan)`.
- [x] Only `tan` is dual (invariant 11 narrowed); `li la e pi anu` outside position → INVALID. `jan pi li pali` → INVALID.
- [x] Multiple `e`, `e`/`tan` any order, multiple `li` accepted.
- [ ] Clause-level `anu` (`jan li pali anu jan li awen`) — OPEN until Toki Pona usage is confirmed.
- [ ] Multiple `pi` groups — accepted, flagged as Toki Pona grey zone; confirm or restrict to one group.
