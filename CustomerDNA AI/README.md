# CustomerDNA AI - Repository Guide

CustomerDNA AI is organized so that the implementation code, generated artifacts, business documentation, and presentation assets are easy to distinguish.

## Top-Level Structure

- `src/`
  Main implementation code for ingestion, lake, warehousing, orchestration, monitoring, and downstream ML experimentation.

- `artifacts/`
  Generated runtime outputs such as ML datasets, model files, reports, and warehouse-backed EDA results.

- `datasets/`
  Source datasets used by the platform before they enter the streaming and lakehouse pipeline.

- `project_requirements/`
  Functional scope, business rules, and PFE-oriented documentation.

- `project_presentation/`
  Presentation assets prepared for reporting and defense.

- `verify_installations/`
  Environment bootstrap helpers for validating required local dependencies.

## Platform Flow

The implemented Client 1 data platform follows this sequence:

`Source datasets -> Kafka -> MinIO bronze -> PostgreSQL raw_data -> dbt -> Great Expectations -> Airflow -> Prometheus/Grafana`

## Design Principle

This repository keeps a clear separation between:

- source code that defines the platform
- generated outputs produced by running the platform

That separation makes the project easier to maintain during development and easier to explain during the jury presentation.
