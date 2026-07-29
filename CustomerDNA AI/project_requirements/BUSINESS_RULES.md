# AdOptimizer Customer Data Platform - Business Rules & Project Specification

> **Global Project Document** | Version 17.4
> Status: Distributed lakehouse architecture fully validated end to end for Client 1 with Kafka, HDFS, Spark, Hive Metastore, Iceberg, Trino, dbt-spark, Airflow, Great Expectations, Prometheus, and Grafana
> Last Updated: 2026-07-29

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

## 1.1 New Engineer Quick Start

This section is a practical starting point for a new engineer (or an external assistant) who needs to understand the project before making any deployment decisions.

### 1.1.1 Where to Start Reading

- Repository structure reference (authoritative tree): `full_project_strcuture.md`
- Local runbook (validated baseline): `RUNBOOK_local_Acer.md`
- Local tool ports (validated baseline): `tools_port_local_Acer.txt`
- PFE framing rules (jury-oriented): `project_requirements/BUSINESS_RULES_PFE_REPORT.md`

### 1.1.2 Current Implemented Scope

- Active scope: Client 1 only
- Active datasets:
  - `datasets/client_1/Customer_Personality_Analysis/marketing_campaign.csv`
  - `datasets/client_1/E-commerce_customer_churn/E-commerce_customer_churn.xlsx`
  - `datasets/client_1/Retailrocket_recommender_system_dataset/category_tree.csv`
  - `datasets/client_1/Retailrocket_recommender_system_dataset/events.csv`
  - `datasets/client_1/Retailrocket_recommender_system_dataset/item_properties_part1.csv`
  - `datasets/client_1/Retailrocket_recommender_system_dataset/item_properties_part2.csv`
  - `datasets/client_1/UCI_Online_Retail_2/online_retail_2.xlsx`

### 1.1.3 What “Done” Means in This Repository

The project is considered implemented locally when all these are true:

- Airflow runs the Client 1 DAG sequence successfully.
- HDFS bronze zone is initialized and receives dataset-specific landed files.
- Spark job writes Iceberg raw tables and registers metadata through Hive Metastore.
- dbt-spark produces staging/intermediate/analytics outputs over the lakehouse.
- Trino can query Iceberg tables through the lakehouse catalog.
- Great Expectations produces validation results and HTML Data Docs evidence.
- Prometheus and Grafana show infrastructure and pipeline-health dashboards.

### 1.1.4 Local Execution Order (Source of Truth)

Recommended operational order (from a clean start):

1. `customerdna_client1_lakehouse_readiness_pipeline` (pre-check)
2. `customerdna_client1_lakehouse_setup_pipeline`
3. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
4. `customerdna_client1_dbt_spark_lakehouse_pipeline`
5. `customerdna_client1_lakehouse_readiness_pipeline` (post-check, optional)

### 1.1.5 Key Evidence Locations (for Validation and Reporting)

- Airflow execution logs: `src/airflow/logs/`
- dbt execution artifacts: `src/transformation/dbt_spark/client_1/target/`
- Great Expectations Data Docs (HTML): `src/quality/great_expectations/client_1/gx_project/gx/uncommitted/data_docs/local_site/index.html`
- Great Expectations validation result store (JSON): `src/quality/great_expectations/client_1/gx_project/gx/uncommitted/validations/`
- Project monitoring state:
  - `src/monitoring/state/airflow_pipeline_state.json`
  - `src/monitoring/state/raw_load_state.json`
  - `src/monitoring/state/gx_state.json`

### 1.1.6 Deployment Rule for External Assistants

No multi-machine deployment plan should be executed unless it is directly derived from:

- the current repository files (compose files, `.env.example` templates, and configs under `src/`),
- the validated local runbook (`RUNBOOK_local_Acer.md`),
- and the VM deployment guides under `src/deployments/VM1`, `src/deployments/VM2`, `src/deployments/VM3`.

If any referenced compose/env/config file is missing or ambiguous, deployment must pause until the mismatch is resolved.

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

At the current state of the project, this architecture is no longer only a target design. It has been executed and validated locally end to end through the active Airflow DAG chain, with successful monitoring visibility and successful quality-validation runs.

### 4.1 Current Executable Runtime Sequence

The implemented platform must be explained through its concrete operational sequence.

Recommended operational order (from a clean start):

1. `customerdna_client1_lakehouse_readiness_pipeline` (pre-check)
2. `customerdna_client1_lakehouse_setup_pipeline`
3. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
4. `customerdna_client1_dbt_spark_lakehouse_pipeline`
5. `customerdna_client1_lakehouse_readiness_pipeline` (post-check, optional)

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

### 4.2 Final Validated Runtime State

The project has now reached a **validated local operational state** in which:

- the HDFS bronze zone initializes correctly,
- Hive Metastore namespaces are initialized correctly,
- Spark processes source data and writes Iceberg raw tables successfully,
- dbt-spark transformations run successfully,
- Trino exposes the curated lakehouse objects successfully,
- Great Expectations checkpoints succeed on the implemented scope,
- Airflow orchestrates the four-DAG chain successfully,
- Prometheus and Grafana expose working infrastructure and pipeline-health dashboards.

This validated state must be treated as the current architectural baseline of the project.

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
The platform should organize lakehouse data into clear layers that separate raw landing from curated analytics.

Two valid conceptual naming patterns exist:

- `bronze` / `silver` / `gold` (generic medallion pattern)
- `raw_data` / `staging` / `intermediate` / `analytics` (analytics-engineering pattern)

In the implemented Client 1 scope, the lakehouse is organized to support dbt-spark modeling and uses the second pattern for curated layers (staging/intermediate/analytics), with HDFS as the bronze file landing zone.

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

Recommended operational order (from a clean start):

1. `customerdna_client1_lakehouse_readiness_pipeline` (pre-check)
2. `customerdna_client1_lakehouse_setup_pipeline`
3. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
4. `customerdna_client1_dbt_spark_lakehouse_pipeline`
5. `customerdna_client1_lakehouse_readiness_pipeline` (post-check, optional)

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

The active project structure must reflect the distributed lakehouse architecture clearly and must remain readable for a new engineer joining the project.

The authoritative, up-to-date repository structure is documented in:

- `full_project_strcuture.md` (repository root)

The active structure should be understood at a responsibility level as follows:

```text
CustomerDNA AI/
  datasets/
    client_1/ (CSV/XLSX sources used for the implemented scope)
  project_presentation/
    PFE_Report/ (LaTeX report)
    PFE_resources/ (figures, logos, and tech logos used in the report)
  project_requirements/
    BUSINESS_RULES.md
    BUSINESS_RULES_PFE_REPORT.md
    initial_project_description.txt
  src/
    airflow/ (orchestration + DAGs + local Airflow stack)
    streaming/kafka/ (Kafka ingestion + producers/consumers)
    lake/hdfs/ (bronze landing zone helpers and HDFS stack)
    processing/spark/ (Spark stack + raw loader job into Iceberg)
    catalog/hive/ (Hive Metastore + catalog configs)
    query/trino/ (Trino stack + lakehouse catalog)
    transformation/dbt_spark/ (dbt project: staging/intermediate/analytics)
    quality/great_expectations/ (GE project + validations + Data Docs)
    monitoring/ (Prometheus/Grafana + custom exporter + pipeline state)
    deployments/ (multi-VM deployment guides: VM1/VM2/VM3)
```

Generated runtime artifacts exist in the repo during local runs (for example `src/airflow/logs/` and `src/transformation/dbt_spark/client_1/target/`). They are not source-of-truth implementation modules and should not be treated as architectural components.

The project must no longer keep a traditional PostgreSQL business-warehouse layer as the core analytical storage design.

PostgreSQL may exist only as:

- a metadata backend service for Hive Metastore,
- an Airflow metadata support component,
- or another infrastructure support component,
- but not as the main client analytical warehouse.

---

## 16. Final Architecture Consolidation Rule

The project has completed its strategic architecture transition:

- from a PostgreSQL warehouse-centric design,
- to a distributed **Kafka + HDFS + Spark + Hive Metastore + Iceberg + Trino + dbt-spark** lakehouse design.

This final architecture is now the only architecture that should be used in:

- the report,
- the oral defense,
- the architecture diagrams,
- the deployment narrative,
- and the future evolution roadmap.

Its advantages are:

- distributed storage,
- distributed processing,
- stronger Big Data positioning,
- cleaner separation between bronze landing and curated modeling,
- standards-based SQL access through Trino,
- governed transformation logic through dbt-spark,
- better alignment with modern enterprise lakehouse practice.

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

## 19. Local Runtime and Distributed Deployment Comparison Rule

The current project must continue to run correctly on the local development machine. The local environment is the validated development and demonstration baseline. It proves that the architecture, DAG ordering, data contracts, transformations, quality checks, and dashboards work end to end before deployment.

The future company-server deployment must use the same logical architecture and the same project responsibilities:

```text
source datasets
  -> Kafka
  -> HDFS bronze
  -> Spark distributed processing
  -> Iceberg lakehouse tables registered in Hive Metastore
  -> dbt-spark curated transformations
  -> Trino analytical access
  -> Great Expectations validation
  -> Airflow orchestration
  -> Prometheus/Grafana monitoring
```

The deployment must not change the conceptual pipeline. It should only change the runtime distribution:

- local mode runs the platform on one development machine through Docker Compose,
- deployment mode can distribute services across multiple machines,
- HDFS can distribute blocks across several DataNodes,
- Spark can distribute jobs across several workers,
- Kafka can be scaled with more broker capacity if needed,
- Trino can be extended for multi-node query execution if workload grows,
- monitoring must remain centralized through Prometheus and Grafana.

### 19.1 Local Mode Rule

The local development mode must remain operational because it is required for:

- iterative development,
- debugging,
- demonstrations before deployment,
- controlled pipeline validation,
- reproducible jury screenshots,
- confirming that changes do not break the platform.

Local mode is allowed to use local `.env` files for development and demonstration. These values are acceptable in the development branch, but production deployment must move toward stronger secrets management and environment-specific configuration.

### 19.2 Multi-Machine Deployment Rule

The future deployment should be positioned as a scale-out version of the same platform, not as a different project. The expected production-style distribution is:

- one or more machines for Kafka ingestion,
- multiple machines for HDFS NameNode/DataNode responsibilities,
- multiple machines for Spark master/worker execution,
- one machine or service group for Hive Metastore,
- one or more machines for Trino query access,
- one orchestration layer for Airflow,
- one monitoring layer for Prometheus and Grafana.

The important defense point is that HDFS and Spark are designed for distributed execution. When the company provides several machines, the architecture can use them to distribute storage and processing work instead of keeping all workload on one machine.

### 19.3 Performance and Latency Comparison Rule

The report should include a comparison between:

- the validated local Docker-based environment,
- and the future deployed multi-machine environment.

The comparison must use the same datasets and the same DAG sequence. The goal is not to claim theoretical performance only, but to measure concrete pipeline behavior.

Recommended metrics:

| Metric | Local Measurement | Deployment Measurement | Why It Matters |
|---|---:|---:|---|
| Total end-to-end pipeline duration | measured from Airflow | measured from Airflow | Shows full platform execution time |
| Kafka publish throughput | records/second | records/second | Shows ingestion speed |
| HDFS bronze write duration | seconds/minutes | seconds/minutes | Shows landing-zone performance |
| Spark raw table build duration | seconds/minutes | seconds/minutes | Shows distributed processing benefit |
| dbt-spark transformation duration | seconds/minutes | seconds/minutes | Shows curated-model build time |
| Great Expectations validation duration | seconds/minutes | seconds/minutes | Shows quality-control overhead |
| Trino query latency | seconds/query | seconds/query | Shows analytical access performance |
| CPU and memory utilization | Grafana | Grafana | Shows resource pressure |
| Failed task count | Airflow/Grafana | Airflow/Grafana | Shows operational reliability |

### 19.4 Fair Benchmarking Rule

For a fair comparison, both environments should:

- use the same source datasets,
- run the same DAGs in the same order,
- run the same dbt-spark models,
- run the same Great Expectations checks,
- use the same dashboard metrics where possible,
- document hardware details clearly,
- repeat measurements several times when possible,
- report average, minimum, and maximum duration.

The report must explain that local execution is useful for validation, while distributed deployment is useful for scalability and workload distribution.

### 19.5 Expected Interpretation

The expected result is not that every single operation is always faster in a cluster. Small workloads can be faster locally because there is less coordination overhead. The important Big Data argument is:

- as data volume grows,
- as jobs become heavier,
- and as more workloads run concurrently,

distributed storage and distributed processing become more valuable because work can be split across machines.

This is the correct scientific and engineering interpretation for the PFE report.

---

## 20. Document History

| Version | Date | Change |
|---|---|---|
| 16.2 | 2026-07-14 | Previous version aligned to Kafka -> HDFS -> Spark -> PostgreSQL raw flow. |
| 17.0 | 2026-07-15 | Rewritten to reflect the architecture shift toward Kafka + HDFS + Spark + Hive Metastore + Iceberg + Trino as the target distributed lakehouse platform. |
| 17.1 | 2026-07-16 | Updated to reflect the operational 4-DAG runtime, the dbt-spark transformation layer, the current monitoring stack, and the detailed live project structure with important files. |
| 17.2 | 2026-07-17 | Refined for the final validated state: architecture transition marked as completed, runtime validation status clarified, and the global document aligned with the fully successful local end-to-end lakehouse execution. |
| 17.3 | 2026-07-18 | Added local-vs-distributed deployment comparison rules, benchmark metrics, and guidance for preserving local runnable behavior while preparing future multi-machine evaluation. |
| 17.4 | 2026-07-29 | Updated project-structure section to match the current repository (removed legacy references), aligned DAG execution guidance with the pre-check/setup/run/post-check pattern, and clarified Great Expectations Data Docs as report evidence. |
