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

## Grammar decisions (author interview, 2026-09-30)

Decided by the author. Implementation in `openpona/` and `conformance/` still follows the earlier draft until updated.

- [x] L1 — Precedence as in Toki Pona, loosest to tightest: `la` → `li` → `e`/`tan` → `anu` → `pi`.
- [x] L2 — `pi` grouping: a group is 1 or 2 units; `pi` separates groups and is used only when the concept has 3+ units (`sona pi lawa` is INVALID). Several `pi` groups are allowed; as in Toki Pona, each `pi` group modifies the head (first) group, they do not nest. Examples: `ilo pi sona lawa`, `ilo sona pi lawa`, `jan pi ilo pi sona lawa`, `jan ilo pi sona lawa`, `jan pi ilo sona pi lawa`.
- [x] L3 — One statement per line.
- [x] META depth — n flat repetitions give `D^(n-1)`; only the resulting depth matters. `D^m(D^n(P)) = D^(m+n)(P)` (associativity: snap `D^4` = acceleration of acceleration `D^2(D^2)`); there is no separate surface form for nested derivatives. SPEC §7 "four repetitions can be grouped as two repeated pairs" is wrong and must be replaced.
- [x] META beats structure — `sona li kama tan tan` = `kama D1(tan)`.
- [x] Structure beats vector — when a structural token can be read as an operator, it is one; the vector reading is used only when no structural parse exists. `jan pi li pali` → RESOLVED `({jan pi} li {pali})`. Resulting priority: META → structure → vector.
- [x] Close gaps as in Toki Pona: multiple `e`, any order of `e`/`tan` phrases, multiple `li`, clause-level `anu`.
