# VM3 Data Plane Worker

This folder is the isolated deployment bundle for `VM3` in the distributed demonstration architecture.

## VM3 Role

VM3 is a distributed worker node. It extends the cluster capacity started on `VM2`.

It hosts:

- Kafka broker/controller `3`
- HDFS DataNode `3`
- Spark worker `3`
- Trino worker `2`
- cAdvisor

## Why VM3 Starts After VM2

VM3 depends on VM2 for:

- HDFS NameNode
- Spark master
- Trino coordinator

Kafka controller quorum also expects VM2 to already be online.

## Files To Run

1. [prepare_fresh_vm3.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm3/prepare_fresh_vm3.sh>)
2. [vm3_preflight_checks.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm3/vm3_preflight_checks.sh>)
3. [start_vm3_stack.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm3/start_vm3_stack.sh>)
4. [reset_vm3_state.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm3/reset_vm3_state.sh>) for full wipe-and-redeploy tests

## Access Points On VM3

- Kafka broker external: `10.10.252.13:9092`
- HDFS DataNode web: `http://10.10.252.13:9864`
- Spark worker UI: `http://10.10.252.13:8087`
- Trino worker HTTP: `http://10.10.252.13:8080`
- cAdvisor: `http://10.10.252.13:8081`
