-- ============================================================
-- 09. USER ACTIVITY ANALYSIS
-- Mobile Subscription Product Analytics
-- ============================================================

-- Activity is the number of resolved event rows per user in
-- events_user_level. Users with no recorded events are included with zero.
WITH user_event_counts AS (
    SELECT
        u.user_id,
        COUNT(e.user_id) AS event_count
    FROM `project-4-507020.1.users` u
    LEFT JOIN `project-4-507020.1.events_user_level` e
        ON u.user_id = e.user_id
    GROUP BY u.user_id
),

user_activity_tiers AS (
    SELECT
        user_id,
        event_count,
        CASE
            WHEN event_count <= 5 THEN 'Low'
            WHEN event_count <= 20 THEN 'Medium'
            ELSE 'High'
        END AS activity_tier
    FROM user_event_counts
),

tier_counts AS (
    SELECT
        activity_tier,
        COUNT(*) AS users,
        AVG(event_count) AS average_events_per_user
    FROM user_activity_tiers
    GROUP BY activity_tier
)

-- Result set 1: user counts and activity share by tier.
SELECT
    activity_tier,
    users,
    ROUND(average_events_per_user, 2) AS average_events_per_user,
    ROUND(
        100 * SAFE_DIVIDE(users, SUM(users) OVER ()),
        2
    ) AS share_of_users_pct
FROM tier_counts
ORDER BY
    CASE activity_tier
        WHEN 'Low' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'High' THEN 3
    END;

-- Result set 2: monthly active users. A user is active in a month
-- when they have at least one resolved event in that calendar month.
SELECT
    DATE_TRUNC(DATE(event_ts), MONTH) AS activity_month,
    COUNT(DISTINCT user_id) AS monthly_active_users
FROM `project-4-507020.1.events_user_level`
GROUP BY activity_month
ORDER BY activity_month;