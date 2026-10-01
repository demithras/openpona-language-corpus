# Changelog

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
