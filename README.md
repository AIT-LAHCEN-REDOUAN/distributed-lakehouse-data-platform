# CustomerDNA AI: Distributed Lakehouse Data Platform

A distributed lakehouse platform for ingesting, transforming, validating, and serving customer data for analytics.

The project follows a Medallion Architecture to convert data from multiple sources into reliable, analytics-ready datasets. It is designed around scalable data engineering practices: ingestion, transformation, orchestration, data quality, observability, and SQL-based consumption.

## Architecture

```text
Data Sources
    |
    v
Kafka and Python Ingestion
    |
    v
Bronze Layer: Raw Data
    |
    v
Silver Layer: Cleaned and Standardized Data
    |
    v
Gold Layer: Analytics-Ready Data Models
    |
    +--> Trino SQL Queries
    +--> BI and Analytics Consumption
