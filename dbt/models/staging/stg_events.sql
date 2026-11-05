-- Parse the raw JSON, drop malformed events (see stg_events_rejected), and de-duplicate re-delivered events.
with parsed as (
    select
        kafka_partition,
        kafka_offset,
        ingested_at,
        json_extract_string(payload, '$.event_id')                    as event_id,
        json_extract_string(payload, '$.user_id')                     as user_id,
        json_extract_string(payload, '$.event_type')                  as event_type,
        try_cast(json_extract_string(payload, '$.event_ts') as timestamptz) as event_ts,
        json_extract_string(payload, '$.platform')                    as platform,
        json_extract_string(payload, '$.dietary_goal')                as dietary_goal,
        json_extract_string(payload, '$.recipe_id')                   as recipe_id
    from {{ source('raw', 'events') }}
),
valid as (
    select * from parsed
    where event_id is not null and user_id is not null and event_ts is not null
      and event_type in ('app_opened','recipe_searched','recipe_viewed','meal_added_to_plan','plan_completed')
),
ranked as (
    select *, row_number() over (partition by event_id order by kafka_partition, kafka_offset) as rn
    from valid
)
select
    event_id, user_id, event_type,
    cast(event_ts as timestamp) as event_ts,
    cast(event_ts as date)      as event_date,
    platform, dietary_goal, recipe_id
from ranked
where rn = 1
