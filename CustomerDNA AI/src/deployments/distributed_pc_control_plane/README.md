# Distributed Deployment v2

This deployment tree is isolated from the original local deployment and from the earlier `VM1` / `VM2` / `VM3` control-plane attempt.

## Target Architecture

- `Local PC` = control plane
- `VM1 + VM2 + VM3` = distributed data plane

## Service Placement

### Local PC

- Airflow
- Airflow PostgreSQL
- Prometheus
- Grafana
- dbt execution
- Great Expectations execution

### VM1

- Kafka broker/controller `1`
- HDFS DataNode `1`
- Spark worker `1`
- Trino worker `1`
- Monitoring exporters

### VM2

- Kafka broker/controller `2`
- HDFS NameNode
- HDFS DataNode `2`
- Hive Metastore
- Hive Metastore PostgreSQL
- Spark master
- Spark submit helper
- Spark History Server
- Spark Thrift Server
- Spark worker `2`
- Trino coordinator
- Monitoring exporters

### VM3

- Kafka broker/controller `3`
- HDFS DataNode `3`
- Spark worker `3`
- Trino worker `2`
- Monitoring exporters

## Purpose of This Folder

This tree is the new deployment baseline for:

- distributed storage
- distributed ingestion
- distributed processing
- distributed query execution
- local orchestration outside the cluster

Each node has its own isolated folder so we can:

- edit one node without affecting the others
- zip and upload each node independently
- troubleshoot node-by-node
- keep deployment artifacts separate from the original local implementation
