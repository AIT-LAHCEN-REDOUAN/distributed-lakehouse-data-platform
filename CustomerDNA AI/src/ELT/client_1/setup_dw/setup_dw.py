"""
CustomerDNA AI - Client 1 Data Warehouse Setup

Creates only the client data warehouse:

    client1_DW

Schemas:
    raw_data          -> raw tables populated by the Kafka-backed loading pipeline
    metadata          -> loading metadata
    staging           -> future dbt staging models
    intermediate      -> future dbt intermediate models
    analytics         -> future marts / ML-ready tables
    reports           -> dashboard tables
    client_specific   -> client-specific objects

No separate client1_DB is used anymore.
"""

import sys
import os
import psycopg2
from psycopg2 import sql

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "config"))

from config import (
    DATA_WAREHOUSE_NAME,
    CLIENT_DW_CONFIG,
    get_connection_params,
    validate_config,
)


class ClientDWSetup:
    """Create and initialize the Client 1 Data Warehouse."""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.postgres_conn = None
        self.dw_conn = None

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

    def connect_to_postgres(self):
        """Connect to default PostgreSQL database."""
        try:
            self.postgres_conn = psycopg2.connect(
                **get_connection_params("postgres")
            )
            self.postgres_conn.autocommit = True
            self.log("Connected to PostgreSQL server")
            return True

        except Exception as e:
            self.log(f"Failed to connect to PostgreSQL server: {str(e)}", "ERROR")
            return False

    def create_database(self):
        """Create client DW database if it does not exist."""
        try:
            cursor = self.postgres_conn.cursor()

            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (DATA_WAREHOUSE_NAME,),
            )

            if cursor.fetchone():
                self.log(f"Database already exists: {DATA_WAREHOUSE_NAME}")
                cursor.close()
                return True

            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(DATA_WAREHOUSE_NAME)
                )
            )

            self.log(f"Created database: {DATA_WAREHOUSE_NAME}", "SUCCESS")
            cursor.close()
            return True

        except Exception as e:
            self.log(f"Failed to create database {DATA_WAREHOUSE_NAME}: {str(e)}", "ERROR")
            return False

    def connect_to_dw(self):
        """Connect to client DW database."""
        try:
            self.dw_conn = psycopg2.connect(
                **get_connection_params(DATA_WAREHOUSE_NAME)
            )
            self.dw_conn.autocommit = True
            self.log(f"Connected to Data Warehouse: {DATA_WAREHOUSE_NAME}")
            return True

        except Exception as e:
            self.log(f"Failed to connect to Data Warehouse: {str(e)}", "ERROR")
            return False

    def create_schemas(self):
        """Create DW schemas."""
        try:
            cursor = self.dw_conn.cursor()

            for schema_name in CLIENT_DW_CONFIG["schemas"]:
                cursor.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                        sql.Identifier(schema_name)
                    )
                )
                self.log(f"Schema created/verified: {schema_name}")

            cursor.close()
            return True

        except Exception as e:
            self.log(f"Failed to create schemas: {str(e)}", "ERROR")
            return False

    def create_metadata_tables(self):
        """Create metadata tables."""
        try:
            cursor = self.dw_conn.cursor()

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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata.pipeline_runs (
                    id SERIAL PRIMARY KEY,
                    pipeline_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finished_at TIMESTAMP,
                    details TEXT
                )
            """)

            self.log("Metadata tables created/verified")
            cursor.close()
            return True

        except Exception as e:
            self.log(f"Failed to create metadata tables: {str(e)}", "ERROR")
            return False

    def create_analytics_placeholders(self):
        """Create placeholder analytical tables."""
        try:
            cursor = self.dw_conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.customer_segments (
                    customer_id TEXT PRIMARY KEY,
                    segment TEXT NOT NULL,
                    recency_score INTEGER,
                    frequency_score INTEGER,
                    monetary_score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.sales_summary (
                    summary_date DATE PRIMARY KEY,
                    total_sales NUMERIC(14, 2),
                    total_orders INTEGER,
                    avg_order_value NUMERIC(14, 2),
                    unique_customers INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.product_performance (
                    product_id TEXT PRIMARY KEY,
                    product_name TEXT,
                    total_quantity_sold INTEGER,
                    total_revenue NUMERIC(14, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.log("Analytics placeholder tables created/verified")
            cursor.close()
            return True

        except Exception as e:
            self.log(f"Failed to create analytics placeholders: {str(e)}", "ERROR")
            return False

    def create_readme_table(self):
        """Create a small documentation table inside metadata."""
        try:
            cursor = self.dw_conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata.dw_documentation (
                    id SERIAL PRIMARY KEY,
                    object_name TEXT NOT NULL,
                    object_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                INSERT INTO metadata.dw_documentation
                    (object_name, object_type, description)
                VALUES
                    ('raw_data', 'schema', 'Stores raw ingested CSV tables as TEXT columns.'),
                    ('staging', 'schema', 'Future dbt staging models.'),
                    ('intermediate', 'schema', 'Future dbt intermediate business logic models.'),
                    ('analytics', 'schema', 'Final analytical and ML-ready tables.'),
                    ('reports', 'schema', 'Dashboard and reporting objects.'),
                    ('client_specific', 'schema', 'Client-specific extensions.')
                ON CONFLICT DO NOTHING
            """)

            cursor.close()
            self.log("DW documentation table created/verified")
            return True

        except Exception as e:
            self.log(f"Failed to create DW documentation table: {str(e)}", "WARNING")
            return True

    def run_setup(self):
        """Run complete DW setup."""
        print("=" * 70)
        print("CUSTOMERDNA AI - CLIENT 1 DATA WAREHOUSE SETUP")
        print("=" * 70)
        print(f"Database: {DATA_WAREHOUSE_NAME}")
        print("Architecture: Simplified ELT")
        print("Flow: source datasets -> Kafka -> client1_DW.raw_data -> dbt -> client1_DW.analytics")
        print("=" * 70)

        validate_config()

        if not self.connect_to_postgres():
            return False

        try:
            if not self.create_database():
                return False

            if not self.connect_to_dw():
                return False

            if not self.create_schemas():
                return False

            if not self.create_metadata_tables():
                return False

            if not self.create_analytics_placeholders():
                self.log("Analytics placeholder creation failed, continuing", "WARNING")

            self.create_readme_table()

            print("\n" + "=" * 70)
            self.log("DATA WAREHOUSE SETUP COMPLETED SUCCESSFULLY", "SUCCESS")
            print("=" * 70)

            self.log(f"Database: {DATA_WAREHOUSE_NAME}")
            self.log(f"Schemas: {', '.join(CLIENT_DW_CONFIG['schemas'])}")
            self.log("Raw data target: client1_DW.raw_data")
            self.log("Raw load mode: Kafka-backed batch ingestion")
            self.log("Future dbt target: client1_DW.analytics")

            return True

        except Exception as e:
            self.log(f"Setup failed: {str(e)}", "ERROR")
            return False

        finally:
            if self.dw_conn:
                self.dw_conn.close()

            if self.postgres_conn:
                self.postgres_conn.close()

            self.log("Closed database connections")


def main():
    setup = ClientDWSetup(verbose=True)
    success = setup.run_setup()

    if success:
        print("\n[SUCCESS] Client Data Warehouse setup completed.")
        return 0

    print("\n[ERROR] Client Data Warehouse setup failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
