# Exploratory EOO examples

**Status: EXPLORATORY, not canonical Ontology Language syntax.**

These sketches exist only to explain what the companion experiment must test.

A future OpenPona Ontology Language would need to distinguish at least:

```text
ObjectType
Property
LinkType
Interface
Function
Action
Policy
Authority
Observation
Version
Constraint
```

The current language has vectors that can contribute to these meanings (`ijo`, `linja`, `pali`, `lawa`, `lukin`, `sona`, `ken`, `tenpo`, etc.), but a usable Ontology Language requires **unambiguous typed compilation**, not poetic resemblance.

For example, the following conceptual distinction must survive compilation:

```text
Function: computes risk score, no business side effect
Action: changes work-order priority, governed business side effect
```

If OpenPona can only express that difference by placing indispensable type information in an external YAML sidecar, the strong Ontology-Language hypothesis is weakened or rejected.
