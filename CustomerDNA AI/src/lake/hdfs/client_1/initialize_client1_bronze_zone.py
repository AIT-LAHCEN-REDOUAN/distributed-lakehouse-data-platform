"""Ensure the Client 1 bronze root exists in HDFS."""

from __future__ import annotations

import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
COMMON_DIR = CURRENT_DIR / "common"

if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from hdfs_bronze_config import (  # noqa: E402
    HDFS_BRONZE_ROOT,
    HDFS_WEB_ENDPOINT,
    HDFS_WEBHDFS_USER,
    describe_hdfs_access,
)
from hdfs_bronze_utils import build_hdfs_client, ensure_bronze_root_exists  # noqa: E402


def main() -> int:
    print("=" * 80)
    print("CUSTOMERDNA AI - HDFS BRONZE ZONE INITIALIZATION")
    print("=" * 80)
    print(f"HDFS access mode: {describe_hdfs_access()}")
    print(f"WebHDFS endpoint: {HDFS_WEB_ENDPOINT}")
    print(f"WebHDFS user: {HDFS_WEBHDFS_USER}")
    print(f"Bronze root: {HDFS_BRONZE_ROOT}")

    client = build_hdfs_client()
    ensure_bronze_root_exists(client)

    if not client.path_exists(HDFS_BRONZE_ROOT):
        raise RuntimeError(f"Bronze root '{HDFS_BRONZE_ROOT}' does not exist after initialization.")

    print("[SUCCESS] Client 1 bronze zone is ready.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
