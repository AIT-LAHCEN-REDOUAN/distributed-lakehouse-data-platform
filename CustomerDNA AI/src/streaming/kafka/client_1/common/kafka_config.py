"""Common Kafka and dataset configuration for the Client 1 ingestion backbone."""

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

DATASET_ORDER = [
    "retailrocket_category_tree",
    "marketing_campaign",
    "ecommerce_customer_churn",
    "online_retail",
    "retailrocket_events",
    "retailrocket_item_properties",
]

DATASET_PIPELINE_CONFIGS = {
    "marketing_campaign": {
        "topic_name": "client1.marketing_campaign",
        "bronze_ready_topic_name": "client1.marketing_campaign.bronze_ready",
        "target_table": "marketing_campaign",
        "key_field_priority": ["ID"],
        "produce_progress_interval": 500,
        "bronze_flush_rows": 5000,
        "bronze_progress_interval": 500,
        "bronze_consumer_timeout_ms": 30000,
        "load_event_consumer_timeout_ms": 30000,
        "load_copy_batch_size": 5000,
        "load_progress_interval": 1000,
        "source_paths": [
            SOURCE_DATASETS_ROOT / "Customer_Personality_Analysis" / "marketing_campaign.csv",
        ],
        "source_label": "marketing_campaign.csv",
        "source_type": "csv",
        "delimiter": "\t",
        "encoding": "utf-8",
    },
    "ecommerce_customer_churn": {
        "topic_name": "client1.ecommerce_customer_churn",
        "bronze_ready_topic_name": "client1.ecommerce_customer_churn.bronze_ready",
        "target_table": "e_commerce_customer_churn",
        "key_field_priority": ["CustomerID", "customerid"],
        "produce_progress_interval": 500,
        "bronze_flush_rows": 5000,
        "bronze_progress_interval": 1000,
        "bronze_consumer_timeout_ms": 30000,
        "load_event_consumer_timeout_ms": 30000,
        "load_copy_batch_size": 5000,
        "load_progress_interval": 2000,
        "source_paths": [
            SOURCE_DATASETS_ROOT / "E-commerce_customer_churn" / "E-commerce_customer_churn.xlsx",
        ],
        "source_label": "E-commerce_customer_churn.xlsx",
        "source_type": "excel",
        "sheet_name": "E Comm",
    },
    "retailrocket_category_tree": {
        "topic_name": "client1.retailrocket_category_tree",
        "bronze_ready_topic_name": "client1.retailrocket_category_tree.bronze_ready",
        "target_table": "category_tree",
        "key_field_priority": ["categoryid"],
        "produce_progress_interval": 500,
        "bronze_flush_rows": 5000,
        "bronze_progress_interval": 500,
        "bronze_consumer_timeout_ms": 30000,
        "load_event_consumer_timeout_ms": 30000,
        "load_copy_batch_size": 5000,
        "load_progress_interval": 1000,
        "source_paths": [
            SOURCE_DATASETS_ROOT / "Retailrocket_recommender_system_dataset" / "category_tree.csv",
        ],
        "source_label": "category_tree.csv",
        "source_type": "csv",
        "delimiter": ",",
        "encoding": "utf-8",
    },
    "retailrocket_events": {
        "topic_name": "client1.retailrocket_events",
        "bronze_ready_topic_name": "client1.retailrocket_events.bronze_ready",
        "target_table": "events",
        "key_field_priority": ["visitorid", "itemid", "timestamp"],
        "produce_progress_interval": 100000,
        "bronze_flush_rows": 50000,
        "bronze_progress_interval": 100000,
        "bronze_consumer_timeout_ms": 45000,
        "load_event_consumer_timeout_ms": 45000,
        "load_copy_batch_size": 20000,
        "load_progress_interval": 100000,
        "source_paths": [
            SOURCE_DATASETS_ROOT / "Retailrocket_recommender_system_dataset" / "events.csv",
        ],
        "source_label": "events.csv",
        "source_type": "csv",
        "delimiter": ",",
        "encoding": "utf-8",
    },
    "retailrocket_item_properties": {
        "topic_name": "client1.retailrocket_item_properties",
        "bronze_ready_topic_name": "client1.retailrocket_item_properties.bronze_ready",
        "target_table": "item_properties",
        "key_field_priority": ["itemid", "property", "timestamp"],
        "produce_progress_interval": 500000,
        "bronze_flush_rows": 50000,
        "bronze_progress_interval": 500000,
        "bronze_consumer_timeout_ms": 60000,
        "load_event_consumer_timeout_ms": 60000,
        "load_copy_batch_size": 20000,
        "load_progress_interval": 500000,
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
        "topic_name": "client1.online_retail",
        "bronze_ready_topic_name": "client1.online_retail.bronze_ready",
        "target_table": "online_retail",
        "key_field_priority": ["Invoice", "Customer ID", "StockCode"],
        "produce_progress_interval": 100000,
        "bronze_flush_rows": 20000,
        "bronze_progress_interval": 100000,
        "bronze_consumer_timeout_ms": 45000,
        "load_event_consumer_timeout_ms": 45000,
        "load_copy_batch_size": 15000,
        "load_progress_interval": 100000,
        "source_paths": [
            SOURCE_DATASETS_ROOT / "UCI_Online_Retail_2" / "online_retail_2.xlsx",
        ],
        "source_label": "online_retail_2.xlsx",
        "source_type": "excel_multi_sheet",
        "sheet_names": ["Year 2009-2010", "Year 2010-2011"],
    },
}

SOURCE_DATASET_CONFIGS = DATASET_PIPELINE_CONFIGS
TOPICS = {
    dataset_key: dataset_config["topic_name"]
    for dataset_key, dataset_config in DATASET_PIPELINE_CONFIGS.items()
}
BRONZE_READY_TOPICS = {
    dataset_key: dataset_config["bronze_ready_topic_name"]
    for dataset_key, dataset_config in DATASET_PIPELINE_CONFIGS.items()
}
ALL_TOPICS = list(TOPICS.values()) + list(BRONZE_READY_TOPICS.values())

LOG_OUTPUT_DIR = STREAMING_ROOT / "logs" / "client_1"
LOG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_dataset_config(dataset_key: str) -> dict[str, object]:
    """Return the central pipeline configuration for one dataset."""
    try:
        return DATASET_PIPELINE_CONFIGS[dataset_key]
    except KeyError as exc:
        raise KeyError(f"Unsupported dataset key: {dataset_key}") from exc
