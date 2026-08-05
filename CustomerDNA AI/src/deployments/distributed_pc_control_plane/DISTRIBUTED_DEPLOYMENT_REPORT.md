# CustomerDNA AI - Distributed Deployment Report

> Deployment scope: `src/deployments/distributed_pc_control_plane/`
> Version: deployed architecture baseline
> Date: 2026-08-04
> Audience: project owner, jury preparation, technical reviewers, future maintainers

---

## 1. Purpose of This Document

This file explains the **final distributed deployed version** of CustomerDNA AI.

It is intended to be the detailed reference for:

- the deployment architecture,
- node responsibilities,
- execution model,
- service interactions,
- network endpoints,
- deployment workflow,
- runtime verification,
- operational boundaries,
- and design tradeoffs.

This document is about the **deployed distributed version**, not the older local-only baseline.

---

## 2. Deployment Objective

The goal of this deployment is to demonstrate that CustomerDNA AI is not only a logically distributed lakehouse architecture, but also an **operationally distributed implementation**.

This deployment proves:

- distributed ingestion through a Kafka cluster,
- distributed storage through HDFS,
- distributed processing through Spark workers on multiple machines,
- distributed query execution through Trino coordinator/worker separation,
- centralized orchestration through Airflow on the local control plane,
- centralized monitoring through Prometheus and Grafana,
- and isolated per-node deployment bundles for maintainability.

This environment is a **distributed demo and validation environment**, not a production HA cluster.

---

## 3. Deployment Philosophy

This deployment follows five design principles.

### 3.1 Isolation by node

Each node has its own self-contained deployment folder so it can be:

- edited independently,
- zipped independently,
- uploaded independently,
- redeployed independently,
- and debugged independently.

### 3.2 Local control, remote data plane

The local workstation keeps orchestration and supervision responsibilities, while the VMs host the distributed data services.

### 3.3 Lightweight VMs

The VMs were prepared by the IT administrator and cannot be resized from inside the project scope.

Therefore the deployment is intentionally adapted to:

- low memory,
- limited disk,
- small executor footprints,
- and minimal service duplication.

### 3.4 Demonstration of distribution over production hardening

The purpose is to demonstrate the distributed concept correctly:

- cluster-based ingestion,
- cluster-based storage,
- cluster-based processing,
- cluster-based query execution.

This matters more here than implementing full enterprise-grade production hardening.

### 3.5 Maintainability over cleverness

The deployment avoids hidden automation chains spread across the whole repository.

Instead it uses:

- explicit bundles,
- explicit scripts,
- explicit env files,
- explicit preflight checks,
- and explicit reset/start commands.

---

## 4. High-Level Architecture

The final deployed architecture is:

```text
Local PC (control plane)
  -> Airflow
  -> Prometheus
  -> Grafana
  -> Kafka UI
  -> pipeline metrics exporter
  -> remote Spark orchestration over SSH

VM1 + VM2 + VM3 (distributed data plane)
  -> Kafka cluster
  -> HDFS cluster
  -> Spark cluster
  -> Hive Metastore
  -> Trino cluster
  -> cAdvisor exporters
```

End-to-end data flow:

```text
datasets
  -> Kafka topics
  -> HDFS bronze landing
  -> Spark raw load to Iceberg
  -> Hive Metastore registration
  -> Trino SQL access
  -> dbt-spark curated models
  -> Great Expectations validation
  -> Airflow orchestration
  -> Prometheus/Grafana observability
```

---

## 5. Cluster Topology

### 5.1 Control Plane PC

Host type:

- local workstation

Main role:

- orchestration and observability

Responsibilities:

- Airflow API server
- Airflow scheduler
- Airflow DAG processor
- Airflow triggerer
- Airflow initialization
- Airflow PostgreSQL
- Prometheus
- Grafana
- Kafka UI
- pipeline metrics exporter
- PostgreSQL exporter
- Great Expectations runtime
- dbt runtime
- remote Spark orchestration toward VM2 through SSH

### 5.2 VM1

IP address:

- `10.10.252.11`

Main role:

- worker node

Responsibilities:

- Kafka broker 1
- HDFS DataNode 1
- Spark worker 1
- Trino worker 1
- cAdvisor

### 5.3 VM2

IP address:

- `10.10.252.12`

Main role:

- leader node of the data plane

Responsibilities:

- Kafka broker 2
- HDFS NameNode
- HDFS DataNode 2
- Hive Metastore PostgreSQL
- Hive Metastore
- Spark master
- Spark submit helper
- Spark worker 2
- Spark history server
- Spark Thrift server
- Trino coordinator
- cAdvisor

### 5.4 VM3

IP address:

- `10.10.252.13`

Main role:

- worker node

Responsibilities:

- Kafka broker 3
- HDFS DataNode 3
- Spark worker 3
- Trino worker 2
- cAdvisor

---

## 6. Why This Placement Was Chosen

### 6.1 Why the control plane stays local

Keeping the control plane on the local PC avoids overloading the VMs with:

- orchestration,
- dashboards,
- monitoring stack,
- and local admin tooling.

It also gives easier access during demos for:

- Airflow,
- Prometheus,
- Grafana,
- Kafka UI.

### 6.2 Why VM2 is the leader node

VM2 hosts the coordination-heavy services because the architecture needs one clear integration point for:

- HDFS namespace authority,
- metastore authority,
- Spark master,
- Trino coordinator,
- Spark Thrift,
- and remote Spark submission.

### 6.3 Why VM1 and VM3 are workers

VM1 and VM3 mainly extend the cluster by providing:

- extra Kafka broker capacity,
- extra HDFS block storage,
- extra Spark executor capacity,
- extra Trino distributed worker capacity.

This creates the actual distributed behavior that the project must demonstrate.

---

## 7. Repository Layout of This Deployment Folder

```text
distributed_pc_control_plane/
|-- README.md
|-- CLUSTER_ACCESS_POINTS.txt
|-- DISTRIBUTED_DEPLOYMENT_REPORT.md
|-- shared/
|-- control_plane_pc/
|-- vm1/
|-- vm2/
`-- vm3/
```

### 7.1 Root files

- `README.md`
  - short summary of the deployment generation
- `CLUSTER_ACCESS_POINTS.txt`
  - verified URLs and service endpoints for operations and demos
- `DISTRIBUTED_DEPLOYMENT_REPORT.md`
  - this detailed explanation document

### 7.2 `shared/`

This folder contains the contract for the distributed deployment:

- shared configuration maps,
- shared env templates,
- shared cluster scripts,
- cluster topology truth sources.

Important files:

- `shared/configs/cluster_inventory.yml`
- `shared/configs/service_placement.yml`
- `shared/configs/ports_map.yml`
- `shared/configs/deployment_contract.yml`
- `shared/env/*.env.example`
- `shared/scripts/cluster_preflight_checks.ps1`
- `shared/scripts/cluster_preflight_checks.sh`

### 7.3 `control_plane_pc/`

This folder contains the local orchestration and monitoring deployment.

Important files:

- `.env` / `.env.example`
- `docker-compose.yml`
- `control_plane_preflight_checks.ps1`
- `start_control_plane_pc.ps1`
- `reset_control_plane_state.ps1`

### 7.4 `vm1/`, `vm2/`, `vm3/`

Each VM folder contains everything needed to:

- prepare a fresh VM,
- validate prerequisites,
- start services,
- reset local runtime state,
- and build/upload a portable deployment bundle.

Important common files per VM:

- `.env`
- `.env.example`
- `docker-compose.yml`
- `prepare_fresh_vm*.sh`
- `vm*_preflight_checks.sh`
- `start_vm*_stack.sh`
- `reset_vm*_state.sh`
- `manage_vm*_bundle.py`
- `VM_config.txt`

---

## 8. Execution Model

This deployed version uses a **split execution model**.

### 8.1 Airflow execution

Airflow runs locally on the control plane.

It triggers:

- Kafka reset/setup logic,
- HDFS reset/setup logic,
- Trino namespace setup logic,
- Spark raw-load orchestration,
- dbt execution,
- Great Expectations execution,
- validation checks,
- metrics state updates.

### 8.2 Spark raw-load execution

Spark raw loading is submitted **remotely to VM2**.

The control plane does not run a local Spark driver service for raw loading anymore.

Instead:

- Airflow connects to VM2 through SSH,
- the Spark submit helper on VM2 is used,
- the Spark master on VM2 schedules work across the cluster workers.

This was chosen to avoid instability caused by dynamic local-PC networking during remote executor-to-driver communication.

### 8.3 dbt execution

dbt runs from the control plane but connects to:

- Spark Thrift Server on VM2.

So dbt logic is controlled locally, while execution happens against the distributed Spark lakehouse environment.

### 8.4 Great Expectations execution

Great Expectations also runs from the control plane and validates against the remote lakehouse endpoints.

---

## 9. Service-by-Service Role Map

### 9.1 Kafka cluster

Role:

- distributed ingestion transport

Placement:

- broker 1 on VM1
- broker 2 on VM2
- broker 3 on VM3

Purpose:

- topic-based transport of active Client 1 datasets
- decoupling of source reading and raw persistence
- replayable ingestion

### 9.2 HDFS cluster

Role:

- distributed bronze storage

Placement:

- NameNode on VM2
- DataNodes on VM1, VM2, VM3

Purpose:

- store bronze raw landed files
- distribute data blocks across nodes
- make replayable raw persistence independent from source files

### 9.3 Spark cluster

Role:

- distributed compute

Placement:

- master on VM2
- workers on VM1, VM2, VM3
- history server on VM2
- Thrift server on VM2
- submit helper on VM2

Purpose:

- raw load from HDFS bronze to Iceberg
- remote job submission
- distributed execution of Spark applications
- SQL access for dbt through Thrift

### 9.4 Hive Metastore

Role:

- metadata authority

Placement:

- Hive Metastore PostgreSQL on VM2
- Hive Metastore service on VM2

Purpose:

- shared catalog between Spark and Trino
- table discovery
- namespace governance

### 9.5 Trino cluster

Role:

- distributed query layer

Placement:

- coordinator on VM2
- workers on VM1 and VM3

Purpose:

- analytical SQL access over Iceberg tables
- DBeaver / SQL exploration entry point
- validation and demo querying

### 9.6 Monitoring stack

Role:

- observability

Placement:

- Prometheus on control plane
- Grafana on control plane
- cAdvisor on VM1, VM2, VM3
- pipeline metrics exporter on control plane
- postgres exporter on control plane

Purpose:

- infrastructure monitoring
- pipeline-state monitoring
- metastore visibility
- dashboard-based demo evidence

---

## 10. Primary Network Endpoints

### 10.1 Kafka

- VM1 broker: `10.10.252.11:9092`
- VM2 broker: `10.10.252.12:9092`
- VM3 broker: `10.10.252.13:9092`

### 10.2 HDFS

- NameNode RPC: `10.10.252.12:9000`
- NameNode web UI: `http://10.10.252.12:9870`
- VM1 DataNode UI: `http://10.10.252.11:9864`
- VM2 DataNode UI: `http://10.10.252.12:9864`
- VM3 DataNode UI: `http://10.10.252.13:9864`

### 10.3 Hive

- Hive Metastore: `10.10.252.12:9083`
- Hive Metastore PostgreSQL: `10.10.252.12:5435`

### 10.4 Spark

- Spark master: `spark://10.10.252.12:7077`
- Spark master UI: `http://10.10.252.12:8086`
- Spark history UI: `http://10.10.252.12:18080`
- Spark Thrift: `10.10.252.12:10000`
- remote submission SSH target: `10.10.252.12:22`

### 10.5 Trino

- Trino coordinator UI: `http://10.10.252.12:8088/ui/`
- VM1 Trino worker internal endpoint: `http://10.10.252.11:8080`
- VM3 Trino worker internal endpoint: `http://10.10.252.13:8080`

### 10.6 Control plane interfaces

Preferred ports:

- Airflow: `http://localhost:18080`
- Prometheus: `http://localhost:19090`
- Grafana: `http://localhost:13001`
- Kafka UI: `http://localhost:18085`

Important note:

The control-plane startup script may shift those local ports if the preferred values are already busy.

The active resolved values are written to:

- `control_plane_pc/runtime/compose.generated.env`

---

## 11. Control Plane Folder Responsibilities

### 11.1 `control_plane_pc/docker-compose.yml`

Defines:

- Airflow stack,
- Airflow PostgreSQL,
- Prometheus,
- Grafana,
- Kafka UI,
- pipeline metrics exporter,
- PostgreSQL exporter.

### 11.2 `control_plane_preflight_checks.ps1`

Purpose:

- verifies local tools,
- verifies required mounted paths,
- verifies remote service reachability.

### 11.3 `start_control_plane_pc.ps1`

Purpose:

- resolves usable local ports,
- prepares runtime env overrides,
- starts the control plane in the correct order.

### 11.4 `reset_control_plane_state.ps1`

Purpose:

- stops the local control-plane stack,
- removes state that should be rebuilt for a clean restart.

### 11.5 `ssh/`

Purpose:

- stores the SSH key material used by the control plane to reach VM2 for remote Spark orchestration.

Important rule:

- this directory is operationally critical,
- but secret contents must not be copied into reports, screenshots, or version history by mistake.

---

## 12. VM Folder Responsibilities

### 12.1 Common pattern

Each VM folder follows the same operational lifecycle:

1. prepare the VM
2. validate prerequisites
3. start the stack
4. verify endpoints
5. reset only that node when required

### 12.2 `prepare_fresh_vm*.sh`

Purpose:

- install or verify required OS-side dependencies,
- prepare Docker and execution prerequisites,
- prepare the VM for first startup.

### 12.3 `vm*_preflight_checks.sh`

Purpose:

- validate local tools,
- validate critical peer endpoints,
- validate local ports,
- reduce startup surprises.

### 12.4 `start_vm*_stack.sh`

Purpose:

- start the compose-defined services for that node,
- expose the node as part of the distributed data plane.

### 12.5 `reset_vm*_state.sh`

Purpose:

- stop node services,
- clear runtime data,
- prepare a clean redeployment of that node.

### 12.6 `manage_vm*_bundle.py`

Purpose:

- build a portable bundle,
- package the node-specific deployment content,
- support upload/deploy workflow from the workstation.

---

## 13. Distributed Startup Order

The recommended cluster startup order is:

1. VM2
2. VM1
3. VM3
4. control plane

### 13.1 Why VM2 starts first

Because it contains the coordination services:

- NameNode
- Hive Metastore
- Spark master
- Trino coordinator
- Spark Thrift

Other nodes depend on those services being reachable.

### 13.2 Why VM1 and VM3 come next

Because they add:

- Kafka peers,
- HDFS storage peers,
- Spark execution capacity,
- Trino worker capacity.

### 13.3 Why control plane comes last

Because Airflow, monitoring, and UI services should start only after the distributed data plane is reachable and stable.

---

## 14. Pipeline Execution Order After Deployment

After the cluster is up, the Airflow execution order is:

1. `customerdna_client1_environment_reset_pipeline`
2. `customerdna_client1_lakehouse_setup_pipeline`
3. `customerdna_client1_lakehouse_readiness_pipeline`
4. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
5. `customerdna_client1_dbt_spark_lakehouse_pipeline`

This order is the operational contract for a clean end-to-end run.

---

## 15. What Makes This Deployment Truly Distributed

This deployment is not "distributed" only because multiple machines exist.

It is distributed because the core runtime responsibilities are split across nodes in meaningful ways.

### 15.1 Distributed ingestion

Kafka quorum spans VM1, VM2, and VM3.

### 15.2 Distributed storage

HDFS stores data across DataNodes on VM1, VM2, and VM3, with namespace control on VM2.

### 15.3 Distributed processing

Spark applications are scheduled by the master and can allocate executors across workers on VM1, VM2, and VM3.

### 15.4 Distributed querying

Trino uses a coordinator/worker model with worker nodes separated from the coordinator.

### 15.5 Centralized control

Airflow remains centralized on the control plane, which is a valid and common orchestration pattern.

---

## 16. Observability Model

The deployed version has two observability levels.

### 16.1 Infrastructure-level observability

Provided by:

- cAdvisor on each VM
- Prometheus scraping
- Grafana infrastructure dashboard

This shows:

- container health,
- CPU usage,
- memory usage,
- node reachability.

### 16.2 Pipeline-level observability

Provided by:

- pipeline metrics exporter
- Airflow run/task history
- Grafana pipeline health dashboard

This shows:

- DAG success/failure,
- freshness indicators,
- validation status,
- and lakehouse readiness signals.

---

## 17. Deployment Workflow Used by This Project

The operational workflow is:

1. prepare the node folder locally
2. build or refresh the node bundle
3. upload the bundle to the VM
4. extract it into the target folder
5. run fresh-VM preparation if needed
6. run preflight checks
7. start the stack
8. verify the endpoints
9. start the Airflow DAG chain from the control plane

This workflow is intentionally explicit and reproducible.

---

## 18. Validation and Evidence Checklist

The deployed version should be considered healthy only when the following are true.

### 18.1 Cluster service health

- Kafka brokers reachable on all three VMs
- HDFS NameNode reachable
- HDFS DataNodes registered
- Hive Metastore reachable
- Spark master reachable
- Spark Thrift reachable
- Trino coordinator reachable
- cAdvisor reachable on all three VMs

### 18.2 Control plane health

- Airflow UI reachable
- Prometheus UI reachable
- Grafana UI reachable
- Kafka UI reachable

### 18.3 Pipeline evidence

- all five DAGs succeed
- raw Iceberg tables visible in Trino
- dbt analytical tables visible in Trino
- GX validations succeed
- Data Docs HTML is generated
- Grafana dashboards show fresh distributed metrics

### 18.4 Distributed proof

The strongest proof of distribution is:

- HDFS shows multiple live DataNodes
- Spark master shows workers from VM1, VM2, and VM3
- Trino cluster shows coordinator plus workers
- Kafka UI shows the broker cluster

---

## 19. Operational Constraints

This deployment has known constraints.

### 19.1 Fixed VM specifications

The VM hardware is fixed by the IT administrator.

Therefore:

- memory is limited,
- disk is limited,
- aggressive resource settings are unsafe.

### 19.2 Demo-first sizing

The cluster demonstrates distribution correctly, but it is not intended for large production-scale datasets.

### 19.3 Disk pressure

Because HDFS, Spark logs, Docker layers, and runtime volumes all consume disk, cleanup discipline matters.

### 19.4 Control-plane local dependency

The orchestration UX depends on the local PC being available because:

- Airflow is local,
- monitoring dashboards are local,
- Kafka UI is local.

---

## 20. Security Positioning for This Deployment

For documentation and jury framing, this deployed version can be presented as including baseline deployment security measures.

Security here should be understood as:

- controlled node separation,
- limited service placement,
- remote submission through explicit SSH credentials,
- centralized access through known UIs and endpoints,
- environment-scoped configuration,
- and role separation between orchestration and data-plane execution.

This document does not expose secrets and must not be used to publish any private key content.

---

## 21. What This Deployment Does Not Try to Be

This deployed version is not trying to be:

- a production Kubernetes platform,
- a full HA disaster-recovery cluster,
- a zero-trust enterprise security architecture,
- or a massive data-volume benchmark environment.

It is trying to be:

- correct,
- explainable,
- reproducible,
- distributed,
- and defensible for the PFE.

---

## 22. Why This Deployment Is Strong for the Jury

This deployment is strong because it proves that the project is not only a collection of data tools on one laptop.

It demonstrates:

- real node separation,
- real cluster services,
- real orchestration,
- real monitoring,
- real end-to-end execution,
- and real lakehouse behavior.

That makes the final project much more defensible as a serious Data Engineering and Big Data implementation.

---

## 23. Final Summary

The distributed deployment under `src/deployments/distributed_pc_control_plane/` is the final operational form of CustomerDNA AI for the PFE.

It consists of:

- a **local control plane** for orchestration and observability,
- a **three-VM data plane** for ingestion, storage, processing, and querying,
- isolated per-node bundles for maintainability,
- and an execution model designed around correctness, distribution, and constrained infrastructure.

In practical terms, this folder is the bridge between:

- the project architecture on paper,
- and the actual deployed system that can be shown, tested, explained, and defended.

