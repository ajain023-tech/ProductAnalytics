"""Create interpretable, leakage-conscious features for D30 retention."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "outputs" / "cleaned_data" / "cleaned_ab_test_dataset.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "features"
FEATURES_PATH = OUTPUT_DIR / "model_features.csv"
SUMMARY_PATH = OUTPUT_DIR / "feature_summary.csv"

TARGET_COLUMN = "d30_retained"
FEATURE_COLUMNS = (
    "experiment_treatment",
    "onboarding_completed",
    "trial_started",
    "paid_conversion",
    "d1_retained",
)
SOURCE_BINARY_COLUMNS = (
    "onboarding_completed",
    "trial_started",
    "paid_conversion",
    "d1_retained",
    TARGET_COLUMN,
)
FEATURE_DESCRIPTIONS = {
    "experiment_treatment": (
        "Experiment assignment indicator: control=0, treatment=1."
    ),
    "onboarding_completed": "1 if onboarding was completed; otherwise 0.",
    "trial_started": "1 if the user started a trial; otherwise 0.",
    "paid_conversion": (
        "1 if the paid-conversion lifecycle flag is true; treated as a "
        "pre-D30 stage indicator for this educational setup, although its "
        "timestamp is unavailable."
    ),
    "d1_retained": "1 if the user was retained on D1; otherwise 0.",
    TARGET_COLUMN: "Target label: 1 if the user was retained on D30; otherwise 0.",
}


def load_cleaned_data(path=DATA_PATH):
    """Load the cleaned source and validate fields used in feature creation."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {path}. Run python/data_cleaning.py first."
        )

    data = pd.read_csv(path)
    required_columns = {"user_id", "variant", *SOURCE_BINARY_COLUMNS}
    missing_columns = sorted(required_columns - set(data.columns))
    if missing_columns:
        raise ValueError(
            f"The cleaned dataset is missing required columns: "
            f"{', '.join(missing_columns)}"
        )
    if data.empty:
        raise ValueError("The cleaned dataset contains no users.")
    if data["user_id"].isna().any() or data["user_id"].duplicated().any():
        raise ValueError("Expected one non-missing row per unique user ID.")
    if data["variant"].isna().any() or not data["variant"].isin(
        ("control", "treatment")
    ).all():
        raise ValueError("Expected only non-missing control/treatment variants.")

    for column in SOURCE_BINARY_COLUMNS:
        if data[column].isna().any() or not data[column].isin((0, 1)).all():
            raise ValueError(f"Expected only non-missing 0/1 values in {column}.")
    return data


def create_model_features(data):
    """Create only the documented predictors and keep the target separate."""
    features = pd.DataFrame(index=data.index)
    features["user_id"] = data["user_id"].astype("string")
    features["experiment_treatment"] = data["variant"].eq("treatment").astype("int64")
    for column in (
        "onboarding_completed",
        "trial_started",
        "paid_conversion",
        "d1_retained",
    ):
        features[column] = data[column].astype("int64")

    features[TARGET_COLUMN] = data[TARGET_COLUMN].astype("int64")
    return features[
        ["user_id", *FEATURE_COLUMNS, TARGET_COLUMN]
    ]


def create_feature_summary(model_features):
    """Summarize each model input and target without treating IDs as features."""
    rows = []
    for column in (*FEATURE_COLUMNS, TARGET_COLUMN):
        values = model_features[column]
        rows.append(
            {
                "feature": column,
                "data_type": str(values.dtype),
                "min": values.min(),
                "max": values.max(),
                "mean": values.mean(),
                "missing_values": int(values.isna().sum()),
                "unique_values": int(values.nunique(dropna=True)),
                "description": FEATURE_DESCRIPTIONS[column],
            }
        )
    return pd.DataFrame(
        rows,
        columns=(
            "feature",
            "data_type",
            "min",
            "max",
            "mean",
            "missing_values",
            "unique_values",
            "description",
        ),
    )


def validate_model_features(model_features):
    """Check the feature table for leakage, schema, and range problems."""
    expected_columns = ["user_id", *FEATURE_COLUMNS, TARGET_COLUMN]
    if model_features.columns.tolist() != expected_columns:
        raise ValueError("Feature table columns do not match the documented schema.")
    if model_features["user_id"].isna().any() or not model_features[
        "user_id"
    ].is_unique:
        raise ValueError("Feature table must contain one row per unique user ID.")
    if model_features[list(FEATURE_COLUMNS)].isna().any().any():
        raise ValueError("Model input features must not contain missing values.")
    if not model_features[TARGET_COLUMN].isin((0, 1)).all():
        raise ValueError("D30 target must contain only 0/1 values.")
    if not model_features["experiment_treatment"].isin((0, 1)).all():
        raise ValueError("Experiment indicator must contain only 0/1 values.")
    forbidden_features = {"d30_retained", "d7_retained", "user_id"}
    if forbidden_features.intersection(FEATURE_COLUMNS):
        raise ValueError("A target, later retention outcome, or identifier leaked in.")
    if TARGET_COLUMN not in model_features.columns:
        raise ValueError("D30 target is missing from the output table.")


def save_outputs(model_features, feature_summary):
    """Write the model-ready table and its descriptive summary."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_features.to_csv(FEATURES_PATH, index=False)
    feature_summary.to_csv(SUMMARY_PATH, index=False)
    return FEATURES_PATH, SUMMARY_PATH


def main():
    """Build, validate, and save the feature dataset and summary."""
    data = load_cleaned_data()
    model_features = create_model_features(data)
    validate_model_features(model_features)
    feature_summary = create_feature_summary(model_features)
    features_path, summary_path = save_outputs(model_features, feature_summary)

    print("FEATURE ENGINEERING SUMMARY")
    print(f"Source users: {len(data):,}")
    print(f"Feature rows: {len(model_features):,}")
    print(f"Model input features: {', '.join(FEATURE_COLUMNS)}")
    print(f"Target: {TARGET_COLUMN}")
    print("\nTarget distribution:")
    print(model_features[TARGET_COLUMN].value_counts().sort_index().to_string())
    print("\nFeature summary:")
    print(feature_summary.to_string(index=False))
    print(f"\nModel feature dataset: {features_path}")
    print(f"Feature summary: {summary_path}")


if __name__ == "__main__":
    main()
