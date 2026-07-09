# CustomerDNA AI - MinIO Bronze Layer

This folder provides the MinIO-based bronze layer for CustomerDNA AI.

## Purpose

MinIO stores the bronze copy of Kafka-ingested Client 1 data before it is loaded into PostgreSQL `raw_data`.

The ingestion architecture is now:

- Source datasets
- Kafka producers
- Kafka consumers
- MinIO bronze
- PostgreSQL `client1_DW.raw_data`
- dbt transformations
- Great Expectations validation
- Airflow orchestration
- Grafana and Prometheus monitoring

## Services

- `minio`
  - S3-compatible object storage API on port `9000`
  - MinIO web console on port `9001`

## Files

- `docker-compose.yml`
  Runs MinIO locally and joins the shared Kafka/Airflow Docker network
- `.env.example`
  Example MinIO credentials and ports

## Local Start

1. Copy `.env.example` to `.env`
2. Run:

```bash
docker compose up -d
```

3. Open:
   - API endpoint: `http://localhost:9000`
   - Console: `http://localhost:9001`

## Client 1 Bronze Utilities

The Client 1 bronze scripts live in:

- `src/lake/minio/client_1`

Install the MinIO Python client before running them:

```bash
python -m pip install -r "src/lake/minio/requirements.txt"
```

Available utilities:

- `reset_client1_bronze.py`
  Deletes the existing Client 1 bronze objects for a clean full rerun
- `list_client1_bronze_objects.py`
  Lists the bronze JSONL objects currently stored for Client 1

## Bronze Object Layout

Client 1 Kafka consumers write JSONL batches under:

```text
bronze/client_1/kafka_topics/<dataset_key>/run_id=<timestamp>/part_00001.jsonl
```

This keeps bronze data:

- dataset-separated
- run-separated
- easy to inspect
- easy to reload into PostgreSQL raw tables

## Role in the Pipeline

MinIO is not replacing PostgreSQL raw storage.

Its job is to add a proper bronze data-lake layer between Kafka and the warehouse:

- Kafka guarantees durable event transport
- MinIO preserves bronze ingestion batches
- PostgreSQL `raw_data` remains the structured warehouse raw layer

So the final interpretation is:

- `MinIO bronze` = immutable ingestion landing layer
- `PostgreSQL raw_data` = structured warehouse raw layer
