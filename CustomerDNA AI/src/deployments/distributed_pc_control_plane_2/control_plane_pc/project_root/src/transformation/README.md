# Client 1 Transformation Layer

This folder contains the SQL transformation layer for the lakehouse architecture.

Current implementation:

- `dbt_spark/client_1/`
  - runs through Spark Thrift Server,
  - reads Iceberg raw tables from the `lakehouse` catalog,
  - builds the `staging`, `intermediate`, and `analytics` namespaces,
  - is orchestrated from Airflow through the `customerdna_client1_dbt_spark_lakehouse_pipeline` DAG.
