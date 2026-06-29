from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

from client_1.customerdna_client1_dag_common import (
    DEFAULT_ARGS,
    bootstrap_raw_gx,
    load_raw_data,
    validate_raw_data,
)


with DAG(
    dag_id="customerdna_client1_raw_load_pipeline",
    description="Client 1 raw load pipeline: load ingested CSVs into raw_data and validate raw quality",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 6, 28),
    schedule=None,
    catchup=False,
    tags=["customerdna", "client1", "raw", "gx"],
) as dag:
    start = EmptyOperator(task_id="start")
    load_raw = PythonOperator(
        task_id="load_raw_data_to_dw",
        python_callable=load_raw_data,
    )
    gx_bootstrap = PythonOperator(
        task_id="bootstrap_great_expectations",
        python_callable=bootstrap_raw_gx,
    )
    gx_raw = PythonOperator(
        task_id="validate_raw_data_quality",
        python_callable=validate_raw_data,
    )
    end = EmptyOperator(task_id="end")

    start >> load_raw >> gx_bootstrap >> gx_raw >> end