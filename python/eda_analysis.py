"""Create descriptive EDA summaries and charts from the cleaned dataset."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "outputs" / "cleaned_data" / "cleaned_ab_test_dataset.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "eda"

VARIANT_ORDER = ("control", "treatment")
OUTCOME_COLUMNS = (
    "onboarding_completed",
    "trial_started",
    "paid_conversion",
    "d1_retained",
    "d7_retained",
    "d30_retained",
)
METRIC_LABELS = {
    "onboarding_completed": "Onboarding",
    "trial_started": "Trial",
    "paid_conversion": "Paid",
    "d1_retained": "D1 Retention",
    "d7_retained": "D7 Retention",
    "d30_retained": "D30 Retention",
}
RETENTION_COLUMNS = {
    "D1": ("d1_eligible", "d1_retained"),
    "D7": ("d7_eligible", "d7_retained"),
    "D30": ("d30_eligible", "d30_retained"),
}
FUNNEL_COLUMNS = (
    "user_id",
    "variant",
    "onboarding_completed",
    "trial_eligible",
    "trial_started",
    "paid_eligible",
    "paid_conversion",
)


def load_cleaned_data(path=DATA_PATH):
    """Load the validated dataset and confirm fields required by this analysis."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {path}. Run python/data_cleaning.py first."
        )

    data = pd.read_csv(path)
    required_columns = {
        *FUNNEL_COLUMNS,
        *OUTCOME_COLUMNS,
        *(column for pair in RETENTION_COLUMNS.values() for column in pair),
        "assigned_at",
        "signup_ts",
        "data_end_date",
    }
    missing_columns = sorted(required_columns - set(data.columns))
    if missing_columns:
        raise ValueError(
            f"The cleaned dataset is missing required columns: "
            f"{', '.join(missing_columns)}"
        )
    if data.empty:
        raise ValueError("The cleaned dataset contains no user records.")

    for column in (
        "assigned_at",
        "signup_ts",
        "data_end_date",
    ):
        data[column] = pd.to_datetime(data[column], errors="coerce", utc=True)
    if data["variant"].isna().any():
        raise ValueError("The cleaned dataset contains missing experiment variants.")
    unexpected_variants = sorted(set(data["variant"]) - set(VARIANT_ORDER))
    if unexpected_variants:
        raise ValueError(
            f"Unexpected experiment variants in cleaned data: "
            f"{', '.join(unexpected_variants)}"
        )
    return data


def _rate(successes, eligible_users):
    """Return a percentage rate, or zero when the eligible group is empty."""
    return float(successes / eligible_users * 100) if eligible_users else 0.0


def _funnel_counts(data):
    """Count users who reach each stage in the ordered journey."""
    assigned_users = len(data)
    onboarding_users = int(data["onboarding_completed"].eq(1).sum())
    onboarding_mask = data["onboarding_completed"].eq(1)
    trial_mask = (
        onboarding_mask
        & data["trial_eligible"].eq(1)
        & data["trial_started"].eq(1)
    )
    paid_mask = (
        trial_mask
        & data["paid_eligible"].eq(1)
        & data["paid_conversion"].eq(1)
    )
    return {
        "Assigned": assigned_users,
        "Onboarding Completed": onboarding_users,
        "Trial Started": int(trial_mask.sum()),
        "Paid Conversion": int(paid_mask.sum()),
    }


def calculate_basic_statistics(data):
    """Summarize dataset size, group allocation, and recorded user outcomes."""
    users = len(data)
    control_users = int(data["variant"].eq("control").sum())
    treatment_users = int(data["variant"].eq("treatment").sum())
    metrics = [
        ("Total Users", users),
        ("Total Columns", len(data.columns)),
        ("Control Users", control_users),
        ("Treatment Users", treatment_users),
        ("Control Percentage", _rate(control_users, users)),
        ("Treatment Percentage", _rate(treatment_users, users)),
        ("Onboarding Users", int(data["onboarding_completed"].sum())),
        ("Trial Users", int(data["trial_started"].sum())),
        ("Paid Users", int(data["paid_conversion"].sum())),
        ("D1 Retained Users", int(data["d1_retained"].sum())),
        ("D7 Retained Users", int(data["d7_retained"].sum())),
        ("D30 Retained Users", int(data["d30_retained"].sum())),
    ]
    return pd.DataFrame(metrics, columns=("Metric", "Value"))


def analyze_experiment_groups(data):
    """Return assignment counts and shares for the observed experiment arms."""
    counts = data["variant"].value_counts().reindex(VARIANT_ORDER, fill_value=0)
    total_users = len(data)
    return pd.DataFrame(
        {
            "Variant": VARIANT_ORDER,
            "Users": [int(counts[variant]) for variant in VARIANT_ORDER],
            "Percentage": [
                _rate(int(counts[variant]), total_users)
                for variant in VARIANT_ORDER
            ],
        }
    )


def analyze_funnel(data):
    """Calculate cumulative funnel counts, step rates, and step drop-offs."""
    stage_names = (
        "Assigned",
        "Onboarding Completed",
        "Trial Started",
        "Paid Conversion",
    )
    counts = _funnel_counts(data)
    rows = []
    for index, stage in enumerate(stage_names):
        users = counts[stage]
        previous_users = counts[stage_names[index - 1]] if index else users
        next_users = (
            counts[stage_names[index + 1]]
            if index < len(stage_names) - 1
            else users
        )
        conversion_rate = _rate(users, previous_users) if index else 100.0
        dropoff_users = users - next_users if index < len(stage_names) - 1 else 0

        rows.append(
            {
                "Stage": stage,
                "Users": users,
                "Conversion_Rate": conversion_rate,
                "Dropoff_Users": dropoff_users,
                "Dropoff_Percentage": _rate(dropoff_users, users),
            }
        )
    return pd.DataFrame(rows)


def analyze_retention(data):
    """Calculate retention using each day’s eligible users as its denominator."""
    rows = []
    for day, (eligibility_column, retained_column) in RETENTION_COLUMNS.items():
        eligible_users = int(data[eligibility_column].sum())
        retained_users = int(
            data.loc[data[eligibility_column].eq(1), retained_column].sum()
        )
        rows.append(
            {
                "Retention_Day": day,
                "Eligible_Users": eligible_users,
                "Retained_Users": retained_users,
                "Retention_Rate": _rate(retained_users, eligible_users),
            }
        )
    return pd.DataFrame(rows)


def analyze_group_comparison(data):
    """Compare outcome rates, using eligibility flags when an outcome has one."""
    eligible_columns = {
        "trial_started": "trial_eligible",
        "paid_conversion": "paid_eligible",
        "d1_retained": "d1_eligible",
        "d7_retained": "d7_eligible",
        "d30_retained": "d30_eligible",
    }
    rows = []
    for column in OUTCOME_COLUMNS:
        rates = {}
        for variant in VARIANT_ORDER:
            group = data.loc[data["variant"].eq(variant)]
            eligible_column = eligible_columns.get(column)
            eligible_group = (
                group.loc[group[eligible_column].eq(1)]
                if eligible_column
                else group
            )
            rates[variant] = _rate(
                int(eligible_group[column].sum()), len(eligible_group)
            )
        rows.append(
            {
                "Metric": METRIC_LABELS[column],
                "Control_Rate": rates["control"],
                "Treatment_Rate": rates["treatment"],
                "Difference_pp": rates["treatment"] - rates["control"],
            }
        )
    return pd.DataFrame(rows)


def analyze_retention_by_variant(data):
    """Calculate D1, D7, and D30 retention separately for each variant."""
    rows = []
    for variant in VARIANT_ORDER:
        group = data.loc[data["variant"].eq(variant)]
        row = {"Variant": variant}
        for day, (eligibility_column, retained_column) in RETENTION_COLUMNS.items():
            eligible_users = int(group[eligibility_column].sum())
            retained_users = int(
                group.loc[group[eligibility_column].eq(1), retained_column].sum()
            )
            row[f"{day}_Retention"] = _rate(retained_users, eligible_users)
        rows.append(row)
    return pd.DataFrame(rows)


def analyze_funnel_by_variant(data):
    """Calculate ordered funnel counts and stage conversion by experiment arm."""
    rows = []
    for variant in VARIANT_ORDER:
        group = data.loc[data["variant"].eq(variant)]
        counts = _funnel_counts(group)
        assigned_users = counts["Assigned"]
        onboarding_users = counts["Onboarding Completed"]
        trial_users = counts["Trial Started"]
        paid_users = counts["Paid Conversion"]
        rows.append(
            {
                "Variant": variant,
                "Assigned Users": assigned_users,
                "Onboarding": onboarding_users,
                "Trial": trial_users,
                "Paid": paid_users,
                "Onboarding Rate": _rate(onboarding_users, assigned_users),
                "Trial Rate": _rate(trial_users, onboarding_users),
                "Paid Rate": _rate(paid_users, trial_users),
            }
        )
    return pd.DataFrame(rows)


def analyze_time_trend(data):
    """Summarize monthly assignments when timestamps span multiple months."""
    dates = data["assigned_at"].dropna()
    monthly = dates.dt.strftime("%Y-%m").value_counts().sort_index()
    if monthly.size < 2:
        return None, "Assignment dates span fewer than two months; no monthly trend was created."

    trend = pd.DataFrame(
        {"Month": monthly.index, "Assigned_Users": monthly.to_numpy(dtype=int)}
    )
    delay_minutes = (
        data["assigned_at"] - data["signup_ts"]
    ).dt.total_seconds() / 60
    delay_minutes = delay_minutes.dropna()
    descriptive_statistics = pd.DataFrame(
        [
            {
                "Field": "Assignment minus signup delay (minutes)",
                "Count": int(delay_minutes.count()),
                "Mean": float(delay_minutes.mean()),
                "Median": float(delay_minutes.median()),
                "Minimum": float(delay_minutes.min()),
                "Maximum": float(delay_minutes.max()),
            }
        ]
    )
    date_range = (
        f"{dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}"
    )
    note = (
        f"Monthly assignment counts cover {monthly.size} months ({date_range}). "
        "April is a partial month because observations begin on April 15. "
        "This is an assignment trend, "
        "not a cohort analysis."
    )
    return (trend, descriptive_statistics), note


def calculate_key_insights(
    data,
    funnel,
    retention,
    comparison,
    funnel_by_variant,
):
    """Generate concise observations from the calculated tables."""
    transitions = funnel.iloc[1:].copy()
    weakest_stage = transitions.loc[transitions["Conversion_Rate"].idxmin()]
    dropoff_stages = (
        "Assigned -> Onboarding",
        "Onboarding -> Trial",
        "Trial -> Paid",
    )
    dropoff_rows = funnel.iloc[:-1]
    largest_dropoff_position = int(
        np.argmax(dropoff_rows["Dropoff_Users"].to_numpy(dtype=int))
    )
    largest_dropoff = dropoff_rows.iloc[largest_dropoff_position]
    retention_rates = retention["Retention_Rate"].to_numpy(dtype=float)
    retention_declines = retention_rates[:-1] - retention_rates[1:]
    interval_labels = ("D1 to D7", "D7 to D30")
    largest_retention_decline = int(np.argmax(retention_declines))
    onboarding_comparison = comparison.loc[
        comparison["Metric"].eq("Onboarding")
    ].iloc[0]
    paid_comparison = comparison.loc[comparison["Metric"].eq("Paid")].iloc[0]
    d30_comparison = comparison.loc[
        comparison["Metric"].eq("D30 Retention")
    ].iloc[0]
    onboarding_variant = (
        "Treatment" if onboarding_comparison["Difference_pp"] > 0 else "Control"
    )
    paid_variant = "Treatment" if paid_comparison["Difference_pp"] > 0 else "Control"
    d30_variant = "Treatment" if d30_comparison["Difference_pp"] > 0 else "Control"
    control_paid = float(
        funnel_by_variant.loc[
            funnel_by_variant["Variant"].eq("control"), "Paid Rate"
        ].iloc[0]
    )
    treatment_paid = float(
        funnel_by_variant.loc[
            funnel_by_variant["Variant"].eq("treatment"), "Paid Rate"
        ].iloc[0]
    )
    if control_paid > treatment_paid:
        paid_observation = "Control"
        paid_difference = control_paid - treatment_paid
    else:
        paid_observation = "Treatment"
        paid_difference = treatment_paid - control_paid

    return [
        (
            f"The largest absolute funnel drop-off is "
            f"{dropoff_stages[largest_dropoff_position]} "
            f"({int(largest_dropoff['Dropoff_Users']):,} users)."
        ),
        (
            f"The weakest funnel conversion is {weakest_stage['Stage']} "
            f"at {weakest_stage['Conversion_Rate']:.2f}%."
        ),
        (
            f"Paid conversion from all assigned users is "
            f"{_rate(int(funnel.iloc[-1]['Users']), int(funnel.iloc[0]['Users'])):.2f}% "
            f"({int(funnel.iloc[-1]['Users']):,} of "
            f"{int(funnel.iloc[0]['Users']):,} users in the ordered funnel)."
        ),
        (
            f"Retention changes from {retention_rates[0]:.2f}% on D1 to "
            f"{retention_rates[-1]:.2f}% on D30, a decline of "
            f"{retention_rates[0] - retention_rates[-1]:.2f} percentage points; "
            f"the largest adjacent drop is {interval_labels[largest_retention_decline]} "
            f"({retention_declines[largest_retention_decline]:.2f} percentage points)."
        ),
        (
            f"{onboarding_variant} has the higher onboarding rate by "
            f"{abs(onboarding_comparison['Difference_pp']):.2f} percentage points; "
            f"{paid_variant} has the higher eligible paid-conversion rate by "
            f"{abs(paid_comparison['Difference_pp']):.2f} points; and "
            f"{d30_variant} has the higher D30 retention rate by "
            f"{abs(d30_comparison['Difference_pp']):.2f} points. "
            f"In the ordered funnel, {paid_observation} has the higher "
            f"trial-to-paid rate by {paid_difference:.2f} points. "
            "These are descriptive differences, not significance tests."
        ),
        (
            f"Among observed funnel flags, "
            f"{_funnel_order_exception_count(data):,} records have a "
            "later-stage outcome without the preceding funnel stage; the "
            "ordered funnel excludes these records from downstream stages."
        ),
    ]


def _funnel_order_exception_count(data):
    """Count users whose recorded lifecycle flags skip a prior funnel stage."""
    skips_onboarding = (
        data["trial_started"].eq(1)
        & data["onboarding_completed"].eq(0)
    )
    skips_trial = data["paid_conversion"].eq(1) & data["trial_started"].eq(0)
    return int((skips_onboarding | skips_trial).sum())


def _save_figure(figure, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return path


def create_plots(data, groups, funnel, retention, comparison,
                 retention_by_variant, funnel_by_variant, time_trend):
    """Save readable charts for the calculated EDA tables."""
    sns.set_theme(style="whitegrid", context="notebook")
    palette = {"control": "#4778A8", "treatment": "#E08B4F"}

    figure, axis = plt.subplots(figsize=(7, 4.5))
    bars = axis.bar(
        groups["Variant"].str.title(),
        groups["Users"],
        color=[palette[variant] for variant in groups["Variant"]],
    )
    axis.set_title("Control vs Treatment User Distribution")
    axis.set_ylabel("Users")
    axis.set_xlabel("Experiment Group")
    for bar, percentage in zip(bars, groups["Percentage"]):
        axis.annotate(
            f"{int(bar.get_height()):,}\n{percentage:.1f}%",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )
    _save_figure(figure, "experiment_group_distribution.png")

    figure, axis = plt.subplots(figsize=(8, 5))
    bars = axis.barh(funnel["Stage"], funnel["Users"], color="#4778A8")
    axis.invert_yaxis()
    axis.set_title("User Journey Funnel")
    axis.set_xlabel("Users reaching each ordered stage")
    axis.set_ylabel("")
    axis.set_xlim(0, max(funnel["Users"]) * 1.15)
    for bar in bars:
        axis.annotate(
            f"{int(bar.get_width()):,}",
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
        )
    _save_figure(figure, "user_funnel.png")

    stage_conversion = funnel.iloc[1:]
    figure, axis = plt.subplots(figsize=(8, 4.5))
    bars = axis.bar(
        stage_conversion["Stage"],
        stage_conversion["Conversion_Rate"],
        color="#4E9A86",
    )
    axis.set_title("Conversion Rate by Funnel Stage")
    axis.set_ylabel("Conversion rate (%)")
    axis.set_xlabel("")
    axis.set_ylim(
        0, max(10, float(stage_conversion["Conversion_Rate"].max()) * 1.18)
    )
    axis.tick_params(axis="x", rotation=12)
    for bar, value in zip(bars, stage_conversion["Conversion_Rate"]):
        axis.annotate(
            f"{value:.1f}%",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
        )
    _save_figure(figure, "funnel_conversion_rates.png")

    figure, axis = plt.subplots(figsize=(7, 4.5))
    axis.plot(
        retention["Retention_Day"],
        retention["Retention_Rate"],
        color="#7A72A8",
        marker="o",
        linewidth=2.5,
    )
    axis.set_title("User Retention Curve")
    axis.set_xlabel("Retention Day")
    axis.set_ylabel("Retention Rate (%)")
    axis.set_ylim(
        0, max(50, float(retention["Retention_Rate"].max()) * 1.2)
    )
    for day, value in zip(
        retention["Retention_Day"], retention["Retention_Rate"]
    ):
        axis.annotate(
            f"{value:.1f}%",
            (day, value),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
        )
    _save_figure(figure, "retention_curve.png")

    comparison_long = comparison.melt(
        id_vars="Metric",
        value_vars=("Control_Rate", "Treatment_Rate"),
        var_name="Variant",
        value_name="Rate",
    )
    comparison_long["Variant"] = comparison_long["Variant"].str.replace(
        "_Rate", "", regex=False
    ).str.lower()
    comparison_long["Variant"] = comparison_long["Variant"].map(
        {"control": "Control", "treatment": "Treatment"}
    )
    figure, axis = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=comparison_long,
        x="Metric",
        y="Rate",
        hue="Variant",
        hue_order=("Control", "Treatment"),
        palette=(palette["control"], palette["treatment"]),
        ax=axis,
    )
    axis.set_title("Control vs Treatment Performance")
    axis.set_xlabel("")
    axis.set_ylabel("Rate (%)")
    axis.tick_params(axis="x", rotation=18)
    axis.legend(title="Experiment Group")
    for container in axis.containers:
        axis.bar_label(container, fmt="%.1f%%", padding=2, fontsize=8)
    _save_figure(figure, "control_treatment_comparison.png")

    retention_long = retention_by_variant.melt(
        id_vars="Variant",
        var_name="Retention_Day",
        value_name="Retention_Rate",
    )
    retention_long["Retention_Day"] = pd.Categorical(
        retention_long["Retention_Day"].str.replace("_Retention", "", regex=False),
        categories=("D1", "D7", "D30"),
        ordered=True,
    )
    figure, axis = plt.subplots(figsize=(7, 4.5))
    sns.lineplot(
        data=retention_long,
        x="Retention_Day",
        y="Retention_Rate",
        hue="Variant",
        hue_order=VARIANT_ORDER,
        palette=palette,
        marker="o",
        linewidth=2.5,
        ax=axis,
    )
    axis.set_title("Retention by Experiment Group")
    axis.set_xlabel("Retention Day")
    axis.set_ylabel("Retention Rate (%)")
    axis.legend(title="Experiment Group")
    for _, row in retention_long.iterrows():
        rates_for_day = retention_long.loc[
            retention_long["Retention_Day"].eq(row["Retention_Day"]),
            "Retention_Rate",
        ]
        vertical_offset = (
            12 if row["Retention_Rate"] == rates_for_day.max() else -12
        )
        axis.annotate(
            f"{row['Retention_Rate']:.1f}%",
            (row["Retention_Day"], row["Retention_Rate"]),
            xytext=(0, vertical_offset),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )
    _save_figure(figure, "retention_by_variant.png")

    funnel_long = funnel_by_variant.melt(
        id_vars="Variant",
        value_vars=("Onboarding Rate", "Trial Rate", "Paid Rate"),
        var_name="Funnel Stage",
        value_name="Rate",
    )
    figure, axis = plt.subplots(figsize=(8, 4.5))
    sns.barplot(
        data=funnel_long,
        x="Funnel Stage",
        y="Rate",
        hue="Variant",
        hue_order=VARIANT_ORDER,
        palette=palette,
        ax=axis,
    )
    axis.set_title("Ordered Funnel Conversion by Experiment Group")
    axis.set_xlabel("")
    axis.set_ylabel("Conversion rate (%)")
    axis.legend(title="Experiment Group")
    _save_figure(figure, "funnel_by_variant.png")

    if time_trend is not None:
        trend, _ = time_trend
        figure, axis = plt.subplots(figsize=(7, 4.5))
        bars = axis.bar(trend["Month"], trend["Assigned_Users"], color="#4778A8")
        axis.set_title("Users Assigned by Month")
        axis.set_xlabel("Assignment Month")
        axis.set_ylabel("Assigned Users")
        for bar in bars:
            axis.annotate(
                f"{int(bar.get_height()):,}",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
            )
        _save_figure(figure, "time_trend.png")


def _write_csv(data, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    data.to_csv(path, index=False)
    return path


def run_eda(data):
    """Calculate summaries, save CSV/text outputs, and create all applicable plots."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    basic_summary = calculate_basic_statistics(data)
    groups = analyze_experiment_groups(data)
    funnel = analyze_funnel(data)
    retention = analyze_retention(data)
    comparison = analyze_group_comparison(data)
    retention_by_variant = analyze_retention_by_variant(data)
    funnel_by_variant = analyze_funnel_by_variant(data)
    time_trend, time_note = analyze_time_trend(data)

    retention_rates = retention["Retention_Rate"].to_numpy(dtype=float)
    summary_metrics = [
        ("Overall Paid Conversion from Assigned (%)", _rate(
            int(funnel.iloc[-1]["Users"]), int(funnel.iloc[0]["Users"])
        )),
        ("D1 to D7 Retention Decline (pp)", retention_rates[0] - retention_rates[1]),
        ("D7 to D30 Retention Decline (pp)", retention_rates[1] - retention_rates[2]),
        ("D1 to D30 Retention Decline (pp)", retention_rates[0] - retention_rates[2]),
    ]
    summary = pd.concat(
        [
            basic_summary,
            pd.DataFrame(summary_metrics, columns=("Metric", "Value")),
        ],
        ignore_index=True,
    )
    insights = calculate_key_insights(
        data, funnel, retention, comparison, funnel_by_variant
    )

    _write_csv(summary, "eda_summary.csv")
    _write_csv(funnel, "user_funnel.csv")
    _write_csv(retention, "retention_summary.csv")
    _write_csv(comparison, "control_treatment_comparison.csv")
    _write_csv(retention_by_variant, "retention_by_variant.csv")
    _write_csv(funnel_by_variant, "funnel_by_variant.csv")
    if time_trend is not None:
        trend, descriptive_statistics = time_trend
        _write_csv(trend, "time_trend.csv")
        _write_csv(descriptive_statistics, "date_descriptive_statistics.csv")
    else:
        for filename in ("time_trend.csv", "date_descriptive_statistics.csv"):
            output_path = OUTPUT_DIR / filename
            if output_path.exists():
                output_path.unlink()

    insight_path = OUTPUT_DIR / "key_insights.txt"
    insight_path.write_text(
        "\n".join(f"{index}. {insight}" for index, insight in enumerate(insights, 1))
        + "\n",
        encoding="utf-8",
    )
    create_plots(
        data,
        groups,
        funnel,
        retention,
        comparison,
        retention_by_variant,
        funnel_by_variant,
        time_trend,
    )

    return {
        "summary": summary,
        "groups": groups,
        "funnel": funnel,
        "retention": retention,
        "comparison": comparison,
        "retention_by_variant": retention_by_variant,
        "funnel_by_variant": funnel_by_variant,
        "time_trend": time_trend,
        "time_note": time_note,
        "insights": insights,
    }


def main():
    """Run the EDA from the cleaned CSV and print its key outputs."""
    data = load_cleaned_data()
    results = run_eda(data)
    print("EDA SUMMARY")
    print(results["summary"].to_string(index=False))
    print("\nUSER FUNNEL")
    print(results["funnel"].to_string(index=False))
    print("\nRETENTION SUMMARY")
    print(results["retention"].to_string(index=False))
    print("\nCONTROL VS TREATMENT")
    print(results["comparison"].to_string(index=False))
    print(f"\nTIME-BASED ANALYSIS: {results['time_note']}")
    print("\nKEY INSIGHTS")
    for index, insight in enumerate(results["insights"], 1):
        print(f"{index}. {insight}")
    print(f"\nEDA outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
