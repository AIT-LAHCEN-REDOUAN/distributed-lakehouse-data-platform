# Hive Metastore and Iceberg Catalog

This folder contains the local Docker-based catalog layer for the lakehouse architecture.

## Purpose

- `Hive Metastore` provides the shared metadata catalog for distributed tables.
- `Iceberg` is the table format used by Spark for bronze, silver, and gold tables.
- `HDFS` remains the distributed storage layer.
- `Spark` uses this metastore to create and manage Iceberg tables.

## Local Design

The local branch uses Docker containers for:

- PostgreSQL-backed Hive metastore database
- Hive standalone metastore service

Iceberg is not a separate service container. It is enabled through:

- Spark runtime package
- Spark catalog configuration
- Hive metastore registration

## Startup Order

1. Start Kafka network and services
2. Start HDFS
3. Start Hive Metastore
4. Start Spark
5. Start Airflow and monitoring

## Main Files

- `.env.example`: local environment template
- `docker-compose.yml`: metastore stack
- `config/`: Hive/HDFS configuration files
- `metastore/Dockerfile`: custom metastore image with PostgreSQL JDBC driver
