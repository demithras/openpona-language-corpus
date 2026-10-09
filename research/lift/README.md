# Lift experiment scaffold (stdlib-only)

**For prospective experimental setup, not a claim of result.** External axes were approved as **research coordinates** by the author on 2026-10-08; the axis names became canonical on 2026-10-09 (`canon/03_matrix.md`), while the generative/predictive claim remains RESEARCH, unvalidated. This harness contains known reference answers solely to verify and score later, independently obtained predictions.

## Commands

From the package root:

```bash
python research/lift/blind_experiment.py validate
python -m unittest discover -s research/lift/tests -v
python research/lift/blind_experiment.py prepare --condition external --seed 20261008 --public-dir /tmp/lift-external/public --private-dir /private-store/lift-external
python research/lift/blind_experiment.py prepare --condition embedded --seed 20261008 --public-dir /tmp/lift-embedded/public --private-dir /private-store/lift-embedded
python research/lift/blind_experiment.py prepare --condition generic --seed 20261008 --public-dir /tmp/lift-generic/public --private-dir /private-store/lift-generic
python research/lift/blind_experiment.py prepare --condition shuffled --seed 20261008 --public-dir /tmp/lift-shuffled/public --private-dir /private-store/lift-shuffled
# Fill the generated submission_template.json in a separate blinded evaluation.
python research/lift/blind_experiment.py score --gold /private-store/lift-external/private_gold.json --answers submitted.json --out score.json
python research/lift/blind_experiment.py null --gold /private-store/lift-external/private_gold.json --answers submitted.json --reps 10000 --seed 20261008 --out null.json
```

`prepare` takes two required, separate output roots. `--public-dir` receives `public_prompt.json` (coordinate labels, candidate list, the frozen candidate glossary, NO cell-token mapping) and `submission_template.json` (blank tokens); `--private-dir` receives `private_gold.json` (truth mapping, keep secret). `prepare` exits non-zero (and writes nothing) when the two directories are equal or one lies inside the other (symlinks resolved; PREREGISTRATION point 9), and when either directory is non-empty. Distribute only the public directory. The shared package itself reveals the table and cannot be a blind participant resource.

The public prompt includes `glossary`: the English definition of each of the 42 candidate tokens from `glossary/linku_en_2026-10-09.json` (lipu Linku, CC BY-SA 4.0, retrieved 2026-10-09, snapshot SHA-256 recorded in the file; see `glossary/LICENSE-NOTICE.md`). It is identical in all four arms.

## Pilot kit (isolated LLM participants)

`pilot/` holds the operator kit for the exploratory pilot added by the 2026-10-09 amendment (PREREGISTRATION.md, "Pilot amendment"): `make_packets.py`, `freeze.py`, `ingest.py`, `analyze.py` and the step-by-step `pilot/PILOT_PROTOCOL.md`. Every output of the kit is headed `PILOT - EXPLORATORY, NOT CONFIRMATORY`.

```bash
python research/lift/pilot/make_packets.py --vendors a,b,c --per-arm-per-vendor 3 --seed 20261009 --out-dir PILOT_DIR
python research/lift/pilot/freeze.py --dir PILOT_DIR          # before ANY response
# collect responses/<pid>.txt (see PILOT_PROTOCOL.md), then:
python research/lift/pilot/ingest.py --dir PILOT_DIR
python research/lift/blind_experiment.py prepare --condition external --seed 1 --public-dir SCRATCH --private-dir PRIVATE_DIR   # gold only
python research/lift/pilot/analyze.py --dir PILOT_DIR --gold PRIVATE_DIR
```

Model-level analysis (unit = model, runs are not independent): `python research/lift/analysis/model_level.py --results PILOT_DIR/results.json --out-dir OUT_DIR` (see `analysis/model_level.py`).

Packets contain no gold; the gold pair of a cell (trial id with its token) never appears in a packet. `analyze.py` is the only step that reads gold, and it refuses to run if any frozen hash (profile, glossary, scorer, pilot scripts, config, allocation, every packet, seed) changed.

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

Blinded evaluators with no project knowledge (the candidate glossary now exists: `glossary/`), preregistered N/randomization/threshold for the main study (the pilot sizes it), enforced separate private-gold storage for production, completed observed responses, confidence intervals per independent evaluator, and independent replay. These are tracked in TP-08/TP-15. Do not describe any smoke-test as experimental support.
