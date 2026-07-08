"""Publish Client 1 retailrocket category tree records into Kafka."""

from __future__ import annotations

import os
import sys

COMMON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

from dataset_producer import run_producer  # noqa: E402


DATASET_KEY = "retailrocket_category_tree"
KEY_FIELD_PRIORITY = ["categoryid"]


if __name__ == "__main__":
    run_producer(
        dataset_key=DATASET_KEY,
        key_field_priority=KEY_FIELD_PRIORITY,
        progress_interval=500,
    )
