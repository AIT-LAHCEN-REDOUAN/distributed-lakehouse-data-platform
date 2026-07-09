"""List the Client 1 bronze-layer Kafka objects currently stored in MinIO."""

from __future__ import annotations

import sys
from pathlib import Path


CLIENT_ROOT = Path(__file__).resolve().parent
COMMON_DIR = CLIENT_ROOT / "common"
COMMON_DIR_STR = str(COMMON_DIR)
if COMMON_DIR_STR not in sys.path:
    sys.path.insert(0, COMMON_DIR_STR)

from minio_bronze_config import MINIO_BUCKET_NAME, MINIO_ENDPOINT  # noqa: E402
from minio_bronze_utils import build_minio_client, list_bronze_objects  # noqa: E402


def main() -> int:
    print("=" * 80)
    print("CUSTOMERDNA AI - CLIENT 1 MINIO BRONZE OBJECT LIST")
    print("=" * 80)
    print(f"Endpoint: {MINIO_ENDPOINT}")
    print(f"Bucket: {MINIO_BUCKET_NAME}")

    client = build_minio_client()
    objects = list_bronze_objects(client)

    for index, object_info in enumerate(objects, start=1):
        print(f"[{index}] {object_info.object_name} | {object_info.size:,} bytes")

    print(f"Objects found: {len(objects)}")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
