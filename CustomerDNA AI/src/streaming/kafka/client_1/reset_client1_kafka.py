"""Reset Client 1 Kafka topics and local Kafka logs."""

from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

CURRENT_DIR = Path(__file__).resolve().parent
COMMON_DIR = CURRENT_DIR / "common"

if str(COMMON_DIR) not in sys.path:
    sys.path.append(str(COMMON_DIR))

from kafka_config import (  # noqa: E402
    ALL_TOPICS,
    KAFKA_BOOTSTRAP_SERVERS,
    LOG_OUTPUT_DIR,
)


TOPIC_PARTITIONS = 3
TOPIC_REPLICATION_FACTOR = 1


def build_admin_client() -> KafkaAdminClient:
    """Create a Kafka admin client for reset operations."""
    return KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        client_id="customerdna-client1-kafka-reset",
    )


def delete_topics(admin_client: KafkaAdminClient, topics: list[str]) -> None:
    """Delete Client 1 topics if they exist."""
    existing_topics = set(admin_client.list_topics())
    topics_to_delete = [topic for topic in topics if topic in existing_topics]

    if not topics_to_delete:
        print("[INFO] No existing Client 1 topics were found to delete.")
        return

    admin_client.delete_topics(topics=topics_to_delete)

    for topic in topics_to_delete:
        print(f"[INFO] Delete requested for topic: {topic}")

    wait_for_topic_deletion(admin_client, topics_to_delete)


def wait_for_topic_deletion(admin_client: KafkaAdminClient, topics: list[str], timeout_seconds: int = 60) -> None:
    """Wait until topics disappear from Kafka metadata."""
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        existing_topics = set(admin_client.list_topics())
        remaining_topics = [topic for topic in topics if topic in existing_topics]

        if not remaining_topics:
            for topic in topics:
                print(f"[SUCCESS] Deleted topic: {topic}")
            return

        time.sleep(1)

    raise TimeoutError(f"Timed out while waiting for topic deletion: {', '.join(topics)}")


def create_topics(admin_client: KafkaAdminClient, topics: list[str]) -> None:
    """Recreate Client 1 topics as empty topics."""
    new_topics = [
        NewTopic(
            name=topic,
            num_partitions=TOPIC_PARTITIONS,
            replication_factor=TOPIC_REPLICATION_FACTOR,
        )
        for topic in topics
    ]

    try:
        admin_client.create_topics(new_topics=new_topics, validate_only=False)
    except TopicAlreadyExistsError:
        print("[INFO] One or more topics already existed during recreation.")

    for topic in topics:
        print(f"[SUCCESS] Created empty topic: {topic}")


def clear_directory_contents(target_dir: Path) -> int:
    """Remove files and folders inside the target directory while keeping the directory itself."""
    target_dir.mkdir(parents=True, exist_ok=True)
    removed_items = 0

    for item in target_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
        removed_items += 1

    return removed_items


def main() -> None:
    """Reset Client 1 Kafka topics and local log artifacts."""
    topics = list(ALL_TOPICS)

    print("=" * 80)
    print("CUSTOMERDNA AI - CLIENT 1 KAFKA RESET")
    print("=" * 80)
    print(f"Bootstrap servers: {', '.join(KAFKA_BOOTSTRAP_SERVERS)}")
    print("Topics to reset:")

    for topic in topics:
        print(f"  - {topic}")

    admin_client = build_admin_client()

    try:
        delete_topics(admin_client, topics)
        create_topics(admin_client, topics)
    finally:
        admin_client.close()

    removed_logs = clear_directory_contents(LOG_OUTPUT_DIR)

    print(f"[INFO] Cleared Kafka log artifacts: {removed_logs}")
    print("[INFO] Data warehouse tables were not modified by this reset script.")
    print("Kafka reset completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
