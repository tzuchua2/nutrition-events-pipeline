select
    user_id,
    any_value(platform)      as platform,
    any_value(dietary_goal)  as dietary_goal,
    min(event_date)          as first_seen_date,
    date_trunc('week', min(event_date)) as signup_week,
    max(event_date)          as last_seen_date,
    count(*)                 as total_events,
    count(distinct event_date) as active_days
from {{ ref('stg_events') }}
group by user_id
