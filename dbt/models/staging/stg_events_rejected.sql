-- Everything that failed validation, kept for data-quality monitoring instead of silently dropped.
select kafka_partition, kafka_offset, payload
from {{ source('raw', 'events') }}
where json_extract_string(payload, '$.event_type') not in
      ('app_opened','recipe_searched','recipe_viewed','meal_added_to_plan','plan_completed')
   or json_extract_string(payload, '$.event_type') is null
   or json_extract_string(payload, '$.event_id') is null
   or json_extract_string(payload, '$.user_id') is null
