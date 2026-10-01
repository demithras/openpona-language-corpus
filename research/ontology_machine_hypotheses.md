# OpenPona Ontology Machine hypothesis history

**Status: RESEARCH — small POCs and adversarial reasoning, not canon.**

**Evidence status (added 2026-10-01 after independent review):** every strength label in this file describes an internal, unpublished experiment from the 2026-09 research conversations. No data, method, baseline or code for them is in this repository. Read each label as *reported, unpublished*; nothing here is reproducible from the repository alone.

These experiments explored whether OpenPona semantic expressions could remain stable while a generic machine handled grounding, binding and execution.

## H11-R — reflexive semantic graph notation

Working model:

```text
semantic vectors → units
structural tokens → relations
repetition → semantic derivatives/meta
linear OpenPona surface → reflexive semantic graph
```

This model motivated the later META algebra. A remaining risk was reliable serialization/parsing of completed phrase boundaries under deeper graph patterns.

**Status:** conceptually useful; not a proof of a complete ontology language.

## H12 — generic matcher without new semantic vectors

A first POC explored typing, properties, authorization, constraints, interfaces, actions, transactions, provenance, functions and automation using a generic matcher without adding new OpenPona semantic vectors.

**Observed result:** the synthetic POC survived with zero new semantic vectors.

**Remaining risk:** complex graph-pattern/binding serialization and the possibility that genericity was achieved by pushing essential semantics into the machine rather than the language.

This is one reason the planned Round 3 pack (not yet published) audits indispensable sidecars/IR meaning explicitly (its hypothesis H23).

## H14 — semantic/grounding separation

A small executable experiment used one semantic rule over different grounded sources (reported examples included SQL, sensor and API inputs) and applied a generic machine across several synthetic domains.

Reported result:

```text
semantic rule changed: no
domain-specific `if` in generic machine: 0 in the tested cases
```

**Status:** survived the first POC; scope limited.

It supports the possibility of separating stable semantics from transport/source grounding, not the claim that every real domain can be grounded without judgment.

## H15 — grounding purity

Stronger claim:

> grounding normalizes what reality/source reports but does not decide the domain significance of that observation.

Falsifiers include:

- business thresholds or policy hidden in an adapter;
- domain classification performed during supposedly neutral grounding;
- backend changes forcing the semantic rule to change;
- adapters containing the substantive decision the machine claims to compute.

**Status:** open / boundary hypothesis.

## R4.4 — authority predicts substantive judgment

Strong formulation: once the authority graph is known, a generic machine can compute the correct content of the authority's discretionary decision.

Adversarial examples from IETF rough-consensus governance and Linux maintainership showed the boundary: procedural authority can be explicit while the actual decision still depends on substantive technical judgment.

**Status:** REJECTED in the strong predictive form.

## R4.5a — authority determines operational force

Narrower surviving claim:

> the machine can compute whether a decision was made by a recognized authority within scope/delegation/review rules and therefore has recognized operational force, without claiming to compute whether the authority's substantive judgment was wise/correct.

**Status:** survived the adversarial governance examples as the preferred boundary.

## Consequence for OpenPona

OpenPona can describe authority, provenance and decision relations without pretending that a compact semantic language eliminates expertise. This boundary is part of the current runtime philosophy and must be preserved in any EOO compilation experiment.
