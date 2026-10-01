"""Consume the bronze-ready event for Client 1 bank marketing and load it to raw_data."""

from __future__ import annotations

import os
import sys

COMMON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

from load_event_consumer import run_load_event_consumer  # noqa: E402


DATASET_KEY = "bank_marketing"


if __name__ == "__main__":
    run_load_event_consumer(DATASET_KEY)
