# OpenPona

**Consolidated language corpus — canonical token inventory `anu 1.1`, grammar consolidated through 2026-09-29.**

OpenPona is a compact operational language built from **42 canonical tokens** arranged in a **6 × 7 matrix**. The current kernel contains **36 semantic primitives** and **6 structural operators**. Every token is treated first as a vector/operator/direction; combinations form context-resolved concepts, entity addresses, relations and narratives.

This repository has two goals:

1. preserve the current OpenPona canon without silently importing superseded ideas;
2. make the language precise enough to test, rather than assume, stronger claims about OpenPona — especially whether it can serve as the Ontology Language of a backend-neutral Executable Operational Ontology.

## What is canonical here

The authoritative entry point is [`SPEC.md`](SPEC.md). The canonical 42-token matrix is:

```text
open     lon      tawa     wile     pali     pilin    li
seme     ma       lukin    sona     ni       kute     la
nasin    sijelo   ilo      lawa     awen     ken      e
jan      ante     kama     sama     ijo      selo     tan
sitelen  linja    pana     toki     tenpo    pini     pi
sike     ale      weka     ala      kulupu   pona     anu
```

The six structural operators are `li la e tan pi anu`. They remain vectors in their own right, but have structural force when used between semantic expressions in grammatical position.

## Canon vs research

This repository deliberately separates:

- `canon/` — accepted language rules and invariants;
- `research/` — hypotheses and experiments whose results must not be promoted to canon automatically;
- `history/` — superseded matrices, old interpretations, and why they were superseded;
- `examples/` — normative and exploratory examples;
- `tests/` — executable integrity checks for the corpus itself.

A key example: the **6 × 7 placement is canon**; the stronger claim that the matrix is a unique generative coordinate system is **not** canon. Recent experiments provide substantial evidence that row/column location carries semantic information, but exact unique generation of all 42 lexical tokens remains unproven.

## Current architectural position

OpenPona is **not assumed to be the core representation of Executable Operational Ontology**. Earlier tests weakened that claim. The current stronger research posture is:

> OpenPona is a candidate human/agent operational language and a candidate Ontology Language. Whether it can losslessly express a typed, executable ontology must be falsified experimentally.

The companion Round 3 hypothesis pack contains that experiment.

## Quick start

Read in this order:

1. [`SPEC.md`](SPEC.md)
2. [`canon/01_definition.md`](canon/01_definition.md)
3. [`canon/02_tokens.md`](canon/02_tokens.md)
4. [`canon/03_matrix.md`](canon/03_matrix.md)
5. [`canon/04_grammar.md`](canon/04_grammar.md)
6. [`canon/05_addressing.md`](canon/05_addressing.md)
7. [`canon/06_truth_context_and_execution.md`](canon/06_truth_context_and_execution.md)
8. [`research/hypothesis_ledger.md`](research/hypothesis_ledger.md)
9. [`history/supersession_ledger.md`](history/supersession_ledger.md)

## Repository status

This is a **review-ready corpus**, not a claim that every unresolved parser detail is solved. Where the historical record supports a rule, it is marked `CANON`. Where evidence is promising but incomplete, it is marked `RESEARCH`. Where a previous formulation was displaced, it is marked `SUPERSEDED`.

Before public release, choose explicit licenses for the specification and code; see [`LICENSE_POLICY.md`](LICENSE_POLICY.md).
