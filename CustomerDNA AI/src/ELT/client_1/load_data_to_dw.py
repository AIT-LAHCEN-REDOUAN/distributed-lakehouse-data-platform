"""
CustomerDNA AI - Load Data into Existing Raw Tables in Client 1 DW

Location:
    src/ELT/client_1/load_data_to_dw.py

Purpose:
    Loads CSV data into raw_data tables already created by:

        setup_dw/create_base_tables.py

Flow:
    setup_dw.py
        -> create_base_tables.py
        -> load_data_to_dw.py
        -> verify_dw.py

Important:
    This script does NOT create raw tables.
    It only truncates and loads data into existing raw_data tables.
"""

import sys
import os
import csv
import pandas as pd
import psycopg2
from psycopg2 import sql
from tqdm import tqdm

# This file is in:
# src/ELT/client_1/load_data_to_dw.py
# config folder is:
# src/ELT/client_1/config
sys.path.append(os.path.join(os.path.dirname(__file__), "config"))

from config import (
    DATA_WAREHOUSE_NAME,
    CLIENT_DW_CONFIG,
    INGESTED_DATA_DIR,
    get_connection_params,
    validate_config,
)


# ============================================================================
# FILE TO TABLE MAPPING
# Must match setup_dw/create_base_tables.py
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


class DWDataLoader:
    """Loads CSV data into existing raw_data tables."""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.connection = None
        self.raw_schema = CLIENT_DW_CONFIG["raw_schema"]
        self.metadata_schema = CLIENT_DW_CONFIG["metadata_schema"]

    def log(self, message, level="INFO"):
        """Print formatted logs."""
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

    # ============================================================================
    # CONNECTION
    # ============================================================================

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

    def close_connection(self):
        """Close DB connection."""
        if self.connection:
            self.connection.close()
            self.log("Closed database connection")

    # ============================================================================
    # METADATA
    # ============================================================================

    def create_metadata_table(self):
        """Create metadata.loaded_files if missing."""
        try:
            cursor = self.connection.cursor()

            cursor.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(self.metadata_schema)
                )
            )

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata.loaded_files (
                    id SERIAL PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    table_schema TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_count BIGINT NOT NULL,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(file_name, table_schema, table_name)
                )
            """)

            cursor.close()
            self.log("metadata.loaded_files created/verified")
            return True

        except Exception as e:
            self.log(f"Failed to create metadata.loaded_files: {str(e)}", "ERROR")
            return False

    def register_loaded_file(self, csv_path, table_name, record_count):
        """Save load result in metadata.loaded_files."""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                INSERT INTO metadata.loaded_files
                    (file_name, source_path, table_schema, table_name, record_count)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (file_name, table_schema, table_name)
                DO UPDATE SET
                    source_path = EXCLUDED.source_path,
                    record_count = EXCLUDED.record_count,
                    loaded_at = CURRENT_TIMESTAMP
            """, (
                os.path.basename(csv_path),
                csv_path,
                self.raw_schema,
                table_name,
                record_count,
            ))

            cursor.close()
            return True

        except Exception as e:
            self.log(f"Failed to register loaded file metadata: {str(e)}", "ERROR")
            return False

    # ============================================================================
    # FILE DISCOVERY
    # ============================================================================

    def should_ignore_path(self, file_path):
        """Ignore folders that should not be loaded."""
        path_parts = [part.lower() for part in file_path.split(os.sep)]

        for ignored in IGNORED_FOLDER_NAMES:
            if ignored.lower() in path_parts:
                return True

        return False

    def get_mapped_csv_files(self, data_dir):
        """Find only mapped CSV files inside ingested_data."""
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
        """Return mapped table name for a CSV file."""
        file_name = os.path.basename(csv_path).lower()
        return FILE_TABLE_MAPPING.get(file_name)

    # ============================================================================
    # TABLE VALIDATION
    # ============================================================================

    def table_exists(self, table_name):
        """Check if raw_data table exists."""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    AND table_name = %s
                    AND table_type = 'BASE TABLE'
                )
            """, (self.raw_schema, table_name))

            exists = cursor.fetchone()[0]
            cursor.close()
            return exists

        except Exception as e:
            self.log(f"Failed to check table existence for {table_name}: {str(e)}", "ERROR")
            return False

    def get_table_columns(self, table_name):
        """Get table columns in ordinal order."""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                AND table_name = %s
                ORDER BY ordinal_position
            """, (self.raw_schema, table_name))

            columns = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return columns

        except Exception as e:
            self.log(f"Failed to get columns for {table_name}: {str(e)}", "ERROR")
            return []

    def truncate_table(self, table_name):
        """Truncate table before fresh load."""
        try:
            cursor = self.connection.cursor()

            cursor.execute(
                sql.SQL("TRUNCATE TABLE {}.{}").format(
                    sql.Identifier(self.raw_schema),
                    sql.Identifier(table_name),
                )
            )

            cursor.close()
            self.log(f"Truncated table: {self.raw_schema}.{table_name}")
            return True

        except Exception as e:
            self.log(f"Failed to truncate table {table_name}: {str(e)}", "ERROR")
            return False

    # ============================================================================
    # CSV HELPERS
    # ============================================================================

    def count_csv_rows(self, csv_path):
        """Count CSV rows excluding header."""
        encodings = ["utf-8", "utf-8-sig", "latin1"]

        for encoding in encodings:
            try:
                with open(csv_path, "r", encoding=encoding, newline="") as file:
                    reader = csv.reader(file)
                    row_count = sum(1 for _ in reader)

                return max(row_count - 1, 0)

            except UnicodeDecodeError:
                continue
            except Exception:
                return 0

        return 0

    def get_csv_iterator(self, csv_path, chunk_size):
        """Return pandas CSV iterator with encoding fallback."""
        encodings = ["utf-8", "utf-8-sig", "latin1"]

        last_error = None

        for encoding in encodings:
            try:
                return pd.read_csv(
                    csv_path,
                    chunksize=chunk_size,
                    dtype=str,
                    keep_default_na=False,
                    encoding=encoding,
                    low_memory=False,
                )
            except UnicodeDecodeError as e:
                last_error = e
                continue

        raise last_error

    # ============================================================================
    # DATA LOADING
    # ============================================================================

    def load_csv_with_pandas_chunks(self, csv_path, table_name, table_columns):
        """
        Load CSV data into existing table.

        Important:
            create_base_tables.py already created columns using cleaned names.
            Here we reuse the existing table columns and assign CSV chunks to them.
        """
        try:
            cursor = self.connection.cursor()

            insert_sql = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
                sql.Identifier(self.raw_schema),
                sql.Identifier(table_name),
                sql.SQL(", ").join([sql.Identifier(col) for col in table_columns]),
                sql.SQL(", ").join([sql.Placeholder()] * len(table_columns)),
            )

            total_inserted = 0
            chunk_size = 50000

            csv_iterator = self.get_csv_iterator(csv_path, chunk_size)

            for chunk in csv_iterator:
                if len(chunk.columns) != len(table_columns):
                    raise ValueError(
                        f"Column count mismatch for {os.path.basename(csv_path)}. "
                        f"CSV columns={len(chunk.columns)}, table columns={len(table_columns)}"
                    )

                # Assign existing DB columns to the chunk
                chunk.columns = table_columns

                # Convert empty strings to NULL
                records = [
                    tuple(None if value == "" else value for value in row)
                    for row in chunk.to_numpy()
                ]

                if records:
                    cursor.executemany(insert_sql, records)

                total_inserted += len(records)

                if total_inserted % 500000 == 0 and total_inserted > 0:
                    self.log(f"Inserted {total_inserted:,} rows into {table_name}")

            cursor.close()

            self.register_loaded_file(csv_path, table_name, total_inserted)

            self.log(
                f"Loaded {total_inserted:,} rows into {self.raw_schema}.{table_name}",
                "SUCCESS",
            )

            return True, total_inserted

        except Exception as e:
            self.log(f"Failed to load CSV {csv_path}: {str(e)}", "ERROR")
            return False, 0

    def load_one_csv(self, csv_path):
        """Load one mapped CSV file into an existing raw_data table."""
        file_name = os.path.basename(csv_path)
        table_name = self.get_table_name_for_file(csv_path)

        print("-" * 80)
        self.log(f"File: {file_name}")
        self.log(f"Target table: {self.raw_schema}.{table_name}")

        if not table_name:
            self.log(f"No mapping found for file: {file_name}", "ERROR")
            return False, 0

        if not self.table_exists(table_name):
            self.log(
                f"Target table does not exist: {self.raw_schema}.{table_name}. "
                f"Run setup_dw/create_base_tables.py first.",
                "ERROR",
            )
            return False, 0

        table_columns = self.get_table_columns(table_name)

        if not table_columns:
            self.log(f"No columns found in target table: {self.raw_schema}.{table_name}", "ERROR")
            return False, 0

        expected_rows = self.count_csv_rows(csv_path)

        self.log(f"Target columns: {len(table_columns)}")
        self.log(f"Expected CSV rows: {expected_rows:,}")

        if not self.truncate_table(table_name):
            return False, 0

        success, loaded_rows = self.load_csv_with_pandas_chunks(
            csv_path,
            table_name,
            table_columns,
        )

        if success and expected_rows and expected_rows != loaded_rows:
            self.log(
                f"Row count mismatch for {file_name}: CSV={expected_rows:,}, DB={loaded_rows:,}",
                "WARNING",
            )

        return success, loaded_rows

    # ============================================================================
    # MAIN RUNNER
    # ============================================================================

    def print_loading_plan(self, csv_files):
        """Print file-to-table mapping plan."""
        print("\n" + "=" * 80)
        print("DATA LOADING PLAN")
        print("=" * 80)

        for csv_file in csv_files:
            file_name = os.path.basename(csv_file)
            table_name = self.get_table_name_for_file(csv_file)
            print(f"{file_name}  -->  {self.raw_schema}.{table_name}")

        print("=" * 80)

    def run_loading(self, data_dir):
        """Run full data loading process."""
        print("=" * 80)
        print("CUSTOMERDNA AI - LOAD DATA INTO CLIENT 1 DW RAW TABLES")
        print("=" * 80)
        print(f"Database: {DATA_WAREHOUSE_NAME}")
        print(f"Target schema: {self.raw_schema}")
        print(f"Source directory: {data_dir}")
        print("=" * 80)

        if not validate_config():
            return False

        if not self.connect_to_dw():
            return False

        try:
            if not self.create_metadata_table():
                return False

            csv_files = self.get_mapped_csv_files(data_dir)

            if not csv_files:
                self.log("No mapped CSV files found", "ERROR")
                return False

            self.log(f"Found {len(csv_files)} mapped CSV file(s)")
            self.print_loading_plan(csv_files)

            successful_files = 0
            total_records = 0

            for csv_file in tqdm(csv_files, desc="Loading CSV files", unit="file"):
                success, record_count = self.load_one_csv(csv_file)

                if success:
                    successful_files += 1
                    total_records += record_count

            print("\n" + "=" * 80)
            print("DATA LOADING SUMMARY")
            print("=" * 80)

            self.log(f"Mapped files found: {len(csv_files)}")
            self.log(f"Files loaded successfully: {successful_files}")
            self.log(f"Total rows loaded: {total_records:,}")

            if successful_files == len(csv_files):
                self.log("ALL DATA LOADED SUCCESSFULLY", "SUCCESS")
                return True

            self.log(f"{len(csv_files) - successful_files} file(s) failed", "ERROR")
            return False

        finally:
            self.close_connection()


def main():
    print(f"Using ingested data directory: {INGESTED_DATA_DIR}")

    if not os.path.exists(INGESTED_DATA_DIR):
        print(f"[ERROR] Directory does not exist: {INGESTED_DATA_DIR}")
        print("Please run the Data_Ingestion phase first.")
        return 1

    loader = DWDataLoader(verbose=True)
    success = loader.run_loading(INGESTED_DATA_DIR)

    if success:
        print("\n[SUCCESS] Data loaded into existing client1_DW.raw_data tables.")
        print("Next step: run verify_dw.py")
        return 0

    print("\n[ERROR] Data loading failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())