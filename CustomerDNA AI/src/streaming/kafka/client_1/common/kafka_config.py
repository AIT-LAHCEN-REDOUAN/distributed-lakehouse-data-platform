"""Common Kafka and dataset configuration for the Client 1 ingestion backbone."""

from __future__ import annotations

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
    import os

    configured_value = os.getenv("CUSTOMERDNA_KAFKA_BOOTSTRAP_SERVERS", "").strip()

    if configured_value:
        return [server.strip() for server in configured_value.split(",") if server.strip()]

    return ["localhost:9092"]


KAFKA_BOOTSTRAP_SERVERS = get_kafka_bootstrap_servers()

DATASET_ORDER = [
    "bank_marketing",
    "online_shoppers_intention",
    "online_retail_2",
]

DATASET_PIPELINE_CONFIGS = {
    "bank_marketing": {
        "topic_name": "client1.bank_marketing",
        "bronze_ready_topic_name": "client1.bank_marketing.bronze_ready",
        "target_table": "bank_marketing",
        "key_field_priority": ["age", "job", "month", "campaign", "duration"],
        "produce_progress_interval": 5000,
        "bronze_flush_rows": 5000,
        "bronze_progress_interval": 5000,
        "bronze_consumer_timeout_ms": 30000,
        "load_event_consumer_timeout_ms": 30000,
        "load_copy_batch_size": 5000,
        "load_progress_interval": 5000,
        "source_paths": [
            SOURCE_DATASETS_ROOT / "bank_marketing" / "bank-additional-full.csv",
        ],
        "source_label": "bank-additional-full.csv",
        "source_type": "csv",
        "delimiter": ";",
        "encoding": "utf-8",
    },
    "online_shoppers_intention": {
        "topic_name": "client1.online_shoppers_intention",
        "bronze_ready_topic_name": "client1.online_shoppers_intention.bronze_ready",
        "target_table": "online_shoppers_intention",
        "key_field_priority": ["Month", "VisitorType", "TrafficType", "Region", "ProductRelated"],
        "produce_progress_interval": 5000,
        "bronze_flush_rows": 5000,
        "bronze_progress_interval": 5000,
        "bronze_consumer_timeout_ms": 30000,
        "load_event_consumer_timeout_ms": 30000,
        "load_copy_batch_size": 5000,
        "load_progress_interval": 5000,
        "source_paths": [
            SOURCE_DATASETS_ROOT / "online_shoppers_intention" / "online_shoppers_intention.csv",
        ],
        "source_label": "online_shoppers_intention.csv",
        "source_type": "csv",
        "delimiter": ",",
        "encoding": "utf-8",
    },
    "online_retail_2": {
        "topic_name": "client1.online_retail_2",
        "bronze_ready_topic_name": "client1.online_retail_2.bronze_ready",
        "target_table": "online_retail_2",
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
