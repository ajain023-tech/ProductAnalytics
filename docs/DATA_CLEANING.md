# Data Cleaning & Validation

This document records the checks run by `python/data_cleaning.py` against the
local experiment dataset. Counts describe the current source CSV and are
written again to `outputs/cleaned_data/data_quality_report.csv` each time the
script runs.

## 1. Why data cleaning was required

Before later analysis, identifiers, categories, outcome flags, dates, and
eligibility relationships need basic validation. These checks help prevent
invalid records from distorting experiment counts or retention measures. The
raw CSV is never overwritten.

## 2. Dataset before cleaning

`data/ab_test_dataset.csv` contains **11,462 rows and 16 columns**, with
**11,462 unique user IDs**. Its columns are:

`user_id`, `variant`, `assigned_at`, `signup_ts`, `data_end_date`,
`onboarding_completed`, `trial_eligible`, `trial_started`, `paid_eligible`,
`paid_conversion`, `d1_eligible`, `d1_retained`, `d7_eligible`, `d7_retained`,
`d30_eligible`, and `d30_retained`.

The project README identifies the source as realistic synthetic portfolio
data for educational purposes, not real customer data.

## 3. Missing-value analysis

The script counts missing cells in every column and reports both a count and
percentage. The current file has **0 missing cells**. No values were filled or
imputed.

## 4. Duplicate analysis

The source has **0 duplicate complete rows** and **0 repeated user IDs**.
There are 11,462 unique users. A duplicate complete row means every field in
the row repeats; a duplicate user means a `user_id` appears on more than one
row, even if other fields differ.

The script does not automatically discard duplicate records. If a duplicate
row or user ID is found, it stops with an explicit error and asks for review
before producing a cleaned dataset.

## 5. Variant validation

The only observed variants are `control` and `treatment`, both valid:

| Variant | Users | Share |
|---|---:|---:|
| `control` | 5,677 | 49.53% |
| `treatment` | 5,785 | 50.47% |

The assignment-share difference (`treatment` minus `control`) is **0.94
percentage points**. There are **0 invalid variants**, and neither expected
group is missing. Valid labels are preserved exactly as they appear in the
source.

## 6. Binary-value validation

The script validates only the actual outcome and eligibility columns. All 11
contain only `0` and `1`; there are **0 invalid binary values**.

| Column | Value 0 | Value 1 |
|---|---:|---:|
| `onboarding_completed` | 5,171 | 6,291 |
| `trial_eligible` | 0 | 11,462 |
| `trial_started` | 9,584 | 1,878 |
| `paid_eligible` | 0 | 11,462 |
| `paid_conversion` | 10,339 | 1,123 |
| `d1_eligible` | 0 | 11,462 |
| `d1_retained` | 6,793 | 4,669 |
| `d7_eligible` | 0 | 11,462 |
| `d7_retained` | 9,358 | 2,104 |
| `d30_eligible` | 0 | 11,462 |
| `d30_retained` | 9,770 | 1,692 |

## 7. Eligibility consistency checks

For each available eligibility/outcome pair, the script checks whether an
outcome is `1` while its eligibility flag is `0`. It checks trial starts,
paid conversion, and D1, D7, and D30 retention. The current dataset has
**0 inconsistent records** across these rules. Records are not silently
removed if a future source file contains such a contradiction; the cleaning
script excludes them and reports the count.

## 8. Data type conversion

The cleaned data keeps `user_id` and `variant` as strings, keeps the 11
validated binary columns as integers, parses `assigned_at` and `signup_ts` as
UTC datetimes, and parses `data_end_date` as a date/datetime value. Invalid
date/time values are counted and excluded rather than replaced with invented
dates.

## 9. Final cleaned dataset

The output is `outputs/cleaned_data/cleaned_ab_test_dataset.csv`. Missing
records, unexpected variants, invalid binary values, unparseable dates, and
eligibility-inconsistent records are explicitly counted and excluded. No
imputation is performed. Duplicate rows or IDs stop the run so they can be
investigated instead of being automatically removed.

For the current source, **11,462 rows remain and 0 rows are removed**. The
output contains **11,462 unique user IDs**. The raw source file remains
unchanged.

## 10. Final data quality summary

| Metric | Measured result |
|---|---:|
| Original rows | 11,462 |
| Cleaned rows | 11,462 |
| Rows removed | 0 |
| Unique users in cleaned data | 11,462 |
| Duplicate rows | 0 |
| Duplicate users | 0 |
| Missing cells | 0 |
| Invalid variants | 0 |
| Missing expected variants | 0 |
| Invalid binary values | 0 |
| Invalid date/time values | 0 |
| Inconsistent eligibility records | 0 |

The report CSV contains these quality counts and the experiment assignment
counts/shares. The values above are measured from the local file, not
fabricated sample results. EDA, feature engineering, and modeling are outside
this cleaning phase.
