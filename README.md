# OpenPona

**A 42-word subset of Toki Pona with a strict grammar, for people and AI agents to write observations, intentions and requests as one-line statements a parser can check and a runtime can bind.** Values (ids, numbers, names) never go in the line; they live in a record next to it.

Who it is for: builders of agents that must log what they saw, what they intend and what they were asked without the three blurring together; people who want a small operational notation they can hold in their head; researchers testing whether such a language can serve as the surface syntax of an executable ontology.

What you can do today: parse and validate statements, test an LLM's OpenPona output against 81 conformance cases, paste a ready-made system prompt. **No runtime ships here** — this repository is the language, its reference parser and its tests.

```text
$ pip install .                       # Python >= 3.11
$ python -m openpona parse "ma pali la ilo pali li pona ala"
RESOLVED
({ma pali} la ({ilo pali} li {pona ala}))
```

```yaml
surface: ma pali la ilo pali li pona ala      # in the project scope, the CI tool is not fit
subject: {tokens: [ilo, pali], bound_ref: pr:678}
literals: {pr_number: 678}
actor: urn:agent:linja
truth_status: observed
```

Read in this order: [`CHEATSHEET.md`](CHEATSHEET.md) (one page) → [`LEARN_OPENPONA.md`](LEARN_OPENPONA.md) (tutorial) → [`examples/walkthrough_ci_failure.md`](examples/walkthrough_ci_failure.md) (one event end to end) → [`SPEC.md`](SPEC.md) and [`canon/`](canon/) for reference → [`GLOSSARY.md`](GLOSSARY.md) for every term.

## The language in three lines

- **42 tokens, 6 × 7 matrix**: 36 semantic tokens read as directions of meaning ("vectors": `open` = initiate, `lukin` = inspect, `pini` = complete) and 6 structural tokens `li la e tan pi anu` that are particles, as in Toki Pona (`tan` is also an ordinary word, source/cause).
- **One grammar**: `context la subject li predicate e object tan source`; three or more words in one concept need `pi`; a repeated unit is a META derivative (`lukin lukin` = inspection as such); one statement per line; `jan ni` = the author of the statement.
- **Ambiguity is a value**: the parser answers RESOLVED, AMBIGUOUS or INVALID and never guesses; binding an address to an entity is a separate step that may return UNRESOLVED.

```text
open     lon      tawa     wile     pali     pilin    li
seme     ma       lukin    sona     ni       kute     la
nasin    sijelo   ilo      lawa     awen     ken      e
jan      ante     kama     sama     ijo      selo     tan
sitelen  linja    pana     toki     tenpo    pini     pi
sike     ale      weka     ala      kulupu   pona     anu
```

## Relationship to Toki Pona

All 42 tokens are words of **Toki Pona**, the language created by Sonja Lang (2001; *Toki Pona: The Language of Good*, 2014; [tokipona.org](https://tokipona.org)). OpenPona reuses the words and the particles and is **designed not to contradict Toki Pona grammar**: it may be stricter (fewer words, mandatory `pi`, no `mi`/`sina`/`o`) and may add meaning inside a phrase, but must never accept what Toki Pona rejects. That claim is verified so far only for rejection cases; an independent review on 2026-10-01 listed seven departures, recorded with their status in [`canon/11_toki_pona_compatibility.md`](canon/11_toki_pona_compatibility.md). OpenPona is an independent project, not endorsed by or affiliated with Sonja Lang or the Toki Pona community.

## Canon, research, history

This repository keeps three things apart and never lets them leak into each other silently:

- `canon/` — accepted language rules and invariants (`SPEC.md` is the entry point);
- `research/` — hypotheses and experiments; every strength label there describes an **internal, unpublished** experiment, and no data or code for them is in this repository;
- `history/` — superseded rules and why they were replaced (`history/supersession_ledger.md`).

The stronger ideas around OpenPona — that the 6 × 7 placement is a generative coordinate system, or that OpenPona can be the Ontology Language of a backend-neutral Executable Operational Ontology (EOO) — are research, not canon. The executable side of the earlier EOO rounds is public at [demithras/operational-ontology-poc](https://github.com/demithras/operational-ontology-poc); the next hypothesis pack is not yet published.

## Tools

- Reference parser: `python -m openpona parse "…"` (RESOLVED / AMBIGUOUS / INVALID, skeletons, located error messages); `python -m openpona conformance` runs the 81-case oracle in [`conformance/`](conformance/).
- [`docs/for-agents.md`](docs/for-agents.md) — how an agent reads and writes OpenPona; [`prompts/openpona_system.md`](prompts/openpona_system.md) — a system prompt to paste.
- `make check` — unit tests, conformance, and a test that parses every OpenPona line in every `.md` file (so the documentation cannot drift from the parser).

## Status

Version 0.2.0, single author, grammar consolidated through 2026-10-01 after an independent five-lens review (`CHANGELOG.md`). Open decisions are listed in `canon/11` ("Known departures"). Contributions follow [`CONTRIBUTING.md`](CONTRIBUTING.md) and the agent rules in [`AGENTS.md`](AGENTS.md).

## License

- Text (specification, canon, research, history, examples, guides): [CC BY 4.0](LICENSE-CC-BY-4.0.txt).
- Code, tests, schemas and data (`openpona/`, `tests/`, `schema/`, `data/`, `conformance/`, `Makefile`, `pyproject.toml`): [MIT](LICENSE-MIT.txt).

See [`LICENSE`](LICENSE) and [`LICENSE_POLICY.md`](LICENSE_POLICY.md).
