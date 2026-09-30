# Statistical Analysis

## Objective

This phase tests whether the observed Control and Treatment outcome
proportions differ in the local user-level experiment data. It uses the
cleaned dataset at `outputs/cleaned_data/cleaned_ab_test_dataset.csv`.
The tests are descriptive evidence about these groups and do not establish
causality.

Run `python python/statistical_analysis.py` to recreate the result table and
plain-language interpretations under `outputs/statistics/`.

## Hypotheses and test selection

For each outcome:

- **Null hypothesis (H0):** Control and Treatment have the same outcome
  proportion.
- **Alternative hypothesis (H1):** Control and Treatment have different
  outcome proportions.

A two-proportion z-test is suitable because the outcomes are binary (0/1) and
the analysis compares a proportion from each of two experiment groups. The
test is two-sided, with Control as the reference and the difference defined
as **Treatment rate minus Control rate**. It uses the pooled proportion for
the null-hypothesis test. The 95% confidence interval uses the unpooled
standard error for the difference in proportions.

The **p-value** is the probability, assuming the null hypothesis is true, of
observing a difference at least as extreme as the one measured. It is not the
probability that the null hypothesis is true. **Alpha = 0.05** is the chosen
per-test threshold: a p-value below 0.05 is labeled statistically significant.
A **95% confidence interval** is an interval-estimation method that would
cover the true difference in about 95% of repeated comparable samples.

Onboarding uses each group's assigned users because the dataset has no
onboarding eligibility column. Trial, paid conversion, and each retention
outcome use the matching eligibility flag as their denominator.

## Results

Rates and confidence interval bounds are percentages; differences and interval
bounds are in percentage points. P-values are two-sided. Significance uses
alpha 0.05 for each test.

| Metric | Control eligible | Control successes | Control rate | Treatment eligible | Treatment successes | Treatment rate | Difference (pp) | p-value | 95% CI (pp) | Significant at 0.05 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `onboarding_completed` | 5,677 | 3,020 | 53.20% | 5,785 | 3,271 | 56.54% | +3.35 | 0.000319 | [1.52, 5.17] | Yes |
| `trial_started` | 5,677 | 889 | 15.66% | 5,785 | 989 | 17.10% | +1.44 | 0.037794 | [0.08, 2.79] | Yes |
| `paid_conversion` | 5,677 | 576 | 10.15% | 5,785 | 547 | 9.46% | -0.69 | 0.213614 | [-1.78, 0.40] | No |
| `d1_retained` | 5,677 | 2,276 | 40.09% | 5,785 | 2,393 | 41.37% | +1.27 | 0.165157 | [-0.52, 3.07] | No |
| `d7_retained` | 5,677 | 1,063 | 18.72% | 5,785 | 1,041 | 17.99% | -0.73 | 0.312888 | [-2.15, 0.69] | No |
| `d30_retained` | 5,677 | 823 | 14.50% | 5,785 | 869 | 15.02% | +0.52 | 0.428652 | [-0.77, 1.82] | No |

## Interpretation

- **Onboarding:** Control completed onboarding at 53.20%; Treatment at
  56.54%. Treatment was higher by 3.35 percentage points
  (p = 0.000319), statistically significant at the 5% level.
- **Trial start:** Control was 15.66%; Treatment was 17.10%. Treatment was
  higher by 1.44 points (p = 0.037794), statistically significant at the 5%
  level.
- **Paid conversion:** Control was 10.15%; Treatment was 9.46%. Treatment was
  lower by 0.69 points (p = 0.213614), not statistically significant at 5%.
- **D1 retention:** Control was 40.09%; Treatment was 41.37%. Treatment was
  higher by 1.27 points (p = 0.165157), not statistically significant at 5%.
- **D7 retention:** Control was 18.72%; Treatment was 17.99%. Treatment was
  lower by 0.73 points (p = 0.312888), not statistically significant at 5%.
- **D30 retention:** Control was 14.50%; Treatment was 15.02%. Treatment was
  higher by 0.52 points (p = 0.428652), not statistically significant at 5%.

These are comparisons in the available dataset. Statistical significance does
not by itself establish practical importance or causality.

## Assumptions and limitations

- Each user contributes one binary outcome to each comparison, and users are
  treated as independent observations.
- Group sizes and success/failure counts are sufficient for the normal
  approximation used by the two-proportion z-test.
- The local file is synthetic portfolio data, not real customer data.
- All users in this file have `trial_eligible`, `paid_eligible`, `d1_eligible`,
  `d7_eligible`, and `d30_eligible` equal to 1. The script nevertheless uses
  those eligibility fields so the denominators remain correct if eligibility
  varies in a future valid input.
- The six requested tests use alpha 0.05 individually. No multiple-comparison
  adjustment is applied in this phase; interpret the collection of tests with
  that limitation in mind.
- This phase does not create additional user segments, run regression, or
  make causal claims.

## Output files

- `outputs/statistics/statistical_test_results.csv` — six test results with
  sample counts, rates, rate difference, z-statistic, p-value, confidence
  interval, and significance flag.
- `outputs/statistics/statistical_test_results.txt` — plain-language
  interpretation for each outcome.
- `notebooks/02_statistical_analysis.ipynb` — hypotheses, test explanation,
  calculations, result table, and interpretation.
