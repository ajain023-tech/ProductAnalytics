# Product Analytics & User Retention Analysis

**Owner:** Anushka Jain  
Product and user analytics portfolio project for a mobile subscription app.

[**View Interactive Tableau Dashboard**](https://public.tableau.com/app/profile/nikita.sergeevich/viz/Project4_MobileSubscriptionProductAnalytics/ProductAnalyticsDashboard)

The project investigates the complete new-user journey from registration to paid subscription, identifies funnel bottlenecks, compares user segments, measures cohort retention and monetization, and evaluates an onboarding A/B test.

> The dataset is realistic synthetic data created for portfolio and educational purposes. It does not contain real customer information.

---

## Business Problem

A mobile subscription app is acquiring a large number of new users, but paid subscriber growth is not keeping pace.

The product team wants to understand:

1. Where users drop out between signup, onboarding, trial and paid subscription.
2. Which acquisition, device, platform, geographic and behavioral segments perform differently.
3. How D1, D7 and D30 retention develops across signup cohorts.
4. How trial conversion, cancellations and revenue vary across segments.
5. Whether a new onboarding flow should be rolled out after an A/B test.

---

## Analysis Focus

- **Data:** Users, events, subscriptions, payments, and experiment assignments.
- **Analysis:** Data quality checks, ordered funnel analysis, segmentation,
  exact-day cohort retention, monetization, and A/B testing.
- **Experiment methods:** Intention-to-treat, Sample Ratio Mismatch checks,
  two-proportion tests, confidence intervals, p-values, and Holm correction.
- **Project focus:** Product/user analytics, user journey analysis, retention,
  experimentation, statistical testing, and evaluated D30-retention classifiers.
- **Retention models:** Logistic Regression, Decision Tree, and K-Nearest
  Neighbors have been trained and evaluated. Random Forest and K-Means are
  intentionally excluded from this project.

## Intended Technology Stack

- **Python:** scripts, analysis, and application code.
- **Pandas and NumPy:** tabular data handling and numerical calculations.
- **Matplotlib and Seaborn:** EDA and report-ready analysis plots.
- **SciPy and Statsmodels:** existing statistical analysis in the A/B notebook.
- **Scikit-learn:** the three trained classifiers and their evaluation.
- **Plotly and Streamlit:** interactive dashboard charts and application.
- **SQL / BigQuery:** existing warehouse queries for data quality, funnel,
  retention, monetization, segmentation, and A/B dataset preparation.

`requirements.txt` includes the libraries used by the analysis scripts, model
training/evaluation, and Streamlit dashboard.

---

## Dataset

### Data Model

| Table | Grain | Primary Key | Main Relationships |
|---|---|---|---|
| `users` | One row per registered user | `user_id` | Base entity for events, subscriptions, payments and experiments |
| `events` | One row per product event | `event_id` | `user_id` → `users`; `anonymous_id` used for identity recovery |
| `subscriptions` | One row per subscription | `subscription_id` | `user_id` → `users` |
| `payments` | One row per payment transaction | `payment_id` | `user_id` → `users`; `subscription_id` → `subscriptions` |
| `experiment_assignments` | One row per experiment assignment record | `assignment_id` | `user_id` → `users` |

Dataset scale:

- **34,000 registered users**
- **~803K raw events**
- **5,508 subscriptions**
- **~8.4K payment records**
- **~11.6K experiment assignment records**

The observation period covers user signups from January through July 2025, with product and commercial activity observed through August 15, 2025.

---

## Data Quality & Preparation

Before calculating business metrics, the raw data was audited for:

- primary-key uniqueness
- duplicate records
- missing identifiers
- orphan foreign keys
- subscription lifecycle consistency
- payment chronology
- experiment assignment conflicts
- event-to-user identity resolution

Important findings included:

- duplicate event records were exact duplicates rather than conflicting versions
- duplicate payment rows were removed
- anonymous IDs were used to recover missing event-level `user_id` values where possible
- users assigned to conflicting A/B variants were excluded from experiment analysis

Reusable analytical views were created for cleaned events, payments, resolved event users and experiment assignments.

See [`sql/01_data_quality.sql`](sql/01_data_quality.sql).

---

## Metric Definitions

### Funnel

The ordered user funnel is:

**Signup → Onboarding Completed → Trial Started → Paid**

A user is counted at a later step only if the previous funnel step occurred first.

### Retention

Retention is based on an `app_open` event on the exact calendar day relative to signup:

- **D1** — app open exactly 1 day after signup
- **D7** — app open exactly 7 days after signup
- **D30** — app open exactly 30 days after signup

Only users with a complete observation window are included in each denominator.

### Monetization

- **Gross Revenue** — captured positive charge transactions
- **Refunds** — captured negative refund transactions
- **Net Revenue** — captured revenue after refunds
- **Trial → Paid** — paying users divided by trial starters
- **Cancellation Rate** — paid users with a recorded cancellation
- **Revenue / Payer** — net revenue divided by paying users

Revenue should not be interpreted as profit because cost and marketing-spend data are not available.

---

# Key Findings

The figures below are previously recorded BigQuery analysis results. The
funnel ordering and user-level monetization aggregation were corrected during
this audit, but BigQuery is unavailable locally, so these figures could not be
recomputed against the corrected queries. Refresh them from BigQuery before
presenting them as current results.

## 1. Product Funnel

| Funnel Step | Users | Conversion from Previous Step |
|---|---:|---:|
| Signup | 34,000 | 100.00% |
| Onboarding Completed | 18,341 | 53.94% |
| Trial Started | 5,499 | 29.98% |
| Paid | 3,281 | 59.67% |

The largest **absolute user loss** occurs between signup and onboarding.

However, the largest **percentage bottleneck** occurs between:

**Onboarding → Trial: only 29.98% conversion**

This means approximately 70% of users who complete onboarding do not start a trial.

See [`sql/02_funnel.sql`](sql/02_funnel.sql).

---

## 2. Segment Analysis

Funnel performance was compared across:

- acquisition channel
- region
- platform
- device tier
- primary goal

Several patterns emerged:

- **Referral traffic** showed comparatively strong funnel performance.
- **Paid Social** performed weakly across multiple funnel stages.
- **iOS** users converted better than Android users.
- **Low-tier devices** showed weaker onboarding, trial and paid conversion.
- Geographic differences exist, although no single region explains the entire product-level funnel problem.

The consistency of the onboarding-to-trial drop across many segments suggests that the core problem is primarily **systemic rather than isolated to one audience**.

See [`sql/03_segmentation.sql`](sql/03_segmentation.sql).

---

## 3. Retention

Overall exact-day retention:

| Metric | Retention |
|---|---:|
| D1 | **41.01%** |
| D7 | **19.07%** |
| D30 | **14.73%** |

The largest retention decline occurs between **D1 and D7**.

Monthly cohorts remain relatively stable, with no single cohort showing a dramatic structural break.

This suggests that early retention is a persistent product challenge rather than a temporary acquisition or cohort anomaly.

See [`sql/04_retention.sql`](sql/04_retention.sql).

---

## 4. Monetization

Overall monetization performance:

| Metric | Result |
|---|---:|
| Trial Users | 5,499 |
| Paying Users | 3,281 |
| Trial → Paid | **59.67%** |
| Paid Cancellation Rate | **6.71%** |
| Gross Revenue | **$145,262.81** |
| Refunds | **$2,919.03** |
| Net Revenue | **$142,343.78** |
| Refund Share | **2.01%** |
| Net Revenue / Payer | **$43.38** |

Revenue per payer is relatively similar across major segments, meaning total revenue differences are driven primarily by **user volume and conversion**, rather than large differences in payer value.

Paid Social is particularly important to monitor because it combines relatively weak funnel performance with lower monetization quality than several other acquisition channels.

See [`sql/05_monetization.sql`](sql/05_monetization.sql).

---

# A/B Test — `onboarding_flow_v2`

The experiment compared:

- **Control** — existing onboarding flow
- **Treatment** — shorter revised onboarding flow

The analysis follows an **intention-to-treat (ITT)** approach.

A Sample Ratio Mismatch check found no evidence of abnormal allocation between control and treatment.

## Primary Metric — Onboarding Completion

| Group | Rate |
|---|---:|
| Control | 53.20% |
| Treatment | 56.54% |

**Treatment effect: +3.35 percentage points**

- Relative uplift: approximately **+6.3%**
- 95% CI: approximately **[+1.52 pp, +5.17 pp]**
- p-value: **0.0003**

The treatment produced a statistically significant improvement in the experiment's primary metric.

---

## Paid Conversion Guardrail

| Group | Paid Conversion |
|---|---:|
| Control | 10.15% |
| Treatment | 9.46% |

**Observed effect: -0.69 percentage points**

95% CI:

**[-1.78 pp, +0.40 pp]**

The result is not statistically significant, but the confidence interval still includes economically meaningful negative effects.

Therefore, the experiment does **not provide sufficient evidence that paid conversion is protected at tighter business guardrails**.

Secondary metrics were evaluated using Holm correction for multiple comparisons. No downstream improvement was statistically confirmed after adjustment.

---

## Experiment Decision

### DO NOT FULL ROLLOUT YET

The new onboarding flow clearly improves onboarding completion, but the improvement has not yet been shown to propagate reliably into downstream commercial outcomes.

A full rollout would therefore be premature.

Recommended next step:

- continue or prospectively extend the experiment
- define an explicit acceptable paid-conversion guardrail
- collect enough observations to evaluate downstream effects with adequate precision
- consider a staged rollout rather than immediate 100% deployment

The Python statistical analysis includes:

- Sample Ratio Mismatch testing
- two-proportion z-tests
- 95% confidence intervals
- Holm multiple-testing correction
- paid-conversion guardrail sensitivity analysis

See:

- [`sql/06_ab_test_dataset.sql`](sql/06_ab_test_dataset.sql)
- [`python/ab_test_analysis.ipynb`](python/ab_test_analysis.ipynb)
- [`python/ab_test_summary.py`](python/ab_test_summary.py) and its
  [summary CSV](outputs/experiments/ab_test_summary.csv)
- [A/B testing viva notes](docs/AB_TEST_VIVA.md)

---

## Dashboard

The project is titled **Product Analytics & User Retention Analysis**. The
dashboard title is **Product Analytics & User Retention Dashboard**, with the
subtitle **User Journey • Retention • Experimentation • Predictive Analytics**.
The dashboard owner is Anushka Jain.

Run it from the project root:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The dashboard includes Executive Overview, User Funnel, User & Segment
Analysis, Retention & Cohorts, A/B Experiment, ML Retention Prediction, SQL
Analysis, Documented Monetization, Data & Methodology, and Project Workflow
pages. Local experiment, retention, cohort, and model results are labeled as
locally reproducible analysis. Monetization and broader historical product
metrics are labeled as documented project analysis where applicable. The app
does not execute BigQuery. Local channel, platform, device, and region fields
are unavailable and are not fabricated.
The archived Tableau screenshot remains in
[`dashboard/dashboard.png`](dashboard/dashboard.png). See the
[Dashboard Guide](docs/DASHBOARD_GUIDE.md) for data provenance and limitations.

---

## Project Structure

The current files are retained in place to preserve existing paths and
analysis. The completed analysis workflow and output locations are
documented in [`docs/PROJECT_WORKFLOW.md`](docs/PROJECT_WORKFLOW.md), and the
actual local datasets and output status are listed in
[`docs/DATASET_INVENTORY.md`](docs/DATASET_INVENTORY.md). Data collection and
the first cleaning phase are documented in
[`docs/DATA_COLLECTION.md`](docs/DATA_COLLECTION.md) and
[`docs/DATA_CLEANING.md`](docs/DATA_CLEANING.md). The completed descriptive
EDA is documented in [`docs/EDA.md`](docs/EDA.md). Statistical tests and
interpretations are documented in
[`docs/STATISTICAL_ANALYSIS.md`](docs/STATISTICAL_ANALYSIS.md). D30-retention
feature preparation and its timing assumptions are documented in
[`docs/FEATURE_ENGINEERING.md`](docs/FEATURE_ENGINEERING.md).
?   ??? ML_MODEL_TRAINING.md
?   ??? ML_MODEL_EVALUATION.md
?   ??? RETENTION_ANALYSIS.md

```text
product-analytics-user-retention/
│
├── README.md
├── app.py
├── requirements.txt
│
├── sql/
│   ├── 01_data_quality.sql
│   ├── 02_funnel.sql
│   ├── 03_segmentation.sql
│   ├── 04_retention.sql
│   ├── 05_monetization.sql
│   ├── 06_ab_test_dataset.sql
│   ├── 07_product_kpis.sql
│   ├── 08_funnel_segment_analysis.sql
│   ├── 09_user_activity_analysis.sql
│   ├── 10_funnel_summary.sql
│   └── 11_cohort_retention.sql
│
├── python/
│   ├── ab_test_analysis.ipynb
│   ├── ab_test_summary.py
│   ├── data_cleaning.py
│   ├── eda_analysis.py
│   ├── statistical_analysis.py
│   ├── feature_engineering.py
?   ??? model_training.py
?   ??? model_evaluation.py
?   ??? retention_analysis.py
│   └── generate_sql_outputs.py  # existing file is zero bytes
│
├── data/
│   ├── ab_test_dataset.csv
│   ├── ab_test_results.csv
│   ├── raw/                 # prepared; source exports are not local
│   └── processed/           # prepared for a future cleaning stage
│
├── notebooks/
│   ├── 01_data_cleaning_eda.ipynb  # data cleaning and descriptive EDA
│   ├── 02_statistical_analysis.ipynb
│   └── 03_feature_engineering.ipynb
?   ??? 04_ml_model_training.ipynb
│
├── outputs/
│   ├── dashboard/
│   ├── experiments/
│   ├── funnel/
│   ├── retention/
│   ├── sql/
│   ├── cleaned_data/        # cleaned experiment data and quality report
│   ├── eda/                 # generated descriptive tables, charts, and insights
│   ├── statistics/          # six two-proportion tests
│   ├── features/            # D30-retention features and feature summary
│   ├── models/              # three trained model artifacts and metadata
│   └── evaluation/          # evaluation metrics, curves, and charts
│
├── docs/
│   ├── DATASET_INVENTORY.md
│   ├── DATA_COLLECTION.md
│   ├── DATA_CLEANING.md
│   ├── EDA.md
│   ├── STATISTICAL_ANALYSIS.md
│   ├── FEATURE_ENGINEERING.md
│   ├── PROJECT_WORKFLOW.md
│   ├── AB_TEST_VIVA.md
│   ├── DASHBOARD_GUIDE.md
│   └── SQL_ENHANCEMENTS_VIVA.md
│
└── dashboard/
    └── dashboard.png
```

The workflow is implemented through model training, held-out evaluation,
retention/A-B integration, and the Streamlit dashboard. Phase 5 feature
engineering remains a separate preparation step; model training and
validation are documented in the Phase 6 and Phase 7 guides.
Existing source files, notebooks, SQL, and output CSVs were not moved or
removed. The zero-byte
`python/generate_sql_outputs.py`, `docs/PROJECT_MODIFICATION_PLAN.md`, and
`docs/SQL_VIVA_NOTES.md` have been identified but retained.
