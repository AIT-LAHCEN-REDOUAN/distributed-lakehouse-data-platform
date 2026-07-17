"""Consume Client 1 e-commerce churn messages from Kafka into HDFS bronze."""

from __future__ import annotations

import os
import sys

COMMON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

from bronze_consumer import run_bronze_consumer  # noqa: E402


DATASET_KEY = "ecommerce_customer_churn"
if __name__ == "__main__":
    run_bronze_consumer(DATASET_KEY)
