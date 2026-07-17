"""Consume one bronze-ready Kafka event and trigger Spark to load the referenced HDFS run into an Iceberg raw table."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from kafka import KafkaConsumer

from kafka_config import BRONZE_READY_TOPICS, KAFKA_BOOTSTRAP_SERVERS, get_dataset_config


SPARK_COMMON_DIR = Path(__file__).resolve().parents[4] / "processing" / "spark" / "client_1" / "common"
if str(SPARK_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(SPARK_COMMON_DIR))

from spark_raw_loader_submitter import submit_hdfs_bronze_to_iceberg_spark_job  # noqa: E402


def build_consumer(*, topic_name: str, consumer_group: str, consumer_timeout_ms: int) -> KafkaConsumer:
    """Return a Kafka consumer configured for one bronze-ready event."""
    return KafkaConsumer(
        topic_name,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id=consumer_group,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        key_deserializer=lambda value: value.decode("utf-8") if value else None,
        consumer_timeout_ms=consumer_timeout_ms,
        max_poll_records=1,
    )


def run_load_event_consumer(dataset_key: str) -> None:
    """Consume the bronze-ready event for one dataset and build the Iceberg raw table with Spark."""
    dataset_config = get_dataset_config(dataset_key)
    topic_name = BRONZE_READY_TOPICS[dataset_key]
    target_table = str(dataset_config["target_table"])
    consumer_timeout_ms = int(dataset_config["load_event_consumer_timeout_ms"])
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    consumer_group = f"customerdna-client1-{dataset_key}-spark-raw-builder-{run_id.lower()}"

    print("=" * 80)
    print("CUSTOMERDNA AI - KAFKA BRONZE-READY TO SPARK ICEBERG RAW LOAD")
    print("=" * 80)
    print(f"Dataset: {dataset_key}")
    print(f"Bronze-ready topic: {topic_name}")
    print(f"Target Iceberg table: raw_data.{target_table}")

    consumer = build_consumer(
        topic_name=topic_name,
        consumer_group=consumer_group,
        consumer_timeout_ms=consumer_timeout_ms,
    )

    try:
        try:
            message = next(iter(consumer))
        except StopIteration as exc:
            raise RuntimeError(
                f"No bronze-ready Kafka event was found for dataset '{dataset_key}'. "
                "The HDFS bronze consumer may have failed before publishing the Spark build event."
            ) from exc

        event_payload = message.value
        event_dataset = str(event_payload.get("dataset_name", "")).strip()
        if event_dataset != dataset_key:
            raise RuntimeError(
                f"Bronze-ready event dataset mismatch: expected '{dataset_key}', got '{event_dataset}'."
            )

        event_target_table = str(event_payload.get("target_table", "")).strip()
        if event_target_table != target_table:
            raise RuntimeError(
                f"Bronze-ready event target mismatch: expected '{target_table}', got '{event_target_table}'."
            )

        print(f"Bronze run prefix: {event_payload.get('bronze_run_prefix')}")
        print(f"Expected bronze files: {int(event_payload.get('file_count', 0)):,}")
        print(f"Expected rows: {int(event_payload.get('row_count', 0)):,}")

        result = submit_hdfs_bronze_to_iceberg_spark_job(
            dataset_key=dataset_key,
            target_table=target_table,
            bronze_prefix=str(event_payload.get("bronze_run_prefix", "")),
            hdfs_namenode_uri=os.getenv("CUSTOMERDNA_HDFS_NAMENODE_URI", "hdfs://localhost:9000"),
            expected_rows=int(event_payload.get("row_count", 0)) or None,
            expected_file_count=int(event_payload.get("file_count", 0)) or None,
        )
        consumer.commit()

        print(f"Bronze files read: {result.bronze_files_read:,}")
        print(f"Rows loaded: {result.rows_loaded:,}")
        print(f"Duration (seconds): {result.duration_seconds}")
        print("Kafka bronze-ready Spark Iceberg raw load completed successfully.")
        print("=" * 80)
    finally:
        consumer.close()
