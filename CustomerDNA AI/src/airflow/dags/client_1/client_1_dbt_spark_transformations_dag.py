from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator

from client_1.client_1_dag_common import (
    DEFAULT_ARGS,
    run_dbt_spark_transformations,
    test_dbt_spark_transformations,
    validate_spark_thrift_service,
    validate_trino_query_service,
)


with DAG(
    dag_id="customerdna_client1_dbt_spark_lakehouse_pipeline",
    description="Client 1 transformation pipeline: dbt-spark staging, intermediate, and analytics layers on top of Iceberg raw tables",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 7, 15),
    schedule=None,
    catchup=False,
    tags=["customerdna", "client1", "lakehouse", "dbt-spark", "transformations", "analytics"],
) as dag:
    start = EmptyOperator(task_id="start")
    spark_thrift_check = PythonOperator(
        task_id="validate_spark_thrift_service",
        python_callable=validate_spark_thrift_service,
    )
    dbt_run = PythonOperator(
        task_id="run_dbt_spark_lakehouse_models",
        python_callable=run_dbt_spark_transformations,
    )
    dbt_test = PythonOperator(
        task_id="test_dbt_spark_lakehouse_models",
        python_callable=test_dbt_spark_transformations,
    )
    trino_check = PythonOperator(
        task_id="validate_trino_query_service",
        python_callable=validate_trino_query_service,
    )
    end = EmptyOperator(task_id="end")

    start >> spark_thrift_check >> dbt_run >> dbt_test >> trino_check >> end
