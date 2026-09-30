# Final Project Audit & Validation

**Project:** Product Analytics & User Retention Analysis  
**Audit scope:** End-to-end repository, dataset, model, result, SQL, dashboard, and documentation checks. No analytical results or methodology were changed during this audit. Stale pre-Phase-6/9 statements in project documentation were corrected to reflect the current implementation.

## A. Project workflow

Data Collection ? Data Cleaning ? EDA ? Statistical Analysis ? Feature Engineering ? ML Model Training ? ML Evaluation ? Retention & A/B Analysis ? Streamlit Dashboard.

The workflow is implemented for the local user-level experiment dataset. Historical full-product SQL/BigQuery analysis is documented separately because its original source exports are not available locally.

## B. Dataset summary

- Raw dataset: `data/ab_test_dataset.csv`, 11,462 rows and 16 columns.
- Cleaned dataset: `outputs/cleaned_data/cleaned_ab_test_dataset.csv`, 11,462 rows.
- Raw SHA-256: `1535154A7943D207E84CAFB82A1B179C911C245D35B59C343883E998F68FA9F9` (matches the expected hash).
- Cleaned IDs are unique; there are no duplicate rows, repeated IDs, or missing cells.

## C. Data quality status

**PASS.** The data quality report records 11,462 original and cleaned rows, zero removed rows, zero duplicate rows/users, zero missing cells, zero invalid variants/binary values/dates, and zero eligibility inconsistencies.

## D. EDA status

**PASS.** `python/eda_analysis.py`, its output directory, and `docs/EDA.md` exist. EDA outputs are present. The audit compiled the script and did not rerun it, avoiding overwriting validated EDA artifacts.

## E. Statistical analysis status

**PASS.** The six Phase 4 results and text interpretations exist. All six tests remain present, and Phase 8 A/B summary rates, differences, p-values, confidence intervals, and significance flags match the existing statistical-results CSV. Methodology remains the two-sided pooled two-proportion z-test with unpooled 95% confidence intervals, alpha 0.05 per test, and no multiple-comparison adjustment.

## F. Feature engineering status

**PASS.** The final inputs are exactly `experiment_treatment`, `onboarding_completed`, `trial_started`, `paid_conversion`, and `d1_retained`; `d30_retained` is the target and `user_id` is identifier-only. The input matrix is 11,462 ? 5, has rank 5, has no missing values, and has no D7, derived-score, identifier, or target leakage. Target counts are 9,770 zeros and 1,692 ones.

## G. ML training status

**PASS.** The Logistic Regression, Decision Tree, and KNN artifacts load successfully. Logistic Regression and KNN artifacts are pipelines containing fitted `StandardScaler` steps. The Decision Tree loads as a classifier. Phase 6 metadata records 9,169 training users, 2,293 test users, and a shared test-user fingerprint. Models were not retrained for this audit.

## H. ML evaluation status

**PASS.** Phase 7 metrics and confusion matrices match the expected saved results:

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | TN | FP | FN | TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.8526 | 0.0000 | 0.0000 | 0.0000 | 0.6652 | 1,955 | 0 | 338 | 0 |
| Decision Tree | 0.8526 | 0.0000 | 0.0000 | 0.0000 | 0.6630 | 1,955 | 0 | 338 | 0 |
| K-Nearest Neighbors | 0.7322 | 0.1974 | 0.2663 | 0.2267 | 0.5597 | 1,589 | 366 | 248 | 90 |

The positive class is D30 retention. Accuracy alone is insufficient for the imbalanced target. Evaluation CSVs, curve data, and all four PNG artifacts exist. They were not regenerated during the audit.

## I. Retention and A/B status

**PASS.** Phase 8 outputs and documentation exist. Overall retention matches the output files: D1 40.73%, D7 18.36%, D30 14.76%. Control/Treatment rates and differences match: D1 40.09%/41.37% (+1.27 pp), D7 18.72%/17.99% (?0.73 pp), D30 14.50%/15.02% (+0.52 pp). Assignment cohort labels are derived from `assigned_at` and are not described as acquisition cohorts. Six A/B tests match Phase 4; the ML retention summary matches Phase 7.

## J. SQL analysis status

**PASS.** All 11 SQL files (01?11) exist. No SQL query was modified or deleted during the audit. The dashboard displays SQL topics and local export availability but does not execute SQL or claim that unavailable local user/event/subscription/payment tables were reproduced.

## K. Dashboard status

**PASS with interactive verification limitation.** The ten requested dashboard sections are defined, old placeholder routing/text is absent, `python -m py_compile app.py` passes, and the Streamlit health endpoint returned HTTP 200 (`ok`); the root endpoint returned HTTP 200. The existing structure and project branding remain in place.

Streamlit compilation and HTTP health checks passed. Full interactive page-by-page browser verification was not available in this environment.

## L. Data limitations

The local dataset contains user-level assignment, stage, eligibility, and retention flags. It does not include the original raw event, subscription, or payment exports, nor local revenue, acquisition channel, device/platform, region, demographic, or event-count dimensions. No such dimensions were fabricated. Broader historical metrics are labeled documented project analysis; calculations based on current files are labeled locally reproducible analysis. A/B significance is not causal proof; model results do not establish production readiness or generalization beyond this dataset.

## M. Reproducibility status

**PASS for compile and validation checks.** `python -m py_compile` passed for `app.py` and the seven major data/model scripts: cleaning, EDA, statistical analysis, feature engineering, model training, model evaluation, and retention analysis. Dataset schemas/counts, model loads, Phase 6 split metadata, Phase 7 metrics, Phase 8 outputs, and Phase 4 consistency were checked directly. Analysis scripts were not rerun because they write over validated outputs; model training was not run because the saved models must remain unchanged.

## N. Known limitations and remaining verification gap

- Interactive browser rendering of every dashboard page was not verified because no in-app browser backend was available. Compilation, application startup, HTTP health, root response, page route definitions, and required data-file existence were verified.
- The audit did not recompute EDA, statistical, evaluation, or retention analyses; it validated the existing artifacts and their cross-phase consistency to preserve results.
- Historical BigQuery findings cannot be locally reproduced without their source tables.

## Final validation summary

| Area | Status | Evidence |
|---|---|---|
| Data collection / structure | PASS | Required source and project files exist. |
| Data cleaning | PASS | 11,462 cleaned users; zero missingness/duplicates/removals. |
| EDA | PASS | Script, outputs, and documentation exist; compile passes. |
| Statistical analysis | PASS | Six tests present and cross-phase A/B values match. |
| Feature engineering | PASS | Exact five inputs; 11,462 ? 5; rank 5; target counts match. |
| ML training | PASS | Three artifacts load; fitted scaler pipelines and metadata validated. |
| ML evaluation | PASS | Metrics and confusion matrices match expected values. |
| Retention / A/B | PASS | Overall and variant retention match; cohorts and integrated summaries exist. |
| SQL preservation | PASS | All 11 files exist and were left untouched. |
| Dashboard | PASS with limitation | Compilation and HTTP 200 passed; interactive pages not verified. |
| Documentation integrity | PASS | Current scope, provenance, class imbalance, cohort naming, and claim limitations are documented. |
| Raw data integrity | PASS | SHA-256 matches expected value. |
| Remaining limitation | OPEN | Full interactive page-by-page browser verification unavailable. |

Generated `__pycache__` directories were removed. No analysis output was regenerated or overwritten during the audit.
