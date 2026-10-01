# Control Plane Certificates

This folder is reserved for optional control-plane certificate files.

Current demo behavior:

- browser-facing control-plane TLS is generated automatically by the local Caddy gateway
- control-plane to Trino traffic is encrypted over HTTPS through the VM2 gateway
- TLS verification is disabled by configuration for the demo deployment, so no manual CA import is required for pipeline execution

If you later decide to enforce certificate validation end to end, place the trusted CA certificate here and point the related environment variables to the mounted file path inside the containers.
