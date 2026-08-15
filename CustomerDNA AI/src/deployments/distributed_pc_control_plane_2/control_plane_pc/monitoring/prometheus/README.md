# Prometheus Monitoring Stack

This folder contains the local Prometheus stack for CustomerDNA AI.

Included services:
- `prometheus`: metrics collection and querying
- `postgres_exporter`: PostgreSQL database metrics for the Hive metastore metadata database (`metastore_db`)
- `cadvisor`: Docker container resource metrics
- `pipeline_metrics_exporter`: custom exporter for project-specific Airflow / Kafka / HDFS / Spark / GX pipeline metrics

Setup:
1. Fill in your PostgreSQL password in `.env`.
2. Start the stack with Docker Compose.
3. Open Prometheus at `http://localhost:19090`.
4. Verify the targets page shows `prometheus`, `postgres_exporter`, `cadvisor`, and `pipeline_metrics_exporter` as healthy.

Suggested Grafana datasource:
- Type: Prometheus
- URL: `http://prometheus:9090`

Notes:
- `postgres_exporter` connects to the Hive metastore PostgreSQL service through `${CUSTOMERDNA_MONITORING_POSTGRES_HOST:-host.docker.internal}` on port `5435`.
- The compose file adds a `host.docker.internal -> host-gateway` mapping so the same config works more reliably on Linux Docker hosts.
- `cadvisor` is included for container-level CPU and memory monitoring.
- `pipeline_metrics_exporter` reads generated monitoring state files from `src/monitoring/state` and exposes them on port `9109`.
- `raw_load_state.json` appears only after the Kafka raw-load pipeline runs.
- This stack is intentionally lightweight for development and PFE demonstration.
