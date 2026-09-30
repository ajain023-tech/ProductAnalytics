-- ============================================================
-- 08. FUNNEL SEGMENT ANALYSIS
-- Mobile Subscription Product Analytics
-- ============================================================

-- Count each stage only when the user's events occurred in the
-- established order: signup, onboarding, trial, then paid.
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
        u.acquisition_channel,
        u.platform,
        u.device_tier,
        u.region,
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

segment_rows AS (
    SELECT
        uf.user_id,
        uf.onboarding_ts,
        uf.trial_ts,
        uf.paid_ts,
        s.dimension,
        s.segment
    FROM user_funnel uf
    CROSS JOIN UNNEST([
        STRUCT(
            'acquisition_channel' AS dimension,
            COALESCE(uf.acquisition_channel, 'Unknown') AS segment
        ),
        STRUCT(
            'platform',
            COALESCE(uf.platform, 'Unknown')
        ),
        STRUCT(
            'device_tier',
            COALESCE(uf.device_tier, 'Unknown')
        ),
        STRUCT(
            'region',
            COALESCE(uf.region, 'Unknown')
        )
    ]) AS s
),

segment_counts AS (
    SELECT
        dimension,
        segment,
        COUNT(*) AS signup_users,
        COUNTIF(onboarding_ts IS NOT NULL) AS onboarding_users,
        COUNTIF(trial_ts IS NOT NULL) AS trial_users,
        COUNTIF(paid_ts IS NOT NULL) AS paid_users
    FROM segment_rows
    GROUP BY dimension, segment
)

SELECT
    dimension,
    segment,
    signup_users,
    onboarding_users,
    trial_users,
    paid_users,
    signup_users - onboarding_users AS signup_to_onboarding_dropoff,
    onboarding_users - trial_users AS onboarding_to_trial_dropoff,
    trial_users - paid_users AS trial_to_paid_dropoff,
    ROUND(
        100 * SAFE_DIVIDE(onboarding_users, signup_users),
        2
    ) AS signup_to_onboarding_rate_pct,
    ROUND(
        100 * SAFE_DIVIDE(trial_users, onboarding_users),
        2
    ) AS onboarding_to_trial_rate_pct,
    ROUND(
        100 * SAFE_DIVIDE(paid_users, trial_users),
        2
    ) AS trial_to_paid_conversion_rate_pct
FROM segment_counts
ORDER BY
    CASE dimension
        WHEN 'acquisition_channel' THEN 1
        WHEN 'platform' THEN 2
        WHEN 'device_tier' THEN 3
        WHEN 'region' THEN 4
    END,
    segment;