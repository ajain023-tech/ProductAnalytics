# SQL Enhancements Viva Notes

- **CTE (`WITH`)**: A named temporary result used by a query. It breaks the
  funnel into readable steps such as onboarding events, trial starts, and
  payments.
- **`GROUP BY`**: Combines rows that share a value so aggregate measures can
  be calculated. It is used for signup-month, segment, and activity-tier
  summaries.
- **`CASE WHEN`**: Assigns a value based on conditions. It places users into
  Low, Medium, or High activity tiers based on their event counts.
- **`COUNT` and `COUNT DISTINCT`**: `COUNT` counts rows or non-null values;
  `COUNT(DISTINCT user_id)` counts unique users. Unique counts are useful for
  monthly active users.
- **Conversion rate**: The number of users reaching a step divided by the
  users eligible at the preceding step, multiplied by 100.
- **Funnel analysis**: Measures users progressing through ordered steps. The
  project uses Signup → Onboarding Completed → Trial Started → Paid.
- **Segmentation**: Compares the same measure across groups. The funnel
  summary compares acquisition channel, platform, device tier, and region.
- **Activity tiers**: Simple groups based on recorded event counts: Low is
  0–5 events, Medium is 6–20, and High is more than 20. These are descriptive
  categories, not predictions.
- **Why SQL for product analytics?** SQL can filter, join, and summarize
  product event and user tables close to where the data is stored. This makes
  repeatable metrics easier to inspect and explain.

The queries use BigQuery tables and views referenced by the project. They
require access to BigQuery to return actual results; this repository does not
include those source tables locally.
