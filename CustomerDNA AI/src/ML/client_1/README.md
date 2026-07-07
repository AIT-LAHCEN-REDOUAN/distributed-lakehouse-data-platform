# Client 1 ML Workspace

This folder is the ML layer for Client 1 in CustomerDNA AI.

It is intentionally separated from ingestion, dbt, Great Expectations, Airflow, and monitoring so that the ML phase behaves as a controlled downstream consumer of trusted warehouse outputs.

## Design Rule

The ML layer must consume curated data from the `serving` schema, not directly from `raw_data`, `staging`, or `intermediate`.

## Planned Use Cases

- customer segmentation
- churn prediction
- lifetime value prediction
- persona generation
- marketing recommendation generation

## Folder Purpose

- `configs/` stores run configuration files for each ML use case.
- `data_access/` stores warehouse extraction and dataset snapshot logic.
- `datasets/` stores generated local snapshots, manifests, and safe samples.
- `pipelines/` stores end-to-end orchestration scripts for ML workflows.
- `preprocessing/` stores ML-specific data preparation code.
- `training/` stores model-training entry points.
- `evaluation/` stores metrics and evaluation logic.
- `models/` stores serialized models and model metadata.
- `inference/` stores batch prediction and downstream output generation logic.
- `reports/` stores experiment summaries and business-readable outputs.
- `notebooks/` stores exploratory notebooks only.

## Implementation Principle

Business meaning should remain in dbt and the serving layer. Python in this ML workspace should focus on model-specific preparation, training, evaluation, and inference.
