# Local PC Monitoring

Monitoring is centralized on the local PC.

## Files That Matter

- [`../prometheus.yml`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/prometheus.yml)
- [`../grafana/provisioning/datasources/prometheus.yml`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/grafana/provisioning/datasources/prometheus.yml)
- [`../grafana/provisioning/dashboards/customerdna.yml`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc/grafana/provisioning/dashboards/customerdna.yml)

## Runtime Model

- Prometheus scrapes the local exporters and the remote VM cAdvisor endpoints.
- Grafana is provisioned locally but reads the dashboards from the shared project repository.
- Pipeline metrics continue to come from the existing monitoring state JSON files in the main project.
