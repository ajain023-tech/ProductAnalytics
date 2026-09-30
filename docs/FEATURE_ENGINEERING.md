# Feature Engineering

## Objective

Prepare a validated feature table for a future model predicting D30 retention. This phase creates features only; no model is trained or evaluated.

Run `python python/feature_engineering.py` to rebuild the feature table and summary from `outputs/cleaned_data/cleaned_ab_test_dataset.csv`.

## Target and identifier

`d30_retained` is the binary target and appears only as the final label column. Its distribution is **9,770 zeros** and **1,692 ones**. `user_id` is retained as a unique identifier and is never a model input.

## Final model inputs

| Feature | Definition | Purpose |
|---|---|---|
| `experiment_treatment` | 0 for Control, 1 for Treatment | Experiment assignment indicator. |
| `onboarding_completed` | Existing 0/1 onboarding outcome | Product-journey indicator. |
| `trial_started` | Existing 0/1 trial outcome | Trial-stage indicator. |
| `paid_conversion` | Existing 0/1 paid-conversion outcome | Paid lifecycle-stage indicator. |
| `d1_retained` | Existing 0/1 D1 retention outcome | Early retention indicator. |

The five ML inputs are exactly those listed above. The `model_features.csv` column order is `user_id`, these five inputs, then `d30_retained`. Neither `early_engagement_score` nor `journey_progress_score` is included in the model feature matrix. `d7_retained` is also excluded. `feature_summary.csv` summarizes the five inputs and target; it excludes the identifier.

## Leakage and timing checks

- `d30_retained` is only the target, never an input.
- `d7_retained`, `user_id`, timestamps, and `data_end_date` are not model inputs.
- The source has no lifecycle outcome timestamps. `paid_conversion` is included as specified for this educational setup, but its availability before the D30 prediction point cannot be verified. Confirm the prediction cutoff and feature timing before real prediction.
- `d1_retained` is an earlier retention outcome than D30, though event timestamps are unavailable for independent timing verification.

## Data availability

The cleaned CSV has no acquisition channel, platform, device, region, revenue, session, click, or engagement-duration fields. No such dimensions are fabricated.

## Next phase

The five-column numerical input matrix has full column rank on the current data. No model is trained in this phase. Recheck the schema and feature timing when beginning model training.

## Outputs

- `outputs/features/model_features.csv`: 11,462 user rows, identifier, five inputs, and target.
- `outputs/features/feature_summary.csv`: summaries for five inputs and target.
- `notebooks/03_feature_engineering.ipynb`: feature definitions, creation, validation, and target distribution review.
