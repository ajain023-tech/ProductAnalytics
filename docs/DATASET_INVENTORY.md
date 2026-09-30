# Product Analytics & User Retention Analysis — Dataset Inventory

This inventory describes files present in the project workspace. Counts below
were calculated from the local CSV files; an empty or header-only export is
not treated as analytical data.

## Local analytical datasets

| Filename | Rows × columns | Important columns and data types | Missing values | Duplicate rows | Unique users | Purpose |
|---|---:|---|---:|---:|---:|---|
| `data/ab_test_dataset.csv` | 11,462 × 16 | `user_id` (string); `variant` (string); `assigned_at`, `signup_ts`, `data_end_date` (date/time values stored as strings); 11 binary outcome/eligibility flags (`int64`) | 0 cells | 0 | 11,462 | User-level experiment assignment and outcome dataset. Supports Control/Treatment summaries for onboarding, trial, paid conversion, and D1/D7/D30 retention. |
| `data/ab_test_results.csv` | 6 × 13 | `metric` (string); `control_n`, `treatment_n` (`int64`); rates, effects, confidence limits, z-statistic, p-values (`float64`); `significant` (boolean) | 0 cells | 0 | Not applicable; aggregate metric rows | Existing A/B statistical results for `onboarding_completion`, `trial_start`, `paid_conversion`, `D1_retention`, `D7_retention`, and `D30_retention`. |
| `outputs/experiments/ab_test_summary.csv` | 2 × 13 | `experiment_name`, `metric` (string); group sizes (`int64`); conversion rates, uplifts, confidence limits, and p-values (`float64`); significance (boolean) | 0 cells | 0 | Not applicable; aggregate metric rows | Compact summary for `onboarding_flow_v2`: `onboarding_completion` and `paid_conversion`. The summary script validates its calculations against `data/ab_test_results.csv`. |

### User assignment dataset schema

The actual columns in `data/ab_test_dataset.csv` are:

- **Identifiers and assignment context:** `user_id`, `variant`,
  `assigned_at`, `signup_ts`, `data_end_date`.
- **Binary outcomes and eligibility flags:** `onboarding_completed`,
  `trial_eligible`, `trial_started`, `paid_eligible`, `paid_conversion`,
  `d1_eligible`, `d1_retained`, `d7_eligible`, `d7_retained`,
  `d30_eligible`, `d30_retained`.
- **Observed variants:** `control` (5,677 users) and `treatment` (5,785 users).
- **Other categorical values:** `data_end_date` has one observed value,
  `2025-08-15`.
- **Data types:** identifiers, variant, and date/time fields are read as strings;
  outcome and eligibility flags are integer 0/1 values.

The only meaningful categorical segmentation variable in this local
user-level file is `variant`. It contains no acquisition-channel, platform,
device-tier, region, or demographic columns. Do not infer those attributes
from the experiment assignments.

## Dashboard, funnel, retention, and SQL exports

The cleaning phase also creates these populated local outputs:

| Filename | Rows × columns | Missing values / duplicate rows | Unique users | Purpose and current status |
|---|---:|---|---:|---|
| `outputs/cleaned_data/cleaned_ab_test_dataset.csv` | 11,462 × 16 | 0 / 0 | 11,462 | Cleaned copy of the local experiment dataset; source CSV remains unchanged. |
| `outputs/cleaned_data/data_quality_report.csv` | 18 × 2 | Not applicable; metric/value report | Not applicable | Actual input checks, cleaning counts, and experiment group assignment shares. |

The EDA phase also generates the following summary CSVs:

| Filename | Rows × columns | Purpose |
|---|---:|---|
| `outputs/eda/eda_summary.csv` | 16 × 2 | Dataset totals, group shares, outcome counts, and derived overall/retention metrics. |
| `outputs/eda/user_funnel.csv` | 4 × 5 | Ordered funnel users, step conversion, and drop-off. |
| `outputs/eda/retention_summary.csv` | 3 × 4 | Eligibility-based D1, D7, and D30 retention. |
| `outputs/eda/control_treatment_comparison.csv` | 6 × 4 | Descriptive outcome-rate differences by experiment arm. |
| `outputs/eda/retention_by_variant.csv` | 2 × 4 | D1/D7/D30 retention rates by experiment arm. |
| `outputs/eda/funnel_by_variant.csv` | 2 × 8 | Ordered funnel counts and step rates by experiment arm. |
| `outputs/eda/time_trend.csv` | 3 × 2 | Monthly assignment counts for observed assignment dates. |
| `outputs/eda/date_descriptive_statistics.csv` | 1 × 6 | Descriptive statistics for assignment-minus-signup delay. |

`outputs/eda/` also contains eight generated PNG charts and
`key_insights.txt`. Findings and limitations are explained in `docs/EDA.md`;
the assignment trend is not presented as cohort analysis.

The statistical phase creates:

| Filename | Rows × columns | Purpose |
|---|---:|---|
| `outputs/statistics/statistical_test_results.csv` | 6 × 13 | Two-proportion z-test results for onboarding, trial, paid conversion, D1, D7, and D30 retention. |
| `outputs/statistics/statistical_test_results.txt` | 6 interpretations | Plain-language Control/Treatment rate comparisons and test conclusions. |

The feature engineering phase creates:

| Filename | Rows × columns | Purpose |
|---|---:|---|
| `outputs/features/model_features.csv` | 11,462 rows, 7 columns | User identifier, five model input features, and the D30-retention target. |
| `outputs/features/feature_summary.csv` | 6 rows, 8 columns | Descriptive summary for five inputs and the target; user ID is excluded. |

Some legacy dashboard, funnel, retention, and SQL export templates listed
below remain header-only or zero-byte. Phase 8 local retention, cohort, funnel,
A/B, and ML summary outputs are populated separately under `outputs/retention/`;
their presence does not imply local channel/platform or historical BigQuery
exports are available.

| Filename | Rows × columns | Missing values / duplicate rows | Unique users | Purpose and current status |
|---|---:|---|---|---|
| `outputs/dashboard/ab_test_summary.csv` | 2 × 13 | 0 / 0 | Not applicable | Populated dashboard copy of the experiment summary. |
| `outputs/dashboard/activity_summary.csv` | 0 × 4 | Not applicable; no data rows | Not available | Header-only activity-tier template. |
| `outputs/dashboard/executive_kpis.csv` | 0 × 3 | Not applicable; no data rows | Not available | Header-only executive KPI template. |
| `outputs/dashboard/funnel_segments.csv` | 0 × 9 | Not applicable; no data rows | Not available | Header-only funnel segment template. |
| `outputs/dashboard/funnel_summary.csv` | 0 × 4 | Not applicable; no data rows | Not available | Header-only funnel summary template. |
| `outputs/dashboard/monetization_summary.csv` | 0 × 3 | Not applicable; no data rows | Not available | Header-only monetization template. |
| `outputs/dashboard/retention_cohorts.csv` | 0 × 5 | Not applicable; no data rows | Not available | Header-only retention cohort template. |
| `outputs/funnel/funnel_segment_summary.csv` | 0 × 10 | Not applicable; no data rows | Not available | Header-only SQL funnel segment output. |
| `outputs/funnel/funnel_summary.csv` | 0 × 7 | Not applicable; no data rows | Not available | Header-only SQL funnel output. |
| `outputs/retention/cohort_retention.csv` | 0 × 11 | Not applicable; no data rows | Not available | Header-only cohort retention output. |
| `outputs/retention/retention_by_channel.csv` | 0 × 11 | Not applicable; no data rows | Not available | Header-only channel retention output. |
| `outputs/retention/retention_by_platform.csv` | 0 × 11 | Not applicable; no data rows | Not available | Header-only platform retention output. |
| `outputs/sql/funnel_segment_analysis.csv` | No rows or columns; 0 bytes | Not applicable | Not available | Empty generated SQL output file; no query results. |
| `outputs/sql/product_kpis.csv` | No rows or columns; 0 bytes | Not applicable | Not available | Empty generated SQL output file; no query results. |
| `outputs/sql/product_kpis_monthly.csv` | No rows or columns; 0 bytes | Not applicable | Not available | Empty generated SQL output file; no query results. |
| `outputs/sql/user_activity_channel_rank.csv` | No rows or columns; 0 bytes | Not applicable | Not available | Empty generated SQL output file; no query results. |
| `outputs/sql/user_activity_levels.csv` | No rows or columns; 0 bytes | Not applicable | Not available | Empty generated SQL output file; no query results. |
| `outputs/sql/user_activity_mau.csv` | No rows or columns; 0 bytes | Not applicable | Not available | Empty generated SQL output file; no query results. |

The populated A/B summary copy at
`outputs/dashboard/ab_test_summary.csv` matches the 2-row experiment summary.
The remaining dashboard, funnel, retention, and SQL output templates do not
provide locally populated segment or product-analysis results.

## Other analytical assets and data availability

- `python/ab_test_analysis.ipynb` contains the existing A/B analysis,
  including Sample Ratio Mismatch, two-proportion tests, confidence intervals,
  Holm adjustment, guardrail sensitivity, and a decision section.
- `python/ab_test_summary.py` recalculates the concise A/B summary and checks
  it against the existing result CSV.
- `python/data_cleaning.py` checks the local user-level experiment CSV and
  writes a cleaned copy and quality report without overwriting the source.
- `python/eda_analysis.py` creates descriptive funnel, retention, date, and
  experiment-group analyses from the cleaned CSV; it does not run significance
  tests.
- `python/statistical_analysis.py` tests six binary outcome proportions using
  the matching eligibility denominators and writes a test table and
  interpretations.
- `python/feature_engineering.py` creates five documented D30-retention
  inputs from the cleaned user-level CSV. It does not train a model.
- `python/model_training.py` trains three saved classifiers using one common
  stratified split; `outputs/models/` contains the artifacts and metadata.
- `python/model_evaluation.py` evaluates the saved artifacts on the same
  holdout and writes metrics, curves, and charts under `outputs/evaluation/`.
- `python/retention_analysis.py` writes populated local retention, assignment
  cohort, ordered funnel, A/B summary, and ML summary outputs under `outputs/retention/`.
- `app.py` integrates the local outputs and labels historical project metrics
  separately; it does not execute BigQuery SQL.
- `notebooks/01_data_cleaning_eda.ipynb` documents and runs data cleaning and
  the descriptive EDA section.
- `notebooks/02_statistical_analysis.ipynb` explains the hypotheses, test
  choice, calculated results, and interpretations.
- `notebooks/03_feature_engineering.ipynb` documents feature definitions,
  score construction, and validation without fitting a model.
- `dashboard/dashboard.png` is an image asset, not a row-level dataset or
  interactive Tableau workbook.
- The repository has BigQuery SQL referring to user, event, subscription,
  payment, and experiment-assignment tables. Those source tables are not
  present as local CSVs in `data/`; BigQuery-derived headline values already
  documented in the README have not been re-executed here.
- The project README describes the data as realistic synthetic portfolio
  data. The local experiment rows are the only populated user-level dataset
  available in this workspace.

## Existing work assessment

### Reusable

- SQL files `sql/01_data_quality.sql` through `sql/11_cohort_retention.sql`
  cover quality checks, ordered funnel analysis, segmentation, retention,
  monetization, A/B dataset preparation, product KPIs, and activity analysis.
- `python/ab_test_analysis.ipynb` and `python/ab_test_summary.py` contain
  reusable experiment methods and validated summaries.
- `app.py` integrates the populated local analytics, ML evaluation, SQL
  inventory, and documented project-level analysis with clear source labels.
- `dashboard/dashboard.png` and the public Tableau attribution in the README
  are preserved as historical/reference assets.

### Retained pending review

- `python/generate_sql_outputs.py` is 0 bytes and cannot currently generate
  output files.
- `docs/PROJECT_MODIFICATION_PLAN.md` and `docs/SQL_VIVA_NOTES.md` are 0 bytes.
- `outputs/sql/` contains six zero-byte files; legacy SQL/funnel/retention
  templates remain empty or header-only where corresponding local results are unavailable.
- `outputs/dashboard/ab_test_summary.csv` repeats the same two-row summary
  purpose as `outputs/experiments/ab_test_summary.csv`; it is kept as a
  dashboard-ready copy, not treated as a second analysis.

These files have not been deleted or rewritten during the structure
preparation. Review them in a later cleanup decision after confirming that no
external workflow depends on their current paths.

## Inventory method

Row/column counts, pandas-inferred data types, null counts, duplicate-row
counts, distinct user IDs, and category counts were computed by reading the
populated source, cleaned, feature, evaluation, retention, and summary CSVs
and enumerating the existing output CSVs.
“Unique users” is reported only where a user identifier exists; it is not
applicable to aggregate statistical-result tables.
