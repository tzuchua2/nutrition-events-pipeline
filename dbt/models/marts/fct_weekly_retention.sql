with activity as (
    select distinct user_id, date_trunc('week', event_date) as active_week from {{ ref('stg_events') }}
),
cohorts as (
    select signup_week, count(*) as cohort_size from {{ ref('dim_users') }} group by signup_week
),
joined as (
    select u.signup_week,
           cast(date_diff('week', u.signup_week, a.active_week) as integer) as weeks_since_signup,
           count(distinct a.user_id) as active_users
    from {{ ref('dim_users') }} u
    join activity a using (user_id)
    group by 1, 2
)
select j.signup_week, j.weeks_since_signup, c.cohort_size, j.active_users,
       round(j.active_users * 1.0 / c.cohort_size, 3) as retention_rate
from joined j join cohorts c using (signup_week)
where j.weeks_since_signup >= 0
order by j.signup_week, j.weeks_since_signup
