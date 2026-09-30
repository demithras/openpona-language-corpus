# Addressing examples

## Context-relative address

Suppose a project context contains exactly one logging system. The expression:

```text
ilo sitelen
```

may resolve to that system.

Persisted representation:

```yaml
surface_address: [ilo, sitelen]
bound_ref: urn:uuid:8d1b...
resolution_context:
  - project:operational-ontology-poc
resolution_status: RESOLVED
```

In a different project, the same surface expression may resolve to another entity. Historical statements keep their original `bound_ref`.

## Ambiguity

If two tools both match `ilo sitelen` in the same scope:

```yaml
resolution_status: AMBIGUOUS
candidates:
  - urn:uuid:...
  - urn:uuid:...
```

The system must not choose one merely because it was used most recently.

## Narrowing

An explicit context can disambiguate:

```text
ma pali la ilo sitelen
```

The exact context semantics depend on the bound meaning of `ma pali`, but the resolution strategy is deterministic: narrow scope first, widen only as needed.
