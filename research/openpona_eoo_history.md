# OpenPona ↔ Executable Operational Ontology: research history

**Status: RESEARCH/HISTORY**

## Phase 1 — candidate semantic core

OpenPona was initially explored as a compact language that might directly ground a graph/ontology runtime. This produced useful ideas: operations before nouns, explicit context, addresses, authority relations, reality checks and event narrative.

## Phase 2 — separation pressure

The operational ontology POC demonstrated that a governed decision/action loop can be implemented without OpenPona. This weakened the claim that EOO must be written in or compiled from OpenPona.

The engineering result was a cleaner boundary:

```text
OpenPona value ≠ proof of EOO dependency
```

## Phase 3 — Ontology Machine experiments

Grounding and execution were moved into a generic Ontology Machine. Small executable experiments supported a separation in which:

- grounding normalizes observations;
- semantic rules remain stable across backends/domains;
- authority can determine operational force;
- substantive discretionary judgment may remain external.

The strong claim that a generic authority graph predicts expert judgment was partially falsified by governance examples such as IETF rough consensus and Linux maintainer decisions. The surviving rule is narrower: authority can validate **who may decide and whether a decision has force**, not necessarily **what the expert decision should be**.

## Phase 4 — current question

The current architecture no longer asks whether EOO depends on OpenPona. It asks:

> Can OpenPona serve as the **surface Ontology Language** for a backend-neutral Palantir-class EOO while a typed IR and Engine remain independent?

This claim is materially stronger than "OpenPona is useful notation" and materially weaker than "EOO must be OpenPona". It is the primary candidate-language experiment in the Round 3 pack.
