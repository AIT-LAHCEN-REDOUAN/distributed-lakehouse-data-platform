# CustomerDNA Platform - Security and DataSecOps Guide

This guide documents the practical security baseline for the development branch while keeping the platform easy to run locally for demos, testing, and jury presentations.

## Objectives

- keep real credentials out of tracked source files
- make runtime configuration explicit and reproducible
- separate source code from generated runtime state
- make troubleshooting easier through predictable logs and state artifacts
- prepare the project for a smoother transition toward production hardening later

## Configuration Model

The repository uses two configuration layers:

1. tracked `.env.example` files
   These document the variables each subsystem expects.
2. untracked local `.env` files
   These hold the real values used on the developer machine.

### Current `.env.example` locations

- `src/airflow/.env.example`
- `src/lake/hdfs/.env.example`
- `src/processing/spark/.env.example`
- `src/catalog/hive/.env.example`
- `src/query/trino/.env.example`
- `src/monitoring/prometheus/.env.example`
- `src/monitoring/grafana/.env.example`

## Sensitive Values

The following values must stay local and must not be committed:

- PostgreSQL passwords
- Airflow admin password
- Airflow JWT secret
- Grafana admin password
- future API keys, OAuth secrets, or cloud credentials

The repository `.gitignore` now excludes all `.env` files while preserving `.env.example`.

## Runtime State Separation

Generated state is intentionally separated from source code:

- Airflow task logs: `src/airflow/logs/`
- Monitoring exported logs: `src/monitoring/logs/`
- Monitoring state JSON: `src/monitoring/state/`
- Kafka runtime logs and samples: `src/streaming/kafka/logs/`, `src/streaming/kafka/consumer_output/`
- Great Expectations runtime artifacts: `src/quality/great_expectations/client_1/artifacts/`, `src/quality/great_expectations/client_1/data_docs/`
- Spark event logs: Spark-managed event/log volumes configured from `src/processing/spark/`

This makes it easier to explain which files are source-controlled platform code and which files are execution artifacts.

## Service-Level Security Notes

### Airflow

- metadata database credentials are now parameterized through environment variables
- the admin user profile fields are no longer hardcoded directly in the compose file
- local host/port rewriting is handled centrally in DAG helpers so containers do not accidentally target invalid localhost endpoints

### Kafka

- Kafka remains the ingestion backbone
- dataset-specific producers and consumers are isolated by folder for traceability
- topic reset behavior supports deterministic reruns in development

### HDFS Bronze

- HDFS acts as the bronze persistence layer
- raw source files are landed before structured loading
- this separation helps data lineage, rerun control, and future replay scenarios

### Spark

- Spark is the distributed raw-loading layer between HDFS bronze and Iceberg raw tables
- credentials passed to Spark submission are masked in displayed commands where applicable
- Spark submit settings are centralized in the submitter utility

### Hive Metastore PostgreSQL

- PostgreSQL is still used, but now only as the metadata backend for the Hive metastore service
- business data is no longer landed in PostgreSQL tables as the primary raw layer
- the metastore database remains isolated from direct source-file ingestion logic

### Monitoring

- Prometheus and Grafana are kept in `src/monitoring/`
- pipeline-state exporters are separated from dashboard definitions
- runtime logs can be exported consistently for incident analysis

## DataSecOps Practices Already Reflected in the Project

- configuration externalization through environment variables
- explicit runtime/log separation
- orchestration traceability through Airflow task history
- data quality checkpoints through Great Expectations
- separated bronze persistence before distributed Spark-to-Iceberg loading
- pipeline observability through Prometheus and Grafana
- independent service layers for Kafka, HDFS, Hive Metastore, Spark, Iceberg, Trino, and monitoring

## Recommended Production Hardening Later

The dev branch remains demo-friendly. For production, the next hardening steps should be:

- move secrets to a vault or server-side secret manager
- disable weak fallback credentials in compose stacks
- restrict exposed ports to only the necessary interfaces
- add TLS and reverse-proxy protection for Airflow, Grafana, and Kafka UI
- enforce role-based access and stronger password rotation
- schedule backup and restore tests for HDFS and PostgreSQL
- add image pinning and vulnerability scanning in CI/CD

## Jury Explanation

When presenting security and DataSecOps in the defense, emphasize that the platform already includes:

- secret externalization
- layered persistence
- reproducible orchestration
- automated quality controls
- centralized observability

This positions the project as a serious data-engineering platform rather than only a collection of scripts.
