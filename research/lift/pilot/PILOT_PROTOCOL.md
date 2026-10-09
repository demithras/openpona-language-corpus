# Lift pilot protocol: isolated LLM participants

**PILOT - EXPLORATORY, NOT CONFIRMATORY.** Authority: PREREGISTRATION.md, section "Pilot amendment (2026-10-09, author decision)". The main study stays DRAFT; this pilot only sizes it.

## Known limitation (read first)

The Lift labels and the 42 cell tokens have been canonical on public GitHub since 2026-10-09. Model training exposure or browsing exposure therefore **cannot be excluded** for any vendor, and a good score does not show independent reconstruction. The post-task familiarity answer is **reported** for every participant and is **not used to exclude** anyone silently; any exclusion is a logged, named decision in `ingest_log.json`.

## Roles and separation

- **Operator** prepares the pilot directory (`PILOT_DIR`), pastes packets, saves replies. The operator never opens the private gold directory (`PRIVATE_DIR`) during collection.
- **Participant** is a fresh LLM context. It receives only the text of one `packets/<pid>.md`.
- Gold lives only under `PRIVATE_DIR`, created by `blind_experiment.py prepare --private-dir`, a location outside `PILOT_DIR` and not inside the repository checkout used for collection.

## Steps

1. **Build packets.** `python research/lift/pilot/make_packets.py --vendors <v1,v2,...> --per-arm-per-vendor <k> --seed <int> --out-dir PILOT_DIR` (`PILOT_DIR` absent or empty). It writes `allocation.csv` (participant, vendor, arm, order group), `packets/<pid>.md`, `pilot_config.json` (seed) and an empty `responses/`. Nothing in it is gold.
2. **Freeze before any response.** `python research/lift/pilot/freeze.py --dir PILOT_DIR` writes `pilot_freeze.json` (SHA-256 of profile, glossary, scorer, pilot scripts, config, allocation, every packet, seed). It refuses if `responses/` is not empty. Commit or archive `pilot_freeze.json` with a timestamp before step 3. Do not edit packets, scripts or allocation afterwards; `ingest.py` and `analyze.py` refuse if any hash changed.
3. **Run each participant**, one packet per participant, in the order you like (the allocation is already randomized):
   - new, empty context for every participant (new chat or fresh API call with no history);
   - no tools, no web search, no code execution, no memory feature, no uploaded files, and a system prompt with no project content (none, or a vendor default; record which);
   - record in `responses/<pid>.meta.json`: `{"vendor": ..., "model_id": "<exact model id string>", "date": "YYYY-MM-DD", "temperature": ..., "other_settings": {...}, "system_prompt": "none|default|<text>"}` (missing meta is flagged in the ingest log);
   - paste the whole packet as the single user message and send it once; do not answer follow-up questions or retry on a poor answer;
   - save the complete raw reply, unedited, as `responses/<pid>.txt`.
   Do not look into `PRIVATE_DIR` and do not score during collection.
4. **Ingest.** `python research/lift/pilot/ingest.py --dir PILOT_DIR`. It extracts the JSON answer object from surrounding prose, requires the 42 trial ids exactly once each (missing, duplicate and foreign ids reject the reply; tokens must be `""` or a candidate token; two different answer objects in one reply reject it), records the `FAMILIARITY:` line, and writes `parsed/<pid>.json` and `ingest_log.json` (accepted, excluded with reason, flags, allocated-without-response). A rejected reply is not rerun and not edited; it stays in the log.
5. **Prepare gold elsewhere**, only after collection: `python research/lift/blind_experiment.py prepare --condition external --seed <any> --public-dir <scratch> --private-dir PRIVATE_DIR`. All conditions share the same gold mapping.
6. **Analyze.** `python research/lift/pilot/analyze.py --dir PILOT_DIR --gold PRIVATE_DIR` writes `report.md` and `results.json`: per participant Top-1 on interior 30 / interior w/o C7 25 / C7 5 / edge 12 / all 42 (abstention is wrong), per-arm mean with a participant-level bootstrap 95% CI (fixed seed), per-cell confusion, per-participant label-permutation null, familiarity counts, ingest exclusions. Both files start with `PILOT - EXPLORATORY, NOT CONFIRMATORY`.
7. **Report honestly.** Quote the limitation above, the number of rejected and missing participants, and the familiarity table. Do not describe the pilot as support for MX3-W or MX3-S. Deviations from this protocol are written down as exploratory deviations.

## Column C7 cue

In the external arm column C7 is labelled "Structure", and the Linku glossary tags 4 of its 5 interior tokens (la, e, pi, anu) as "(particle)" (tan is "(preposition)"), a trivial column cue. The primary endpoint stays interior 30; analysis also reports `interior_no_c7` (25 cells) and `c7_interior` (5 cells) in every table. A result favouring external labels must hold on `interior_no_c7`, otherwise it is reported as cue-driven.

## What the pilot is for

Spread of participant scores per arm and vendor, abstention behavior, ingest failure rate, and cost. From these the author decides N, alpha and the effect size of the main study; none is fixed here.
