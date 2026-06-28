from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus
import sys


CURRENT_DIR = Path(__file__).resolve().parent
CLIENT_ELT_DIR = CURRENT_DIR.parent

if str(CLIENT_ELT_DIR) not in sys.path:
    sys.path.insert(0, str(CLIENT_ELT_DIR))

from config.config import (  # noqa: E402
    CLIENT_ENV_PATH,
    CLIENT_NAME,
    DATA_WAREHOUSE_NAME,
    POSTGRES_CONFIG,
    validate_config,
)


GX_PROJECT_DIR = CURRENT_DIR
GX_CONTEXT_DIR = GX_PROJECT_DIR / "gx"

DATASOURCE_NAME = "client1_dw_postgres"
RAW_CHECKPOINT_NAME = "raw_data_quality_checkpoint"
ANALYTICS_CHECKPOINT_NAME = "analytics_data_quality_checkpoint"
ML_CHECKPOINT_NAME = "ml_feature_readiness_checkpoint"
DATA_DOCS_ACTION_NAME = "update_data_docs"


ASSET_CONFIGS = [
    {
        "layer": "raw",
        "asset_name": "raw_marketing_campaign",
        "schema_name": "raw_data",
        "table_name": "marketing_campaign",
        "batch_definition_name": "marketing_campaign_whole_table",
        "suite_name": "raw_marketing_campaign_suite",
        "validation_name": "validate_raw_marketing_campaign",
    },
    {
        "layer": "raw",
        "asset_name": "raw_ecommerce_customer_churn",
        "schema_name": "raw_data",
        "table_name": "e_commerce_customer_churn",
        "batch_definition_name": "ecommerce_customer_churn_whole_table",
        "suite_name": "raw_ecommerce_customer_churn_suite",
        "validation_name": "validate_raw_ecommerce_customer_churn",
    },
    {
        "layer": "raw",
        "asset_name": "raw_online_retail",
        "schema_name": "raw_data",
        "table_name": "online_retail",
        "batch_definition_name": "online_retail_whole_table",
        "suite_name": "raw_online_retail_suite",
        "validation_name": "validate_raw_online_retail",
    },
    {
        "layer": "raw",
        "asset_name": "raw_retailrocket_events",
        "schema_name": "raw_data",
        "table_name": "events",
        "batch_definition_name": "retailrocket_events_whole_table",
        "suite_name": "raw_retailrocket_events_suite",
        "validation_name": "validate_raw_retailrocket_events",
    },
    {
        "layer": "raw",
        "asset_name": "raw_retailrocket_item_properties",
        "schema_name": "raw_data",
        "table_name": "item_properties",
        "batch_definition_name": "retailrocket_item_properties_whole_table",
        "suite_name": "raw_retailrocket_item_properties_suite",
        "validation_name": "validate_raw_retailrocket_item_properties",
    },
    {
        "layer": "raw",
        "asset_name": "raw_retailrocket_category_tree",
        "schema_name": "raw_data",
        "table_name": "category_tree",
        "batch_definition_name": "retailrocket_category_tree_whole_table",
        "suite_name": "raw_retailrocket_category_tree_suite",
        "validation_name": "validate_raw_retailrocket_category_tree",
    },
    {
        "layer": "analytics",
        "asset_name": "analytics_customer_segments",
        "schema_name": "analytics",
        "table_name": "analytics_customer_segments",
        "batch_definition_name": "analytics_customer_segments_whole_table",
        "suite_name": "analytics_customer_segments_suite",
        "validation_name": "validate_analytics_customer_segments",
    },
    {
        "layer": "analytics",
        "asset_name": "analytics_product_performance",
        "schema_name": "analytics",
        "table_name": "analytics_product_performance",
        "batch_definition_name": "analytics_product_performance_whole_table",
        "suite_name": "analytics_product_performance_suite",
        "validation_name": "validate_analytics_product_performance",
    },
    {
        "layer": "analytics",
        "asset_name": "analytics_sales_analytics",
        "schema_name": "analytics",
        "table_name": "analytics_sales_analytics",
        "batch_definition_name": "analytics_sales_analytics_whole_table",
        "suite_name": "analytics_sales_analytics_suite",
        "validation_name": "validate_analytics_sales_analytics",
    },
    {
        "layer": "analytics",
        "asset_name": "analytics_business_intelligence",
        "schema_name": "analytics",
        "table_name": "analytics_business_intelligence",
        "batch_definition_name": "analytics_business_intelligence_whole_table",
        "suite_name": "analytics_business_intelligence_suite",
        "validation_name": "validate_analytics_business_intelligence",
    },
]


RAW_VALIDATION_NAMES = [
    config["validation_name"]
    for config in ASSET_CONFIGS
    if config["layer"] == "raw"
]

ANALYTICS_VALIDATION_NAMES = [
    config["validation_name"]
    for config in ASSET_CONFIGS
    if config["layer"] == "analytics"
]

ML_VALIDATION_NAMES = [
    "validate_analytics_customer_segments",
    "validate_analytics_sales_analytics",
]


def build_connection_string() -> str:
    if not validate_config():
        raise RuntimeError(
            "Missing PostgreSQL configuration. "
            f"Please update {CLIENT_ENV_PATH} before running Great Expectations."
        )

    user = quote_plus(POSTGRES_CONFIG["user"])
    password = quote_plus(POSTGRES_CONFIG["password"])
    host = POSTGRES_CONFIG["host"]
    port = POSTGRES_CONFIG["port"]
    database = DATA_WAREHOUSE_NAME

    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def get_asset_config_map() -> dict[str, dict]:
    return {config["asset_name"]: config for config in ASSET_CONFIGS}


def get_validation_config_map() -> dict[str, dict]:
    return {config["validation_name"]: config for config in ASSET_CONFIGS}


def describe_project() -> str:
    return (
        f"Great Expectations quality layer for {CLIENT_NAME}. "
        "Validates raw source contracts, analytics marts, and ML-readiness checks "
        f"against {DATA_WAREHOUSE_NAME}."
    )
