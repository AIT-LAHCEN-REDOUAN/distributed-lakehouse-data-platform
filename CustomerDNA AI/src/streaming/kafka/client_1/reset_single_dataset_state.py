"""Reset one Client 1 dataset state for a targeted raw-pipeline resume."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
COMMON_DIR = CURRENT_DIR / "common"
HDFS_COMMON_DIR = CURRENT_DIR.parents[2] / "lake" / "hdfs" / "client_1" / "common"
TRINO_COMMON_DIR = CURRENT_DIR.parents[2] / "query" / "trino" / "client_1" / "common"

for import_root in (COMMON_DIR, HDFS_COMMON_DIR, TRINO_COMMON_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from hdfs_bronze_utils import (  # noqa: E402
    bronze_dataset_prefix,
    build_hdfs_client,
    ensure_bronze_root_exists,
    remove_bronze_objects,
)
from kafka_config import BRONZE_READY_TOPICS, TOPICS, get_dataset_config  # noqa: E402
from reset_client1_kafka import build_admin_client, create_topics, delete_topics  # noqa: E402
from trino_rest import TRINO_CATALOG, execute_trino_statement  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset Kafka, HDFS bronze, and Iceberg raw state for one Client 1 dataset."
    )
    parser.add_argument("--dataset-key", required=True)
    return parser.parse_args()


def reset_dataset_topics(dataset_key: str) -> None:
    topics = [
        TOPICS[dataset_key],
        BRONZE_READY_TOPICS[dataset_key],
    ]
    admin_client = build_admin_client()

    try:
        delete_topics(admin_client, topics)
        create_topics(admin_client, topics)
    finally:
        admin_client.close()


def reset_dataset_bronze(dataset_key: str) -> None:
    client = build_hdfs_client()
    ensure_bronze_root_exists(client)
    dataset_prefix = bronze_dataset_prefix(dataset_key)
    removed = remove_bronze_objects(client, dataset_prefix)
    if removed:
        print(f"[SUCCESS] Removed HDFS bronze prefix: {dataset_prefix}")
    else:
        print(f"[INFO] No HDFS bronze files found for prefix: {dataset_prefix}")


def reset_dataset_raw_table(dataset_key: str) -> None:
    dataset_config = get_dataset_config(dataset_key)
    table_name = str(dataset_config["target_table"])
    qualified_table = f'{TRINO_CATALOG}.raw_data."{table_name}"'
    execute_trino_statement(f"DROP TABLE IF EXISTS {qualified_table}")
    print(f"[SUCCESS] Dropped raw table if present: {qualified_table}")


def main() -> int:
    args = parse_args()
    dataset_key = args.dataset_key
    get_dataset_config(dataset_key)

    print("=" * 80)
    print("CUSTOMERDNA AI - SINGLE DATASET STATE RESET")
    print("=" * 80)
    print(f"Dataset: {dataset_key}")
    print(f"Kafka topic: {TOPICS[dataset_key]}")
    print(f"Bronze-ready topic: {BRONZE_READY_TOPICS[dataset_key]}")
    print(f"Bronze prefix: {bronze_dataset_prefix(dataset_key)}")
    print("=" * 80)

    reset_dataset_topics(dataset_key)
    reset_dataset_bronze(dataset_key)
    reset_dataset_raw_table(dataset_key)

    print("[SUCCESS] Targeted dataset reset completed successfully.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
