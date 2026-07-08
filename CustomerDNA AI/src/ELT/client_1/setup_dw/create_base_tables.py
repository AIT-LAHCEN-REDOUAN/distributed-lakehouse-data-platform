"""
CustomerDNA AI - Create Raw Base Tables in Client 1 Data Warehouse

Purpose:
    Creates the raw_data tables inside client1_DW before Kafka-backed raw loading.

Flow:
    setup_dw.py
        -> create_base_tables.py
        -> Kafka raw loading pipeline
        -> dbt transformations

Important:
    Tables are created with TEXT columns.
    Column definitions are inferred from the active Kafka source readers so the
    raw schema stays aligned with the ingestion backbone.
"""

from __future__ import annotations

import os
import re
import sys

import psycopg2
from psycopg2 import sql

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
if CONFIG_DIR not in sys.path:
    sys.path.append(CONFIG_DIR)

STREAMING_COMMON_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "streaming",
        "kafka",
        "client_1",
        "common",
    )
)
if STREAMING_COMMON_DIR not in sys.path:
    sys.path.append(STREAMING_COMMON_DIR)

from config import (  # noqa: E402
    CLIENT_DW_CONFIG,
    DATA_WAREHOUSE_NAME,
    SOURCE_DATASETS_DIR,
    get_connection_params,
    validate_config,
)
from kafka_config import SOURCE_DATASET_CONFIGS  # noqa: E402
from source_row_iterators import get_source_paths, iter_source_rows  # noqa: E402


DATASET_TABLE_MAPPING = {
    "marketing_campaign": "marketing_campaign",
    "ecommerce_customer_churn": "e_commerce_customer_churn",
    "retailrocket_category_tree": "category_tree",
    "retailrocket_events": "events",
    "retailrocket_item_properties": "item_properties",
    "online_retail": "online_retail",
}

DATASET_ORDER = [
    "retailrocket_category_tree",
    "marketing_campaign",
    "ecommerce_customer_churn",
    "online_retail",
    "retailrocket_events",
    "retailrocket_item_properties",
]


class RawTableCreator:
    """Create raw tables and register them in metadata."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.connection = None
        self.raw_schema = CLIENT_DW_CONFIG["raw_schema"]
        self.metadata_schema = CLIENT_DW_CONFIG["metadata_schema"]

    def log(self, message: str, level: str = "INFO") -> None:
        if not self.verbose:
            return

        print(f"[{level}] {message}")

    def connect_to_dw(self) -> bool:
        try:
            self.connection = psycopg2.connect(**get_connection_params(DATA_WAREHOUSE_NAME))
            self.connection.autocommit = True
            self.log(f"Connected to Data Warehouse: {DATA_WAREHOUSE_NAME}", "SUCCESS")
            return True
        except Exception as exc:
            self.log(f"Failed to connect to Data Warehouse: {exc}", "ERROR")
            return False

    def close_connection(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None
            self.log("Closed database connection")

    def create_required_schemas(self) -> bool:
        try:
            cursor = self.connection.cursor()
            for schema_name in [self.raw_schema, self.metadata_schema]:
                cursor.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_name))
                )
                self.log(f"Schema created/verified: {schema_name}")
            cursor.close()
            return True
        except Exception as exc:
            self.log(f"Failed to create required schemas: {exc}", "ERROR")
            return False

    def create_table_registry(self) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata.raw_table_registry (
                    id SERIAL PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    table_schema TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    column_count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(file_name, table_schema, table_name)
                )
                """
            )
            cursor.close()
            self.log("metadata.raw_table_registry created/verified")
            return True
        except Exception as exc:
            self.log(f"Failed to create table registry: {exc}", "ERROR")
            return False

    def clean_identifier(self, name: str) -> str:
        name = str(name).strip().lower()
        name = re.sub(r"[^a-z0-9_]+", "_", name)
        name = re.sub(r"_+", "_", name)
        name = name.strip("_")

        if not name:
            name = "unnamed"

        if name[0].isdigit():
            name = f"col_{name}"

        return name

    def make_unique_columns(self, columns: list[str]) -> list[str]:
        cleaned_columns: list[str] = []
        seen: dict[str, int] = {}

        for column in columns:
            base_name = self.clean_identifier(column)
            duplicate_count = seen.get(base_name, 0)

            if duplicate_count == 0:
                cleaned_columns.append(base_name)
            else:
                cleaned_columns.append(f"{base_name}_{duplicate_count}")

            seen[base_name] = duplicate_count + 1

        return cleaned_columns

    def get_dataset_columns(self, dataset_key: str) -> list[str]:
        try:
            first_row = next(iter_source_rows(dataset_key))
        except StopIteration as exc:
            raise ValueError(f"Dataset '{dataset_key}' does not contain any rows.") from exc

        return self.make_unique_columns(list(first_row.keys()))

    def create_raw_table(self, table_name: str, columns: list[str]) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                sql.SQL("DROP TABLE IF EXISTS {}.{} CASCADE").format(
                    sql.Identifier(self.raw_schema),
                    sql.Identifier(table_name),
                )
            )

            column_definitions = [
                sql.SQL("{} TEXT").format(sql.Identifier(column_name))
                for column_name in columns
            ]

            cursor.execute(
                sql.SQL("CREATE TABLE {}.{} ({})").format(
                    sql.Identifier(self.raw_schema),
                    sql.Identifier(table_name),
                    sql.SQL(", ").join(column_definitions),
                )
            )
            cursor.close()
            self.log(f"Created table: {self.raw_schema}.{table_name}", "SUCCESS")
            return True
        except Exception as exc:
            self.log(f"Failed to create table {table_name}: {exc}", "ERROR")
            return False

    def save_table_registry(self, dataset_key: str, table_name: str, columns: list[str]) -> bool:
        try:
            cursor = self.connection.cursor()
            source_paths = get_source_paths(dataset_key)
            source_path_text = " | ".join(str(path) for path in source_paths)
            source_name_text = " + ".join(path.name for path in source_paths)

            cursor.execute(
                """
                INSERT INTO metadata.raw_table_registry
                    (file_name, source_path, table_schema, table_name, column_count)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (file_name, table_schema, table_name)
                DO UPDATE SET
                    source_path = EXCLUDED.source_path,
                    column_count = EXCLUDED.column_count,
                    created_at = CURRENT_TIMESTAMP
                """,
                (
                    source_name_text,
                    source_path_text,
                    self.raw_schema,
                    table_name,
                    len(columns),
                ),
            )
            cursor.close()
            return True
        except Exception as exc:
            self.log(f"Failed to save registry for {table_name}: {exc}", "ERROR")
            return False

    def print_creation_plan(self) -> None:
        print("\n" + "=" * 80)
        print("RAW TABLE CREATION PLAN")
        print("=" * 80)

        for dataset_key in DATASET_ORDER:
            source_label = SOURCE_DATASET_CONFIGS[dataset_key]["source_label"]
            table_name = DATASET_TABLE_MAPPING[dataset_key]
            print(f"{source_label}  -->  {self.raw_schema}.{table_name}")

        print("=" * 80)

    def create_tables(self) -> bool:
        print("=" * 80)
        print("CUSTOMERDNA AI - CREATE RAW TABLES IN CLIENT 1 DW")
        print("=" * 80)
        print(f"Database: {DATA_WAREHOUSE_NAME}")
        print(f"Target schema: {self.raw_schema}")
        print(f"Source datasets root: {SOURCE_DATASETS_DIR}")
        print("=" * 80)

        if not validate_config():
            return False

        if not self.connect_to_dw():
            return False

        try:
            if not self.create_required_schemas():
                return False

            if not self.create_table_registry():
                return False

            self.log(f"Found {len(DATASET_ORDER)} dataset definition(s)")
            self.print_creation_plan()

            successful_tables = 0

            for dataset_key in DATASET_ORDER:
                table_name = DATASET_TABLE_MAPPING[dataset_key]
                source_label = SOURCE_DATASET_CONFIGS[dataset_key]["source_label"]

                print("-" * 80)
                self.log(f"Dataset: {dataset_key}")
                self.log(f"Source: {source_label}")
                self.log(f"Target table: {self.raw_schema}.{table_name}")

                try:
                    columns = self.get_dataset_columns(dataset_key)
                except Exception as exc:
                    self.log(f"Failed to infer columns for {dataset_key}: {exc}", "ERROR")
                    continue

                self.log(f"Detected columns: {len(columns)}")

                if self.create_raw_table(table_name, columns):
                    self.save_table_registry(dataset_key, table_name, columns)
                    successful_tables += 1

            print("\n" + "=" * 80)
            print("RAW TABLE CREATION SUMMARY")
            print("=" * 80)
            self.log(f"Datasets defined: {len(DATASET_ORDER)}")
            self.log(f"Tables created successfully: {successful_tables}")

            if successful_tables == len(DATASET_ORDER):
                self.log("ALL RAW TABLES CREATED SUCCESSFULLY", "SUCCESS")
                return True

            self.log(f"{len(DATASET_ORDER) - successful_tables} table(s) failed", "ERROR")
            return False
        finally:
            self.close_connection()


def main() -> int:
    creator = RawTableCreator(verbose=True)
    success = creator.create_tables()

    if success:
        print("\n[SUCCESS] Raw base tables created in client1_DW.raw_data.")
        print("Next step: run the Kafka raw loading pipeline.")
        return 0

    print("\n[ERROR] Raw table creation failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
