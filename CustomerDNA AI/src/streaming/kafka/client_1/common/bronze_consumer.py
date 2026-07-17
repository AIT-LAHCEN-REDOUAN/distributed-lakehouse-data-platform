"""Shared Kafka-to-HDFS bronze consumer workflow for Client 1 datasets."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from kafka import KafkaConsumer

from kafka_config import BRONZE_READY_TOPICS, KAFKA_BOOTSTRAP_SERVERS, TOPICS, get_dataset_config
from producer_utils import build_reliable_producer, ensure_topic_exists, get_topic_message_count

HDFS_COMMON_DIR = Path(__file__).resolve().parents[4] / "lake" / "hdfs" / "client_1" / "common"
if str(HDFS_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(HDFS_COMMON_DIR))

from hdfs_bronze_utils import (  # noqa: E402
    bronze_dataset_prefix,
    bronze_run_prefix,
    build_hdfs_client,
    ensure_bronze_root_exists,
    upload_bronze_batch_file,
)
from hdfs_bronze_config import HDFS_NAMENODE_URI, HDFS_WEB_ENDPOINT  # noqa: E402


def build_consumer(*, topic_name: str, consumer_group: str, consumer_timeout_ms: int) -> KafkaConsumer:
    """Return a Kafka consumer configured for durable bronze ingestion."""
    return KafkaConsumer(
        topic_name,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id=consumer_group,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        key_deserializer=lambda value: value.decode("utf-8") if value else None,
        consumer_timeout_ms=consumer_timeout_ms,
        max_poll_records=5000,
    )


def flush_batch_to_hdfs(
    *,
    client,
    dataset_key: str,
    run_id: str,
    batch_index: int,
    records: list[dict[str, object]],
) -> str:
    """Persist one in-memory Kafka batch as a JSONL bronze file in HDFS."""
    with NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".jsonl", delete=False) as handle:
        temp_path = Path(handle.name)
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True))
            handle.write("\n")

    try:
        object_key = upload_bronze_batch_file(
            client=client,
            dataset_key=dataset_key,
            run_id=run_id,
            batch_index=batch_index,
            local_path=temp_path,
        )
    finally:
        temp_path.unlink(missing_ok=True)

    return object_key


def build_bronze_ready_event(
    *,
    dataset_key: str,
    run_id: str,
    source_topic_name: str,
    target_table: str,
    uploaded_objects: int,
    total_consumed: int,
) -> dict[str, object]:
    """Build the Kafka event that signals one bronze run is ready for warehouse loading."""
    return {
        "client_id": "client_1",
        "dataset_name": dataset_key,
        "source_topic_name": source_topic_name,
        "bronze_ready_topic_name": BRONZE_READY_TOPICS[dataset_key],
        "bronze_dataset_prefix": bronze_dataset_prefix(dataset_key),
        "bronze_run_prefix": bronze_run_prefix(dataset_key, run_id),
        "storage_type": "hdfs",
        "hdfs_web_endpoint": HDFS_WEB_ENDPOINT,
        "hdfs_namenode_uri": HDFS_NAMENODE_URI,
        "run_id": run_id,
        "target_table": target_table,
        "file_count": uploaded_objects,
        "row_count": total_consumed,
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "load_mode": "kafka_bronze_ready_event",
    }


def publish_bronze_ready_event(dataset_key: str, event_payload: dict[str, object]) -> None:
    """Publish a single Kafka event that points the DW loader to the exact bronze run."""
    topic_name = BRONZE_READY_TOPICS[dataset_key]
    ensure_topic_exists(topic_name)

    topic_count_before = get_topic_message_count(topic_name)
    producer = build_reliable_producer()

    try:
        delivery_future = producer.send(topic_name, key=dataset_key, value=event_payload)
        producer.flush()
        delivery_future.get(timeout=60)
    finally:
        producer.close()

    topic_count_after = get_topic_message_count(topic_name)
    topic_delta = topic_count_after - topic_count_before
    if topic_delta != 1:
        raise RuntimeError(
            f"Bronze-ready topic growth mismatch for {topic_name}: "
            f"expected delta 1, observed {topic_delta}."
        )

    print(f"[INFO] Published bronze-ready event to {topic_name}")


def run_bronze_consumer(dataset_key: str) -> None:
    """Consume one dataset topic fully and persist it into the HDFS bronze layer."""
    dataset_config = get_dataset_config(dataset_key)
    topic_name = TOPICS[dataset_key]
    target_table = str(dataset_config["target_table"])
    expected_rows = get_topic_message_count(topic_name)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    consumer_group = f"customerdna-client1-{dataset_key}-bronze-{run_id.lower()}"
    consumer_timeout_ms = int(dataset_config["bronze_consumer_timeout_ms"])
    bronze_flush_rows = int(dataset_config["bronze_flush_rows"])
    progress_interval = int(dataset_config["bronze_progress_interval"])

    print("=" * 80)
    print("CUSTOMERDNA AI - KAFKA TO HDFS BRONZE")
    print("=" * 80)
    print(f"Dataset: {dataset_key}")
    print(f"Topic: {topic_name}")
    print(f"Bronze prefix: {bronze_dataset_prefix(dataset_key)}")
    print(f"WebHDFS endpoint: {HDFS_WEB_ENDPOINT}")
    print(f"Expected topic rows: {expected_rows:,}")

    client = build_hdfs_client()
    ensure_bronze_root_exists(client)
    consumer = build_consumer(
        topic_name=topic_name,
        consumer_group=consumer_group,
        consumer_timeout_ms=consumer_timeout_ms,
    )

    total_consumed = 0
    uploaded_objects = 0
    buffered_records: list[dict[str, object]] = []

    try:
        for message in consumer:
            buffered_records.append(message.value)

            if len(buffered_records) >= bronze_flush_rows:
                uploaded_objects += 1
                object_key = flush_batch_to_hdfs(
                    client=client,
                    dataset_key=dataset_key,
                    run_id=run_id,
                    batch_index=uploaded_objects,
                    records=buffered_records,
                )
                total_consumed += len(buffered_records)
                consumer.commit()
                print(
                    f"[INFO] Uploaded bronze batch {uploaded_objects:,} "
                    f"({len(buffered_records):,} rows) -> {object_key}"
                )
                if total_consumed % progress_interval == 0:
                    print(f"[INFO] Confirmed {total_consumed:,} rows consumed into bronze")
                buffered_records = []

        if buffered_records:
            uploaded_objects += 1
            object_key = flush_batch_to_hdfs(
                client=client,
                dataset_key=dataset_key,
                run_id=run_id,
                batch_index=uploaded_objects,
                records=buffered_records,
            )
            total_consumed += len(buffered_records)
            consumer.commit()
            print(
                f"[INFO] Uploaded bronze batch {uploaded_objects:,} "
                f"({len(buffered_records):,} rows) -> {object_key}"
            )

        if total_consumed == 0:
            raise RuntimeError(
                f"No Kafka messages were consumed for {dataset_key}. "
                "The bronze layer was not updated."
            )

        if total_consumed != expected_rows:
            raise RuntimeError(
                f"Kafka-to-bronze row mismatch for {dataset_key}: "
                f"expected {expected_rows:,}, consumed {total_consumed:,}."
            )

        bronze_ready_event = build_bronze_ready_event(
            dataset_key=dataset_key,
            run_id=run_id,
            source_topic_name=topic_name,
            target_table=target_table,
            uploaded_objects=uploaded_objects,
            total_consumed=total_consumed,
        )
        publish_bronze_ready_event(dataset_key, bronze_ready_event)

        print(f"Consumed rows: {total_consumed:,}")
        print(f"Bronze files uploaded: {uploaded_objects:,}")
        print(f"Bronze run prefix: {bronze_run_prefix(dataset_key, run_id)}")
        print(f"Bronze-ready event topic: {BRONZE_READY_TOPICS[dataset_key]}")
        print("Kafka-to-HDFS bronze completed successfully.")
        print("=" * 80)
    finally:
        consumer.close()
