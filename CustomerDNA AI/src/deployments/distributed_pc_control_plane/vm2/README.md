# VM2 Data Plane Leader

This folder is the isolated deployment bundle for `VM2` in the distributed demonstration architecture.

## VM2 Role

VM2 is the metadata and coordination node of the distributed data plane.

It hosts:

- Kafka broker/controller `2`
- HDFS NameNode
- HDFS DataNode `2`
- Hive Metastore PostgreSQL
- Hive Metastore
- Spark master
- Spark worker `2`
- Spark History Server
- Spark Thrift Server
- Trino coordinator
- cAdvisor

## Why VM2 Starts First

VM2 is the anchor node for:

- HDFS namespace
- Hive catalog metadata
- Spark master coordination
- Trino coordination

VM1 and VM3 depend on these services to join the distributed cluster cleanly.

## Files To Run

1. [prepare_fresh_vm2.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm2/prepare_fresh_vm2.sh>)
2. [vm2_preflight_checks.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm2/vm2_preflight_checks.sh>)
3. [start_vm2_stack.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm2/start_vm2_stack.sh>)
4. [reset_vm2_state.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm2/reset_vm2_state.sh>) for full wipe-and-redeploy tests

## Important Note

Kafka broker `2` may not become fully healthy until `VM1` and `VM3` bring up broker/controller `1` and `3`, because the KRaft controller quorum spans all three VMs. That is expected.

On older VM CPUs, newer Trino images can fail immediately with `CPU does not support x86-64-v3`. This VM2 bundle therefore pins Trino to an older image line by default.

## Access Points On VM2

- Kafka broker external: `10.10.252.12:9092`
- HDFS NameNode RPC: `10.10.252.12:9000`
- HDFS NameNode web: `http://10.10.252.12:9870`
- Hive Metastore: `10.10.252.12:9083`
- Hive Metastore PostgreSQL: `10.10.252.12:5435`
- Spark master: `spark://10.10.252.12:7077`
- Spark master UI: `http://10.10.252.12:8086`
- Spark Thrift: `10.10.252.12:10000`
- Spark History UI: `http://10.10.252.12:18080`
- Trino coordinator: `http://10.10.252.12:8088`
- cAdvisor: `http://10.10.252.12:8081`
