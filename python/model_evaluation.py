"""Evaluate the saved Phase 6 models on their exact shared test set."""

from hashlib import sha256
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "outputs" / "features" / "model_features.csv"
MODEL_DIR = PROJECT_ROOT / "outputs" / "models"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "evaluation"
METADATA_PATH = MODEL_DIR / "training_metadata.csv"
ID_COLUMN = "user_id"
TARGET_COLUMN = "d30_retained"
FEATURE_COLUMNS = (
    "experiment_treatment",
    "onboarding_completed",
    "trial_started",
    "paid_conversion",
    "d1_retained",
)
RANDOM_STATE = 42
TEST_SIZE = 0.20
MODEL_ARTIFACTS = {
    "Logistic Regression": "logistic_regression.joblib",
    "Decision Tree": "decision_tree.joblib",
    "K-Nearest Neighbors": "knn.joblib",
}


def load_and_split():
    """Recreate Phase 6's split and verify its saved test-user fingerprint."""
    data = pd.read_csv(DATA_PATH)
    expected = [ID_COLUMN, *FEATURE_COLUMNS, TARGET_COLUMN]
    if data.columns.tolist() != expected:
        raise ValueError("Feature table columns do not match the Phase 5 schema.")
    if len(data) != 11_462 or data.isna().any().any():
        raise ValueError("Expected 11,462 complete feature rows.")
    if not data[ID_COLUMN].is_unique:
        raise ValueError("user_id must be unique.")
    X = data.loc[:, FEATURE_COLUMNS]
    y = data[TARGET_COLUMN]
    if not y.isin((0, 1)).all() or y.value_counts().sort_index().to_dict() != {0: 9770, 1: 1692}:
        raise ValueError("Unexpected target values or class distribution.")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    train_ids = set(data.loc[X_train.index, ID_COLUMN])
    test_ids = set(data.loc[X_test.index, ID_COLUMN])
    if len(X_test) != 2293 or train_ids & test_ids:
        raise ValueError("Recreated split size or train/test separation is invalid.")
    fingerprint = sha256("\n".join(sorted(test_ids)).encode("utf-8")).hexdigest()
    metadata = pd.read_csv(METADATA_PATH)
    if set(metadata["test_user_ids_sha256"]) != {fingerprint}:
        raise ValueError("Recreated test users do not match Phase 6 metadata.")
    if set(metadata["model_name"]) != set(MODEL_ARTIFACTS):
        raise ValueError("Phase 6 metadata does not list the expected models.")
    return data, X_train, X_test, y_train, y_test, train_ids, test_ids, fingerprint


def evaluate_models():
    data, X_train, X_test, y_train, y_test, train_ids, test_ids, fingerprint = load_and_split()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows, confusion_rows, roc_rows, pr_rows = [], [], [], []
    loaded_models = {}

    for model_name, filename in MODEL_ARTIFACTS.items():
        model = joblib.load(MODEL_DIR / filename)
        if not hasattr(model, "predict_proba"):
            raise TypeError(f"{model_name} does not provide predict_proba().")
        loaded_models[model_name] = model
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)
        classes = list(model.classes_)
        if 1 not in classes:
            raise ValueError(f"{model_name} has no positive class 1.")
        positive_scores = probabilities[:, classes.index(1)]
        if len(predictions) != len(X_test) or len(positive_scores) != len(X_test):
            raise ValueError(f"{model_name} did not score every test row.")

        tn, fp, fn, tp = confusion_matrix(y_test, predictions, labels=[0, 1]).ravel()
        summary_rows.append({
            "model": model_name,
            "accuracy": accuracy_score(y_test, predictions),
            "precision": precision_score(y_test, predictions, zero_division=0),
            "recall": recall_score(y_test, predictions, zero_division=0),
            "f1_score": f1_score(y_test, predictions, zero_division=0),
            "roc_auc": roc_auc_score(y_test, positive_scores),
        })
        confusion_rows.append({
            "model": model_name,
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        })
        fpr, tpr, roc_thresholds = roc_curve(y_test, positive_scores)
        roc_rows.extend({"model": model_name, "fpr": float(a), "tpr": float(b), "threshold": float(c)}
                        for a, b, c in zip(fpr, tpr, roc_thresholds))
        precision, recall, pr_thresholds = precision_recall_curve(y_test, positive_scores)
        # The final PR point has no corresponding threshold; store thresholded points only.
        pr_rows.extend({"model": model_name, "precision": float(a), "recall": float(b), "threshold": float(c)}
                       for a, b, c in zip(precision[:-1], recall[:-1], pr_thresholds))

    metrics = pd.DataFrame(summary_rows)
    matrices = pd.DataFrame(confusion_rows)
    roc_data = pd.DataFrame(roc_rows)
    pr_data = pd.DataFrame(pr_rows)
    metrics.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False, float_format="%.10g")
    matrices.to_csv(OUTPUT_DIR / "confusion_matrices.csv", index=False)
    roc_data.to_csv(OUTPUT_DIR / "roc_curve_data.csv", index=False, float_format="%.10g")
    pr_data.to_csv(OUTPUT_DIR / "precision_recall_curve_data.csv", index=False, float_format="%.10g")
    make_plots(metrics, matrices, roc_data, pr_data)
    write_report(metrics, matrices, len(data), len(X_test), fingerprint)
    return metrics, matrices, roc_data, pr_data, loaded_models, (X_train, X_test, y_train, y_test, train_ids, test_ids)


def make_plots(metrics, matrices, roc_data, pr_data):
    colors = ["#2673A6", "#D58A24", "#4C956C"]
    fig, ax = plt.subplots(figsize=(11, 6.2), layout="constrained")
    metrics.set_index("model")[["accuracy", "precision", "recall", "f1_score", "roc_auc"]].plot(
        kind="bar", ax=ax, color=colors + ["#855E9F", "#C75D5D"], width=0.78
    )
    ax.set(title="D30 Retention Model Comparison", ylabel="Score", xlabel="")
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="lower right", ncol=2, frameon=False)
    ax.tick_params(axis="x", rotation=0)
    fig.savefig(OUTPUT_DIR / "model_comparison.png", dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4), layout="constrained")
    for ax, row in zip(axes, matrices.itertuples(index=False)):
        matrix = np.array([[row.true_negative, row.false_positive], [row.false_negative, row.true_positive]])
        ax.imshow(matrix, cmap="Blues")
        ax.set(title=row.model, xlabel="Predicted label", ylabel="Actual label", xticks=[0, 1], yticks=[0, 1])
        ax.set_xticklabels(["Not retained", "Retained"])
        ax.set_yticklabels(["Not retained", "Retained"])
        for (i, j), value in np.ndenumerate(matrix):
            ax.text(j, i, f"{value:,}", ha="center", va="center", color="black", fontsize=12)
    fig.suptitle("Confusion Matrices (Positive class: D30 retained)")
    fig.savefig(OUTPUT_DIR / "confusion_matrices.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 6), layout="constrained")
    for color, (name, group) in zip(colors, roc_data.groupby("model", sort=False)):
        score = metrics.loc[metrics.model.eq(name), "roc_auc"].iloc[0]
        ax.plot(group.fpr, group.tpr, color=color, lw=2, label=f"{name} (AUC={score:.3f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="#777777", lw=1, label="Chance")
    ax.set(title="ROC Curves", xlabel="False positive rate", ylabel="True positive rate", xlim=(0, 1), ylim=(0, 1.02))
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", frameon=False)
    fig.savefig(OUTPUT_DIR / "roc_curves.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 6), layout="constrained")
    for color, (name, group) in zip(colors, pr_data.groupby("model", sort=False)):
        ax.plot(group.recall, group.precision, color=color, lw=2, label=name)
    prevalence = 1692 / 11462
    ax.axhline(prevalence, linestyle="--", color="#777777", lw=1, label=f"Prevalence ({prevalence:.3f})")
    ax.set(title="Precision?Recall Curves", xlabel="Recall", ylabel="Precision", xlim=(0, 1), ylim=(0, 1.02))
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", frameon=False)
    fig.savefig(OUTPUT_DIR / "precision_recall_curves.png", dpi=200)
    plt.close(fig)


def write_report(metrics, matrices, total_rows, test_rows, fingerprint):
    lines = [
        "# ML Model Evaluation (Phase 7)", "",
        "## Objective", "",
        "Evaluate the three Phase 6 classifiers on the exact saved test partition. Models were loaded from their existing artifacts; no retraining, tuning, or split changes were performed.", "",
        "## Test-set methodology", "",
        f"The Phase 6 split was recreated with `test_size=0.20`, `random_state=42`, and `stratify=y`: {total_rows:,} users total, 9,169 train rows, and {test_rows:,} test rows. The recreated test-user SHA-256 fingerprint matches the Phase 6 metadata (`{fingerprint}`). No train/test user overlap was found.", "",
        "The target is imbalanced: 9,770 users are not retained at D30 (class 0) and 1,692 are retained (class 1; 14.76%). Accuracy alone is therefore insufficient.", "",
        "## Metrics", "",
        "Precision, recall, and F1 treat `d30_retained=1` as the positive class and therefore describe prediction of retained users. Precision is the share of predicted retained users who were retained; recall is the share of retained users identified; F1 is their harmonic mean. Accuracy is the overall correct fraction. ROC-AUC measures ranking discrimination across thresholds using positive-class probabilities.", "",
        "## Results", "",
        "| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |", "|---|---:|---:|---:|---:|---:|"
    ]
    for row in metrics.itertuples(index=False):
        lines.append(f"| {row.model} | {row.accuracy:.4f} | {row.precision:.4f} | {row.recall:.4f} | {row.f1_score:.4f} | {row.roc_auc:.4f} |")
    lines += ["", "### Confusion matrices", "", "| Model | TN | FP | FN | TP |", "|---|---:|---:|---:|---:|"]
    for row in matrices.itertuples(index=False):
        lines.append(f"| {row.model} | {row.true_negative} | {row.false_positive} | {row.false_negative} | {row.true_positive} |")
    lines += [
        "", "For this use case, a false positive labels a user as likely retained when they were not retained by D30; this can misdirect retention outreach or product decisions. A false negative misses a user who was retained and may distort estimates of which behaviors accompany retention. The preferred balance depends on the action taken and its cost.", "",
        "## Interpretation", "",
        "Compare precision, recall, F1, ROC-AUC, and accuracy together. Higher recall finds more eventual retained users but can lower precision; higher precision makes positive predictions more reliable but can miss more retained users. ROC-AUC summarizes threshold-independent ranking, not the quality of a particular operating threshold. No single model is declared best from accuracy alone.", "",
        "## Limitations", "",
        "These results describe only this held-out sample from the supplied educational dataset. They do not establish causality, production readiness, or generalization beyond this dataset. The target is imbalanced, and outcome timestamps are unavailable to independently verify point-in-time feature availability. No hyperparameter tuning was performed.", "",
        "## Saved outputs", "",
        "Metric and curve tables plus report-ready PNGs are saved under `outputs/evaluation/`."
    ]
    (PROJECT_ROOT / "docs" / "ML_MODEL_EVALUATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    metrics, matrices, roc_data, pr_data, models, split = evaluate_models()
    X_train, X_test, y_train, y_test, train_ids, test_ids = split
    print(f"Loaded models: {len(models)}; test rows: {len(X_test)}; overlap: {len(train_ids & test_ids)}")
    print("Test user fingerprint matches Phase 6 metadata.")
    print(metrics.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(matrices.to_string(index=False))
    print("Saved all requested CSVs, plots, and evaluation documentation.")


if __name__ == "__main__":
    main()
