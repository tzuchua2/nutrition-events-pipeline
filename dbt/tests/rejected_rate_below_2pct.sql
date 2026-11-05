-- Data-quality guard: fail the pipeline if more than 2% of landed events are malformed.
with t as (
    select (select count(*) from {{ ref('stg_events_rejected') }}) as bad,
           (select count(*) from {{ source('raw', 'events') }}) as total
)
select * from t where total > 0 and bad * 1.0 / total > 0.02
