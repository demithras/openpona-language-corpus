# 05 — Contextual addressing

**Status: CANON model; reconstruction strength remains RESEARCH.**

## Identity vs address

OpenPona separates stable identity from human/agent-readable address.

```text
machine identity = stable reference / UUID
OpenPona address = shortest ordered semantic expression that resolves uniquely in context
```

This allows the same compact expression to resolve differently in different domains without rewriting persisted history.

## Resolution algorithm

Given expression `A` and context stack `C0..Cn`:

1. search the narrowest explicit context;
2. search parent/ancestor contexts outward;
3. search domain/project scope;
4. search wider graph scope if policy permits;
5. if exactly one candidate remains, bind it;
6. if zero remain, return `UNRESOLVED`;
7. if more than one remains, return `AMBIGUOUS`.

No probabilistic guess may silently become a historical binding.

## Persistence rule

Persist both:

```yaml
surface_address: [ilo, sitelen]
bound_ref: uuid:...
resolution_context: [...]
```

A later change in context may change what `ilo sitelen` would resolve to *now*, but must not change what the historical statement referred to.

## Address reconstruction hypothesis

Recent matrix experiments give a strong preliminary signal that an address/coordinate can help reconstruct a hidden token, but exact lexical recovery is not universal. The matrix is therefore useful as an information-bearing address system without being treated as a perfect hash.
