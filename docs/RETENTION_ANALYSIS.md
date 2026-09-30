# Product Retention and Experiment Analysis (Phase 8)

## Scope and provenance

This integration uses the local user-level experiment dataset and existing Phase 4 statistical results and Phase 7 model evaluation outputs. It does not regenerate or replace EDA, statistical tests, model evaluation, SQL, or historical project-level BigQuery results. Local results are reproducible from the available assignment and outcome fields; historical BigQuery/Tableau findings describe a broader source dataset and are not merged into these local calculations.

## Retention definitions and overall results

D1, D7, and D30 rates use each day?s eligible users as the denominator and that day?s retained flag as the numerator.

| Day | Eligible | Retained | Rate |
|---|---:|---:|---:|
| D1 | 11,462 | 4,669 | 40.73% |
| D7 | 11,462 | 2,104 | 18.36% |
| D30 | 11,462 | 1,692 | 14.76% |

## Retention by experiment variant

Rates below use eligible users within each assignment arm. Differences are treatment minus control, in percentage points; these are descriptive rates.

| Day | Control | Treatment | Difference (pp) |
|---|---:|---:|---:|
| D1 | 40.09% | 41.37% | +1.27 |
| D7 | 18.72% | 17.99% | -0.73 |
| D30 | 14.50% | 15.02% | +0.52 |

## Assignment cohort retention

Cohorts are grouped by the calendar month of `assigned_at`; they are assignment cohorts, not acquisition or signup cohorts. Within each cohort, each retention day uses only users eligible for that observation window.

| Assignment month | Assigned | D1 | D7 | D30 |
|---|---:|---:|---:|---:|
| 2025-04 | 940 | 41.38% | 19.15% | 15.32% |
| 2025-05 | 4,871 | 40.77% | 19.05% | 15.38% |
| 2025-06 | 5,651 | 40.59% | 17.63% | 14.14% |

## Ordered funnel

The funnel reuses Phase 3 logic: Assigned ? Onboarding Completed ? Trial Started (onboarding plus trial eligibility and start) ? Paid Conversion (prior stages plus paid eligibility and conversion).

| Stage | Users | Conversion from previous |
|---|---:|---:|
| Assigned | 11,462 | 100.00% |
| Onboarding Completed | 6,291 | 54.89% |
| Trial Started | 1,874 | 29.79% |
| Paid Conversion | 1,093 | 58.32% |

## A/B statistical results

These six test results are reused from `outputs/statistics/statistical_test_results.csv`; the statistical methodology is unchanged. P-values and 95% confidence intervals are included in `ab_experiment_summary.csv`. Alpha is 0.05, with no multiple-comparison adjustment. Statistical significance is not automatically causal proof; results concern the provided experiment dataset.

| Metric | Control | Treatment | Difference (pp) | p-value | 95% CI (pp) | Significant |
|---|---:|---:|---:|---:|---:|:---:|
| onboarding_completed | 5319.71% | 5654.28% | +3.35 | 0.0003195 | [+1.52, +5.17] | Yes |
| trial_started | 1565.97% | 1709.59% | +1.44 | 0.03779 | [+0.08, +2.79] | Yes |
| paid_conversion | 1014.62% | 945.55% | -0.69 | 0.2136 | [-1.78, +0.40] | No |
| d1_retained | 4009.16% | 4136.56% | +1.27 | 0.1652 | [-0.52, +3.07] | No |
| d7_retained | 1872.47% | 1799.48% | -0.73 | 0.3129 | [-2.15, +0.69] | No |
| d30_retained | 1449.71% | 1502.16% | +0.52 | 0.4287 | [-0.77, +1.82] | No |

## ML retention results

The positive class is D30 retention. Accuracy alone is insufficient because the target is imbalanced (9,770 class 0; 1,692 class 1). Logistic Regression and Decision Tree predicted no positive users at the default threshold. KNN found some positive users but produced false positives. Precision, recall, F1, and ROC-AUC add class-specific and ranking information; the model results are unchanged from Phase 7 and do not establish causality, production readiness, or generalization beyond this dataset.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | TP | TN | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.8526 | 0.0000 | 0.0000 | 0.0000 | 0.6652 | 0 | 1955 | 0 | 338 |
| Decision Tree | 0.8526 | 0.0000 | 0.0000 | 0.0000 | 0.6630 | 0 | 1955 | 0 | 338 |
| K-Nearest Neighbors | 0.7322 | 0.1974 | 0.2663 | 0.2267 | 0.5597 | 90 | 1589 | 366 | 248 |

## Limitations

The local source contains experiment assignment and user-level stage/retention flags, but not raw event histories or acquisition channel, device, platform, region, or revenue. None are fabricated. Assignment-month groups must not be interpreted as signup/acquisition cohorts. Existing broader BigQuery/Tableau summaries are historical project-level findings based on data unavailable locally. Descriptive rate differences and statistical tests answer different questions and should not be conflated.

## Outputs

CSV summaries and four visualizations are stored under `outputs/retention/`.
