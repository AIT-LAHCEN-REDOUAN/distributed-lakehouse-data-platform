"""
CustomerDNA AI - Load Data into Existing Raw Tables in Client 1 DW

Location:
    src/ELT/client_1/load_data_to_dw.py

Purpose:
    Loads processed CSV data into existing raw_data tables.

Current loading behavior:
    - Snapshot-style datasets are fully refreshed when the source file changes.
    - Large append-style datasets are loaded incrementally when the source file grows.
    - Unchanged files are skipped entirely.

Important:
    This script does NOT create raw tables.
    It only loads data into existing raw_data tables created by setup_dw/create_base_tables.py.
"""

import csv
import os
import sys
from datetime import datetime, timezone

import pandas as pd
import psycopg2
from psycopg2 import sql
from tqdm import tqdm

sys.path.append(os.path.join(os.path.dirname(__file__), "config"))

from config import (  # noqa: E402
    CLIENT_DW_CONFIG,
    DATA_WAREHOUSE_NAME,
    INGESTED_DATA_DIR,
    get_connection_params,
    validate_config,
)


FILE_TABLE_MAPPING = {
    "processed_marketing_campaign.csv": "marketing_campaign",
    "processed_e-commerce_customer_churn.csv": "e_commerce_customer_churn",
    "processed_e_commerce_customer_churn.csv": "e_commerce_customer_churn",
    "category_tree_processed.csv": "category_tree",
    "events_processed.csv": "events",
    "item_properties_processed.csv": "item_properties",
    "online_retail_processed.csv": "online_retail",
}

IGNORED_FOLDER_NAMES = {
    "power_bi_loading",
    "__pycache__",
}

TABLE_LOAD_STRATEGIES = {
    "marketing_campaign": "snapshot",
    "e_commerce_customer_churn": "snapshot",
    "category_tree": "snapshot",
    "events": "append_only",
    "item_properties": "append_only",
    "online_retail": "append_only",
}


class DWDataLoader:
    """Loads CSV data into existing raw_data tables."""

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
        try:
            self.connection = psycopg2.connect(**get_connection_params(DATA_WAREHOUSE_NAME))
            self.connection.autocommit = True
            self.log(f"Connected to Data Warehouse: {DATA_WAREHOUSE_NAME}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to connect to Data Warehouse: {str(e)}", "ERROR")
            return False

    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.log("Closed database connection")

    def create_metadata_tables(self):
        try:
            cursor = self.connection.cursor()

            cursor.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(self.metadata_schema)
                )
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata.loaded_files (
                    id SERIAL PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    table_schema TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_count BIGINT NOT NULL DEFAULT 0,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(file_name, table_schema, table_name)
                )
                """
            )

            alter_statements = [
                "ALTER TABLE metadata.loaded_files ADD COLUMN IF NOT EXISTS file_signature TEXT",
                "ALTER TABLE metadata.loaded_files ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT",
                "ALTER TABLE metadata.loaded_files ADD COLUMN IF NOT EXISTS file_modified_at TIMESTAMP",
                "ALTER TABLE metadata.loaded_files ADD COLUMN IF NOT EXISTS source_row_count BIGINT DEFAULT 0",
                "ALTER TABLE metadata.loaded_files ADD COLUMN IF NOT EXISTS rows_inserted BIGINT DEFAULT 0",
                "ALTER TABLE metadata.loaded_files ADD COLUMN IF NOT EXISTS load_strategy TEXT",
                "ALTER TABLE metadata.loaded_files ADD COLUMN IF NOT EXISTS load_mode TEXT",
                "ALTER TABLE metadata.loaded_files ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'completed'",
                "ALTER TABLE metadata.loaded_files ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ]

            for statement in alter_statements:
                cursor.execute(statement)

            cursor.close()
            self.log("metadata.loaded_files created/verified")
            return True
        except Exception as e:
            self.log(f"Failed to create metadata.loaded_files: {str(e)}", "ERROR")
            return False

    def should_ignore_path(self, file_path):
        path_parts = [part.lower() for part in file_path.split(os.sep)]
        return any(ignored.lower() in path_parts for ignored in IGNORED_FOLDER_NAMES)

    def get_mapped_csv_files(self, data_dir):
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
        file_name = os.path.basename(csv_path).lower()
        return FILE_TABLE_MAPPING.get(file_name)

    def get_load_strategy(self, table_name):
        return TABLE_LOAD_STRATEGIES.get(table_name, "snapshot")

    def table_exists(self, table_name):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = %s
                      AND table_name = %s
                      AND table_type = 'BASE TABLE'
                )
                """,
                (self.raw_schema, table_name),
            )
            exists = cursor.fetchone()[0]
            cursor.close()
            return exists
        except Exception as e:
            self.log(f"Failed to check table existence for {table_name}: {str(e)}", "ERROR")
            return False

    def get_table_columns(self, table_name):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = %s
                ORDER BY ordinal_position
                """,
                (self.raw_schema, table_name),
            )
            columns = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return columns
        except Exception as e:
            self.log(f"Failed to get columns for {table_name}: {str(e)}", "ERROR")
            return []

    def truncate_table(self, table_name):
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

    def count_csv_rows(self, csv_path):
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

    def get_csv_iterator(self, csv_path, chunk_size, skip_data_rows=0):
        encodings = ["utf-8", "utf-8-sig", "latin1"]
        last_error = None

        for encoding in encodings:
            try:
                read_kwargs = {
                    "chunksize": chunk_size,
                    "dtype": str,
                    "keep_default_na": False,
                    "encoding": encoding,
                    "low_memory": False,
                }
                if skip_data_rows > 0:
                    read_kwargs["skiprows"] = range(1, skip_data_rows + 1)

                return pd.read_csv(csv_path, **read_kwargs)
            except UnicodeDecodeError as e:
                last_error = e
                continue

        raise last_error

    def get_file_state(self, csv_path):
        stat_result = os.stat(csv_path)
        modified_at = datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc).replace(tzinfo=None)
        return {
            "file_name": os.path.basename(csv_path),
            "source_path": csv_path,
            "file_signature": f"{stat_result.st_size}:{stat_result.st_mtime_ns}",
            "file_size_bytes": stat_result.st_size,
            "file_modified_at": modified_at,
        }

    def get_loaded_file_metadata(self, csv_path, table_name):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT file_signature, source_row_count, rows_inserted, load_strategy, load_mode, status
                FROM metadata.loaded_files
                WHERE file_name = %s
                  AND table_schema = %s
                  AND table_name = %s
                """,
                (os.path.basename(csv_path), self.raw_schema, table_name),
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                "file_signature": row[0],
                "source_row_count": row[1] or 0,
                "rows_inserted": row[2] or 0,
                "load_strategy": row[3],
                "load_mode": row[4],
                "status": row[5],
            }
        except Exception as e:
            self.log(f"Failed to read metadata for {table_name}: {str(e)}", "ERROR")
            return None

    def register_loaded_file(self, file_state, table_name, source_row_count, rows_inserted, load_strategy, load_mode, status):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO metadata.loaded_files (
                    file_name,
                    source_path,
                    table_schema,
                    table_name,
                    record_count,
                    file_signature,
                    file_size_bytes,
                    file_modified_at,
                    source_row_count,
                    rows_inserted,
                    load_strategy,
                    load_mode,
                    status,
                    loaded_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (file_name, table_schema, table_name)
                DO UPDATE SET
                    source_path = EXCLUDED.source_path,
                    record_count = EXCLUDED.record_count,
                    file_signature = EXCLUDED.file_signature,
                    file_size_bytes = EXCLUDED.file_size_bytes,
                    file_modified_at = EXCLUDED.file_modified_at,
                    source_row_count = EXCLUDED.source_row_count,
                    rows_inserted = EXCLUDED.rows_inserted,
                    load_strategy = EXCLUDED.load_strategy,
                    load_mode = EXCLUDED.load_mode,
                    status = EXCLUDED.status,
                    loaded_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    file_state["file_name"],
                    file_state["source_path"],
                    self.raw_schema,
                    table_name,
                    source_row_count,
                    file_state["file_signature"],
                    file_state["file_size_bytes"],
                    file_state["file_modified_at"],
                    source_row_count,
                    rows_inserted,
                    load_strategy,
                    load_mode,
                    status,
                ),
            )
            cursor.close()
            return True
        except Exception as e:
            self.log(f"Failed to register loaded file metadata: {str(e)}", "ERROR")
            return False

    def load_csv_rows(self, csv_path, table_name, table_columns, skip_data_rows=0):
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
            csv_iterator = self.get_csv_iterator(csv_path, chunk_size, skip_data_rows=skip_data_rows)

            for chunk in csv_iterator:
                if len(chunk.columns) != len(table_columns):
                    raise ValueError(
                        f"Column count mismatch for {os.path.basename(csv_path)}. "
                        f"CSV columns={len(chunk.columns)}, table columns={len(table_columns)}"
                    )

                chunk.columns = table_columns
                records = [
                    tuple(None if value == "" else value for value in row)
                    for row in chunk.itertuples(index=False, name=None)
                ]

                if records:
                    cursor.executemany(insert_sql, records)
                    total_inserted += len(records)

                if total_inserted % 500000 == 0 and total_inserted > 0:
                    self.log(f"Inserted {total_inserted:,} rows into {table_name}")

            cursor.close()
            return True, total_inserted
        except Exception as e:
            self.log(f"Failed to load CSV {csv_path}: {str(e)}", "ERROR")
            return False, 0

    def determine_load_mode(self, load_strategy, file_state, previous_metadata, current_source_rows):
        if not previous_metadata or previous_metadata.get("status") != "completed":
            return "full_refresh", 0, None

        previous_signature = previous_metadata.get("file_signature")
        previous_source_rows = previous_metadata.get("source_row_count", 0)

        if previous_signature == file_state["file_signature"]:
            return "skip", 0, None

        if load_strategy == "append_only":
            if current_source_rows > previous_source_rows:
                return "incremental_append", previous_source_rows, None

            if current_source_rows == previous_source_rows:
                return "full_refresh", 0, (
                    "File content changed without row-count growth for append-only dataset; "
                    "falling back to full refresh."
                )

            return "full_refresh", 0, (
                "Source row count decreased for append-only dataset; falling back to full refresh."
            )

        return "full_refresh", 0, None

    def load_one_csv(self, csv_path):
        file_name = os.path.basename(csv_path)
        table_name = self.get_table_name_for_file(csv_path)

        print("-" * 80)
        self.log(f"File: {file_name}")
        self.log(f"Target table: {self.raw_schema}.{table_name}")

        if not table_name:
            self.log(f"No mapping found for file: {file_name}", "ERROR")
            return False, 0, "failed"

        if not self.table_exists(table_name):
            self.log(
                f"Target table does not exist: {self.raw_schema}.{table_name}. "
                f"Run setup_dw/create_base_tables.py first.",
                "ERROR",
            )
            return False, 0, "failed"

        table_columns = self.get_table_columns(table_name)
        if not table_columns:
            self.log(f"No columns found in target table: {self.raw_schema}.{table_name}", "ERROR")
            return False, 0, "failed"

        current_source_rows = self.count_csv_rows(csv_path)
        file_state = self.get_file_state(csv_path)
        previous_metadata = self.get_loaded_file_metadata(csv_path, table_name)
        load_strategy = self.get_load_strategy(table_name)
        load_mode, skip_data_rows, warning_message = self.determine_load_mode(
            load_strategy,
            file_state,
            previous_metadata,
            current_source_rows,
        )

        self.log(f"Load strategy: {load_strategy}")
        self.log(f"Target columns: {len(table_columns)}")
        self.log(f"Current CSV rows: {current_source_rows:,}")

        if warning_message:
            self.log(warning_message, "WARNING")

        if load_mode == "skip":
            self.log("File unchanged since last successful load; skipping", "SUCCESS")
            self.register_loaded_file(
                file_state,
                table_name,
                current_source_rows,
                0,
                load_strategy,
                load_mode,
                "completed",
            )
            return True, 0, "skipped"

        if load_mode == "full_refresh":
            if not self.truncate_table(table_name):
                self.register_loaded_file(
                    file_state,
                    table_name,
                    current_source_rows,
                    0,
                    load_strategy,
                    load_mode,
                    "failed",
                )
                return False, 0, "failed"

        success, loaded_rows = self.load_csv_rows(
            csv_path,
            table_name,
            table_columns,
            skip_data_rows=skip_data_rows,
        )

        self.register_loaded_file(
            file_state,
            table_name,
            current_source_rows,
            loaded_rows,
            load_strategy,
            load_mode,
            "completed" if success else "failed",
        )

        if success:
            if load_mode == "incremental_append":
                self.log(
                    f"Incrementally loaded {loaded_rows:,} new rows into {self.raw_schema}.{table_name}",
                    "SUCCESS",
                )
            else:
                self.log(
                    f"Loaded {loaded_rows:,} rows into {self.raw_schema}.{table_name}",
                    "SUCCESS",
                )
            return True, loaded_rows, load_mode

        return False, 0, "failed"

    def print_loading_plan(self, csv_files):
        print("\n" + "=" * 80)
        print("DATA LOADING PLAN")
        print("=" * 80)

        for csv_file in csv_files:
            file_name = os.path.basename(csv_file)
            table_name = self.get_table_name_for_file(csv_file)
            strategy = self.get_load_strategy(table_name)
            print(f"{file_name}  -->  {self.raw_schema}.{table_name}  [{strategy}]")

        print("=" * 80)

    def run_loading(self, data_dir):
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
            if not self.create_metadata_tables():
                return False

            csv_files = self.get_mapped_csv_files(data_dir)
            if not csv_files:
                self.log("No mapped CSV files found", "ERROR")
                return False

            self.log(f"Found {len(csv_files)} mapped CSV file(s)")
            self.print_loading_plan(csv_files)

            successful_files = 0
            skipped_files = 0
            total_rows_inserted = 0

            for csv_file in tqdm(csv_files, desc="Loading CSV files", unit="file"):
                success, rows_inserted, load_mode = self.load_one_csv(csv_file)
                if success:
                    successful_files += 1
                    total_rows_inserted += rows_inserted
                    if load_mode == "skip":
                        skipped_files += 1

            print("\n" + "=" * 80)
            print("DATA LOADING SUMMARY")
            print("=" * 80)

            self.log(f"Mapped files found: {len(csv_files)}")
            self.log(f"Files completed successfully: {successful_files}")
            self.log(f"Files skipped as unchanged: {skipped_files}")
            self.log(f"Rows inserted this run: {total_rows_inserted:,}")

            if successful_files == len(csv_files):
                self.log("ALL DATA LOADING TASKS COMPLETED SUCCESSFULLY", "SUCCESS")
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
        print("Next step: run downstream validation and transformations.")
        return 0

    print("\n[ERROR] Data loading failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())