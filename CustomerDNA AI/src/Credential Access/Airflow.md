# Airflow

- URL: `https://localhost:18080`
- Username: `admin`
- Password: `CustomerDNA_Airflow_Admin_2026!`
- Role: `Admin`
- Backing database:
  - Host: `localhost` inside Docker network as `airflow-postgres`
  - Database: `airflow`
  - Username: `airflow`
  - Password: `CustomerDNA_Airflow_DB_2026!`

Purpose:

- Trigger and monitor DAGs
- Review task logs
- Validate end-to-end orchestration

Notes:

- The local TLS gateway uses an internal demo certificate authority, so the browser may show a certificate warning on first access.
- If the startup script remaps the port because `18080` is busy, read the active value from `control_plane_pc/runtime/compose.generated.env`.
