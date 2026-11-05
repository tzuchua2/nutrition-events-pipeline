-- A user can't complete a plan without opening the app, etc.: later steps never exceed the first step.
select * from {{ ref('fct_funnel') }}
where completed_plan > opened or added_to_plan > opened or viewed > opened
