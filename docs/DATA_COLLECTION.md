# Data Collection

## Data source

This phase uses the local user-level subscription experiment dataset at
`data/ab_test_dataset.csv`. The project README describes the data as realistic
synthetic portfolio data created for educational purposes; it is not real
customer data.

The CSV is already present in the project. This phase does not connect to an
external service or collect new records. The raw file is treated as read-only;
the cleaning script writes processed data under `outputs/cleaned_data/`.

## Dataset size

The source file contains **11,462 rows and 16 columns**, with **11,462 unique
user IDs**. These values were measured from the local CSV with Pandas.

## Important data fields

The table below lists fields present in the source CSV. pandas reads the
identifier and category as strings, timestamp/date fields as strings, and the
outcome and eligibility fields as integers. The cleaning step parses the date
fields and retains binary fields as integers.

| Column | Meaning | Source data type |
|---|---|---|
| `user_id` | Unique user identifier in this file | string |
| `variant` | Experiment assignment (`control` or `treatment`) | string |
| `assigned_at` | Time the user was assigned to an experiment group | string (timestamp) |
| `signup_ts` | User signup timestamp | string (timestamp) |
| `data_end_date` | End date of the dataset's observation period | string (date) |
| `onboarding_completed` | Whether onboarding was completed (0/1) | integer |
| `trial_eligible` | Whether the user is eligible for the trial outcome (0/1) | integer |
| `trial_started` | Whether the user started a trial (0/1) | integer |
| `paid_eligible` | Whether the user is eligible for the paid-conversion outcome (0/1) | integer |
| `paid_conversion` | Whether the user converted to paid (0/1) | integer |
| `d1_eligible` | Whether the user has an observable D1 retention window (0/1) | integer |
| `d1_retained` | Whether the user was retained on D1 (0/1) | integer |
| `d7_eligible` | Whether the user has an observable D7 retention window (0/1) | integer |
| `d7_retained` | Whether the user was retained on D7 (0/1) | integer |
| `d30_eligible` | Whether the user has an observable D30 retention window (0/1) | integer |
| `d30_retained` | Whether the user was retained on D30 (0/1) | integer |

## Experiment group counts

The actual values are lowercase in the CSV:

| Variant | Users | Assignment share |
|---|---:|---:|
| `control` | 5,677 | 49.53% |
| `treatment` | 5,785 | 50.47% |

The treatment assignment share is **0.94 percentage points** higher than the
control share. The cleaning step preserves the original valid labels; it does
not change their case or assignment.

## Limits of the local source

This file supports user-level experiment and retention-flag checks. It does not
contain acquisition channel, platform, device, region, or raw event-history
columns. Those fields are not created or inferred during data collection or
cleaning.
