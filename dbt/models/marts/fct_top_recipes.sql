select recipe_id,
       count(*) filter (where event_type = 'recipe_viewed')      as views,
       count(*) filter (where event_type = 'meal_added_to_plan') as adds_to_plan,
       round(count(*) filter (where event_type = 'meal_added_to_plan') * 1.0
             / nullif(count(*) filter (where event_type = 'recipe_viewed'), 0), 3) as add_rate,
       rank() over (order by count(*) filter (where event_type = 'meal_added_to_plan') desc) as popularity_rank
from {{ ref('stg_events') }}
where recipe_id is not null
group by recipe_id
order by popularity_rank, recipe_id
