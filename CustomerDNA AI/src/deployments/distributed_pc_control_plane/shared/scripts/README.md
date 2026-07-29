# Shared Scripts

These helper scripts are meant to be reused across nodes in the new distributed deployment.

## Files

- `cluster_preflight_checks.ps1`
  Windows and control-plane friendly endpoint checks.

- `cluster_preflight_checks.sh`
  Linux and VM friendly endpoint checks.

Both scripts assume the current cluster topology from `cluster.shared.env.example`.
