-- ============================================================
-- 07. PRODUCT KPIs
-- Mobile Subscription Product Analytics
-- ============================================================

-- Funnel stages use the same order and timestamp rules as 02_funnel.sql:
-- Signup -> Onboarding Completed -> Trial Started -> Paid.
CREATE TEMP TABLE product_user_funnel AS
WITH onboarding AS (
    SELECT
        u.user_id,
        MIN(e.event_ts) AS onboarding_ts
    FROM `project-4-507020.1.users` u
    JOIN `project-4-507020.1.events_user_level` e
        ON u.user_id = e.user_id
       AND e.event_ts >= u.signup_ts
    WHERE e.event_name = 'onboarding_completed'
    GROUP BY u.user_id
),

trial AS (
    SELECT
        o.user_id,
        MIN(s.trial_start_at) AS trial_ts
    FROM onboarding o
    JOIN `project-4-507020.1.subscriptions` s
        ON o.user_id = s.user_id
       AND s.trial_start_at >= o.onboarding_ts
    WHERE s.trial_start_at IS NOT NULL
    GROUP BY o.user_id
),

paid AS (
    SELECT
        t.user_id,
        MIN(p.transaction_ts) AS paid_ts
    FROM trial t
    JOIN `project-4-507020.1.payments_clean` p
        ON t.user_id = p.user_id
       AND p.transaction_ts >= t.trial_ts
    WHERE p.transaction_type = 'charge'
      AND p.status = 'captured'
      AND p.amount_usd > 0
    GROUP BY t.user_id
)

SELECT
    u.user_id,
    u.signup_ts,
    CASE
        WHEN o.onboarding_ts >= u.signup_ts
        THEN o.onboarding_ts
    END AS onboarding_ts,
    CASE
        WHEN o.onboarding_ts >= u.signup_ts
         AND t.trial_ts >= o.onboarding_ts
        THEN t.trial_ts
    END AS trial_ts,
    CASE
        WHEN o.onboarding_ts >= u.signup_ts
         AND t.trial_ts >= o.onboarding_ts
         AND p.paid_ts >= t.trial_ts
        THEN p.paid_ts
    END AS paid_ts
FROM `project-4-507020.1.users` u
LEFT JOIN onboarding o
    ON u.user_id = o.user_id
LEFT JOIN trial t
    ON u.user_id = t.user_id
LEFT JOIN paid p
    ON u.user_id = p.user_id;

-- Result set 1: overall counts and step-to-step conversion rates.
WITH counts AS (
    SELECT
        COUNT(*) AS total_users,
        COUNTIF(onboarding_ts IS NOT NULL) AS onboarding_completed_users,
        COUNTIF(trial_ts IS NOT NULL) AS trial_users,
        COUNTIF(paid_ts IS NOT NULL) AS paid_users
    FROM product_user_funnel
)
SELECT
    total_users,
    onboarding_completed_users,
    trial_users,
    paid_users,
    ROUND(
        100 * SAFE_DIVIDE(onboarding_completed_users, total_users),
        2
    ) AS onboarding_completion_rate_pct,
    ROUND(
        100 * SAFE_DIVIDE(trial_users, onboarding_completed_users),
        2
    ) AS trial_start_rate_pct,
    ROUND(
        100 * SAFE_DIVIDE(paid_users, trial_users),
        2
    ) AS trial_to_paid_conversion_rate_pct
FROM counts;

-- Result set 2: signup-month trend for each ordered funnel stage.
SELECT
    FORMAT_DATE('%Y-%m', DATE(signup_ts)) AS signup_month,
    COUNT(*) AS signup_users,
    COUNTIF(onboarding_ts IS NOT NULL) AS onboarding_users,
    COUNTIF(trial_ts IS NOT NULL) AS trial_users,
    COUNTIF(paid_ts IS NOT NULL) AS paid_users
FROM product_user_funnel
GROUP BY signup_month
ORDER BY signup_month;