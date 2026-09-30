# OpenPona

**Consolidated language corpus — canonical token inventory `anu 1.1`, grammar consolidated through 2026-09-29.**

OpenPona is a **42-token Executable Operational Language (EOL)**: a compact operational language built from **42 canonical tokens** arranged in a **6 × 7 matrix**, whose resolved statements an external runtime can bind and execute. OpenPona **does not contradict Toki Pona**: it may be stricter and may add meaning, but never accepts what Toki Pona rejects. The current kernel contains **36 semantic primitives** and **6 structural operators**. Every token is treated first as a vector/operator/direction; combinations form context-resolved concepts, entity addresses, relations and narratives.

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

The six structural operators are `li la e tan pi anu`. As in Toki Pona, five of them are particles only; `tan` is also an ordinary vector (source/cause) where no structural reading exists.

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

That experiment belongs to a companion EOO hypothesis pack that is not yet published. The executable side of the earlier rounds is public at [demithras/operational-ontology-poc](https://github.com/demithras/operational-ontology-poc).

## Quick start

Read in this order:

1. [`SPEC.md`](SPEC.md)
2. [`canon/01_definition.md`](canon/01_definition.md)
3. [`canon/02_tokens.md`](canon/02_tokens.md)
4. [`canon/03_matrix.md`](canon/03_matrix.md)
5. [`canon/04_grammar.md`](canon/04_grammar.md)
6. [`canon/05_addressing.md`](canon/05_addressing.md)
7. [`canon/06_truth_context_and_execution.md`](canon/06_truth_context_and_execution.md)
8. [`canon/11_toki_pona_compatibility.md`](canon/11_toki_pona_compatibility.md)
9. [`research/hypothesis_ledger.md`](research/hypothesis_ledger.md)
10. [`history/supersession_ledger.md`](history/supersession_ledger.md)

## Tools

- [`CHEATSHEET.md`](CHEATSHEET.md) — the language on one page.
- [`LEARN_OPENPONA.md`](LEARN_OPENPONA.md) — the tutorial; [`examples/walkthrough_ci_failure.md`](examples/walkthrough_ci_failure.md) — one real event end to end.
- [`docs/for-agents.md`](docs/for-agents.md) and [`prompts/openpona_system.md`](prompts/openpona_system.md) — how an agent reads and writes OpenPona, and a system prompt to paste.
- [`GLOSSARY.md`](GLOSSARY.md) — every abbreviation and project term.
- Reference parser: `pip install -e .` then `python -m openpona parse "ilo sitelen li awen"`; `python -m openpona conformance` runs the 63-case oracle in [`conformance/`](conformance/).

## Acknowledgement

OpenPona's 42 tokens are words of **Toki Pona**, the language created by Sonja Lang (2001; *Toki Pona: The Language of Good*, 2014). OpenPona is an independent project that reuses Toki Pona's lexical forms and particles and, by its own canon (`canon/11_toki_pona_compatibility.md`), never contradicts Toki Pona grammar. It is not endorsed by or affiliated with Sonja Lang or the Toki Pona community.

## Repository status

This is a **review-ready corpus**, not a claim that every unresolved parser detail is solved. Where the historical record supports a rule, it is marked `CANON`. Where evidence is promising but incomplete, it is marked `RESEARCH`. Where a previous formulation was displaced, it is marked `SUPERSEDED`.

## License

- Specification, canon, research, history, examples and other text: [CC BY 4.0](LICENSE-CC-BY-4.0.txt).
- Code, tests, schemas and data files (`openpona/`, `tests/`, `schema/`, `data/`, `conformance/`): [MIT](LICENSE-MIT.txt).

See [`LICENSE_POLICY.md`](LICENSE_POLICY.md) for the split.
