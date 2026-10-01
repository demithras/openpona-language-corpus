# 11 — Toki Pona compatibility

**Status: CANON design principle (author decision, 2026-09-30). Verification status: partial — see "Status of the claim".**

OpenPona reuses Toki Pona's lexical forms and particles. It is designed not to contradict Toki Pona.

## The rule

> Every valid OpenPona statement is a valid Toki Pona sentence, and its OpenPona parse coincides with a Toki Pona parse at the level of particle structure.

"Particle structure" means the boundaries drawn by `la`, `li`, `e`, `pi`, `anu` and the preposition `tan`. Inside a content phrase OpenPona may add structure that Toki Pona does not have (META units, head/group semantics); at the particle level the two parses must agree.

## What OpenPona may do

| Allowed | Example |
|---|---|
| be stricter: fewer words | `mi`, `sina`, `o`, `en`, `mute`, `kalama`, `nimi` are not OpenPona tokens |
| be stricter: require `pi` where Toki Pona merely allows it | `jan ilo sona` is valid Toki Pona and INVALID OpenPona |
| add meaning inside a phrase | `ilo ilo` is emphasis in Toki Pona usage and `D(ilo)` in OpenPona; the line is the same sentence, the reading is OpenPona's (departure 5) |
| fix conventions Toki Pona leaves to the speaker | one statement per line; each `pi` group exactly two units |

## What OpenPona may not do

| Forbidden | Consequence |
|---|---|
| accept a sentence Toki Pona rejects | `li pali`, `la jan li pali`, `jan pi li pali`, `sona pi lawa` are INVALID |
| give a particle a content reading Toki Pona does not give it | `li la e pi anu` are never vectors; only `tan` is (in OpenPona — Toki Pona has further prepositions, departure 1) |
| draw a particle boundary Toki Pona would not draw | precedence follows Toki Pona for `la li e pi`; `anu` placement is OpenPona's own choice, since Toki Pona sets none |

## Grey zones

Where Toki Pona usage is itself divided, OpenPona picks one reading and records it here:

- **multiple `pi` groups** — accepted; each group modifies the head. Toki Pona speakers often avoid this shape; prefer one group where meaning allows.
- **`anu` between whole clauses** — not a rule of OpenPona (author decision, 2026-09-30). `anu` joins phrases; a choice between statements is two `la` statements on two lines. Caveat found in review: a sentence such as `jan li pali anu jan li awen` is not *rejected*, it is accepted with the phrase-level reading, which a Toki Pona speaker would not give it — see departure 2 below.

## Negation and tense

Both follow Toki Pona under this principle (author decision, 2026-09-30):

- **Negation**: `ala` follows the unit it negates, inside a head or a `pi` group — `ilo li awen ala`; `ilo pali li kama pi pona ala` = became [not-good]. `ilo pali li kama pona ala` is INVALID only because it is three units without `pi` — stricter than Toki Pona, so compatible. Limits found in review: "did not become fit" (`kama ala pona`) cannot be said at all under the `pi` shape; the yes/no form `X ala X` is not supported; the `pi` form after a preverb-like head reads nominally to a Toki Pona speaker.
- **Tense**: by context, as in Toki Pona — `tenpo pini la …` (past), `tenpo ni la …` (now), `tenpo kama la …` (future). There is no tense marking inside the clause. Limit: one `la` per statement, so a tense context and a scope context (`tenpo pini la ma pali la …`) cannot appear in the same statement.

## Status of the claim

What is verified: every case in `conformance/toki_pona_compat.jsonl` is rejected by the reference parser as required — some because Toki Pona rejects them (`li pali`, `jan pi li pali`), some as OpenPona strictness over valid Toki Pona (k08, k18, k19; each case says which). What is **not** verified: the positive direction — that every RESOLVED statement is a Toki Pona sentence with the same particle structure. No Toki Pona checker runs in this repository; the only oracle used so far (nim-ka/tpparser, in `research/parser_probe/`) is unlicensed and describes one speaker's grammar.

## Reference edition

Grammar follows **pu** (*Toki Pona: The Language of Good*, 2014). Word senses follow **ku** (*Toki Pona Dictionary*, 2021) where it refines pu; the sense column in `canon/02` currently gives the pu senses, and ku refinements are still to be added (decision 2026-10-01).

## Known departures (independent reviews, 2026-10-01) — all eleven decided 2026-10-01

Each row records a place where the rules accepted something Toki Pona reads differently, or where the wording overstated the match, and what the author decided.

| # | Departure | Where | Decision |
|---|---|---|---|
| 1 | `lon`, `tawa`, `sama` are prepositions in Toki Pona (pu lists lon, tawa, tan, kepeken, sama); OpenPona reads them as content words only, so `jan li lon ma` carries no preposition boundary. "`tan` is the only dual token" is true of OpenPona, not of Toki Pona | `canon/02`, `canon/04` §3 | **Declared.** `lon`/`tawa`/`sama` stay content words; compatibility is defined at the particle level (`la li e pi anu` + `tan`). A Toki Pona reader will see a prepositional phrase where OpenPona sees a content phrase. |
| 2 | `jan li pali anu jan li awen` is accepted as `jan li (pali anu jan) li awen`; a speaker reads a choice between two clauses. The pattern is general: any `anu` + phrase + `li` chain parses this way (`jan li pali anu jan li awen anu ilo`) | `SPEC` §6, `conformance` k08 | **INVALID.** A predicate containing `anu` must be the last predicate (`anu-then-li`). The sentences are valid Toki Pona; rejecting them is OpenPona strictness. |
| 3 | `e` after a `tan` phrase is accepted (`jan li pali tan ilo e sitelen`); pu orders objects before prepositional phrases | `SPEC` §6 | **Forbidden.** Objects come before source phrases, as in pu (`e-after-tan`). Reverses the "any order" part of the 2026-09-30 decision. |
| 4 | `jan ni` = the speaker; in Toki Pona it means "this person" and reads as third person | `SPEC` §8.1, `canon/05` | **Resolved: Toki Pona meaning restored.** `jan ni` = "this person". Self-reference is by the agent's own address (`jan linja`); authorship lives in the record's `actor`. |
| 5 | Repetition is a derivative, not emphasis (`canon/07`): this *replaces* the Toki Pona reading rather than adding to it, and `tan tan` folds over the preposition reading | `canon/07`, `SPEC` §7 | **Declared.** Repetition is a derivative in OpenPona (the Toki Pona emphasis reading is replaced); `tan tan` folds (META beats structure), and so does a repeated source phrase: `jan li pali e ilo tan ma tan ma` → `e {ilo D1(tan ma)}`, where Toki Pona reads two `tan` phrases. |
| 6 | Several glosses hide the Toki Pona sense (`lon` at/in; `tawa` to; `sama` like; `ma` land/place; `ni` this; `jan` person) | `canon/02` | **Done.** `canon/02` and `data/tokens.csv` carry a Toki Pona sense column (pu) next to the operational anchor. |
| 7 | The `lukin la …` research prefix (H-TS) reads as "by appearance / visually" in Toki Pona usage, not as a verified observation | `research/truth_status_in_language.md` | Research only; recorded there. |
| 8 | `tan` directly after `li` is read as a content word (`jan li tan ma` → `{tan ma}`), while Toki Pona reads a prepositional predicate ("is from the land"); `jan li tan ma tan kute` gives `tan` two readings in one sentence | `canon/04` §3, `SPEC` §6 | **Structural.** `li tan X` is a source predicate ("derives from X"); the structural reading wins where it exists, the vector reading applies only where it does not (`jan li tan ma e ijo`). |
| 9 | The reference edition of Toki Pona (pu 2014 / ku 2021) is not stated | `canon/11` | **Stated** above: pu for grammar, ku for word senses. |
| 10 | `tan X la` at the start of a statement is read as a content phrase (`tan ni la jan li pali` → `({tan ni} la …)`), while Toki Pona reads a prepositional context ("because of this, …" — one of its most common formulas); the same `tan ni` after a verb is structural | `SPEC` §6, `canon/04` §3 | **Structural.** `tan X la S` is a source context ("because of X: S"); the structural reading wins, `jan tan la …` (tan not first) stays a content phrase. |
| 11 | `anu seme` is Toki Pona's yes/no question tag (`ilo li pona anu seme`); OpenPona reads an ordinary phrase choice | `SPEC` §6 | **Declared as convergent.** `X anu seme` is read as a choice between X and the unresolved variable `seme`, which is the question idiom in OpenPona too (record status `unknown`); no special grammar. |

## Test

The conformance corpus includes `toki_pona_compat.jsonl`: sentences OpenPona must reject — either because Toki Pona rejects them, or as declared strictness over valid Toki Pona (marked per case). A positive-direction checker (every RESOLVED case through an independent Toki Pona grammar, agreement at particle level) is **not yet built**; until it exists the claim above stays a design principle.
