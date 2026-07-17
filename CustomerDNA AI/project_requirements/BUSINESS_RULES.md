# AdOptimizer Customer Data Platform - Business Rules & Project Specification

> **Global Project Document** | Version 17.1
> Status: Distributed lakehouse architecture operational for Client 1 with Kafka, HDFS, Spark, Hive Metastore, Iceberg, Trino, dbt-spark, Airflow, Great Expectations, Prometheus, and Grafana
> Last Updated: 2026-07-16

---

## 1. Document Purpose

This document is the main business-rules and technical-specification reference for the implemented customer-data platform delivered inside the broader **AdOptimizer AI** initiative.

It defines:

- the business problem being solved,
- the target architecture and engineering standards,
- the role of each technology in the platform,
- the rules governing ingestion, storage, processing, querying, validation, orchestration, and monitoring,
- the current Client 1 scope,
- the expected evolution path of the platform.

This document is the **global architectural truth** of the project.

---

## 2. Project Identity

### 2.1 Official Project Name
**AdOptimizer Customer Data Platform**

### 2.2 Relationship to AdOptimizer AI
The platform must be understood as the **data-engineering foundation** of the broader **AdOptimizer AI** program.

In this relationship:

- **AdOptimizer AI** is the umbrella business and intelligent-platform vision.
- **AdOptimizer Customer Data Platform** is the implemented data platform responsible for collecting, standardizing, governing, storing, and exposing customer-related data products.
- analytics and future AI/ML capabilities depend on this platform, but they are not the primary identity of the current implementation.

### 2.3 Core Positioning
The platform is positioned first as a **Data Engineering and Distributed Data Platform**.

It is not to be presented primarily as:

- a machine-learning project,
- a dashboarding project,
- a standalone BI project,
- or a simple ETL script collection.

### 2.4 Architectural Identity
The platform is now designed as a **distributed lakehouse-oriented architecture** based on:

- **Kafka** for ingestion transport and event streaming,
- **HDFS** for bronze-layer distributed storage,
- **Spark** for distributed processing,
- **Hive Metastore** for metadata and table catalog management,
- **Apache Iceberg** as the managed analytical table format,
- **Trino** for SQL query access over the lakehouse,
- **dbt-spark** for transformation modeling over Iceberg-backed lakehouse tables,
- **Airflow** for orchestration,
- **Great Expectations** for data-quality validation,
- **Prometheus + Grafana** for monitoring and observability.

### 2.5 Deployment Orientation
The platform must remain:

- runnable in development,
- portable to Docker-based environments,
- explainable for deployment on a company-owned server cluster,
- scalable toward multi-node execution later.

---

## 3. Problem Statement

Customer-related data is commonly fragmented across multiple heterogeneous sources, formats, and business perspectives.

Typical operational problems include:

1. **Fragmented source landscape**
   - customer, transaction, event, and campaign data arrive from different files and structures.

2. **Weak ingestion discipline**
   - data loading may rely on manual or tightly coupled scripts that are difficult to replay and audit.

3. **Poor separation of responsibilities**
   - ingestion, storage, transformation, validation, and monitoring are often mixed together.

4. **Low trust in downstream outputs**
   - data may be used in analytics or future intelligent applications without explicit validation or observability.

5. **Limited scalability**
   - architectures built around one local database or one direct script often become hard to scale, explain, or distribute.

The project therefore addresses the following question:

> How can we build a distributed customer-data engineering platform that ingests heterogeneous datasets, persists them in a bronze data lake, processes them through a scalable lakehouse architecture, validates data quality, orchestrates the complete flow, and exposes trusted analytical outputs for downstream consumption within the broader AdOptimizer AI vision?

---

## 4. Proposed Solution

The proposed solution is a **distributed batch-oriented lakehouse platform** with the following high-level flow:

```text
Client source datasets
  -> Kafka producers
  -> Kafka topics
  -> bronze consumers
  -> HDFS bronze storage
  -> Spark processing
  -> Iceberg tables registered in Hive Metastore
  -> Trino SQL access
  -> dbt-spark transformations
  -> Great Expectations validation
  -> Airflow orchestration
  -> Prometheus + Grafana monitoring
  -> downstream analytics / BI / future intelligent consumers
```

This design is chosen because it provides:

- clear separation of concerns,
- distributed storage and compute,
- replayable ingestion,
- table-format governance,
- SQL accessibility,
- orchestration and observability,
- future extensibility toward more clients and more use cases.

### 4.1 Current Executable Runtime Sequence

The implemented platform must also be explained through its concrete operational sequence:

1. `customerdna_client1_lakehouse_setup_pipeline`
2. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
3. `customerdna_client1_dbt_spark_lakehouse_pipeline`
4. `customerdna_client1_lakehouse_readiness_pipeline`

In practical terms, the executed runtime flow is:

```text
initialize HDFS bronze + Hive/Iceberg namespaces + Trino validation
  -> stream source datasets through Kafka
  -> persist bronze files in HDFS
  -> process bronze data with Spark
  -> write raw Iceberg tables and register them in Hive Metastore
  -> run dbt-spark staging/intermediate/analytics models over the lakehouse
  -> expose SQL access through Trino
  -> validate raw and transformed lakehouse quality through Great Expectations
  -> monitor infrastructure and pipeline health with Prometheus + Grafana
```

The report and oral defense must describe the platform according to this real executed sequence rather than according to any previous local warehouse-oriented iteration.

---

## 5. Strategic Objectives

### 5.1 Immediate Objectives

- build a stable Client 1 distributed customer-data platform,
- integrate multi-source datasets through a unified ingestion backbone,
- make Kafka the official source-ingestion layer,
- make HDFS the official bronze landing layer,
- make Spark the official distributed processing layer,
- make Hive Metastore + Iceberg the official structured lakehouse layer,
- make Trino the official SQL query layer,
- make dbt-spark the official transformation modeling layer for curated lakehouse outputs,
- validate platform outputs with Great Expectations,
- orchestrate the platform with Airflow,
- monitor the platform with Prometheus and Grafana.

### 5.2 Medium-Term Objectives

- onboard additional datasets and future clients,
- improve partitioning and performance tuning,
- add stronger DataSecOps and governance controls,
- expose curated outputs to downstream analytics and future applications.

### 5.3 Long-Term Objectives

- evolve toward a reusable multi-client customer data platform,
- support broader AdOptimizer AI workloads,
- scale from local development to server deployment and then to multi-node execution.

---

## 6. Scope and Non-Goals

### 6.1 In Scope

- Client 1 source dataset organization,
- Kafka ingestion and event transport,
- HDFS bronze persistence,
- Spark processing jobs,
- Hive Metastore integration,
- Iceberg table management,
- Trino SQL access,
- dbt-spark transformation project and model execution,
- Airflow pipeline orchestration,
- Great Expectations validation,
- Prometheus and Grafana monitoring,
- architecture documentation and deployment readiness.

### 6.2 Out of Scope for the Core Platform Identity

- full enterprise AI/ML lifecycle automation,
- production model serving,
- real-time decision APIs,
- cloud-provider-specific managed services,
- fine-grained enterprise IAM/governance products.

### 6.3 Architectural Non-Goals

The platform must avoid:

- using a traditional PostgreSQL business warehouse as the core analytical storage layer,
- mixing bronze persistence with business transformations,
- bypassing distributed storage and compute once the lakehouse direction is adopted,
- hiding validation behind undocumented scripts,
- exposing raw engineering layers directly to business consumers.

---

## 7. Stakeholders

### 7.1 Primary Technical Stakeholder
- the project owner delivering the PFE with a strong Data Engineering orientation

### 7.2 Business Stakeholders
- managers,
- analysts,
- reporting consumers,
- future business application stakeholders.

### 7.3 Technical Stakeholders
- data engineers,
- analytics engineers,
- platform engineers,
- DevOps / DataSecOps stakeholders,
- future data scientists and ML engineers.

---

## 8. Source Data Landscape

### 8.1 Client 1 Active Source Groups

Client 1 currently uses four heterogeneous source groups:

| Dataset Group | Business Meaning |
|---|---|
| Customer Personality Analysis | demographics, spending patterns, campaign response |
| E-commerce Customer Churn | churn behavior and usage indicators |
| RetailRocket Dataset | behavioral events, item properties, category structure |
| UCI Online Retail II | transaction and sales behavior |

### 8.2 Active Source Files

- `datasets/client_1/Customer_Personality_Analysis/marketing_campaign.csv`
- `datasets/client_1/E-commerce_customer_churn/E-commerce_customer_churn.xlsx`
- `datasets/client_1/Retailrocket_recommender_system_dataset/category_tree.csv`
- `datasets/client_1/Retailrocket_recommender_system_dataset/events.csv`
- `datasets/client_1/Retailrocket_recommender_system_dataset/item_properties_part1.csv`
- `datasets/client_1/Retailrocket_recommender_system_dataset/item_properties_part2.csv`
- `datasets/client_1/UCI_Online_Retail_2/online_retail_2.xlsx`

### 8.3 Source Interpretation Rule

The datasets represent heterogeneous but related business perspectives.

Therefore:

- source identity must be preserved,
- ingestion must remain dataset-aware,
- reconciliation or integration logic must be explicit,
- downstream curated products must document their transformation assumptions.

---

## 9. Core Architecture Rules

### 9.1 Kafka Rule
Kafka is the official ingestion and event transport backbone.

Kafka is responsible for:

- receiving source-derived records,
- decoupling producers from downstream processors,
- organizing per-dataset streams via topics,
- enabling replay and observability at the transport layer.

Kafka must not be used as the long-term storage layer.

### 9.2 HDFS Rule
HDFS is the official **bronze distributed storage layer**.

HDFS is responsible for:

- persisting bronze batches,
- keeping replayable ingestion artifacts,
- separating transport from processing,
- providing distributed storage for later Spark jobs.

### 9.3 Spark Rule
Spark is the official **distributed processing engine**.

Spark is responsible for:

- reading bronze data from HDFS,
- applying scalable data processing logic,
- writing structured outputs into Iceberg tables,
- supporting future performance scaling across multiple workers.

### 9.4 Hive Metastore Rule
Hive Metastore is the official metadata and catalog service for lakehouse tables.

It is responsible for:

- table registration,
- schema visibility,
- namespace management,
- interoperability with Spark and Trino.

### 9.5 Iceberg Rule
Iceberg is the official analytical table format.

It is responsible for:

- structured table management over data-lake storage,
- snapshot-based table evolution,
- schema evolution support,
- partition management,
- reliable table semantics for large-scale analytical processing.

### 9.6 Trino Rule
Trino is the official SQL query and analytical access layer.

It is responsible for:

- interactive SQL querying,
- inspection of Iceberg tables,
- lakehouse consumption for analytics,
- future BI connectivity.

### 9.7 dbt-spark Rule
dbt-spark is the official transformation-modeling layer for the curated lakehouse.

It must be used to:

- define staging, intermediate, and analytics transformations as versioned models,
- keep transformation logic modular, auditable, and explainable,
- separate business modeling from low-level ingestion and Spark raw-loading code,
- materialize governed analytical tables on top of Iceberg-backed lakehouse data.

### 9.8 Great Expectations Rule
Great Expectations is the official quality-validation framework.

It must validate:

- bronze and processed data assumptions where relevant,
- table-level quality contracts,
- structural readiness before downstream reuse.

### 9.9 Airflow Rule
Airflow is the official orchestration layer.

Airflow is responsible for:

- workflow decomposition,
- dependency control,
- rerun management,
- operational scheduling and traceability.

### 9.10 Monitoring Rule
Prometheus and Grafana are mandatory platform components.

Monitoring must provide visibility into:

- infrastructure health,
- storage services,
- processing services,
- orchestration status,
- pipeline execution metrics.

---

## 10. Target Layered Flow

### 10.1 Logical Flow

```text
Sources
  -> Kafka transport layer
  -> HDFS bronze layer
  -> Spark distributed processing
  -> Hive Metastore + Iceberg raw tables
  -> dbt-spark transformation layer
  -> Trino analytical access
  -> validated downstream outputs
```

### 10.2 Layer Responsibility Rule

Each layer must keep its own responsibility:

- **source layer**: input ownership
- **Kafka**: transport and decoupling
- **HDFS bronze**: raw distributed persistence
- **Spark**: processing and writing
- **Iceberg raw**: structured raw analytical persistence
- **dbt-spark**: governed transformation modeling
- **Iceberg**: table management
- **Hive**: catalog
- **Trino**: query access
- **GX**: validation
- **Airflow**: orchestration
- **Prometheus/Grafana**: observability

---

## 11. Client 1 Topic and Dataset Rules

### 11.1 Dataset-Specific Topic Pattern
Client 1 topics must follow:

- `client1.marketing_campaign`
- `client1.ecommerce_customer_churn`
- `client1.retailrocket_category_tree`
- `client1.retailrocket_events`
- `client1.retailrocket_item_properties`
- `client1.online_retail`

### 11.2 Bronze Persistence Rule
Each ingestion run must create dataset-specific bronze artifacts in HDFS under a client-aware structure.

### 11.3 Processing Rule
Spark jobs must process bronze inputs deterministically and load them into registered Iceberg tables without silent row loss.

### 11.4 Verification Rule
Each dataset pipeline must be verifiable through:

- source count,
- Kafka publish confirmation,
- bronze write confirmation,
- Spark processing success,
- final table row verification,
- monitoring signals.

---

## 12. Lakehouse Design Rules

### 12.1 Core Table Organization
The platform should organize lakehouse data into business-relevant namespaces and layers, for example:

- `bronze`
- `silver`
- `gold`

or, if a domain-first organization is preferred:

- `client1_bronze`
- `client1_silver`
- `client1_gold`

### 12.2 Bronze Rule
Bronze tables or files preserve ingested source records with minimal interpretation.

### 12.3 Silver Rule
Silver tables standardize, clean, and reconcile source records into reusable structured assets.

### 12.4 Gold Rule
Gold tables expose trusted analytical outputs ready for reporting, downstream consumption, and future intelligent applications.

### 12.5 Query Boundary Rule
Business and analytical consumers must query curated Iceberg tables through Trino rather than reading bronze artifacts directly.

---

## 13. Orchestration Design Rules

### 13.1 Four-Phase Orchestration Principle
The platform should remain decomposed into clear orchestration phases:

1. **Foundation / environment setup**
2. **Bronze ingestion and processing**
3. **dbt-spark transformation and curation**
4. **Lakehouse readiness and quality validation**

This decomposition is implemented concretely through the following DAGs:

1. `customerdna_client1_lakehouse_setup_pipeline`
2. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
3. `customerdna_client1_dbt_spark_lakehouse_pipeline`
4. `customerdna_client1_lakehouse_readiness_pipeline`

### 13.2 Orchestration Benefit Rule
This split is intentional because it improves:

- restartability,
- troubleshooting,
- partial reruns,
- operational readability during the defense,
- production deployment readiness.

---

## 14. Monitoring and Observability Rules

### 14.1 Active Monitoring Components

- Prometheus
- Grafana
- cAdvisor
- Kafka/HDFS/Spark/Hive/Trino operational metrics where available
- custom pipeline metrics exporter

### 14.2 Dashboard Expectations
The monitoring layer should expose at least:

- infrastructure dashboard,
- lakehouse services dashboard,
- pipeline-health dashboard,
- PostgreSQL support-services dashboard where relevant,
- query-platform dashboard.

### 14.3 Monitoring Principle
Monitoring is a first-class platform capability, not a presentation extra.

It exists to prove that the system is:

- observable,
- measurable,
- debuggable,
- explainable to operational stakeholders.

---

## 15. Project Structure Rule

The active project structure must reflect the distributed lakehouse architecture clearly.

The project structure must remain readable from the top business level down to the operational file level.

The active structure must be understood as follows:

```text
CustomerDNA AI/
  Architectural Diagrams/
  datasets/
    client_1/
      Customer_Personality_Analysis/
        marketing_campaign.csv
      E-commerce_customer_churn/
        E-commerce_customer_churn.xlsx
      Retailrocket_recommender_system_dataset/
        category_tree.csv
        events.csv
        item_properties_part1.csv
        item_properties_part2.csv
      UCI_Online_Retail_2/
        online_retail_2.xlsx
    client_2/
      database.sqlite
      Reviews.csv
  project_presentation/
    PFE_presentation/
    PFE_Report/
      main.tex
      README.md
    PFE_resources/
      Figures/
      Logos/
        company_image.png
        School_image.png
        University_image.png
  project_requirements/
    BUSINESS_RULES.md
    BUSINESS_RULES_PFE_REPORT.md
    initial_project_description.txt
  Resources_by_azmani/
  src/
    README.md
    SECURITY_AND_DATASECOPS_GUIDE.md
    airflow/
      .env
      .env.example
      docker-compose.yml
      requirements.txt
      dags/
        client_1/
          __init__.py
          client_1_dag_common.py
          client_1_lakehouse_setup_dag.py
          client_1_kafka_hdfs_spark_raw_dag.py
          client_1_dbt_spark_transformations_dag.py
          client_1_lakehouse_readiness_dag.py
    catalog/
      hive/
        .env.example
        docker-compose.yml
        README.md
        config/
          core-site.xml
          hdfs-site.xml
          hive-site.xml
        metastore/
          Dockerfile
        client_1/
          external_tables/
          iceberg_catalog/
          namespaces/
    lake/
      hdfs/
        .env
        .env.example
        docker-compose.yml
        README.md
        client_1/
          initialize_client1_bronze_zone.py
          list_client1_bronze_objects.py
          reset_client1_bronze.py
          bronze/
            ecommerce_customer_churn/
            marketing_campaign/
            online_retail/
            retailrocket_category_tree/
            retailrocket_events/
            retailrocket_item_properties/
          silver/
          gold/
          common/
            hdfs_bronze_config.py
            hdfs_bronze_utils.py
    monitoring/
      README.md
      exporters/
        pipeline_metrics_exporter.py
        pipeline_metrics/
        hdfs_metrics/
        spark_metrics/
      grafana/
        .env.example
        docker-compose.yml
        dashboards/
          customerdna_infrastructure.dashboard.json
          customerdna_pipeline_health.dashboard.json
          customerdna_postgres.dashboard.json
          README.md
        provisioning/
          dashboards/
            customerdna.yml
          datasources/
            prometheus.yml
      prometheus/
        .env
        .env.example
        docker-compose.yml
        prometheus.yml
        README.md
      shared/
        pipeline_metrics.py
      state/
        airflow_pipeline_state.json
        gx_state.json
        raw_load_state.json
      tools/
        export_runtime_logs.py
    processing/
      spark/
        .env
        .env.example
        docker-compose.yml
        Dockerfile
        README.md
        config/
          hive-site.xml
          spark-defaults.conf
        jobs/
          client_1/
            load_hdfs_bronze_to_iceberg.py
        client_1/
          bronze_to_silver/
          silver_to_gold/
          quality_helpers/
          schemas/
          sql/
          common/
            spark_raw_loader_submitter.py
    quality/
      great_expectations/
        client_1/
          bootstrap_gx.py
          run_gx_validations.py
          checkpoints/
          expectations/
            bronze/
            silver/
            gold/
          data_docs/
            index.html
          artifacts/
    query/
      trino/
        .env.example
        docker-compose.yml
        README.md
        etc/
          config.properties
          core-site.xml
          hdfs-site.xml
          jvm.config
          node.properties
          catalog/
            lakehouse.properties
        client_1/
          initialize_lakehouse_namespace.py
          common/
            trino_rest.py
    streaming/
      kafka/
        .gitignore
        docker-compose.yml
        requirements.txt
        client_1/
          reset_client1_kafka.py
          run_client1_kafka_raw_pipeline.py
          common/
            bronze_consumer.py
            dataset_producer.py
            kafka_config.py
            load_event_consumer.py
            producer_utils.py
            source_row_iterators.py
          ecommerce_customer_churn/
            __init__.py
            produce.py
            consume.py
            load.py
          marketing_campaign/
            __init__.py
            produce.py
            consume.py
            load.py
          online_retail/
            __init__.py
            produce.py
            consume.py
            load.py
          retailrocket_category_tree/
            __init__.py
            produce.py
            consume.py
            load.py
          retailrocket_events/
            __init__.py
            produce.py
            consume.py
            load.py
          retailrocket_item_properties/
            __init__.py
            produce.py
            consume.py
            load.py
    transformation/
      dbt_spark/
        README.md
        client_1/
          .env.example
          .user.yml
          dbt_project.yml
          profiles.yml
          requirements.txt
          macros/
            lakehouse_schema_management.sql
            safe_casts.sql
          models/
            staging/
            intermediate/
            analytics/
          dbt_packages/
          logs/
          target/
  verify_installations/
  README.md
  tools_port.txt
```

The project must no longer keep a traditional PostgreSQL business-warehouse layer as the core analytical storage design.

PostgreSQL may exist only as:

- a metadata backend service for Hive Metastore,
- an Airflow metadata support component,
- or another infrastructure support component,
- but not as the main client analytical warehouse.

---

## 16. Current Shift Rule

The project is undergoing a **strategic architectural shift**:

- from a PostgreSQL warehouse-centric design,
- toward a distributed **HDFS + Spark + Hive + Iceberg + Trino** lakehouse design.

This shift is justified because it better supports:

- distributed storage,
- distributed processing,
- stronger Big Data positioning,
- cleaner lakehouse semantics,
- better alignment with jury expectations for a modern Big Data engineering platform.

---

## 17. PFE Positioning Rule

For the defense, the platform must be presented in the following order:

1. business context inside AdOptimizer AI
2. multi-source customer data challenge
3. ingestion backbone with Kafka
4. bronze persistence in HDFS
5. distributed processing in Spark
6. catalog and table governance through Hive + Iceberg
7. transformation governance through dbt-spark
8. SQL query access through Trino
9. validation with Great Expectations
10. orchestration with Airflow
11. observability with Prometheus and Grafana

This is the correct narrative order for the project.

---

## 18. Final Business Rules Summary

1. **Kafka is the official ingestion transport layer.**
2. **HDFS is the official bronze distributed storage layer.**
3. **Spark is the official distributed processing layer.**
4. **Hive Metastore is the official metadata catalog.**
5. **Iceberg is the official analytical table format.**
6. **Trino is the official SQL access layer.**
7. **dbt-spark is the official transformation-modeling layer for curated lakehouse outputs.**
8. **Great Expectations is the official quality-validation layer.**
9. **Airflow is the official orchestration layer.**
10. **Prometheus and Grafana are mandatory observability components.**
11. **Traditional PostgreSQL business-warehouse logic is no longer the target architecture.**
12. **The platform must be presented primarily as a distributed Data Engineering platform under AdOptimizer AI.**

---

## 19. Document History

| Version | Date | Change |
|---|---|---|
| 16.2 | 2026-07-14 | Previous version aligned to Kafka -> HDFS -> Spark -> PostgreSQL raw flow. |
| 17.0 | 2026-07-15 | Rewritten to reflect the architecture shift toward Kafka + HDFS + Spark + Hive Metastore + Iceberg + Trino as the target distributed lakehouse platform. |
| 17.1 | 2026-07-16 | Updated to reflect the operational 4-DAG runtime, the dbt-spark transformation layer, the current monitoring stack, and the detailed live project structure with important files. |
