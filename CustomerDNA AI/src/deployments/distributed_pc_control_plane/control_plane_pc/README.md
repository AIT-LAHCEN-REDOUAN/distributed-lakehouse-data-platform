# Local PC Control Plane

This folder is the isolated control-plane deployment for the distributed demonstration architecture:

- local PC: Airflow, Airflow PostgreSQL, Prometheus, Grafana, dbt runtime, Great Expectations runtime
- VM1, VM2, VM3: distributed Kafka, HDFS, Spark, Hive, Trino, exporters

## What Runs Here

- Airflow API server, scheduler, dag processor, triggerer
- Airflow metadata PostgreSQL
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
2. Place the SSH private key for VM2 remote Spark submission under `ssh/id_ed25519` and authorize the matching public key on VM2.
3. Run [control_plane_preflight_checks.ps1](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/control_plane_preflight_checks.ps1).
4. Start the stack with [start_control_plane_pc.ps1](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/start_control_plane_pc.ps1).
5. If a port is busy, the startup script writes the resolved ports to `runtime/compose.generated.env`. Use the script again for retries so the same ports are reused.
6. Use [backup_control_plane_state.ps1](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/backup_control_plane_state.ps1) whenever you want a quick metadata and config backup snapshot.

## Access Points

- Airflow: `http://localhost:18080`
- Kafka UI: `http://localhost:18085`
- Prometheus: `http://localhost:19090`
- Grafana: `http://localhost:13001`
- Credential reference files: `src/Credential Access/`

## Notes

- This stack expects the distributed data-plane services on the VMs to be started first, especially Kafka, HDFS, Hive Metastore, Spark, and Trino.
- Airflow stays local, but raw Spark submission is executed remotely on VM2 over SSH inside the VM2 `spark-submit-client` container.
- `CUSTOMERDNA_SPARK_DRIVER_HOST` is now pinned to `VM2`, so Spark executors no longer depend on the changing workstation IP.
- Monitoring state for the distributed demo is isolated under `runtime/monitoring/state` so it does not reuse the local single-machine run history.
- Airflow startup is intentionally staged: PostgreSQL starts first, then `airflow-init`, then the API server, and only after that the scheduler, dag processor, and triggerer.
- Trino access now goes through the secured VM2 gateway on `http://10.10.252.12:8088`, while the coordinator itself listens internally on port `8089`.
