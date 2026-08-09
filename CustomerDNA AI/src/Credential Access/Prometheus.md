# Prometheus

- URL: `https://localhost:19090`
- Application login: `Not enabled in the demo`
- Password: `Not applicable`

Purpose:

- Validate scrape targets
- Inspect raw metrics before Grafana visualization

Notes:

- The local TLS gateway uses an internal demo certificate authority, so the browser may show a certificate warning on first access.
- If the startup script remaps the port because `19090` is busy, read the active value from `control_plane_pc/runtime/compose.generated.env`.
