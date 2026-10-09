# Changelog

## 2026-10-09 - author follow-ups (PARSER, CONFORMANCE)

- fold gate per overlap component: `max_fold_candidates` limits the maximal fold sets of ONE overlap component, not their product (`jan li` + n x `ilo ilo sitelen ilo sitelen` joined by `e` is RESOLVED for n = 8..14); the dominance pruning checks `max_seconds`; the 36 remaining `ambiguity_v2.jsonl` cases are ACCEPTED (author decision 2026-10-09); frozen conformance files, matrix and canon unchanged.

## 2026-10-09 - author decisions D1-D5 (CANON)

- D1 `canon/03_matrix.md`, `SPEC.md` §3: the Lift labels are canonical axis names (rows R1-R6 Process, Inquiry, Method, Agency, Representation, Integration; columns C1-C7 Identity, Ground, Transform, Select, Realize, Evaluate, Structure) next to the functional column names and narrative row roles. The generative relation `T[i,j] ≈ Lex(F(Row[i], Column[j]))` stays RESEARCH. No token, cell, label or harness change; 42 tokens and `anu 1.1` unchanged, no token-version bump; research status wording updated;
- D2 `canon/10_versioning.md`: token inventory `anu 1.1`, grammar = the SPEC as of its last change, parser API `1.0.0`, package `0.2.0` named separately; `RESOURCE_EXHAUSTED` is an operational outcome of the reference parser, not a syntax status (name accepted);
- D3 META fold fallback (SPEC invariant 12, §7.1): a fold applies only where the resulting reading is valid (`jan pi ilo ilo` RESOLVED, `jan li ilo tan tan ma` AMBIGUOUS);
- D4 priority combination (SPEC invariant 18, §7.2): lexicographic, maximal fold set then maximal structural-`tan` set (`ma li tan ma tan ma ma` RESOLVED);
- D5 line edges (SPEC invariant 17): spaces, tabs and exactly one trailing LF or CR LF are ignored; any other line boundary or NBSP is INVALID;
- parser and oracle follow D3-D5 (commit e78be09); 96 baseline conformance cases and the 7 frozen files unchanged; ledger entries in `history/supersession_ledger.md`.

## 2026-10-08 - TP-12 CI, counts, clean-wheel smoke (ENGINEERING)

- `.github/workflows/ci.yml`: separate jobs `tests` (py3.11/3.12, `make check`, hard `import hypothesis` step), `conformance-counts`, `docs-lint`, `package-smoke` (wheel + sdist, fresh venv), `security` (gitleaks, pip-audit); `constraints.txt` pins the toolchain;
- `make check` also runs `tools/conformance_counts.py --check` and lift validate + unittest; `make smoke-wheel` installs the built wheel into a fresh venv and runs conformance from outside the checkout; `python -m openpona conformance` now exits 2 when it finds no cases (was a silent `0 passed`);
- README and MANIFEST.json counts are generated (`--write`) and verified (`--check`): the stale "81" is gone (134 cases at this commit);
- `docs/RELEASE_CHECKLIST.md`: package 0.2.0 / token inventory anu 1.1 / parser API 1.0.0 are separate; docs lint validates complete JSON record examples against the record profiles. Legacy flat YAML sketches (`bound_ref`, `surface_address`, `candidates`, `evidence`) are tolerated explicitly; migrating them is PENDING AUTHOR REVIEW. No canon, matrix or baseline file changed.

## 2026-10-08 - TP-04 conformance independence (ENGINEERING, proposals pending author review)

- `tools/oracle/recognizer.py`: independent structural recognizer written from SPEC 5-7 and `canon/` only; `tools/oracle/compare.py` lists oracle/parser disagreements (2 triaged, both PENDING AUTHOR DECISION: what META priority does when the folded reading is invalid);
- `conformance/ambiguity_v2.jsonl`: proposed cases with rationale, source rule and expected trees (2 carry `triage: open`); `conformance/BASELINE.lock` freezes the six original files, which are unchanged;
- tests: duplicate ids, missing fields, stale count text, changed baseline and any skip-on-missing-dependency now fail; Hypothesis metamorphic properties; `tools/conformance_counts.py` generates the RESOLVED/INVALID/AMBIGUOUS counts. No canon, token or baseline expectation changed.

## 2026-10-01 — tier-2 decisions (author interview)

- grammar: objects before source phrases (`e` after `tan` INVALID); `tan` directly after `li` is a source predicate (`jan li tan ma`), structural reading wins where it exists; a predicate containing `anu` must be the last one (`jan li pali anu jan li awen` INVALID); 9 conformance cases changed/added (90 total);
- speaker: no pronoun — self-reference by the agent's own address (`jan linja`), authorship in `actor`; `jan ni` = "this person" as in Toki Pona (supersedes 2026-09-30);
- `lon`/`tawa`/`sama` stay content words (declared departure); repetition-as-derivative and `tan tan` folding declared;
- glosses: Toki Pona sense column (pu) added to `canon/02` and `data/tokens.csv`; reference edition stated (pu for grammar, ku for senses);
- planets removed from canon/SPEC/cheat-sheet/data table headers; the mnemonic stays in LEARN Lesson 1 and history;
- linguist re-review (6/10): departures 10 (`tan X la` context → decided: source context, structural) and 11 (`anu seme` → declared convergent question idiom) added and decided; conformance 96 cases;
- linguist re-review 4 (7/10): the particle-level rule now carries its META exception and row 5 is classed as a declared breach; `toki_pona_compat.jsonl` holds rejections only (control k20 → basic b19); row 11 scoped to a bare predicate; walkthrough caveats on `kama pi pona ala` and `jan linja`; `ma` sense trimmed to pu; ku senses honestly marked as not yet added; row 5 extended (repeated source phrases fold); `toki_pona_compat.jsonl` relabelled (rejections = Toki Pona-invalid OR declared strictness); EBNF fixed (source predicate takes no objects); `open`/`pilin` senses trimmed to pu.

## 2026-10-01 — independent review round

Five fresh-context reviewers (first-time reader, Toki Pona linguist, tooling engineer, research integrity, mechanical checker) assessed the repository; scores for "publish as-is" were 5/4/4/5/8 of 10. Changes made in response:

- parser: META candidates are units of semantic tokens or `tan` only — particles never fold (`li li li`, `la la jan li pali` INVALID; `jan li pali li pali` is two predicates); uppercase INVALID; any Unicode line separator ends a statement; 256-token guard; located, rule-named error messages; 18 new conformance cases (81 total);
- packaging: `tokens.csv` shipped inside the package (non-editable install works), package renamed `openpona-language-corpus` 0.2.0, root `LICENSE`, `.gitignore` entries;
- canon: `canon/11` now states the verification status of the Toki Pona claim and lists seven departures found by the review as *under author decision*; negation and tense section; invariant 4 and META scope narrowed in text (particles are not vectors; META units are 1–2 tokens); stale "remain vectors" / "completed phrase" / "implementation question" wording removed;
- research: evidence-status banner on every research file (all strength labels are unpublished internal results); `MX3-W` relabelled "SUPPORTED INTERNALLY (unpublished)";
- re-review (newcomer 6/10, linguist 5/10): `tan` directly after `li` and the unstated reference edition added as departures 8–9; departure 7 softened (`lukin la` = "by appearance"); negation/tense limits recorded; "only `tan` is dual *as in Toki Pona*" and "precedence as in Toki Pona" reworded (true of OpenPona; `anu` placement is OpenPona's own); META "does not change its syntax" reworded (reading replaced, not added); CI-tool examples bind to a CI run, not to the PR; agent docs and system prompt use the walkthrough's `pona ala`; prompt says to strip ` | status` before parsing; parse-level vs binding-level AMBIGUOUS distinguished; LICENSE states no rights over Toki Pona are claimed;
- docs: README first screen rewritten (what / who / what you can do today, 5-line demo, install); `!`/`?` markers explained; gloss drift between cheat sheet and system prompt removed; walkthrough negation gloss corrected (`kama pi pona ala` = became not-fit, Toki Pona reading "became bad"); `REVIEW_CHECKLIST.md` moved to `history/`.

## 2026-09-30 — Toki Pona compatibility and grammar decisions

- definition: OpenPona is a 42-token Executable Operational Language (EOL);
- canon principle: OpenPona does not contradict Toki Pona (`canon/11_toki_pona_compatibility.md`);
- invariant 11 narrowed: only `tan` is both structural and semantic;
- operator precedence, `pi` shape (head 1–2, groups of exactly 2), one statement per line, META depth `n-1` fixed (SPEC §7 pair-regrouping sentence removed);
- multiple `e`/`li`, `e`/`tan` in any order accepted; `anu` joins phrases only (clause-level choice = two `la` statements);
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
