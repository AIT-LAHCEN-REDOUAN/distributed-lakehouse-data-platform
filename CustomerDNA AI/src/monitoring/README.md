# CustomerDNA Monitoring

This folder contains the monitoring stack for CustomerDNA AI:
- Grafana dashboards and provisioning
- Prometheus configuration and exporters
- Shared pipeline-state tracking utilities
- Runtime state files used by the pipeline metrics exporter
- Runtime log exports for easier troubleshooting

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
