"""Build local retention, assignment-cohort, and experiment summaries."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "ab_test_dataset.csv"
STATISTICS = ROOT / "outputs" / "statistics" / "statistical_test_results.csv"
MODEL_METRICS = ROOT / "outputs" / "evaluation" / "model_comparison.csv"
MODEL_CM = ROOT / "outputs" / "evaluation" / "confusion_matrices.csv"
OUT = ROOT / "outputs" / "retention"
DAYS = {
    "D1": ("d1_eligible", "d1_retained"),
    "D7": ("d7_eligible", "d7_retained"),
    "D30": ("d30_eligible", "d30_retained"),
}
VARIANTS = ("control", "treatment")
FUNNEL_REQUIRED = (
    "user_id", "variant", "onboarding_completed", "trial_eligible",
    "trial_started", "paid_eligible", "paid_conversion",
)


def load_data():
    data = pd.read_csv(SOURCE)
    required = {
        "user_id", "variant", "assigned_at", "onboarding_completed",
        "trial_eligible", "trial_started", "paid_eligible", "paid_conversion",
        *(c for pair in DAYS.values() for c in pair),
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Source missing required fields: {', '.join(missing)}")
    if data.user_id.isna().any() or not data.user_id.is_unique:
        raise ValueError("Expected one row per non-missing user_id.")
    if set(data.variant.dropna().unique()) != set(VARIANTS) or data.variant.isna().any():
        raise ValueError("Expected control and treatment variants only.")
    data["assigned_at"] = pd.to_datetime(data.assigned_at, errors="coerce", utc=True)
    if data.assigned_at.isna().any():
        raise ValueError("Assignment timestamps must be present and parseable.")
    return data


def calculate_retention(data):
    overall = []
    for day, (eligible, retained) in DAYS.items():
        group = data.loc[data[eligible].eq(1)]
        n, successes = len(group), int(group[retained].sum())
        rate = successes / n if n else np.nan
        overall.append({"metric": day, "eligible_users": n, "retained_users": successes, "retention_rate": rate})

    variant_rows = []
    for day, (eligible, retained) in DAYS.items():
        rates = {}
        counts = {}
        for variant in VARIANTS:
            group = data.loc[data.variant.eq(variant) & data[eligible].eq(1)]
            counts[variant] = len(group)
            rates[variant] = int(group[retained].sum()) / len(group) if len(group) else np.nan
        variant_rows.append({
            "metric": day,
            "control_eligible_users": counts["control"],
            "control_rate": rates["control"],
            "treatment_eligible_users": counts["treatment"],
            "treatment_rate": rates["treatment"],
            "difference_pp": (rates["treatment"] - rates["control"]) * 100,
        })

    rates = {r["metric"]: r["retention_rate"] for r in overall}
    decay = []
    for start, end in (("D1", "D7"), ("D7", "D30"), ("D1", "D30")):
        decay.append({"transition": f"{start}_to_{end}", "start_rate": rates[start], "end_rate": rates[end], "change_pp": (rates[end] - rates[start]) * 100})
    return pd.DataFrame(overall), pd.DataFrame(variant_rows), pd.DataFrame(decay)


def calculate_funnel(data):
    # Preserve Phase 3 ordered stage/eligibility definitions.
    onboarding = data.onboarding_completed.eq(1)
    trial = onboarding & data.trial_eligible.eq(1) & data.trial_started.eq(1)
    paid = trial & data.paid_eligible.eq(1) & data.paid_conversion.eq(1)
    counts = [len(data), int(onboarding.sum()), int(trial.sum()), int(paid.sum())]
    names = ["Assigned", "Onboarding Completed", "Trial Started", "Paid Conversion"]
    rows = []
    for i, (name, count) in enumerate(zip(names, counts)):
        prior = counts[i - 1] if i else count
        next_count = counts[i + 1] if i < len(counts) - 1 else count
        rows.append({
            "stage": name,
            "users": count,
            "conversion_from_previous": count / prior if prior else np.nan,
            "dropoff_users": count - next_count if i < len(counts) - 1 else 0,
            "dropoff_rate": (count - next_count) / count if count else 0.0,
        })
    return pd.DataFrame(rows)


def calculate_cohorts(data):
    frame = data.copy()
    frame["assignment_cohort"] = frame.assigned_at.dt.strftime("%Y-%m")
    rows = []
    for cohort, group in frame.groupby("assignment_cohort", sort=True):
        row = {"assignment_cohort": cohort, "assigned_users": len(group)}
        for day, (eligible, retained) in DAYS.items():
            eligible_group = group.loc[group[eligible].eq(1)]
            n = len(eligible_group)
            row[f"{day.lower()}_eligible_users"] = n
            row[f"{day.lower()}_retained_users"] = int(eligible_group[retained].sum())
            row[f"{day.lower()}_retention"] = row[f"{day.lower()}_retained_users"] / n if n else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def prepare_ab_summary():
    tests = pd.read_csv(STATISTICS)
    expected_metrics = ["onboarding_completed", "trial_started", "paid_conversion", "d1_retained", "d7_retained", "d30_retained"]
    tests = tests.set_index("metric").loc[expected_metrics].reset_index()
    return tests.rename(columns={
        "control_rate": "control_rate",
        "treatment_rate": "treatment_rate",
        "absolute_difference_pp": "difference_pp",
        "p_value": "p_value",
        "ci_lower_pp": "ci_lower_pp",
        "ci_upper_pp": "ci_upper_pp",
        "significant_at_0_05": "significant_at_0_05",
    })[["metric", "control_eligible_users", "control_successes", "control_rate",
       "treatment_eligible_users", "treatment_successes", "treatment_rate",
       "difference_pp", "p_value", "ci_lower_pp", "ci_upper_pp", "significant_at_0_05"]]


def prepare_ml_summary():
    metrics = pd.read_csv(MODEL_METRICS)
    cm = pd.read_csv(MODEL_CM)
    merged = metrics.merge(cm, on="model", validate="one_to_one")
    return merged.rename(columns={"f1_score": "f1"})[[
        "model", "accuracy", "precision", "recall", "f1", "roc_auc",
        "true_positive", "true_negative", "false_positive", "false_negative",
    ]]


def make_plots(overall, by_variant, cohorts, funnel, decay):
    colors = {"control": "#2878A5", "treatment": "#D48623"}
    fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
    x = np.arange(3); width = 0.34
    for j, variant in enumerate(VARIANTS):
        vals = by_variant.set_index("metric").loc[["D1", "D7", "D30"], f"{variant}_rate"] * 100
        ax.bar(x + (j - .5) * width, vals, width, label=variant.title(), color=colors[variant])
        for xp, val in zip(x + (j - .5) * width, vals): ax.text(xp, val + .6, f"{val:.1f}%", ha="center", fontsize=9)
    ax.set(xticks=x, xticklabels=["D1", "D7", "D30"], ylabel="Retention (%)", title="Retention by Experiment Variant")
    ax.set_ylim(0, max(by_variant[["control_rate", "treatment_rate"]].max()) * 115)
    ax.legend(frameon=False); ax.grid(axis="y", alpha=.22)
    fig.savefig(OUT / "retention_by_variant.png", dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
    for day, color in zip(("D1", "D7", "D30"), ("#2673A6", "#D58A24", "#4C956C")):
        ax.plot(cohorts.assignment_cohort, cohorts[f"{day.lower()}_retention"] * 100, marker="o", lw=2, label=day, color=color)
    ax.set(title="Retention by Monthly Assignment Cohort", xlabel="Assignment month", ylabel="Eligible users retained (%)")
    ax.grid(alpha=.25); ax.legend(frameon=False); ax.tick_params(axis="x", rotation=25)
    fig.savefig(OUT / "cohort_retention.png", dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
    ax.barh(funnel.stage, funnel.users, color="#2673A6")
    for i, n in enumerate(funnel.users): ax.text(n + max(funnel.users)*.012, i, f"{n:,}", va="center")
    ax.set(title="Ordered User Funnel", xlabel="Users", ylabel="")
    ax.grid(axis="x", alpha=.2); ax.invert_yaxis()
    fig.savefig(OUT / "funnel.png", dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
    labels = ["D1 ? D7", "D7 ? D30", "D1 ? D30"]
    vals = decay.change_pp
    bars = ax.bar(labels, vals, color=["#C75D5D" if v < 0 else "#4C956C" for v in vals])
    ax.bar_label(bars, fmt="%+.2f pp", padding=4)
    ax.axhline(0, color="#444", lw=.8)
    ax.set(title="Retention Change Between Days", ylabel="Change (percentage points)")
    ax.grid(axis="y", alpha=.22)
    fig.savefig(OUT / "retention_decay.png", dpi=200); plt.close(fig)


def write_doc(overall, variants, cohorts, ab, ml):
    def pct(x): return f"{x*100:.2f}%"
    lines = [
        "# Product Retention and Experiment Analysis (Phase 8)", "",
        "## Scope and provenance", "",
        "This integration uses the local user-level experiment dataset and existing Phase 4 statistical results and Phase 7 model evaluation outputs. It does not regenerate or replace EDA, statistical tests, model evaluation, SQL, or historical project-level BigQuery results. Local results are reproducible from the available assignment and outcome fields; historical BigQuery/Tableau findings describe a broader source dataset and are not merged into these local calculations.", "",
        "## Retention definitions and overall results", "",
        "D1, D7, and D30 rates use each day?s eligible users as the denominator and that day?s retained flag as the numerator.", "",
        "| Day | Eligible | Retained | Rate |", "|---|---:|---:|---:|"
    ]
    for r in overall.itertuples(index=False): lines.append(f"| {r.metric} | {r.eligible_users:,} | {r.retained_users:,} | {pct(r.retention_rate)} |")
    lines += ["", "## Retention by experiment variant", "", "Rates below use eligible users within each assignment arm. Differences are treatment minus control, in percentage points; these are descriptive rates.", "", "| Day | Control | Treatment | Difference (pp) |", "|---|---:|---:|---:|"]
    for r in variants.itertuples(index=False): lines.append(f"| {r.metric} | {pct(r.control_rate)} | {pct(r.treatment_rate)} | {r.difference_pp:+.2f} |")
    lines += ["", "## Assignment cohort retention", "", "Cohorts are grouped by the calendar month of `assigned_at`; they are assignment cohorts, not acquisition or signup cohorts. Within each cohort, each retention day uses only users eligible for that observation window.", "", "| Assignment month | Assigned | D1 | D7 | D30 |", "|---|---:|---:|---:|---:|"]
    for r in cohorts.itertuples(index=False): lines.append(f"| {r.assignment_cohort} | {r.assigned_users:,} | {pct(r.d1_retention)} | {pct(r.d7_retention)} | {pct(r.d30_retention)} |")
    lines += ["", "## Ordered funnel", "", "The funnel reuses Phase 3 logic: Assigned ? Onboarding Completed ? Trial Started (onboarding plus trial eligibility and start) ? Paid Conversion (prior stages plus paid eligibility and conversion).", "", "| Stage | Users | Conversion from previous |", "|---|---:|---:|"]
    # funnel is emitted below from the saved output to keep a single source of truth.
    funnel = pd.read_csv(OUT / "funnel_summary.csv")
    for r in funnel.itertuples(index=False): lines.append(f"| {r.stage} | {r.users:,} | {r.conversion_from_previous:.2%} |")
    lines += ["", "## A/B statistical results", "", "These six test results are reused from `outputs/statistics/statistical_test_results.csv`; the statistical methodology is unchanged. P-values and 95% confidence intervals are included in `ab_experiment_summary.csv`. Alpha is 0.05, with no multiple-comparison adjustment. Statistical significance is not automatically causal proof; results concern the provided experiment dataset.", ""]
    lines += ["| Metric | Control | Treatment | Difference (pp) | p-value | 95% CI (pp) | Significant |", "|---|---:|---:|---:|---:|---:|:---:|"]
    for r in ab.itertuples(index=False): lines.append(f"| {r.metric} | {r.control_rate:.2%} | {r.treatment_rate:.2%} | {r.difference_pp:+.2f} | {r.p_value:.4g} | [{r.ci_lower_pp:+.2f}, {r.ci_upper_pp:+.2f}] | {'Yes' if r.significant_at_0_05 else 'No'} |")
    lines += ["", "## ML retention results", "", "The positive class is D30 retention. Accuracy alone is insufficient because the target is imbalanced (9,770 class 0; 1,692 class 1). Logistic Regression and Decision Tree predicted no positive users at the default threshold. KNN found some positive users but produced false positives. Precision, recall, F1, and ROC-AUC add class-specific and ranking information; the model results are unchanged from Phase 7 and do not establish causality, production readiness, or generalization beyond this dataset.", "", "| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | TP | TN | FP | FN |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in ml.itertuples(index=False): lines.append(f"| {r.model} | {r.accuracy:.4f} | {r.precision:.4f} | {r.recall:.4f} | {r.f1:.4f} | {r.roc_auc:.4f} | {r.true_positive} | {r.true_negative} | {r.false_positive} | {r.false_negative} |")
    lines += ["", "## Limitations", "", "The local source contains experiment assignment and user-level stage/retention flags, but not raw event histories or acquisition channel, device, platform, region, or revenue. None are fabricated. Assignment-month groups must not be interpreted as signup/acquisition cohorts. Existing broader BigQuery/Tableau summaries are historical project-level findings based on data unavailable locally. Descriptive rate differences and statistical tests answer different questions and should not be conflated.", "", "## Outputs", "", "CSV summaries and four visualizations are stored under `outputs/retention/`."]
    (ROOT / "docs" / "RETENTION_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    data = load_data()
    overall, variants, decay = calculate_retention(data)
    cohorts = calculate_cohorts(data)
    funnel = calculate_funnel(data)
    ab = prepare_ab_summary()
    ml = prepare_ml_summary()
    overall.to_csv(OUT / "overall_retention.csv", index=False)
    variants.to_csv(OUT / "retention_by_variant.csv", index=False)
    cohorts.to_csv(OUT / "assignment_cohorts.csv", index=False)
    funnel.to_csv(OUT / "funnel_summary.csv", index=False)
    decay.to_csv(OUT / "retention_decay.csv", index=False)
    ab.to_csv(OUT / "ab_experiment_summary.csv", index=False)
    ml.to_csv(OUT / "ml_retention_summary.csv", index=False)
    make_plots(overall, variants, cohorts, funnel, decay)
    write_doc(overall, variants, cohorts, ab, ml)
    return overall, variants, cohorts, funnel, decay, ab, ml


if __name__ == "__main__":
    overall, variants, cohorts, funnel, decay, ab, ml = run()
    print("OVERALL RETENTION (fraction)")
    print(overall.to_string(index=False))
    print("\nRETENTION BY VARIANT (fraction, difference in pp)")
    print(variants.to_string(index=False))
    print(f"\nAssignment cohorts created: {len(cohorts)}")
    print("A/B statistical summary rows:", len(ab))
    print("ML retention summary rows:", len(ml))
