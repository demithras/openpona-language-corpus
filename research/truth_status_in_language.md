# H-TS — Truth/speech-act status inside the surface

**Status: RESEARCH — open hypothesis, not canon (author decision, 2026-09-30).**

## Problem

SPEC §9 keeps the truth/speech-act status (`observed`, `asserted`, `requested`, `intended`, `hypothesis`, `inferred`, `unknown`, `rejected`) in the bound statement, outside the surface text. That is the one piece of core meaning the surface cannot express on its own — exactly the kind of "indispensable sidecar" that `ontology_language_candidate.md` names as a failure condition for the Ontology-Language hypothesis (H-OP).

The language already has the vectors: `lukin` (observe), `sona` (know), `wile` (intend), `seme` (query), `pilin` (evaluate), `kama` (become). `la` already marks context.

## Hypothesis

> The status can be carried in the surface as a context phrase, with zero new tokens and no change to the grammar:

```text
lukin la ilo pali li pini ala      observed:   the build tool did not complete
sona la ilo pali li pini ala       asserted:   (I hold it as known that) the build did not complete
wile la ilo pali li pini           intended:   I want the build to complete
seme la ilo pali li pini           unknown:    whether the build completed is open
pilin la ilo pali li pini ala      hypothesis: my evaluation is that it did not complete
```

`requested` would be `wile la` plus an addressee, `inferred` might be `sona pi kama la`, `rejected` `ala la` — these are the weak spots.

Every line above is a valid Toki Pona sentence (`X la Y`), so the proposal is compatible under `canon/11`.

## What would confirm it

- Every one of the eight statuses has a `la` prefix that (a) is grammatical, (b) reads naturally to a Toki Pona speaker, (c) is distinct from the others, and (d) survives translation back from the bound record without loss.
- A corpus of real LINJA / agent statements written with the prefixes shows no case where the status field and the prefix disagree.

## Falsifiers

- Two statuses collapse into the same prefix in practice (e.g. `sona la` for both `asserted` and `inferred`), so the record still needs the field to disambiguate — the sidecar stays indispensable.
- A prefix changes the ordinary meaning of `la` context for a reader who does not know the convention (`lukin la` read as "in the context of looking" rather than "observed").
- The prefix competes with a genuine context phrase (`ma pali la lukin la …` needs two `la` clauses, which the grammar does not allow).

## Observations so far

- 2026-09-30, `examples/walkthrough_ci_failure.md`: `requested` ("the colleague wants it fixed") and `intended` ("I will fix it") both come out as `wile la …`; only the record's `actor` tells them apart. First falsifier above, hit on the first real story.
- Same file: a status prefix occupies the single `la` slot, so it cannot coexist with a scope context (`ma pali la lukin la …` is INVALID). Third falsifier, also hit.

- 2026-10-01, independent linguist review: in Toki Pona usage `lukin la` reads as "by appearance / visually", not as a verified observation; `wile la` reads as "if desired"; `seme la X` reads as a question. The prefixes do not meet the "reads naturally to a Toki Pona speaker" criterion above.

All hits are recorded, not resolved; the hypothesis stays OPEN until a prefix scheme survives a full story and a Toki Pona reading.

## Consequence if confirmed

The `truth_status` field becomes a derived, machine-readable copy of the prefix rather than an independent source of meaning. SPEC §9 would be rewritten and the change recorded in `history/supersession_ledger.md`. Until then the field is authoritative and the prefix is a convention only.
