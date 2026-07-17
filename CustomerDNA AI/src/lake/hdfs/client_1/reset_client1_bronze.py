"""Delete all Client 1 bronze files from HDFS for a clean rerun."""

from __future__ import annotations

import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
COMMON_DIR = CURRENT_DIR / "common"

if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from hdfs_bronze_config import HDFS_BRONZE_ROOT, HDFS_WEB_ENDPOINT, HDFS_WEBHDFS_USER  # noqa: E402
from hdfs_bronze_utils import build_hdfs_client, ensure_bronze_root_exists, remove_bronze_objects  # noqa: E402


def main() -> None:
    print("=" * 80)
    print("CUSTOMERDNA AI - CLIENT 1 HDFS BRONZE RESET")
    print("=" * 80)
    print(f"WebHDFS endpoint: {HDFS_WEB_ENDPOINT}")
    print(f"WebHDFS user: {HDFS_WEBHDFS_USER}")
    print(f"Bronze root: {HDFS_BRONZE_ROOT}")

    client = build_hdfs_client()
    ensure_bronze_root_exists(client)
    removed = remove_bronze_objects(client, HDFS_BRONZE_ROOT)

    if removed:
        print("[SUCCESS] Cleared the Client 1 HDFS bronze root.")
    else:
        print("[INFO] No existing Client 1 HDFS bronze files were found to delete.")

    print("=" * 80)


if __name__ == "__main__":
    main()
