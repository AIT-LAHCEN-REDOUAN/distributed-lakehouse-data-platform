## Project Overview

CustomerDNA AI is a distributed lakehouse project designed to ingest, process, validate, and serve customer-related data for analytics.

The platform centralizes data from multiple sources and transforms it through a Medallion Architecture:

- **Bronze layer** stores raw ingested data.
- **Silver layer** cleans, standardizes, and validates data.
- **Gold layer** creates curated, analytics-ready datasets.

The project focuses on reliable data pipelines, scalable processing, data quality, orchestration, monitoring, and SQL-based analytics.

## Architecture

![CustomerDNA AI distributed lakehouse architecture](CustomerDNA%20AI/Architecture_Final.drawio.png)


The platform is deployed across three Linux virtual machines. Each component has a dedicated responsibility in the ingestion, storage, transformation, orchestration, and analytics workflow.

## Technology Stack

| Project Component | Technologies | Purpose |
| --- | --- | --- |
| Data ingestion | Apache Kafka, Python | Ingest data from source systems and stream records into the platform. |
| Distributed storage | HDFS | Store raw and intermediate data across the distributed environment. |
| Lakehouse tables | Apache Iceberg | Manage structured, versioned, and queryable datasets across Bronze, Silver, and Gold layers. |
| Data processing | Apache Spark, PySpark | Transform, clean, aggregate, and prepare data at scale. |
| Data transformation | dbt-spark | Build modular data models and test transformations. |
| Workflow orchestration | Apache Airflow | Schedule, coordinate, and monitor pipeline dependencies. |
| Data quality | Great Expectations | Validate critical data rules and identify quality issues. |
| SQL analytics | Trino | Query curated Iceberg tables using SQL. |
| Monitoring | Prometheus, Grafana | Monitor platform health, pipeline behavior, and operational metrics. |
| Deployment | Docker, Kubernetes | Package and manage platform services. |
| Security | Kerberos | Secure access in the protected deployment configuration. |

## Data Flow

1. Source data enters the platform through Python and Kafka ingestion pipelines.
2. Raw data is stored in the **Bronze layer** using HDFS and Apache Iceberg.
3. Apache Spark and PySpark transform raw records into cleaned and standardized **Silver layer** datasets.
4. dbt-spark creates validated data models for the **Gold layer**.
5. Airflow orchestrates pipeline execution, dependencies, retries, and scheduling.
6. Great Expectations validates data-quality rules during the pipeline lifecycle.
7. Trino provides SQL access to curated Gold-layer datasets.
8. Prometheus collects operational metrics, while Grafana visualizes platform and pipeline health.

## Implementation Scope

- Distributed deployment across three Linux virtual machines.
- Kafka and Python ingestion pipelines.
- Bronze, Silver, and Gold data layers.
- Spark and dbt-spark transformations.
- 10 data models with 11 passing tests.
- Five Airflow DAGs for workflow orchestration.
- Three Great Expectations validations.
- Prometheus and Grafana observability.
- Trino SQL access to curated datasets.

## Project Goal

The goal of CustomerDNA AI is to demonstrate how a modern distributed lakehouse can transform raw multi-source data into trusted, analytics-ready data products through scalable processing, quality controls, orchestration, and monitoring.
