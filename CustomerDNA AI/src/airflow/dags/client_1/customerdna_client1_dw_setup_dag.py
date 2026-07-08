from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator

from client_1.customerdna_client1_dag_common import (
    DEFAULT_ARGS,
    run_create_base_tables,
    run_setup_dw,
)


with DAG(
    dag_id="customerdna_client1_dw_setup_pipeline",
    description="Client 1 warehouse setup pipeline: create the database, schemas, metadata objects, and raw base tables",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 7, 7),
    schedule=None,
    catchup=False,
    tags=["customerdna", "client1", "setup", "dw"],
) as dag:
    start = EmptyOperator(task_id="start")
    setup_dw = PythonOperator(
        task_id="setup_client1_data_warehouse",
        python_callable=run_setup_dw,
    )
    create_base_tables = PythonOperator(
        task_id="create_client1_raw_base_tables",
        python_callable=run_create_base_tables,
    )
    end = EmptyOperator(task_id="end")

    start >> setup_dw >> create_base_tables >> end
