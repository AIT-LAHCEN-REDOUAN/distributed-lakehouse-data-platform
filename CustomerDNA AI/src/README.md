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
  MinIO services and Client 1 bronze utilities for reset, inspection, and object-level persistence.

- `ELT/`
  Contains the structured warehouse pipeline:
  PostgreSQL setup, bronze-to-raw loading logic, dbt transformations, Great Expectations validation, and dataset-level EDA.

- `monitoring/`
  Contains observability assets:
  Prometheus, Grafana, pipeline exporters, runtime log export helpers, and monitoring state files.

- `ML/`
  Contains downstream experimentation assets:
  serving-data extraction, preprocessing, training, inference, and ML-focused EDA built on curated warehouse outputs.

## Data Flow View

The implemented Client 1 platform follows this path:

`Source files -> Kafka -> MinIO bronze -> PostgreSQL raw_data -> dbt -> GX -> Airflow -> Prometheus/Grafana`

## Code vs Runtime Artifacts

The repository keeps source code and generated artifacts conceptually separate:

- Source logic lives in the folders above.
- Runtime outputs such as logs, dbt targets, Kafka samples, ML generated outputs, and EDA outputs are treated as generated artifacts.
- The preferred destination for generated business artifacts is `CustomerDNA AI/artifacts/`.
- The repository `.gitignore` is configured to reduce future clutter from these generated files.

## Jury Explanation Tip

When presenting the project, explain the folders in this order:

1. `streaming/` for ingestion transport
2. `lake/` for bronze persistence
3. `ELT/` for warehouse loading and transformation
4. `airflow/` for orchestration
5. `monitoring/` for observability
6. `ML/` as downstream reuse of curated data products

This order matches the real technical flow and makes the architecture easier to understand.
