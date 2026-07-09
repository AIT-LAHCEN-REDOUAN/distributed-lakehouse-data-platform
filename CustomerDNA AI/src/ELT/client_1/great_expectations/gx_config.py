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
GX_UNCOMMITTED_DIR = GX_CONTEXT_DIR / "uncommitted"
GX_CONFIG_VARIABLES_PATH = GX_UNCOMMITTED_DIR / "config_variables.yml"
GX_CONNECTION_STRING_VARIABLE = "customerdna_gx_connection_string"
GX_CONNECTION_STRING_PLACEHOLDER = f"${{{GX_CONNECTION_STRING_VARIABLE}}}"

DATASOURCE_NAME = "client1_dw_postgres"
RAW_CHECKPOINT_NAME = "raw_data_quality_checkpoint"
ANALYTICS_CHECKPOINT_NAME = "analytics_data_quality_checkpoint"
SERVING_CHECKPOINT_NAME = "serving_data_quality_checkpoint"
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
    {
        "layer": "serving",
        "asset_name": "serving_customer_360",
        "schema_name": "serving",
        "table_name": "customer_360",
        "batch_definition_name": "customer_360_whole_table",
        "suite_name": "serving_customer_360_suite",
        "validation_name": "validate_serving_customer_360",
    },
    {
        "layer": "serving",
        "asset_name": "serving_segmentation_feature_base",
        "schema_name": "serving",
        "table_name": "segmentation_feature_base",
        "batch_definition_name": "segmentation_feature_base_whole_table",
        "suite_name": "serving_segmentation_feature_base_suite",
        "validation_name": "validate_serving_segmentation_feature_base",
    },
    {
        "layer": "serving",
        "asset_name": "serving_churn_feature_base",
        "schema_name": "serving",
        "table_name": "churn_feature_base",
        "batch_definition_name": "churn_feature_base_whole_table",
        "suite_name": "serving_churn_feature_base_suite",
        "validation_name": "validate_serving_churn_feature_base",
    },
    {
        "layer": "serving",
        "asset_name": "serving_ltv_feature_base",
        "schema_name": "serving",
        "table_name": "ltv_feature_base",
        "batch_definition_name": "ltv_feature_base_whole_table",
        "suite_name": "serving_ltv_feature_base_suite",
        "validation_name": "validate_serving_ltv_feature_base",
    },
    {
        "layer": "serving",
        "asset_name": "serving_persona_base",
        "schema_name": "serving",
        "table_name": "persona_base",
        "batch_definition_name": "persona_base_whole_table",
        "suite_name": "serving_persona_base_suite",
        "validation_name": "validate_serving_persona_base",
    },
    {
        "layer": "serving",
        "asset_name": "serving_marketing_recommendation_base",
        "schema_name": "serving",
        "table_name": "marketing_recommendation_base",
        "batch_definition_name": "marketing_recommendation_base_whole_table",
        "suite_name": "serving_marketing_recommendation_base_suite",
        "validation_name": "validate_serving_marketing_recommendation_base",
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

SERVING_VALIDATION_NAMES = [
    config["validation_name"]
    for config in ASSET_CONFIGS
    if config["layer"] == "serving"
]

ML_VALIDATION_NAMES = [
    "validate_serving_segmentation_feature_base",
    "validate_serving_churn_feature_base",
    "validate_serving_ltv_feature_base",
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


def ensure_local_config_variables() -> Path:
    """
    Write the sensitive GX connection string into the local uncommitted config.

    This keeps secrets out of the tracked `great_expectations.yml` while
    preserving the current local workflow.
    """
    GX_UNCOMMITTED_DIR.mkdir(parents=True, exist_ok=True)

    connection_string = build_connection_string()
    escaped_connection_string = connection_string.replace("\\", "\\\\").replace('"', '\\"')

    GX_CONFIG_VARIABLES_PATH.write_text(
        "# Auto-generated locally by CustomerDNA AI Great Expectations bootstrap.\n"
        "# This file is intentionally uncommitted and environment-specific.\n"
        f'{GX_CONNECTION_STRING_VARIABLE}: "{escaped_connection_string}"\n',
        encoding="utf-8",
    )
    return GX_CONFIG_VARIABLES_PATH


def get_gx_connection_string_reference() -> str:
    """
    Return the non-secret placeholder stored in tracked GX configuration.
    """
    return GX_CONNECTION_STRING_PLACEHOLDER


def get_asset_config_map() -> dict[str, dict]:
    return {config["asset_name"]: config for config in ASSET_CONFIGS}


def get_validation_config_map() -> dict[str, dict]:
    return {config["validation_name"]: config for config in ASSET_CONFIGS}


def describe_project() -> str:
    return (
        f"Great Expectations quality layer for {CLIENT_NAME}. "
        "Validates raw source contracts, analytics marts, serving data products, and ML-readiness checks "
        f"against {DATA_WAREHOUSE_NAME}."
    )
