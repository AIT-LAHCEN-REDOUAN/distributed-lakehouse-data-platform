# AdOptimizer CDP - Distributed Deployment Report

> Deployment scope: `src/deployments/distributed_pc_control_plane/`
> Version: secured distributed deployment baseline with stabilized Kerberos, browser access path, and hardened remote Spark orchestration
> Date: Wednesday, August 12, 2026
> Audience: project owner, jury preparation, technical reviewers, future maintainers

---

## 1. Purpose of This Document

This file explains the **final distributed deployed version** of AdOptimizer CDP after the security-layer extension.

It is intended to be the detailed reference for:

- the deployment architecture,
- node responsibilities,
- execution model,
- service interactions,
- network endpoints,
- implemented security controls,
- deployment workflow,
- runtime verification,
- operational boundaries,
- known limitations,
- and design tradeoffs.

This document is about the **deployed distributed version**, not the older local-only baseline.

For automated report-generation workflows, this file is the deployment-specific companion to:

- `project_requirements/REPORT_MASTER_ARCHITECTURE_MATRIX.md`
- `project_requirements/PRISM_REPORT_MASTER_CONTEXT.md`
- `project_requirements/BUSINESS_RULES_PFE_REPORT.md`

---

## 2. Deployment Objective

The goal of this deployment is to demonstrate that AdOptimizer CDP is not only a logically distributed lakehouse architecture, but also an **operationally distributed and security-aware implementation**.

This deployment proves:

- distributed ingestion through a Kafka cluster,
- distributed storage through HDFS,
- distributed processing through Spark workers on multiple machines,
- distributed query execution through Trino coordinator/worker separation,
- centralized orchestration through Airflow on the local control plane,
- centralized monitoring through Prometheus and Grafana,
- baseline infrastructure security through Kerberos, TLS, authenticated gateways, and encrypted runtime storage,
- and isolated per-node deployment bundles for maintainability.

This environment is a **distributed demo and validation environment**, not a production HA cluster.

---

## 3. Deployment Philosophy

This deployment follows six design principles.

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

The main purpose is to demonstrate the distributed concept correctly:

- cluster-based ingestion,
- cluster-based storage,
- cluster-based processing,
- cluster-based query execution.

The security layer strengthens the deployment story, but this is still a demo-oriented academic environment rather than a full production security program.

### 3.5 Maintainability over cleverness

The deployment avoids hidden automation chains spread across the whole repository.

Instead it uses:

- explicit bundles,
- explicit scripts,
- explicit env files,
- explicit preflight checks,
- explicit reset/start commands,
- and explicit client-side setup notes where browser-based security is involved.

### 3.6 Security added without rewriting the whole platform

The security design was introduced in a way that preserves the lakehouse architecture rather than replacing it.

That is important academically because it shows:

- progressive hardening,
- realistic engineering tradeoffs,
- and a separation between core data-platform logic and secure deployment controls.

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
  -> local TLS gateway
  -> remote Spark orchestration over SSH

VM1 + VM2 + VM3 (distributed data plane)
  -> Kafka cluster
  -> Kerberos-secured HDFS cluster
  -> Spark cluster
  -> Hive Metastore
  -> Trino cluster
  -> VM2 HTTPS Trino gateway
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

Security overlay:

```text
Kerberos KDC on VM2
  -> service principals and keytabs
  -> Hadoop secure mode
  -> SPNEGO for HDFS web endpoints

TLS gateways
  -> HTTPS access to control-plane tools
  -> HTTPS + authenticated access to Trino on VM2

LUKS runtime volumes
  -> encrypted service data on VM1, VM2, VM3 when enabled

Operational stabilization
  -> SSH-based remote Spark submission from control plane to VM2
  -> hostname-based HDFS secure browsing path
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
- local TLS gateway
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
- Kerberos KDC
- Kerberos admin service
- HDFS NameNode
- HDFS DataNode 2
- HDFS admin helper client
- Hive Metastore PostgreSQL
- Hive Metastore
- Spark master
- Spark submit helper
- Spark worker 2
- Spark history server
- Spark Thrift server
- Trino coordinator
- Trino HTTPS gateway
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
- Kerberos authority,
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

### 6.4 Why Kerberos is centralized on VM2

Kerberos was placed on VM2 because that node already hosts the main coordination services.

This keeps:

- principal provisioning,
- keytab extraction,
- admin access,
- and NameNode-aligned secure mode setup

within one controlled node.

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
|-- vm3/
`-- windows_kerberos_client/
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
- `tls_gateway/`
- `ssh/`

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

### 7.5 `windows_kerberos_client/`

This folder contains the Windows-side helper assets for browser-based Kerberos demo access.

Important files:

- `krb5.ini`
- `README.md`
- `hosts_example.txt`
- `firefox_spnego_prefs.txt`

This folder matters because HDFS browser access in secure mode depends on correct Windows and Firefox client configuration, not only on cluster-side health.

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

Spark raw loading is submitted remotely to **VM2**.

The control plane does not keep a local Spark driver for the final deployment path.

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

### 8.5 Security execution model

The security layer is distributed across runtime responsibilities:

- Kerberos KDC and principal administration run on VM2,
- service keytabs are provisioned before starting secured services,
- Hadoop services use Kerberos-aware configs and HTTPS web policies,
- Trino UI is exposed through a TLS gateway,
- control-plane UIs are exposed through a local TLS gateway,
- browser-side HDFS secure access depends on a valid Kerberos ticket on Windows plus Firefox SPNEGO settings.

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
- HTTPS gateway on VM2

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

### 9.7 Kerberos

Role:

- authentication backbone for the secured Hadoop deployment

Placement:

- KDC and admin service on VM2
- service principals and keytabs consumed on all relevant nodes

Purpose:

- secure Hadoop service identity
- support SPNEGO on HDFS web endpoints
- support keytab-based non-interactive service execution

### 9.8 LUKS encrypted storage

Role:

- data-at-rest protection for runtime service data

Placement:

- optional per-node encrypted runtime mount under `/mnt/customerdna_secure`

Purpose:

- protect service runtime data on VM disks
- support a defensible security section in the report

---

## 10. Primary Network Endpoints

### 10.1 Kafka

- VM1 broker: `10.10.252.11:9092`
- VM2 broker: `10.10.252.12:9092`
- VM3 broker: `10.10.252.13:9092`

### 10.2 Kerberos

- KDC on VM2: `10.10.252.12:88`
- admin server on VM2: `10.10.252.12:749`

### 10.3 HDFS

- NameNode RPC: `10.10.252.12:9000`
- NameNode web UI: `https://10.10.252.12:9871`
- NameNode browser alias: `https://namenode.customerdna.local:9871`
- VM1 DataNode UI: `https://10.10.252.11:9865`
- VM2 DataNode UI: `https://10.10.252.12:9865`
- VM3 DataNode UI: `https://10.10.252.13:9865`

### 10.4 Hive

- Hive Metastore: `10.10.252.12:9083`
- Hive Metastore PostgreSQL: `10.10.252.12:5435`

### 10.5 Spark

- Spark master: `spark://10.10.252.12:7077`
- Spark master UI: `http://10.10.252.12:8086`
- Spark history UI: `http://10.10.252.12:18080`
- Spark Thrift: `10.10.252.12:10000`
- remote submission SSH target: `10.10.252.12:22`

### 10.6 Trino

- Trino coordinator UI (HTTP): `http://10.10.252.12:8088/ui/`
- Trino coordinator UI (HTTPS): `https://10.10.252.12:8443/ui/`
- VM1 Trino worker internal endpoint: `http://10.10.252.11:8080`
- VM3 Trino worker internal endpoint: `http://10.10.252.13:8080`

### 10.7 Control plane interfaces

Preferred ports:

- Airflow: `https://localhost:18080`
- Prometheus: `https://localhost:19090`
- Grafana: `https://localhost:13001`
- Kafka UI: `https://localhost:18085`

Important note:

The control-plane startup script may shift those local ports if the preferred values are already busy.

The active resolved values are written to:

- `control_plane_pc/runtime/compose.generated.env`

---

## 11. Security Model

### 11.1 Security goals of this deployment

The security layer is intended to protect:

- service identity,
- browser-facing traffic,
- selected administrative interfaces,
- and VM runtime data at rest.

It is not intended to deliver full enterprise identity governance.

### 11.2 Implemented controls

The deployment includes:

- Kerberos-secured Hadoop runtime,
- service principals for NameNode, DataNodes, Spark, Hive, Trino, and Airflow helper operations,
- keytab-based service startup flows,
- SPNEGO-protected HDFS web endpoints,
- HTTPS-only HDFS web access,
- HTTPS Trino gateway on VM2 with authenticated browser entry,
- local HTTPS gateway for control-plane tools,
- optional LUKS-backed runtime storage on VM1, VM2, and VM3,
- credential separation between admin, service, analyst, and demo-browser identities.

### 11.3 Demo-oriented security choices

For demonstration practicality:

- self-signed or internal trust paths are used instead of enterprise PKI,
- some client-side TLS verification flags are relaxed in automation paths,
- browser-side Kerberos access requires manual Windows and Firefox configuration,
- credentials are easier to manage than in a production vault-backed environment.

### 11.4 Security boundary

This deployment should be described as **security-aware and meaningfully hardened for a PFE demo**, but not as a complete enterprise security platform.

---

## 12. Windows and Browser Kerberos Access Path

### 12.1 Why this matters

The secured HDFS browser experience depends on both sides:

- server-side Hadoop secure mode must be healthy,
- client-side Kerberos and Firefox SPNEGO behavior must be configured correctly.

### 12.2 Required Windows helper assets

The project includes a dedicated helper folder:

- `windows_kerberos_client/krb5.ini`
- `windows_kerberos_client/hosts_example.txt`
- `windows_kerberos_client/firefox_spnego_prefs.txt`
- `windows_kerberos_client/README.md`

### 12.3 Required client-side sequence

The validated browser access path is:

1. install MIT Kerberos for Windows
2. place the project `krb5.ini` in the active MIT Kerberos client configuration path or point `KRB5_CONFIG` to it
3. obtain a Kerberos ticket with the demo principal
4. configure Firefox SPNEGO trusted and delegation URIs
5. point Firefox to the MIT Kerberos GSS library if required
6. browse HDFS using the hostname alias, not the raw IP
7. renew or recreate the Kerberos ticket if the browser stops negotiating after client-side changes

### 12.4 Important operational truth

If the NameNode overview page opens but `explorer.html` shows `Unauthorized`, that does **not** automatically mean the backend cluster is unhealthy.

It often indicates a browser-side SPNEGO or WebHDFS authentication path issue.

That distinction is important for debugging and for honest report-writing.

### 12.5 Stabilized result achieved in this deployment

After the final client-side correction pass, the secured HDFS browser flow was validated end to end:

- Kerberos ticket acquisition works from Windows,
- Firefox can reuse that ticket for SPNEGO negotiation,
- the secure NameNode overview page opens through the hostname alias,
- and `explorer.html` can browse HDFS successfully when the client configuration is exact.

This means the remaining risk is not an unresolved backend defect, but a configuration-sensitive client workflow that must be reproduced carefully on any new Windows machine.

---

## 13. Control Plane Folder Responsibilities

### 13.1 `control_plane_pc/docker-compose.yml`

Defines:

- Airflow stack,
- Airflow PostgreSQL,
- Prometheus,
- Grafana,
- Kafka UI,
- pipeline metrics exporter,
- PostgreSQL exporter,
- local TLS gateway.

### 13.2 `control_plane_preflight_checks.ps1`

Purpose:

- verifies local tools,
- verifies required mounted paths,
- verifies remote service reachability,
- verifies security-critical endpoints such as Kerberos and HTTPS services.

### 13.3 `start_control_plane_pc.ps1`

Purpose:

- resolves usable local ports,
- prepares runtime env overrides,
- starts the control plane in the correct order,
- starts the local TLS gateway.

### 13.4 `reset_control_plane_state.ps1`

Purpose:

- stops the local control-plane stack,
- removes state that should be rebuilt for a clean restart.

### 13.5 `ssh/`

Purpose:

- stores the SSH key material used by the control plane to reach VM2 for remote Spark orchestration.

Important rule:

- this directory is operationally critical,
- but secret contents must not be copied into reports, screenshots, or version history by mistake.

---

## 14. VM Folder Responsibilities

### 14.1 Common pattern

Each VM folder follows the same operational lifecycle:

1. prepare the VM
2. validate prerequisites
3. start the stack
4. verify endpoints
5. reset only that node when required

### 14.2 `prepare_fresh_vm*.sh`

Purpose:

- install or verify required OS-side dependencies,
- prepare Docker and execution prerequisites,
- prepare the VM for first startup.

### 14.3 `vm*_preflight_checks.sh`

Purpose:

- validate local tools,
- validate critical peer endpoints,
- validate local ports,
- reduce startup surprises.

### 14.4 `start_vm*_stack.sh`

Purpose:

- provision service principals and keytabs where required,
- validate secure storage mounts when enabled,
- start the compose-defined services for that node,
- expose the node as part of the distributed data plane.

### 14.5 `reset_vm*_state.sh`

Purpose:

- stop node services,
- clear runtime data,
- prepare a clean redeployment of that node.

### 14.6 `manage_vm*_bundle.py`

Purpose:

- build a portable bundle,
- package the node-specific deployment content,
- support upload/deploy workflow from the workstation.

### 14.7 `setup_encrypted_storage_vm*.sh`

Purpose:

- create or reuse the encrypted image,
- initialize the LUKS container,
- mount the secure runtime filesystem,
- prepare the service data directories used by the node.

---

## 15. Distributed Startup Order

The recommended cluster startup order is:

1. VM2
2. VM1
3. VM3
4. control plane

### 15.1 Why VM2 starts first

Because it contains the coordination services:

- Kerberos KDC
- HDFS NameNode
- Hive Metastore
- Spark master
- Trino coordinator
- Spark Thrift

Other nodes depend on those services being reachable and stable.

### 15.2 Why VM1 and VM3 come next

Because they add:

- Kafka peers,
- HDFS storage peers,
- Spark execution capacity,
- Trino worker capacity.

### 15.3 Why control plane comes last

Because Airflow, monitoring, and UI services should start only after the distributed data plane is reachable and stable.

---

## 16. Pipeline Execution Order After Deployment

After the cluster is up, the Airflow execution order is:

1. `customerdna_client1_environment_reset_pipeline`
2. `customerdna_client1_lakehouse_setup_pipeline`
3. `customerdna_client1_lakehouse_readiness_pipeline`
4. `customerdna_client1_kafka_hdfs_spark_lakehouse_pipeline`
5. `customerdna_client1_dbt_spark_lakehouse_pipeline`

This order is the operational contract for a clean end-to-end run.

---

## 17. What Makes This Deployment Truly Distributed

This deployment is not "distributed" only because multiple machines exist.

It is distributed because the core runtime responsibilities are split across nodes in meaningful ways.

### 17.1 Distributed ingestion

Kafka quorum spans VM1, VM2, and VM3.

### 17.2 Distributed storage

HDFS stores data across DataNodes on VM1, VM2, and VM3, with namespace control on VM2.

### 17.3 Distributed processing

Spark applications are scheduled by the master and can allocate executors across workers on VM1, VM2, and VM3.

### 17.4 Distributed querying

Trino uses a coordinator/worker model with worker nodes separated from the coordinator.

### 17.5 Centralized control

Airflow remains centralized on the control plane, which is a valid and common orchestration pattern.

---

## 18. Observability Model

The deployed version has two observability levels.

### 18.1 Infrastructure-level observability

Provided by:

- cAdvisor on each VM
- Prometheus scraping
- Grafana infrastructure dashboard

This shows:

- container health,
- CPU usage,
- memory usage,
- node reachability.

### 18.2 Pipeline-level observability

Provided by:

- pipeline metrics exporter
- Airflow run/task history
- Grafana pipeline health dashboard

This shows:

- DAG success/failure,
- freshness indicators,
- validation status,
- lakehouse readiness signals.

### 18.3 Security-level observability

Security is not monitored through a full SIEM stack, but relevant visibility exists through:

- container startup logs,
- Kerberos service logs,
- Trino gateway access logs,
- HDFS secure endpoint reachability checks,
- and browser/client-side validation steps.

---

## 19. Validation and Evidence Checklist

The deployed version should be considered healthy only when the following are true.

### 19.1 Cluster service health

- Kafka brokers reachable on all three VMs
- Kerberos KDC reachable on VM2
- HDFS NameNode reachable
- HDFS DataNodes registered
- Hive Metastore reachable
- Spark master reachable
- Spark Thrift reachable
- Trino coordinator reachable
- cAdvisor reachable on all three VMs

### 19.2 Control plane health

- Airflow UI reachable
- Prometheus UI reachable
- Grafana UI reachable
- Kafka UI reachable

### 19.3 Pipeline evidence

- the secured baseline preserves the five-DAG execution order
- environment reset and readiness validation succeed under the hardened runtime
- raw Iceberg tables remain the official output of the Kafka -> HDFS -> Spark stage
- dbt analytical tables remain the official curated output of the transformation stage
- GX validations remain the official data-quality evidence layer
- Data Docs HTML remains the expected quality-report artifact
- Grafana dashboards remain the expected distributed observability artifact

Important report rule:

- claim a DAG as operationally validated only when its run logs or screenshots are available as evidence,
- do not convert the intended execution order into a blanket statement that every DAG was fully benchmarked under every security permutation.

### 19.4 Distributed proof

The strongest proof of distribution is:

- HDFS shows multiple live DataNodes
- Spark master shows workers from VM1, VM2, and VM3
- Trino cluster shows coordinator plus workers
- Kafka UI shows the broker cluster

### 19.5 Security proof

The strongest proof of security implementation is:

- HDFS secure mode reports that security is on
- HDFS web endpoints are exposed over HTTPS
- Kerberos ticket acquisition works from Windows
- Firefox-based Kerberos browsing of HDFS works through the hostname alias when the documented client settings are applied
- Trino HTTPS gateway is reachable
- control-plane HTTPS entry points are reachable
- encrypted runtime mount scripts exist and are used when secure storage is enabled

---

## 20. Known Limitations and Honest Reporting Notes

### 20.1 Browser-based HDFS Explorer is configuration-sensitive

At the time of this report update:

- the secure HDFS backend is functioning,
- Kerberos ticket acquisition from Windows is functioning,
- the NameNode secure overview page is reachable,
- and the `explorer.html` path is working in the validated Firefox setup,
- but this path remains sensitive to exact client-side Kerberos and Firefox SPNEGO configuration.

This should be reported honestly as:

- a configuration-sensitive secure browsing workflow,
- not as evidence that the cluster or HDFS secure mode is broken.

### 20.2 Security hardening required targeted runtime fixes

The security layer was not only a configuration addition. It required operational stabilization work, including:

- ensuring Airflow runtime variables point to the secure endpoints and deployment-safe hostnames,
- reducing dbt concurrency to a safer demo value,
- ensuring Spark-side services obtain and renew Kerberos tickets before contacting Hive Metastore,
- ensuring the Trino browser gateway stays aligned with the coordinator port and authenticated entry path,
- aligning HDFS secure browsing around hostname-based SPNEGO rather than raw IP navigation,
- and validating the Windows + Firefox Kerberos client path for HDFS browsing.

This is an important academic point because it shows that secure distributed systems often need runtime adaptation, not only checkbox-style configuration.

### 20.3 Demo-oriented certificate trust

The deployment uses demo-friendly TLS trust paths and may show browser warnings if the local CA is not trusted.

### 20.4 Fixed VM constraints

The VM hardware remains fixed by the IT administrator.

Therefore:

- memory is limited,
- disk is limited,
- aggressive resource settings are unsafe.

### 20.5 Not a full enterprise IAM design

The deployment demonstrates meaningful security controls, but not full:

- centralized secret rotation,
- external identity federation,
- enterprise PKI management,
- or production zero-trust segmentation.

---

## 21. Operational Constraints

This deployment has known operational constraints.

### 21.1 Fixed VM specifications

The VM hardware is fixed by the IT administrator.

### 21.2 Demo-first sizing

The cluster demonstrates distribution correctly, but it is not intended for large production-scale datasets.

### 21.3 Disk pressure

Because HDFS, Spark logs, Docker layers, encrypted runtime images, and runtime volumes all consume disk, cleanup discipline matters.

### 21.4 Control-plane local dependency

The orchestration UX depends on the local PC being available because:

- Airflow is local,
- monitoring dashboards are local,
- Kafka UI is local.

---

## 22. Why This Deployment Is Strong for the Jury

This deployment is strong because it proves that the project is not only a collection of data tools on one laptop.

It demonstrates:

- real node separation,
- real cluster services,
- real orchestration,
- real monitoring,
- real end-to-end execution,
- real lakehouse behavior,
- meaningful security hardening,
- and a careful distinction between implemented controls and remaining integration-sensitive client behavior.

That makes the final project much more defensible as a serious Data Engineering and Big Data implementation.

---

## 23. Final Summary

The distributed deployment under `src/deployments/distributed_pc_control_plane/` is the final operational form of AdOptimizer CDP for the PFE.

It consists of:

- a **local control plane** for orchestration and observability,
- a **three-VM data plane** for ingestion, storage, processing, querying, and secure Hadoop control,
- isolated per-node bundles for maintainability,
- and an execution model designed around correctness, distribution, constrained infrastructure, and baseline security hardening.

In practical terms, this folder is the bridge between:

- the project architecture on paper,
- and the actual deployed system that can be shown, tested, explained, secured, and defended.

Its final deployment story should specifically emphasize that the secured version is not only distributed on paper, but also stabilized in practice through:

- Kerberos-secured Hadoop runtime,
- SPNEGO + HTTPS HDFS browser access through documented hostname aliases,
- HTTPS and authenticated Trino access,
- local TLS exposure for control-plane tools,
- optional encrypted runtime storage,
- and SSH-based Spark submission that avoids unstable local-driver networking from the workstation.
