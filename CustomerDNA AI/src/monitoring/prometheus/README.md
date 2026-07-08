# Prometheus Monitoring Stack

This folder contains the local Prometheus stack for CustomerDNA AI.

Included services:
- `prometheus`: metrics collection and querying
- `postgres_exporter`: PostgreSQL database metrics for `client1_DW`
- `cadvisor`: Docker container resource metrics
- `pipeline_metrics_exporter`: custom exporter for project-specific Airflow / Kafka raw-load / dbt / GX metrics

Setup:
1. Fill in your PostgreSQL password in `.env`.
2. Start the stack with Docker Compose.
3. Open Prometheus at `http://localhost:9090`.
4. Verify the targets page shows `prometheus`, `postgres_exporter`, `cadvisor`, and `pipeline_metrics_exporter` as healthy.

Suggested Grafana datasource:
- Type: Prometheus
- URL: `http://host.docker.internal:9090`

Notes:
- `postgres_exporter` connects to your local PostgreSQL warehouse on port `5440`.
- `cadvisor` is included for container-level CPU and memory monitoring.
- `pipeline_metrics_exporter` reads generated monitoring state files from `src/monitoring/state` and exposes them on port `9109`.
- `raw_load_state.json` appears only after the Kafka raw-load pipeline runs.
- This stack is intentionally lightweight for development and PFE demonstration.
