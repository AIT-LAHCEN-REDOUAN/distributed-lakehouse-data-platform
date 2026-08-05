"""Publish Client 1 online retail 2 records into Kafka."""

from __future__ import annotations

import os
import sys

COMMON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

from dataset_producer import run_producer  # noqa: E402


DATASET_KEY = "online_retail_2"
KEY_FIELD_PRIORITY = ["Invoice", "Customer ID", "StockCode"]


if __name__ == "__main__":
    run_producer(
        dataset_key=DATASET_KEY,
        key_field_priority=KEY_FIELD_PRIORITY,
        progress_interval=100000,
    )
