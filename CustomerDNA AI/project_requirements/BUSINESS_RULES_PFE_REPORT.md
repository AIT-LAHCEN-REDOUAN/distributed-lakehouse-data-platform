# CustomerDNA AI - PFE Report Business Rules

> PFE jury-focused framing document
> Scope: Data Engineering, Big Data, distributed lakehouse, secure distributed deployment, orchestration, quality, and observability
> Version: 5.1
> Last Updated: Monday, August 10, 2026

---

## 1. Purpose of This Document

This file is the official report-framing document for the PFE.

Its purpose is to help a report-writing system or a human writer describe the project correctly after the final dataset refactor, distributed deployment stabilization, and security-layer implementation.

This document must be treated as the business and academic truth source for:

- project identity,
- implemented scope,
- architecture narrative,
- deployment narrative,
- data-flow narrative,
- dataset positioning,
- jury defense priorities,
- security positioning,
- and boundaries between implemented work and future AI/ML work.

This file is intentionally interpretive rather than operational.

It explains what the project means, why it was built this way, how it should be defended academically, and which claims are valid versus exaggerated.

---

## 2. Official Project Identity

### 2.1 Official Project Name

**CustomerDNA AI - Distributed Customer Data Lakehouse Platform**

### 2.2 Correct Academic Positioning

For the PFE, the project must be defended primarily as:

- a **Data Engineering platform**,
- a **Big Data architecture**,
- a **distributed lakehouse implementation**,
- a **secure multi-node data platform**,
- a **multi-layer pipeline orchestration project**,
- and a **deployment-oriented technical foundation for downstream Customer 360 and AI use cases**.

### 2.3 What the Project Is Not Primarily

The project must **not** be presented primarily as:

- a finished machine learning platform,
- a pure BI dashboarding project,
- a simple ETL script collection,
- a classical single-database data warehouse,
- a direct LLM application,
- or a cybersecurity research thesis.

### 2.4 Correct High-Level Identity Sentence

> CustomerDNA AI is a secure distributed customer-data engineering platform that ingests heterogeneous customer-related datasets, stores them in a replayable bronze layer, processes them through a lakehouse pipeline, exposes curated analytical tables, validates data quality, orchestrates execution, monitors runtime behavior, and applies baseline infrastructure security controls to create a trustworthy foundation for future Customer 360 and AI-driven marketing use cases.

---

## 3. Business Problem

Customer-related data is usually fragmented across different operational contexts.

In this project, the fragmentation is represented through heterogeneous source datasets that capture different parts of the customer journey:

- marketing contact and campaign response behavior,
- web-session behavior and digital intent,
- transactional purchase behavior.

Without a strong engineering foundation, this causes:

- incomplete customer understanding,
- weak analytical trust,
- difficult reprocessing,
- poor reproducibility,
- limited scalability,
- weak governance,
- and low readiness for future segmentation, churn, conversion, and value-prediction models.

The engineering question answered by this project is:

> How can we build a distributed customer-data platform that ingests heterogeneous datasets through a reproducible pipeline, stores replayable raw data in distributed storage, processes it into governed lakehouse tables, exposes it for analytics, validates its quality, orchestrates it end to end, monitors the full system, and secures core infrastructure flows in a way that is defensible as a modern Big Data Engineering project?

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

The implemented contribution of this PFE is the **secure distributed data platform that makes those future capabilities possible and trustworthy**.

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
  - distributed deployment demonstration,
  - and baseline infrastructure security controls.

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

1. **Bank Marketing (`bank-additional-full.csv`)**
2. **Online Shoppers Purchasing Intention (`online_shoppers_intention.csv`)**
3. **Online Retail II (`online_retail_2.xlsx`)**

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

The dataset bundle is easier to defend in front of a jury because:

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

This is the authoritative functional architecture for the final report.

The deployment chapter must additionally show that this architecture is wrapped by a security layer built around:

- Kerberos-authenticated Hadoop secure mode,
- SPNEGO-protected HDFS web access,
- TLS-protected browser-facing interfaces,
- encrypted runtime storage on the VMs,
- and controlled entry points for orchestration and SQL access.

---

## 7. Final Deployed Topology

The deployed version is a **distributed data plane with a local control plane**.

### 7.1 Control Plane on the Local PC

The local PC hosts the orchestration and supervision components:

- Airflow,
- Prometheus,
- Grafana,
- Kafka UI,
- pipeline metrics exporter,
- PostgreSQL exporter,
- local TLS gateway for browser-facing control-plane access.

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
- Kerberos KDC and admin service,
- HDFS NameNode,
- HDFS DataNode 2,
- HDFS admin helper client,
- Hive Metastore,
- Hive Metastore PostgreSQL,
- Spark master,
- Spark submit helper,
- Spark worker 2,
- Spark history server,
- Spark Thrift server,
- Trino coordinator,
- Trino HTTPS gateway,
- cAdvisor.

### 7.4 VM3 Responsibilities

VM3 hosts:

- Kafka broker 3,
- HDFS DataNode 3,
- Spark worker 3,
- Trino worker 2,
- cAdvisor.

### 7.5 Correct Interpretation

The project therefore demonstrates:

- distributed ingestion,
- distributed storage,
- distributed processing,
- distributed query execution,
- centralized orchestration,
- centralized observability,
- and distributed baseline security enforcement.

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

### 8.11 Security Overlay

The report must also explain that the data flow is not left completely open:

- Hadoop service-to-service interactions are secured through Kerberos-aware configuration,
- HDFS browser-facing endpoints are exposed through HTTPS,
- Trino browser-facing access is available through an HTTPS gateway,
- browser-to-control-plane access is protected through a local TLS gateway,
- and VM runtime service data can be placed on encrypted LUKS-backed storage.

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

This order proves that the platform is:

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

### 10.11 Kerberos

Kerberos is the core authentication layer of the secured distributed deployment.

It is responsible for:

- service principal management,
- service-to-service authentication in Hadoop secure mode,
- keytab-based non-interactive service access,
- and browser ticket-based user authentication for protected HDFS pages.

### 10.12 TLS Gateways

TLS gateways are used to protect browser-facing traffic in the demo deployment.

They are responsible for:

- HTTPS access to control-plane tools,
- HTTPS access to the Trino entry point on VM2,
- and encrypted browser traffic without redesigning the internal service containers.

### 10.13 LUKS Encrypted Storage

LUKS-backed runtime storage is the main data-at-rest protection mechanism on the VMs.

It is responsible for:

- encrypting runtime service data at the filesystem level,
- protecting Kafka, HDFS, Hive, Spark, and Trino runtime directories when enabled,
- and strengthening the deployment narrative around secure data persistence.

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

The report should now present security as an **implemented deployment layer**, not only as a generic future concern.

### 14.1 Security Controls That Are Implemented

The security chapter may describe the platform as including:

- Kerberos-based Hadoop secure mode,
- service principals and keytab-based service authentication,
- SPNEGO-protected HDFS web endpoints,
- HTTPS-only HDFS NameNode and DataNode web interfaces,
- HTTPS-protected Trino gateway access,
- HTTPS-protected control-plane browser access through a local TLS gateway,
- environment-scoped credential handling for demo operations,
- host-level separation between control plane and data plane,
- remote Spark submission through explicit SSH access,
- and optional LUKS-backed encrypted runtime storage on the VMs.

### 14.2 Security Controls That Must Be Described Carefully

The following controls are valid to present, but with correct scope language:

- browser-side Kerberos for HDFS browsing is implemented as a **demo access path** and requires local client configuration on Windows and Firefox,
- demo TLS currently uses internal/self-signed trust paths rather than a public enterprise certificate chain,
- the deployment is secured enough to defend architectural intent, but it is not a complete enterprise IAM program.

### 14.3 Important Report Rule

Security should be presented as:

- an implemented platform requirement,
- a deployment hardening layer,
- and a necessary complement to distributed data engineering,

not as the main scientific contribution of the PFE.

### 14.4 Honest Limitation Rule

If the report discusses secure browser access to HDFS Explorer specifically, it must state that:

- secure HDFS and Kerberos are implemented,
- HDFS secure pages are reachable,
- but browser-side SPNEGO integration on Windows/Firefox is an integration-sensitive client path and should not be confused with the health of the backend cluster itself.

This is the honest and defensible way to describe the current state.

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
- distributed VM deployment demonstration,
- Kerberos-secured Hadoop deployment,
- HTTPS browser-facing access paths,
- and optional encrypted-at-rest VM runtime storage.

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
- enterprise certificate lifecycle automation,
- centralized secrets vault integration,
- and enterprise-grade IAM beyond the implemented baseline.

### 15.3 Correct Boundary Sentence

> The current PFE ends at the level of a deployed, observable, quality-aware, and security-aware distributed data platform. AI and ML capabilities are downstream consumers of the curated outputs, not the core implemented scope of this report.

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
- secure distributed deployment principles,
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
- the fact that the architecture prepares downstream Customer 360 and AI use cases,
- and the fact that security was not ignored after deployment, but added as a meaningful infrastructure layer.

---

## 18. What Must Be Avoided During the Defense

The defense should avoid:

- claiming the project is already a finished AI platform,
- exaggerating the scope into full enterprise MDM,
- presenting dashboards as the main contribution,
- presenting the system as a simple ETL chain,
- hiding the distinction between the data platform and future ML modules,
- or claiming enterprise-perfect browser SSO behavior if a client-side SPNEGO issue is still under investigation.

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

The deployment folder must now also be framed as the location of:

- the node bundles,
- the secure runtime topology,
- the Kerberos configuration,
- the Windows Kerberos client helper,
- and the LUKS-enabled storage setup scripts.

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
14. secure distributed deployment across the three VMs plus local control plane
15. downstream AI/ML readiness

This is the cleanest and most defensible order.

---

## 21. Final Positioning Statement

> CustomerDNA AI is a secure distributed customer-data lakehouse platform that centralizes heterogeneous customer-related datasets through Kafka, HDFS, Spark, Hive Metastore, Iceberg, Trino, dbt-spark, Great Expectations, Airflow, and observability tooling in order to produce trusted analytical foundations for Customer 360 analysis and future AI-driven marketing use cases.

---

## 22. Document History

| Version | Date | Change |
|---|---|---|
| 4.4 | 2026-07-27 | Previous jury-focused version before the final dataset and deployment refactor. |
| 5.0 | 2026-08-04 | Rewritten to reflect the final active datasets, the five-DAG orchestration flow, the local control plane plus distributed VM deployment, the current dbt model set, the GX validation set, and the jury-facing scope boundaries. |
| 5.1 | 2026-08-10 | Updated to reflect the implemented security layer: Kerberos-secured Hadoop deployment, SPNEGO-protected HDFS web access path, TLS browser-facing gateways, LUKS-backed VM runtime storage option, Windows Kerberos client helper assets, and the correct report boundary around client-side HDFS Explorer behavior. |
