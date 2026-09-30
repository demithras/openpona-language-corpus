# 06 — Truth, context, grounding and execution

**Status: CANON architectural boundary.**

## Speech-act/truth status

OpenPona text must be accompanied by operational status where the distinction matters:

- `observed`
- `asserted`
- `requested`
- `intended`
- `hypothesis`
- `inferred`
- `unknown`
- `rejected`

An intended action is not evidence that the action happened. A command returning success is not evidence that the world reached the expected state.

## Context

`la` makes validity/context explicit, while runtime context can also be inherited from parent structures such as project → task → note or graph ancestors.

Context narrows meaning; it must not alter immutable historical bindings.

## Grounding separation

A grounding adapter may convert heterogeneous observations into stable representations. It should not silently hide the domain decision rule when an experiment claims semantic/grounding separation.

A useful boundary is:

```text
Grounding: "what observation does this source report?"
Semantics: "what does this relation mean in the model?"
Policy/judgment: "what should be done about it?"
```

Experiments on a generic Ontology Machine supported this separation in small examples, but the result is not proof that every domain can be grounded without domain-specific judgment.

## Authority separation

Authority structure can determine who is allowed to make a decision and what operational force a decision has. It does not necessarily compute the content of discretionary expert judgment.

This boundary survived adversarial examples such as governance systems where authorized maintainers/chairs must still apply substantive expertise.

## Execution

OpenPona itself does not execute side effects. An external runtime may map a resolved expression to functions/actions, but must independently enforce identity, authority, policy, preconditions, idempotency, evidence and observed outcomes.
