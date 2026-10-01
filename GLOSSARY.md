# Glossary

Terms and abbreviations used across this repository. Language terms first, project terms second.

## Language terms

| Term | Meaning |
|---|---|
| **OpenPona** | The 42-token Executable Operational Language defined here. Earlier names `Io Pona`, `Open Pona`, `ilu pona` are superseded. |
| **EOL** | Executable Operational Language: the definition of OpenPona (`SPEC.md` §1). "Executable" means a resolved statement can be bound and executed by an external runtime; the language itself performs no effects. |
| **Toki Pona** | The minimalist constructed language by Sonja Lang (2001) whose words OpenPona reuses. OpenPona is designed not to contradict its grammar; verification status and known departures are in `canon/11`. |
| **token** | One of the 42 canonical words. 36 semantic, 6 structural. |
| **semantic token / vector** | A token read as a direction of meaning (`open`, `lukin`, `pini`). "Vector" is the corpus's word for the token-as-operator view. |
| **structural token / particle** | `li la e tan pi anu`. Five are particles only; `tan` is also a vector (source/cause). |
| **unit** | One semantic token, or `tan`, or a META unit. |
| **head** | The first one or two units of a phrase; every `pi` group modifies it. |
| **`pi` group** | Exactly two units introduced by `pi`; several groups may follow one head. |
| **META / derivative** | Repetition of a unit: `n` copies of `P` mean `D^(n-1)(P)`, a semantic derivative. `D^2(D^2) = D^4`, as snap is the acceleration of acceleration. |
| **address** | The shortest ordered composition that resolves an entity in the current context (`ilo sitelen`). Contextual; may change. |
| **machine identity / `bound_ref`** | The stable UUID or reference an address resolves to at write time. Never changes for a persisted statement. |
| **bound statement / record** | The persisted form of a statement: surface + bindings + `truth_status` + `literals` (`schema/statement.schema.json`). |
| **`jan ni`** | The author of the statement (the speaking agent or person); bound to the record's `actor`. There is no `mi`/`sina`. |
| **truth status / speech-act status** | `observed`, `asserted`, `requested`, `intended`, `hypothesis`, `inferred`, `unknown`, `rejected`. Lives in the record; carrying it in the surface is research (`H-TS`). |
| **RESOLVED / AMBIGUOUS / INVALID / UNRESOLVED** | Parse outcomes: exactly one parse; more than one; none; and, at binding time, no candidate entity. |
| **skeleton** | The compact bracketed rendering of a parse used by the conformance corpus (`conformance/README.md`). |
| **matrix / Sprint / Day** | The 6 × 7 arrangement of the tokens. Rows are also called Sprints (1–6), columns Days (1–7) in older material; `canon/03` uses row/column. Column names are functional (Seed, Map, Explore, Decide, Work, Resonate, Structure) with planets as a mnemonic alias. |
| **`anu 1.1`** | The current canonical token inventory version. `anu 1.0` had the same 36+6 split with an older row-5 ordering. |
| **CANON / RESEARCH / HISTORY / SUPERSEDED** | Status labels: accepted rule; hypothesis with evidence and falsifiers; preserved older material; a formulation displaced by an explicit later decision. |

## Project terms

| Term | Meaning |
|---|---|
| **EOO** | Executable Operational Ontology: a governed decision/action runtime over a typed ontology. OpenPona is a *candidate* surface language for it, not its core (`research/hypothesis_ledger.md` H1–H3, H-OP). |
| **Ontology Language** | The surface syntax in which an EOO's types, links, functions, actions, policies and constraints are written. Whether OpenPona can be one is hypothesis H-OP. |
| **IR** | Intermediate representation: the backend-neutral typed form an Ontology Language must compile to losslessly. |
| **Ontology Machine** | The generic grounding/binding/execution engine explored in `research/ontology_machine_hypotheses.md`. |
| **grounding** | Converting heterogeneous observations (SQL rows, sensor readings, API responses) into stable representations without deciding their domain significance. |
| **authority** | Who may decide and what force a decision has; it does not compute the content of expert judgment (R4.5a). |
| **operational-ontology-poc** | The public repository with the executable side of the EOO rounds: <https://github.com/demithras/operational-ontology-poc>. |
| **Round 2 / Round 3 pack** | Earlier and next EOO hypothesis packs. Round 2 artifacts are listed in `sources/`; the Round 3 pack is not yet published. |
| **HDD** | Appears in the name of a Round 2 source artifact (`operational-ontology-round2-hdd-spec.zip`); its expansion is not recorded in this corpus. |
| **Core42 / Thoth / decan** | The 2026-09-09..10 exploration of 42-cell matrices with Thoth/decan structure. Historical source only; superseded where it conflicts with canon. |
| **LINJA** | A Logseq administrator agent built on OpenPona; the first live producer of OpenPona statements. Lives in a separate repository that is not yet public. |
| **conformance corpus** | `conformance/*.jsonl`: 63 hand-written cases with expected parse outcomes that any parser can be tested against. |
| **tpparser** | A third-party Toki Pona parser (nim-ka) used only as a local Toki Pona oracle in `research/parser_probe/`; unlicensed, so nothing from it is included here. |
