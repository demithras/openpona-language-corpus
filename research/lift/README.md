# Lift experiment scaffold (stdlib-only)

**For prospective experimental setup, not a claim of result.** External axes were approved as **research coordinates** by the author on 2026-10-08. This harness contains known reference answers solely to verify and score later, independently obtained predictions.

## Commands

From the package root:

```bash
python research/lift/blind_experiment.py validate
python -m unittest discover -s research/lift/tests -v
python research/lift/blind_experiment.py prepare --condition external --seed 20261008 --out-dir /tmp/lift-external
python research/lift/blind_experiment.py prepare --condition embedded --seed 20261008 --out-dir /tmp/lift-embedded
python research/lift/blind_experiment.py prepare --condition generic --seed 20261008 --out-dir /tmp/lift-generic
python research/lift/blind_experiment.py prepare --condition shuffled --seed 20261008 --out-dir /tmp/lift-shuffled
# Fill the generated submission_template.json in a separate blinded evaluation.
python research/lift/blind_experiment.py score --gold /tmp/lift-external/private_gold.json --answers submitted.json --out score.json
python research/lift/blind_experiment.py null --gold /tmp/lift-external/private_gold.json --answers submitted.json --reps 10000 --seed 20261008 --out null.json
```

`prepare` creates: `public_prompt.json` (coordinate labels, candidate list, NO cell-token mapping), `submission_template.json` (blank tokens), and `private_gold.json` (truth mapping, keep secret). **Do not distribute output directory as-is.** Separate gold and public files before human/agent use. The shared package itself reveals the table and cannot be a blind participant resource.

## Validation (TP-14)

`validate [PROFILE.json] [--matrix data/matrix.csv]` checks the profile's 42 cell tokens against the repo `data/matrix.csv` (bijection: 42 cells, 42 unique tokens, 6 rows, 7 columns, structural column `li la e tan pi anu`, row five exactly `sitelen linja pana toki tenpo pini pi`). It exits 0 on PASS, and exits 3 printing `DRIFT[<kind>]` on stderr for: `missing_slot`, `duplicate_token`, `structural_column_drift`, `row_five_drift`, `matrix_token_mismatch` (plus id/label kinds). The older row-five order `sitelen linja tenpo toki pana pini pi` is an unverified historical variant, recorded only in `research/externalized_lift_coordinates.md`; the validator rejects it as `row_five_drift`.

Public exports keep labels in `row_labels` / `column_labels` lists and trial records carry only indices. The `embedded` arm deliberately uses matrix first-column/first-row tokens as labels, so its edge cells are answerable from the headers by design (see PREREGISTRATION: edge results are secondary there).

## Evaluation contract

One submission file:

```json
{"profile_id":"externalized-lift-0.1", "condition":"external", "answers":[{"trial_id":"R1C1", "token":"open"}]}
```

Real scoring requires **all 42** trial ids; use empty string for abstention. Trial IDs, not list order, determine accuracy. This example reveals a gold value, so NEVER insert it into participant trial packets; use `submission_template.json` instead.

`score` counts correct on all 42 (12 edge; 30 interior), logs incorrect trial IDs and answers, and refuses duplicates, unknown tokens or omitted trials. `null` uses deterministic token-label permutation to produce a random-label reference, not controlled human-model empirical evidence.

## What is missing before actual experiment

Independent candidate glossary, blinded evaluators with no project knowledge, preregistered N/randomization/threshold, separate private-gold storage, completed observed responses, confidence intervals per independent evaluator, and independent replay. These are tracked in TP-08/TP-15. Do not describe any smoke-test as experimental support.
