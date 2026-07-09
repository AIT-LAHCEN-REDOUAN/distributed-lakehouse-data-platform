# Grafana Dashboards

This folder stores versioned Grafana dashboard definitions as JSON.

Important:
- These dashboard JSON files are source-controlled assets.
- If Grafana is restarted and a dashboard appears empty or missing, first verify the JSON file still exists in this folder and the provisioning path still mounts it into the container.

Current dashboards:

- `customerdna_infrastructure.dashboard.json`
  Covers stable Prometheus / cAdvisor infrastructure metrics such as healthy scrape targets, host CPU cores, host memory capacity, exporter availability, exporter CPU usage, and exporter memory usage.

- `customerdna_postgres.dashboard.json`
  Covers PostgreSQL warehouse metrics exposed through `postgres_exporter`, including availability, database size, active connections, commit rate, rollback rate, and rows returned rate.

- `customerdna_pipeline_health.dashboard.json`
  Covers project-level pipeline observability, including DAG health, Kafka raw-loading outcomes, dbt/GX task execution, and raw rows inserted by table.

Recommended usage:

1. Start Prometheus and the exporters from `src/monitoring/prometheus`.
2. Start Grafana with the compose file in this folder.
3. Grafana provisions the `prometheus` datasource automatically from `provisioning/datasources/prometheus.yml`.
4. Grafana provisions dashboards automatically into the `CustomerDNA Monitoring` folder from `provisioning/dashboards/customerdna.yml`.
5. If you update a dashboard JSON file, restart Grafana or wait for the provider refresh interval.

Manual import remains possible if you want to test a dashboard before committing it.

Notes:
- All dashboards assume the Prometheus datasource is named `prometheus`.
- The PostgreSQL dashboard assumes the warehouse database label is `client1_DW`.
- The infrastructure dashboard intentionally avoids unstable container labels, because this local cAdvisor setup exposes host-oriented `id` labels instead of Docker-friendly `container` labels.
- The pipeline-health dashboard depends on state files written under `src/monitoring/state` by Airflow task instrumentation, the Client 1 Kafka raw pipeline runner, and Great Expectations validation scripts.
