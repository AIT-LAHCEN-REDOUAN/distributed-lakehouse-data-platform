# AdOptimizer CDP - Architecture and Security Summary

This file is a local standalone architecture summary for the report workspace.

## Logical pipeline

```text
Customer datasets
  -> Kafka ingestion
  -> HDFS bronze storage
  -> Spark raw loading
  -> Iceberg analytical tables
  -> Hive Metastore catalog
  -> Trino query layer
  -> dbt-spark transformations
  -> Great Expectations validation
  -> Airflow orchestration
  -> Prometheus and Grafana monitoring
```

## Physical deployment

### Local control plane

- Airflow
- Prometheus
- Grafana
- Kafka UI
- pipeline metrics exporter

### VM1

- Kafka broker
- HDFS DataNode
- Spark worker
- Trino worker
- cAdvisor

### VM2

- Kafka broker
- HDFS NameNode
- HDFS DataNode
- Spark master
- Spark worker
- Spark submit client
- Spark thrift server
- Spark history server
- Hive Metastore
- Hive Metastore database
- Trino coordinator
- Trino gateway
- Kerberos KDC
- cAdvisor

### VM3

- Kafka broker
- HDFS DataNode
- Spark worker
- Trino worker
- cAdvisor

## Security layer

The final deployed architecture integrates:

- Kerberos-secured Hadoop services,
- SPNEGO-protected HDFS browser access,
- TLS-protected browser-facing interfaces,
- authenticated Trino access,
- SSH-based remote Spark submission,
- and encrypted runtime storage support.

## Report meaning

This architecture must be presented as a distributed and secured customer-data engineering platform rather than a simple ETL pipeline.
