# Product Analytics & User Retention Analysis ? Project Workflow

**Owner:** Anushka Jain  
**Status:** Phases 1?9 are implemented for the available local user-level experiment dataset. Phase 10 audit and validation is documented separately in `docs/FINAL_PROJECT_AUDIT.md`.

The local dataset contains assignment, stage, and retention outcomes for 11,462 users. The original user, event, subscription, and payment exports referenced by historical SQL/BigQuery analysis are not available locally. Local analyses and historical project-level findings are kept clearly distinct.

## End-to-end workflow

1. **Data collection:** Inventory and document `data/ab_test_dataset.csv`; no external data collection is performed.
2. **Data cleaning:** `python/data_cleaning.py` validates identifiers, dates, variants, binary values, eligibility, missingness, and duplicates; it writes a cleaned copy and quality report without overwriting the raw source.
3. **EDA:** `python/eda_analysis.py` produces descriptive experiment allocation, ordered funnel, eligible retention, and assignment-date summaries in `outputs/eda/`.
4. **Statistical analysis:** `python/statistical_analysis.py` produces six two-sided pooled two-proportion z-tests with unpooled 95% confidence intervals. The six tests use alpha 0.05 individually and have no multiple-testing adjustment.
5. **Feature engineering:** `python/feature_engineering.py` prepares five binary inputs (`experiment_treatment`, `onboarding_completed`, `trial_started`, `paid_conversion`, `d1_retained`), with `d30_retained` as target and `user_id` as identifier.
6. **ML model training:** `python/model_training.py` uses one stratified 80/20 split (seed 42) for Logistic Regression, a depth-4 Decision Tree, and KNN with k=5. Scaling is fit within training-only pipelines for Logistic Regression and KNN.
7. **ML evaluation:** `python/model_evaluation.py` loads the saved models and evaluates the same Phase 6 test users. Metrics include accuracy, precision, recall, F1, ROC-AUC, confusion matrices, ROC points, and precision-recall points. No tuning is performed.
8. **Retention and A/B analysis:** `python/retention_analysis.py` produces exact-day eligible retention, monthly assignment-cohort retention, the Phase 3 ordered funnel, a summary of the existing six statistical tests, and an integration of the Phase 7 model results. Assignment cohorts are not acquisition cohorts.
9. **Dashboard:** `app.py` presents local outcomes, retention, experimentation, ML evaluation, SQL topic inventory, documented historical monetization, methodology, and project workflow. It does not execute SQL or query BigQuery.

## Reproducibility and interpretation

Analysis outputs are saved under `outputs/`. Training metadata records the common test-user fingerprint. Statistical and model evaluation outputs are consumed without changing their methodology or results during retention/dashboard integration. Descriptive differences are not significance tests; statistical significance is not by itself causal proof. Model metrics describe the held-out sample only and do not establish production readiness or generalization beyond this dataset.

## Source and data limitations

The local table has no raw event history, acquisition channel, device/platform, region, revenue, or payment exports. No such dimensions are fabricated. Historical SQL and README metrics refer to a broader documented project analysis and are not locally recomputed from this experiment table. See `docs/DATASET_INVENTORY.md`, `docs/RETENTION_ANALYSIS.md`, and `docs/ML_MODEL_EVALUATION.md` for scope and data provenance.
