# CustomerDNA Monitoring

This folder centralizes the local monitoring and observability stack for CustomerDNA AI.

Structure:
- `grafana/`: Grafana container setup, dashboard provisioning, and versioned dashboards.
- `prometheus/`: Prometheus container setup, scrape configuration, and exporters.
- `exporters/`: custom exporters built for project-specific metrics.
- `shared/`: shared Python helpers used by Airflow, Kafka raw-loading scripts, and validation jobs to publish monitoring state.
- `state/`: generated runtime state files consumed by the custom exporter.

Main capabilities:
- Infrastructure monitoring for Prometheus, cAdvisor, and PostgreSQL exporter.
- PostgreSQL warehouse monitoring for `client1_DW`.
- Pipeline-health monitoring for Airflow task execution, Kafka raw loading, dbt execution, and Great Expectations checkpoints.
- Local execution compatible with the project constraint of running entirely on one machine.

Important design rule:
- Monitoring code and configuration should stay inside `src/monitoring` so observability remains isolated, versioned, and easy to maintain.

Generated state:
- Files inside `state/` are produced automatically when Airflow tasks, Kafka raw-loading scripts, and Great Expectations validations run.
- These state files are exported as Prometheus metrics through `exporters/pipeline_metrics_exporter.py`.
- Only `.gitkeep` and `.gitignore` should stay versioned in `state/`; JSON files there are runtime-generated artifacts.

Active generated state files:
- `airflow_pipeline_state.json`
- `raw_load_state.json`
- `gx_state.json`
