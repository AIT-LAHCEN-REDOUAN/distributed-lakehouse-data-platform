# CustomerDNA AI - HDFS Bronze Layer

This folder provides the Hadoop-style bronze storage layer for the project.

Current role:
- Kafka producers publish dataset rows into Kafka topics.
- Kafka bronze consumers persist immutable JSONL batch files into HDFS bronze paths.
- Kafka bronze-ready events trigger Spark to read those HDFS files and build Iceberg `raw_data` tables.

Main folders:
- `client_1/common/`
  Shared HDFS bronze configuration and WebHDFS helpers.
- `client_1/reset_client1_bronze.py`
  Clears the Client 1 bronze landing zone for a clean rerun.
- `client_1/list_client1_bronze_objects.py`
  Lists the current bronze files stored for Client 1.

Runtime assumption:
- HDFS is exposed through WebHDFS on port `9870`.
- The namenode RPC endpoint is exposed on port `9000`.

Default flow:
`source datasets -> Kafka -> HDFS bronze -> Kafka bronze-ready event -> Spark -> Iceberg raw tables`
