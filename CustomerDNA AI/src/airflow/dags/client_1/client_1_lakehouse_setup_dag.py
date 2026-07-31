from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator

from client_1.client_1_dag_common import (
    DEFAULT_ARGS,
    initialize_bronze_zone,
    initialize_lakehouse_namespace,
    validate_hive_metastore_service,
    validate_trino_query_service,
)


with DAG(
    dag_id="customerdna_client1_lakehouse_setup_pipeline",
    description="Client 1 lakehouse setup pipeline: initialize the HDFS bronze zone, prepare the Iceberg lakehouse namespaces, and verify Trino access",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 7, 7),
    schedule=None,
    catchup=False,
    tags=["customerdna", "client1", "lakehouse", "setup", "hdfs", "trino", "iceberg"],
) as dag:
    start = EmptyOperator(task_id="start")
    initialize_bronze = PythonOperator(
        task_id="initialize_client1_hdfs_bronze_zone",
        python_callable=initialize_bronze_zone,
    )
    initialize_namespace = PythonOperator(
        task_id="initialize_client1_iceberg_namespaces",
        python_callable=initialize_lakehouse_namespace,
    )
    validate_hive_metastore = PythonOperator(
        task_id="validate_hive_metastore_service",
        python_callable=validate_hive_metastore_service,
    )
    validate_trino = PythonOperator(
        task_id="validate_trino_query_service",
        python_callable=validate_trino_query_service,
    )
    end = EmptyOperator(task_id="end")

    start >> initialize_bronze >> validate_hive_metastore >> initialize_namespace >> validate_trino >> end
