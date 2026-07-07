"""Publish Client 1 marketing campaign records into Kafka."""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from kafka import KafkaAdminClient, KafkaProducer
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

COMMON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

from kafka_config import KAFKA_BOOTSTRAP_SERVERS, PROCESSED_DATASET_PATHS, TOPICS  # noqa: E402


DATASET_KEY = "marketing_campaign"
TOPIC_NAME = TOPICS[DATASET_KEY]
SOURCE_PATH = PROCESSED_DATASET_PATHS[DATASET_KEY]


def _normalize_row(row: dict[str, str]) -> dict[str, str | None]:
    """Normalize empty strings to None and preserve string-safe values."""
    normalized: dict[str, str | None] = {}

    for key, value in row.items():
        if value is None:
            normalized[key] = None
            continue

        stripped = value.strip()
        normalized[key] = stripped if stripped != "" else None

    return normalized


def ensure_topic_exists(topic_name: str) -> None:
    """Create the topic if it does not already exist."""
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
    """Wrap the CSV row in a structured Kafka event payload."""
    payload = _normalize_row(row)

    return {
        "client_id": "client_1",
        "dataset_name": DATASET_KEY,
        "source_file": SOURCE_PATH.name,
        "row_number": row_number,
        "produced_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }


def build_producer() -> KafkaProducer:
    """Return a JSON-producing Kafka producer."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        acks="all",
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda value: value.encode("utf-8") if value else None,
    )


def publish_dataset(source_path: Path, topic_name: str) -> int:
    """Publish the processed dataset row-by-row to Kafka."""
    if not source_path.exists():
        raise FileNotFoundError(f"Processed dataset not found: {source_path}")

    ensure_topic_exists(topic_name)
    producer = build_producer()
    published_count = 0

    try:
        with source_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            for row_number, row in enumerate(reader, start=1):
                message = build_message(row, row_number)
                message_key = str(message["payload"].get("ID") or row_number)

                producer.send(topic_name, key=message_key, value=message)
                published_count += 1

                if row_number % 500 == 0:
                    print(f"[INFO] Published {row_number:,} records to {topic_name}")

        producer.flush()
        return published_count
    finally:
        producer.close()


def main() -> None:
    """Run the first Client 1 Kafka producer proof of concept."""
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
