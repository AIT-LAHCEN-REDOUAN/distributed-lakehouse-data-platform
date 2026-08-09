# Grafana

- URL: `https://localhost:13001`
- Username: `admin`
- Password: `CustomerDNA_Grafana_Admin_2026!`

Purpose:

- View infrastructure dashboards
- View pipeline health dashboards
- Confirm distributed monitoring metrics

Notes:

- The local TLS gateway uses an internal demo certificate authority, so the browser may show a certificate warning on first access.
- If the startup script remaps the port because `13001` is busy, read the active value from `control_plane_pc/runtime/compose.generated.env`.
