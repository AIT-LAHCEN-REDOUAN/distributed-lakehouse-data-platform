"""Reset Client 1 Kafka topics and local Kafka logs."""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import NoBrokersAvailable, RequestTimedOutError, TopicAlreadyExistsError

CURRENT_DIR = Path(__file__).resolve().parent
COMMON_DIR = CURRENT_DIR / "common"

if str(COMMON_DIR) not in sys.path:
    sys.path.append(str(COMMON_DIR))

from kafka_config import (  # noqa: E402
    ALL_TOPICS,
    KAFKA_BOOTSTRAP_SERVERS,
    LOG_OUTPUT_DIR,
)


TOPIC_PARTITIONS = max(1, int(os.getenv("CUSTOMERDNA_KAFKA_DEFAULT_PARTITIONS", "3")))
TOPIC_REPLICATION_FACTOR = max(1, int(os.getenv("CUSTOMERDNA_KAFKA_REPLICATION_FACTOR", "1")))
TOPIC_MIN_INSYNC_REPLICAS = max(1, int(os.getenv("CUSTOMERDNA_KAFKA_MIN_INSYNC_REPLICAS", "1")))
KAFKA_ADMIN_CONNECT_TIMEOUT_SECONDS = max(
    5,
    int(os.getenv("CUSTOMERDNA_KAFKA_ADMIN_CONNECT_TIMEOUT_SECONDS", "90")),
)
KAFKA_ADMIN_CONNECT_RETRY_INTERVAL_SECONDS = max(
    1,
    int(os.getenv("CUSTOMERDNA_KAFKA_ADMIN_CONNECT_RETRY_INTERVAL_SECONDS", "5")),
)
KAFKA_TOPIC_STATE_TIMEOUT_SECONDS = max(
    30,
    int(os.getenv("CUSTOMERDNA_KAFKA_TOPIC_STATE_TIMEOUT_SECONDS", "120")),
)
KAFKA_TOPIC_STATE_POLL_INTERVAL_SECONDS = max(
    1,
    int(os.getenv("CUSTOMERDNA_KAFKA_TOPIC_STATE_POLL_INTERVAL_SECONDS", "2")),
)
KAFKA_TOPIC_DELETE_ATTEMPTS = max(
    1,
    int(os.getenv("CUSTOMERDNA_KAFKA_TOPIC_DELETE_ATTEMPTS", "3")),
)


def list_topics_with_retry(
    admin_client: KafkaAdminClient,
    *,
    operation_label: str,
    timeout_seconds: int = KAFKA_TOPIC_STATE_TIMEOUT_SECONDS,
) -> set[str]:
    """Fetch Kafka topic metadata with short retries during controller churn."""
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            return set(admin_client.list_topics())
        except (RequestTimedOutError, NoBrokersAvailable) as exc:
            last_error = exc
            print(
                f"[WARN] Kafka metadata not ready while {operation_label}. "
                f"Retrying in {KAFKA_TOPIC_STATE_POLL_INTERVAL_SECONDS}s..."
            )
            time.sleep(KAFKA_TOPIC_STATE_POLL_INTERVAL_SECONDS)

    raise RuntimeError(
        f"Timed out while fetching Kafka topic metadata during {operation_label}."
    ) from last_error


def build_admin_client() -> KafkaAdminClient:
    """Create a Kafka admin client for reset operations with brief broker readiness retries."""
    deadline = time.time() + KAFKA_ADMIN_CONNECT_TIMEOUT_SECONDS
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                client_id="customerdna-client1-kafka-reset",
                request_timeout_ms=30000,
                api_version_auto_timeout_ms=10000,
            )
            # Force metadata fetch so we only continue once the broker is truly usable.
            list_topics_with_retry(
                admin_client,
                operation_label="waiting for Kafka admin connectivity",
                timeout_seconds=15,
            )
            return admin_client
        except NoBrokersAvailable as exc:
            last_error = exc
            print(
                "[WARN] Kafka brokers are not ready yet. "
                f"Retrying in {KAFKA_ADMIN_CONNECT_RETRY_INTERVAL_SECONDS}s..."
            )
            time.sleep(KAFKA_ADMIN_CONNECT_RETRY_INTERVAL_SECONDS)

    raise RuntimeError(
        "Kafka brokers did not become ready in time for reset operations."
    ) from last_error


def delete_topics(admin_client: KafkaAdminClient, topics: list[str]) -> None:
    """Delete Client 1 topics if they exist."""
    existing_topics = list_topics_with_retry(
        admin_client,
        operation_label="discovering topics to delete",
    )
    topics_to_delete = [topic for topic in topics if topic in existing_topics]

    if not topics_to_delete:
        print("[INFO] No existing Client 1 topics were found to delete.")
        return

    last_timeout: RequestTimedOutError | None = None
    for attempt in range(1, KAFKA_TOPIC_DELETE_ATTEMPTS + 1):
        try:
            admin_client.delete_topics(topics=topics_to_delete)
            last_timeout = None
            break
        except RequestTimedOutError as exc:
            last_timeout = exc
            print(
                "[WARN] Kafka topic deletion request timed out while waiting for the controller. "
                f"Attempt {attempt}/{KAFKA_TOPIC_DELETE_ATTEMPTS}. "
                "Verifying whether deletion is already progressing..."
            )
            try:
                remaining_topics = [
                    topic
                    for topic in topics_to_delete
                    if topic in list_topics_with_retry(
                        admin_client,
                        operation_label="verifying timed-out topic deletion",
                        timeout_seconds=15,
                    )
                ]
            except RuntimeError:
                remaining_topics = topics_to_delete

            if not remaining_topics:
                last_timeout = None
                break

            if attempt == KAFKA_TOPIC_DELETE_ATTEMPTS:
                raise

            time.sleep(KAFKA_TOPIC_STATE_POLL_INTERVAL_SECONDS)

    for topic in topics_to_delete:
        print(f"[INFO] Delete requested for topic: {topic}")

    wait_for_topic_deletion(admin_client, topics_to_delete)


def wait_for_topic_deletion(
    admin_client: KafkaAdminClient,
    topics: list[str],
    timeout_seconds: int = KAFKA_TOPIC_STATE_TIMEOUT_SECONDS,
) -> None:
    """Wait until topics disappear from Kafka metadata."""
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        existing_topics = list_topics_with_retry(
            admin_client,
            operation_label="waiting for topic deletion",
            timeout_seconds=15,
        )
        remaining_topics = [topic for topic in topics if topic in existing_topics]

        if not remaining_topics:
            for topic in topics:
                print(f"[SUCCESS] Deleted topic: {topic}")
            return

        time.sleep(KAFKA_TOPIC_STATE_POLL_INTERVAL_SECONDS)

    raise TimeoutError(f"Timed out while waiting for topic deletion: {', '.join(topics)}")


def wait_for_topic_creation(
    admin_client: KafkaAdminClient,
    topics: list[str],
    timeout_seconds: int = KAFKA_TOPIC_STATE_TIMEOUT_SECONDS,
) -> None:
    """Wait until every expected topic appears in Kafka metadata."""
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        existing_topics = list_topics_with_retry(
            admin_client,
            operation_label="waiting for topic creation",
            timeout_seconds=15,
        )
        missing_topics = [topic for topic in topics if topic not in existing_topics]

        if not missing_topics:
            for topic in topics:
                print(f"[SUCCESS] Created empty topic: {topic}")
            return

        time.sleep(KAFKA_TOPIC_STATE_POLL_INTERVAL_SECONDS)

    raise TimeoutError(f"Timed out while waiting for topic creation: {', '.join(topics)}")


def create_topics(admin_client: KafkaAdminClient, topics: list[str]) -> None:
    """Recreate Client 1 topics as empty topics."""
    new_topics = [
        NewTopic(
            name=topic,
            num_partitions=TOPIC_PARTITIONS,
            replication_factor=TOPIC_REPLICATION_FACTOR,
            topic_configs={
                "min.insync.replicas": str(min(TOPIC_MIN_INSYNC_REPLICAS, TOPIC_REPLICATION_FACTOR))
            },
        )
        for topic in topics
    ]

    try:
        admin_client.create_topics(new_topics=new_topics, validate_only=False)
    except TopicAlreadyExistsError:
        print("[INFO] One or more topics already existed during recreation.")
    except RequestTimedOutError:
        print(
            "[WARN] Kafka topic creation request timed out while waiting for the controller. "
            "Verifying whether the topics were created anyway..."
        )

    wait_for_topic_creation(admin_client, topics)


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
