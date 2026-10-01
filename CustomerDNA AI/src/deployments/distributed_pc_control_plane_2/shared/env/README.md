# Shared Env Templates

Use these templates as the reusable environment baseline for the distributed deployment.

## Files

- `cluster.shared.env.example`
  Cluster-wide IPs, service endpoints, replication settings, and common runtime values.

- `vm.common.env.example`
  Common Docker and service defaults that each VM-specific folder can inherit.

- `control_plane_pc.reference.env`
  Reference mapping for the local control plane against the remote VM cluster.

## Usage

Copy the relevant template into a node folder and then override only the node-specific values there.
