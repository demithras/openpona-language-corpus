# Externalized Lift — frozen coordinate profile H7-W / MX3-W

**Status:** axis names (labels R1-R6, C1-C7) **CANONICAL since 2026-10-09** (author decision, `canon/03_matrix.md`); the generative/predictive claim `T_ij ≈ Lex(F(R_i,C_j))` remains **RESEARCH, NOT CANON**, empirically **UNVERIFIED**. Approved as a research candidate on 2026-10-08.  
**Profile:** `externalized-lift-0.1` (`research/lift/coordinates.v0.1.json`)  
**Source canonical inventory:** `anu 1.1`, 42 tokens, GitHub repo `demithras/openpona-language-corpus` `main` at `97a9b9e8ca8800fda0a22f51ea59fccb6f60f35b`.

## Why lift?

The tempting "embedded headers" model treats the first row and first column as the axes. But these are **tokens**, already occupying cells in the matrix. Inferring their semantics as axis definitions risks circularity and a weaker fit outside the edges. The **Externalized Lift** puts axis meanings outside the matrix, while all 42 cells remain tokens.

This profile was reconstructed from previous discussions, shown to the author and *accepted as the profile to test* on 2026-10-08. Original experimental prompt sheets, reconstructor outputs and raw axis derivation were not independently archived. Do not state that this is authenticated evidence of what all historical trials used.

## External row archetypes

| ID | Value | Operational interpretation (working gloss) |
|---|---|---|
| R1 | Process | unfolding/initiating operational sequence |
| R2 | Inquiry | questioning, seeing, learning |
| R3 | Method | procedures, tools, capabilities |
| R4 | Agency | actors, relations, transformation of entities |
| R5 | Representation | inscribing, communicating, temporal presentation |
| R6 | Integration | cycling, aggregation, evaluation and release |

## External column operations

| ID | Value | Operational interpretation (working gloss) |
|---|---|---|
| C1 | Identity | making an identity or initiating unit distinct |
| C2 | Ground | positioning or situating it |
| C3 | Transform | exploring/changing it |
| C4 | Select | choosing/deciding/comparing |
| C5 | Realize | doing or instantiating |
| C6 | Evaluate | sensing/completing/qualifying |
| C7 | Structure | relational grammar roles |

**The interpretations above are tentative glosses**, not operational definitions precise enough to uniquely determine token strings.

## Matrix = research coordinate overlay on unchanged canonical token values

| | C1 Identity | C2 Ground | C3 Transform | C4 Select | C5 Realize | C6 Evaluate | C7 Structure |
|---|---|---|---|---|---|---|---|
| R1 Process | open | lon | tawa | wile | pali | pilin | li |
| R2 Inquiry | seme | ma | lukin | sona | ni | kute | la |
| R3 Method | nasin | sijelo | ilo | lawa | awen | ken | e |
| R4 Agency | jan | ante | kama | sama | ijo | selo | tan |
| R5 Representation | sitelen | linja | pana | toki | tenpo | pini | pi |
| R6 Integration | sike | ale | weka | ala | kulupu | pona | anu |

## Proposed relation (NOT a fitted deterministic generator)

`T_ij ≈ Lex(F(R_i,C_j))`

- `R_i` = external archetype; `C_j` = external operation.
- `F` = hypothesized semantic intersection; **no complete independent function is currently implemented**.
- `Lex` = lexicalization into a canonical token; could be many-to-one, nonunique or convention-dependent.
- Existing table is **ground truth for lookup, never evidence that the formula predicts the table**. The blind experiment aims to test whether independent judges recover tokens from external labels above null/control performance.

Example candidate readings: `(R1,C1) -> open`, `(R1,C5) -> pali`, `(R2,C3) -> lukin`, `(R4,C4) -> sama`. These are *descriptions of known cells*, not held-out successes.

## Historical status

- MX1 first/edge header lift: rejected as a strong explanatory model (reported unpublished).
- MX2 weak row × column intersection: plausible internally, no archived reproduction.
- H7-W / MX3-W: reported **11/11** hidden edge cells under a historical internal holdout, but hidden set, independent evaluator and raw scripts unavailable; cannot substantiate chance-adjusted accuracy.
- H7-S / MX3-S: exact unique generation of 42 token lexemes from axis identities has **not** been demonstrated; `sijelo`, `sama`, `ni`, `pini` and the Structure column are stress cases.
- One intermediate historical variant allegedly placed row 5 as `sitelen linja tenpo toki pana pini pi`; **current canon** unambiguously uses `sitelen linja pana toki tenpo pini pi`. This research profile only uses current canon and records the other as unverified history.

## Governance and decision

1. Author-approved working *profile* does not equal independent support for its efficacy.
2. Axis metadata are not extra primitive tokens, do not change grammar or `data/matrix.csv`.
3. Current corpus `canon/03_matrix.md` is the authority for placement and, since 2026-10-09, for the axis names; `research/` is authority only for the generative hypothesis, which is unvalidated.
4. Independent confirmatory trial: read `research/lift/PREREGISTRATION.md` and use `blind_experiment.py` for scaffold. Freeze experiment before participants see prompts.
5. If null performance is not exceeded, retain coordinates as a mnemonic hypothesis only. If weak claim survives, do not infer unique lexical generation.
