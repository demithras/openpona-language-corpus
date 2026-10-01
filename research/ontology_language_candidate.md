# Candidate: OpenPona as Ontology Language

**Status: OPEN HYPOTHESIS — do not treat as canon.**

For OpenPona to qualify as the surface Ontology Language of the target EOO, it must be able to represent, without hidden semantic sidecars:

- ObjectType / object identity
- Property / typed value constraints
- LinkType / cardinality
- Interface / polymorphism
- Function / pure or read-oriented logic
- Action / governed side effect
- Policy
- Authority / permissions
- Observation / event
- Version / migration reference
- Constraint / invariant

It must also preserve the hard distinction:

```text
Function ≠ Action
```

and compile to a backend-neutral IR with enough information for deterministic round-trip equivalence.

The hypothesis is rejected if core meaning repeatedly escapes into YAML/Rego/FGA/code that is semantically indispensable, or if new domain primitives must be added to the 42-token kernel.

The executable protocol belongs to the companion EOO Round 3 pack, which is not yet published.
