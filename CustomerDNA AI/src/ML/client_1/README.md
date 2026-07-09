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
- `preprocessing/` stores ML-specific data preparation code.
- `training/` stores model-training entry points.
- `inference/` stores batch prediction and downstream output generation logic.
- `eda/` stores ML-oriented exploratory analysis scripts and visualization logic.

## Generated Artifacts

Runtime outputs are intentionally kept outside `src/` so the ML codebase stays clean:

- snapshots, samples, and processed matrices go to `CustomerDNA AI/artifacts/client_1/ml/datasets/`
- model binaries and metadata go to `CustomerDNA AI/artifacts/client_1/ml/models/`
- experiment reports and business summaries go to `CustomerDNA AI/artifacts/client_1/ml/reports/`
- ML EDA plots and markdown outputs go to `CustomerDNA AI/artifacts/client_1/ml/eda/`

## Implementation Principle

Business meaning should remain in dbt and the serving layer. Python in this ML workspace should focus on model-specific preparation, training, evaluation, and inference.
