select event_date, platform, count(distinct user_id) as active_users, count(*) as events
from {{ ref('stg_events') }}
group by event_date, platform
order by event_date, platform
