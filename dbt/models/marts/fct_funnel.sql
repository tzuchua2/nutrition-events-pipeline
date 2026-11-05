-- Daily sessions (user-day) reaching each funnel step, per dietary goal, with step-to-step conversion.
with steps as (
    select dietary_goal,
        count(distinct case when event_type = 'app_opened' then user_id || '|' || cast(event_date as varchar) end) as opened,
        count(distinct case when event_type = 'recipe_searched' then user_id || '|' || cast(event_date as varchar) end) as searched,
        count(distinct case when event_type = 'recipe_viewed' then user_id || '|' || cast(event_date as varchar) end) as viewed,
        count(distinct case when event_type = 'meal_added_to_plan' then user_id || '|' || cast(event_date as varchar) end) as added_to_plan,
        count(distinct case when event_type = 'plan_completed' then user_id || '|' || cast(event_date as varchar) end) as completed_plan
    from {{ ref('stg_events') }}
    group by dietary_goal
)
select *,
    round(searched * 1.0 / nullif(opened, 0), 3)        as search_rate,
    round(viewed * 1.0 / nullif(searched, 0), 3)        as view_rate,
    round(added_to_plan * 1.0 / nullif(viewed, 0), 3)   as add_rate,
    round(completed_plan * 1.0 / nullif(added_to_plan, 0), 3) as completion_rate
from steps
order by dietary_goal
