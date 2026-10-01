# Local PC dbt

dbt stays on the local PC as a client runtime.

## Runtime Model

- Airflow runs `dbt run` and `dbt test` from the real project repository.
- Execution is remote through the Spark Thrift Server on VM2.
- Artifacts continue to be written into the existing dbt `target/` directory inside the main project.
