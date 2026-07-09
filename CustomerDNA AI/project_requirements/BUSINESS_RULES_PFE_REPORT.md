# CustomerDNA AI - PFE Data Engineering Business Rules

> **PFE Jury-Focused Document**
> Scope: Data Engineering positioning only
> Status: Implemented Client 1 platform view
> Version: 2.0
> Last Updated: 2026-07-08

---

## 1. Document Purpose

This document is the jury-facing reference for the **Data Engineering identity** of the CustomerDNA AI project.

It exists to explain, in a rigorous and defense-ready way:

- what business and technical problem the project solves,
- why the project is positioned primarily as a Data Engineering platform,
- what architecture has been implemented,
- what tools and layers are used,
- how data moves from source files to trusted warehouse outputs,
- how quality, orchestration, and monitoring are enforced,
- what exactly is already operational for Client 1,
- how the platform is prepared for later deployment and future extensions.

This file must be treated as the **official PFE interpretation document**.

Unlike the global `BUSINESS_RULES.md`, this file intentionally minimizes broader AI/ML framing and keeps the report narrative centered on **Data Engineering, warehouse architecture, quality, orchestration, and observability**.

---

## 2. Official PFE Positioning

### 2.1 Project Name
**CustomerDNA AI - Data Engineering Platform for Customer Analytics and AI/ML-Ready Data Products**

### 2.2 Core Positioning Rule
For the PFE, CustomerDNA AI must be presented first and foremost as an **end-to-end Data Engineering platform**.

### 2.3 Meaning of This Positioning
This means the project is not being defended primarily as:

- a dashboarding project,
- a machine-learning project,
- a business-reporting project,
- or a simple ETL scripting exercise.

Instead, it is being defended as the design and implementation of a structured platform that:

- centralizes heterogeneous customer data,
- preserves raw source records,
- loads data safely into a warehouse,
- transforms data through explicit layered modeling,
- validates quality through automated checks,
- orchestrates the pipeline through scheduled workflows,
- monitors infrastructure and pipeline health,
- exposes reusable and trusted data products.

### 2.4 Secondary Positioning Rule
Analytics and AI/ML use cases are valid and useful, but within the PFE they must be framed as:

- **downstream consumers** of the Data Engineering platform,
- **proof of platform reusability**,
- **future-ready extension points**,
- not the main academic identity of the project.

### 2.5 Deployment Positioning Rule
The project must also be presented as **deployment-oriented**.

This means the architecture is not limited to a one-time academic demonstration. It is organized so it can later be transferred to a **company-owned server environment** with the same logic, the same layers, and the same operational flow.

---

## 3. Business and Technical Problem Statement

Customer-related data is often fragmented across multiple independent files and source domains. In practice, this creates several recurring operational and analytical difficulties.

### 3.1 Fragmentation Problem
Customer information is dispersed across datasets that represent different perspectives, such as:

- marketing and campaign response,
- churn behavior,
- retail transactions,
- clickstream events,
- item attributes and category structure.

Because these datasets come from different structures and formats, they are difficult to integrate consistently.

### 3.2 Reproducibility Problem
Without a defined platform:

- loading logic is often manual,
- transformations are difficult to replay,
- debugging is inconsistent,
- pipeline behavior depends too much on ad hoc execution.

### 3.3 Trust Problem
Without explicit quality rules:

- raw issues may propagate downstream,
- transformed outputs may be consumed too early,
- dashboards may be built on unstable logic,
- future data products may be difficult to trust.

### 3.4 Scalability Problem
If the architecture is built only for one dataset or one script:

- onboarding future sources becomes painful,
- adding new clients becomes harder,
- deployment readiness remains weak,
- future intelligent use cases have no stable foundation.

### 3.5 Formal Problem Statement
The project therefore addresses the following question:

> How can we build a customer-data platform that centralizes heterogeneous customer datasets, ingests and loads them safely, transforms them through explicit warehouse layers, validates data quality, orchestrates end-to-end execution, monitors runtime health, and exposes trusted data products ready for analytics and future intelligent applications?

---

## 4. Proposed Solution

The project implements a **warehouse-centric Data Engineering platform** using PostgreSQL as the storage and transformation foundation, Kafka as the ingestion and raw-loading backbone, dbt as the transformation backbone, Great Expectations as the data-quality framework, Airflow as the orchestration layer, and Prometheus/Grafana as the observability layer.

### 4.1 High-Level Implemented Flow

```text
Client source files
  -> Kafka producers
  -> Kafka topics
  -> Kafka raw loaders
  -> PostgreSQL raw_data schema
  -> dbt staging views
  -> dbt intermediate tables
  -> dbt analytics marts
  -> dbt serving data products
  -> dbt tests + Great Expectations checkpoints
  -> Airflow orchestration
  -> Prometheus + Grafana observability
  -> trusted analytics-ready and serving-ready outputs
```

### 4.2 Why This Architecture Is Strong for a PFE
This architecture is strong academically and technically because it demonstrates:

- separation of concerns,
- explicit layer boundaries,
- reproducibility,
- traceability,
- validation,
- orchestration,
- operational visibility,
- future reusability.

### 4.3 Main Engineering Benefit
The platform moves the project from:

- isolated scripts,
- manual loading,
- and weakly governed transformations

to:

- structured ingestion,
- governed warehouse layers,
- explicit validation gates,
- operational workflow control,
- and monitored execution.

---

## 5. Strategic Objectives of the PFE

### 5.1 Main Objectives
The main objectives of the project are:

- build a complete Client 1 customer-data platform,
- integrate multiple heterogeneous customer datasets,
- make Kafka the active ingestion and raw-loading backbone,
- build a layered warehouse inside PostgreSQL,
- implement controlled transformations with dbt,
- enforce data quality with dbt tests and Great Expectations,
- orchestrate the workflow with Airflow,
- monitor the platform using Prometheus and Grafana,
- prepare trusted data products for analytics and future AI/ML reuse,
- prepare the platform for later deployment on a company-owned server.

### 5.2 Engineering Objectives
From a Data Engineering perspective, the project specifically aims to prove:

- source preservation,
- controlled warehouse design,
- layered ELT transformation,
- operational rerunnability,
- quality enforcement,
- observability,
- and deployment-oriented organization.

### 5.3 Academic Objectives
From a PFE perspective, the project must show that the student can:

- design an end-to-end data architecture,
- justify tool choices,
- separate data concerns correctly,
- implement a structured pipeline,
- govern transformation logic,
- validate outputs,
- and reason about platform operations.

---

## 6. Current Implemented Scope

The current implemented scope for Client 1 already includes the following production-style platform components.

### 6.1 Source Dataset Organization

- a dedicated top-level `datasets/client_1` source-data area,
- multiple customer-related source domains,
- mixed input formats including CSV and XLSX,
- clear dataset identity preservation.

### 6.2 Warehouse Setup

- PostgreSQL-based Client 1 data warehouse,
- schema initialization,
- metadata schema support,
- raw-table creation,
- repeatable setup scripts.

### 6.3 Kafka Ingestion and Raw Loading

- Kafka broker,
- Kafka UI,
- dataset-specific producers,
- dataset-specific loaders,
- topic-based ingestion flow,
- ordered raw loading pipeline for Client 1.

### 6.4 dbt Transformation Layer

- staging models,
- intermediate models,
- analytics models,
- serving models,
- documentation assets,
- tests and exposures.

### 6.5 Data Quality Layer

- Great Expectations context bootstrap,
- raw-layer validation,
- analytics-layer validation,
- serving-layer validation,
- ML-readiness validation,
- generated Data Docs.

### 6.6 Orchestration Layer

- three Airflow DAGs,
- warehouse setup flow,
- raw load flow,
- transformation-quality flow,
- rerunnable task decomposition.

### 6.7 Monitoring Layer

- Prometheus metrics collection,
- Grafana dashboards,
- cAdvisor metrics,
- PostgreSQL exporter metrics,
- custom pipeline metrics exporter,
- operational state files.

### 6.8 Curated Data Product Layer

- analytics-ready marts,
- serving-ready customer-level data products,
- stable downstream entities prepared for future reuse.

---

## 7. What Is In Scope for the Jury

The jury should focus on the platform components that prove Data Engineering maturity.

### 7.1 Data Ingestion and Raw Loading

- Kafka as ingestion backbone,
- dataset-to-topic logic,
- loader verification,
- repeatable raw loading into the warehouse.

### 7.2 Data Warehouse Design

- database setup,
- schema separation,
- raw preservation,
- metadata tracking,
- transformation layers.

### 7.3 Transformation Engineering

- dbt project structure,
- staged semantic cleanup,
- reusable intermediate models,
- final analytics marts,
- curated serving products.

### 7.4 Data Quality Engineering

- dbt tests,
- Great Expectations checkpoints,
- Data Docs,
- explicit trust gates.

### 7.5 Workflow Orchestration

- Airflow DAG decomposition,
- task sequencing,
- rerun control,
- failure isolation.

### 7.6 Monitoring and Observability

- infrastructure visibility,
- warehouse visibility,
- pipeline-health visibility,
- runtime inspection.

### 7.7 Deployment Readiness

- service separation,
- configuration-driven organization,
- Docker Compose support,
- server-transferable architecture.

---

## 8. What Is Not the Main Jury Focus

The following may be discussed briefly, but they must not dominate the defense narrative:

- advanced ML optimization,
- production inference APIs,
- model-serving architecture,
- enterprise MLOps lifecycle tooling,
- cloud-native platform design,
- real-time AI decision serving.

These are valid future directions, but the current PFE must remain focused on the **Data Engineering backbone**.

---

## 9. Client 1 Source Data Landscape

### 9.1 Source Dataset Families
Client 1 currently uses the following major source dataset groups:

1. **Customer Personality Analysis**
2. **E-commerce Customer Churn**
3. **RetailRocket Recommender System Dataset**
4. **UCI Online Retail II**

### 9.2 Source Dataset Files
The active files are:

- `datasets/client_1/Customer_Personality_Analysis/marketing_campaign.csv`
- `datasets/client_1/E-commerce_customer_churn/E-commerce_customer_churn.xlsx`
- `datasets/client_1/Retailrocket_recommender_system_dataset/category_tree.csv`
- `datasets/client_1/Retailrocket_recommender_system_dataset/events.csv`
- `datasets/client_1/Retailrocket_recommender_system_dataset/item_properties_part1.csv`
- `datasets/client_1/Retailrocket_recommender_system_dataset/item_properties_part2.csv`
- `datasets/client_1/UCI_Online_Retail_2/online_retail_2.xlsx`

### 9.3 Source Data Business Meaning
These datasets contribute different business views:

- demographic and campaign behavior,
- churn-related customer behavior,
- transactional sales behavior,
- digital interaction behavior,
- product and category metadata.

### 9.4 Source Data Rule
These sources are heterogeneous and must therefore be treated as:

- separate source domains,
- preserved raw inputs,
- engineering-managed upstream datasets,
- not a naturally unified enterprise operational schema.

---

## 10. Active Kafka Ingestion Backbone

### 10.1 Official Rule
Kafka is the **official active ingestion and raw-loading backbone** for Client 1.

### 10.2 Why Kafka Was Added
Kafka strengthens the platform because it introduces:

- decoupling between source reading and warehouse loading,
- topic-based transport,
- explicit dataset pipelines,
- better operational structure than a single direct raw loader,
- stronger justification for future scale and controlled ingestion.

### 10.3 Dataset-Specific Topic Pattern
The Client 1 topic naming pattern follows the form `client1.<dataset_name>`.

The current implemented topics correspond to:

- `client1.marketing_campaign`
- `client1.ecommerce_customer_churn`
- `client1.retailrocket_category_tree`
- `client1.retailrocket_events`
- `client1.retailrocket_item_properties`
- `client1.online_retail`

### 10.4 Active Kafka Components
The Kafka layer currently includes:

- `docker-compose.yml` for Kafka services,
- `requirements.txt`,
- `reset_client1_kafka.py`,
- `run_client1_kafka_raw_pipeline.py`,
- a common utility layer,
- dataset-specific producer scripts,
- dataset-specific sample consumer scripts,
- dataset-specific `load_to_raw.py` loaders.

### 10.5 Ordering Strategy
The raw pipeline processes smaller datasets first and larger datasets later. This improves:

- earlier failure visibility,
- easier debugging,
- better operational control,
- more practical long-run sequencing.

### 10.6 Kafka Boundary Rule
Kafka ingestion is allowed to:

- read source rows,
- serialize source data into topics,
- transport dataset records,
- batch inserts into raw tables,
- verify final raw counts.

Kafka ingestion must not:

- calculate final business KPIs,
- replace dbt transformation logic,
- perform hidden business reinterpretation,
- silently discard records without explicit handling.

---

## 11. Warehouse Architecture

### 11.1 Active Warehouse
The active Client 1 warehouse database is:

- `client1_DW`

### 11.2 Active Schemas
The current schema design includes:

- `raw_data`
- `metadata`
- `staging`
- `intermediate`
- `analytics`
- `serving`

### 11.3 Planned or Reserved Schemas
The broader design also anticipates:

- `reports`
- `client_specific`

### 11.4 Core Warehouse Rule
Each schema must have a single dominant responsibility. This is a key architectural discipline of the project.

---

## 12. Raw Layer Rules

### 12.1 Purpose of `raw_data`
The `raw_data` schema is the warehouse landing zone.

It exists to:

- preserve source-compatible records,
- keep source identity visible,
- support auditing and debugging,
- provide a clean handoff into transformation layers.

### 12.2 Active Raw Tables
The active raw tables are:

- `raw_data.marketing_campaign`
- `raw_data.e_commerce_customer_churn`
- `raw_data.category_tree`
- `raw_data.events`
- `raw_data.item_properties`
- `raw_data.online_retail`

### 12.3 Raw Layer Design Rule
The raw layer must remain:

- source-oriented,
- low-interpretation,
- robust to loading,
- not business-facing.

### 12.4 Raw Access Rule
Raw tables may be used for:

- debugging,
- auditing,
- source inspection,
- validation support.

They must not be used directly for final dashboard logic or direct business consumption.

---

## 13. Metadata Layer Rules

### 13.1 Purpose of `metadata`
The `metadata` schema exists to capture operational and audit-related information about the platform.

### 13.2 Metadata Responsibilities
The metadata layer supports:

- loaded-file tracking,
- pipeline-run tracking,
- raw-table registry information,
- warehouse documentation support.

### 13.3 Metadata Rule
Metadata is not a business-analytics layer. It is an **operational governance layer** for traceability and control.

---

## 14. dbt Transformation Architecture

### 14.1 dbt as the Transformation Backbone
dbt is the official transformation backbone of the platform.

It is responsible for:

- type-safe transformation logic,
- layered SQL modeling,
- lineage,
- testing,
- documentation,
- exposure definition,
- curated data-product construction.

### 14.2 Active dbt Layer Flow

```text
raw_data -> staging -> intermediate -> analytics -> serving
```

### 14.3 Materialization Philosophy

- `staging` models are lightweight **views**
- `intermediate` models are reusable **tables**
- `analytics` models are business-facing **tables**
- `serving` models are curated downstream-ready **tables**

### 14.4 dbt Layer Rule
Each dbt layer must solve the right type of problem:

- staging for standardization,
- intermediate for reusable business preparation,
- analytics for business marts,
- serving for curated downstream data products.

---

## 15. Staging Layer Rules

### 15.1 Purpose
The staging layer standardizes raw inputs while staying close to source semantics.

### 15.2 Implemented Staging Models

- `stg_customer_personality`
- `stg_ecommerce_churn`
- `stg_online_retail`
- `stg_retailrocket_category_tree`
- `stg_retailrocket_events`
- `stg_retailrocket_item_properties`

### 15.3 What Staging Must Do

- rename columns consistently,
- cast values safely,
- normalize basic inconsistencies,
- preserve source meaning,
- expose clean source-shaped relations.

### 15.4 What Staging Must Not Do

- create final KPIs,
- perform broad analytical aggregation,
- behave like a reporting layer,
- hide source meaning through aggressive reshaping.

---

## 16. Intermediate Layer Rules

### 16.1 Purpose
The intermediate layer builds reusable transformation components and controlled joins.

### 16.2 Implemented Intermediate Models

- `int_customer_profile`
- `int_online_retail_customer_summary`
- `int_retailrocket_event_summary`
- `int_retailrocket_latest_item_properties`
- `int_customer_behavior`
- `int_product_analysis`

### 16.3 What Intermediate Must Do

- combine staging outputs carefully,
- define reusable transformation logic,
- create stable downstream building blocks,
- isolate complex join and summarization logic.

### 16.4 Intermediate Grain Rule
Each intermediate model must have a clearly defensible grain.

### 16.5 Join Honesty Rule
If a join is analytical rather than naturally operational, it must still be documented honestly and kept controlled.

---

## 17. Analytics Layer Rules

### 17.1 Purpose
The analytics layer exposes trusted marts for business analysis and reporting.

### 17.2 Implemented Analytics Models

- `analytics_customer_segments`
- `analytics_sales_analytics`
- `analytics_product_performance`
- `analytics_business_intelligence`

### 17.3 What Analytics Must Do

- expose business-facing metrics,
- support reporting and BI consumption,
- package stable interpreted outputs,
- remain readable and reusable.

### 17.4 What Analytics Must Not Do

- act like raw cleanup,
- bypass intermediate preparation,
- become an uncontrolled feature dump,
- depend on undocumented transformations.

---

## 18. Serving Layer Rules

### 18.1 Purpose
The serving layer exposes curated customer-level and use-case-oriented data products.

### 18.2 Implemented Serving Models

- `customer_360`
- `segmentation_feature_base`
- `churn_feature_base`
- `ltv_feature_base`
- `persona_base`
- `marketing_recommendation_base`

### 18.3 Serving Layer Meaning in the PFE
For the PFE, the serving layer must be presented as:

- a curated **data-product layer**,
- a structured downstream-consumption layer,
- a reusable warehouse output for future APIs and future AI/ML workflows.

### 18.4 What Serving Must Do

- centralize trusted customer-level products,
- package curated downstream features,
- remain stable enough for reuse,
- serve as a controlled bridge between analytics engineering and future intelligent applications.

### 18.5 What Serving Must Not Do

- bypass quality gates,
- act as raw feature dumping,
- replace the analytics layer for standard business consumption,
- hide label-generation logic.

---

## 19. Data Quality Framework

### 19.1 Quality Philosophy
The project follows the rule that a dataset is not trustworthy simply because it builds successfully.

Trust must be earned through:

- valid raw loading,
- correct transformations,
- passing tests,
- explicit validation checkpoints,
- inspectable results.

### 19.2 dbt Tests
dbt tests are used to validate model integrity at warehouse level.

### 19.3 Great Expectations
Great Expectations is used to validate dataset-level contracts and readiness conditions.

### 19.4 Great Expectations Checkpoints
The implemented checkpoints are:

- raw data quality checkpoint,
- analytics data quality checkpoint,
- serving data quality checkpoint,
- ML feature readiness checkpoint.

### 19.5 Data Docs
Data Docs provide inspectable validation artifacts and strengthen explainability during development and presentation.

### 19.6 Quality Rule
No curated layer should be considered ready for downstream reuse unless its relevant validation path has passed.

---

## 20. Airflow Orchestration Architecture

### 20.1 Orchestration Principle
The platform must be runnable in a controlled, decomposed, restartable way.

### 20.2 Active Airflow DAGs
The current Airflow layer contains exactly three active DAGs:

1. `customerdna_client1_dw_setup_pipeline`
2. `customerdna_client1_raw_load_pipeline`
3. `customerdna_client1_transformation_quality_pipeline`

### 20.3 DAG 1 - Warehouse Setup Pipeline
`customerdna_client1_dw_setup_pipeline`

This DAG is responsible for preparing the warehouse base.

Its implemented task order is:

1. `start`
2. `setup_client1_data_warehouse`
3. `create_client1_raw_base_tables`
4. `end`

Its responsibility is to:

- create the warehouse environment,
- prepare schemas,
- create metadata objects,
- create raw base tables.

### 20.4 DAG 2 - Raw Load Pipeline
`customerdna_client1_raw_load_pipeline`

This DAG is responsible for the Kafka-based raw loading stage.

Its implemented task order is:

1. `start`
2. `run_kafka_raw_pipeline_to_dw`
3. `bootstrap_great_expectations`
4. `validate_raw_data_quality`
5. `end`

Its responsibility is to:

- run the Client 1 Kafka raw pipeline,
- load all source datasets into `raw_data`,
- bootstrap Great Expectations for the raw scope,
- validate raw-layer quality.

### 20.5 DAG 3 - Transformation and Quality Pipeline
`customerdna_client1_transformation_quality_pipeline`

This DAG is responsible for the full transformation and trust-validation stage.

Its implemented task order is:

1. `start`
2. `dbt_run_all_models`
3. `bootstrap_great_expectations`
4. `dbt_test_all_models`
5. `validate_analytics_quality`
6. `validate_serving_quality`
7. `validate_ml_feature_readiness`
8. `end`

Its responsibility is to:

- build all dbt layers,
- run dbt tests,
- validate analytics outputs,
- validate serving outputs,
- validate ML-readiness conditions.

### 20.6 Official Execution Order
The official complete execution order of the platform is:

1. warehouse setup DAG,
2. raw load DAG,
3. transformation-quality DAG.

### 20.7 Orchestration Design Benefit
This split architecture improves:

- rerun control,
- restartability,
- troubleshooting,
- failure isolation,
- defense clarity.

---

## 21. Monitoring and Observability Layer

### 21.1 Monitoring Purpose
Monitoring is part of the platform’s engineering value because it proves the system can be observed and operated, not only built.

### 21.2 Active Monitoring Stack
The monitoring stack includes:

- Prometheus,
- Grafana,
- cAdvisor,
- PostgreSQL exporter,
- custom pipeline metrics exporter.

### 21.3 Monitoring Coverage
The current monitoring layer provides visibility into:

- infrastructure/container health,
- PostgreSQL behavior,
- pipeline execution state,
- quality-process state artifacts.

### 21.4 Implemented Dashboards
The Grafana layer includes provisioned dashboards such as:

- infrastructure dashboard,
- PostgreSQL dashboard,
- pipeline-health dashboard.

### 21.5 Monitoring Rule
Monitoring is not an accessory. It is an engineering requirement because a serious data platform must be:

- operable,
- inspectable,
- measurable,
- explainable under execution.

---

## 22. Deployment Orientation

### 22.1 Deployment Rule
The architecture must be described as **deployment-ready in structure**, even if final company deployment steps come later.

### 22.2 Why the Platform Is Deployment-Oriented
The project already demonstrates:

- service separation,
- structured folders,
- explicit configuration,
- orchestrated workflows,
- container-based service composition,
- centralized monitoring components.

### 22.3 Deployment Target Interpretation
The intended deployment direction is a **company-owned server environment**, not a personal notebook-style execution model.

---

## 23. Folder Organization Value

### 23.1 Why Project Organization Matters
Folder structure is part of the engineering quality of the project.

It improves:

- maintainability,
- readability,
- deployment readiness,
- onboarding clarity,
- separation of responsibilities.

### 23.2 Main Active Technical Areas
The project is organized around these main active areas:

- `datasets/`
- `src/streaming/kafka/`
- `src/ELT/client_1/`
- `src/airflow/`
- `src/monitoring/`
- `src/ML/client_1/`
- `project_requirements/`

### 23.3 Organizational Rule
Any future additions must respect the same architecture-first separation rather than mixing all logic in one folder or one execution path.

---

## 24. Current Implemented Deliverables

At this stage, the project already delivers:

- organized heterogeneous Client 1 source data,
- Kafka-based ingestion and raw loading,
- PostgreSQL warehouse setup scripts,
- preserved `raw_data` tables,
- operational `metadata` support,
- dbt transformations from `staging` through `serving`,
- dbt docs and tests,
- Great Expectations validation and Data Docs,
- Airflow workflow orchestration,
- Prometheus monitoring,
- Grafana dashboards,
- deployment-oriented structure.

These are full Data Engineering deliverables, not partial prototypes.

---

## 25. Expected Jury Interpretation

The jury should understand the project in the following way:

> CustomerDNA AI is an end-to-end Data Engineering platform that ingests, preserves, transforms, validates, orchestrates, and monitors heterogeneous customer data in order to produce trusted analytics-ready and serving-ready data products, while establishing a reusable technical foundation for future enterprise analytics and future intelligent applications.

This sentence captures the correct final positioning.

---

## 26. Defense Framing Rules

### 26.1 What Must Be Emphasized
During the defense, the following should be emphasized:

- heterogeneous source integration,
- Kafka-based ingestion and loading,
- warehouse schema design,
- dbt layering,
- validation strategy,
- orchestration,
- monitoring,
- deployment readiness.

### 26.2 What Must Be Framed Carefully
If AI/ML is mentioned, it should be framed as:

- downstream experimentation,
- proof that the serving layer is reusable,
- evidence that the platform is future-ready,
- not the center of the current PFE.

### 26.3 What Must Not Be Claimed
The defense should avoid presenting the project primarily as:

- a real-time production AI platform,
- a cloud-native MLOps system,
- a production model-serving environment,
- or a pure BI dashboard project.

---

## 27. Final PFE Rule

For the report, presentation, and oral defense, the final official rule is:

> **CustomerDNA AI must be presented first as a Data Engineering platform, with analytics and future AI/ML use cases positioned as downstream value enabled by the platform.**

### 27.1 Practical Interpretation of the Final Rule
This means the story of the project should always begin with:

1. source data,
2. ingestion,
3. warehouse loading,
4. transformation layers,
5. validation,
6. orchestration,
7. monitoring,
8. curated data products,
9. future consumers.

This is the correct order for a strong and coherent PFE defense.
