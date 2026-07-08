"""Common Kafka configuration for Client 1 source-to-Kafka ingestion."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    """Return the repository root."""
    return Path(__file__).resolve().parents[6]


def customerdna_root() -> Path:
    """Return the CustomerDNA project root in both local and container environments."""
    current_path = Path(__file__).resolve()

    for candidate in current_path.parents:
        if (candidate / "src").is_dir() and (candidate / "datasets").is_dir():
            return candidate

    fallback_path = project_root() / "CustomerDNA AI"
    return fallback_path


STREAMING_ROOT = Path(__file__).resolve().parents[2]
CLIENT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATASETS_ROOT = customerdna_root() / "datasets" / "client_1"

def get_kafka_bootstrap_servers() -> list[str]:
    """Return Kafka bootstrap servers from environment or sensible defaults."""
    configured_value = os.getenv("CUSTOMERDNA_KAFKA_BOOTSTRAP_SERVERS", "").strip()

    if configured_value:
        return [server.strip() for server in configured_value.split(",") if server.strip()]

    return ["localhost:9092"]


KAFKA_BOOTSTRAP_SERVERS = get_kafka_bootstrap_servers()

TOPICS = {
    "marketing_campaign": "client1.marketing_campaign",
    "ecommerce_customer_churn": "client1.ecommerce_customer_churn",
    "retailrocket_category_tree": "client1.retailrocket_category_tree",
    "retailrocket_events": "client1.retailrocket_events",
    "retailrocket_item_properties": "client1.retailrocket_item_properties",
    "online_retail": "client1.online_retail",
}

SOURCE_DATASET_CONFIGS = {
    "marketing_campaign": {
        "source_paths": [
            SOURCE_DATASETS_ROOT / "Customer_Personality_Analysis" / "marketing_campaign.csv",
        ],
        "source_label": "marketing_campaign.csv",
        "source_type": "csv",
        "delimiter": "\t",
        "encoding": "utf-8",
    },
    "ecommerce_customer_churn": {
        "source_paths": [
            SOURCE_DATASETS_ROOT / "E-commerce_customer_churn" / "E-commerce_customer_churn.xlsx",
        ],
        "source_label": "E-commerce_customer_churn.xlsx",
        "source_type": "excel",
        "sheet_name": "E Comm",
    },
    "retailrocket_category_tree": {
        "source_paths": [
            SOURCE_DATASETS_ROOT / "Retailrocket_recommender_system_dataset" / "category_tree.csv",
        ],
        "source_label": "category_tree.csv",
        "source_type": "csv",
        "delimiter": ",",
        "encoding": "utf-8",
    },
    "retailrocket_events": {
        "source_paths": [
            SOURCE_DATASETS_ROOT / "Retailrocket_recommender_system_dataset" / "events.csv",
        ],
        "source_label": "events.csv",
        "source_type": "csv",
        "delimiter": ",",
        "encoding": "utf-8",
    },
    "retailrocket_item_properties": {
        "source_paths": [
            SOURCE_DATASETS_ROOT / "Retailrocket_recommender_system_dataset" / "item_properties_part1.csv",
            SOURCE_DATASETS_ROOT / "Retailrocket_recommender_system_dataset" / "item_properties_part2.csv",
        ],
        "source_label": "item_properties_part1.csv + item_properties_part2.csv",
        "source_type": "csv_multi",
        "delimiter": ",",
        "encoding": "utf-8",
    },
    "online_retail": {
        "source_paths": [
            SOURCE_DATASETS_ROOT / "UCI_Online_Retail_2" / "online_retail_2.xlsx",
        ],
        "source_label": "online_retail_2.xlsx",
        "source_type": "excel_multi_sheet",
        "sheet_names": ["Year 2009-2010", "Year 2010-2011"],
    },
}

LOG_OUTPUT_DIR = STREAMING_ROOT / "logs" / "client_1"
LOG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONSUMER_OUTPUT_DIR = STREAMING_ROOT / "consumer_output" / "client_1"
CONSUMER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
