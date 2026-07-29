# Shared Deployment Assets

This folder is now the reusable baseline for the isolated distributed deployment under
[`distributed_pc_control_plane`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane).

## Purpose

Use this folder for values and helper assets that must stay consistent across:

- [control_plane_pc](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/control_plane_pc)
- [vm1](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/vm1)
- [vm2](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/vm2)
- [vm3](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/vm3)

## What Is Here

- [`configs/cluster_inventory.yml`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/shared/configs/cluster_inventory.yml)
- [`configs/service_placement.yml`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/shared/configs/service_placement.yml)
- [`configs/ports_map.yml`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/shared/configs/ports_map.yml)
- [`configs/deployment_conventions.md`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/shared/configs/deployment_conventions.md)
- [`env/cluster.shared.env.example`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/shared/env/cluster.shared.env.example)
- [`env/vm.common.env.example`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/shared/env/vm.common.env.example)
- [`env/control_plane_pc.reference.env`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/shared/env/control_plane_pc.reference.env)
- [`scripts/cluster_preflight_checks.ps1`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/shared/scripts/cluster_preflight_checks.ps1)
- [`scripts/cluster_preflight_checks.sh`](D:/github/Master_PFE_Project/CustomerDNA%20AI/src/deployments/distributed_pc_control_plane/shared/scripts/cluster_preflight_checks.sh)

## How To Use It

1. Read `cluster_inventory.yml` and `service_placement.yml` before editing any VM folder.
2. Copy the env templates into node-specific folders instead of rewriting values by hand.
3. Use the shared preflight scripts to validate cross-node connectivity before starting services.
4. Treat the values in this folder as the source of truth for the new distributed deployment only.

## Design Notes

- This folder is intentionally separate from the original local implementation.
- The cluster is resource-constrained, so the values here are tuned for a demonstration of distribution, not for production hardening.
- The preferred control-plane ports here are the default targets. The local startup script may auto-shift them if your workstation already has something bound to those ports.
