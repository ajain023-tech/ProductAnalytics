"""Create a concise A/B test summary from the existing experiment files."""

import csv
import math
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "ab_test_dataset.csv"
RESULTS_PATH = PROJECT_ROOT / "data" / "ab_test_results.csv"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "experiments" / "ab_test_summary.csv"
EXPERIMENT_NAME = "onboarding_flow_v2"
ALPHA = 0.05
Z_CRITICAL_95 = 1.959963984540054

METRICS = (
    ("onboarding_completion", "onboarding_completed", None, True),
    ("paid_conversion", "paid_conversion", "paid_eligible", False),
)

OUTPUT_COLUMNS = (
    "experiment_name",
    "metric",
    "control_users",
    "treatment_users",
    "control_conversion_rate",
    "treatment_conversion_rate",
    "absolute_uplift",
    "relative_uplift",
    "confidence_interval_lower",
    "confidence_interval_upper",
    "p_value",
    "adjusted_p_value",
    "statistically_significant",
)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(f"Required experiment file not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError(f"Required experiment file is empty: {path}")
        return reader.fieldnames, list(reader)


def as_binary(value, column, row_number):
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Expected a binary value for {column} on data row {row_number}"
        ) from error
    if number not in (0, 1):
        raise ValueError(
            f"Expected 0 or 1 for {column} on data row {row_number}"
        )
    return number


def require_columns(fields, required, path):
    missing = sorted(set(required) - set(fields))
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def close_enough(actual, expected, label, metric):
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=5e-6):
        raise ValueError(
            f"{metric} {label} differs from the existing analysis: "
            f"{actual} != {expected}"
        )


def calculate_metric(data, results, metric, success_column, eligible_column,
                     is_primary):
    groups = {"control": [], "treatment": []}
    for row_number, row in enumerate(data, start=2):
        variant = row["variant"]
        if variant not in groups:
            raise ValueError(
                f"Unexpected experiment variant {variant!r} on data row {row_number}"
            )
        if eligible_column is not None and as_binary(
            row[eligible_column], eligible_column, row_number
        ) != 1:
            continue
        success = as_binary(row[success_column], success_column, row_number)
        groups[variant].append(success)

    control_n = len(groups["control"])
    treatment_n = len(groups["treatment"])
    if not control_n or not treatment_n:
        raise ValueError(f"{metric} has no eligible users in one or both variants")

    control_success = sum(groups["control"])
    treatment_success = sum(groups["treatment"])
    control_rate = control_success / control_n
    treatment_rate = treatment_success / treatment_n
    difference = treatment_rate - control_rate

    pooled_rate = (control_success + treatment_success) / (control_n + treatment_n)
    pooled_se = math.sqrt(
        pooled_rate
        * (1 - pooled_rate)
        * (1 / control_n + 1 / treatment_n)
    )
    z_statistic = difference / pooled_se
    p_value = math.erfc(abs(z_statistic) / math.sqrt(2))

    unpooled_se = math.sqrt(
        control_rate * (1 - control_rate) / control_n
        + treatment_rate * (1 - treatment_rate) / treatment_n
    )
    ci_lower = difference - Z_CRITICAL_95 * unpooled_se
    ci_upper = difference + Z_CRITICAL_95 * unpooled_se
    relative_uplift = difference / control_rate if control_rate else float("nan")

    stored = results.get(metric)
    if stored is None:
        raise ValueError(f"{RESULTS_PATH} has no row for metric {metric!r}")

    expected_values = {
        "control_n": float(control_n),
        "treatment_n": float(treatment_n),
        "control_rate_pct": control_rate * 100,
        "treatment_rate_pct": treatment_rate * 100,
        "difference_pp": difference * 100,
        "relative_uplift_pct": relative_uplift * 100,
        "ci_low_pp": ci_lower * 100,
        "ci_high_pp": ci_upper * 100,
        "p_value": p_value,
    }
    for column, expected in expected_values.items():
        close_enough(float(stored[column]), expected, column, metric)

    adjusted_p_value = float(stored["adjusted_p_value"])
    statistically_significant = (
        p_value < ALPHA if is_primary else adjusted_p_value < ALPHA
    )
    if stored["significant"].strip().lower() != str(
        statistically_significant
    ).lower():
        raise ValueError(
            f"{metric} significance does not match the existing analysis"
        )

    return {
        "experiment_name": EXPERIMENT_NAME,
        "metric": metric,
        "control_users": control_n,
        "treatment_users": treatment_n,
        "control_conversion_rate": control_rate * 100,
        "treatment_conversion_rate": treatment_rate * 100,
        "absolute_uplift": difference * 100,
        "relative_uplift": relative_uplift * 100,
        "confidence_interval_lower": ci_lower * 100,
        "confidence_interval_upper": ci_upper * 100,
        "p_value": p_value,
        "adjusted_p_value": adjusted_p_value,
        "statistically_significant": str(statistically_significant).lower(),
    }


def main():
    dataset_fields, data = read_csv(DATA_PATH)
    results_fields, result_rows = read_csv(RESULTS_PATH)
    require_columns(
        dataset_fields,
        ("variant", "onboarding_completed", "paid_conversion", "paid_eligible"),
        DATA_PATH,
    )
    require_columns(
        results_fields,
        (
            "metric",
            "control_n",
            "treatment_n",
            "control_rate_pct",
            "treatment_rate_pct",
            "difference_pp",
            "relative_uplift_pct",
            "ci_low_pp",
            "ci_high_pp",
            "p_value",
            "adjusted_p_value",
            "significant",
        ),
        RESULTS_PATH,
    )

    results = {}
    for row in result_rows:
        if row["metric"] in results:
            raise ValueError(f"Duplicate metric in existing results: {row['metric']}")
        results[row["metric"]] = row

    summary_rows = [
        calculate_metric(data, results, *metric_spec)
        for metric_spec in METRICS
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Validated {len(summary_rows)} metrics against {RESULTS_PATH}")
    for row in summary_rows:
        print(
            f"{row['metric']}: control={row['control_conversion_rate']:.2f}%, "
            f"treatment={row['treatment_conversion_rate']:.2f}%, "
            f"uplift={row['absolute_uplift']:+.2f} pp, "
            f"p={row['p_value']:.6f}, "
            f"95% CI=[{row['confidence_interval_lower']:+.2f}, "
            f"{row['confidence_interval_upper']:+.2f}] pp, "
            f"significant={row['statistically_significant']}"
        )
    print(f"Saved summary to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
