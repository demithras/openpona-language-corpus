# META/repetition examples

Let `P` denote a valid completed semantic unit.

```text
P
P P
P P P
P P P P
```

These correspond conceptually to:

```text
P
D(P)
D^2(P)
D^3(P)
```

The surface may be grouped for parsing convenience, but derivative depth must be preserved.

A critical parser rule is that META recognition happens before ordinary structural interpretation. Repeated structural-looking units cannot be split prematurely if the repetition itself forms a valid META unit.
