# Local PC Great Expectations

Great Expectations remains a control-plane runtime on the local PC.

## Runtime Model

- Airflow invokes the existing GX scripts from the main repository.
- GX validates the remote lakehouse through Trino and project-local configuration.
- Validation JSON and Data Docs generation still land in the main project folders, not inside this deployment folder.
