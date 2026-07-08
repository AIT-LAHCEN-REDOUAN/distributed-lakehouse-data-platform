"""Shared Kafka producer workflow for Client 1 datasets."""

from __future__ import annotations

from datetime import datetime, timezone

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

from kafka_config import KAFKA_BOOTSTRAP_SERVERS, TOPICS
from producer_utils import (
    build_reliable_producer,
    get_topic_message_count,
    publish_with_confirmation,
)
from source_row_iterators import get_source_label, iter_source_rows


def ensure_topic_exists(topic_name: str) -> None:
    """Create a Kafka topic if it does not already exist."""
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


def build_message(dataset_key: str, row: dict[str, str | None], row_number: int) -> dict[str, object]:
    """Wrap one normalized source row in a structured Kafka event payload."""
    return {
        "client_id": "client_1",
        "dataset_name": dataset_key,
        "source_file": get_source_label(dataset_key),
        "row_number": row_number,
        "produced_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload": row,
    }


def publish_dataset(
    *,
    dataset_key: str,
    key_field_priority: list[str],
    progress_interval: int,
) -> int:
    """Publish all rows for a dataset and verify topic growth matches confirmation count."""
    topic_name = TOPICS[dataset_key]
    ensure_topic_exists(topic_name)

    producer = build_reliable_producer()
    topic_count_before = get_topic_message_count(topic_name)

    try:
        def row_stream():
            for row_number, row in enumerate(iter_source_rows(dataset_key), start=1):
                message = build_message(dataset_key, row, row_number)
                payload = message["payload"]
                message_key = None

                for field_name in key_field_priority:
                    field_value = payload.get(field_name)
                    if field_value not in (None, ""):
                        message_key = str(field_value)
                        break

                if message_key is None:
                    message_key = str(row_number)

                yield message_key, message

        confirmed_count = publish_with_confirmation(
            producer=producer,
            topic_name=topic_name,
            rows=row_stream(),
            progress_message_factory=lambda count: f"[INFO] Confirmed {count:,} records in {topic_name}",
            progress_interval=progress_interval,
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


def run_producer(
    *,
    dataset_key: str,
    key_field_priority: list[str],
    progress_interval: int,
) -> None:
    """Execute a complete dataset producer run."""
    topic_name = TOPICS[dataset_key]
    source_label = get_source_label(dataset_key)

    print("=" * 80)
    print("CUSTOMERDNA AI - KAFKA PRODUCER")
    print("=" * 80)
    print(f"Dataset: {dataset_key}")
    print(f"Topic: {topic_name}")
    print(f"Source: {source_label}")

    published_count = publish_dataset(
        dataset_key=dataset_key,
        key_field_priority=key_field_priority,
        progress_interval=progress_interval,
    )

    print(f"Published rows: {published_count:,}")
    print("Kafka producer completed successfully.")
    print("=" * 80)
