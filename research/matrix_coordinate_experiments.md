# Matrix and coordinate experiments

**Status: RESEARCH**

## Problem

The canonical 6×7 arrangement is useful mnemonically, but a stronger claim was proposed: perhaps cell position is itself an address from which token meaning can be reconstructed.

Several progressively stronger models were attacked.

## H5-S — single-header lift

A model where one edge/header supplied the dominant type/operator lift was tested and rejected. Both axes behaved operator-like.

**Status:** REJECTED.

## H6 — semantic intersection

A better model treated each cell as approximately:

```text
T_ij ≈ lexicalize(Row_i ∩ Column_j)
```

This survived initial separability tests better than the single-header model. It explains why the first row and first column can look header-like without actually being literal headers.

**Status:** PLAUSIBLE / PROVISIONALLY SUPPORTED.

## H7-W — external coordinate model, weak form

The strongest surviving weak formulation uses **six external row archetypes × seven external column operations**. The 42 tokens are data at their intersections; the axis labels are meta-labels and are not added to the OpenPona vocabulary.

A double-edge holdout reconstructed **11/11 hidden edge tokens** in the internal experiment.

**Status:** STRONGLY SUPPORTED INTERNALLY for the weak coordinate claim.

## H7-S — exact unique lexical generator

The strong version would require exact unique generation of all 42 lexical items from coordinates alone.

This is not demonstrated. Problems include:

- non-unique lexicalization;
- ambiguous cells such as `sijelo`, `sama`, `ni`, `pini`;
- a weaker Structure column;
- axis ordering not independently proven.

**Status:** NOT DEMONSTRATED.

## Canon consequence

The matrix placement remains canon. The coordinate generator does not.

Use the matrix as an information-bearing semantic address and mnemonic field; do not claim it is a perfect deterministic hash from coordinates to lexical token.
