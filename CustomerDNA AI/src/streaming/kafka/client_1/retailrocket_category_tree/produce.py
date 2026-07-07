"""Publish Client 1 retailrocket category tree records into Kafka."""

from __future__ import annotations

import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

COMMON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

from kafka_config import KAFKA_BOOTSTRAP_SERVERS, PROCESSED_DATASET_PATHS, TOPICS  # noqa: E402
from producer_utils import (  # noqa: E402
    build_reliable_producer,
    get_topic_message_count,
    publish_with_confirmation,
)


DATASET_KEY = "retailrocket_category_tree"
TOPIC_NAME = TOPICS[DATASET_KEY]
SOURCE_PATH = PROCESSED_DATASET_PATHS[DATASET_KEY]


def _normalize_row(row: dict[str, str]) -> dict[str, str | None]:
    normalized: dict[str, str | None] = {}

    for key, value in row.items():
        if value is None:
            normalized[key] = None
            continue

        stripped = value.strip()
        normalized[key] = stripped if stripped != "" else None

    return normalized


def ensure_topic_exists(topic_name: str) -> None:
    admin_client = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        client_id="customerdna-client1-topic-admin",
    )

    try:
        admin_client.create_topics(
            new_topics=[
                NewTopic(
                    name=topic_name,
                    num_partitions=3,
                    replication_factor=1,
                )
            ],
            validate_only=False,
        )
        print(f"[INFO] Created topic: {topic_name}")
    except TopicAlreadyExistsError:
        print(f"[INFO] Topic already exists: {topic_name}")
    finally:
        admin_client.close()


def build_message(row: dict[str, str], row_number: int) -> dict[str, object]:
    payload = _normalize_row(row)

    return {
        "client_id": "client_1",
        "dataset_name": DATASET_KEY,
        "source_file": SOURCE_PATH.name,
        "row_number": row_number,
        "produced_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }


def publish_dataset(source_path: Path, topic_name: str) -> int:
    if not source_path.exists():
        raise FileNotFoundError(f"Processed dataset not found: {source_path}")

    ensure_topic_exists(topic_name)
    producer = build_reliable_producer()
    topic_count_before = get_topic_message_count(topic_name)

    try:
        with source_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            def row_stream():
                for row_number, row in enumerate(reader, start=1):
                    message = build_message(row, row_number)
                    message_key = str(message["payload"].get("categoryid") or row_number)
                    yield message_key, message

            confirmed_count = publish_with_confirmation(
                producer=producer,
                topic_name=topic_name,
                rows=row_stream(),
                progress_message_factory=lambda count: f"[INFO] Confirmed {count:,} records in {topic_name}",
                progress_interval=500,
            )

        topic_count_after = get_topic_message_count(topic_name)
        topic_delta = topic_count_after - topic_count_before

        if topic_delta != confirmed_count:
            raise RuntimeError(
                f"Kafka topic growth mismatch for {topic_name}: "
                f"confirmed={confirmed_count:,}, topic_delta={topic_delta:,}"
            )

        return confirmed_count
    finally:
        producer.close()


def main() -> None:
    print("=" * 80)
    print("CUSTOMERDNA AI - KAFKA PRODUCER")
    print("=" * 80)
    print(f"Dataset: {DATASET_KEY}")
    print(f"Topic: {TOPIC_NAME}")
    print(f"Source: {SOURCE_PATH}")

    published_count = publish_dataset(SOURCE_PATH, TOPIC_NAME)

    print(f"Published rows: {published_count:,}")
    print("Kafka producer completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
