"""Load one Client 1 dataset from MinIO bronze into PostgreSQL raw_data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


RAW_LOAD_COMMON_DIR = Path(__file__).resolve().parent / "common"
if str(RAW_LOAD_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(RAW_LOAD_COMMON_DIR))

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
if str(CONFIG_DIR) not in sys.path:
    sys.path.insert(0, str(CONFIG_DIR))

STREAMING_COMMON_DIR = Path(__file__).resolve().parents[3] / "streaming" / "kafka" / "client_1" / "common"
if str(STREAMING_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(STREAMING_COMMON_DIR))

from bronze_raw_loader import BronzeToRawLoader  # noqa: E402
from config import CLIENT_DW_CONFIG, validate_config  # noqa: E402
from kafka_config import TOPICS, get_dataset_config  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load one Client 1 bronze dataset into PostgreSQL raw_data."
    )
    parser.add_argument(
        "--dataset-key",
        required=True,
        choices=sorted(TOPICS.keys()),
        help="Dataset key to load from MinIO bronze into raw_data.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_key = args.dataset_key
    dataset_config = get_dataset_config(dataset_key)

    print("=" * 80)
    print("CUSTOMERDNA AI - BRONZE TO RAW LOAD")
    print("=" * 80)
    print(f"Dataset: {dataset_key}")
    print(f"Topic: {TOPICS[dataset_key]}")
    print(f"Target table: {CLIENT_DW_CONFIG['raw_schema']}.{dataset_config['target_table']}")

    if not validate_config():
        return 1

    loader = BronzeToRawLoader(dataset_key=dataset_key, verbose=True)
    if not loader.connect_to_dw():
        return 1

    try:
        result = loader.load_from_bronze()
        print(f"Bronze objects read: {result.object_count:,}")
        print(f"Rows loaded: {result.rows_loaded:,}")
        print(f"Duration (seconds): {result.duration_seconds}")
        print("Bronze-to-raw load completed successfully.")
        print("=" * 80)
        return 0
    except Exception as exc:
        print(f"[ERROR] Bronze-to-raw load failed: {exc}")
        return 1
    finally:
        loader.close_connection()


if __name__ == "__main__":
    raise SystemExit(main())
