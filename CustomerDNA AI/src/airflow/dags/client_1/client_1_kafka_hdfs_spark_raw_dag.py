from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator

from client_1.client_1_dag_common import (
    DEFAULT_ARGS,
    bootstrap_raw_gx,
    run_kafka_hdfs_spark_raw_pipeline,
    validate_raw_data,
)


with DAG(
    dag_id="customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline",
    description="Client 1 raw lakehouse pipeline: source files -> Kafka -> HDFS bronze -> Spark -> Iceberg raw tables -> Great Expectations validation",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 6, 28),
    schedule=None,
    catchup=False,
    tags=["customerdna", "client1", "lakehouse", "kafka", "hdfs", "spark", "iceberg", "gx"],
) as dag:
    start = EmptyOperator(task_id="start")
    raw_lakehouse_build = PythonOperator(
        task_id="stream_sources_to_hdfs_and_build_iceberg_raw_with_spark",
        python_callable=run_kafka_hdfs_spark_raw_pipeline,
    )
    gx_bootstrap = PythonOperator(
        task_id="bootstrap_raw_lakehouse_quality_assets",
        python_callable=bootstrap_raw_gx,
    )
    gx_raw = PythonOperator(
        task_id="validate_raw_lakehouse_quality",
        python_callable=validate_raw_data,
    )
    end = EmptyOperator(task_id="end")

    start >> raw_lakehouse_build >> gx_bootstrap >> gx_raw >> end
