# 11 — Toki Pona compatibility

**Status: CANON principle (author decision, 2026-09-30).**

OpenPona reuses Toki Pona's lexical forms and particles. It must not contradict Toki Pona.

## The rule

> Every valid OpenPona statement is a valid Toki Pona sentence, and its OpenPona parse coincides with a Toki Pona parse at the level of particle structure.

"Particle structure" means the boundaries drawn by `la`, `li`, `e`, `pi`, `anu` and the preposition `tan`. Inside a content phrase OpenPona may add structure that Toki Pona does not have (META units, head/group semantics); at the particle level the two parses must agree.

## What OpenPona may do

| Allowed | Example |
|---|---|
| be stricter: fewer words | `mi`, `sina`, `o`, `en`, `mute`, `kalama`, `nimi` are not OpenPona tokens |
| be stricter: require `pi` where Toki Pona merely allows it | `jan ilo sona` is valid Toki Pona and INVALID OpenPona |
| add meaning inside a phrase | `ilo ilo` is emphasis in Toki Pona usage and `D(ilo)` in OpenPona; the syntax is the same |
| fix conventions Toki Pona leaves to the speaker | one statement per line; each `pi` group exactly two units |

## What OpenPona may not do

| Forbidden | Consequence |
|---|---|
| accept a sentence Toki Pona rejects | `li pali`, `la jan li pali`, `jan pi li pali`, `sona pi lawa` are INVALID |
| give a particle a content reading Toki Pona does not give it | `li la e pi anu` are never vectors; only `tan` is (as in Toki Pona) |
| draw a particle boundary Toki Pona would not draw | precedence is Toki Pona's: `la` → `li` → `e`/`tan` → `anu` → `pi` |

## Grey zones

Where Toki Pona usage is itself divided, OpenPona picks one reading and records it here:

- **multiple `pi` groups** — accepted; each group modifies the head. Toki Pona speakers often avoid this shape; prefer one group where meaning allows.
- **`anu` between whole clauses** — not accepted until Toki Pona usage is confirmed (research).

## Test

The conformance corpus includes `toki_pona_compat.jsonl`: sentences that Toki Pona rejects and OpenPona must therefore reject. A future compatibility checker should run every RESOLVED OpenPona case through an independent Toki Pona grammar; agreement at particle level is the pass condition.
