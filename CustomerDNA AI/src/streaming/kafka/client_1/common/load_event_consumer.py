"""Consume one bronze-ready Kafka event and load the referenced run into PostgreSQL raw_data."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from kafka import KafkaConsumer

from kafka_config import BRONZE_READY_TOPICS, KAFKA_BOOTSTRAP_SERVERS, get_dataset_config


RAW_LOAD_COMMON_DIR = Path(__file__).resolve().parents[4] / "ELT" / "client_1" / "raw_load" / "common"
if str(RAW_LOAD_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(RAW_LOAD_COMMON_DIR))

from bronze_raw_loader import BronzeToRawLoader  # noqa: E402


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
    """Consume the bronze-ready event for one dataset and load that bronze run to PostgreSQL."""
    dataset_config = get_dataset_config(dataset_key)
    topic_name = BRONZE_READY_TOPICS[dataset_key]
    target_table = str(dataset_config["target_table"])
    consumer_timeout_ms = int(dataset_config["load_event_consumer_timeout_ms"])
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    consumer_group = f"customerdna-client1-{dataset_key}-raw-loader-{run_id.lower()}"

    print("=" * 80)
    print("CUSTOMERDNA AI - KAFKA BRONZE-READY TO RAW LOAD")
    print("=" * 80)
    print(f"Dataset: {dataset_key}")
    print(f"Bronze-ready topic: {topic_name}")
    print(f"Target table: raw_data.{target_table}")

    consumer = build_consumer(
        topic_name=topic_name,
        consumer_group=consumer_group,
        consumer_timeout_ms=consumer_timeout_ms,
    )

    loader = BronzeToRawLoader(dataset_key=dataset_key, verbose=True)

    try:
        try:
            message = next(iter(consumer))
        except StopIteration as exc:
            raise RuntimeError(
                f"No bronze-ready Kafka event was found for dataset '{dataset_key}'. "
                "The MinIO bronze consumer may have failed before publishing the load event."
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
        print(f"Expected bronze objects: {int(event_payload.get('object_count', 0)):,}")
        print(f"Expected rows: {int(event_payload.get('row_count', 0)):,}")

        if not loader.connect_to_dw():
            raise RuntimeError("Unable to connect to the data warehouse for raw loading.")

        result = loader.load_from_bronze_event(event_payload)
        consumer.commit()

        print(f"Bronze objects read: {result.object_count:,}")
        print(f"Rows loaded: {result.rows_loaded:,}")
        print(f"Duration (seconds): {result.duration_seconds}")
        print("Kafka bronze-ready raw load completed successfully.")
        print("=" * 80)
    finally:
        loader.close_connection()
        consumer.close()
