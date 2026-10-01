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

`Source datasets -> Kafka -> HDFS bronze -> Spark raw loading -> PostgreSQL raw_data -> dbt -> Great Expectations -> Airflow -> Prometheus/Grafana`

In the current architecture:

- Apache Kafka is the transport and event-driven loading backbone.
- HDFS is the bronze persistence layer for dataset-run files before structured loading.
- Apache Spark is the distributed raw-loading and heavy-processing execution layer between bronze and the warehouse.
- PostgreSQL is the warehouse engine for `raw_data`, `staging`, `intermediate`, `analytics`, and `serving`.
- dbt, Great Expectations, Airflow, Prometheus, and Grafana complete the transformation, quality, orchestration, and observability stack.

## Design Principle

This repository keeps a clear separation between:

- source code that defines the platform
- generated outputs produced by running the platform

That separation makes the project easier to maintain during development and easier to explain during the jury presentation.
