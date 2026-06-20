"""
CustomerDNA AI - Create Raw Base Tables in Client 1 Data Warehouse

Location:
    src/ELT/client_1/setup_dw/create_base_tables.py

Purpose:
    Creates the raw_data tables inside client1_DW before loading data.

Flow:
    setup_dw.py
        -> create_base_tables.py
        -> load_data_to_dw.py
        -> future dbt transformations

Important:
    Tables are created with TEXT columns.
    dbt will handle type casting later in staging models.
"""

import sys
import os
import re
import pandas as pd
import psycopg2
from psycopg2 import sql

# Because this file is inside setup_dw/
# config folder is one level up: ../config
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "config"))

from config import (
    DATA_WAREHOUSE_NAME,
    CLIENT_DW_CONFIG,
    INGESTED_DATA_DIR,
    get_connection_params,
    validate_config,
)


# ============================================================================
# FILE TO TABLE MAPPING
# ============================================================================

FILE_TABLE_MAPPING = {
    # Customer Personality Analysis
    "processed_marketing_campaign.csv": "marketing_campaign",

    # E-commerce Customer Churn
    "processed_e-commerce_customer_churn.csv": "e_commerce_customer_churn",
    "processed_e_commerce_customer_churn.csv": "e_commerce_customer_churn",

    # RetailRocket
    "category_tree_processed.csv": "category_tree",
    "events_processed.csv": "events",
    "item_properties_processed.csv": "item_properties",

    # UCI Online Retail II
    "online_retail_processed.csv": "online_retail",
}


IGNORED_FOLDER_NAMES = {
    "power_bi_loading",
    "__pycache__",
}


class RawTableCreator:
    """Creates raw_data tables in the client data warehouse."""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.connection = None
        self.raw_schema = CLIENT_DW_CONFIG["raw_schema"]
        self.metadata_schema = CLIENT_DW_CONFIG["metadata_schema"]

    def log(self, message, level="INFO"):
        if not self.verbose:
            return

        if level == "ERROR":
            print(f"[ERROR] {message}")
        elif level == "SUCCESS":
            print(f"[SUCCESS] {message}")
        elif level == "WARNING":
            print(f"[WARNING] {message}")
        else:
            print(f"[INFO] {message}")

    def connect_to_dw(self):
        """Connect to client1_DW."""
        try:
            self.connection = psycopg2.connect(
                **get_connection_params(DATA_WAREHOUSE_NAME)
            )
            self.connection.autocommit = True
            self.log(f"Connected to Data Warehouse: {DATA_WAREHOUSE_NAME}", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Failed to connect to Data Warehouse: {str(e)}", "ERROR")
            return False

    def create_required_schemas(self):
        """Create required schemas if they do not exist."""
        try:
            cursor = self.connection.cursor()

            for schema_name in [self.raw_schema, self.metadata_schema]:
                cursor.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                        sql.Identifier(schema_name)
                    )
                )
                self.log(f"Schema created/verified: {schema_name}")

            cursor.close()
            return True

        except Exception as e:
            self.log(f"Failed to create required schemas: {str(e)}", "ERROR")
            return False

    def create_table_registry(self):
        """Create metadata table for tracking raw table definitions."""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
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
            """)

            cursor.close()
            self.log("metadata.raw_table_registry created/verified")
            return True

        except Exception as e:
            self.log(f"Failed to create table registry: {str(e)}", "ERROR")
            return False

    def should_ignore_path(self, file_path):
        """Ignore folders that should not be loaded into DW."""
        path_parts = [part.lower() for part in file_path.split(os.sep)]

        for ignored in IGNORED_FOLDER_NAMES:
            if ignored.lower() in path_parts:
                return True

        return False

    def get_mapped_csv_files(self, data_dir):
        """Find only mapped CSV files."""
        csv_files = []

        if not os.path.exists(data_dir):
            self.log(f"Data directory does not exist: {data_dir}", "ERROR")
            return csv_files

        for root, _, files in os.walk(data_dir):
            for file in files:
                if not file.lower().endswith(".csv"):
                    continue

                full_path = os.path.join(root, file)

                if self.should_ignore_path(full_path):
                    self.log(f"Ignoring file inside ignored folder: {full_path}", "WARNING")
                    continue

                normalized_name = file.lower()

                if normalized_name in FILE_TABLE_MAPPING:
                    csv_files.append(full_path)
                else:
                    self.log(f"CSV file found but not mapped, skipping: {file}", "WARNING")

        return sorted(csv_files)

    def get_table_name_for_file(self, csv_path):
        """Return mapped table name."""
        file_name = os.path.basename(csv_path).lower()
        return FILE_TABLE_MAPPING.get(file_name)

    def clean_identifier(self, name):
        """Clean PostgreSQL column names."""
        name = str(name).strip().lower()
        name = re.sub(r"[^a-z0-9_]+", "_", name)
        name = re.sub(r"_+", "_", name)
        name = name.strip("_")

        if not name:
            name = "unnamed"

        if name[0].isdigit():
            name = f"col_{name}"

        return name

    def make_unique_columns(self, columns):
        """Clean and deduplicate column names."""
        cleaned_columns = []
        seen = {}

        for col in columns:
            base = self.clean_identifier(col)

            if base not in seen:
                seen[base] = 0
                cleaned_columns.append(base)
            else:
                seen[base] += 1
                cleaned_columns.append(f"{base}_{seen[base]}")

        return cleaned_columns

    def read_csv_columns(self, csv_path):
        """Read CSV header and return cleaned column names."""
        try:
            df_header = pd.read_csv(csv_path, nrows=0)
            return self.make_unique_columns(df_header.columns)

        except UnicodeDecodeError:
            try:
                df_header = pd.read_csv(csv_path, nrows=0, encoding="latin1")
                return self.make_unique_columns(df_header.columns)

            except Exception as e:
                self.log(f"Failed to read header with latin1: {csv_path} - {str(e)}", "ERROR")
                return []

        except Exception as e:
            self.log(f"Failed to read CSV header: {csv_path} - {str(e)}", "ERROR")
            return []

    def create_raw_table(self, table_name, columns):
        """Create raw table with TEXT columns."""
        try:
            cursor = self.connection.cursor()

            cursor.execute(
                sql.SQL("DROP TABLE IF EXISTS {}.{} CASCADE").format(
                    sql.Identifier(self.raw_schema),
                    sql.Identifier(table_name),
                )
            )

            column_definitions = [
                sql.SQL("{} TEXT").format(sql.Identifier(column))
                for column in columns
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

        except Exception as e:
            self.log(f"Failed to create table {table_name}: {str(e)}", "ERROR")
            return False

    def save_table_registry(self, csv_path, table_name, columns):
        """Save table definition metadata."""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                INSERT INTO metadata.raw_table_registry
                    (file_name, source_path, table_schema, table_name, column_count)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (file_name, table_schema, table_name)
                DO UPDATE SET
                    source_path = EXCLUDED.source_path,
                    column_count = EXCLUDED.column_count,
                    created_at = CURRENT_TIMESTAMP
            """, (
                os.path.basename(csv_path),
                csv_path,
                self.raw_schema,
                table_name,
                len(columns),
            ))

            cursor.close()
            return True

        except Exception as e:
            self.log(f"Failed to save registry for {table_name}: {str(e)}", "ERROR")
            return False

    def print_creation_plan(self, csv_files):
        """Print file-to-table mapping plan."""
        print("\n" + "=" * 80)
        print("RAW TABLE CREATION PLAN")
        print("=" * 80)

        for csv_file in csv_files:
            file_name = os.path.basename(csv_file)
            table_name = self.get_table_name_for_file(csv_file)
            print(f"{file_name}  -->  {self.raw_schema}.{table_name}")

        print("=" * 80)

    def create_tables(self, data_dir):
        """Create all mapped raw tables."""
        print("=" * 80)
        print("CUSTOMERDNA AI - CREATE RAW TABLES IN CLIENT 1 DW")
        print("=" * 80)
        print(f"Database: {DATA_WAREHOUSE_NAME}")
        print(f"Target schema: {self.raw_schema}")
        print(f"Source directory: {data_dir}")
        print("=" * 80)

        if not validate_config():
            return False

        if not self.connect_to_dw():
            return False

        if not self.create_required_schemas():
            return False

        if not self.create_table_registry():
            return False

        csv_files = self.get_mapped_csv_files(data_dir)

        if not csv_files:
            self.log("No mapped CSV files found", "ERROR")
            return False

        self.log(f"Found {len(csv_files)} mapped CSV file(s)")
        self.print_creation_plan(csv_files)

        successful_tables = 0

        for csv_file in csv_files:
            file_name = os.path.basename(csv_file)
            table_name = self.get_table_name_for_file(csv_file)

            print("-" * 80)
            self.log(f"File: {file_name}")
            self.log(f"Target table: {self.raw_schema}.{table_name}")

            columns = self.read_csv_columns(csv_file)

            if not columns:
                self.log(f"No columns found in {file_name}", "ERROR")
                continue

            self.log(f"Detected columns: {len(columns)}")

            if self.create_raw_table(table_name, columns):
                self.save_table_registry(csv_file, table_name, columns)
                successful_tables += 1

        print("\n" + "=" * 80)
        print("RAW TABLE CREATION SUMMARY")
        print("=" * 80)

        self.log(f"Mapped CSV files: {len(csv_files)}")
        self.log(f"Tables created successfully: {successful_tables}")

        if successful_tables == len(csv_files):
            self.log("ALL RAW TABLES CREATED SUCCESSFULLY", "SUCCESS")
            return True

        self.log(f"{len(csv_files) - successful_tables} table(s) failed", "ERROR")
        return False


def main():
    print(f"Using ingested data directory: {INGESTED_DATA_DIR}")

    if not os.path.exists(INGESTED_DATA_DIR):
        print(f"[ERROR] Directory does not exist: {INGESTED_DATA_DIR}")
        print("Please run the Data_Ingestion phase first.")
        return 1

    creator = RawTableCreator(verbose=True)
    success = creator.create_tables(INGESTED_DATA_DIR)

    if success:
        print("\n[SUCCESS] Raw base tables created in client1_DW.raw_data.")
        print("Next step: run load_data_to_dw.py")
        return 0

    print("\n[ERROR] Raw table creation failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())