"""Train the Phase 6 D30-retention classifiers without evaluation."""

from hashlib import sha256
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "outputs" / "features" / "model_features.csv"
MODEL_DIR = PROJECT_ROOT / "outputs" / "models"
TARGET_COLUMN = "d30_retained"
ID_COLUMN = "user_id"
FEATURE_COLUMNS = (
    "experiment_treatment",
    "onboarding_completed",
    "trial_started",
    "paid_conversion",
    "d1_retained",
)
RANDOM_STATE = 42
TEST_SIZE = 0.20
EXPECTED_ROWS = 11_462
EXPECTED_TARGET_COUNTS = {0: 9_770, 1: 1_692}
ARTIFACTS = {
    "Logistic Regression": "logistic_regression.joblib",
    "Decision Tree": "decision_tree.joblib",
    "K-Nearest Neighbors": "knn.joblib",
}


def load_training_data(path=DATA_PATH):
    """Load the finalized Phase 5 table and enforce its exact schema."""
    if not path.is_file():
        raise FileNotFoundError(f"Feature dataset not found: {path}")
    data = pd.read_csv(path)
    expected_columns = [ID_COLUMN, *FEATURE_COLUMNS, TARGET_COLUMN]
    if data.columns.tolist() != expected_columns:
        raise ValueError(
            "Unexpected feature table schema. Expected exactly: "
            + ", ".join(expected_columns)
        )
    if len(data) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, found {len(data)}.")
    if data[ID_COLUMN].isna().any() or not data[ID_COLUMN].is_unique:
        raise ValueError("user_id must be non-missing and unique.")
    if data.isna().any().any():
        raise ValueError("Training data must not contain missing values.")
    if not data[TARGET_COLUMN].isin((0, 1)).all():
        raise ValueError("Target must contain only binary 0/1 values.")
    if data[TARGET_COLUMN].value_counts().sort_index().to_dict() != EXPECTED_TARGET_COUNTS:
        raise ValueError("Target distribution differs from the validated Phase 5 data.")
    for feature in FEATURE_COLUMNS:
        if not pd.api.types.is_numeric_dtype(data[feature]):
            raise ValueError(f"Feature {feature} must be numeric.")
        if not data[feature].isin((0, 1)).all():
            raise ValueError(f"Feature {feature} must contain only 0/1 values.")
    return data


def build_models():
    """Return the three requested reproducible classifiers."""
    return {
        "Logistic Regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
            ]
        ),
        "Decision Tree": DecisionTreeClassifier(max_depth=4, random_state=RANDOM_STATE),
        "K-Nearest Neighbors": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("classifier", KNeighborsClassifier(n_neighbors=5)),
            ]
        ),
    }


def run_training(data=None, output_dir=MODEL_DIR):
    """Split once, fit all classifiers on the shared training partition, and save."""
    data = load_training_data() if data is None else data
    X = data.loc[:, FEATURE_COLUMNS]
    y = data[TARGET_COLUMN]
    user_ids = data[ID_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    train_ids = set(user_ids.loc[X_train.index])
    test_ids = set(user_ids.loc[X_test.index])
    if train_ids & test_ids:
        raise ValueError("Train/test user ID overlap detected.")
    if len(X_train) + len(X_test) != len(data):
        raise ValueError("Train and test rows do not sum to the dataset total.")
    if abs(y_train.mean() - y.mean()) > 0.01 or abs(y_test.mean() - y.mean()) > 0.01:
        raise ValueError("Stratified target proportions differ more than expected.")

    output_dir.mkdir(parents=True, exist_ok=True)
    test_id_hash = sha256("\n".join(sorted(test_ids)).encode("utf-8")).hexdigest()
    metadata_rows = []
    fitted_models = build_models()
    for model_name, model in fitted_models.items():
        model.fit(X_train, y_train)
        joblib.dump(model, output_dir / ARTIFACTS[model_name])
        metadata_rows.append(
            {
                "model_name": model_name,
                "train_rows": len(X_train),
                "test_rows": len(X_test),
                "feature_count": len(FEATURE_COLUMNS),
                "random_state": RANDOM_STATE,
                "test_size": TEST_SIZE,
                "target_name": TARGET_COLUMN,
                "test_user_ids_sha256": test_id_hash,
            }
        )

    metadata = pd.DataFrame(metadata_rows)
    metadata.to_csv(output_dir / "training_metadata.csv", index=False)
    return {
        "models": fitted_models,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "train_ids": train_ids,
        "test_ids": test_ids,
        "metadata": metadata,
        "output_dir": output_dir,
    }


def main():
    data = load_training_data()
    result = run_training(data)
    print(f"Dataset rows: {len(data):,}; X shape: {data[list(FEATURE_COLUMNS)].shape}")
    print(f"Target counts: {data[TARGET_COLUMN].value_counts().sort_index().to_dict()}")
    print(
        f"Train rows: {len(result['X_train']):,}; "
        f"test rows: {len(result['X_test']):,}; shared test split across all models"
    )
    for model_name, filename in ARTIFACTS.items():
        print(f"Saved {model_name}: {result['output_dir'] / filename}")
    print(f"Saved training metadata: {result['output_dir'] / 'training_metadata.csv'}")
    print("Training complete. No evaluation metrics were calculated.")


if __name__ == "__main__":
    main()
