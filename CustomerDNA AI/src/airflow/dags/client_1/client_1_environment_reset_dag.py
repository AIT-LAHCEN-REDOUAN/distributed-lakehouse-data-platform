from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator

from client_1.client_1_dag_common import (
    DEFAULT_ARGS,
    reset_hdfs_bronze_zone,
    reset_kafka_topics,
    reset_lakehouse_namespaces,
    validate_hive_metastore_service,
    validate_trino_query_service,
)


with DAG(
    dag_id="customerdna_client1_environment_reset_pipeline",
    description=(
        "Client 1 recovery/reset pipeline: drop lakehouse schemas through Trino, "
        "clear the HDFS bronze area, and recreate empty Kafka topics for a fresh rerun"
    ),
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 7, 30),
    schedule=None,
    catchup=False,
    tags=["customerdna", "client1", "reset", "recovery", "kafka", "hdfs", "trino", "iceberg"],
) as dag:
    start = EmptyOperator(task_id="start")
    validate_hive_metastore = PythonOperator(
        task_id="validate_hive_metastore_service",
        python_callable=validate_hive_metastore_service,
    )
    validate_trino = PythonOperator(
        task_id="validate_trino_query_service",
        python_callable=validate_trino_query_service,
    )
    reset_lakehouse = PythonOperator(
        task_id="reset_client1_iceberg_lakehouse",
        python_callable=reset_lakehouse_namespaces,
    )
    reset_bronze = PythonOperator(
        task_id="reset_client1_hdfs_bronze_zone",
        python_callable=reset_hdfs_bronze_zone,
    )
    reset_kafka = PythonOperator(
        task_id="reset_client1_kafka_topics",
        python_callable=reset_kafka_topics,
    )
    end = EmptyOperator(task_id="end")

    start >> validate_hive_metastore >> validate_trino >> reset_lakehouse >> reset_bronze >> reset_kafka >> end
