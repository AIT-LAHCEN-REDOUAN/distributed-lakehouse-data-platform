# CustomerDNA AI: Distributed Lakehouse Data Platform

A distributed lakehouse platform for ingesting, transforming, validating, and serving customer data for analytics.

The project follows a Medallion Architecture to convert data from multiple sources into reliable, analytics-ready datasets. It applies practical Data Engineering principles across ingestion, transformation, orchestration, data quality, observability, and SQL-based consumption.

## Architecture

![CustomerDNA AI distributed lakehouse architecture](CustomerDNA%20AI/project_presentation/PFE_report/90_assets/architecture/Architecture_Final.drawio.png)

The platform ingests source data through streaming and batch pipelines, processes it through Bronze, Silver, and Gold layers, and exposes curated datasets for analytics and reporting.

## Technical Stack

| Area | Technologies |
| --- | --- |
| Data engineering | Python, SQL, ETL/ELT, data modeling |
| Data processing | Apache Spark, PySpark, dbt-spark |
| Lakehouse storage | HDFS, Apache Iceberg |
| Streaming and ingestion | Apache Kafka, Python |
| Orchestration | Apache Airflow |
| Query engine | Trino |
| Data quality | Great Expectations |
| Monitoring | Prometheus, Grafana |
| Platform and deployment | Linux, Docker, Kubernetes |
| Security | Kerberos deployment variant |

## Key Highlights

- Deployed a distributed lakehouse across three Linux virtual machines.
- Built Kafka and Python ingestion pipelines for multiple source datasets.
- Implemented Bronze, Silver, and Gold data layers using Spark, Iceberg, and dbt-spark.
- Produced 10 data models with 11 passing data-quality tests.
- Orchestrated five Airflow DAGs for automated workflow execution.
- Implemented three Great Expectations validations for data reliability.
- Added Prometheus and Grafana monitoring for platform observability.
- Enabled SQL access to curated data through Trino.

## Data Flow

1. Source data is ingested through Kafka and Python pipelines.
2. Raw records are stored in the Bronze layer.
3. Spark and dbt-spark clean, standardize, and model data in the Silver layer.
4. Analytics-ready datasets are produced in the Gold layer.
5. Airflow schedules and orchestrates pipeline dependencies.
6. Great Expectations validates critical data-quality rules.
7. Trino provides SQL access to curated datasets.
8. Prometheus and Grafana monitor system health and pipeline behavior.

## Repository Structure

```text
CustomerDNA AI/
  project_presentation/
    PFE_report/
      90_assets/
        architecture/
          Architecture_Final.drawio.png
  logs/
```

## Public Release Policy

This repository is prepared as a portfolio project. Before it becomes public, credentials, internal endpoints, customer data, local logs, and sensitive configuration must be removed or replaced with safe examples.

## Author

**Redouan Ait-Lahcen**  
Junior Data Engineer

- LinkedIn: [linkedin.com/in/ait-lahcen-redouan](https://www.linkedin.com/in/ait-lahcen-redouan/)
- GitHub: [github.com/AIT-LAHCEN-REDOUAN](https://github.com/AIT-LAHCEN-REDOUAN)
