# Externalized Lift — prospective blinded study preregistration (DRAFT)

**Status:** DRAFT, NOT PREREGISTERED WITH AN EXTERNAL REGISTRY, NO PARTICIPANT RESULTS. Must be frozen, dated and hashed BEFORE the first evaluated response. Historical MX3-W 11/11 cannot be retroactively preregistered.

## Questions / hypotheses

- **MX3-W weak:** independent interpreters using frozen external axes reconstruct held-out canonical cell tokens more accurately in the **interior** (R2–R6 × C2–C7 = 30 cells) than interpreters using generic axes, shuffled external axes, or first-row/first-column embedded labels.
- **MX3-S strong:** a uniquely defined F and Lex predicts all cells solely from fixed axis semantics, with no memorized placement or post-hoc labels. Not tested conclusively by a forced-choice reconstruction task; requires a distinct deterministic generator and additional cases.
- **Null:** external labels provide no superior blind recovery relative to assigned controls.

## Study design (fix before running)

1. Participants: independent human/agent subjects unfamiliar with the final table. Declare recruitment source, how prior OpenPona exposure is screened, randomization unit, model context isolation, and target N in a signed pre-study amendment. **N, effect size, and primary alpha are intentionally NOT invented by this draft.** A pilot may size the full study but cannot also serve as a confirmatory sample.
2. Random assignment across four conditions: `external` (Process/Inquiry/... × Identity/Ground/...), `embedded` (first-column/first-row tokens as semantic anchors), `generic` (R1..R6,C1..C7 only), `shuffled` (frozen external axis labels permuted across positions). All conditions get the same candidate token vocabulary and independent glossary (required to be authored and frozen before use; no glossary generated here).
3. Each trial contains only a coordinate and its condition-specific row/column label plus candidates. No canonical matrix, sample cells, examples giving correct token labels, or `private_gold.json` in public materials. Participants must not have access to this ZIP, GitHub repository or source metadata revealing placements during tasks.
4. Study operator keeps blind packet (`public_prompt.json`, `submission_template.json`) and private lookup (`private_gold.json`) in separate access-controlled locations; participants must not have the files or network lookup. Log any leakage and exclude/flag before unblinding.
5. Do **not** treat an agent with this OpenPona context in its system prompt or training history as independent; use a fresh isolated context and document training-leakage limits.
6. Primary endpoint: **per-participant Top-1 exact match rate over 30 interior cells**, counting unanswered as incorrect. Why exclude edges: embedded labels literally name edge tokens, giving direct leakage at first row/column. Secondary: 12 edge cells, all 42 cells, per-row/column and hard cells (sijelo, sama, ni, pini, Structure), time/cost and abstention.
7. Report participants and trials, each individual's raw scores, intervals of paired/unpaired arm contrasts as appropriate, uncertainty, and full confusion matrices. Use independent participant-level inference, not 42 correlated responses as if 42 independent people.
8. Negative control: shuffle axis meanings across positions before participants see them; after collection, permutation-null script randomizes gold label assignments while preserving one-to-one mapping. Null script **tests a label-symmetry null, not a population arm effect**.
9. `prepare` takes separate, required `--public-dir` and `--private-dir` and refuses when they are equal or one lies inside the other (implemented 2026-10-09). The operator still keeps the private directory in access-controlled storage and never opens it during collection.
10. Once analysis begins, do not rename axes, adjust cell mapping, swap historical row 5, change exclusion rules or revise score cutoffs without publishing it as exploratory deviation.

## Frozen artifacts checklist (before enrollment)

- Profile JSON hash, candidate glossary, study questions, arm exports and scorer source hash.
- Participants/agent configurations, N and allocation strategy, random seeds, stopping rule, effect/alpha threshold, privacy/consent if people are involved.
- Pilot results segregated, exclusions policy, repeated-exposure avoidance.
- Timestamped artifact hashes (SHA-256), immutability / preregistration destination.

## Interpret results adversarially

- External > generic/shuffled/embedded on interior **supports only a weak coordinate signal** under these materials and population.
- External ≈ controls: no supported benefit under test (retain as mnemonic research hypothesis).
- External only wins at edges: insufficient and suspicious for reconstruction claim.
- Full accuracy: still does not prove `Lex(F(...))` is uniquely generative; source table/lexical prior leakage must be investigated.
- Historic 11/11 is always labeled *reported internal, unpublished, unreproduced* until its materials are archived and a comparable independent test is run.

Note (2026-10-09): the axis names tested here became canonical by author decision on 2026-10-09 (`canon/03_matrix.md`). The hypotheses above (MX3-W, MX3-S) and the design are unchanged; the generative/predictive claim remains RESEARCH, unvalidated.

## Pilot amendment (2026-10-09, author decision)

Status of this amendment: **pilot only, exploratory**. The main study above stays **DRAFT**; nothing in this amendment preregisters or confirms it.

- **Participants:** isolated LLMs of several vendors, each run in a fresh context with no tools, web, memory, files or project content in the system prompt (operator steps: `research/lift/pilot/PILOT_PROTOCOL.md`). The recruitment, screening and "unfamiliar with the final table" requirements of point 1 are replaced, for the pilot only, by this isolation protocol plus a post-task familiarity question whose answers are **reported, not used to exclude silently**.
- **Purpose:** an exploratory pilot that sizes the main study (spread of participant scores, vendor differences, abstention, feasibility). It is not a confirmatory sample and cannot be one (point 1).
- **Design:** the four arms of point 2, allocated by `pilot/make_packets.py` (vendors x arms x k participants, seeded, counterbalanced candidate/trial order), packets and tooling frozen with `pilot/freeze.py` before the first response, analysis by `pilot/analyze.py` (Top-1 interior 30 / edge 12 / all 42, participant-level bootstrap 95% CI with a fixed seed, per-cell confusion, per-participant label-permutation null; every output headed `PILOT - EXPLORATORY, NOT CONFIRMATORY`).
- **N, alpha and effect size for the main study** are decided by the author **after** the pilot, from the pilot's observed spread; this amendment fixes none of them.
- **Glossary (point 2 requirement):** English definitions of the 42 matrix tokens from lipu Linku (`translations.en.definition`), https://github.com/lipu-linku/sona, CC BY-SA 4.0, retrieved 2026-10-09, snapshot SHA-256 `369cc79d9b764feabcda59112d92171d486456be973b62fc6689a7442718e9d1`, stored verbatim in `research/lift/glossary/linku_en_2026-10-09.json`, identical in all arms; no other definitions, no edits.
- **Known limitation (leak):** the Lift labels and cell tokens have been canonical on public GitHub since 2026-10-09, so exposure through model training data or browsing cannot be excluded for any vendor. A high pilot score therefore cannot be read as independent reconstruction.
