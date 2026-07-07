"""Common Kafka configuration for Client 1 streaming proofs of concept."""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Return the repository root."""
    return Path(__file__).resolve().parents[6]


def customerdna_root() -> Path:
    """Return the CustomerDNA AI root directory."""
    return project_root() / "CustomerDNA AI"


STREAMING_ROOT = Path(__file__).resolve().parents[2]
CLIENT_ROOT = Path(__file__).resolve().parents[1]

KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092"]

TOPICS = {
    "marketing_campaign": "client1.marketing_campaign",
    "ecommerce_customer_churn": "client1.ecommerce_customer_churn",
}

PROCESSED_DATASET_PATHS = {
    "marketing_campaign": customerdna_root()
    / "src"
    / "Data_Ingestion"
    / "client_1"
    / "ingested_data"
    / "Customer_Personality_Analysis"
    / "processed_marketing_campaign.csv",
    "ecommerce_customer_churn": customerdna_root()
    / "src"
    / "Data_Ingestion"
    / "client_1"
    / "ingested_data"
    / "E-commerce_customer_churn"
    / "processed_E-commerce_customer_churn.csv",
}

LOG_OUTPUT_DIR = STREAMING_ROOT / "logs" / "client_1"
LOG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONSUMER_OUTPUT_DIR = STREAMING_ROOT / "consumer_output" / "client_1"
CONSUMER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
