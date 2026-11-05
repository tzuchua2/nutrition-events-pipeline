select * from {{ ref('stg_events') }} e join {{ ref('dim_users') }} u using (user_id) where e.event_date < u.first_seen_date
