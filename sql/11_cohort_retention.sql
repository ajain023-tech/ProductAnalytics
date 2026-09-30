-- ============================================================
-- 11. COHORT RETENTION
-- Mobile Subscription Product Analytics
-- ============================================================

-- D1, D7, and D30 are app_open on exactly 1, 7, and 30 calendar
-- days after signup, respectively, matching 04_retention.sql.
-- Each metric's denominator includes only users with a complete
-- observation window for that day.
--
-- This BigQuery script returns three result sets, in order:
-- 1. Signup-month cohorts
-- 2. Acquisition-channel summary
-- 3. Platform summary

CREATE TEMP TABLE retention_user_level AS
WITH data_window AS (
    SELECT
        MAX(DATE(event_ts)) AS data_end_date
    FROM `project-4-507020.1.events_user_level`
),

app_open_days AS (
    SELECT DISTINCT
        user_id,
        DATE(event_ts) AS activity_date
    FROM `project-4-507020.1.events_user_level`
    WHERE event_name = 'app_open'
)

SELECT
    u.user_id,
    DATE(u.signup_ts) AS signup_date,
    FORMAT_DATE('%Y-%m', DATE(u.signup_ts)) AS cohort_month,
    dw.data_end_date,
    u.acquisition_channel,
    u.platform,
    MAX(
        IF(
            a.activity_date = DATE_ADD(DATE(u.signup_ts), INTERVAL 1 DAY),
            1,
            0
        )
    ) AS retained_d1,
    MAX(
        IF(
            a.activity_date = DATE_ADD(DATE(u.signup_ts), INTERVAL 7 DAY),
            1,
            0
        )
    ) AS retained_d7,
    MAX(
        IF(
            a.activity_date = DATE_ADD(DATE(u.signup_ts), INTERVAL 30 DAY),
            1,
            0
        )
    ) AS retained_d30
FROM `project-4-507020.1.users` u
CROSS JOIN data_window dw
LEFT JOIN app_open_days a
    ON u.user_id = a.user_id
   AND a.activity_date IN (
        DATE_ADD(DATE(u.signup_ts), INTERVAL 1 DAY),
        DATE_ADD(DATE(u.signup_ts), INTERVAL 7 DAY),
        DATE_ADD(DATE(u.signup_ts), INTERVAL 30 DAY)
   )
GROUP BY
    u.user_id,
    signup_date,
    cohort_month,
    dw.data_end_date,
    u.acquisition_channel,
    u.platform;

-- Result set 1: one row per signup-month cohort.
SELECT
    cohort_month,
    COUNT(*) AS cohort_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
    ) AS d1_eligible_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
        AND retained_d1 = 1
    ) AS d1_retained_users,
    ROUND(
        100 * SAFE_DIVIDE(
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
                AND retained_d1 = 1
            ),
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
            )
        ),
        2
    ) AS d1_retention_pct,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
    ) AS d7_eligible_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
        AND retained_d7 = 1
    ) AS d7_retained_users,
    ROUND(
        100 * SAFE_DIVIDE(
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
                AND retained_d7 = 1
            ),
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
            )
        ),
        2
    ) AS d7_retention_pct,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
    ) AS d30_eligible_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
        AND retained_d30 = 1
    ) AS d30_retained_users,
    ROUND(
        100 * SAFE_DIVIDE(
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
                AND retained_d30 = 1
            ),
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
            )
        ),
        2
    ) AS d30_retention_pct
FROM retention_user_level
GROUP BY cohort_month
ORDER BY cohort_month;

-- Result set 2: retention summarized by acquisition channel.
SELECT
    COALESCE(acquisition_channel, 'Unknown') AS acquisition_channel,
    COUNT(*) AS segment_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
    ) AS d1_eligible_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
        AND retained_d1 = 1
    ) AS d1_retained_users,
    ROUND(
        100 * SAFE_DIVIDE(
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
                AND retained_d1 = 1
            ),
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
            )
        ),
        2
    ) AS d1_retention_pct,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
    ) AS d7_eligible_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
        AND retained_d7 = 1
    ) AS d7_retained_users,
    ROUND(
        100 * SAFE_DIVIDE(
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
                AND retained_d7 = 1
            ),
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
            )
        ),
        2
    ) AS d7_retention_pct,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
    ) AS d30_eligible_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
        AND retained_d30 = 1
    ) AS d30_retained_users,
    ROUND(
        100 * SAFE_DIVIDE(
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
                AND retained_d30 = 1
            ),
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
            )
        ),
        2
    ) AS d30_retention_pct
FROM retention_user_level
GROUP BY acquisition_channel
ORDER BY acquisition_channel;

-- Result set 3: retention summarized by platform.
SELECT
    COALESCE(platform, 'Unknown') AS platform,
    COUNT(*) AS segment_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
    ) AS d1_eligible_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
        AND retained_d1 = 1
    ) AS d1_retained_users,
    ROUND(
        100 * SAFE_DIVIDE(
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
                AND retained_d1 = 1
            ),
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 1 DAY)
            )
        ),
        2
    ) AS d1_retention_pct,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
    ) AS d7_eligible_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
        AND retained_d7 = 1
    ) AS d7_retained_users,
    ROUND(
        100 * SAFE_DIVIDE(
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
                AND retained_d7 = 1
            ),
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 7 DAY)
            )
        ),
        2
    ) AS d7_retention_pct,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
    ) AS d30_eligible_users,
    COUNTIF(
        signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
        AND retained_d30 = 1
    ) AS d30_retained_users,
    ROUND(
        100 * SAFE_DIVIDE(
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
                AND retained_d30 = 1
            ),
            COUNTIF(
                signup_date <= DATE_SUB(data_end_date, INTERVAL 30 DAY)
            )
        ),
        2
    ) AS d30_retention_pct
FROM retention_user_level
GROUP BY platform
ORDER BY platform;
