# AdOptimizer CDP - Updated Project Structure

> Updated on 2026-08-12 after the Client 1 dataset refactor, distributed deployment refactor, and security-layer integration.
> This file focuses on the current active project structure.
> Generated caches, historical logs, compiled artifacts, and transient runtime files are intentionally omitted unless they are part of the engineered design.

---

## 1. Root Layout

### Naming clarification

- **AdOptimizer AI**
  - the global strategic initiative at SMART AUTOMATION TECHNOLOGIES
- **AdOptimizer CDP**
  - the actual PFE project identity and business-facing platform name
- **`CustomerDNA AI/`**
  - the repository folder name kept for continuity in the local workspace

```text
CustomerDNA AI/
|-- datasets/
|-- project_presentation/
|-- project_requirements/
|-- src/
|-- README.md
|-- RUNBOOK_local_Acer.md
`-- tools_port_local_Acer.txt
```

### Structure meaning

- `CustomerDNA AI/`
  - repository root folder name only; the implemented platform identity is AdOptimizer CDP
- `datasets/`
  - active Client 1 source data used by the platform
- `project_presentation/`
  - report and presentation material
- `project_requirements/`
  - business rules and scope truth sources
- `src/`
  - the actual engineering implementation
- `RUNBOOK_local_Acer.md`
  - historical local execution reference
- `tools_port_local_Acer.txt`
  - local service/port reference

---

## 2. Active Dataset Structure

```text
datasets/
`-- client_1/
    |-- README.md
    |-- bank_marketing/
    |   |-- bank-additional-full.csv
    |   `-- bank-additional-names.txt
    |-- online_shoppers_intention/
    |   `-- online_shoppers_intention.csv
    `-- UCI_Online_Retail_2/
        `-- online_retail_2.xlsx
```

### Dataset meaning

- `bank_marketing/`
  - profile, campaign-response, and macro-economic context dataset
- `online_shoppers_intention/`
  - web-session intent and browsing behavior dataset
- `UCI_Online_Retail_2/`
  - transaction and revenue behavior dataset
- `README.md`
  - explains why these are the active Client 1 datasets

---

## 3. Requirements and Report Truth Sources

```text
project_requirements/
|-- BUSINESS_RULES.md
|-- BUSINESS_RULES_PFE_REPORT.md
|-- PRISM_REPORT_MASTER_CONTEXT.md
|-- REPORT_MASTER_ARCHITECTURE_MATRIX.md
`-- initial_project_description.txt
```

### Meaning

- `BUSINESS_RULES.md`
  - engineering scope and operational truth source
- `BUSINESS_RULES_PFE_REPORT.md`
  - jury-facing and report-facing business framing for AdOptimizer CDP under AdOptimizer AI
- `PRISM_REPORT_MASTER_CONTEXT.md`
  - single high-density synthesis file for Prism or other automated report-generation systems
- `REPORT_MASTER_ARCHITECTURE_MATRIX.md`
  - strict structured matrix for Prism parsing, cross-checking, and Draw.io architecture preparation
- `initial_project_description.txt`
  - updated high-level positioning of AdOptimizer CDP within the broader AdOptimizer AI initiative

---

## 4. Source Code Root

```text
src/
|-- README.md
|-- airflow/
|-- catalog/
|-- deployments/
|-- lake/
|-- monitoring/
|-- processing/
|-- quality/
|-- query/
|-- streaming/
`-- transformation/
```

### Meaning

Each folder maps to one platform responsibility:

- orchestration,
- metadata/catalog,
- deployment,
- storage,
- monitoring,
- distributed processing,
- quality,
- querying,
- ingestion,
- transformation.

---

## 5. Airflow Orchestration Layer

```text
src/airflow/
|-- .env
|-- .env.example
|-- docker-compose.yml
|-- requirements.txt
|-- config/
|-- plugins/
|-- dags/
|   `-- client_1/
|       |-- __init__.py
|       |-- client_1_dag_common.py
|       |-- client_1_environment_reset_dag.py
|       |-- client_1_lakehouse_setup_dag.py
|       |-- client_1_lakehouse_readiness_dag.py
|       |-- client_1_kafka_hdfs_spark_raw_dag.py
|       `-- client_1_dbt_spark_transformations_dag.py
`-- logs/
```

### Meaning

- `docker-compose.yml`
  - Airflow service stack definition
- `requirements.txt`
  - Python dependencies needed by Airflow tasks
- `client_1_dag_common.py`
  - shared task helpers and execution wrappers
- `client_1_environment_reset_dag.py`
  - environment reset orchestration
- `client_1_lakehouse_setup_dag.py`
  - namespace and storage setup orchestration
- `client_1_lakehouse_readiness_dag.py`
  - readiness validation orchestration
- `client_1_kafka_hdfs_spark_raw_dag.py`
  - Kafka -> HDFS -> Spark raw lakehouse execution
- `client_1_dbt_spark_transformations_dag.py`
  - dbt-spark transformation and testing orchestration

---

## 6. Kafka Ingestion Layer

```text
src/streaming/kafka/
|-- .gitignore
|-- docker-compose.yml
|-- requirements.txt
|-- config/
|-- docker/
|-- logs/
`-- client_1/
    |-- __init__.py
    |-- reset_client1_kafka.py
    |-- reset_single_dataset_state.py
    |-- run_client1_kafka_raw_pipeline.py
    |-- topic_admin/
    |-- bronze_writers/
    |-- common/
    |   |-- __init__.py
    |   |-- bronze_consumer.py
    |   |-- dataset_producer.py
    |   |-- kafka_config.py
    |   |-- load_event_consumer.py
    |   |-- producer_utils.py
    |   `-- source_row_iterators.py
    |-- bank_marketing/
    |   |-- __init__.py
    |   |-- produce.py
    |   |-- consume.py
    |   `-- load.py
    |-- online_shoppers_intention/
    |   |-- __init__.py
    |   |-- produce.py
    |   |-- consume.py
    |   `-- load.py
    `-- online_retail_2/
        |-- __init__.py
        |-- produce.py
        |-- consume.py
        `-- load.py
```

### Meaning

- `run_client1_kafka_raw_pipeline.py`
  - master ingestion runner for all active Client 1 datasets
- `reset_client1_kafka.py`
  - resets Kafka topics and ingestion state
- `common/`
  - reusable ingestion logic
- dataset folders
  - source-specific produce/consume/load logic for each active dataset

---

## 7. HDFS Storage Layer

```text
src/lake/hdfs/
|-- docker-compose.yml
`-- client_1/
    |-- .gitignore
    |-- initialize_client1_bronze_zone.py
    |-- list_client1_bronze_objects.py
    |-- reset_client1_bronze.py
    |-- bronze/
    |-- silver/
    |-- gold/
    `-- common/
        |-- hdfs_bronze_config.py
        `-- hdfs_bronze_utils.py
```

### Meaning

- `initialize_client1_bronze_zone.py`
  - creates the Client 1 HDFS bronze layout
- `list_client1_bronze_objects.py`
  - inspection helper for landed bronze objects
- `reset_client1_bronze.py`
  - reset helper for raw storage state
- `bronze/`, `silver/`, `gold/`
  - logical zone placeholders used to explain storage layering

---

## 8. Spark Processing Layer

```text
src/processing/spark/
|-- .env
|-- .env.example
|-- docker-compose.yml
|-- Dockerfile
|-- README.md
|-- conf/
|-- config/
|   |-- hive-site.xml
|   `-- spark-defaults.conf
|-- jobs/
|   `-- client_1/
|       `-- load_hdfs_bronze_to_iceberg.py
`-- client_1/
    |-- bronze_to_silver/
    |-- silver_to_gold/
    |-- quality_helpers/
    |-- schemas/
    |-- sql/
    `-- common/
        `-- spark_raw_loader_submitter.py
```

### Meaning

- `Dockerfile`
  - Spark execution image definition
- `load_hdfs_bronze_to_iceberg.py`
  - main Spark raw loading job
- `spark_raw_loader_submitter.py`
  - controlled Spark submission helper
- `config/`
  - Spark/Hive config used by processing services

---

## 9. Hive Metastore and Catalog Layer

```text
src/catalog/hive/
|-- .env.example
|-- docker-compose.yml
|-- README.md
|-- config/
|   |-- core-site.xml
|   |-- hdfs-site.xml
|   `-- hive-site.xml
|-- metastore/
|   `-- Dockerfile
`-- client_1/
    |-- external_tables/
    |-- iceberg_catalog/
    `-- namespaces/
```

### Meaning

- `docker-compose.yml`
  - Hive Metastore service stack
- `config/`
  - shared HDFS/Hive metadata configuration
- `metastore/Dockerfile`
  - metastore container image definition
- `client_1/`
  - catalog organization for Client 1 lakehouse objects

---

## 10. Trino Query Layer

```text
src/query/trino/
|-- .env.example
|-- docker-compose.yml
|-- README.md
|-- etc/
|   |-- config.properties
|   |-- core-site.xml
|   |-- hdfs-site.xml
|   |-- jvm.config
|   |-- node.properties
|   `-- catalog/
|       `-- lakehouse.properties
`-- client_1/
    |-- initialize_lakehouse_namespace.py
    |-- reset_lakehouse_namespaces.py
    `-- common/
        `-- trino_rest.py
```

### Meaning

- `lakehouse.properties`
  - Trino connector definition for the lakehouse
- `initialize_lakehouse_namespace.py`
  - namespace bootstrap through Trino
- `reset_lakehouse_namespaces.py`
  - namespace cleanup/reset helper
- `trino_rest.py`
  - reusable Trino REST helper

---

## 11. dbt-spark Transformation Layer

```text
src/transformation/dbt_spark/
`-- client_1/
    |-- .env.example
    |-- .user.yml
    |-- dbt_project.yml
    |-- profiles.yml
    |-- README.md
    |-- requirements.txt
    |-- logs/
    |-- target/
    |-- macros/
    |   |-- lakehouse_schema_management.sql
    |   `-- safe_casts.sql
    `-- models/
        |-- staging/
        |   |-- sources.yml
        |   |-- schema.yml
        |   |-- stg_bank_marketing.sql
        |   |-- stg_online_shoppers_intention.sql
        |   `-- stg_online_retail_2.sql
        |-- intermediate/
        |   |-- schema.yml
        |   |-- int_bank_marketing_contacts.sql
        |   |-- int_online_shopper_sessions.sql
        |   |-- int_online_retail_customer_sales.sql
        |   `-- int_customer_360_feature_store.sql
        `-- analytics/
            |-- schema.yml
            |-- analytics_customer360_overview.sql
            |-- analytics_conversion_performance.sql
            `-- analytics_sales_performance.sql
```

### Meaning

- `dbt_project.yml`
  - dbt project definition
- `profiles.yml`
  - Spark/Thrift profile configuration
- `macros/`
  - reusable SQL helpers
- `staging/`
  - source standardization
- `intermediate/`
  - domain combination and feature-engineering preparation
- `analytics/`
  - report-facing analytical outputs

---

## 12. Great Expectations Quality Layer

```text
src/quality/great_expectations/
`-- client_1/
    |-- bootstrap_gx.py
    |-- run_gx_validations.py
    |-- artifacts/
    |-- checkpoints/
    |-- data_docs/
    |-- expectations/
    |   |-- bronze/
    |   |-- silver/
    |   `-- gold/
    `-- gx_project/
        `-- gx/
            |-- .gitignore
            |-- great_expectations.yml
            |-- checkpoints/
            |-- expectations/
            |-- plugins/
            |-- validation_definitions/
            |   |-- raw_lakehouse_quality_checkpoint__bank_marketing.json
            |   |-- raw_lakehouse_quality_checkpoint__online_shoppers_intention.json
            |   `-- raw_lakehouse_quality_checkpoint__online_retail_2.json
            `-- uncommitted/
                |-- data_docs/
                `-- validations/
```

### Meaning

- `bootstrap_gx.py`
  - builds or refreshes the GX project structure
- `run_gx_validations.py`
  - executes validations and generates evidence
- `data_docs/`
  - HTML Data Docs output
- `validation_definitions/`
  - active raw-lakehouse validation contracts

---

## 13. Monitoring and Observability Layer

```text
src/monitoring/
|-- README.md
|-- exporters/
|   |-- pipeline_metrics_exporter.py
|   |-- hdfs_metrics/
|   |-- spark_metrics/
|   `-- pipeline_metrics/
|-- grafana/
|   |-- .env.example
|   |-- docker-compose.yml
|   |-- dashboards/
|   |   |-- customerdna_infrastructure.dashboard.json
|   |   |-- customerdna_pipeline_health.dashboard.json
|   |   |-- customerdna_postgres.dashboard.json
|   |   `-- README.md
|   `-- provisioning/
|       |-- dashboards/
|       |   `-- customerdna.yml
|       `-- datasources/
|           `-- prometheus.yml
|-- prometheus/
|   |-- .env
|   |-- .env.example
|   |-- docker-compose.yml
|   |-- prometheus.yml
|   `-- README.md
|-- shared/
|   |-- __init__.py
|   `-- pipeline_metrics.py
|-- state/
|   `-- .gitkeep
`-- tools/
    `-- export_runtime_logs.py
```

### Meaning

- `pipeline_metrics_exporter.py`
  - exposes pipeline status metrics
- `prometheus.yml`
  - metrics scraping configuration
- Grafana dashboards
  - infrastructure, pipeline-health, and metastore visibility
- `state/`
  - persistent monitoring state location

---

## 14. Distributed Deployment Layer

```text
src/deployments/
`-- distributed_pc_control_plane/
    |-- README.md
    |-- CLUSTER_ACCESS_POINTS.txt
    |-- shared/
    |   |-- README.md
    |   |-- configs/
    |   |   |-- cluster_inventory.yml
    |   |   |-- deployment_contract.yml
    |   |   |-- ports_map.yml
    |   |   |-- service_placement.yml
    |   |   `-- README.md
    |   |-- env/
    |   |   |-- cluster.shared.env.example
    |   |   |-- control_plane_pc.env.example
    |   |   |-- vm.common.env.example
    |   |   `-- README.md
    |   `-- scripts/
    |       |-- cluster_preflight_checks.ps1
    |       |-- cluster_preflight_checks.sh
    |       `-- README.md
    |-- control_plane_pc/
    |   |-- .env
    |   |-- .env.example
    |   |-- .gitignore
    |   |-- docker-compose.yml
    |   |-- control_plane_preflight_checks.ps1
    |   |-- start_control_plane_pc.ps1
    |   |-- reset_control_plane_state.ps1
    |   |-- README.md
    |   |-- airflow/
    |   |-- grafana/
    |   |-- monitoring/
    |   |-- quality/
    |   |-- spark_submit_client/
    |   |-- ssh/
    |   |-- transformation/
    |   `-- runtime/
    |-- vm1/
    |   |-- .env
    |   |-- .env.example
    |   |-- .gitignore
    |   |-- docker-compose.yml
    |   |-- manage_vm1_bundle.py
    |   |-- prepare_fresh_vm1.sh
    |   |-- vm1_preflight_checks.sh
    |   |-- start_vm1_stack.sh
    |   |-- reset_vm1_state.sh
    |   |-- VM_config.txt
    |   |-- hdfs/
    |   |-- kafka/
    |   |-- spark/
    |   |-- trino/
    |   `-- exporters/
    |-- vm2/
    |   |-- .env
    |   |-- .env.example
    |   |-- .gitignore
    |   |-- docker-compose.yml
    |   |-- manage_vm2_bundle.py
    |   |-- prepare_fresh_vm2.sh
    |   |-- vm2_preflight_checks.sh
    |   |-- start_vm2_stack.sh
    |   |-- reset_vm2_state.sh
    |   |-- VM_config.txt
    |   |-- app/
    |   |-- hdfs/
    |   |-- hive/
    |   |-- kafka/
    |   |-- spark/
    |   |-- trino/
    |   `-- exporters/
    `-- vm3/
        |-- .env
        |-- .env.example
        |-- .gitignore
        |-- docker-compose.yml
        |-- manage_vm3_bundle.py
        |-- prepare_fresh_vm3.sh
        |-- vm3_preflight_checks.sh
        |-- start_vm3_stack.sh
        |-- reset_vm3_state.sh
        |-- VM_config.txt
        |-- hdfs/
        |-- kafka/
        |-- spark/
        |-- trino/
        `-- exporters/
```

### Meaning

- `shared/`
  - shared distributed deployment contract, env templates, and cluster rules
- `control_plane_pc/`
  - local orchestration and supervision deployment
- `vm1/`
  - worker-side distributed bundle for broker/datanode/spark worker/trino worker
- `vm2/`
  - leader-side distributed bundle for namenode/metastore/spark master/thrift/trino coordinator
- `vm3/`
  - additional worker-side distributed bundle
- `manage_vm*.py`
  - bundle build/upload automation scripts

---

## 15. Architectural Reading Rule

The correct way to read this repository is:

1. `datasets/`
2. `project_requirements/`
3. `src/streaming/kafka/`
4. `src/lake/hdfs/`
5. `src/processing/spark/`
6. `src/catalog/hive/`
7. `src/query/trino/`
8. `src/transformation/dbt_spark/`
9. `src/quality/great_expectations/`
10. `src/airflow/`
11. `src/monitoring/`
12. `src/deployments/distributed_pc_control_plane/`

This order follows the actual system lifecycle:

source -> ingest -> store -> process -> catalog -> query -> transform -> validate -> orchestrate -> monitor -> deploy

---

## 16. Important Interpretation Rule

This structure is intentionally layered.

Nothing major is placed arbitrarily.

Every main folder corresponds to a real engineering responsibility in the distributed customer-data platform.

That is exactly why the repository is defensible in a jury context:

- the architecture is visible in the codebase,
- the deployment is visible in the codebase,
- the quality layer is visible in the codebase,
- and the final system is explainable end to end.
