# VM1 Data Plane Worker

This folder is the isolated deployment bundle for `VM1` in the distributed demonstration architecture.

## VM1 Role

VM1 is a distributed worker node. It extends the cluster capacity started on `VM2`.

It hosts:

- Kafka broker/controller `1`
- HDFS DataNode `1`
- Spark worker `1`
- Trino worker `1`
- cAdvisor

## Why VM1 Starts After VM2

VM1 depends on VM2 for:

- HDFS NameNode
- Spark master
- Trino coordinator

Kafka controller quorum also expects VM2 to already be online.

## Files To Run

1. [prepare_fresh_vm1.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm1/prepare_fresh_vm1.sh>)
2. [vm1_preflight_checks.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm1/vm1_preflight_checks.sh>)
3. [start_vm1_stack.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm1/start_vm1_stack.sh>)
4. [reset_vm1_state.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm1/reset_vm1_state.sh>) for full wipe-and-redeploy tests
5. [setup_encrypted_storage_vm1.sh](</D:/github/Master_PFE_Project/CustomerDNA AI/src/deployments/distributed_pc_control_plane/vm1/setup_encrypted_storage_vm1.sh>) before stack startup when LUKS-backed runtime storage is enabled

## Access Points On VM1

- Kafka broker external: `10.10.252.11:9092`
- HDFS DataNode web: `http://10.10.252.11:9864`
- Spark worker UI: `http://10.10.252.11:8087`
- Trino worker HTTP: `http://10.10.252.11:8080`
- cAdvisor: `http://10.10.252.11:8081`

## Security Note

The VM1 runtime service data can be mounted on a LUKS-encrypted filesystem under `/mnt/customerdna_secure`. When enabled, Kafka, HDFS DataNode data, Spark event data, Spark Ivy cache, and Trino runtime data use the encrypted mount instead of the plain local runtime folder.
