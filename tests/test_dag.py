import os

from airflow.models import DagBag


def test_dag_imports_and_wiring():
    home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ["NEP_HOME"] = home
    bag = DagBag(dag_folder=os.path.join(home, "dags"), include_examples=False)
    assert not bag.import_errors, bag.import_errors
    dag = bag.get_dag("nutrition_events_pipeline")
    order = [t.task_id for t in dag.topological_sort()]
    assert order == ["produce_events", "land_raw_events", "dbt_run", "dbt_test", "export_dashboard_json"]
