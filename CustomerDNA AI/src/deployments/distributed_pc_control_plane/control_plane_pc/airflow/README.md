# Local PC Airflow

Airflow runs on the local PC as the orchestration layer for the distributed cluster.

## Files That Matter

- [`../docker-compose.yml`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/docker-compose.yml)
- [`../.env`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/.env)
- [`../start_control_plane_pc.ps1`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/start_control_plane_pc.ps1)

## Runtime Model

- Airflow containers stay local.
- DAG code is mounted from the real repository.
- DAG tasks target Kafka, HDFS, Hive, Spark, and Trino on the VMs by IP.
- Raw Spark submission is forwarded from local Airflow to `VM2` over SSH, then executed inside the remote `spark-submit-client` container on `VM2`.
