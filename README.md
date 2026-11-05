# Nutrition Events Pipeline

An end-to-end data pipeline: **Kafka → Airflow → dbt → React**.
A synthetic nutrition/meal-planning app emits events; the pipeline streams, lands, models, tests, and serves them.
All data is synthetic (no real users, no company data). Inspired by the product-analytics questions behind my MaziMeal capstone.

```
producer (Python) ──► Kafka topic app_events (3 partitions, keyed by user)
                          │
                consumer (at-least-once, manual commit, idempotent landing)
                          ▼
                 DuckDB raw.events  ──► dbt: staging (parse, validate, dedupe, quarantine)
                                          └► marts: dim_users, fct_daily_active_users, fct_funnel,
                                                    fct_weekly_retention, fct_top_recipes
                                          └► 16 data tests (unique/not_null/accepted_values + custom)
                          ▼
                 export marts.json ──► React dashboard (Vite + Recharts)
                 
 Orchestrated by an Airflow DAG: produce → land_raw → dbt_run → dbt_test → export (tests gate publishing)
```

## Run it
Needs Docker (Kafka), Python 3.12 + [uv](https://docs.astral.sh/uv/), Node 16+.
```bash
docker compose up -d                                        # Kafka broker (KRaft)
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python confluent-kafka duckdb dbt-duckdb pytest pyyaml
uv venv --python 3.12 .venv-airflow && uv pip install --python .venv-airflow/bin/python "apache-airflow==2.10.5" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt"

export AIRFLOW_HOME=$PWD/.airflow AIRFLOW__CORE__DAGS_FOLDER=$PWD/dags AIRFLOW__CORE__LOAD_EXAMPLES=False NEP_HOME=$PWD
.venv-airflow/bin/airflow db migrate
.venv-airflow/bin/airflow dags test nutrition_events_pipeline 2026-11-05   # runs the whole pipeline

cd dashboard && npm install && npm run build && npx vite preview
```
(`airflow standalone` gives you the Airflow UI + scheduler if you want the DAG on a schedule.)

## Tests
```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_pipeline_units.py   # generator + idempotent landing
.venv-airflow/bin/python -m pytest tests/test_dag.py                     # DAG imports and task order
.venv/bin/dbt test --project-dir dbt --profiles-dir dbt                  # 16 data-quality tests
cd dashboard && npm test                                                  # transform unit tests
```

## Design decisions (what to say in an interview)
- **Why Kafka keyed by `user_id`:** keeps each user's events ordered within a partition while allowing parallel consumers.
- **At-least-once + idempotent landing:** the consumer commits offsets only after the batch is written; `raw.events` has a primary key on (topic, partition, offset), so a replay can't create duplicates. The generator deliberately injects ~1% duplicate deliveries to prove dbt de-duplicates by `event_id`.
- **ELT, not ETL:** raw payloads are landed untouched; validation lives in dbt (`stg_events` keeps valid rows, `stg_events_rejected` quarantines the rest so bad data is counted, not silently dropped).
- **Airflow as the gate:** `dbt_test` sits between `dbt_run` and `export`; if data quality fails, the dashboard doesn't update. Retries (2) on every task.
- **Separate virtualenvs** for Airflow and the project (Airflow pins many dependencies; isolating avoids conflicts).
- **DuckDB** instead of a cloud warehouse: zero-ops for a portfolio project; the dbt models would port to Snowflake/BigQuery with minimal changes (swap the adapter and a few JSON functions).
- **Honest limits:** single broker, synthetic data, batch consumer (not a streaming job), no schema registry. Next steps: Schema Registry/Avro, incremental dbt models, Snowflake target.
