# Prometheus Monitoring Stack

This folder contains a local Prometheus stack for CustomerDNA AI.

Included services:
- `prometheus`: metrics collection and querying
- `postgres_exporter`: PostgreSQL database metrics for `client1_DW`
- `cadvisor`: Docker container resource metrics

Setup:
1. Copy `.env.example` to `.env`
2. Fill in your PostgreSQL password in `.env`
3. Start the stack with Docker Compose
4. Open Prometheus at `http://localhost:9090`

Suggested Grafana datasource:
- Type: Prometheus
- URL: `http://host.docker.internal:9090`

Notes:
- `postgres_exporter` connects to your local PostgreSQL warehouse on port `5440`
- `cadvisor` is included for container-level CPU/memory monitoring
- This stack is intentionally local and lightweight for PFE demonstration