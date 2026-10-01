# Trino Query Layer for Iceberg Lakehouse

This folder adds the SQL query layer used to explore and query the project lakehouse with `DBeaver`.

## Purpose

- `Trino` exposes a distributed SQL endpoint over the project data lakehouse.
- `Iceberg` remains the table format.
- `Hive Metastore` remains the catalog.
- `HDFS` remains the distributed storage layer.
- `DBeaver` connects to `Trino`, giving a visual query experience similar to `pgAdmin`.

## Why Trino is added

The project already uses:

- `Kafka` for ingestion
- `HDFS` for bronze distributed storage
- `Spark` for distributed processing
- `Hive Metastore` for shared metadata
- `Iceberg` for table management

`Trino` is the missing interactive SQL/query layer that lets developers and reviewers inspect the lakehouse visually and run SQL without using Spark jobs directly.

## Local startup order

1. Start Kafka
2. Start HDFS
3. Start Hive Metastore
4. Start Spark
5. Start Trino
6. Start Airflow and monitoring
7. Run dbt-spark transformations once raw Iceberg tables are available

## Main files

- `.env.example`: environment template for local setup
- `docker-compose.yml`: Trino container definition
- `etc/config.properties`: Trino coordinator configuration
- `etc/node.properties`: node identity and data directory
- `etc/jvm.config`: JVM tuning for local runs
- `etc/catalog/lakehouse.properties`: Iceberg catalog definition
- `etc/core-site.xml`: HDFS client configuration
- `etc/hdfs-site.xml`: HDFS client configuration

## DBeaver connection

Use a `Trino` connection in DBeaver with:

- Host: `localhost`
- Port: `8088` (or your mapped host port)
- Catalog: `lakehouse`
- Schema: `raw_data`, `staging`, `intermediate`, or `analytics`

## Current scope

This setup exposes the lakehouse query layer for:

- raw Iceberg tables created by Spark from HDFS bronze data,
- transformed dbt-spark layers (`staging`, `intermediate`, `analytics`),
- operational SQL inspection through DBeaver or any compatible Trino client.
