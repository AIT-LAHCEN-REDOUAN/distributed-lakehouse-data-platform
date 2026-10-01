from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator

from client_1.client_1_dag_common import (
    DEFAULT_ARGS,
    validate_hdfs_bronze_service,
    validate_hive_metastore_service,
    validate_spark_cluster_service,
    validate_spark_thrift_service,
    validate_trino_query_service,
)


with DAG(
    dag_id="customerdna_client1_lakehouse_readiness_pipeline",
    description="Client 1 lakehouse readiness pipeline: validate HDFS bronze availability, Hive metastore, Spark cluster, Spark Thrift Server, and Trino query service connectivity",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 6, 28),
    schedule=None,
    catchup=False,
    tags=["customerdna", "client1", "lakehouse", "hdfs", "hive", "spark", "trino", "readiness"],
) as dag:
    start = EmptyOperator(task_id="start")
    hdfs_readiness = PythonOperator(
        task_id="validate_hdfs_bronze_service",
        python_callable=validate_hdfs_bronze_service,
    )
    hive_readiness = PythonOperator(
        task_id="validate_hive_metastore_service",
        python_callable=validate_hive_metastore_service,
    )
    spark_readiness = PythonOperator(
        task_id="validate_spark_cluster_service",
        python_callable=validate_spark_cluster_service,
    )
    spark_thrift_readiness = PythonOperator(
        task_id="validate_spark_thrift_service",
        python_callable=validate_spark_thrift_service,
    )
    trino_readiness = PythonOperator(
        task_id="validate_trino_query_service",
        python_callable=validate_trino_query_service,
    )
    end = EmptyOperator(task_id="end")

    start >> hdfs_readiness >> hive_readiness >> spark_readiness >> spark_thrift_readiness >> trino_readiness >> end
