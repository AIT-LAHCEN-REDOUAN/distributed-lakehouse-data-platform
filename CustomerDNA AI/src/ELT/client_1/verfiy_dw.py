"""
CustomerDNA AI - Verify Client 1 Data Warehouse

Location:
    src/ELT/client_1/verify_dw.py

Checks:
    1. Connection to client1_DW
    2. Required schemas
    3. Raw table registry from metadata.raw_table_registry
    4. Loaded files from metadata.loaded_files
    5. Actual raw_data table row counts
    6. Comparison between created tables and loaded tables
"""

import sys
import os
import psycopg2
from psycopg2 import sql

sys.path.append(os.path.join(os.path.dirname(__file__), "config"))

from config import (
    DATA_WAREHOUSE_NAME,
    CLIENT_DW_CONFIG,
    get_connection_params,
    validate_config,
)


EXPECTED_RAW_TABLES = [
    "marketing_campaign",
    "e_commerce_customer_churn",
    "category_tree",
    "events",
    "item_properties",
    "online_retail",
]


class DWVerifier:
    """Verifies Client 1 Data Warehouse."""

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

    def connect(self):
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
    # BASIC CHECKS
    # ============================================================================

    def verify_schemas(self):
        """Verify all required schemas exist."""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                ORDER BY schema_name
            """)

            existing_schemas = {row[0] for row in cursor.fetchall()}
            cursor.close()

            print("\n" + "=" * 80)
            print("SCHEMA CHECK")
            print("=" * 80)

            all_ok = True

            for schema_name in CLIENT_DW_CONFIG["schemas"]:
                if schema_name in existing_schemas:
                    self.log(f"{schema_name}: exists", "SUCCESS")
                else:
                    self.log(f"{schema_name}: missing", "ERROR")
                    all_ok = False

            return all_ok

        except Exception as e:
            self.log(f"Failed to verify schemas: {str(e)}", "ERROR")
            return False

    def table_exists(self, schema_name, table_name):
        """Check if table exists."""
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
            """, (schema_name, table_name))

            exists = cursor.fetchone()[0]
            cursor.close()
            return exists

        except Exception:
            return False

    def get_table_row_count(self, schema_name, table_name):
        """Return row count for a table."""
        try:
            cursor = self.connection.cursor()

            cursor.execute(
                sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name),
                )
            )

            row_count = cursor.fetchone()[0]
            cursor.close()
            return row_count

        except Exception as e:
            self.log(f"Failed to count {schema_name}.{table_name}: {str(e)}", "ERROR")
            return None

    def get_table_column_count(self, schema_name, table_name):
        """Return column count for a table."""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = %s
                AND table_name = %s
            """, (schema_name, table_name))

            column_count = cursor.fetchone()[0]
            cursor.close()
            return column_count

        except Exception as e:
            self.log(f"Failed to count columns for {schema_name}.{table_name}: {str(e)}", "ERROR")
            return None

    # ============================================================================
    # RAW TABLE CHECKS
    # ============================================================================

    def list_raw_tables(self):
        """List raw_data tables and row counts."""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (self.raw_schema,))

            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()

            print("\n" + "=" * 80)
            print("RAW DATA TABLES")
            print("=" * 80)

            if not tables:
                self.log("No raw_data tables found", "ERROR")
                return False

            total_rows = 0
            all_ok = True

            for table_name in tables:
                row_count = self.get_table_row_count(self.raw_schema, table_name)
                column_count = self.get_table_column_count(self.raw_schema, table_name)

                if row_count is None:
                    all_ok = False
                    continue

                total_rows += row_count

                print(
                    f"{self.raw_schema}.{table_name}: "
                    f"{row_count:,} rows | {column_count} columns"
                )

            print("-" * 80)
            print(f"Total raw rows: {total_rows:,}")

            return all_ok

        except Exception as e:
            self.log(f"Failed to list raw tables: {str(e)}", "ERROR")
            return False

    def verify_expected_raw_tables(self):
        """Verify expected raw tables exist and are loaded."""
        print("\n" + "=" * 80)
        print("EXPECTED RAW TABLES CHECK")
        print("=" * 80)

        all_ok = True

        for table_name in EXPECTED_RAW_TABLES:
            if not self.table_exists(self.raw_schema, table_name):
                self.log(f"{self.raw_schema}.{table_name}: missing", "ERROR")
                all_ok = False
                continue

            row_count = self.get_table_row_count(self.raw_schema, table_name)
            column_count = self.get_table_column_count(self.raw_schema, table_name)

            if row_count is None:
                all_ok = False
                continue

            if row_count == 0:
                self.log(
                    f"{self.raw_schema}.{table_name}: exists but empty | {column_count} columns",
                    "WARNING",
                )
                all_ok = False
            else:
                self.log(
                    f"{self.raw_schema}.{table_name}: OK | {row_count:,} rows | {column_count} columns",
                    "SUCCESS",
                )

        return all_ok

    # ============================================================================
    # METADATA CHECKS
    # ============================================================================

    def show_raw_table_registry(self):
        """Show metadata.raw_table_registry."""
        print("\n" + "=" * 80)
        print("RAW TABLE REGISTRY")
        print("=" * 80)

        if not self.table_exists(self.metadata_schema, "raw_table_registry"):
            self.log("metadata.raw_table_registry does not exist", "WARNING")
            return False

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT
                    file_name,
                    table_schema,
                    table_name,
                    column_count,
                    created_at
                FROM metadata.raw_table_registry
                ORDER BY table_name
            """)

            rows = cursor.fetchall()
            cursor.close()

            if not rows:
                self.log("metadata.raw_table_registry is empty", "WARNING")
                return False

            for file_name, table_schema, table_name, column_count, created_at in rows:
                print(
                    f"{file_name} -> {table_schema}.{table_name} | "
                    f"{column_count} columns | {created_at}"
                )

            return True

        except Exception as e:
            self.log(f"Failed to read metadata.raw_table_registry: {str(e)}", "ERROR")
            return False

    def show_loaded_files_metadata(self):
        """Show metadata.loaded_files."""
        print("\n" + "=" * 80)
        print("LOADED FILES METADATA")
        print("=" * 80)

        if not self.table_exists(self.metadata_schema, "loaded_files"):
            self.log("metadata.loaded_files does not exist", "WARNING")
            return False

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT
                    file_name,
                    table_schema,
                    table_name,
                    record_count,
                    loaded_at
                FROM metadata.loaded_files
                ORDER BY table_name
            """)

            rows = cursor.fetchall()
            cursor.close()

            if not rows:
                self.log("metadata.loaded_files is empty", "WARNING")
                return False

            for file_name, table_schema, table_name, record_count, loaded_at in rows:
                print(
                    f"{file_name} -> {table_schema}.{table_name}: "
                    f"{record_count:,} rows | {loaded_at}"
                )

            return True

        except Exception as e:
            self.log(f"Failed to read metadata.loaded_files: {str(e)}", "ERROR")
            return False

    def compare_registry_and_loaded_files(self):
        """Compare created table registry with loaded files metadata."""
        print("\n" + "=" * 80)
        print("REGISTRY VS LOADED FILES CHECK")
        print("=" * 80)

        if not self.table_exists(self.metadata_schema, "raw_table_registry"):
            self.log("Cannot compare: metadata.raw_table_registry missing", "WARNING")
            return False

        if not self.table_exists(self.metadata_schema, "loaded_files"):
            self.log("Cannot compare: metadata.loaded_files missing", "WARNING")
            return False

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT table_name
                FROM metadata.raw_table_registry
                ORDER BY table_name
            """)

            registered_tables = {row[0] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT table_name
                FROM metadata.loaded_files
                ORDER BY table_name
            """)

            loaded_tables = {row[0] for row in cursor.fetchall()}

            cursor.close()

            missing_loads = registered_tables - loaded_tables
            unexpected_loads = loaded_tables - registered_tables

            if not missing_loads and not unexpected_loads:
                self.log("Registry and loaded files metadata are aligned", "SUCCESS")
                return True

            if missing_loads:
                self.log(f"Tables created but not loaded: {sorted(missing_loads)}", "WARNING")

            if unexpected_loads:
                self.log(f"Tables loaded but not registered: {sorted(unexpected_loads)}", "WARNING")

            return False

        except Exception as e:
            self.log(f"Failed to compare metadata tables: {str(e)}", "ERROR")
            return False

    # ============================================================================
    # MAIN VERIFICATION
    # ============================================================================

    def run_verification(self):
        """Run all DW verification checks."""
        print("=" * 80)
        print("CUSTOMERDNA AI - VERIFY CLIENT 1 DATA WAREHOUSE")
        print("=" * 80)
        print(f"Database: {DATA_WAREHOUSE_NAME}")
        print(f"Raw schema: {self.raw_schema}")
        print(f"Metadata schema: {self.metadata_schema}")
        print("=" * 80)

        if not validate_config():
            return False

        if not self.connect():
            return False

        try:
            schemas_ok = self.verify_schemas()
            raw_tables_listed = self.list_raw_tables()
            expected_tables_ok = self.verify_expected_raw_tables()
            registry_ok = self.show_raw_table_registry()
            loaded_files_ok = self.show_loaded_files_metadata()
            metadata_alignment_ok = self.compare_registry_and_loaded_files()

            print("\n" + "=" * 80)
            print("VERIFICATION SUMMARY")
            print("=" * 80)

            checks = {
                "Schemas": schemas_ok,
                "Raw tables listed": raw_tables_listed,
                "Expected raw tables loaded": expected_tables_ok,
                "Raw table registry": registry_ok,
                "Loaded files metadata": loaded_files_ok,
                "Registry vs loaded files": metadata_alignment_ok,
            }

            for check_name, status in checks.items():
                if status:
                    self.log(f"{check_name}: OK", "SUCCESS")
                else:
                    self.log(f"{check_name}: WARNING/ERROR", "WARNING")

            all_ok = all(checks.values())

            if all_ok:
                self.log("DW verification completed successfully", "SUCCESS")
                return True

            self.log("DW verification completed with warnings/errors", "WARNING")
            return False

        finally:
            self.close_connection()


def main():
    verifier = DWVerifier(verbose=True)
    success = verifier.run_verification()

    if success:
        print("\n[SUCCESS] Data Warehouse is ready.")
        return 0

    print("\n[WARNING] Data Warehouse verification found issues.")
    return 1


if __name__ == "__main__":
    sys.exit(main())