# CustomerDNA Monitoring

This folder contains the observability layer for the current lakehouse architecture:
- Grafana dashboards and provisioning
- Prometheus configuration and exporters
- Shared pipeline-state tracking utilities
- Runtime state files used by the pipeline metrics exporter
- Runtime log exports for easier troubleshooting

Important:
- Dashboard JSON files under `grafana/dashboards/` are source files and should stay version-controlled.
- Runtime state files under `state/` are generated at execution time and should not be committed.
- Exported logs are troubleshooting artifacts and should not be committed.
- Real credentials should remain in local `.env` files; tracked `.env.example` files document the expected variables.

## Key Folders
- `grafana/`: dashboard JSON files and Grafana provisioning
- `prometheus/`: Prometheus stack configuration
- `shared/`: Python helpers used by Airflow, Kafka, and GX monitoring
- `state/`: generated JSON state files consumed by the pipeline metrics exporter
- `logs/`: exported runtime logs for Grafana, Prometheus, and exporters
- `tools/`: troubleshooting utilities, including Docker log export helpers

## Runtime Log Export
Use `tools/export_runtime_logs.py` to export the latest container logs into project files.

Typical outputs:
- `src/airflow/logs/system/airflow_api_server.log`
- `src/airflow/logs/system/airflow_scheduler.log`
- `src/airflow/logs/system/airflow_dag_processor.log`
- `src/airflow/logs/system/airflow_triggerer.log`
- `src/airflow/logs/system/airflow_postgres.log`
- `src/streaming/kafka/logs/broker.log`
- `src/streaming/kafka/logs/kafka_ui.log`
- `src/monitoring/logs/grafana/grafana.log`
- `src/monitoring/logs/prometheus/prometheus.log`
- `src/monitoring/logs/prometheus/postgres_exporter.log`
- `src/monitoring/logs/prometheus/cadvisor.log`
- `src/monitoring/logs/prometheus/pipeline_metrics_exporter.log`

## Environment Files

- `prometheus/.env.example` documents the Hive metastore PostgreSQL exporter variables and the lakehouse service probe variables.
- `grafana/.env.example` documents the Grafana admin variables.
- local `.env` files are intentionally ignored by Git.

## Monitoring Scope

This monitoring layer covers three views:

- infrastructure monitoring
  Container health, exporter availability, pipeline exporter reachability, and host-level CPU and memory visibility.
- Hive metastore PostgreSQL monitoring
  Availability, metadata database size, connections, commit activity, rollback activity, and returned-row metrics.
- pipeline health monitoring
  Airflow execution state, Kafka-to-HDFS-to-Spark raw-load summaries, raw-quality checkpoint status, dbt-spark transformation execution, lakehouse readiness checks, and freshness-style operational indicators.

## Lakehouse Service Probes

The custom pipeline metrics exporter also probes the core runtime services used by the platform:

- Kafka broker
- HDFS NameNode web endpoint
- Hive metastore service
- Spark master UI
- Spark Thrift Server
- Trino query service

These probes are emitted as Prometheus metrics and are used by the dashboards to confirm whether the lakehouse control plane is reachable.

## Runtime Log Export

The log export utility now covers the full runtime stack:

- Airflow services
- Kafka broker and Kafka UI
- HDFS NameNode and DataNode
- Hive metastore and its PostgreSQL metadata database
- Spark master, worker, history server, and Thrift Server
- Trino
- Grafana, Prometheus, cAdvisor, PostgreSQL exporter, and the pipeline metrics exporter
