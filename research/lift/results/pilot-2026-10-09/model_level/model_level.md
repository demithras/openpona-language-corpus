# PILOT - EXPLORATORY, NOT CONFIRMATORY - unit of analysis: model (runs are not independent)

Models: 2 (haiku, sonnet). Model score per arm = mean of that model's runs. Bootstrap resamples models with replacement, seed 20261009, 10000 reps.

## Sector: interior

| model | arm | mean | n_runs |
|---|---|---|---|
| haiku | embedded | 0.000 | 3 |
| haiku | external | 0.033 | 3 |
| haiku | generic | 0.000 | 3 |
| haiku | shuffled | 0.011 | 3 |
| sonnet | embedded | 0.000 | 3 |
| sonnet | external | 0.056 | 3 |
| sonnet | generic | 0.011 | 3 |
| sonnet | shuffled | 0.022 | 3 |

| contrast | per-model | k>0 / k<0 / ties of M | sign-test p (1-sided) | mean | model-bootstrap 95% CI |
|---|---|---|---|---|---|
| external_minus_embedded_interior | haiku: +0.033, sonnet: +0.056 | 2 / 0 / 0 of 2 | 0.250 | 0.044 | [0.033, 0.056] |
| external_minus_generic_interior | haiku: +0.033, sonnet: +0.044 | 2 / 0 / 0 of 2 | 0.250 | 0.039 | [0.033, 0.044] |
| external_minus_shuffled_interior | haiku: +0.022, sonnet: +0.033 | 2 / 0 / 0 of 2 | 0.250 | 0.028 | [0.022, 0.033] |

- M=2 < 5: the bootstrap interval is not interpretable as a population CI.
- Minimum attainable one-sided sign-test p with 2 non-tied models is 0.25.

## Sector: interior_no_c7

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

## Sector: c7_interior

| model | arm | mean | n_runs |
|---|---|---|---|
| haiku | embedded | 0.000 | 3 |
| haiku | external | 0.000 | 3 |
| haiku | generic | 0.000 | 3 |
| haiku | shuffled | 0.000 | 3 |
| sonnet | embedded | 0.000 | 3 |
| sonnet | external | 0.133 | 3 |
| sonnet | generic | 0.000 | 3 |
| sonnet | shuffled | 0.000 | 3 |

| contrast | per-model | k>0 / k<0 / ties of M | sign-test p (1-sided) | mean | model-bootstrap 95% CI |
|---|---|---|---|---|---|
| external_minus_embedded_c7_interior | haiku: +0.000, sonnet: +0.133 | 1 / 0 / 1 of 2 | 0.500 | 0.067 | [0.000, 0.133] |
| external_minus_generic_c7_interior | haiku: +0.000, sonnet: +0.133 | 1 / 0 / 1 of 2 | 0.500 | 0.067 | [0.000, 0.133] |
| external_minus_shuffled_c7_interior | haiku: +0.000, sonnet: +0.133 | 1 / 0 / 1 of 2 | 0.500 | 0.067 | [0.000, 0.133] |

- M=2 < 5: the bootstrap interval is not interpretable as a population CI.
- Minimum attainable one-sided sign-test p with 1 non-tied models is 0.5.

## Sector: edge

| model | arm | mean | n_runs |
|---|---|---|---|
| haiku | embedded | 0.000 | 3 |
| haiku | external | 0.194 | 3 |
| haiku | generic | 0.000 | 3 |
| haiku | shuffled | 0.000 | 3 |
| sonnet | embedded | 1.000 | 3 |
| sonnet | external | 0.361 | 3 |
| sonnet | generic | 0.000 | 3 |
| sonnet | shuffled | 0.000 | 3 |

| contrast | per-model | k>0 / k<0 / ties of M | sign-test p (1-sided) | mean | model-bootstrap 95% CI |
|---|---|---|---|---|---|
| external_minus_embedded_edge | haiku: +0.194, sonnet: -0.639 | 1 / 1 / 0 of 2 | 0.750 | -0.222 | [-0.639, 0.194] |
| external_minus_generic_edge | haiku: +0.194, sonnet: +0.361 | 2 / 0 / 0 of 2 | 0.250 | 0.278 | [0.194, 0.361] |
| external_minus_shuffled_edge | haiku: +0.194, sonnet: +0.361 | 2 / 0 / 0 of 2 | 0.250 | 0.278 | [0.194, 0.361] |

- M=2 < 5: the bootstrap interval is not interpretable as a population CI.
- Minimum attainable one-sided sign-test p with 2 non-tied models is 0.25.

## Sector: all

| model | arm | mean | n_runs |
|---|---|---|---|
| haiku | embedded | 0.000 | 3 |
| haiku | external | 0.079 | 3 |
| haiku | generic | 0.000 | 3 |
| haiku | shuffled | 0.008 | 3 |
| sonnet | embedded | 0.286 | 3 |
| sonnet | external | 0.143 | 3 |
| sonnet | generic | 0.008 | 3 |
| sonnet | shuffled | 0.016 | 3 |

| contrast | per-model | k>0 / k<0 / ties of M | sign-test p (1-sided) | mean | model-bootstrap 95% CI |
|---|---|---|---|---|---|
| external_minus_embedded_all | haiku: +0.079, sonnet: -0.143 | 1 / 1 / 0 of 2 | 0.750 | -0.032 | [-0.143, 0.079] |
| external_minus_generic_all | haiku: +0.079, sonnet: +0.135 | 2 / 0 / 0 of 2 | 0.250 | 0.107 | [0.079, 0.135] |
| external_minus_shuffled_all | haiku: +0.071, sonnet: +0.127 | 2 / 0 / 0 of 2 | 0.250 | 0.099 | [0.071, 0.127] |

- M=2 < 5: the bootstrap interval is not interpretable as a population CI.
- Minimum attainable one-sided sign-test p with 2 non-tied models is 0.25.

## Limits

- Run-level CIs in analyze.py are descriptive only; conclusions need agreement across models on interior_no_c7.
- Ties are counted separately and excluded from the sign test.
