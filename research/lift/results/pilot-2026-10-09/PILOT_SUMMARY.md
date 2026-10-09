PILOT - EXPLORATORY, NOT CONFIRMATORY

# Lift pilot summary (N2)

Source: results.json, ingest_log.json, report.md, run_log.jsonl in lift-pilot-2026-10-09 (values copied, not recomputed). Qwen 3.5 vendor was dropped mid-collection by author decision 2026-10-09; its 3 collected replies were moved to responses_excluded_qwen/ and are not analysed.

## Limitation (verbatim, PILOT_PROTOCOL.md line 7)

> The Lift labels and the 42 cell tokens have been canonical on public GitHub since 2026-10-09. Model training exposure or browsing exposure therefore **cannot be excluded** for any vendor, and a good score does not show independent reconstruction. The post-task familiarity answer is **reported** for every participant and is **not used to exclude** anyone silently; any exclusion is a logged, named decision in `ingest_log.json`.

## Ingest

| category | count | ids / reason |
|---|---|---|
| accepted | 24 | p002, p004, p005, p006, p007, p008, p011, p015, p016, p017, p019, p021, p024, p025, p026, p027, p028, p029, p030, p032, p033, p034, p035, p036 |
| rejected | 0 | none (ingest_log excluded=[], flags=[]) |
| missing (allocated, no response) | 12 | p001, p003, p009, p010, p012, p013, p014, p018, p020, p022, p023, p031; includes 3 qwen allocations (p001, p003, p009) whose replies were dropped with the qwen vendor |

Freeze verified: True. Seed 20261009, bootstrap reps 10000, null reps 10000. Abstention counts as wrong.

## Per arm (results.json `arms`, participant-level bootstrap 95% CI)

| arm | n participants | interior 30 mean | interior 30 CI | interior w/o C7 (25) mean | interior w/o C7 CI | C7 (5) mean | C7 CI | edge 12 mean | edge 12 CI |
|---|---|---|---|---|---|---|---|---|---|
| external | 6 | 0.04444444333333333 | [0.005555555, 0.08888888666666667] | 0.04 | [0.006666666666666667, 0.08] | 0.06666666666666667 | [0.0, 0.20000000000000004] | 0.27777777666666664 | [0.15277777833333334, 0.3611111116666667] |
| embedded | 6 | 0.0 | [0.0, 0.0] | 0.0 | [0.0, 0.0] | 0.0 | [0.0, 0.0] | 0.5 | [0.16666666666666666, 0.8333333333333334] |
| generic | 6 | 0.005555555 | [0.0, 0.016666665] | 0.006666666666666667 | [0.0, 0.02] | 0.0 | [0.0, 0.0] | 0.0 | [0.0, 0.0] |
| shuffled | 6 | 0.016666666666666666 | [0.0, 0.03888889] | 0.02 | [0.0, 0.04666666666666667] | 0.0 | [0.0, 0.0] | 0.0 | [0.0, 0.0] |

## Per arm x vendor (per-participant values from results.json `participants`; counts of correct cells)

Each arm x vendor cell holds 3 participants (count from the participant list). results.json has no per-cell mean, so none is shown here.

| arm | vendor | participant | interior 30 | interior w/o C7 25 | C7 5 | edge 12 | all 42 | abstained | familiarity |
|---|---|---|---|---|---|---|---|---|---|
| embedded | haiku | p016 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 42 | unsure |
| embedded | haiku | p029 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 42 | unsure |
| embedded | haiku | p034 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 42 | unsure |
| embedded | sonnet | p011 | 0/30 | 0/25 | 0/5 | 12/12 | 12/42 | 30 | no |
| embedded | sonnet | p021 | 0/30 | 0/25 | 0/5 | 12/12 | 12/42 | 30 | no |
| embedded | sonnet | p025 | 0/30 | 0/25 | 0/5 | 12/12 | 12/42 | 30 | no |
| external | haiku | p024 | 3/30 | 3/25 | 0/5 | 4/12 | 7/42 | 0 | no |
| external | haiku | p033 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 42 | unsure |
| external | haiku | p035 | 0/30 | 0/25 | 0/5 | 3/12 | 3/42 | 0 | no |
| external | sonnet | p004 | 1/30 | 1/25 | 0/5 | 4/12 | 5/42 | 0 | no |
| external | sonnet | p007 | 0/30 | 0/25 | 0/5 | 5/12 | 5/42 | 0 | no |
| external | sonnet | p027 | 4/30 | 2/25 | 2/5 | 4/12 | 8/42 | 0 | no |
| generic | haiku | p017 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 42 | no |
| generic | haiku | p028 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 42 | unsure |
| generic | haiku | p032 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 42 | no |
| generic | sonnet | p006 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 42 | no |
| generic | sonnet | p015 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 42 | unsure |
| generic | sonnet | p036 | 1/30 | 1/25 | 0/5 | 0/12 | 1/42 | 0 | no |
| shuffled | haiku | p002 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 42 | unsure |
| shuffled | haiku | p008 | 1/30 | 1/25 | 0/5 | 0/12 | 1/42 | 0 | no |
| shuffled | haiku | p019 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 0 | no |
| shuffled | sonnet | p005 | 2/30 | 2/25 | 0/5 | 0/12 | 2/42 | 0 | no |
| shuffled | sonnet | p026 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 0 | no |
| shuffled | sonnet | p030 | 0/30 | 0/25 | 0/5 | 0/12 | 0/42 | 10 | no |

Interior mean by vendor (results.json `arms.*.by_vendor_interior_mean`):

| arm | haiku | sonnet |
|---|---|---|
| external | 0.03333333333333333 | 0.055555553333333334 |
| embedded | 0.0 | 0.0 |
| generic | 0.0 | 0.01111111 |
| shuffled | 0.01111111 | 0.022222223333333332 |

## Model ids (from meta files)

| vendor | alias / backend | model_id | temperature | system prompt |
|---|---|---|---|---|
| sonnet | claude -p --model sonnet | claude-sonnet-5-5 | default | You are a helpful assistant. |
| haiku | claude -p --model haiku | claude-haiku-5-5 | default | You are a helpful assistant. |
| qwen (dropped, not analysed) | ollama /api/chat | qwen3.5:9b | - | - |

## Familiarity answers (reported, not used to exclude)

| arm | no | unsure | yes |
|---|---|---|---|
| external | 5 | 1 | 0 |
| embedded | 3 | 3 | 0 |
| generic | 4 | 2 | 0 |
| shuffled | 5 | 1 | 0 |

## External vs controls, interior w/o C7 (results.json `contrasts`)

- external_minus_embedded_interior_no_c7: difference 0.04, CI [0.006666666666666667, 0.08]
- external_minus_generic_interior_no_c7: difference 0.03333333333333333, CI [0.0, 0.07333333333333333]
- external_minus_shuffled_interior_no_c7: difference 0.02, CI [-0.020000000000000004, 0.06666666666666667]

Verdict per the CI only: external beats embedded on interior w/o C7 (CI lower bound above 0); the CIs for generic and shuffled include 0.


## Orchestrator notes (added after analysis, numbers copied from results.json / model_level.json)

### Abstention by model and arm (cells left empty, out of 42, per run)

| model | external | embedded | generic | shuffled |
|---|---|---|---|---|
| haiku | 0, 42, 0 | 42, 42, 42 | 42, 42, 42 | 42, 0, 0 |
| sonnet | 0, 0, 0 | 30, 30, 30 | 42, 42, 0 | 0, 0, 10 |

Abstention counts as wrong. Neutral labels (generic) mostly produced full abstention, and Sonnet answered only the 12 edge cells under embedded labels. The arm contrasts therefore partly measure willingness to answer, not knowledge. The main study should use forced choice or also report accuracy on answered cells.

### Model-level contrasts (unit = model; run-level CIs above are descriptive only)

Sector interior_no_c7 (25 cells):
| model | arm | mean | n_runs |
|---|---|---|---|
| haiku | embedded | 0.000 | 3 |
| haiku | external | 0.040 | 3 |
| haiku | generic | 0.000 | 3 |
| haiku | shuffled | 0.013 | 3 |
| sonnet | embedded | 0.000 | 3 |
| sonnet | external | 0.040 | 3 |
| sonnet | generic | 0.013 | 3 |
| sonnet | shuffled | 0.027 | 3 |

| contrast | per-model | k>0 / k<0 / ties of M | sign-test p (1-sided) | mean | model-bootstrap 95% CI |
|---|---|---|---|---|---|
| external_minus_embedded_interior_no_c7 | haiku: +0.040, sonnet: +0.040 | 2 / 0 / 0 of 2 | 0.250 | 0.040 | [0.040, 0.040] |
| external_minus_generic_interior_no_c7 | haiku: +0.040, sonnet: +0.027 | 2 / 0 / 0 of 2 | 0.250 | 0.033 | [0.027, 0.040] |
| external_minus_shuffled_interior_no_c7 | haiku: +0.027, sonnet: +0.013 | 2 / 0 / 0 of 2 | 0.250 | 0.020 | [0.013, 0.027] |

- M=2 < 5: the bootstrap interval is not interpretable as a population CI.
- Minimum attainable one-sided sign-test p with 2 non-tied models is 0.25.

