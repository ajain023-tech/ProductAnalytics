# ML Model Evaluation (Phase 7)

## Objective

Evaluate the three Phase 6 classifiers on the exact saved test partition. Models were loaded from their existing artifacts; no retraining, tuning, or split changes were performed.

## Test-set methodology

The Phase 6 split was recreated with `test_size=0.20`, `random_state=42`, and `stratify=y`: 11,462 users total, 9,169 train rows, and 2,293 test rows. The recreated test-user SHA-256 fingerprint matches the Phase 6 metadata (`8eb6c7d15a728ebf1ebacf505b4d4e8c60de07a598fe05279139b7afd3b1c741`). No train/test user overlap was found.

The target is imbalanced: 9,770 users are not retained at D30 (class 0) and 1,692 are retained (class 1; 14.76%). Accuracy alone is therefore insufficient.

## Metrics

Precision, recall, and F1 treat `d30_retained=1` as the positive class and therefore describe prediction of retained users. Precision is the share of predicted retained users who were retained; recall is the share of retained users identified; F1 is their harmonic mean. Accuracy is the overall correct fraction. ROC-AUC measures ranking discrimination across thresholds using positive-class probabilities.

## Results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.8526 | 0.0000 | 0.0000 | 0.0000 | 0.6652 |
| Decision Tree | 0.8526 | 0.0000 | 0.0000 | 0.0000 | 0.6630 |
| K-Nearest Neighbors | 0.7322 | 0.1974 | 0.2663 | 0.2267 | 0.5597 |

### Confusion matrices

| Model | TN | FP | FN | TP |
|---|---:|---:|---:|---:|
| Logistic Regression | 1955 | 0 | 338 | 0 |
| Decision Tree | 1955 | 0 | 338 | 0 |
| K-Nearest Neighbors | 1589 | 366 | 248 | 90 |

For this use case, a false positive labels a user as likely retained when they were not retained by D30; this can misdirect retention outreach or product decisions. A false negative misses a user who was retained and may distort estimates of which behaviors accompany retention. The preferred balance depends on the action taken and its cost.

## Interpretation

Compare precision, recall, F1, ROC-AUC, and accuracy together. Higher recall finds more eventual retained users but can lower precision; higher precision makes positive predictions more reliable but can miss more retained users. ROC-AUC summarizes threshold-independent ranking, not the quality of a particular operating threshold. No single model is declared best from accuracy alone.

## Limitations

These results describe only this held-out sample from the supplied educational dataset. They do not establish causality, production readiness, or generalization beyond this dataset. The target is imbalanced, and outcome timestamps are unavailable to independently verify point-in-time feature availability. No hyperparameter tuning was performed.

## Saved outputs

Metric and curve tables plus report-ready PNGs are saved under `outputs/evaluation/`.
