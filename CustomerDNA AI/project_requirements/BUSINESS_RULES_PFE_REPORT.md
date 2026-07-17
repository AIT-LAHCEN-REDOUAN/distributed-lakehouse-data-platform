# AdOptimizer Customer Data Platform - PFE Data Engineering Business Rules

> **PFE Jury-Focused Document**
> Scope: Data Engineering and Big Data positioning only
> Version: 4.1
> Last Updated: 2026-07-16

---

## 1. Purpose of This Document

This document is the jury-oriented interpretation of the project.

Its role is to explain the platform as a **Data Engineering and Big Data system**, not as an AI-first or BI-first project.

It defines:

- the exact academic positioning of the work,
- the business problem addressed,
- the implemented and target architecture logic,
- the role of each major technology,
- the defense narrative that should be followed during the report and oral presentation.

This file must be considered the **official PFE framing document**.

---

## 2. Official PFE Positioning

### 2.1 Project Name
**AdOptimizer Customer Data Platform**

### 2.2 Position Inside the Broader Vision
The platform is a concrete technical subsystem inside the broader **AdOptimizer AI** initiative.

The broader initiative aims to support future intelligent advertising and customer-centric decisioning.

The present project does **not** claim to implement the entire AdOptimizer AI system.

Instead, it implements the part that is strictly necessary before future intelligence can be trusted:

- data ingestion,
- distributed storage,
- distributed processing,
- structured analytical access,
- validation,
- orchestration,
- observability.

### 2.3 Main Academic Identity
For the PFE, the project must be defended primarily as:

- a **Data Engineering platform**,
- a **Big Data architecture**,
- a **distributed lakehouse-oriented system**,
- a **deployment-oriented technical foundation**.

### 2.4 What It Is Not Primarily
The project must not be defended primarily as:

- a machine-learning project,
- a dashboard-only project,
- a simple ETL automation,
- or a classical single-database warehouse project.

---

## 3. Problem Statement

The business problem is that customer-related data is dispersed across multiple heterogeneous sources.

These sources differ in:

- format,
- semantics,
- structure,
- quality,
- and operational behavior.

Without a strong engineering foundation, this leads to:

- fragmented analytics,
- weak reproducibility,
- poor trust in downstream outputs,
- limited scalability,
- weak readiness for future intelligent applications.

The project therefore answers the following question:

> How can we build a distributed customer-data platform capable of ingesting heterogeneous datasets, storing them in a replayable bronze layer, processing them at scale, exposing structured analytical tables, validating quality, orchestrating execution, and monitoring runtime behavior in a way that is defensible as a modern Big Data Engineering platform?

---

## 4. Final Architecture to Present to the Jury

The final architecture to present is:

```text
Source datasets
  -> Kafka
  -> HDFS bronze
  -> Spark processing
  -> Iceberg tables
  -> Hive Metastore catalog
  -> Trino SQL access
  -> dbt-spark transformations
  -> Great Expectations validation
  -> Airflow orchestration
  -> Prometheus + Grafana monitoring
  -> downstream analytics and future intelligent consumers
```

This is the correct architecture to position in the report.

### 4.1 Executable Pipeline Sequence to Defend

The jury-facing explanation should also mention the real orchestration order used by the implemented platform:

1. `customerdna_client1_lakehouse_setup_pipeline`
2. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
3. `customerdna_client1_dbt_spark_lakehouse_pipeline`
4. `customerdna_client1_lakehouse_readiness_pipeline`

This means the effective runtime chain is:

```text
prepare HDFS bronze and Iceberg/Hive namespaces
  -> ingest source datasets through Kafka
  -> land bronze files in HDFS
  -> process data with Spark and create Iceberg raw tables
  -> run dbt-spark transformations for staging/intermediate/analytics outputs
  -> query them through Trino
  -> validate raw and transformed quality with Great Expectations
  -> supervise the platform through Prometheus and Grafana
```

This concrete sequence is important for the defense because it proves that the architecture is not only conceptual, but actually executed end to end.

---

## 5. Why This Architecture Is Strong for the PFE

This architecture is strong for a jury defense because it demonstrates all of the following:

- heterogeneous source integration,
- event-driven ingestion,
- distributed storage,
- distributed processing,
- modern table-format management,
- SQL-based analytical access,
- transformation governance through versioned models,
- automated orchestration,
- quality governance,
- observability,
- deployment readiness.

It is therefore much more defensible as a Big Data Engineering project than a design centered on one traditional warehouse database alone.

---

## 6. Role of Each Main Technology

### 6.1 Kafka
Kafka is the ingestion transport and event-streaming backbone.

It is responsible for:

- transporting dataset records,
- decoupling producers from consumers,
- organizing ingestion by topics,
- enabling replay and transport-level observability.

### 6.2 HDFS
HDFS is the bronze distributed storage layer.

It is responsible for:

- preserving landed ingestion batches,
- enabling replayability,
- supporting distributed storage,
- separating source transport from downstream processing.

### 6.3 Spark
Spark is the distributed processing engine.

It is responsible for:

- reading bronze data,
- processing datasets at scale,
- writing structured lakehouse tables,
- supporting future multi-node execution.

### 6.4 Hive Metastore
Hive Metastore is the metadata catalog.

It is responsible for:

- namespaces,
- schema registration,
- table discovery,
- interoperability between Spark and Trino.

### 6.5 Iceberg
Iceberg is the managed lakehouse table format.

It is responsible for:

- structured analytical tables over lake storage,
- schema evolution,
- partition-aware management,
- snapshot-based consistency.

### 6.6 Trino
Trino is the analytical SQL access layer.

It is responsible for:

- querying the lakehouse,
- enabling analytics over Iceberg tables,
- supporting future reporting connectivity.

### 6.7 dbt-spark
dbt-spark is the transformation-modeling layer on top of the lakehouse.

It is responsible for:

- expressing transformation logic as versioned models,
- separating raw distributed loading from business-ready modeling,
- creating staging, intermediate, and analytics outputs,
- making the transformation layer easier to defend, audit, and maintain.

### 6.8 Great Expectations
Great Expectations is the validation layer.

It is responsible for:

- enforcing explicit quality contracts,
- verifying structural and semantic expectations,
- increasing trust before downstream reuse.

### 6.9 Airflow
Airflow is the orchestration layer.

It is responsible for:

- sequencing the workflows,
- controlling dependencies,
- improving rerun control,
- making pipeline operations explainable.

### 6.10 Prometheus and Grafana
These are the observability components.

They are responsible for:

- metrics collection,
- pipeline-health monitoring,
- infrastructure visibility,
- operational dashboards.

---

## 7. Main Engineering Objectives

The PFE must prove the following engineering capabilities:

- design of a complete multi-layer data architecture,
- structured ingestion and landing,
- distributed storage and processing,
- managed analytical tables,
- separation between storage, processing, querying, and monitoring,
- quality assurance,
- orchestration,
- operational visibility,
- deployment-oriented organization.

---

## 8. Client 1 Scope

The current project scope is centered on **Client 1** and its active heterogeneous source datasets:

- Customer Personality Analysis
- E-commerce Customer Churn
- RetailRocket dataset
- UCI Online Retail II

These are used to prove that the platform can:

- ingest multiple source domains,
- process mixed formats,
- preserve source identity,
- and expose trusted analytical assets.

---

## 9. Data Flow Rules

### 9.1 Source Rule
Source files remain the starting point of the platform and must preserve dataset identity.

### 9.2 Ingestion Rule
All official ingestion must pass through Kafka.

### 9.3 Bronze Rule
All ingested data must land first in HDFS bronze before structured processing.

### 9.4 Processing Rule
Bronze data must be processed by Spark, not by ad hoc manual scripts.

### 9.5 Lakehouse Rule
Structured analytical tables must be represented through Iceberg and cataloged via Hive Metastore.

### 9.6 Transformation Rule
Curated transformations must be expressed through dbt-spark models rather than embedded directly inside ingestion or raw Spark scripts.

### 9.7 Query Rule
Business and analytical SQL access must happen through Trino over the lakehouse.

### 9.8 Validation Rule
No downstream reuse should happen without explicit Great Expectations validation.

### 9.9 Orchestration Rule
The platform must remain runnable end to end through Airflow DAGs.

### 9.10 Monitoring Rule
The platform must remain observable during execution, not only after execution.

---

## 10. Architecture Benefits Compared to a Classical Warehouse-Only Design

The chosen lakehouse architecture is stronger for this PFE because it provides:

- distributed storage through HDFS,
- distributed compute through Spark,
- lakehouse table management through Iceberg,
- transformation governance through dbt-spark,
- query flexibility through Trino,
- better Big Data justification,
- clearer extensibility toward larger workloads.

This is the main reason the project shifts away from a traditional PostgreSQL-centered warehouse identity.

---

## 11. Expected Jury Interpretation

The jury should understand the project as follows:

> The project implements the customer-data engineering foundation of the broader AdOptimizer AI initiative by combining Kafka-based ingestion, HDFS bronze storage, Spark distributed processing, Hive and Iceberg lakehouse management, Trino analytical access, Great Expectations validation, Airflow orchestration, and Prometheus/Grafana observability into one coherent Big Data platform.

This is the recommended one-sentence interpretation for the defense.

---

## 12. What Must Be Emphasized During the Defense

The defense should emphasize:

- the multi-source nature of the data,
- the need for a real platform instead of isolated scripts,
- the ingestion backbone through Kafka,
- the bronze layer in HDFS,
- the distributed processing role of Spark,
- the importance of Iceberg as a modern table format,
- the catalog role of Hive Metastore,
- the transformation role of dbt-spark,
- the analytical access role of Trino,
- the validation role of Great Expectations,
- the orchestration role of Airflow,
- the observability role of Prometheus and Grafana.

---

## 13. What Must Be Avoided in the Defense

The defense should avoid overstating the project as:

- a finished AI platform,
- a production MLOps platform,
- a dashboarding platform,
- a simple ETL automation exercise.

If future AI/ML is discussed, it should be presented as:

- a downstream possibility,
- a consumer of curated data,
- not the center of the current PFE.

---

## 14. Folder-Structure Rule for the Jury

The technical structure must remain readable and layered.

The expected core structure to explain to the jury is:

```text
CustomerDNA AI/
  datasets/
    client_1/
      Customer_Personality_Analysis/marketing_campaign.csv
      E-commerce_customer_churn/E-commerce_customer_churn.xlsx
      Retailrocket_recommender_system_dataset/
        category_tree.csv
        events.csv
        item_properties_part1.csv
        item_properties_part2.csv
      UCI_Online_Retail_2/online_retail_2.xlsx
  project_requirements/
    BUSINESS_RULES.md
    BUSINESS_RULES_PFE_REPORT.md
    initial_project_description.txt
  src/
    airflow/
      docker-compose.yml
      dags/client_1/
        client_1_lakehouse_setup_dag.py
        client_1_kafka_hdfs_spark_raw_dag.py
        client_1_dbt_spark_transformations_dag.py
        client_1_lakehouse_readiness_dag.py
        client_1_dag_common.py
    streaming/
      kafka/
        docker-compose.yml
        client_1/
          run_client1_kafka_raw_pipeline.py
          reset_client1_kafka.py
          common/
          marketing_campaign/
          ecommerce_customer_churn/
          retailrocket_category_tree/
          retailrocket_events/
          retailrocket_item_properties/
          online_retail/
    lake/
      hdfs/
        docker-compose.yml
        client_1/
          initialize_client1_bronze_zone.py
          reset_client1_bronze.py
          bronze/
          silver/
          gold/
    processing/
      spark/
        docker-compose.yml
        Dockerfile
        jobs/client_1/load_hdfs_bronze_to_iceberg.py
    catalog/
      hive/
        docker-compose.yml
        config/
        metastore/Dockerfile
    query/
      trino/
        docker-compose.yml
        etc/catalog/lakehouse.properties
        client_1/initialize_lakehouse_namespace.py
    transformation/
      dbt_spark/
        client_1/
          dbt_project.yml
          profiles.yml
          models/
            staging/
            intermediate/
            analytics/
          macros/
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
    monitoring/
      prometheus/
      grafana/
      exporters/
      shared/
      state/
```

This structure is easier to explain to the jury because each folder maps directly to one platform responsibility.

---

## 15. Final Defense Rule

For the report and presentation, the project must always be narrated in this order:

1. AdOptimizer AI business context
2. customer-data fragmentation problem
3. Kafka ingestion
4. HDFS bronze persistence
5. Spark distributed processing
6. Hive Metastore + Iceberg lakehouse design
7. dbt-spark transformation layer
8. Trino analytical access
9. Great Expectations validation
10. Airflow orchestration
11. Prometheus + Grafana monitoring

This order creates the strongest and cleanest Data Engineering defense narrative.

---

## 16. Final Positioning Statement

> **AdOptimizer Customer Data Platform is a distributed Data Engineering platform that centralizes heterogeneous customer datasets through Kafka, HDFS, Spark, Hive, Iceberg, Trino, dbt-spark, Great Expectations, Airflow, and observability tooling in order to provide trusted analytical data foundations for the broader AdOptimizer AI vision.**

---

## 17. Document History

| Version | Date | Change |
|---|---|---|
| 3.2 | 2026-07-14 | Previous jury-focused version still centered on PostgreSQL warehouse and dbt transformation wording. |
| 4.0 | 2026-07-15 | Rewritten for the distributed lakehouse shift based on Kafka + HDFS + Spark + Hive Metastore + Iceberg + Trino. |
| 4.1 | 2026-07-16 | Updated to reflect the operational 4-DAG flow, the explicit dbt-spark transformation layer, and the detailed current project structure used in the running platform. |
