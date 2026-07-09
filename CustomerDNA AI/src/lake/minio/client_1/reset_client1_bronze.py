"""Delete all Client 1 Kafka bronze objects from MinIO for a clean rerun."""

from __future__ import annotations

import sys
from pathlib import Path


CLIENT_ROOT = Path(__file__).resolve().parent
COMMON_DIR = CLIENT_ROOT / "common"
COMMON_DIR_STR = str(COMMON_DIR)
if COMMON_DIR_STR not in sys.path:
    sys.path.insert(0, COMMON_DIR_STR)

from minio_bronze_config import MINIO_BUCKET_NAME, MINIO_ENDPOINT  # noqa: E402
from minio_bronze_utils import build_minio_client, remove_bronze_objects  # noqa: E402


def main() -> int:
    print("=" * 80)
    print("CUSTOMERDNA AI - RESET CLIENT 1 MINIO BRONZE")
    print("=" * 80)
    print(f"Endpoint: {MINIO_ENDPOINT}")
    print(f"Bucket: {MINIO_BUCKET_NAME}")

    client = build_minio_client()
    deleted_count = remove_bronze_objects(client)

    if deleted_count == 0:
        print("[INFO] No Client 1 bronze objects found to delete.")
        print("=" * 80)
        return 0

    print(f"Deleted objects: {deleted_count}")
    print("Client 1 bronze objects removed successfully.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
