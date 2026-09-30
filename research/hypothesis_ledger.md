# OpenPona research hypothesis ledger

**Status: RESEARCH — not canon.**

This ledger consolidates the main hypotheses that were tested or discussed separately from the language definition. It exists to prevent successful rhetoric from being mistaken for evidence.

| ID | Claim | Current status | Evidence/interpretation |
|---|---|---|---|
| H1 | OpenPona should be the core language of Executable Operational Ontology | **STRONGLY UNSUPPORTED** | EOO behavior was implemented and tested independently; no need for OpenPona in the core was demonstrated. |
| H2 | EOO should be compiled from OpenPona | **UNSUPPORTED** | The operational ontology POC succeeded without such a compilation dependency. |
| H3 | EOO can be architecturally independent of OpenPona | **SUPPORTED** | Current architecture treats OpenPona as separable from the operational runtime. |
| H5 | Internalized OpenPona may be useful to a human/agent operating across contexts | **STRONG WORKING HYPOTHESIS** | Supported by design fit and simulations, not yet by controlled human evidence. |
| H6 | The 42 tokens act as reusable cognitive/operational operators | **SIMULATION-SUPPORTED; HUMAN-UNPROVEN** | Cross-domain compositional use survived synthetic tests, but cognition claims require human evidence. |
| H7 | The 42 tokens are independent arbitrary primitives | **LIKELY FALSE / WEAKENED** | Matrix experiments show meaningful row/column structure. |
| H8 | The 6×7 matrix carries semantic information | **SUBSTANTIALLY SUPPORTED** | Canonical placement outperforms random expectation on several reconstruction/separability probes, though not every metric. |
| H9 | Token address/coordinate supports reconstruction | **STRONG PRELIMINARY SIGNAL** | Holdout experiments recovered edge tokens well; exact lexical recovery is not universal. |
| H10 | The canonical matrix is uniquely optimal | **UNPROVEN** | Coarse optimization found alternate layouts that scored better on some formalized metrics. |
| H-OP | OpenPona can be the Ontology Language of a Palantir-class EOO | **OPEN — NEXT EXPERIMENT** | Must express typed ontology primitives and compile losslessly to backend-neutral IR without adding primitives per domain. |

## Important interpretation

The negative H1/H2 results do **not** imply that OpenPona has no value. They narrow the claim:

```text
technical necessity for EOO core     → unsupported
independent agent/human utility       → plausible / working
Ontology Language candidacy           → open and falsifiable
matrix/address information             → substantially stronger than arbitrary-token model
```

This is the current research posture.

## Ontology Machine detail

See `ontology_machine_hypotheses.md` for the H11-R/H12/H14/H15 and R4.x grounding/authority experiments.
