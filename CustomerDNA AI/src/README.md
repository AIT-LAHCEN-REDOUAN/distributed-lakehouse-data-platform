# CustomerDNA AI - Source Tree Guide

This `src/` directory is organized by platform responsibility so the project is easy to explain during implementation, testing, and jury defense.

Generated outputs are intentionally redirected to `CustomerDNA AI/artifacts/` so `src/` remains focused on maintainable source code.

## Main Folders

- `airflow/`
  Contains orchestration assets:
  Docker Compose, Airflow environment configuration, and the Client 1 DAGs.

- `streaming/`
  Contains the event-streaming layer:
  Kafka services, dataset producers, bronze consumers, and dataset-specific raw-load event handlers.

- `lake/`
  Contains the bronze data-lake layer:
  HDFS services and Client 1 bronze utilities for reset, inspection, and file-level persistence.

- `processing/`
  Contains the distributed processing layer:
  Spark cluster scaffolding, Spark jobs for bronze-to-raw loading, and distributed processing configuration.

- `catalog/`
  Contains the metastore layer:
  Hive Metastore services and configuration for the lakehouse catalog.

- `query/`
  Contains the query-service layer:
  Trino configuration and runtime assets for interactive SQL access over the lakehouse.

- `monitoring/`
  Contains observability assets:
  Prometheus, Grafana, pipeline exporters, runtime log export helpers, and monitoring state files.

## Data Flow View

`Source files -> Kafka -> HDFS bronze -> Spark bronze-to-Iceberg load -> Trino-ready raw lakehouse tables -> Airflow -> Great Expectations raw checks -> Prometheus/Grafana`

## Runtime Configuration

The project now follows an example-driven configuration approach:

- real local secrets and machine-specific values live in untracked `.env` files
- tracked `.env.example` files document the required variables for each runtime area
- service-specific compose stacks still work locally, but the repo no longer relies on committing real credentials

Relevant examples:

- `src/airflow/.env.example`
- `src/lake/hdfs/.env.example`
- `src/processing/spark/.env.example`
- `src/catalog/hive/.env.example`
- `src/query/trino/.env.example`
- `src/monitoring/prometheus/.env.example`
- `src/monitoring/grafana/.env.example`

## Code vs Runtime Artifacts

The repository keeps source code and generated artifacts conceptually separate:

- Source logic lives in the folders above.
- Runtime outputs such as logs, Kafka samples, HDFS bronze files, Spark event logs, and monitoring state are treated as generated artifacts.
- The preferred destination for generated business artifacts is `CustomerDNA AI/artifacts/`.
- The repository `.gitignore` is configured to reduce future clutter from these generated files.

## Jury Explanation Tip

When presenting the project, explain the folders in this order:

1. `streaming/` for ingestion transport
2. `lake/` for bronze persistence
3. `processing/` for distributed bronze-to-raw execution
4. `catalog/` for the Hive metastore service
5. `query/` for Trino SQL access to Iceberg tables
6. `airflow/` for orchestration
7. `monitoring/` for observability

This order matches the real technical flow and makes the architecture easier to understand.
