"""Consume Client 1 retailrocket category tree messages from Kafka into HDFS bronze."""

from __future__ import annotations

import os
import sys

COMMON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

from bronze_consumer import run_bronze_consumer  # noqa: E402


DATASET_KEY = "retailrocket_category_tree"
if __name__ == "__main__":
    run_bronze_consumer(DATASET_KEY)
