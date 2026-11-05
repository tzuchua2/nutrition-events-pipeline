"""Airflow DAG: Kafka -> DuckDB (raw) -> dbt (staging, marts, tests) -> JSON for the React dashboard.

Tasks run the project's own scripts in the project venv (Airflow itself lives in a separate venv to avoid
dependency conflicts, a common production pattern). dbt tests are a hard gate: if data quality fails,
nothing is exported to the dashboard.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT = os.environ.get("NEP_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = f"{PROJECT}/.venv/bin/python"
DBT = f"{PROJECT}/.venv/bin/dbt"
ENV = {"WAREHOUSE_PATH": f"{PROJECT}/data/warehouse.duckdb", "PYTHONPATH": PROJECT}
DBT_ARGS = f"--project-dir '{PROJECT}/dbt' --profiles-dir '{PROJECT}/dbt'"

default_args = {"owner": "andrew", "retries": 2, "retry_delay": timedelta(seconds=20)}

with DAG(
    dag_id="nutrition_events_pipeline",
    description="Stream app events from Kafka, transform with dbt, serve to React",
    start_date=datetime(2026, 9, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["kafka", "dbt", "portfolio"],
) as dag:
    produce = BashOperator(  # stands in for the upstream app emitting events
        task_id="produce_events",
        bash_command=f"cd '{PROJECT}' && '{PY}' -m producer.produce",
        env=ENV,
        append_env=True,
    )
    consume = BashOperator(
        task_id="land_raw_events",
        bash_command=f"cd '{PROJECT}' && '{PY}' -m consumer.consume",
        env=ENV,
        append_env=True,
    )
    dbt_run = BashOperator(task_id="dbt_run", bash_command=f"'{DBT}' run {DBT_ARGS}", env=ENV, append_env=True)
    dbt_test = BashOperator(task_id="dbt_test", bash_command=f"'{DBT}' test {DBT_ARGS}", env=ENV, append_env=True)
    export = BashOperator(
        task_id="export_dashboard_json",
        bash_command=f"cd '{PROJECT}' && '{PY}' scripts/export_marts.py",
        env=ENV,
        append_env=True,
    )
    produce >> consume >> dbt_run >> dbt_test >> export
