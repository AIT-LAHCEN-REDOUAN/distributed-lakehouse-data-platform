# CustomerDNA AI - Business Rules & Project Specification

> **PFE Project Document** | Version 15.0
> Status: Client 1 Kafka-first data-engineering platform implemented with PostgreSQL warehouse setup, Kafka raw ingestion/loading backbone, dbt transformation stack (`staging`, `intermediate`, `analytics`, `serving`), dbt tests/docs, Great Expectations raw/analytics/serving/ML-readiness validation, split Airflow orchestration, Prometheus + Grafana monitoring, and local downstream ML experimentation on curated serving data products
> Last Updated: 2026-07-08

---

## 1. Document Purpose

This document is the central business-rules and technical-specification reference for **CustomerDNA AI**.

It defines:

- what the project is designed to solve,
- what data currently exists for Client 1,
- how data moves from source files to trusted warehouse outputs,
- what each architectural layer is responsible for,
- what standards must be respected as the platform evolves,
- what is already implemented,
- what remains future work.

This file is the **global reference document**. It covers the current data-engineering platform in full detail and also records the downstream local AI/ML experimentation layer that has been built on top of curated serving datasets.

---

## 2. Project Identity

### 2.1 Project Name
**CustomerDNA AI** - Multi-Client Customer Data Platform for Analytics and AI/ML-Ready Products

### 2.2 Strategic Positioning
CustomerDNA AI must be understood in two complementary ways:

- first, as a **Data Engineering platform** that centralizes, preserves, transforms, validates, orchestrates, and monitors heterogeneous customer datasets,
- second, as a **future-ready analytical foundation** that can support downstream AI/ML experimentation and later enterprise intelligent applications.

### 2.3 PFE Positioning
For the PFE, the primary academic and technical positioning remains **Data Engineering first**.

The strongest value demonstrated by the project is:

- architecture design,
- source preservation,
- ingestion/load reliability,
- layered transformation engineering,
- validation and trust controls,
- orchestration,
- monitoring and observability,
- readiness for deployment in a company-owned server environment.

### 2.4 AI/ML Positioning
AI/ML work exists in the current repository and has been implemented locally for experimentation. However, in the overall project positioning:

- AI/ML is a **consumer of curated serving outputs**,
- AI/ML is not the main identity of the current PFE,
- AI/ML implementation proves downstream extensibility, not the primary engineering focus.

### 2.5 Deployment Orientation
The architecture is designed so that it can:

- run in the current development environment,
- be orchestrated locally during development,
- be transferred later to a **company-owned server environment** without redesigning the logical platform.

---

## 3. Problem Statement

Customer data projects often fail because they are built around fragmented files, ad hoc scripts, weak validation, and undocumented transformation logic.

Typical recurring problems include:

1. **Fragmented inputs**
   - customer-related information lives in separate files with different structures, formats, and business meanings.

2. **Weak ingestion discipline**
   - loading logic is often manual, slow, or hard to rerun consistently.

3. **Poor layer separation**
   - raw data, cleaning logic, analytics logic, and business outputs are mixed together.

4. **Low data trust**
   - transformed outputs are used without explicit tests, validation checkpoints, or observability.

5. **Limited reusability**
   - many pipelines are built for one dataset only and cannot scale to multiple clients or future data products.

The project therefore addresses the following combined business and engineering challenge:

> How can we build a customer-data platform that ingests heterogeneous source datasets, loads them safely into a warehouse, transforms them through controlled layers, validates quality explicitly, monitors operational health, and exposes reusable curated outputs for analytics and future AI/ML use cases?

---

## 4. Proposed Solution

CustomerDNA AI solves this challenge through a layered warehouse-centric architecture with Kafka as the active ingestion backbone and dbt as the transformation backbone.

The implemented high-level flow is:

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
  -> Airflow orchestration + Prometheus/Grafana monitoring
  -> analytics consumption / future API / future enterprise AI-ML consumers
```

This design ensures that:

- source datasets remain identifiable,
- raw loading is explicit and repeatable,
- transformation logic is versioned and layered,
- quality gates are enforced,
- business-facing and serving-facing outputs are curated,
- monitoring is built into the platform,
- future client onboarding can follow the same pattern.

---

## 5. Business Objectives

### 5.1 Immediate Objectives

- Build a stable Client 1 customer-data platform.
- Centralize heterogeneous source datasets into one controlled warehouse flow.
- Make Kafka the official ingestion and raw-loading backbone.
- Build trusted dbt layers from `raw_data` to `serving`.
- Validate warehouse outputs with dbt tests and Great Expectations.
- Orchestrate the end-to-end pipeline with Airflow.
- Monitor infrastructure and pipeline state through Prometheus and Grafana.
- Expose reliable analytics marts and customer-level serving products.

### 5.2 Medium-Term Objectives

- Harden the pipeline for repeated server execution.
- Improve operational monitoring depth and alerting.
- Refine pipeline-performance optimization for large datasets.
- Expose curated outputs through future API and dashboard consumers.
- Stabilize future retraining or refresh patterns on top of serving outputs.

### 5.3 Long-Term Objectives

- Onboard additional clients.
- Introduce a later explicit cross-client layer when justified.
- Reuse the same ingestion, warehouse, validation, orchestration, and monitoring pattern for multiple tenants.
- Enable broader AI/ML and decisioning modules built on standardized curated data products.

---

## 6. Scope and Non-Goals

### 6.1 Current Implemented Scope
The currently implemented scope includes:

- Client 1 source dataset organization under the top-level `datasets` directory,
- Client 1 warehouse initialization scripts,
- Kafka broker and Kafka UI setup,
- dataset-specific Kafka producers,
- dataset-specific Kafka sample consumers for verification,
- dataset-specific Kafka-to-raw loaders,
- ordered Kafka raw pipeline runner for Client 1,
- PostgreSQL `raw_data` and `metadata` schemas,
- dbt `staging`, `intermediate`, `analytics`, and `serving` layers,
- dbt tests and documentation assets,
- Great Expectations validation for raw, analytics, serving, and ML-readiness scopes,
- Airflow split DAG orchestration,
- Prometheus metrics collection,
- Grafana dashboards,
- custom pipeline metrics exporter,
- centralized monitoring state files,
- serving-layer data products for customer 360, segmentation, churn, LTV, persona, and marketing recommendation workflows,
- local ML experimentation built on serving-layer snapshots,
- local ML EDA and interpretation artifacts.

### 6.2 Current Out-of-Scope or Future Work
The following are not the main implemented center of the platform:

- production cloud deployment,
- streaming-first business logic at transformation level,
- online inference APIs,
- enterprise model registry and full MLOps lifecycle automation,
- cross-client shared warehouse logic with multiple active clients,
- enterprise-grade access-control and governance services,
- full alerting/incident-management integration.

### 6.3 Architectural Non-Goals
The project must avoid:

- putting business logic inside raw loading,
- letting dashboards query `raw_data` directly,
- treating staging as an analytics layer,
- hiding source limitations through undocumented transformation shortcuts,
- bypassing validation before downstream reuse,
- reintroducing retired direct-loading paths as active architecture.

---

## 7. Stakeholders and Consumers

### 7.1 Primary Technical Stakeholder
The primary technical stakeholder is the project owner delivering the PFE with strong Data Engineering focus.

### 7.2 Business Consumers
Expected business-side consumers include:

- marketing managers,
- business analysts,
- decision makers,
- future dashboard users.

### 7.3 Technical Consumers
Expected technical consumers include:

- data engineers,
- analytics engineers,
- dbt developers,
- future ML engineers,
- API developers,
- dashboard developers,
- deployment and operations stakeholders.

### 7.4 Consumer Access Rule
Each consumer must use the correct layer:

- engineers may inspect all layers for debugging and development,
- business consumers should use curated analytics outputs,
- downstream ML or experimentation workflows should use validated serving outputs,
- monitoring tools should inspect state/metrics rather than query business tables for operational status.

---

## 8. Data Domains and Source Landscape

### 8.1 Client 1 Source Datasets
Client 1 currently uses four heterogeneous public dataset groups:

| Dataset Group | Source Files | Business Meaning | Active Raw Table(s) |
|---|---|---|---|
| Customer Personality Analysis | `marketing_campaign.csv` | Demographics, household composition, campaign response, spending mix | `raw_data.marketing_campaign` |
| E-commerce Customer Churn | `E-commerce_customer_churn.xlsx` | Customer churn behavior and service/usage indicators | `raw_data.e_commerce_customer_churn` |
| RetailRocket Recommender System Dataset | `events.csv`, `item_properties_part1.csv`, `item_properties_part2.csv`, `category_tree.csv` | Clickstream events, item attributes, category structure | `raw_data.events`, `raw_data.item_properties`, `raw_data.category_tree` |
| UCI Online Retail II | `online_retail_2.xlsx` | Transactional retail sales behavior | `raw_data.online_retail` |

### 8.2 Active Source Dataset Locations
The current active source files live under:

- `CustomerDNA AI/datasets/client_1/Customer_Personality_Analysis/marketing_campaign.csv`
- `CustomerDNA AI/datasets/client_1/E-commerce_customer_churn/E-commerce_customer_churn.xlsx`
- `CustomerDNA AI/datasets/client_1/Retailrocket_recommender_system_dataset/category_tree.csv`
- `CustomerDNA AI/datasets/client_1/Retailrocket_recommender_system_dataset/events.csv`
- `CustomerDNA AI/datasets/client_1/Retailrocket_recommender_system_dataset/item_properties_part1.csv`
- `CustomerDNA AI/datasets/client_1/Retailrocket_recommender_system_dataset/item_properties_part2.csv`
- `CustomerDNA AI/datasets/client_1/UCI_Online_Retail_2/online_retail_2.xlsx`

### 8.3 Dataset Interpretation Rule
These datasets contribute different customer-related perspectives. They are not one native operational enterprise source system. Therefore:

- each source keeps its identity in the raw layer,
- joins must be justified at transformation level,
- cross-dataset interpretation must remain honest,
- serving outputs are engineered customer products, not proof of original enterprise identity resolution.

---

## 9. Multi-Client Architecture Principle

### 9.1 Core Rule
The architecture is intentionally reusable for future clients.

### 9.2 Standard Client Pattern
Each client should eventually follow:

```text
client source files
  -> client-specific Kafka ingestion/loading
  -> clientX_DW.raw_data
  -> clientX_DW.staging
  -> clientX_DW.intermediate
  -> clientX_DW.analytics
  -> clientX_DW.serving
  -> validation + orchestration + monitoring
```

### 9.3 Client Isolation Rule
Client data must remain isolated at warehouse level unless an explicit future cross-client layer is introduced.

### 9.4 Future Global Layer Rule
A shared global warehouse or benchmarking layer is valid only after multiple clients are onboarded and standardization rules are strong enough to support safe comparison.

---

## 10. Technology Stack

### 10.1 Core Platform Stack

- **Python** for platform scripts, configuration, validation helpers, monitoring exporter logic, and local downstream experimentation
- **Apache Kafka** as the current active ingestion and raw-loading backbone
- **Kafka UI** for operational topic inspection
- **PostgreSQL** as the warehouse engine
- **dbt** for transformations, testing, lineage, and documentation
- **Great Expectations** for data-quality contracts and Data Docs
- **Apache Airflow** for workflow orchestration
- **Prometheus** for metrics collection
- **Grafana** for dashboard-based operational inspection
- **Docker Compose** for local and portable service composition
- **FastAPI** as future API layer
- **React** as future frontend layer

### 10.2 Tool-Fit Rule
A tool belongs in the architecture only if it improves engineering quality and operational clarity without breaking the project’s deployability.

### 10.3 Demonstrated Standards
The stack must showcase:

- source preservation,
- explicit layering,
- reproducible execution,
- visible validation,
- inspectable lineage,
- separated orchestration concerns,
- observability and operational feedback.

---

## 11. End-to-End Data Flow

### 11.1 Current Implemented Flow

```text
Source files in datasets/client_1
  -> dataset-specific Kafka producer scripts
  -> one topic per dataset
  -> dataset-specific Kafka raw loader scripts
  -> PostgreSQL raw_data tables
  -> dbt staging views
  -> dbt intermediate tables
  -> dbt analytics marts
  -> dbt serving data products
  -> dbt tests
  -> Great Expectations checkpoints
  -> monitoring state + Grafana/Prometheus dashboards
  -> analytics consumption / future API / future enterprise AI-ML
```

### 11.2 Operational Flow Rule
Each stage must perform only its own responsibility:

- Kafka handles ingestion transport and message-based raw loading,
- raw tables preserve source-compatible structures,
- dbt handles controlled transformation logic,
- quality tools validate trust,
- Airflow coordinates execution order,
- monitoring tools observe platform health.

### 11.3 Rerun Rule
The platform must support clean reruns from the beginning. For Client 1 this is achieved by:

- warehouse setup as a separate DAG,
- Kafka topic reset as part of the raw pipeline,
- dataset-by-dataset raw loading with verification,
- downstream transformation and quality orchestration as a separate final DAG.

---

## 12. Kafka Ingestion and Raw Loading Rules

### 12.1 Strategic Role of Kafka
Kafka is now the official ingestion and raw-loading backbone for Client 1.

It replaces the earlier direct raw-load path as the active architecture because it offers:

- clearer decoupling between source reading and warehouse loading,
- observable dataset-level transport,
- reusable topic-based ingestion design,
- easier justification for future scaling beyond a single manual load script.

### 12.2 Current Kafka Design
The Kafka layer currently includes:

- one broker,
- Kafka UI,
- client-level common producer utilities,
- source-specific row iterators,
- dataset-specific producer scripts,
- dataset-specific consumer verification scripts,
- dataset-specific raw loaders,
- one orchestrated raw pipeline runner.

### 12.3 Dataset-Specific Kafka Topics
The active Client 1 topic pattern follows:

- `client1.marketing_campaign`
- `client1.ecommerce_customer_churn`
- `client1.retailrocket_category_tree`
- `client1.retailrocket_events`
- `client1.retailrocket_item_properties`
- `client1.online_retail`

### 12.4 Current Loading Strategy Rule
The raw pipeline currently processes smaller datasets first and larger datasets last so that:

- early pipeline failures surface faster,
- validation can begin on small datasets sooner,
- long-running large loads are deferred until the smaller steps are already stable.

### 12.5 Kafka Ingestion Boundary Rule
Kafka ingestion may:

- read source rows from CSV/XLSX inputs,
- serialize them into topic messages,
- preserve dataset identity,
- batch raw inserts safely,
- verify final raw row counts.

Kafka ingestion must not:

- perform downstream business feature engineering,
- compute analytics KPIs,
- replace dbt transformation responsibilities,
- silently discard records without explicit handling.

### 12.6 Verification Rule
No dataset load should be considered complete unless:

- the producer publishes the expected dataset volume,
- the loader completes insertion successfully,
- the target raw table row count is verified.

---

## 13. Retired Ingestion Policy

### 13.1 Retired Path Status
The older direct ingestion path is no longer part of the active project structure.

### 13.2 Current Rule
The project must be documented and operated using the Kafka path as the only official Client 1 ingestion and raw-loading backbone.

### 13.3 Architectural Rule
Retired ingestion logic must not be reintroduced into the active platform unless there is an explicit redesign decision.

---

## 14. Raw Data Layer Rules

### 14.1 Raw Layer Purpose
The `raw_data` schema is the preserved warehouse landing layer.

### 14.2 Active Raw Tables
The active Client 1 raw tables are:

- `category_tree`
- `e_commerce_customer_churn`
- `events`
- `item_properties`
- `marketing_campaign`
- `online_retail`

### 14.3 Raw Layer Principles

- Raw tables must remain as close as practical to source-compatible structure.
- Load safety is more important here than analytical convenience.
- Typing and strong cleaning primarily belong downstream.
- Raw data is a debug, audit, and lineage-preservation layer.
- Raw loading must remain traceable through metadata and logs.

### 14.4 Metadata Tracking Rule
Raw loading must remain observable through metadata tables and monitoring state artifacts, including:

- loaded file or dataset metadata,
- pipeline run metadata,
- row-count verification and run status logs.

### 14.5 Raw Consumption Rule
Raw data must not be used directly for final business dashboards or final downstream customer products.

---

## 15. Warehouse Schema Rules

### 15.1 Active Database
The active warehouse database is:

- `client1_DW`

### 15.2 Active and Planned Schemas

- `raw_data` - active
- `metadata` - active
- `staging` - active
- `intermediate` - active
- `analytics` - active
- `serving` - active
- `reports` - planned/future
- `client_specific` - planned/future

### 15.3 Schema Responsibility Rule
Every schema must have a single dominant purpose. Schema boundaries are a core trust mechanism, not an organizational detail.

---

## 16. dbt Transformation Architecture

### 16.1 Core Transformation Backbone
dbt is the official transformation backbone of the platform.

### 16.2 Active dbt Flow

```text
raw_data -> staging -> intermediate -> analytics -> serving
```

### 16.3 Materialization Philosophy

- `staging` models are materialized as **views**
- `intermediate` models are materialized as **tables**
- `analytics` models are materialized as **tables**
- `serving` models are materialized as **tables**

### 16.4 dbt Responsibility Rule
dbt is responsible for:

- type-safe transformation,
- naming standardization,
- business logic layering,
- reusable model logic,
- tests,
- documentation,
- lineage visibility,
- curated output definition.

### 16.5 dbt Boundary Rule
dbt must not be used to hide source limitations. Model logic must remain explainable and aligned with each layer’s responsibility.

---

## 17. Staging Layer Rules

### 17.1 Staging Purpose
The staging layer standardizes raw sources into usable relational forms while staying close to source meaning.

### 17.2 Implemented Staging Models

- `stg_customer_personality`
- `stg_ecommerce_churn`
- `stg_online_retail`
- `stg_retailrocket_category_tree`
- `stg_retailrocket_events`
- `stg_retailrocket_item_properties`

### 17.3 What Staging Must Do

- rename columns consistently,
- cast raw text-heavy values into usable types,
- normalize basic source inconsistencies,
- preserve source-level semantics,
- expose clean source-shaped relations.

### 17.4 What Staging Must Not Do

- perform wide analytical aggregation,
- create final business KPIs,
- mix unrelated grains for convenience,
- behave like a reporting layer.

---

## 18. Intermediate Layer Rules

### 18.1 Intermediate Purpose
The intermediate layer creates reusable transformation building blocks and controlled joins.

### 18.2 Implemented Intermediate Models

- `int_customer_profile`
- `int_online_retail_customer_summary`
- `int_retailrocket_event_summary`
- `int_retailrocket_latest_item_properties`
- `int_customer_behavior`
- `int_product_analysis`

### 18.3 What Intermediate Must Do

- combine staging models in controlled ways,
- prepare reusable customer-level or product-level transformation logic,
- create stable inputs for analytics and serving layers,
- isolate complex transformation logic away from final marts.

### 18.4 Intermediate Grain Rule
Every intermediate model must have a clearly explainable grain and join logic.

### 18.5 Join Honesty Rule
If a join is analytical rather than operationally native, the model must still remain documented honestly and consistently.

---

## 19. Analytics Layer Rules

### 19.1 Analytics Purpose
The analytics layer produces trusted business-facing marts and summary outputs.

### 19.2 Implemented Analytics Models

- `analytics_customer_segments`
- `analytics_sales_analytics`
- `analytics_product_performance`
- `analytics_business_intelligence`

### 19.3 What Analytics Must Do

- expose stable aggregated outputs,
- support BI and dashboard consumption,
- package metrics and segment-level interpretations,
- remain business-readable.

### 19.4 What Analytics Must Not Do

- behave like raw staging cleanup,
- carry unvalidated final ML labels as hidden logic,
- bypass intermediate logic to create fragile marts.

### 19.5 Consumption Rule
Business dashboards should prefer this layer unless a downstream use case explicitly requires a serving-layer product.

---

## 20. Serving Layer Rules

### 20.1 Serving Purpose
The serving layer exposes curated customer-level data products intended for stable downstream reuse.

### 20.2 Implemented Serving Models

- `customer_360`
- `segmentation_feature_base`
- `churn_feature_base`
- `ltv_feature_base`
- `persona_base`
- `marketing_recommendation_base`

### 20.3 Serving Layer Interpretation
For this project, the serving layer acts as:

- a curated customer-product layer,
- a future API-facing layer,
- a future MLOps-ready layer,
- a bridge between analytics engineering and downstream intelligent use cases.

### 20.4 What Serving Must Do

- centralize trusted customer-level outputs,
- package validated features and labels,
- support future experimentation or service layers,
- stay stable enough for downstream consumers.

### 20.5 What Serving Must Not Do

- bypass testing and validation,
- replace analytics marts for ordinary BI usage,
- hide unclear label-generation logic,
- serve as a dumping ground for unrelated features.

---

## 21. dbt Project Assets and Standards

### 21.1 Key dbt Configuration Files

- `src/ELT/client_1/dbt/dbt_project.yml`
- `src/ELT/client_1/dbt/profiles.yml`
- `src/ELT/client_1/dbt/docs/project_overview.md`

### 21.2 Key Model Metadata Files

- `models/staging/sources.yml`
- `models/staging/staging_models.yml`
- `models/intermediate/intermediate_models.yml`
- `models/analytics/analytics_models.yml`
- `models/analytics/exposures.yml`
- `models/serving/serving_models.yml`
- `models/serving/churn_feature_base.yml`
- `models/serving/ltv_feature_base.yml`
- `models/serving/persona_base.yml`
- `models/serving/segmentation_feature_base.yml`
- `models/serving/marketing_recommendation_base.yml`

### 21.3 Naming Rule
Model names must clearly indicate their layer and purpose.

### 21.4 Documentation Rule
All major curated models must be documented sufficiently for lineage inspection and explainable downstream reuse.

---

## 22. Testing and Quality Rules

### 22.1 dbt Testing Rule
dbt tests verify structural integrity of warehouse models and must pass before curated outputs are considered stable.

### 22.2 Great Expectations Rule
Great Expectations complements dbt by validating dataset-level contracts and downstream-readiness conditions that go beyond simple model builds.

### 22.3 Trust Rule
A model that builds successfully is not automatically trustworthy. Trust requires:

- successful build,
- passing dbt tests,
- relevant Great Expectations success,
- explainable layer logic,
- observable execution state.

---

## 23. Great Expectations Quality Layer

### 23.1 Great Expectations Purpose
Great Expectations exists to validate:

- raw source contracts,
- analytics consistency,
- serving-layer readiness,
- downstream ML-readiness conditions.

### 23.2 Key Great Expectations Files

- `src/ELT/client_1/great_expectations/bootstrap_gx.py`
- `src/ELT/client_1/great_expectations/run_gx_validations.py`
- `src/ELT/client_1/great_expectations/gx_config.py`
- `src/ELT/client_1/great_expectations/gx_suite_definitions.py`
- `src/ELT/client_1/great_expectations/README.md`
- `src/ELT/client_1/great_expectations/gx/great_expectations.yml`

### 23.3 Implemented Checkpoints

- `raw_data_quality_checkpoint`
- `analytics_data_quality_checkpoint`
- `serving_data_quality_checkpoint`
- `ml_feature_readiness_checkpoint`

### 23.4 Great Expectations Separation Rule

- dbt controls transformation logic and model tests,
- Great Expectations validates dataset contracts and readiness conditions,
- Airflow orchestrates when each checkpoint runs.

---

## 24. Orchestration Rules

### 24.1 Orchestration Principle
The platform must not depend on ad hoc manual end-to-end execution as its intended operating mode.

### 24.2 Active Airflow DAGs
The implemented Client 1 orchestration layer currently uses three active DAGs:

1. `customerdna_client1_dw_setup_pipeline`
2. `customerdna_client1_raw_load_pipeline`
3. `customerdna_client1_transformation_quality_pipeline`

### 24.3 DAG Responsibilities

#### `customerdna_client1_dw_setup_pipeline`
Responsible for:

- warehouse setup,
- schema creation,
- base-table creation,
- metadata table readiness.

#### `customerdna_client1_raw_load_pipeline`
Responsible for:

- running the Kafka raw pipeline,
- resetting topics/artifacts for clean reruns,
- producing and loading all source datasets into `raw_data`,
- bootstrapping Great Expectations,
- validating raw-layer quality.

#### `customerdna_client1_transformation_quality_pipeline`
Responsible for:

- running all dbt models,
- bootstrapping Great Expectations after transformed layers exist,
- running dbt tests,
- validating analytics quality,
- validating serving quality,
- validating ML-readiness conditions.

### 24.4 Execution Order Rule
The official full reset-and-run order is:

1. `customerdna_client1_dw_setup_pipeline`
2. `customerdna_client1_raw_load_pipeline`
3. `customerdna_client1_transformation_quality_pipeline`

### 24.5 Orchestration Design Rule
Splitting the pipeline by responsibility is intentional because it improves:

- rerun control,
- debugging,
- restartability,
- auditability,
- operational explanation during presentation and deployment.

---

## 25. Monitoring and Observability Rules

### 25.1 Monitoring Purpose
The monitoring layer provides visibility into both infrastructure and pipeline behavior.

### 25.2 Active Monitoring Components

- Prometheus
- Grafana
- PostgreSQL exporter
- cAdvisor metrics
- custom pipeline metrics exporter
- script-generated monitoring state files

### 25.3 Key Monitoring Files

- `src/monitoring/README.md`
- `src/monitoring/exporters/pipeline_metrics_exporter.py`
- `src/monitoring/shared/pipeline_metrics.py`
- `src/monitoring/prometheus/docker-compose.yml`
- `src/monitoring/prometheus/prometheus.yml`
- `src/monitoring/prometheus/README.md`
- `src/monitoring/grafana/docker-compose.yml`
- `src/monitoring/grafana/provisioning/datasources/prometheus.yml`
- `src/monitoring/grafana/provisioning/dashboards/customerdna.yml`
- `src/monitoring/grafana/dashboards/customerdna_infrastructure.dashboard.json`
- `src/monitoring/grafana/dashboards/customerdna_postgres.dashboard.json`
- `src/monitoring/grafana/dashboards/customerdna_pipeline_health.dashboard.json`

### 25.4 State Files
The monitoring layer currently uses state artifacts such as:

- `src/monitoring/state/airflow_pipeline_state.json`
- `src/monitoring/state/gx_state.json`
- `src/monitoring/state/ingestion_state.json`

### 25.5 Monitoring Rule
Monitoring is not optional decoration. It is part of platform trust because it proves the system is operable, inspectable, and defendable.

---

## 26. Dashboard and API Consumption Rules

### 26.1 Dashboard Rule
Dashboards should read curated outputs, not raw engineering layers.

### 26.2 API Rule
A future API should expose curated analytics or serving outputs depending on business need, never raw warehouse tables directly.

### 26.3 Consumption Boundary Rule
Operational monitoring dashboards and business analytics dashboards must remain conceptually separate even if both are visible in Grafana or future reporting layers.

---

## 27. Local Downstream ML Experimentation Layer

### 27.1 Current Status
Local downstream ML experimentation has been implemented for Client 1, but it remains secondary to the Data Engineering identity of the platform.

### 27.2 ML Dependency Rule
Every ML workflow must depend on validated serving-layer outputs rather than bypassing the warehouse architecture.

### 27.3 Current Implemented Local ML Use Cases

- segmentation clustering
- churn classification
- LTV regression
- persona classification
- marketing recommendation classification

### 27.4 Current Local ML Workflow
The implemented local ML workflow currently includes:

1. extract serving snapshots,
2. audit snapshots,
3. preprocess features,
4. train baseline models,
5. interpret predictions or clusters,
6. generate ML EDA reports and plots.

### 27.5 ML Positioning Rule
These workflows prove that the serving layer is reusable and downstream-ready. They do not change the platform’s primary Data Engineering positioning.

---

## 28. Dataset-Specific EDA Rules

### 28.1 ELT-Facing EDA
The project includes maximum EDA scripts for the main source datasets under:

- `src/ELT/client_1/EDA/Customer_Personality_Analysis/scripts/customer_personality_max_eda.py`
- `src/ELT/client_1/EDA/E-commerce_Personality_Analysis/scripts/ecommerce_max_eda.py`
- `src/ELT/client_1/EDA/Retailrocket_recommender_system_dataset/scripts/retailrocket_max_eda.py`
- `src/ELT/client_1/EDA/UCI_Online_Retail_II/scripts/online_retail_max_eda.py`

### 28.2 ML-Facing EDA
The project also includes ML-oriented EDA scripts under:

- `src/ML/client_1/eda/scripts/run_segmentation_eda.py`
- `src/ML/client_1/eda/scripts/run_churn_eda.py`
- `src/ML/client_1/eda/scripts/run_ltv_eda.py`
- `src/ML/client_1/eda/scripts/run_persona_eda.py`
- `src/ML/client_1/eda/scripts/run_marketing_recommendation_eda.py`

### 28.3 EDA Rule
EDA exists to improve understanding and explainability. It must not replace formal transformation and validation logic.

---

## 29. Current Client 1 Implementation Status

### 29.1 Implemented Components

- warehouse setup automation,
- Kafka ingestion and raw loading backbone,
- raw source preservation in PostgreSQL,
- metadata tracking,
- dbt staging layer,
- dbt intermediate layer,
- dbt analytics layer,
- dbt serving layer,
- dbt docs and tests,
- Great Expectations validation across raw, analytics, serving, and ML-readiness scopes,
- split Airflow DAG orchestration,
- Prometheus-based monitoring,
- Grafana dashboards,
- Kafka UI,
- local downstream ML experimentation assets.

### 29.2 Key Technical Achievements

- Clear separation between ingestion, loading, transformation, validation, orchestration, and monitoring.
- Kafka now serves as the official ingestion/raw-load backbone.
- Three-DAG Airflow architecture provides controlled rerun order.
- dbt serving layer exposes reusable customer-level data products.
- Great Expectations now validates not only raw and analytics but also serving and ML-readiness conditions.
- Prometheus and Grafana make the platform operationally inspectable.
- Legacy ingestion was retired cleanly without losing rollback capability.

### 29.3 Current Project Structure

The project structure below reflects the active platform and the retained rollback area.

```text
CustomerDNA AI/
|-- datasets/
|   `-- client_1/
|       |-- Customer_Personality_Analysis/
|       |   `-- marketing_campaign.csv
|       |-- E-commerce_customer_churn/
|       |   `-- E-commerce_customer_churn.xlsx
|       |-- Retailrocket_recommender_system_dataset/
|       |   |-- category_tree.csv
|       |   |-- events.csv
|       |   |-- item_properties_part1.csv
|       |   `-- item_properties_part2.csv
|       `-- UCI_Online_Retail_2/
|           `-- online_retail_2.xlsx
|
|-- project_presentation/
|-- project_requirements/
|   |-- BUSINESS_RULES.md
|   |-- BUSINESS_RULES_PFE_REPORT.md
|   `-- initial_project_description.txt
|
`-- src/
    |-- airflow/
    |   |-- docker-compose.yml
    |   |-- requirements.txt
    |   `-- dags/
    |       `-- client_1/
    |           |-- __init__.py
    |           |-- customerdna_client1_dag_common.py
    |           |-- customerdna_client1_dw_setup_dag.py
    |           |-- customerdna_client1_raw_load_dag.py
    |           `-- customerdna_client1_transformation_quality_dag.py
    |
    |-- ELT/
    |   `-- client_1/
    |       |-- config/
    |       |   `-- config.py
    |       |-- setup_dw/
    |       |   |-- setup_dw.py
    |       |   `-- create_base_tables.py
    |       |-- great_expectations/
    |       |   |-- README.md
    |       |   |-- bootstrap_gx.py
    |       |   |-- gx_config.py
    |       |   |-- gx_suite_definitions.py
    |       |   |-- run_gx_validations.py
    |       |   `-- gx/
    |       |       |-- great_expectations.yml
    |       |       `-- plugins/
    |       |           `-- custom_data_docs/
    |       |               `-- styles/
    |       |                   `-- data_docs_custom_styles.css
    |       |-- dbt/
    |       |   |-- dbt_project.yml
    |       |   |-- profiles.yml
    |       |   |-- docs/
    |       |   |   `-- project_overview.md
    |       |   `-- models/
    |       |       |-- staging/
    |       |       |   |-- sources.yml
    |       |       |   `-- staging_models.yml
    |       |       |-- intermediate/
    |       |       |   `-- intermediate_models.yml
    |       |       |-- analytics/
    |       |       |   |-- analytics_models.yml
    |       |       |   `-- exposures.yml
    |       |       `-- serving/
    |       |           |-- serving_models.yml
    |       |           |-- churn_feature_base.yml
    |       |           |-- ltv_feature_base.yml
    |       |           |-- marketing_recommendation_base.yml
    |       |           |-- persona_base.yml
    |       |           `-- segmentation_feature_base.yml
    |       |-- EDA/
    |       |   |-- Customer_Personality_Analysis/
    |       |   |   |-- scripts/
    |       |   |   |   `-- customer_personality_max_eda.py
    |       |   |   `-- output/
    |       |   |-- E-commerce_Personality_Analysis/
    |       |   |   |-- scripts/
    |       |   |   |   `-- ecommerce_max_eda.py
    |       |   |   `-- output/
    |       |   |-- Retailrocket_recommender_system_dataset/
    |       |   |   |-- scripts/
    |       |   |   |   `-- retailrocket_max_eda.py
    |       |   |   `-- output/
    |       |   `-- UCI_Online_Retail_II/
    |       |       |-- scripts/
    |       |       |   `-- online_retail_max_eda.py
    |       |       `-- output/
    |       `-- verfiy_dw.py
    |
    |-- monitoring/
    |   |-- README.md
    |   |-- exporters/
    |   |   `-- pipeline_metrics_exporter.py
    |   |-- grafana/
    |   |   |-- docker-compose.yml
    |   |   |-- dashboards/
    |   |   |   |-- README.md
    |   |   |   |-- customerdna_infrastructure.dashboard.json
    |   |   |   |-- customerdna_pipeline_health.dashboard.json
    |   |   |   `-- customerdna_postgres.dashboard.json
    |   |   `-- provisioning/
    |   |       |-- dashboards/
    |   |       |   `-- customerdna.yml
    |   |       `-- datasources/
    |   |           `-- prometheus.yml
    |   |-- prometheus/
    |   |   |-- .env
    |   |   |-- README.md
    |   |   |-- docker-compose.yml
    |   |   `-- prometheus.yml
    |   |-- shared/
    |   |   |-- __init__.py
    |   |   `-- pipeline_metrics.py
    |   `-- state/
    |       |-- .gitkeep
    |       |-- airflow_pipeline_state.json
    |       |-- gx_state.json
    |       `-- ingestion_state.json
    |
    |-- streaming/
    |   `-- kafka/
    |       |-- docker-compose.yml
    |       |-- requirements.txt
    |       `-- client_1/
    |           |-- __init__.py
    |           |-- reset_client1_kafka.py
    |           |-- run_client1_kafka_raw_pipeline.py
    |           |-- common/
    |           |   |-- __init__.py
    |           |   |-- dataset_producer.py
    |           |   |-- kafka_config.py
    |           |   |-- producer_utils.py
    |           |   `-- source_row_iterators.py
    |           |-- marketing_campaign/
    |           |   |-- __init__.py
    |           |   |-- consume.py
    |           |   |-- load_to_raw.py
    |           |   `-- produce.py
    |           |-- ecommerce_customer_churn/
    |           |   |-- __init__.py
    |           |   |-- consume.py
    |           |   |-- load_to_raw.py
    |           |   `-- produce.py
    |           |-- retailrocket_category_tree/
    |           |   |-- __init__.py
    |           |   |-- consume.py
    |           |   |-- load_to_raw.py
    |           |   `-- produce.py
    |           |-- retailrocket_events/
    |           |   |-- __init__.py
    |           |   |-- consume.py
    |           |   |-- load_to_raw.py
    |           |   `-- produce.py
    |           |-- retailrocket_item_properties/
    |           |   |-- __init__.py
    |           |   |-- consume.py
    |           |   |-- load_to_raw.py
    |           |   `-- produce.py
    |           `-- online_retail/
    |               |-- __init__.py
    |               |-- consume.py
    |               |-- load_to_raw.py
    |               `-- produce.py
    |
    `-- ML/
        `-- client_1/
            |-- README.md
            |-- configs/
            |-- datasets/
            |-- data_access/
            |   |-- audit_serving_snapshot.py
            |   |-- extract_serving_data.py
            |   `-- schema_manifest.py
            |-- preprocessing/
            |   |-- prepare_segmentation_features.py
            |   |-- prepare_churn_features.py
            |   |-- prepare_ltv_features.py
            |   |-- prepare_persona_features.py
            |   `-- prepare_marketing_recommendation_features.py
            |-- training/
            |   |-- train_segmentation_clusters.py
            |   |-- train_churn_classifier.py
            |   |-- train_ltv_regressor.py
            |   |-- train_persona_classifier.py
            |   `-- train_marketing_recommendation_classifier.py
            |-- inference/
            |   |-- interpret_segmentation_clusters.py
            |   |-- interpret_churn_predictions.py
            |   |-- interpret_ltv_predictions.py
            |   |-- interpret_persona_predictions.py
            |   `-- interpret_marketing_recommendation_predictions.py
            |-- eda/
            |   |-- README.md
            |   |-- scripts/
            |   |   |-- eda_common.py
            |   |   |-- run_segmentation_eda.py
            |   |   |-- run_churn_eda.py
            |   |   |-- run_ltv_eda.py
            |   |   |-- run_persona_eda.py
            |   |   `-- run_marketing_recommendation_eda.py
            |   |-- plots/
            |   `-- reports/
            |-- models/
            |   |-- model_metadata/
            |   |-- preprocessors/
            |   `-- saved_models/
            `-- reports/
                |-- business_summaries/
                `-- experiment_reports/
```

### 29.4 Structure Rule
The active project structure must clearly separate:

- source data,
- streaming ingestion,
- warehouse logic,
- orchestration,
- monitoring,
- downstream experimentation.

---

## 30. Expected Outcomes

### 30.1 Technical Outcomes

- reliable source-to-warehouse loading,
- explicit warehouse schema boundaries,
- documented and tested transformation logic,
- validated analytics and serving products,
- inspectable orchestration,
- observable platform runtime behavior,
- reusable project structure for future clients.

### 30.2 Business-Facing Outcomes

- stronger trust in analytics outputs,
- clearer customer-level data products,
- better readiness for future predictive applications,
- easier explanation of data lineage to stakeholders.

### 30.3 PFE Value Outcomes

- a defendable end-to-end data-engineering architecture,
- clear separation of concerns,
- operational maturity beyond basic ETL scripting,
- strong basis for deployment and future extension.

---

## 31. Immediate Next Steps

The most logical next steps after the current implemented state are:

1. validate the complete platform repeatedly under full reruns,
2. continue refining monitoring thresholds and pipeline-health interpretation,
3. optimize large-volume raw loading performance where justified,
4. prepare deployment packaging for a company-owned server environment,
5. decide whether future orchestration should include optional downstream ML refresh flows or keep them separate.

---

## 32. Future Roadmap

### 32.1 Near-Term Roadmap

- harden Kafka operational practices,
- expand monitoring and alerting,
- refine raw-load performance for the largest datasets,
- document deployment and operations procedures in more detail.

### 32.2 Medium-Term Roadmap

- onboard more clients,
- expose curated outputs via API,
- enrich business dashboards,
- formalize broader governance and benchmarking rules.

### 32.3 Long-Term Roadmap

- cross-client standardization,
- global benchmarking layer,
- enterprise AI/ML lifecycle automation,
- broader data-product platform capabilities.

---

## 33. Final Business Rules Summary

The most important final rules are:

1. **Kafka is the official Client 1 ingestion and raw-loading backbone.**
2. **Raw data must preserve source identity and must not become a business layer.**
3. **dbt is the official transformation backbone from `staging` through `serving`.**
4. **Analytics outputs must come from validated curated layers, not direct raw access.**
5. **Serving outputs are curated customer-level data products for downstream reuse.**
6. **dbt tests and Great Expectations are both required parts of trust.**
7. **Airflow must orchestrate the platform in the order: setup -> raw load -> transformation-quality.**
8. **Prometheus and Grafana are part of the platform, not optional extras.**
9. **Retired ingestion paths must not return as active architecture without an explicit redesign decision.**
10. **The platform must be presented primarily as a Data Engineering system, with AI/ML as downstream capability.**

---

## 34. Document History

| Version | Date | Change |
|---|---|---|
| 13.0 | 2026-06-29 | Updated the document to reflect split Airflow DAG orchestration, metadata-aware raw loading, and the earlier monitoring additions. |
| 13.1 | 2026-07-01 | Documented centralized monitoring under `src/monitoring`, the custom pipeline exporter, and provisioned Grafana dashboards. |
| 13.3 | 2026-07-02 | Added the implemented `serving` schema and the serving-layer customer products. |
| 13.4 | 2026-07-03 | Expanded Great Expectations coverage to serving and ML-readiness validation. |
| 14.0 | 2026-07-04 | Added the implemented local ML experimentation layer and ML EDA workflow. |
| 15.0 | 2026-07-08 | Rewrote the document to align with the finalized Kafka-first ingestion architecture, the active three-DAG Airflow flow, the centralized monitoring stack, the current project structure, and the final Data Engineering-first project positioning. |
