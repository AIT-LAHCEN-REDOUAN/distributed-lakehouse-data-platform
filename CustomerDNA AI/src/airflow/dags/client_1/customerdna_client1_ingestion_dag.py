from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

from client_1.customerdna_client1_dag_common import DEFAULT_ARGS, run_ingestion


with DAG(
    dag_id="customerdna_client1_ingestion_pipeline",
    description="Client 1 ingestion pipeline: build processed source files for downstream loading",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 6, 28),
    schedule=None,
    catchup=False,
    tags=["customerdna", "client1", "ingestion"],
) as dag:
    start = EmptyOperator(task_id="start")
    ingest = PythonOperator(
        task_id="ingest_client1_datasets",
        python_callable=run_ingestion,
    )
    end = EmptyOperator(task_id="end")

    start >> ingest >> end