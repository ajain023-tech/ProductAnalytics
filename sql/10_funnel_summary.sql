-- ============================================================
-- 10. FUNNEL SUMMARY
-- Mobile Subscription Product Analytics
-- ============================================================

-- Funnel definition and event sequencing match 02_funnel.sql:
-- Signup -> Onboarding Completed -> Trial Started -> Paid.

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
),

user_funnel AS (
    SELECT
        u.user_id,
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
        ON u.user_id = p.user_id
),

funnel_counts AS (
    SELECT
        COUNT(*) AS signup_users,
        COUNTIF(onboarding_ts IS NOT NULL) AS onboarding_users,
        COUNTIF(trial_ts IS NOT NULL) AS trial_users,
        COUNTIF(paid_ts IS NOT NULL) AS paid_users
    FROM user_funnel
),

funnel_rows AS (
    SELECT 1 AS step_order, 'signup' AS step, signup_users AS users
    FROM funnel_counts

    UNION ALL

    SELECT 2, 'onboarding_completed', onboarding_users
    FROM funnel_counts

    UNION ALL

    SELECT 3, 'trial_started', trial_users
    FROM funnel_counts

    UNION ALL

    SELECT 4, 'paid', paid_users
    FROM funnel_counts
),

funnel_with_previous AS (
    SELECT
        step_order,
        step,
        users,
        LAG(users) OVER (ORDER BY step_order) AS previous_step_users
    FROM funnel_rows
),

overall_conversion AS (
    SELECT
        ROUND(100 * SAFE_DIVIDE(paid_users, signup_users), 2)
            AS signup_to_paid_conversion_pct
    FROM funnel_counts
)

SELECT
    f.step_order,
    f.step,
    f.users,
    CASE
        WHEN f.step_order = 1 THEN 100.00
        ELSE ROUND(100 * SAFE_DIVIDE(f.users, f.previous_step_users), 2)
    END AS conversion_from_previous_pct,
    f.previous_step_users - f.users AS absolute_user_dropoff,
    ROUND(
        100 * SAFE_DIVIDE(
            f.previous_step_users - f.users,
            f.previous_step_users
        ),
        2
    ) AS percentage_dropoff,
    o.signup_to_paid_conversion_pct
FROM funnel_with_previous f
CROSS JOIN overall_conversion o
ORDER BY f.step_order;
