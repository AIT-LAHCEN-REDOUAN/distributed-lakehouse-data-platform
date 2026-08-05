# CustomerDNA AI - PFE Report Business Rules

> PFE jury-focused framing document
> Scope: Data Engineering, Big Data, distributed lakehouse, deployment, orchestration, quality, and observability
> Version: 5.0
> Last Updated: 2026-08-04

---

## 1. Purpose of This Document

This file is the official report-framing document for the PFE.

Its purpose is to help a report-writing system or a human writer describe the project correctly after the major refactor and deployment updates.

This document must be treated as the business and academic truth source for:

- project identity,
- implemented scope,
- architecture narrative,
- deployment narrative,
- data-flow narrative,
- dataset positioning,
- jury defense priorities,
- boundaries between implemented work and future AI/ML work.

This file is intentionally more interpretive than a runbook.

It explains what the project means, why it was built this way, and how it should be defended academically.

---

## 2. Official Project Identity

### 2.1 Official Project Name

**CustomerDNA AI - Distributed Customer Data Lakehouse Platform**

### 2.2 Correct Academic Positioning

For the PFE, the project must be defended primarily as:

- a **Data Engineering platform**,
- a **Big Data architecture**,
- a **distributed lakehouse implementation**,
- a **multi-layer pipeline orchestration project**,
- a **deployment-oriented technical foundation for downstream Customer 360 and AI use cases**.

### 2.3 What the Project Is Not Primarily

The project must **not** be presented primarily as:

- a finished machine learning platform,
- a pure BI dashboarding project,
- a simple ETL script collection,
- a classical single-database data warehouse,
- or a direct LLM/AI application.

### 2.4 Correct High-Level Identity Sentence

> CustomerDNA AI is a distributed customer-data engineering platform that ingests heterogeneous customer-related datasets, stores them in a replayable bronze layer, processes them through a lakehouse pipeline, exposes curated analytical tables, validates data quality, orchestrates execution, and monitors runtime behavior to create a trustworthy foundation for future Customer 360 and AI-driven marketing use cases.

---

## 3. Business Problem

Customer-related data is usually fragmented across different operational contexts.

In this project, the fragmentation is represented through multiple heterogeneous source datasets that capture different parts of the customer journey:

- transactional behavior,
- digital browsing intent,
- campaign interaction and response behavior.

Without a strong engineering foundation, this causes:

- incomplete customer understanding,
- weak analytical trust,
- difficult reprocessing,
- poor reproducibility,
- limited scalability,
- and low readiness for future segmentation, churn, conversion, and value-prediction models.

The engineering question answered by this project is:

> How can we build a distributed customer-data platform that ingests heterogeneous datasets through a reproducible pipeline, stores replayable raw data in distributed storage, processes it into governed lakehouse tables, exposes it for analytics, validates its quality, orchestrates it end to end, and monitors the full system in a way that is defensible as a modern Big Data Engineering project?

---

## 4. Business Vision and Downstream AI Context

The broader business vision behind the project is a future Customer 360 and intelligent marketing platform.

That broader vision includes downstream capabilities such as:

- dynamic customer segmentation,
- churn prediction,
- LTV-oriented analysis,
- campaign performance optimization,
- customer persona generation,
- behavior-aware personalization,
- and recommendation-oriented marketing actions.

### 4.1 Critical Boundary

These downstream intelligent features are **not** the core implemented contribution of the present PFE.

The implemented contribution of this PFE is the **data platform that makes those future capabilities possible and trustworthy**.

### 4.2 Correct Boundary Statement for the Report

The report must clearly state:

- **implemented today**:
  - ingestion,
  - distributed storage,
  - distributed processing,
  - lakehouse table management,
  - query access,
  - transformation governance,
  - data-quality validation,
  - orchestration,
  - observability,
  - distributed deployment demonstration.

- **future downstream use**:
  - ML segmentation,
  - churn prediction,
  - LTV prediction,
  - behavior scoring,
  - persona generation,
  - personalized action recommendation.

---

## 5. Final Implemented Scope

The current implemented scope is **Client 1** and its active three-source customer-data bundle.

The project was refactored to remove the previous legacy dataset scope and now uses a smaller, academically defensible, customer-oriented dataset set that better fits the available infrastructure and the Customer 360 objective.

### 5.1 Active Datasets

The active datasets are:

1. **Bank Marketing (bank-additional-full.csv)**
2. **Online Shoppers Purchasing Intention (online_shoppers_intention.csv)**
3. **UCI Online Retail II (online_retail_2.xlsx)**

### 5.2 Why These Datasets Were Chosen

This dataset combination is appropriate because together it covers multiple dimensions of customer understanding:

- **Bank Marketing**
  - customer profile attributes,
  - campaign contact history,
  - response outcome,
  - macro-economic context.

- **Online Shoppers Purchasing Intention**
  - web-session behavior,
  - engagement patterns,
  - digital navigation indicators,
  - purchase intention signals.

- **Online Retail II**
  - transaction history,
  - invoice behavior,
  - product-level purchase detail,
  - revenue and repeat-purchase signals.

### 5.3 Why This Supports Customer 360

The active dataset set supports a Customer 360 view because it combines:

- **profile and campaign information**,
- **behavioral intent information**,
- **commercial transaction information**.

This is enough to justify future models around:

- conversion,
- customer value,
- customer activity,
- engagement,
- churn risk proxies,
- and marketing effectiveness.

### 5.4 Academic Defensibility

The dataset bundle is also easier to defend in front of a jury because:

- it is customer-oriented,
- it is heterogeneous,
- it has academic provenance,
- it is small enough to run in the available infrastructure,
- and it still demonstrates multi-source integration and distributed processing.

### 5.5 Source Provenance Rule

The project must reference source provenance when possible.

In particular:

- the Bank Marketing source includes citation and field documentation through `bank-additional-names.txt`,
- the Online Retail II dataset is a widely used academic retail dataset,
- the Online Shoppers Intention dataset is a recognized behavioral analytics dataset.

---

## 6. Final Architecture to Present

The architecture to present in the report is:

```text
Customer datasets
  -> Kafka ingestion
  -> HDFS bronze landing
  -> Spark raw loading
  -> Iceberg raw tables
  -> Hive Metastore catalog
  -> Trino analytical access
  -> dbt-spark transformations
  -> Great Expectations validation
  -> Airflow orchestration
  -> Prometheus + Grafana monitoring
  -> downstream Customer 360 analytics and future AI/ML consumers
```

This is the authoritative architecture for the final report.

---

## 7. Final Deployed Topology

The deployed version is **not** a pure single-machine demo anymore.

It is a **distributed data plane with a local control plane**.

### 7.1 Control Plane on the Local PC

The local PC hosts the orchestration and supervision components:

- Airflow,
- Prometheus,
- Grafana,
- Kafka UI,
- pipeline metrics exporter,
- Spark submit client for remote cluster submission.

### 7.2 VM1 Responsibilities

VM1 hosts:

- Kafka broker 1,
- HDFS DataNode 1,
- Spark worker 1,
- Trino worker 1,
- cAdvisor.

### 7.3 VM2 Responsibilities

VM2 hosts the leader services of the data plane:

- Kafka broker 2,
- HDFS NameNode,
- HDFS DataNode 2,
- Hive Metastore,
- Hive Metastore PostgreSQL,
- Spark master,
- Spark worker 2,
- Spark history server,
- Spark Thrift server,
- Trino coordinator,
- cAdvisor.

### 7.4 VM3 Responsibilities

VM3 hosts:

- Kafka broker 3,
- HDFS DataNode 3,
- Spark worker 3,
- Trino worker 3,
- cAdvisor.

### 7.5 Correct Interpretation

The project therefore demonstrates:

- distributed ingestion,
- distributed storage,
- distributed processing,
- distributed query execution,
- centralized orchestration,
- centralized observability.

This is a strong and realistic deployment pattern for a PFE.

---

## 8. End-to-End Data Flow Narrative

The end-to-end data flow must be explained in the following order.

### 8.1 Source Datasets

The active Client 1 source files are stored under the project datasets folder.

Each dataset keeps its source identity and schema characteristics.

### 8.2 Kafka Ingestion

Each dataset is produced into its own Kafka topic family.

Kafka is used to:

- standardize ingestion entry,
- decouple dataset reading from downstream persistence,
- support replayability,
- support distributed transport.

### 8.3 HDFS Bronze Landing

Kafka consumers write raw landed files into the HDFS bronze layer.

This bronze layer is the replayable raw persistence zone.

It protects the pipeline from direct coupling between source files and downstream lakehouse processing.

### 8.4 Spark Raw Loading

Spark reads bronze files from HDFS and applies the raw loading job.

This raw loading stage:

- parses the landed data,
- applies source-specific schema logic,
- creates raw Iceberg tables,
- and registers them through the shared metastore/catalog layer.

### 8.5 Iceberg + Hive Metastore

The raw structured tables are stored as Iceberg tables and cataloged through Hive Metastore.

This gives the platform:

- managed metadata,
- schema tracking,
- consistency,
- and interoperability between Spark and Trino.

### 8.6 Trino Query Layer

Trino provides SQL access over the lakehouse.

It is the main interactive analytical entry point for:

- validation,
- exploration,
- downstream analytics,
- and report evidence.

### 8.7 dbt-spark Transformations

dbt-spark creates the modeled layers on top of the raw Iceberg tables.

The active transformation layers are:

- **staging**
  - `stg_bank_marketing`
  - `stg_online_shoppers_intention`
  - `stg_online_retail_2`

- **intermediate**
  - `int_bank_marketing_contacts`
  - `int_online_shopper_sessions`
  - `int_online_retail_customer_sales`
  - `int_customer_360_feature_store`

- **analytics**
  - `analytics_customer360_overview`
  - `analytics_conversion_performance`
  - `analytics_sales_performance`

### 8.8 Great Expectations Validation

Great Expectations validates raw-lakehouse data quality and generates evidence artifacts.

The active raw validation definitions are:

- `raw_lakehouse_quality_checkpoint__bank_marketing.json`
- `raw_lakehouse_quality_checkpoint__online_shoppers_intention.json`
- `raw_lakehouse_quality_checkpoint__online_retail_2.json`

It also generates:

- validation JSON result artifacts,
- and HTML Data Docs evidence.

### 8.9 Airflow Orchestration

Airflow coordinates the full sequence through DAGs and task dependencies.

It is the operational backbone of the project.

### 8.10 Monitoring

Prometheus collects metrics, while Grafana exposes dashboards for:

- infrastructure health,
- PostgreSQL metastore visibility,
- pipeline-state visibility.

---

## 9. Exact DAG Set and Execution Order

The current implemented Airflow DAG set is:

1. `customerdna_client1_environment_reset_pipeline`
2. `customerdna_client1_lakehouse_setup_pipeline`
3. `customerdna_client1_lakehouse_readiness_pipeline`
4. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
5. `customerdna_client1_dbt_spark_lakehouse_pipeline`

### 9.1 Correct Clean-Start Order

From a clean deployment, the correct operational order is:

1. `customerdna_client1_environment_reset_pipeline`
2. `customerdna_client1_lakehouse_setup_pipeline`
3. `customerdna_client1_lakehouse_readiness_pipeline`
4. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
5. `customerdna_client1_dbt_spark_lakehouse_pipeline`

### 9.2 What This Order Proves

This order proves that the platform is not only conceptually designed, but actually:

- resettable,
- reproducible,
- staged,
- validated,
- and executable end to end.

---

## 10. Role of Each Main Technology

### 10.1 Kafka

Kafka is the ingestion backbone.

It is responsible for:

- topic-based source transport,
- producer/consumer decoupling,
- replay support,
- distributed ingestion behavior.

### 10.2 HDFS

HDFS is the bronze distributed storage layer.

It is responsible for:

- raw persistence,
- dataset replayability,
- distributed storage demonstration,
- source-to-processing separation.

### 10.3 Spark

Spark is the distributed processing engine.

It is responsible for:

- loading bronze data from HDFS,
- writing Iceberg raw tables,
- executing distributed computation,
- supporting multi-worker parallelism.

### 10.4 Hive Metastore

Hive Metastore is the metadata authority.

It is responsible for:

- namespace registration,
- table registration,
- shared metadata access across engines.

### 10.5 Iceberg

Iceberg is the lakehouse table format.

It is responsible for:

- structured table storage on lake files,
- consistent table semantics,
- scalable table management,
- schema evolution readiness.

### 10.6 Trino

Trino is the distributed SQL query layer.

It is responsible for:

- analytical querying,
- interactive table access,
- downstream BI and evidence extraction.

### 10.7 dbt-spark

dbt-spark is the curated transformation layer.

It is responsible for:

- versioned SQL modeling,
- separation of raw and business-ready logic,
- reproducible model builds,
- testable transformation governance.

### 10.8 Great Expectations

Great Expectations is the data-quality contract layer.

It is responsible for:

- expectation-driven validation,
- validation artifacts,
- HTML evidence generation through Data Docs,
- trust reinforcement before downstream reuse.

### 10.9 Airflow

Airflow is the orchestration layer.

It is responsible for:

- dependency management,
- ordered execution,
- operational reruns,
- pipeline observability through task history.

### 10.10 Prometheus and Grafana

These tools form the observability layer.

They are responsible for:

- metrics scraping,
- dashboard exposure,
- runtime visibility,
- infrastructure monitoring.

---

## 11. Customer 360 Modeling Logic

The project should be described as building a **Customer 360-ready analytical foundation**, not a finished enterprise customer master.

The current logic combines:

- campaign/customer profile signals from Bank Marketing,
- session and intent signals from Online Shoppers Intention,
- sales and transaction signals from Online Retail II.

The dbt intermediate and analytics layers transform these into:

- contact-level marketing information,
- session-level intent information,
- customer-level sales features,
- a customer-oriented feature-store style table,
- analytical overview tables for conversion and sales interpretation.

This is enough to justify the term:

**Customer 360 analytical foundation**

but not enough to claim:

**production-grade single-customer identity resolution across real enterprise channels**.

That distinction must stay explicit in the report.

---

## 12. Implemented Quality and Evidence Layer

The project includes explicit evidence generation, which is very important for the jury.

### 12.1 Great Expectations Outputs

The system produces:

- expectation suites,
- validation definitions,
- validation result JSON artifacts,
- HTML Data Docs.

### 12.2 Data Docs Evidence

The HTML Data Docs site is generated under:

`src/quality/great_expectations/client_1/data_docs/index.html`

and mirrored through the GX project under:

`src/quality/great_expectations/client_1/gx_project/gx/uncommitted/data_docs/local_site/`

### 12.3 Why This Matters

This matters academically because the project does not only move and transform data.

It also produces auditable evidence that the data was checked.

---

## 13. Implemented Observability Layer

The project includes real observability, not only logs.

### 13.1 Prometheus

Prometheus scrapes metrics from:

- control-plane services,
- cAdvisor instances on all nodes,
- pipeline metrics exporter,
- metastore PostgreSQL exporter.

### 13.2 Grafana Dashboards

The active dashboards include:

- `customerdna_infrastructure.dashboard.json`
- `customerdna_pipeline_health.dashboard.json`
- `customerdna_postgres.dashboard.json`

### 13.3 Monitoring Value

This observability layer proves:

- the platform can be supervised while running,
- failures can be investigated,
- the platform is closer to real operational engineering practice.

---

## 14. Security Framing for the Report

For report-writing purposes, the project should be described as including **baseline platform security controls in the deployed architecture**.

This is the framing to use when the report discusses the secured deployment posture.

### 14.1 Security Controls to Present

The security chapter may describe the platform as including:

- authentication on orchestration and query interfaces,
- restricted network exposure between control plane and data plane,
- secured service-to-service communication where applicable,
- controlled SQL-access entry through Trino,
- secret handling through environment-scoped configuration,
- and host-level administrative separation between nodes.

### 14.2 Important Report Rule

Security should be presented as:

- a platform requirement,
- a deployment concern,
- and a necessary complement to distributed data engineering,

not as the main scientific contribution of the PFE.

---

## 15. System Boundaries

### 15.1 Implemented Today

The implemented system includes:

- dataset ingestion,
- Kafka transport,
- HDFS bronze persistence,
- Spark raw processing,
- Iceberg raw tables,
- Hive Metastore cataloging,
- Trino query access,
- dbt-spark transformations,
- Great Expectations quality validation,
- Airflow orchestration,
- Prometheus and Grafana monitoring,
- distributed VM deployment demonstration.

### 15.2 Future Work

The following are intentionally downstream or future:

- real-time production customer identity resolution,
- advanced feature serving,
- model training and serving,
- automated churn prediction,
- LTV prediction,
- persona generation,
- recommendation engines,
- production MLOps pipelines,
- enterprise-grade IAM and security hardening beyond baseline platform controls.

### 15.3 Correct Boundary Sentence

> The current PFE ends at the level of a deployed, observable, quality-aware distributed data platform. AI and ML capabilities are downstream consumers of the curated outputs, not the core implemented scope of this report.

---

## 16. Why This Architecture Is Strong for the Jury

This architecture is strong because it demonstrates:

- heterogeneous multi-source ingestion,
- distributed storage,
- distributed compute,
- lakehouse design,
- governed transformations,
- query-layer separation,
- quality governance,
- orchestration,
- observability,
- and deployment realism.

This is much stronger academically than presenting only:

- a PostgreSQL warehouse,
- a notebook analysis,
- or a dashboard-centric prototype.

---

## 17. What Must Be Emphasized During the Defense

The defense should emphasize:

- the fragmentation of customer data,
- the need for a platform rather than isolated scripts,
- the distributed nature of storage and processing,
- the value of replayable bronze storage,
- the need for governed transformations,
- the operational role of orchestration,
- the importance of quality evidence,
- the role of observability,
- and the fact that the architecture directly prepares downstream Customer 360 and AI use cases.

---

## 18. What Must Be Avoided During the Defense

The defense should avoid:

- claiming the project is already a finished AI platform,
- exaggerating the scope into full enterprise MDM,
- presenting dashboards as the main contribution,
- presenting the system as a simple ETL chain,
- or hiding the distinction between the data platform and future ML modules.

---

## 19. Folder-Structure Rule for the Report

The report must explain the repository as a layered engineering structure.

The layers are:

- `datasets/`
- `project_requirements/`
- `src/airflow/`
- `src/streaming/kafka/`
- `src/lake/hdfs/`
- `src/processing/spark/`
- `src/catalog/hive/`
- `src/query/trino/`
- `src/transformation/dbt_spark/`
- `src/quality/great_expectations/`
- `src/monitoring/`
- `src/deployments/distributed_pc_control_plane/`

Each folder exists for a clear platform responsibility.

Nothing should be described as a decorative tool.

---

## 20. Final Defense Narrative Order

For the written report and oral defense, the strongest narrative order is:

1. customer-data fragmentation problem
2. Customer 360 business objective
3. need for a distributed data platform
4. dataset scope and heterogeneity
5. Kafka ingestion
6. HDFS bronze landing
7. Spark processing
8. Hive Metastore and Iceberg lakehouse
9. Trino SQL access
10. dbt-spark transformation layer
11. Great Expectations quality layer
12. Airflow orchestration
13. Prometheus and Grafana observability
14. distributed deployment across the three VMs plus local control plane
15. downstream AI/ML readiness

This is the cleanest and most defensible order.

---

## 21. Final Positioning Statement

> CustomerDNA AI is a distributed customer-data lakehouse platform that centralizes heterogeneous customer-related datasets through Kafka, HDFS, Spark, Hive Metastore, Iceberg, Trino, dbt-spark, Great Expectations, Airflow, and observability tooling in order to produce trusted analytical foundations for Customer 360 analysis and future AI-driven marketing use cases.

---

## 22. Document History

| Version | Date | Change |
|---|---|---|
| 4.4 | 2026-07-27 | Previous jury-focused version before the final dataset and deployment refactor. |
| 5.0 | 2026-08-04 | Fully rewritten to reflect the final active datasets (Bank Marketing, Online Shoppers Intention, Online Retail II), the five-DAG orchestration flow, the local control plane plus distributed VM deployment, the current dbt model set, the current GX validation set, and the final jury-facing scope boundaries. |
