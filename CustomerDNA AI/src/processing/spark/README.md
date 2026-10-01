# CustomerDNA AI - Spark Processing Layer

This folder contains the distributed-processing layer for the Hadoop-style evolution of the platform.

## Intended Role

Spark is used as the distributed compute engine to:

- read heavy bronze datasets from HDFS,
- process or normalize high-volume raw files,
- build Iceberg raw lakehouse tables from HDFS bronze slices,
- expose Spark SQL through a Thrift Server for dbt-spark transformations,
- support future large-scale enrichment or feature-preparation workloads.

## Architectural Position

`Source files -> Kafka -> HDFS bronze -> Spark bronze-to-Iceberg load -> Iceberg raw tables -> dbt-spark transformations -> Trino query access -> Great Expectations -> Airflow -> Prometheus/Grafana`

This means:

- **Kafka** remains the ingestion backbone,
- **HDFS** remains the bronze persistence layer,
- **Spark** executes the HDFS bronze-to-raw processing and loading step,
- **Spark Thrift Server** exposes the Spark SQL endpoint used by dbt-spark,
- **Iceberg** becomes the structured raw lakehouse table layer,
- **Hive Metastore** and **Trino** support the surrounding lakehouse/query ecosystem.

At this stage, Spark is part of the active bronze-to-raw pipeline and is triggered through the Kafka bronze-ready event flow.

## Folder Purpose

- `docker-compose.yml`
  Starts the Spark standalone cluster containers.

- `.env`
  Stores the local Spark container configuration.

- `jobs/`
  Contains Spark jobs that read bronze files from HDFS and build Iceberg raw tables.

- `conf/`
  Reserved for future Spark configuration files if custom tuning becomes necessary.

## Current Container Scope

The Spark container stack is intentionally lightweight for the first implementation step:

- `spark-master`
- `spark-worker`
- `spark-history-server`
- `spark-thrift-server`

This setup is sufficient for:

- local experimentation,
- PFE demonstration,
- active Airflow-triggered Spark raw-load jobs,
- dbt-spark transformation execution through the Spark Thrift endpoint,
- scaling later to a more complete distributed environment.
