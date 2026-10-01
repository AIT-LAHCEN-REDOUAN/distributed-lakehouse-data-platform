# AdOptimizer Customer Data Platform - Local Runbook

This runbook explains how to run, validate, and later benchmark the project without changing the local development behavior.

The validated local architecture is:

```text
Source datasets
  -> Kafka
  -> HDFS bronze zone
  -> Spark distributed processing
  -> Iceberg lakehouse tables
  -> Hive Metastore catalog
  -> dbt-spark transformations
  -> Trino SQL access
  -> Great Expectations quality checks
  -> Airflow orchestration
  -> Prometheus/Grafana monitoring
```

## 1. Local Runtime Principle

The local machine is the official development and demonstration baseline.

Do not remove local `.env` files from the development branch if they are required for local testing. Production deployment can replace them later with environment-specific secrets and stronger secret-management practices.

## 2. Container Startup Order

Start services in dependency order:

1. Kafka
2. HDFS
3. Hive Metastore
4. Spark
5. Trino
6. Prometheus
7. Grafana
8. Airflow

This order reduces startup issues because later services depend on earlier services.

## 3. Airflow DAG Execution Order

Run the DAGs in this order:

1. `customerdna_client1_lakehouse_setup_pipeline`
2. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
3. `customerdna_client1_dbt_spark_lakehouse_pipeline`
4. `customerdna_client1_lakehouse_readiness_pipeline`

## 4. What Each DAG Proves

### 4.1 Lakehouse Setup Pipeline

`customerdna_client1_lakehouse_setup_pipeline`

Purpose:

- initializes the HDFS bronze root for Client 1,
- initializes Hive/Iceberg namespaces,
- validates Trino query access.

Expected result:

- HDFS contains the initial lakehouse folders,
- Trino can see the lakehouse catalog and schemas,
- Airflow marks all setup tasks as successful.

### 4.2 Kafka HDFS Spark Lakehouse Pipeline

`customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`

Purpose:

- streams source datasets through Kafka,
- persists the bronze files into HDFS,
- runs Spark to process bronze data,
- creates raw Iceberg tables,
- runs raw lakehouse quality validation.

Expected result:

- HDFS bronze contains source-level persisted files,
- Iceberg raw tables are available through Trino,
- row counts match expected source volumes,
- Great Expectations raw validation succeeds.

### 4.3 dbt Spark Lakehouse Pipeline

`customerdna_client1_dbt_spark_lakehouse_pipeline`

Purpose:

- validates Spark Thrift availability,
- runs dbt-spark transformations,
- creates staging, intermediate, and analytics Iceberg tables,
- runs dbt tests,
- validates Trino query access.

Expected result:

- curated lakehouse schemas exist,
- dbt-spark models complete successfully,
- dbt tests complete successfully,
- Trino can query transformed tables.

### 4.4 Lakehouse Readiness Pipeline

`customerdna_client1_lakehouse_readiness_pipeline`

Purpose:

- validates HDFS,
- validates Hive Metastore,
- validates Spark Master,
- validates Spark Thrift,
- validates Trino.

Expected result:

- all critical platform services are reachable,
- Airflow reports a green readiness check,
- Grafana pipeline-health dashboard shows successful service readiness.

## 5. Browser Access Points

Use these URLs in local development:

| Tool | URL | Purpose |
|---|---|---|
| Airflow | `http://localhost:8080` | DAG orchestration and task logs |
| Kafka UI | `http://localhost:8081` | Kafka topics and message inspection |
| HDFS NameNode | `http://localhost:9870` | HDFS health and file browser |
| Spark Master | `http://localhost:8086` | Spark cluster status |
| Spark Worker | `http://localhost:8087` | Spark worker status |
| Spark History Server | `http://localhost:18080` | Spark job history |
| Spark Thrift UI | `http://localhost:4040` | Spark SQL/Thrift runtime UI when active |
| Trino | `http://localhost:8088` | Trino query service UI |
| Prometheus | `http://localhost:9090` | Metrics scraping and queries |
| Grafana | `http://localhost:3001` | Monitoring dashboards |

## 6. DBeaver Connection for Trino

Use DBeaver to inspect Iceberg lakehouse tables through Trino:

| Field | Value |
|---|---|
| Driver | Trino |
| Host | `localhost` |
| Port | `8088` |
| Database/Catalog | `lakehouse` |
| Username | any local username, for example `admin` |
| Password | empty unless local configuration requires one |

After connecting, refresh the `lakehouse` catalog and inspect:

- `raw_data`
- `staging`
- `intermediate`
- `analytics`

## 7. Monitoring Validation

Grafana should show:

- infrastructure targets as healthy,
- Hive Metastore PostgreSQL as available,
- pipeline-health statuses as successful after DAG execution,
- raw rows inserted in the last run,
- Airflow task durations,
- dbt-spark and quality-check statuses.

If a dashboard shows stale values, check:

- the selected Grafana time range,
- Prometheus target health,
- whether the latest Airflow DAG run has completed,
- whether the pipeline metrics exporter is running.

## 8. Local vs Multi-Machine Benchmark Plan

The local environment is the baseline. The future company deployment should be measured using the same DAGs and same datasets.

Recommended benchmark metrics:

| Metric | Source |
|---|---|
| End-to-end DAG duration | Airflow |
| Kafka ingestion duration | Airflow logs and pipeline metrics |
| HDFS bronze write duration | Airflow logs and pipeline metrics |
| Spark raw Iceberg build duration | Airflow logs and Spark UI |
| dbt-spark transformation duration | Airflow logs and dbt output |
| Great Expectations validation duration | Airflow logs |
| Trino query latency | DBeaver, Trino UI, or query logs |
| CPU and memory usage | Grafana |
| Service health | Grafana and Prometheus |

## 9. Fair Benchmarking Rules

For local-vs-deployed comparison:

- use the same data,
- use the same DAG order,
- use the same transformation models,
- use the same quality checks,
- record machine specifications,
- record container/service distribution,
- repeat important runs when possible,
- compare average runtime, not only one run.

## 10. Defense Message

The correct explanation is:

> The local platform validates the full Data Engineering architecture. The deployed platform will evaluate the same architecture when HDFS storage and Spark processing are distributed across several machines.

This makes the project defensible as a Big Data and Data Engineering platform rather than only a local ETL demo.
