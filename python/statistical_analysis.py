"""Test Control vs Treatment proportions using the cleaned experiment data."""

from math import erfc, sqrt
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "outputs" / "cleaned_data" / "cleaned_ab_test_dataset.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "statistics"
RESULTS_CSV_PATH = OUTPUT_DIR / "statistical_test_results.csv"
RESULTS_TEXT_PATH = OUTPUT_DIR / "statistical_test_results.txt"

ALPHA = 0.05
Z_CRITICAL_95 = 1.959963984540054
VARIANTS = ("control", "treatment")
METRICS = (
    ("onboarding_completed", None),
    ("trial_started", "trial_eligible"),
    ("paid_conversion", "paid_eligible"),
    ("d1_retained", "d1_eligible"),
    ("d7_retained", "d7_eligible"),
    ("d30_retained", "d30_eligible"),
)

OUTPUT_COLUMNS = (
    "metric",
    "control_eligible_users",
    "control_successes",
    "control_rate",
    "treatment_eligible_users",
    "treatment_successes",
    "treatment_rate",
    "absolute_difference_pp",
    "z_statistic",
    "p_value",
    "ci_lower_pp",
    "ci_upper_pp",
    "significant_at_0_05",
)


def load_cleaned_data(path=DATA_PATH):
    """Load the cleaned dataset and check the fields required by the tests."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {path}. Run python/data_cleaning.py first."
        )

    data = pd.read_csv(path)
    required_columns = {"variant", *(column for column, _ in METRICS)}
    required_columns.update(
        eligibility for _, eligibility in METRICS if eligibility is not None
    )
    missing_columns = sorted(required_columns - set(data.columns))
    if missing_columns:
        raise ValueError(
            f"The cleaned dataset is missing required columns: "
            f"{', '.join(missing_columns)}"
        )
    if data.empty:
        raise ValueError("The cleaned dataset contains no user records.")

    observed_variants = set(data["variant"].dropna().unique())
    if data["variant"].isna().any() or observed_variants != set(VARIANTS):
        raise ValueError(
            "The cleaned dataset must contain non-missing control and treatment "
            f"variants only; observed: {sorted(str(value) for value in observed_variants)}"
        )

    binary_columns = {
        column for column, _ in METRICS
    } | {
        eligibility for _, eligibility in METRICS if eligibility is not None
    }
    for column in binary_columns:
        if data[column].isna().any() or not data[column].isin((0, 1)).all():
            raise ValueError(f"Expected only 0/1 values in {column}.")
    return data


def _count_outcome(data, variant, outcome_column, eligibility_column):
    """Return eligible users and successes for one experiment group."""
    group = data.loc[data["variant"].eq(variant)]
    if eligibility_column is not None:
        group = group.loc[group[eligibility_column].eq(1)]

    eligible_users = len(group)
    successes = int(group[outcome_column].sum())
    if eligible_users == 0:
        raise ValueError(
            f"No eligible {variant} users for {outcome_column}."
        )
    if successes > eligible_users:
        raise ValueError(
            f"Success count exceeds eligible users for {variant} "
            f"{outcome_column}."
        )
    return eligible_users, successes


def two_proportion_z_test(
    control_users,
    control_successes,
    treatment_users,
    treatment_successes,
):
    """Calculate a two-sided pooled z-test and unpooled 95% rate-difference CI."""
    if control_users <= 0 or treatment_users <= 0:
        raise ValueError("Both experiment groups must have eligible users.")
    if not 0 <= control_successes <= control_users:
        raise ValueError("Control successes must be between zero and its sample size.")
    if not 0 <= treatment_successes <= treatment_users:
        raise ValueError(
            "Treatment successes must be between zero and its sample size."
        )

    control_rate = control_successes / control_users
    treatment_rate = treatment_successes / treatment_users
    difference = treatment_rate - control_rate
    pooled_rate = (
        control_successes + treatment_successes
    ) / (control_users + treatment_users)
    pooled_standard_error = sqrt(
        pooled_rate
        * (1 - pooled_rate)
        * (1 / control_users + 1 / treatment_users)
    )
    if pooled_standard_error == 0:
        z_statistic = 0.0 if difference == 0 else float("inf")
        p_value = 1.0 if difference == 0 else 0.0
    else:
        z_statistic = difference / pooled_standard_error
        p_value = erfc(abs(z_statistic) / sqrt(2))

    unpooled_standard_error = sqrt(
        control_rate * (1 - control_rate) / control_users
        + treatment_rate * (1 - treatment_rate) / treatment_users
    )
    ci_lower = difference - Z_CRITICAL_95 * unpooled_standard_error
    ci_upper = difference + Z_CRITICAL_95 * unpooled_standard_error

    return {
        "control_rate": control_rate,
        "treatment_rate": treatment_rate,
        "absolute_difference_pp": difference * 100,
        "z_statistic": z_statistic,
        "p_value": p_value,
        "ci_lower_pp": ci_lower * 100,
        "ci_upper_pp": ci_upper * 100,
        "significant_at_0_05": bool(p_value < ALPHA),
    }


def analyze_metric(data, metric, eligibility_column):
    """Test one binary outcome with its correct eligible population."""
    outcome_column = metric
    control_users, control_successes = _count_outcome(
        data, "control", outcome_column, eligibility_column
    )
    treatment_users, treatment_successes = _count_outcome(
        data, "treatment", outcome_column, eligibility_column
    )
    test_result = two_proportion_z_test(
        control_users,
        control_successes,
        treatment_users,
        treatment_successes,
    )
    return {
        "metric": metric,
        "control_eligible_users": control_users,
        "control_successes": control_successes,
        "control_rate": test_result["control_rate"] * 100,
        "treatment_eligible_users": treatment_users,
        "treatment_successes": treatment_successes,
        "treatment_rate": test_result["treatment_rate"] * 100,
        **{
            key: value
            for key, value in test_result.items()
            if key not in ("control_rate", "treatment_rate")
        },
    }


def run_statistical_analysis(data):
    """Run all six requested tests and return a consistently ordered table."""
    rows = [
        analyze_metric(data, metric, eligibility_column)
        for metric, eligibility_column in METRICS
    ]
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def save_results(results, csv_path=RESULTS_CSV_PATH, text_path=RESULTS_TEXT_PATH):
    """Write the test table and a plain-language interpretation for each metric."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(csv_path, index=False, float_format="%.10g")

    interpretations = []
    for row in results.itertuples(index=False):
        significance = (
            "statistically significant at the 5% level"
            if row.significant_at_0_05
            else "not statistically significant at the 5% level"
        )
        direction = (
            "higher"
            if row.absolute_difference_pp > 0
            else "lower"
            if row.absolute_difference_pp < 0
            else "the same"
        )
        interpretations.append(
            f"{row.metric}: Control rate was {row.control_rate:.2f}% "
            f"({row.control_successes:,}/{row.control_eligible_users:,}); "
            f"Treatment rate was {row.treatment_rate:.2f}% "
            f"({row.treatment_successes:,}/{row.treatment_eligible_users:,}). "
            f"Treatment was {direction} by "
            f"{abs(row.absolute_difference_pp):.2f} percentage points. "
            f"The two-sided p-value was {row.p_value:.6g}; this difference is "
            f"{significance}. This is an association observed in these data and "
            "does not establish causality."
        )
    text_path.write_text(
        "Control vs Treatment: Statistical Test Interpretations\n"
        "Two-sided two-proportion z-tests; alpha = 0.05.\n"
        "Confidence intervals are 95% intervals for Treatment rate minus Control rate.\n\n"
        + "\n\n".join(interpretations)
        + "\n",
        encoding="utf-8",
    )
    return csv_path, text_path


def main():
    """Run all tests, save outputs, and print the main result table."""
    data = load_cleaned_data()
    results = run_statistical_analysis(data)
    csv_path, text_path = save_results(results)
    print("STATISTICAL ANALYSIS RESULTS")
    print(results.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    print(f"\nResults CSV: {csv_path}")
    print(f"Interpretations: {text_path}")


if __name__ == "__main__":
    main()
