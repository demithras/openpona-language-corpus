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

## Speaker

There is no first or second person in the token set. **`jan ni` denotes the author of the statement**; its binding is the statement's `actor`. It resolves like any other contextual address and never becomes a grammatical pronoun.

```yaml
surface: jan ni li lukin e ilo sitelen
subject:
  tokens: [jan, ni]
  bound_ref: urn:agent:linja      # = actor
actor: urn:agent:linja
```

## External values

The surface never carries numbers, identifiers, strings or proper names — only the 42 tokens. External values live in the bound statement and the surface points at them by address:

```yaml
surface: ilo pali li pini ala
subject:
  tokens: [ilo, pali]
  bound_ref: pr:678
literals:
  pr_number: 678
truth_status: observed
```

The bound statement is the canonical persisted form; the surface is its view. Keeping values out of the surface is what lets the same sentence resolve to different entities in different contexts without rewriting history.

## Address reconstruction hypothesis

Recent matrix experiments give a strong preliminary signal that an address/coordinate can help reconstruct a hidden token, but exact lexical recovery is not universal. The matrix is therefore useful as an information-bearing address system without being treated as a perfect hash.
