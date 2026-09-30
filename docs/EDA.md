# Exploratory Data Analysis

## Objective

This phase describes the cleaned user-level experiment dataset. It summarizes
group allocation, ordered product-journey progression, retention, and
descriptive Control/Treatment differences. The analysis contains no
hypothesis tests, p-values, confidence intervals, feature engineering, or
machine learning.

Run `python python/eda_analysis.py` to rebuild the tables and plots in
`outputs/eda/`. All results below were calculated from
`outputs/cleaned_data/cleaned_ab_test_dataset.csv`.

## Dataset Overview

The cleaned data contains **11,462 users and 16 columns**. There are **5,677
Control users (49.53%)** and **5,785 Treatment users (50.47%)**.

| Recorded outcome flag | Users with value 1 |
|---|---:|
| `onboarding_completed` | 6,291 |
| `trial_started` | 1,878 |
| `paid_conversion` | 1,123 |
| `d1_retained` | 4,669 |
| `d7_retained` | 2,104 |
| `d30_retained` | 1,692 |

These are counts of each recorded outcome flag. The ordered-funnel counts
below additionally require the preceding stage to have been completed.

## Experiment Group Distribution

The assignment counts are close to an even split: **49.53% Control** and
**50.47% Treatment**. The bar chart displays both user counts and shares:

- `outputs/eda/experiment_group_distribution.png`

## User Journey

The analysis defines an ordered user journey as Assigned, Onboarding
Completed, Trial Started, then Paid Conversion. Trial and paid outcomes also
respect their eligibility flags. A later-stage outcome without its prior
stage is not counted as reaching that step in the ordered funnel.

## Funnel Analysis

| Stage | Users reaching stage | Conversion from previous stage | Drop-off to next stage | Drop-off % |
|---|---:|---:|---:|---:|
| Assigned | 11,462 | 100.00% | 5,171 | 45.11% |
| Onboarding Completed | 6,291 | 54.89% | 4,417 | 70.21% |
| Trial Started | 1,874 | 29.79% | 781 | 41.68% |
| Paid Conversion | 1,093 | 58.32% | 0 | 0.00% |

The largest absolute loss is **5,171 users between assignment and
onboarding**. The weakest step conversion is **onboarding to trial at 29.79%**.
Ordered signup/assignment-to-paid conversion is **9.54%** (1,093 of 11,462).
The final stage has no subsequent stage in this funnel, so its drop-off is
reported as zero.

The source outcome flags are not perfectly nested: **32 users** have a
trial/paid outcome without the required preceding funnel stage. These records
remain in the cleaned dataset and in the recorded-flag overview, but are
excluded from downstream counts in the ordered funnel. Consequently, the
recorded paid flag total (1,123) is not the same as the ordered funnel paid
count (1,093).

Charts:

- `outputs/eda/user_funnel.png`
- `outputs/eda/funnel_conversion_rates.png`
- `outputs/eda/funnel_by_variant.png`

## Retention Analysis

Retention rates use each day’s eligible users as the denominator. All
**11,462 users** are eligible for each retention day in this dataset.

| Day | Eligible users | Retained users | Retention rate |
|---|---:|---:|---:|
| D1 | 11,462 | 4,669 | 40.73% |
| D7 | 11,462 | 2,104 | 18.36% |
| D30 | 11,462 | 1,692 | 14.76% |

Retention declines by **22.38 percentage points from D1 to D7**, **3.59 points
from D7 to D30**, and **25.97 points from D1 to D30**. The largest adjacent
decline is D1 to D7.

The source also contains variant-specific retention rates:

| Variant | D1 retention | D7 retention | D30 retention |
|---|---:|---:|---:|
| Control | 40.09% | 18.72% | 14.50% |
| Treatment | 41.37% | 17.99% | 15.02% |

Charts:

- `outputs/eda/retention_curve.png`
- `outputs/eda/retention_by_variant.png`

## Control vs Treatment

The table below compares observed outcome rates. Trial and paid rates use
their eligibility columns as denominators; retention rates also use their
respective eligibility columns. Differences are Treatment minus Control and
are descriptive only.

| Metric | Control rate | Treatment rate | Difference (percentage points) |
|---|---:|---:|---:|
| Onboarding | 53.20% | 56.54% | +3.35 |
| Trial | 15.66% | 17.10% | +1.44 |
| Paid | 10.15% | 9.46% | -0.69 |
| D1 Retention | 40.09% | 41.37% | +1.27 |
| D7 Retention | 18.72% | 17.99% | -0.73 |
| D30 Retention | 14.50% | 15.02% | +0.52 |

In the ordered funnel, Control’s trial-to-paid conversion is **63.77%** and
Treatment’s is **53.44%**. This conditional step rate has a different
denominator from the eligible paid-outcome rate in the table. Neither
comparison tests statistical significance.

Charts:

- `outputs/eda/control_treatment_comparison.png`
- `outputs/eda/funnel_by_variant.png`

## Time-Based Analysis

The `assigned_at` values support a monthly assignment-count trend across three
months, from **2025-04-15 to 2025-06-30**:

| Assignment month | Users assigned |
|---|---:|
| 2025-04 | 940 |
| 2025-05 | 4,871 |
| 2025-06 | 5,651 |

April is partial because observations begin on April 15. `data_end_date` is
the same date for every row, so it does not provide a time series. The
assignment counts are a time trend, **not a cohort analysis**.

Assignment minus signup timestamp differences have **11,462** valid values:
mean **1.01 minutes**, median **0.53 minutes**, minimum **0.13 minutes**, and
maximum **45.00 minutes**.

- `outputs/eda/time_trend.png`
- `outputs/eda/time_trend.csv`
- `outputs/eda/date_descriptive_statistics.csv`

## Key Findings

The generated `outputs/eda/key_insights.txt` contains concise calculations
from the current cleaned data. In summary:

1. The greatest absolute loss is from Assigned to Onboarding: **5,171 users**.
2. The weakest ordered funnel conversion is Onboarding to Trial: **29.79%**.
3. Ordered assignment-to-paid conversion is **9.54%**.
4. Retention falls from **40.73% D1** to **14.76% D30**, with the largest
   adjacent decline between D1 and D7.
5. Treatment has higher descriptive onboarding and D30 retention rates, while
   Control has a higher eligible paid-outcome rate in this sample.
6. Thirty-two records have outcome flags that skip a preceding funnel stage;
   they are excluded from downstream ordered-funnel counts, not deleted.

These observations describe this dataset only. No statistical significance or
causal conclusion is claimed. No user segments beyond experiment variant are
introduced.
