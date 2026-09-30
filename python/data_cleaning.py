"""Validate and clean the local user-level experiment dataset."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "ab_test_dataset.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "cleaned_data"
CLEAN_DATA_PATH = OUTPUT_DIR / "cleaned_ab_test_dataset.csv"
QUALITY_REPORT_PATH = OUTPUT_DIR / "data_quality_report.csv"

EXPECTED_VARIANTS = ("control", "treatment")
BINARY_COLUMNS = (
    "onboarding_completed",
    "trial_eligible",
    "trial_started",
    "paid_eligible",
    "paid_conversion",
    "d1_eligible",
    "d1_retained",
    "d7_eligible",
    "d7_retained",
    "d30_eligible",
    "d30_retained",
)
DATETIME_COLUMNS = ("assigned_at", "signup_ts")
DATE_COLUMNS = ("data_end_date",)
ELIGIBILITY_PAIRS = (
    ("trial_eligible", "trial_started"),
    ("paid_eligible", "paid_conversion"),
    ("d1_eligible", "d1_retained"),
    ("d7_eligible", "d7_retained"),
    ("d30_eligible", "d30_retained"),
)


def load_data(path=DATA_PATH):
    """Read the source CSV without changing the original file."""
    if not path.is_file():
        raise FileNotFoundError(f"Required dataset not found: {path}")

    data = pd.read_csv(path)
    required_columns = {
        "user_id",
        "variant",
        *DATETIME_COLUMNS,
        *DATE_COLUMNS,
        *BINARY_COLUMNS,
    }
    missing_columns = sorted(required_columns - set(data.columns))
    if missing_columns:
        raise ValueError(
            f"The dataset is missing required columns: {', '.join(missing_columns)}"
        )
    return data


def check_missing_values(data):
    """Return missing counts and percentages for every column."""
    missing_counts = data.isna().sum()
    missing_percentages = (
        missing_counts / len(data) * 100
        if len(data)
        else pd.Series(0.0, index=data.columns)
    )
    return pd.DataFrame(
        {
            "Column": data.columns,
            "Missing Count": missing_counts.to_numpy(),
            "Missing %": missing_percentages.to_numpy(),
        }
    )


def check_duplicates(data):
    """Count repeated complete rows and user IDs without removing any rows."""
    duplicate_user_mask = data["user_id"].duplicated(keep=False)
    duplicate_ids = data.loc[duplicate_user_mask, "user_id"].dropna().nunique()
    return {
        "duplicate_rows": int(data.duplicated().sum()),
        "duplicate_users": int(duplicate_ids),
        "duplicate_user_rows": int(data["user_id"].duplicated().sum()),
    }


def check_user_ids(data):
    """Summarize missing, unique, and repeated user identifiers."""
    duplicate_summary = check_duplicates(data)
    return {
        "unique_users": int(data["user_id"].nunique(dropna=True)),
        "missing_user_ids": int(data["user_id"].isna().sum()),
        "duplicate_users": duplicate_summary["duplicate_users"],
        "duplicate_user_rows": duplicate_summary["duplicate_user_rows"],
    }


def check_categorical_values(data):
    """Show the observed experiment groups and flag unexpected values."""
    counts = data["variant"].value_counts(dropna=False)
    rows = []
    for variant in EXPECTED_VARIANTS:
        rows.append(
            {
                "Variant": variant,
                "User Count": int(counts.get(variant, 0)),
                "Assignment Share (%)": (
                    float(counts.get(variant, 0) / len(data) * 100)
                    if len(data)
                    else 0.0
                ),
                "Valid": True,
            }
        )

    unexpected_variants = [
        value
        for value in counts.index
        if pd.notna(value) and value not in EXPECTED_VARIANTS
    ]
    unexpected_variants.sort(key=str)
    for variant in unexpected_variants:
        rows.append(
            {
                "Variant": variant,
                "User Count": int(counts.get(variant, 0)),
                "Assignment Share (%)": (
                    float(counts.get(variant, 0) / len(data) * 100)
                    if len(data)
                    else 0.0
                ),
                "Valid": False,
            }
        )

    missing_variant_count = int(data["variant"].isna().sum())
    if missing_variant_count:
        rows.append(
            {
                "Variant": "<missing>",
                "User Count": missing_variant_count,
                "Assignment Share (%)": missing_variant_count / len(data) * 100,
                "Valid": False,
            }
        )
    return pd.DataFrame(rows)


def check_binary_columns(data):
    """Validate only the known outcome and eligibility columns."""
    rows = []
    for column in BINARY_COLUMNS:
        invalid_values = data.loc[data[column].notna(), column].loc[
            ~data.loc[data[column].notna(), column].isin((0, 1))
        ]
        rows.append(
            {
                "Column": column,
                "Observed Values": ", ".join(
                    sorted(str(value) for value in data[column].dropna().unique())
                ),
                "Invalid Value Count": int(len(invalid_values)),
            }
        )
    return pd.DataFrame(rows)


def check_eligibility_consistency(data):
    """Count outcomes marked true when their corresponding eligibility is false."""
    rows = []
    inconsistent_row_masks = []
    for eligibility_column, outcome_column in ELIGIBILITY_PAIRS:
        valid_pair = (
            data[eligibility_column].isin((0, 1))
            & data[outcome_column].isin((0, 1))
        )
        inconsistent = (
            valid_pair
            & data[eligibility_column].eq(0)
            & data[outcome_column].eq(1)
        )
        rows.append(
            {
                "Eligibility Column": eligibility_column,
                "Outcome Column": outcome_column,
                "Inconsistent Rows": int(inconsistent.sum()),
            }
        )
        inconsistent_row_masks.append(inconsistent)

    if inconsistent_row_masks:
        any_inconsistent = pd.concat(inconsistent_row_masks, axis=1).any(axis=1)
        inconsistent_rows = int(any_inconsistent.sum())
    else:
        inconsistent_rows = 0
    return pd.DataFrame(rows), inconsistent_rows


def _date_validity(data):
    parsed_dates = {}
    invalid_date_masks = []
    for column in DATETIME_COLUMNS:
        parsed = pd.to_datetime(data[column], errors="coerce", utc=True)
        parsed_dates[column] = parsed
        invalid_date_masks.append(data[column].notna() & parsed.isna())
    for column in DATE_COLUMNS:
        parsed = pd.to_datetime(data[column], errors="coerce")
        parsed_dates[column] = parsed
        invalid_date_masks.append(data[column].notna() & parsed.isna())

    if invalid_date_masks:
        invalid_cells = pd.concat(invalid_date_masks, axis=1).sum().sum()
        invalid_rows = pd.concat(invalid_date_masks, axis=1).any(axis=1)
    else:
        invalid_cells = 0
        invalid_rows = pd.Series(False, index=data.index)
    return parsed_dates, invalid_rows, int(invalid_cells)


def clean_data(data):
    """Exclude invalid records and convert retained fields to useful types."""
    duplicate_summary = check_duplicates(data)
    if duplicate_summary["duplicate_rows"] or duplicate_summary["duplicate_users"]:
        raise ValueError(
            "Duplicate rows or user IDs require investigation. No duplicate "
            "records were removed; review the source before cleaning."
        )

    missing_rows = data.isna().any(axis=1)
    invalid_variant_rows = data["variant"].notna() & ~data["variant"].isin(
        EXPECTED_VARIANTS
    )
    invalid_binary_rows = pd.Series(False, index=data.index)
    for column in BINARY_COLUMNS:
        invalid_binary_rows |= data[column].notna() & ~data[column].isin((0, 1))

    parsed_dates, invalid_date_rows, _ = _date_validity(data)
    _, inconsistent_rows = check_eligibility_consistency(data)
    inconsistent_mask = pd.Series(False, index=data.index)
    for eligibility_column, outcome_column in ELIGIBILITY_PAIRS:
        valid_pair = (
            data[eligibility_column].isin((0, 1))
            & data[outcome_column].isin((0, 1))
        )
        inconsistent_mask |= (
            valid_pair
            & data[eligibility_column].eq(0)
            & data[outcome_column].eq(1)
        )

    invalid_rows = (
        missing_rows
        | invalid_variant_rows
        | invalid_binary_rows
        | invalid_date_rows
        | inconsistent_mask
    )
    cleaned = data.loc[~invalid_rows].copy()
    cleaned["user_id"] = cleaned["user_id"].astype("string")
    cleaned["variant"] = cleaned["variant"].astype("string")
    for column in BINARY_COLUMNS:
        cleaned[column] = cleaned[column].astype("int64")
    for column, parsed in parsed_dates.items():
        cleaned[column] = parsed.loc[cleaned.index]

    if inconsistent_rows and not inconsistent_mask.any():
        raise ValueError("Eligibility consistency checks returned conflicting results.")
    return cleaned


def save_clean_data(data, path=CLEAN_DATA_PATH):
    """Save the cleaned records, creating the output directory if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False)
    return path


def build_quality_report(data, cleaned_data):
    """Create a concise, reproducible report of the input and cleaning checks."""
    missing_summary = check_missing_values(data)
    duplicate_summary = check_duplicates(data)
    variant_summary = check_categorical_values(data)
    binary_summary = check_binary_columns(data)
    _, inconsistent_row_count = check_eligibility_consistency(data)
    _, _, invalid_date_cells = _date_validity(data)

    variant_counts = data["variant"].value_counts()
    control_count = int(variant_counts.get("control", 0))
    treatment_count = int(variant_counts.get("treatment", 0))
    control_share = control_count / len(data) * 100 if len(data) else 0.0
    treatment_share = treatment_count / len(data) * 100 if len(data) else 0.0
    invalid_variants = int(
        (
            data["variant"].notna()
            & ~data["variant"].isin(EXPECTED_VARIANTS)
        ).sum()
    )
    missing_expected_variants = sum(
        int(variant_counts.get(variant, 0) == 0)
        for variant in EXPECTED_VARIANTS
    )

    metrics = [
        ("Original Rows", len(data)),
        ("Cleaned Rows", len(cleaned_data)),
        ("Rows Removed", len(data) - len(cleaned_data)),
        ("Unique Users (Cleaned)", cleaned_data["user_id"].nunique(dropna=True)),
        ("Duplicate Rows", duplicate_summary["duplicate_rows"]),
        ("Duplicate Users", duplicate_summary["duplicate_users"]),
        ("Duplicate User Rows", duplicate_summary["duplicate_user_rows"]),
        ("Missing Cells", int(missing_summary["Missing Count"].sum())),
        ("Invalid Variants", invalid_variants),
        ("Missing Expected Variants", missing_expected_variants),
        ("Invalid Binary Values", int(binary_summary["Invalid Value Count"].sum())),
        ("Invalid Date/Time Values", invalid_date_cells),
        ("Inconsistent Eligibility Records", inconsistent_row_count),
        ("Control Count", control_count),
        ("Treatment Count", treatment_count),
        ("Control Assignment Share (%)", round(control_share, 4)),
        ("Treatment Assignment Share (%)", round(treatment_share, 4)),
        (
            "Assignment Share Difference (Treatment - Control, pp)",
            round(treatment_share - control_share, 4),
        ),
    ]
    return pd.DataFrame(metrics, columns=("Metric", "Value"))


def save_quality_report(report, path=QUALITY_REPORT_PATH):
    """Save the quality report as a two-column CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(path, index=False)
    return path


def main():
    data = load_data()
    missing_summary = check_missing_values(data)
    duplicate_summary = check_duplicates(data)
    user_summary = check_user_ids(data)
    variant_summary = check_categorical_values(data)
    binary_summary = check_binary_columns(data)
    eligibility_summary, inconsistent_row_count = check_eligibility_consistency(data)

    print("DATASET INSPECTION")
    print(f"Shape: {data.shape}")
    print(f"Columns: {list(data.columns)}")
    print("\nData types:")
    print(data.dtypes.to_string())
    print("\nFirst five rows:")
    print(data.head().to_string(index=False))
    print(f"\nUnique user IDs: {user_summary['unique_users']}")
    print("\nMissing values by column:")
    print(missing_summary.to_string(index=False))
    print(f"\nDuplicate check: {duplicate_summary}")
    print("\nExperiment variant distribution:")
    print(variant_summary.to_string(index=False))
    print("\nBinary validation:")
    print(binary_summary.to_string(index=False))
    print("\nEligibility consistency:")
    print(eligibility_summary.to_string(index=False))

    cleaned = clean_data(data)
    quality_report = build_quality_report(data, cleaned)
    clean_path = save_clean_data(cleaned)
    report_path = save_quality_report(quality_report)

    metrics = dict(zip(quality_report["Metric"], quality_report["Value"]))
    print("\nDATA CLEANING SUMMARY")
    print(f"Rows before cleaning: {float(metrics['Original Rows']):.0f}")
    print(f"Rows after cleaning: {float(metrics['Cleaned Rows']):.0f}")
    print(f"Rows removed: {float(metrics['Rows Removed']):.0f}")
    print(f"Missing values: {float(metrics['Missing Cells']):.0f}")
    print(f"Duplicate rows: {float(metrics['Duplicate Rows']):.0f}")
    print(f"Duplicate users: {float(metrics['Duplicate Users']):.0f}")
    print(f"Invalid variants: {float(metrics['Invalid Variants']):.0f}")
    print(f"Invalid binary values: {float(metrics['Invalid Binary Values']):.0f}")
    print(f"Inconsistent records: {inconsistent_row_count}")
    print(f"Cleaned dataset: {clean_path}")
    print(f"Data quality report: {report_path}")


if __name__ == "__main__":
    main()
