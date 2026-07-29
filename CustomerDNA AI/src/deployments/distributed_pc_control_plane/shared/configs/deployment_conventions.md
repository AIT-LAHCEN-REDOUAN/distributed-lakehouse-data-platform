# Deployment Conventions

## Scope

These conventions apply only to the new isolated deployment tree:

- `src/deployments/distributed_pc_control_plane/control_plane_pc`
- `src/deployments/distributed_pc_control_plane/shared`
- `src/deployments/distributed_pc_control_plane/vm1`
- `src/deployments/distributed_pc_control_plane/vm2`
- `src/deployments/distributed_pc_control_plane/vm3`

## Principles

1. Each VM folder must stay independently uploadable and runnable.
2. Shared values belong in `shared/`, not copied by hand into every file without a template.
3. The local workstation is the control plane only.
4. The VMs are the distributed data plane.
5. Settings should favor a lightweight distributed demonstration because the VM resources are small.

## Naming

- Use `customerdna-` or `control_plane_` prefixes consistently for container names, volumes, and networks.
- Prefer node-explicit names when a service exists on multiple VMs, such as `broker_1`, `broker_2`, `broker_3`.

## Networking

- Use the VM IPs directly for cross-node communication.
- Keep hostnames inside each VM bundle predictable, but do not depend on local-only Docker DNS across different VMs.
- Document every published port in `ports_map.yml`.
- Prefer `network_mode: host` for the Linux VM bundles when the service must participate directly in cross-VM communication such as Kafka, HDFS, Spark, and Trino.

## Storage and Replication Guidance

- HDFS is distributed across three DataNodes for the demonstration.
- Kafka should use three brokers for the demonstration.
- Because the VMs are small, start with moderate replication values such as `2` instead of `3` unless testing proves the cluster can comfortably handle `3`.

## Runtime Separation

- Airflow, dbt, GX, Prometheus, and Grafana remain on the local PC.
- Spark execution remains remote even when submission starts from the local `spark-submit-client`.
- AI or ML workloads are downstream and out of this deployment scope.

## Validation Order

1. Shared assets
2. VM2 core services
3. VM1 worker-side services
4. VM3 worker-side services
5. Control-plane to cluster connectivity
6. End-to-end DAG execution
