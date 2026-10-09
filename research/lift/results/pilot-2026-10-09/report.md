# PILOT - EXPLORATORY, NOT CONFIRMATORY

Participants analysed: 24; excluded at ingest: 0; allocated without response: 12. Freeze verified. Abstention counts as wrong. Bootstrap/null seed 20261009.

## Per arm (mean of participant Top-1, participant-level bootstrap 95% CI)

| arm | n | interior 30 | interior 95% CI | interior w/o C7 (25) | interior w/o C7 95% CI | C7 (5) | C7 95% CI | edge 12 | all 42 |
|---|---|---|---|---|---|---|---|---|---|
| external | 6 | 0.044 | [0.006, 0.089] | 0.040 | [0.007, 0.080] | 0.067 | [0.000, 0.200] | 0.278 | 0.111 |
| embedded | 6 | 0.000 | [0.000, 0.000] | 0.000 | [0.000, 0.000] | 0.000 | [0.000, 0.000] | 0.500 | 0.143 |
| generic | 6 | 0.006 | [0.000, 0.017] | 0.007 | [0.000, 0.020] | 0.000 | [0.000, 0.000] | 0.000 | 0.004 |
| shuffled | 6 | 0.017 | [0.000, 0.039] | 0.020 | [0.000, 0.047] | 0.000 | [0.000, 0.000] | 0.000 | 0.012 |

## Per participant

| participant | vendor | arm | interior /30 | edge /12 | all /42 | abstained | null p (interior) | familiarity |
|---|---|---|---|---|---|---|---|---|
| p002 | haiku | shuffled | 0 | 0 | 0 | 42 | 1.0 | unsure |
| p004 | sonnet | external | 1 | 4 | 5 | 0 | 0.5050495 | no |
| p005 | sonnet | shuffled | 2 | 0 | 2 | 0 | 0.15838416 | no |
| p006 | sonnet | generic | 0 | 0 | 0 | 42 | 1.0 | no |
| p007 | sonnet | external | 0 | 5 | 5 | 0 | 1.0 | no |
| p008 | haiku | shuffled | 1 | 0 | 1 | 0 | 0.5090491 | no |
| p011 | sonnet | embedded | 0 | 12 | 12 | 30 | 1.0 | no |
| p015 | sonnet | generic | 0 | 0 | 0 | 42 | 1.0 | unsure |
| p016 | haiku | embedded | 0 | 0 | 0 | 42 | 1.0 | unsure |
| p017 | haiku | generic | 0 | 0 | 0 | 42 | 1.0 | no |
| p019 | haiku | shuffled | 0 | 0 | 0 | 0 | 1.0 | no |
| p021 | sonnet | embedded | 0 | 12 | 12 | 30 | 1.0 | no |
| p024 | haiku | external | 3 | 4 | 7 | 0 | 0.03779622 | no |
| p025 | sonnet | embedded | 0 | 12 | 12 | 30 | 1.0 | no |
| p026 | sonnet | shuffled | 0 | 0 | 0 | 0 | 1.0 | no |
| p027 | sonnet | external | 4 | 4 | 8 | 0 | 0.00639936 | no |
| p028 | haiku | generic | 0 | 0 | 0 | 42 | 1.0 | unsure |
| p029 | haiku | embedded | 0 | 0 | 0 | 42 | 1.0 | unsure |
| p030 | sonnet | shuffled | 0 | 0 | 0 | 10 | 1.0 | no |
| p032 | haiku | generic | 0 | 0 | 0 | 42 | 1.0 | no |
| p033 | haiku | external | 0 | 0 | 0 | 42 | 1.0 | unsure |
| p034 | haiku | embedded | 0 | 0 | 0 | 42 | 1.0 | unsure |
| p035 | haiku | external | 0 | 3 | 3 | 0 | 1.0 | no |
| p036 | sonnet | generic | 1 | 0 | 1 | 0 | 0.51324868 | no |

## External minus control, interior and interior w/o C7 (descriptive)

- external_minus_embedded_interior: 0.044 [0.006, 0.089]
- external_minus_generic_interior: 0.039 [0.000, 0.083]
- external_minus_shuffled_interior: 0.028 [-0.017, 0.078]
- external_minus_embedded_interior_no_c7: 0.040 [0.007, 0.080]
- external_minus_generic_interior_no_c7: 0.033 [0.000, 0.073]
- external_minus_shuffled_interior_no_c7: 0.020 [-0.020, 0.067]

## Per-cell correct counts by arm (rows R1-R6, columns C1-C7; full confusion in results.json)

### external (n=6)

| | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|
| R1 | 2 | 0 | 1 | 0 | 2 | 0 | 0 |
| R2 | 3 | 0 | 2 | 0 | 0 | 1 | 1 |
| R3 | 3 | 0 | 1 | 0 | 0 | 0 | 0 |
| R4 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| R5 | 4 | 0 | 0 | 0 | 0 | 0 | 1 |
| R6 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |

### embedded (n=6)

| | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|
| R1 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| R2 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| R3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| R4 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| R5 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| R6 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |

### generic (n=6)

| | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|
| R1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R3 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| R4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### shuffled (n=6)

| | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|
| R1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R4 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| R5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R6 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |

## Familiarity (reported, not used to exclude)

```
{"embedded": {"no": 3, "unsure": 3}, "external": {"no": 5, "unsure": 1}, "generic": {"no": 4, "unsure": 2}, "shuffled": {"no": 5, "unsure": 1}}
```

## Limits

- Abstention counts as incorrect.
- Familiarity answers are reported, never used to exclude.
- The null is a label-permutation (label-symmetry) null per participant, not an arm test.
- Lift labels have been public on GitHub since 2026-10-09: training/browsing exposure cannot be excluded.
- Pilot only: it sizes the main study and is not a confirmatory sample.
