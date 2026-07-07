"""Consume Client 1 retailrocket category tree messages from Kafka."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from kafka import KafkaConsumer

COMMON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

from kafka_config import CONSUMER_OUTPUT_DIR, KAFKA_BOOTSTRAP_SERVERS, TOPICS  # noqa: E402


DATASET_KEY = "retailrocket_category_tree"
TOPIC_NAME = TOPICS[DATASET_KEY]


def build_consumer(topic_name: str) -> KafkaConsumer:
    return KafkaConsumer(
        topic_name,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="customerdna-client1-retailrocket-category-tree-consumer",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        key_deserializer=lambda value: value.decode("utf-8") if value else None,
        consumer_timeout_ms=10000,
    )


def persist_sample_messages(messages: list[dict[str, object]]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = CONSUMER_OUTPUT_DIR / f"retailrocket_category_tree_consumed_sample_{timestamp}.json"
    output_path.write_text(json.dumps(messages, indent=2), encoding="utf-8")
    return output_path


def consume_messages(limit: int = 10) -> tuple[int, Path]:
    consumer = build_consumer(TOPIC_NAME)
    consumed_messages: list[dict[str, object]] = []

    try:
        for index, message in enumerate(consumer, start=1):
            consumed_messages.append(
                {
                    "topic": message.topic,
                    "partition": message.partition,
                    "offset": message.offset,
                    "key": message.key,
                    "value": message.value,
                }
            )

            print(
                "[INFO] Consumed message "
                f"{index} | partition={message.partition} | offset={message.offset}"
            )

            if index >= limit:
                break
    finally:
        consumer.close()

    output_path = persist_sample_messages(consumed_messages)
    return len(consumed_messages), output_path


def main() -> None:
    print("=" * 80)
    print("CUSTOMERDNA AI - KAFKA CONSUMER")
    print("=" * 80)
    print(f"Dataset: {DATASET_KEY}")
    print(f"Topic: {TOPIC_NAME}")

    consumed_count, output_path = consume_messages()

    print(f"Consumed messages: {consumed_count:,}")
    print(f"Sample output: {output_path}")
    print("Kafka consumer completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
