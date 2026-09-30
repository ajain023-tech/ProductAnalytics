# ML Model Training (Phase 6)

## Objective

Train and save three classifiers that predict `d30_retained` from the finalized Phase 5 table. This phase only fits models and saves artifacts; model performance evaluation and comparison belong to Phase 7.

## Dataset and schema

Input: `outputs/features/model_features.csv` (11,462 user rows). `user_id` is used only to verify unique records and train/test separation. The target is `d30_retained` (9,770 zeros and 1,692 ones). The only five numeric binary input features are:

- `experiment_treatment`
- `onboarding_completed`
- `trial_started`
- `paid_conversion`
- `d1_retained`

The training script enforces the exact seven-column CSV schema, required row count, binary values, unique IDs, and no missing values.

## Train/test methodology

`python/model_training.py` performs one stratified split with `test_size=0.20`, `random_state=42`, and `stratify=y`. That same `X_train`, `X_test`, `y_train`, and `y_test` partition is used to fit each of the three classifiers. The split produces 9,169 training rows and 2,293 test rows (11,462 total). The script checks disjoint user IDs and verifies target proportions remain close across partitions. A SHA-256 fingerprint of the shared test user IDs is recorded for each model in `training_metadata.csv`.

## Models and preprocessing

| Model | Setup | Preprocessing |
|---|---|---|
| Logistic Regression | `max_iter=1000`, `random_state=42` | `StandardScaler` then `LogisticRegression` in a scikit-learn Pipeline. The scaler is fit by the Pipeline on training data only. This is the primary interpretable baseline. |
| Decision Tree | `max_depth=4`, `random_state=42` | No scaling; tree splits do not require standardized inputs. Depth is constrained for interpretability. |
| K-Nearest Neighbors | `n_neighbors=5` | `StandardScaler` then `KNeighborsClassifier` in a Pipeline; scaler is fit on training data only. Scaling is needed because KNN uses distances. |

## Reproducibility and outputs

Run `python python/model_training.py`. The common split uses seed 42. The script saves `logistic_regression.joblib`, `decision_tree.joblib`, `knn.joblib`, and `training_metadata.csv` under `outputs/models/`. Metadata records model name, train/test row counts, feature count, seed, test fraction, target name, and test-user fingerprint.

The notebook `notebooks/04_ml_model_training.ipynb` runs the same training function and validates the saved estimators. No scores, predictions, confusion matrices, ROC/AUC values, or model comparisons are produced in Phase 6.

## Limitations

The dataset is an educational user-level experiment dataset. Outcome timestamps are not available, so the point-in-time availability of `paid_conversion` and `d1_retained` relative to a real prediction cutoff cannot be independently confirmed. The target is imbalanced; this phase preserves the observed distribution through stratification and defers metric selection to Phase 7. Training success does not establish predictive quality or production suitability.
