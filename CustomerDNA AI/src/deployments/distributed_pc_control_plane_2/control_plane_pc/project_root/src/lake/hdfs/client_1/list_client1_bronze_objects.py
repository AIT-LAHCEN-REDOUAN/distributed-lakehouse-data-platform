"""List the Client 1 bronze-layer files currently stored in HDFS."""

from __future__ import annotations

import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
COMMON_DIR = CURRENT_DIR / "common"

if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from hdfs_bronze_config import HDFS_BRONZE_ROOT, HDFS_WEB_ENDPOINT  # noqa: E402
from hdfs_bronze_utils import build_hdfs_client, list_bronze_objects_by_prefix  # noqa: E402


def main() -> None:
    print("=" * 80)
    print("CUSTOMERDNA AI - CLIENT 1 HDFS BRONZE LIST")
    print("=" * 80)
    print(f"WebHDFS endpoint: {HDFS_WEB_ENDPOINT}")
    print(f"Bronze root: {HDFS_BRONZE_ROOT}")

    client = build_hdfs_client()
    bronze_files = sorted(
        list_bronze_objects_by_prefix(client, HDFS_BRONZE_ROOT),
        key=lambda item: item.object_name,
    )

    if not bronze_files:
        print("[INFO] No Client 1 bronze files were found.")
    else:
        for file_info in bronze_files:
            print(f"{file_info.object_name} | {file_info.length:,} bytes")
        print(f"[SUCCESS] Listed {len(bronze_files):,} bronze files.")

    print("=" * 80)


if __name__ == "__main__":
    main()
