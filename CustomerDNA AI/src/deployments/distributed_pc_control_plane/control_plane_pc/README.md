# Local PC Control Plane

This folder is the isolated control-plane deployment for the distributed demonstration architecture:

- local PC: Airflow, Airflow PostgreSQL, Prometheus, Grafana, dbt runtime, Great Expectations runtime, Spark submit helper
- VM1, VM2, VM3: distributed Kafka, HDFS, Spark, Hive, Trino, exporters

## What Runs Here

- Airflow API server, scheduler, dag processor, triggerer
- Airflow metadata PostgreSQL
- Spark submit helper container
- Kafka UI for supervising the distributed brokers
- pipeline metrics exporter
- Prometheus
- Grafana
- PostgreSQL exporter for the Hive Metastore database running on VM2

## What This Folder Uses

- duplicated deployment configs that are safe to change independently
- the real project code from the local repository through bind mounts
- the remote VM IPs defined in `.env`

## First Use

1. Review [`.env`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/.env) and confirm VM IPs.
2. Run [control_plane_preflight_checks.ps1](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/control_plane_preflight_checks.ps1).
3. Start the stack with [start_control_plane_pc.ps1](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/start_control_plane_pc.ps1).

## Access Points

- Airflow: `http://localhost:18080`
- Kafka UI: `http://localhost:18085`
- Prometheus: `http://localhost:19090`
- Grafana: `http://localhost:13001`

## Notes

- This stack expects the distributed data-plane services on the VMs to be started first, especially Kafka, HDFS, Hive Metastore, Spark, and Trino.
- `spark-submit-client` stays local on purpose. Airflow submits Spark jobs through it, but the actual execution target remains the remote Spark master on VM2.
