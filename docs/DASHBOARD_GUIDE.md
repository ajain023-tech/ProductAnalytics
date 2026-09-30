# Dashboard Guide

**Project:** Product Analytics & User Retention Analysis  
**Dashboard:** Product Analytics & User Retention Dashboard  
**Owner:** Anushka Jain

Run from the project root with `python -m pip install -r requirements.txt` and `python -m streamlit run app.py`.

## Pages

- **Executive Overview:** local 11,462-user KPIs, ordered funnel, retention trend, and project objective.
- **User Funnel:** locally reproducible ordered assignment-to-onboarding-to-trial-to-paid counts, conversion, and drop-offs.
- **User & Segment Analysis:** local experiment-group comparisons; `variant` is the only meaningful category in the local assignment data.
- **Retention & Cohorts:** eligible D1/D7/D30 rates, Control/Treatment retention, monthly assignment cohorts, and retention decay. These are assignment cohorts, not acquisition cohorts.
- **A/B Experiment:** the existing six Phase 4 tests, confidence intervals, p-values, and unadjusted alpha 0.05 labels. Statistical significance is not automatic causal proof; no overall winner is declared.
- **ML Retention Prediction:** Phase 7 comparison, confusion matrices, ROC and precision-recall curves for D30 retention. The target is imbalanced; accuracy is not sufficient by itself, and no model is labeled best.
- **SQL Analysis:** SQL files 01?11 and output availability. The app displays query topics but does not execute BigQuery.
- **Documented Monetization:** historical project-level metrics from the README, clearly distinguished from local data; no local revenue is inferred.
- **Data & Methodology:** local schema, cleaning report, analysis methods, and source limits.
- **Project Workflow:** concise viva-ready pipeline sequence.

## Provenance and limitations

**Locally reproducible analysis** uses the experiment assignment/outcome CSV and validated Phase 4, Phase 7, and Phase 8 outputs. **Documented project analysis** refers to broader historical BigQuery/Tableau results based on original user, event, subscription, and payment tables not available locally. The dashboard does not claim that local data reproduces those historical analyses.

The local CSV has no raw event history, revenue, acquisition channel, device/platform, region, or demographics. No such dimensions are fabricated. `dashboard/dashboard.png` is an archived image, not an interactive Tableau workbook.
