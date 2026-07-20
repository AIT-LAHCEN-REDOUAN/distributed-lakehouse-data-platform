# AdOptimizer Customer Data Platform - Distributed Deployment Runbook

> **Purpose:** This runbook prepares the future deployment workflow for the 3-machine environment requested from IT.  
> **Important:** This document is only a deployment guide. It does not modify the local project, local Docker configuration, local `.env` files, Airflow DAGs, Spark code, Kafka code, HDFS code, dbt models, Great Expectations assets, or monitoring configuration.

---

## 1. Deployment Scope

The deployment objective is to run the validated local platform on a small distributed environment composed of 3 machines.

The target architecture remains logically identical to the validated local architecture:

```text
Source datasets
  -> Kafka
  -> HDFS bronze zone
  -> Spark distributed processing
  -> Iceberg lakehouse tables
  -> Hive Metastore catalog
  -> dbt-spark transformations
  -> Trino SQL access
  -> Great Expectations quality validation
  -> Airflow orchestration
  -> Prometheus and Grafana monitoring
```

The local machine remains the official development baseline. The deployed environment is used to evaluate distributed behavior, scalability, latency, and performance.

---

## 2. Non-Negotiable Safety Rule

Deployment work must not break the local environment.

Rules:

- Do not overwrite local `.env` files.
- Do not replace local Docker Compose files unless a backup exists.
- Do not delete local Docker volumes during deployment preparation.
- Do not change validated local Airflow DAG logic without testing in local first.
- Do not hardcode server IPs directly in Python, SQL, YAML, or Docker Compose files.
- Use deployment-specific environment files for server settings.
- Keep local and deployment configurations separate.

Recommended separation:

```text
local configuration      -> existing project files and existing local .env
deployment configuration -> future deployment-specific .env or server inventory files
```

---

## 3. Expected Machine Layout

The initial deployment target is 3 machines.

| Machine | Suggested Hostname | Main Role |
|---|---|---|
| Machine 1 | `adoptimizer-node-01` | Orchestration, access, monitoring, Trino coordinator |
| Machine 2 | `adoptimizer-node-02` | Kafka, HDFS DataNode, Hive Metastore support, Spark worker |
| Machine 3 | `adoptimizer-node-03` | HDFS NameNode, HDFS DataNode, Spark master, Spark worker, Spark Thrift |

This role distribution may be adjusted after real resource testing.

---

## 4. Information Needed Before Starting

Before installing anything, collect the following from IT:

| Item | Required Value |
|---|---|
| Machine 1 hostname | To be provided by IT |
| Machine 1 private IP | To be provided by IT |
| Machine 2 hostname | To be provided by IT |
| Machine 2 private IP | To be provided by IT |
| Machine 3 hostname | To be provided by IT |
| Machine 3 private IP | To be provided by IT |
| SSH username | To be provided by IT |
| SSH authentication method | Password or SSH key |
| sudo access | Yes/No |
| internet access | Yes/No |
| proxy required | Yes/No |
| firewall restrictions | To be confirmed |
| internal DNS available | Yes/No |

Do not start deployment until these details are known.

---

## 5. Pre-Deployment Checks

Run these checks manually after receiving SSH access.

### 5.1 SSH Access Check

Confirm that you can connect to each machine.

Expected result:

- SSH works on all 3 machines.
- The same deployment user can access all machines.
- The deployment user has sudo permissions.

### 5.2 Hostname and Network Check

Confirm that:

- Machine 1 can reach Machine 2 and Machine 3.
- Machine 2 can reach Machine 1 and Machine 3.
- Machine 3 can reach Machine 1 and Machine 2.
- The machines can resolve each other by hostname or can be configured in `/etc/hosts`.

### 5.3 Time Synchronization Check

Confirm all machines use the same timezone and synchronized time.

Why this matters:

- Airflow logs must align across services.
- Spark logs must align with Airflow task duration.
- Benchmark latency measurements require reliable timestamps.

### 5.4 Disk Check

Confirm each machine has enough disk.

Minimum expected:

- 50 GB per machine.

Preferred:

- 100 GB per machine or more.

Important storage paths:

```text
/data/hdfs
/data/docker
/data/logs
/data/spark-events
/data/monitoring
```

---

## 6. Configuration Strategy

Deployment configuration must be environment-driven.

Use variables for:

- Kafka bootstrap servers.
- HDFS NameNode URI.
- HDFS WebHDFS endpoint.
- Spark master URL.
- Spark Thrift Server host and port.
- Hive Metastore URI.
- Trino URL.
- Airflow base URL.
- Grafana URL.
- Prometheus URL.
- Dataset paths.
- Log paths.

Do not hardcode machine IPs inside code.

Recommended future pattern:

```text
local .env        -> local laptop execution
deploy .env       -> 3-machine distributed execution
production .env   -> final company server execution
```

---

## 7. Planned Deployment Order

The deployment should be done in this order.

### Step 1 - Prepare Operating System

Goal:

- Make all machines ready for containers and distributed services.

Expected actions:

- Update packages.
- Configure hostnames.
- Configure `/etc/hosts` if internal DNS is not available.
- Configure time synchronization.
- Create deployment directories.
- Confirm SSH/sudo access.

### Step 2 - Install Container Runtime

Goal:

- Prepare Docker and Docker Compose on each machine.

Expected actions:

- Install Docker Engine.
- Install Docker Compose plugin.
- Add deployment user to Docker group.
- Confirm Docker works.

### Step 3 - Deploy Shared Network Foundation

Goal:

- Prepare service-to-service communication between containers and nodes.

Expected actions:

- Decide whether to use Docker Compose on one host first or Docker Swarm later.
- Start with controlled multi-service deployment.
- Keep service names consistent with local configuration when possible.

### Step 4 - Deploy HDFS

Goal:

- Enable distributed bronze storage.

Expected actions:

- Start HDFS NameNode.
- Start HDFS DataNodes.
- Validate HDFS UI.
- Create bronze and warehouse paths.

Expected HDFS paths:

```text
/bronze/client_1
/warehouse
```

### Step 5 - Deploy Hive Metastore

Goal:

- Provide table metadata catalog for Iceberg.

Expected actions:

- Start Hive Metastore metadata database.
- Start Hive Metastore service.
- Validate Hive Metastore connectivity.

### Step 6 - Deploy Spark

Goal:

- Enable distributed processing.

Expected actions:

- Start Spark master.
- Start Spark workers.
- Start Spark History Server.
- Start Spark Thrift Server.
- Validate Spark UI.
- Validate Spark Thrift connectivity.

### Step 7 - Deploy Kafka

Goal:

- Enable ingestion backbone.

Expected actions:

- Start Kafka broker.
- Start Kafka UI.
- Validate topic creation.
- Validate producer/consumer connectivity.

### Step 8 - Deploy Trino

Goal:

- Enable SQL access to Iceberg lakehouse tables.

Expected actions:

- Start Trino coordinator.
- Start Trino workers if configured.
- Configure Iceberg/Hive catalog.
- Validate Trino UI.
- Validate connection from DBeaver.

### Step 9 - Deploy Airflow

Goal:

- Orchestrate the lakehouse pipelines.

Expected actions:

- Start Airflow metadata database.
- Start Airflow webserver.
- Start Airflow scheduler.
- Start Airflow worker components if used.
- Confirm DAG visibility.

### Step 10 - Deploy Monitoring

Goal:

- Observe platform health, pipeline success, and performance.

Expected actions:

- Start Prometheus.
- Start Grafana.
- Start exporters/probes.
- Validate monitoring targets.
- Validate Grafana dashboards.

---

## 8. Expected DAG Execution Order After Deployment

The same validated logical order must be preserved.

| Order | DAG | Purpose |
|---|---|---|
| 1 | `customerdna_client1_lakehouse_setup_pipeline` | Initialize HDFS bronze zone and Iceberg namespaces |
| 2 | `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline` | Source data -> Kafka -> HDFS bronze -> Spark -> Iceberg raw tables |
| 3 | `customerdna_client1_dbt_spark_lakehouse_pipeline` | dbt-spark transformations and tests |
| 4 | `customerdna_client1_lakehouse_readiness_pipeline` | Validate HDFS, Hive Metastore, Spark, Spark Thrift, and Trino services |

This order is important because every layer depends on the previous layer.

---

## 9. Browser Access Points

The final ports may change depending on deployment constraints, but the expected access points are:

| Service | Expected URL |
|---|---|
| Airflow | `http://<machine-ip>:8080` |
| Kafka UI | `http://<machine-ip>:8081` |
| HDFS NameNode | `http://<machine-ip>:9870` |
| Spark Master | `http://<machine-ip>:8086` |
| Spark Worker | `http://<machine-ip>:8087` |
| Spark History Server | `http://<machine-ip>:18080` |
| Spark Thrift UI | `http://<machine-ip>:4040` |
| Trino | `http://<machine-ip>:8088` |
| Prometheus | `http://<machine-ip>:9090` |
| Grafana | `http://<machine-ip>:3001` |

Only expose the services that are needed for project testing and demonstration.

---

## 10. DBeaver Connection Plan

Use DBeaver to connect to Trino.

Expected connection:

| Field | Value |
|---|---|
| Driver | Trino |
| Host | `<trino-host-ip>` |
| Port | `8088` |
| Catalog | `lakehouse` |
| Username | Any non-empty username if authentication is disabled |
| Password | Empty unless authentication is configured |

Expected schemas after pipeline execution:

- `raw_data`
- `staging`
- `intermediate`
- `analytics`

---

## 11. Benchmark Plan

The deployment must allow comparison between local execution and distributed execution.

### 11.1 Local Baseline

The local machine provides:

- correctness baseline,
- functional validation,
- known successful DAG order,
- known expected row counts,
- known dashboard behavior.

### 11.2 Distributed Deployment Baseline

The distributed environment provides:

- multi-machine HDFS storage,
- multi-worker Spark execution,
- distributed service communication,
- resource usage visibility,
- scalability behavior,
- comparison against local execution.

### 11.3 Metrics to Capture

| Metric | Local | Distributed |
|---|---:|---:|
| Total pipeline duration | To measure | To measure |
| Kafka ingestion duration | To measure | To measure |
| HDFS bronze landing duration | To measure | To measure |
| Spark raw Iceberg build duration | To measure | To measure |
| dbt-spark transformation duration | To measure | To measure |
| Great Expectations validation duration | To measure | To measure |
| Trino query latency | To measure | To measure |
| CPU usage | To measure | To measure |
| RAM usage | To measure | To measure |
| Disk usage | To measure | To measure |
| Failed task count | To measure | To measure |

### 11.4 Fair Comparison Rules

The comparison must use:

- same datasets,
- same DAG order,
- same transformations,
- same quality checks,
- same Trino queries,
- same dashboard refresh logic,
- same measurement method.

The report should explain that small datasets may not always be faster on a distributed cluster because distributed systems add network, coordination, and scheduling overhead. The distributed architecture becomes more valuable as data volume, concurrency, and processing complexity increase.

---

## 12. Rollback Plan

If deployment causes problems, rollback must not affect the local environment.

Rollback rules:

- Keep local machine untouched.
- Keep local Docker volumes untouched.
- Keep local `.env` untouched.
- Keep local validated branch untouched unless intentionally merged.
- Stop only the deployment services on the servers.
- Preserve logs before cleanup.

Recommended rollback evidence to collect:

- Airflow task logs.
- Docker Compose logs.
- Spark application logs.
- HDFS NameNode logs.
- Trino logs.
- Prometheus target health.
- Grafana screenshots.

---

## 13. Deployment Success Criteria

The deployment is successful when:

- all required services start,
- Airflow DAGs are visible,
- HDFS bronze paths exist,
- Kafka topics are created,
- source data lands into HDFS bronze,
- Spark creates Iceberg raw tables,
- dbt-spark creates staging/intermediate/analytics tables,
- Trino can query the lakehouse schemas,
- Great Expectations validations pass,
- Grafana dashboards show useful metrics,
- the full DAG order completes successfully.

---

## 14. Defense Message

The local environment proves that the platform is functionally correct and reproducible.  
The distributed environment proves that the same architecture can scale across several machines by distributing storage through HDFS and distributing processing through Spark.

This makes the project defensible as a Big Data Engineering platform, not only a local data pipeline.

