from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator

from client_1.customerdna_client1_dag_common import (
    DEFAULT_ARGS,
    bootstrap_transformation_gx,
    dbt_run_all,
    dbt_test_all,
    validate_analytics_data,
    validate_ml_readiness,
    validate_serving_data,
)


with DAG(
    dag_id="customerdna_client1_transformation_quality_pipeline",
    description="Client 1 transformation pipeline: dbt run, dbt test, analytics GX, serving GX, and ML readiness GX",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 6, 28),
    schedule=None,
    catchup=False,
    tags=["customerdna", "client1", "dbt", "gx", "analytics", "serving", "ml"],
) as dag:
    start = EmptyOperator(task_id="start")
    dbt_run = PythonOperator(
        task_id="dbt_run_all_models",
        python_callable=dbt_run_all,
    )
    gx_bootstrap = PythonOperator(
        task_id="bootstrap_great_expectations",
        python_callable=bootstrap_transformation_gx,
    )
    dbt_test = PythonOperator(
        task_id="dbt_test_all_models",
        python_callable=dbt_test_all,
    )
    gx_analytics = PythonOperator(
        task_id="validate_analytics_quality",
        python_callable=validate_analytics_data,
    )
    gx_serving = PythonOperator(
        task_id="validate_serving_quality",
        python_callable=validate_serving_data,
    )
    gx_ml = PythonOperator(
        task_id="validate_ml_feature_readiness",
        python_callable=validate_ml_readiness,
    )
    end = EmptyOperator(task_id="end")

    start >> dbt_run >> gx_bootstrap >> dbt_test >> gx_analytics >> gx_serving >> gx_ml >> end
