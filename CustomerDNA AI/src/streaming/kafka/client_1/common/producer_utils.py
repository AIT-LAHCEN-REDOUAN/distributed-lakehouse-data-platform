"""Shared reliability helpers for Client 1 Kafka producers."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Iterable

from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer, TopicPartition
from kafka.admin import NewTopic
from kafka.errors import RequestTimedOutError, TopicAlreadyExistsError

from kafka_config import KAFKA_BOOTSTRAP_SERVERS


DEFAULT_TOPIC_PARTITIONS = max(1, int(os.getenv("CUSTOMERDNA_KAFKA_DEFAULT_PARTITIONS", "3")))
DEFAULT_TOPIC_REPLICATION_FACTOR = max(
    1,
    int(os.getenv("CUSTOMERDNA_KAFKA_REPLICATION_FACTOR", "1")),
)
DEFAULT_TOPIC_MIN_INSYNC_REPLICAS = max(
    1,
    int(os.getenv("CUSTOMERDNA_KAFKA_MIN_INSYNC_REPLICAS", "1")),
)
TOPIC_CREATION_CONFIRM_TIMEOUT_SECONDS = max(
    10,
    int(os.getenv("CUSTOMERDNA_KAFKA_TOPIC_CONFIRM_TIMEOUT_SECONDS", "90")),
)


def _wait_for_topic_visibility(admin_client: KafkaAdminClient, topic_name: str) -> None:
    """Wait until the created topic is visible in Kafka metadata."""
    deadline = time.time() + TOPIC_CREATION_CONFIRM_TIMEOUT_SECONDS

    while time.time() < deadline:
        if topic_name in set(admin_client.list_topics()):
            print(f"[INFO] Topic ready: {topic_name}")
            return
        time.sleep(1)

    raise TimeoutError(
        f"Timed out while waiting for Kafka topic metadata to include '{topic_name}'."
    )


def build_reliable_producer() -> KafkaProducer:
    """Return a Kafka producer configured for durable batch publishing."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        acks="all",
        retries=20,
        linger_ms=25,
        batch_size=131072,
        request_timeout_ms=60000,
        max_block_ms=120000,
        compression_type="gzip",
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda value: value.encode("utf-8") if value else None,
    )


def ensure_topic_exists(
    topic_name: str,
    *,
    num_partitions: int = DEFAULT_TOPIC_PARTITIONS,
    replication_factor: int = DEFAULT_TOPIC_REPLICATION_FACTOR,
) -> None:
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
                    num_partitions=num_partitions,
                    replication_factor=replication_factor,
                    topic_configs={
                        "min.insync.replicas": str(
                            min(DEFAULT_TOPIC_MIN_INSYNC_REPLICAS, replication_factor)
                        )
                    },
                )
            ],
            validate_only=False,
        )
    except TopicAlreadyExistsError:
        print(f"[INFO] Topic already exists: {topic_name}")
    except RequestTimedOutError:
        print(
            f"[WARN] Topic creation timed out for {topic_name}. "
            "Verifying whether Kafka completed the operation anyway..."
        )
    else:
        print(f"[INFO] Created topic request sent: {topic_name}")
        _wait_for_topic_visibility(admin_client, topic_name)
        return
    finally:
        if 'admin_client' in locals():
            admin_client.close()

    admin_client = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        client_id="customerdna-client1-topic-admin-postcheck",
    )
    try:
        _wait_for_topic_visibility(admin_client, topic_name)
    finally:
        admin_client.close()


def _get_topic_partitions(topic_name: str) -> list[TopicPartition]:
    """Fetch topic partitions, retrying briefly until metadata is available."""
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        enable_auto_commit=False,
        consumer_timeout_ms=1000,
    )

    try:
        for _ in range(10):
            partition_ids = consumer.partitions_for_topic(topic_name)
            if partition_ids:
                return [TopicPartition(topic_name, partition_id) for partition_id in sorted(partition_ids)]

            time.sleep(1)

        raise RuntimeError(f"Unable to fetch partitions for topic '{topic_name}'.")
    finally:
        consumer.close()


def get_topic_message_count(topic_name: str) -> int:
    """Return the current total number of messages stored in the topic."""
    partitions = _get_topic_partitions(topic_name)
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        enable_auto_commit=False,
        consumer_timeout_ms=1000,
    )

    try:
        end_offsets = consumer.end_offsets(partitions)
        return sum(end_offsets.values())
    finally:
        consumer.close()


def publish_with_confirmation(
    *,
    producer: KafkaProducer,
    topic_name: str,
    rows: Iterable[tuple[str, dict[str, object]]],
    progress_message_factory: Callable[[int], str],
    progress_interval: int = 1000,
) -> int:
    """Publish rows and count only rows confirmed by Kafka."""
    delivery_futures = []
    confirmed_count = 0

    for message_index, (message_key, message_value) in enumerate(rows, start=1):
        delivery_futures.append(producer.send(topic_name, key=message_key, value=message_value))

        if message_index % progress_interval == 0:
            confirmed_count += _drain_delivery_futures(delivery_futures)
            delivery_futures.clear()
            print(progress_message_factory(confirmed_count))

    producer.flush()

    if delivery_futures:
        confirmed_count += _drain_delivery_futures(delivery_futures)

    return confirmed_count


def _drain_delivery_futures(delivery_futures: list) -> int:
    """Wait for Kafka acknowledgements and raise immediately on failure."""
    confirmed_count = 0

    for future in delivery_futures:
        future.get(timeout=60)
        confirmed_count += 1

    return confirmed_count
