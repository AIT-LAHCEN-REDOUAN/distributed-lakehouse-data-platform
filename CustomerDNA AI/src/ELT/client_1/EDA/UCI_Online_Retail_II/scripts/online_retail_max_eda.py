
#!/usr/bin/env python3
"""
UCI Online Retail II Dataset - Maximum EDA (Exploratory Data Analysis)

This script performs comprehensive exploratory data analysis on the
UCI Online Retail II dataset, which contains transactional data from
a UK-based online retail store.

Dataset Characteristics:
- 8 columns: invoice, stockcode, description, quantity, invoicedate, price, customer_id, country
- 1,067,371 rows of transactional data
- Time period: 01/12/2009 to 09/12/2011
- All customers are wholesalers

Key Analysis Areas:
1. Data Quality Assessment
2. Transaction Analysis
3. Customer Analysis
4. Product Analysis
5. Time Series Analysis
6. Geographic Analysis
7. Revenue Analysis
8. Customer Segmentation
"""

import os
import sys
import json
import warnings
from datetime import datetime

import psycopg2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add parent directory to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')))

try:
    from CustomerDNA_AI.src.ELT.client_1.config import config
    print("[INFO] Successfully loaded config from module")
except ImportError:
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config')
    sys.path.insert(0, config_path)
    try:
        import config
        print("[INFO] Successfully loaded config from direct path")
    except ImportError:
        print("[ERROR] Failed to import config module")
        sys.exit(1)

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", palette="deep")

# ============================================================================
# CONFIGURATION
# ============================================================================

DATABASE_CONFIG = {
    "host": config.POSTGRES_CONFIG["host"],
    "port": config.POSTGRES_CONFIG["port"],
    "database": f"client{config.CLIENT_ID}_DW",
    "user": config.POSTGRES_CONFIG["user"],
    "password": config.POSTGRES_CONFIG["password"]
}

RAW_DATA_SCHEMA = "raw_data"
TABLE_NAME = "online_retail"

CURRENT_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
OUTPUT_BASE_DIR = os.path.join(
    PROJECT_ROOT,
    "artifacts",
    "client_1",
    "elt_eda",
    "online_retail",
)
OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, f"max_eda_{CURRENT_TIMESTAMP}")

PLOT_DIR = os.path.join(OUTPUT_DIR, "plots")
DATA_DIR = os.path.join(OUTPUT_DIR, "data")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "summary.txt")
JSON_FILE = os.path.join(DATA_DIR, "eda_results.json")

PLOT_SUBDIRS = {
    "data_quality": os.path.join(PLOT_DIR, "01_data_quality"),
    "transaction_analysis": os.path.join(PLOT_DIR, "02_transaction_analysis"),
    "customer_analysis": os.path.join(PLOT_DIR, "03_customer_analysis"),
    "product_analysis": os.path.join(PLOT_DIR, "04_product_analysis"),
    "time_analysis": os.path.join(PLOT_DIR, "05_time_analysis"),
    "geographic_analysis": os.path.join(PLOT_DIR, "06_geographic_analysis"),
    "revenue_analysis": os.path.join(PLOT_DIR, "07_revenue_analysis"),
    "segmentation": os.path.join(PLOT_DIR, "08_segmentation")
}

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
for _, subdir_path in PLOT_SUBDIRS.items():
    os.makedirs(subdir_path, exist_ok=True)

print(f"[INFO] Output directory created: {OUTPUT_DIR}")


class OnlineRetailEDA:
    """Comprehensive EDA analyzer for UCI Online Retail II dataset."""

    def __init__(self, db_config, schema_name, table_name=TABLE_NAME):
        self.db_config = db_config
        self.schema_name = schema_name
        self.table_name = table_name
        self.conn = None
        self.cursor = None
        self.results = {}

    # ---------------------------------------------------------------------
    # SQL HELPER EXPRESSIONS
    # ---------------------------------------------------------------------

    @property
    def table_ref(self):
        return f'"{self.schema_name}"."{self.table_name}"'

    def txt(self, column_name):
        return f'NULLIF(TRIM(COALESCE({column_name}::text, \'\')), \'\')'

    def num(self, column_name):
        return f"""
        CASE
            WHEN {self.txt(column_name)} ~ '^[-+]?[0-9]*\\.?[0-9]+$'
            THEN ({self.txt(column_name)})::numeric
            ELSE NULL
        END
        """

    def ts(self, column_name):
        return f"""
        CASE
            WHEN {self.txt(column_name)} IS NULL THEN NULL
            WHEN {self.txt(column_name)} ~ '^\\d{{1,2}}/\\d{{1,2}}/\\d{{4}} \\d{{1,2}}:\\d{{2}}$'
                THEN TO_TIMESTAMP({self.txt(column_name)}, 'MM/DD/YYYY HH24:MI')
            WHEN {self.txt(column_name)} ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}'
                THEN ({self.txt(column_name)})::timestamp
            ELSE NULL
        END
        """

    # ---------------------------------------------------------------------
    # CONNECTION + EXECUTION
    # ---------------------------------------------------------------------

    def connect(self):
        """Connect to the PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print(f"[SUCCESS] Connected to database: {self.db_config['database']}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to connect to database: {e}")
            return False

    def disconnect(self):
        """Close cursor and connection."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
                print("[INFO] Database connection closed")
        except Exception as e:
            print(f"[WARNING] Error while closing database resources: {e}")

    def execute_query(self, query, params=None):
        """Execute a SQL query and return results."""
        try:
            self.cursor.execute(query, params)
            if self.cursor.description is not None:
                return self.cursor.fetchall()
            self.conn.commit()
            return True
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"[ERROR] Query execution failed: {e}")
            print(f"[ERROR] Query snippet: {query[:250]}...")
            return None

    def query_to_dataframe(self, query, params=None):
        """Return a pandas DataFrame from a SQL query."""
        try:
            return pd.read_sql_query(query, self.conn, params=params)
        except Exception as e:
            print(f"[ERROR] Failed to load dataframe: {e}")
            print(f"[ERROR] Query snippet: {query[:250]}...")
            return pd.DataFrame()

    # ---------------------------------------------------------------------
    # COMMON FILTERS
    # ---------------------------------------------------------------------

    def sales_where_clause(self):
        """Common filter for valid sales rows."""
        return f"""
        WHERE {self.txt("invoice")} IS NOT NULL
          AND {self.txt("stockcode")} IS NOT NULL
          AND {self.num("quantity")} IS NOT NULL
          AND {self.num("price")} IS NOT NULL
          AND {self.num("quantity")} > 0
          AND {self.num("price")} >= 0
          AND {self.txt("invoice")} NOT LIKE 'C%'
        """

    def any_valid_revenue_where_clause(self):
        """Rows where revenue can be computed, including returns."""
        return f"""
        WHERE {self.num("quantity")} IS NOT NULL
          AND {self.num("price")} IS NOT NULL
        """

    # ---------------------------------------------------------------------
    # DATA QUALITY ANALYSIS
    # ---------------------------------------------------------------------

    def analyze_data_quality(self):
        print("\n" + "=" * 80)
        print("DATA QUALITY ANALYSIS")
        print("=" * 80)

        quality_metrics = {}

        print("[INFO] Fetching schema columns...")
        query_columns = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
        """
        columns_result = self.execute_query(query_columns, (self.schema_name, self.table_name))
        if not columns_result:
            self.results["data_quality"] = quality_metrics
            return quality_metrics

        column_types = {col: dtype for col, dtype in columns_result}
        quality_metrics["column_types"] = column_types

        print("[INFO] Analyzing null / empty values...")
        total_rows_query = f"SELECT COUNT(*) FROM {self.table_ref};"
        total_rows_result = self.execute_query(total_rows_query)
        total_rows = total_rows_result[0][0] if total_rows_result else 0

        null_analysis = {}
        for column_name, _ in columns_result:
            query_null_col = f"""
                SELECT
                    COUNT(*) AS total_rows,
                    SUM(
                        CASE
                            WHEN {self.txt(f'"{column_name}"')} IS NULL THEN 1
                            ELSE 0
                        END
                    ) AS null_or_empty_count
                FROM {self.table_ref};
            """
            result = self.execute_query(query_null_col)
            if result and result[0]:
                _, null_count = result[0]
                null_percentage = round((null_count / total_rows) * 100, 2) if total_rows else 0
                null_analysis[column_name] = {
                    "total_rows": int(total_rows),
                    "null_or_empty_count": int(null_count or 0),
                    "null_percentage": float(null_percentage)
                }
        quality_metrics["null_analysis"] = null_analysis

        print("[INFO] Analyzing duplicate full rows...")
        query_duplicates = f"""
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT (
                    COALESCE(invoice::text, ''),
                    COALESCE(stockcode::text, ''),
                    COALESCE(description::text, ''),
                    COALESCE(quantity::text, ''),
                    COALESCE(invoicedate::text, ''),
                    COALESCE(price::text, ''),
                    COALESCE(customer_id::text, ''),
                    COALESCE(country::text, '')
                )) AS unique_rows
            FROM {self.table_ref};
        """
        dup_result = self.execute_query(query_duplicates)
        if dup_result and dup_result[0]:
            total_rows, unique_rows = dup_result[0]
            duplicate_count = total_rows - unique_rows
            duplicate_percentage = round((duplicate_count / total_rows) * 100, 2) if total_rows else 0
            quality_metrics["duplicate_analysis"] = {
                "total_rows": int(total_rows),
                "unique_rows": int(unique_rows),
                "duplicate_count": int(duplicate_count),
                "duplicate_percentage": float(duplicate_percentage)
            }

        print("[INFO] Analyzing numeric ranges and anomalies...")
        range_analysis = {}
        for column in ["quantity", "price"]:
            query_range = f"""
                SELECT
                    MIN({self.num(column)}) AS min_value,
                    MAX({self.num(column)}) AS max_value,
                    AVG({self.num(column)}) AS avg_value,
                    STDDEV({self.num(column)}) AS std_value,
                    SUM(CASE WHEN {self.num(column)} < 0 THEN 1 ELSE 0 END) AS negative_count,
                    SUM(CASE WHEN {self.num(column)} = 0 THEN 1 ELSE 0 END) AS zero_count
                FROM {self.table_ref};
            """
            result = self.execute_query(query_range)
            if result and result[0]:
                min_val, max_val, avg_val, std_val, negative_count, zero_count = result[0]
                range_analysis[column] = {
                    "min": float(min_val) if min_val is not None else None,
                    "max": float(max_val) if max_val is not None else None,
                    "average": float(avg_val) if avg_val is not None else None,
                    "std_dev": float(std_val) if std_val is not None else None,
                    "negative_count": int(negative_count or 0),
                    "zero_count": int(zero_count or 0)
                }
        quality_metrics["range_analysis"] = range_analysis

        print("[INFO] Checking special business anomalies...")
        anomaly_queries = {
            "cancelled_invoice_rows": f"SELECT COUNT(*) FROM {self.table_ref} WHERE {self.txt('invoice')} LIKE 'C%';",
            "missing_descriptions": f"SELECT COUNT(*) FROM {self.table_ref} WHERE {self.txt('description')} IS NULL;",
            "missing_customer_ids": f"SELECT COUNT(*) FROM {self.table_ref} WHERE {self.txt('customer_id')} IS NULL;",
            "invalid_dates": f"SELECT COUNT(*) FROM {self.table_ref} WHERE {self.txt('invoicedate')} IS NOT NULL AND {self.ts('invoicedate')} IS NULL;"
        }
        anomaly_results = {}
        for metric_name, query in anomaly_queries.items():
            result = self.execute_query(query)
            anomaly_results[metric_name] = int(result[0][0]) if result else 0
        quality_metrics["anomaly_checks"] = anomaly_results

        self.results["data_quality"] = quality_metrics
        print("[SUCCESS] Data quality analysis completed!")
        return quality_metrics

    # ---------------------------------------------------------------------
    # TRANSACTION ANALYSIS
    # ---------------------------------------------------------------------

    def analyze_transactions(self):
        print("\n" + "=" * 80)
        print("TRANSACTION ANALYSIS")
        print("=" * 80)

        transaction_metrics = {}

        print("[INFO] Analyzing invoice statistics...")
        query_invoice_stats = f"""
            SELECT
                COUNT(DISTINCT invoice) AS total_invoices,
                COUNT(*) AS total_transactions,
                ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT invoice), 0), 2) AS avg_items_per_invoice
            FROM {self.table_ref}
            {self.sales_where_clause()};
        """
        result = self.execute_query(query_invoice_stats)
        if result and result[0]:
            total_invoices, total_transactions, avg_items = result[0]
            transaction_metrics["invoice_statistics"] = {
                "total_invoices": int(total_invoices),
                "total_transactions": int(total_transactions),
                "average_items_per_invoice": float(avg_items or 0)
            }

        print("[INFO] Analyzing invoice size distribution...")
        query_invoice_sizes = f"""
            SELECT
                invoice,
                COUNT(*) AS item_count,
                SUM({self.num("quantity")}) AS total_quantity,
                SUM({self.num("quantity")} * {self.num("price")}) AS total_value
            FROM {self.table_ref}
            {self.sales_where_clause()}
            GROUP BY invoice
            ORDER BY item_count DESC;
        """
        df_invoice_sizes = self.query_to_dataframe(query_invoice_sizes)
        if not df_invoice_sizes.empty:
            invoice_sizes = df_invoice_sizes.to_dict(orient="records")
            for row in invoice_sizes:
                row["item_count"] = int(row["item_count"])
                row["total_quantity"] = float(row["total_quantity"] or 0)
                row["total_value"] = float(row["total_value"] or 0)
            transaction_metrics["invoice_sizes"] = invoice_sizes

            item_counts = df_invoice_sizes["item_count"].astype(float)
            total_values = df_invoice_sizes["total_value"].astype(float)
            transaction_metrics["size_statistics"] = {
                "min_items": float(item_counts.min()),
                "max_items": float(item_counts.max()),
                "avg_items": float(item_counts.mean()),
                "median_items": float(item_counts.median()),
                "min_value": float(total_values.min()),
                "max_value": float(total_values.max()),
                "avg_value": float(total_values.mean()),
                "median_value": float(total_values.median())
            }

        print("[INFO] Analyzing cancelled transactions...")
        query_cancelled = f"""
            SELECT
                COUNT(*) AS total_cancelled_rows,
                COUNT(DISTINCT invoice) AS unique_cancelled_invoices,
                COALESCE(SUM({self.num("quantity")} * {self.num("price")}), 0) AS cancelled_value
            FROM {self.table_ref}
            WHERE {self.txt("invoice")} LIKE 'C%';
        """
        result = self.execute_query(query_cancelled)
        if result and result[0]:
            total_cancelled, unique_cancelled, cancelled_value = result[0]
            transaction_metrics["cancelled_transactions"] = {
                "total_cancelled_items": int(total_cancelled or 0),
                "unique_cancelled_invoices": int(unique_cancelled or 0),
                "cancelled_value": float(cancelled_value or 0)
            }

        print("[INFO] Analyzing basket composition...")
        query_basket = f"""
            WITH invoice_product_counts AS (
                SELECT
                    invoice,
                    COUNT(DISTINCT stockcode) AS unique_products
                FROM {self.table_ref}
                {self.sales_where_clause()}
                GROUP BY invoice
            )
            SELECT
                AVG(unique_products) AS avg_unique_products,
                MIN(unique_products) AS min_unique_products,
                MAX(unique_products) AS max_unique_products
            FROM invoice_product_counts;
        """
        result = self.execute_query(query_basket)
        if result and result[0]:
            avg_u, min_u, max_u = result[0]
            transaction_metrics["basket_composition"] = {
                "average_unique_products_per_invoice": float(avg_u or 0),
                "minimum_unique_products_per_invoice": int(min_u or 0),
                "maximum_unique_products_per_invoice": int(max_u or 0)
            }

        self.results["transaction_analysis"] = transaction_metrics
        print("[SUCCESS] Transaction analysis completed!")
        return transaction_metrics

    # ---------------------------------------------------------------------
    # CUSTOMER ANALYSIS
    # ---------------------------------------------------------------------

    def analyze_customers(self):
        print("\n" + "=" * 80)
        print("CUSTOMER ANALYSIS")
        print("=" * 80)

        customer_metrics = {}

        print("[INFO] Analyzing customer statistics...")
        query_customer_stats = f"""
            SELECT
                COUNT(DISTINCT customer_id) FILTER (WHERE {self.txt("customer_id")} IS NOT NULL) AS total_customers,
                SUM(CASE WHEN {self.txt("customer_id")} IS NULL THEN 1 ELSE 0 END) AS missing_customer_ids,
                COUNT(*) AS total_rows
            FROM {self.table_ref};
        """
        result = self.execute_query(query_customer_stats)
        if result and result[0]:
            total_customers, missing_ids, total_rows = result[0]
            customer_metrics["customer_statistics"] = {
                "total_customers": int(total_customers or 0),
                "missing_customer_ids": int(missing_ids or 0),
                "missing_percentage": round((missing_ids / total_rows) * 100, 2) if total_rows else 0
            }

        print("[INFO] Identifying top customers...")
        query_top_customers = f"""
            SELECT
                customer_id,
                COUNT(DISTINCT invoice) AS invoice_count,
                SUM({self.num("quantity")}) AS total_quantity,
                SUM({self.num("quantity")} * {self.num("price")}) AS total_spent
            FROM {self.table_ref}
            {self.sales_where_clause()}
              AND {self.txt("customer_id")} IS NOT NULL
            GROUP BY customer_id
            ORDER BY total_spent DESC
            LIMIT 20;
        """
        df_top_customers = self.query_to_dataframe(query_top_customers)
        if not df_top_customers.empty:
            customer_metrics["top_customers"] = [
                {
                    "customer_id": str(row["customer_id"]),
                    "invoice_count": int(row["invoice_count"]),
                    "total_quantity": float(row["total_quantity"] or 0),
                    "total_spent": float(row["total_spent"] or 0),
                }
                for _, row in df_top_customers.iterrows()
            ]

        print("[INFO] Analyzing customer purchase frequency...")
        query_purchase_freq = f"""
            WITH customer_invoices AS (
                SELECT
                    customer_id,
                    COUNT(DISTINCT invoice) AS invoice_count
                FROM {self.table_ref}
                {self.sales_where_clause()}
                  AND {self.txt("customer_id")} IS NOT NULL
                GROUP BY customer_id
            )
            SELECT
                invoice_count,
                COUNT(*) AS customer_count
            FROM customer_invoices
            GROUP BY invoice_count
            ORDER BY invoice_count;
        """
        df_freq = self.query_to_dataframe(query_purchase_freq)
        if not df_freq.empty:
            customer_metrics["purchase_frequency"] = [
                {
                    "invoice_count": int(row["invoice_count"]),
                    "customer_count": int(row["customer_count"])
                }
                for _, row in df_freq.iterrows()
            ]

        print("[INFO] Analyzing customer recency...")
        query_recency = f"""
            WITH latest_purchases AS (
                SELECT
                    customer_id,
                    MAX({self.ts("invoicedate")}) AS last_purchase_date
                FROM {self.table_ref}
                {self.sales_where_clause()}
                  AND {self.txt("customer_id")} IS NOT NULL
                  AND {self.ts("invoicedate")} IS NOT NULL
                GROUP BY customer_id
            ),
            dataset_max AS (
                SELECT MAX({self.ts("invoicedate")}) AS max_dt
                FROM {self.table_ref}
                WHERE {self.ts("invoicedate")} IS NOT NULL
            )
            SELECT
                l.customer_id,
                l.last_purchase_date,
                EXTRACT(DAY FROM (d.max_dt - l.last_purchase_date)) AS days_since_last_purchase
            FROM latest_purchases l
            CROSS JOIN dataset_max d
            ORDER BY days_since_last_purchase DESC
            LIMIT 20;
        """
        df_recency = self.query_to_dataframe(query_recency)
        if not df_recency.empty:
            customer_metrics["customer_recency"] = [
                {
                    "customer_id": str(row["customer_id"]),
                    "last_purchase_date": row["last_purchase_date"].strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(row["last_purchase_date"]) else None,
                    "days_since_last_purchase": float(row["days_since_last_purchase"]) if pd.notnull(row["days_since_last_purchase"]) else None,
                }
                for _, row in df_recency.iterrows()
            ]

        print("[INFO] Building customer value summary...")
        query_customer_value = f"""
            SELECT
                customer_id,
                COUNT(DISTINCT invoice) AS invoice_count,
                SUM({self.num("quantity")} * {self.num("price")}) AS revenue,
                AVG({self.num("quantity")} * {self.num("price")}) AS avg_line_value
            FROM {self.table_ref}
            {self.sales_where_clause()}
              AND {self.txt("customer_id")} IS NOT NULL
            GROUP BY customer_id
            ORDER BY revenue DESC;
        """
        df_customer_value = self.query_to_dataframe(query_customer_value)
        if not df_customer_value.empty:
            customer_metrics["customer_value_summary"] = {
                "average_customer_revenue": float(df_customer_value["revenue"].mean()),
                "median_customer_revenue": float(df_customer_value["revenue"].median()),
                "max_customer_revenue": float(df_customer_value["revenue"].max()),
                "average_customer_invoices": float(df_customer_value["invoice_count"].mean())
            }

        self.results["customer_analysis"] = customer_metrics
        print("[SUCCESS] Customer analysis completed!")
        return customer_metrics

    # ---------------------------------------------------------------------
    # PRODUCT ANALYSIS
    # ---------------------------------------------------------------------

    def analyze_products(self):
        print("\n" + "=" * 80)
        print("PRODUCT ANALYSIS")
        print("=" * 80)

        product_metrics = {}

        print("[INFO] Analyzing product statistics...")
        query_product_stats = f"""
            SELECT
                COUNT(DISTINCT stockcode) FILTER (WHERE {self.txt("stockcode")} IS NOT NULL) AS total_products,
                COUNT(DISTINCT description) FILTER (WHERE {self.txt("description")} IS NOT NULL) AS unique_descriptions
            FROM {self.table_ref};
        """
        result = self.execute_query(query_product_stats)
        if result and result[0]:
            total_products, unique_descriptions = result[0]
            product_metrics["product_statistics"] = {
                "total_products": int(total_products or 0),
                "unique_descriptions": int(unique_descriptions or 0)
            }

        print("[INFO] Identifying top selling products...")
        query_top_products = f"""
            SELECT
                stockcode,
                MAX(description) AS description,
                COUNT(*) AS transaction_count,
                SUM({self.num("quantity")}) AS total_quantity,
                SUM({self.num("quantity")} * {self.num("price")}) AS total_revenue
            FROM {self.table_ref}
            {self.sales_where_clause()}
            GROUP BY stockcode
            ORDER BY total_revenue DESC
            LIMIT 20;
        """
        df_top_products = self.query_to_dataframe(query_top_products)
        if not df_top_products.empty:
            product_metrics["top_products"] = [
                {
                    "stockcode": str(row["stockcode"]),
                    "description": row["description"],
                    "transaction_count": int(row["transaction_count"]),
                    "total_quantity": float(row["total_quantity"] or 0),
                    "total_revenue": float(row["total_revenue"] or 0),
                }
                for _, row in df_top_products.iterrows()
            ]

        print("[INFO] Analyzing product prices...")
        query_price_analysis = f"""
            SELECT
                stockcode,
                MAX(description) AS description,
                AVG({self.num("price")}) AS avg_price,
                MIN({self.num("price")}) AS min_price,
                MAX({self.num("price")}) AS max_price,
                COUNT(*) AS transaction_count
            FROM {self.table_ref}
            WHERE {self.txt("stockcode")} IS NOT NULL
              AND {self.num("price")} IS NOT NULL
            GROUP BY stockcode
            HAVING COUNT(*) >= 10
            ORDER BY transaction_count DESC
            LIMIT 20;
        """
        df_price = self.query_to_dataframe(query_price_analysis)
        if not df_price.empty:
            product_metrics["price_analysis"] = [
                {
                    "stockcode": str(row["stockcode"]),
                    "description": row["description"],
                    "average_price": float(row["avg_price"] or 0),
                    "minimum_price": float(row["min_price"] or 0),
                    "maximum_price": float(row["max_price"] or 0),
                    "transaction_count": int(row["transaction_count"])
                }
                for _, row in df_price.iterrows()
            ]

        print("[INFO] Analyzing product categories...")
        query_categories = f"""
            SELECT
                UPPER(TRIM(SPLIT_PART(description, ' ', 1))) AS category_prefix,
                COUNT(DISTINCT stockcode) AS product_count,
                SUM({self.num("quantity")} * {self.num("price")}) AS total_revenue
            FROM {self.table_ref}
            {self.sales_where_clause()}
              AND {self.txt("description")} IS NOT NULL
            GROUP BY category_prefix
            HAVING COUNT(DISTINCT stockcode) >= 5
            ORDER BY total_revenue DESC
            LIMIT 15;
        """
        df_categories = self.query_to_dataframe(query_categories)
        if not df_categories.empty:
            product_metrics["product_categories"] = [
                {
                    "category": row["category_prefix"] if pd.notnull(row["category_prefix"]) else "UNKNOWN",
                    "product_count": int(row["product_count"]),
                    "total_revenue": float(row["total_revenue"] or 0)
                }
                for _, row in df_categories.iterrows()
            ]

        print("[INFO] Identifying low-frequency / long-tail products...")
        query_long_tail = f"""
            WITH product_sales AS (
                SELECT
                    stockcode,
                    MAX(description) AS description,
                    COUNT(DISTINCT invoice) AS invoice_count,
                    SUM({self.num("quantity")} * {self.num("price")}) AS revenue
                FROM {self.table_ref}
                {self.sales_where_clause()}
                GROUP BY stockcode
            )
            SELECT
                COUNT(*) AS total_products,
                COUNT(*) FILTER (WHERE invoice_count = 1) AS sold_once_products,
                COUNT(*) FILTER (WHERE invoice_count <= 5) AS sold_five_or_less_products
            FROM product_sales;
        """
        result = self.execute_query(query_long_tail)
        if result and result[0]:
            total_products, sold_once, sold_five_or_less = result[0]
            product_metrics["long_tail_summary"] = {
                "total_products": int(total_products or 0),
                "sold_once_products": int(sold_once or 0),
                "sold_five_or_less_products": int(sold_five_or_less or 0)
            }

        self.results["product_analysis"] = product_metrics
        print("[SUCCESS] Product analysis completed!")
        return product_metrics

    # ---------------------------------------------------------------------
    # TIME SERIES ANALYSIS
    # ---------------------------------------------------------------------

    def analyze_time_series(self):
        print("\n" + "=" * 80)
        print("TIME SERIES ANALYSIS")
        print("=" * 80)

        time_metrics = {}

        print("[INFO] Analyzing time range...")
        query_time_range = f"""
            SELECT
                MIN({self.ts("invoicedate")}) AS earliest_date,
                MAX({self.ts("invoicedate")}) AS latest_date,
                EXTRACT(DAY FROM (MAX({self.ts("invoicedate")}) - MIN({self.ts("invoicedate")}))) AS total_days
            FROM {self.table_ref}
            WHERE {self.ts("invoicedate")} IS NOT NULL;
        """
        result = self.execute_query(query_time_range)
        if result and result[0]:
            earliest, latest, total_days = result[0]
            time_metrics["time_range"] = {
                "earliest_date": earliest.strftime("%Y-%m-%d %H:%M:%S") if earliest else None,
                "latest_date": latest.strftime("%Y-%m-%d %H:%M:%S") if latest else None,
                "total_days": float(total_days or 0)
            }

        print("[INFO] Analyzing daily transaction patterns...")
        query_daily = f"""
            SELECT
                DATE({self.ts("invoicedate")}) AS transaction_date,
                COUNT(*) AS transaction_count,
                COUNT(DISTINCT invoice) AS invoice_count,
                COUNT(DISTINCT customer_id) FILTER (WHERE {self.txt("customer_id")} IS NOT NULL) AS customer_count,
                SUM({self.num("quantity")} * {self.num("price")}) AS daily_revenue
            FROM {self.table_ref}
            {self.sales_where_clause()}
              AND {self.ts("invoicedate")} IS NOT NULL
            GROUP BY transaction_date
            ORDER BY transaction_date;
        """
        df_daily = self.query_to_dataframe(query_daily)
        if not df_daily.empty:
            time_metrics["daily_patterns"] = [
                {
                    "date": row["transaction_date"].strftime("%Y-%m-%d") if pd.notnull(row["transaction_date"]) else None,
                    "transaction_count": int(row["transaction_count"]),
                    "invoice_count": int(row["invoice_count"]),
                    "customer_count": int(row["customer_count"]),
                    "daily_revenue": float(row["daily_revenue"] or 0)
                }
                for _, row in df_daily.iterrows()
            ]

        print("[INFO] Analyzing monthly trends...")
        query_monthly = f"""
            SELECT
                EXTRACT(YEAR FROM {self.ts("invoicedate")}) AS year,
                EXTRACT(MONTH FROM {self.ts("invoicedate")}) AS month,
                COUNT(*) AS transaction_count,
                COUNT(DISTINCT invoice) AS invoice_count,
                SUM({self.num("quantity")} * {self.num("price")}) AS monthly_revenue,
                COUNT(DISTINCT customer_id) FILTER (WHERE {self.txt("customer_id")} IS NOT NULL) AS unique_customers
            FROM {self.table_ref}
            {self.sales_where_clause()}
              AND {self.ts("invoicedate")} IS NOT NULL
            GROUP BY year, month
            ORDER BY year, month;
        """
        df_monthly = self.query_to_dataframe(query_monthly)
        if not df_monthly.empty:
            time_metrics["monthly_trends"] = [
                {
                    "year": int(row["year"]),
                    "month": int(row["month"]),
                    "transaction_count": int(row["transaction_count"]),
                    "invoice_count": int(row["invoice_count"]),
                    "monthly_revenue": float(row["monthly_revenue"] or 0),
                    "unique_customers": int(row["unique_customers"])
                }
                for _, row in df_monthly.iterrows()
            ]

        print("[INFO] Analyzing hourly patterns...")
        query_hourly = f"""
            SELECT
                EXTRACT(HOUR FROM {self.ts("invoicedate")}) AS hour_of_day,
                COUNT(*) AS transaction_count,
                SUM({self.num("quantity")} * {self.num("price")}) AS hourly_revenue
            FROM {self.table_ref}
            {self.sales_where_clause()}
              AND {self.ts("invoicedate")} IS NOT NULL
            GROUP BY hour_of_day
            ORDER BY hour_of_day;
        """
        df_hourly = self.query_to_dataframe(query_hourly)
        if not df_hourly.empty:
            time_metrics["hourly_patterns"] = [
                {
                    "hour": int(row["hour_of_day"]),
                    "transaction_count": int(row["transaction_count"]),
                    "hourly_revenue": float(row["hourly_revenue"] or 0)
                }
                for _, row in df_hourly.iterrows()
            ]

        print("[INFO] Analyzing day-of-week patterns...")
        query_dow = f"""
            SELECT
                EXTRACT(DOW FROM {self.ts("invoicedate")}) AS day_of_week,
                COUNT(*) AS transaction_count,
                SUM({self.num("quantity")} * {self.num("price")}) AS daily_revenue
            FROM {self.table_ref}
            {self.sales_where_clause()}
              AND {self.ts("invoicedate")} IS NOT NULL
            GROUP BY day_of_week
            ORDER BY day_of_week;
        """
        df_dow = self.query_to_dataframe(query_dow)
        if not df_dow.empty:
            day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            time_metrics["day_of_week_patterns"] = [
                {
                    "day_of_week": int(row["day_of_week"]),
                    "day_name": day_names[int(row["day_of_week"])],
                    "transaction_count": int(row["transaction_count"]),
                    "daily_revenue": float(row["daily_revenue"] or 0)
                }
                for _, row in df_dow.iterrows()
            ]

        print("[INFO] Computing month-over-month growth...")
        if "monthly_trends" in time_metrics and time_metrics["monthly_trends"]:
            df = pd.DataFrame(time_metrics["monthly_trends"]).sort_values(["year", "month"]).reset_index(drop=True)
            df["revenue_growth_pct"] = df["monthly_revenue"].pct_change() * 100
            time_metrics["monthly_growth"] = [
                {
                    "year": int(row["year"]),
                    "month": int(row["month"]),
                    "monthly_revenue": float(row["monthly_revenue"]),
                    "revenue_growth_pct": None if pd.isna(row["revenue_growth_pct"]) else float(row["revenue_growth_pct"])
                }
                for _, row in df.iterrows()
            ]

        self.results["time_analysis"] = time_metrics
        print("[SUCCESS] Time series analysis completed!")
        return time_metrics

    # ---------------------------------------------------------------------
    # GEOGRAPHIC ANALYSIS
    # ---------------------------------------------------------------------

    def analyze_geography(self):
        print("\n" + "=" * 80)
        print("GEOGRAPHIC ANALYSIS")
        print("=" * 80)

        geo_metrics = {}

        print("[INFO] Analyzing country distribution...")
        query_country = f"""
            SELECT
                country,
                COUNT(*) AS transaction_count,
                COUNT(DISTINCT customer_id) FILTER (WHERE {self.txt("customer_id")} IS NOT NULL) AS customer_count,
                SUM({self.num("quantity")} * {self.num("price")}) AS total_revenue,
                AVG({self.num("quantity")} * {self.num("price")}) AS avg_transaction_value
            FROM {self.table_ref}
            {self.sales_where_clause()}
              AND {self.txt("country")} IS NOT NULL
            GROUP BY country
            ORDER BY total_revenue DESC;
        """
        df_country = self.query_to_dataframe(query_country)
        if not df_country.empty:
            geo_metrics["country_statistics"] = [
                {
                    "country": row["country"],
                    "transaction_count": int(row["transaction_count"]),
                    "customer_count": int(row["customer_count"]),
                    "total_revenue": float(row["total_revenue"] or 0),
                    "average_transaction_value": float(row["avg_transaction_value"] or 0)
                }
                for _, row in df_country.iterrows()
            ]
            geo_metrics["top_countries"] = geo_metrics["country_statistics"][:10]

            total_revenue = float(df_country["total_revenue"].sum())
            total_customers = float(df_country["customer_count"].sum())
            uk_row = df_country[df_country["country"] == "United Kingdom"]
            if not uk_row.empty and total_revenue > 0 and total_customers > 0:
                uk_revenue = float(uk_row["total_revenue"].iloc[0])
                uk_customers = float(uk_row["customer_count"].iloc[0])
                geo_metrics["concentration_analysis"] = {
                    "uk_revenue_share": round((uk_revenue / total_revenue) * 100, 2),
                    "uk_customer_share": round((uk_customers / total_customers) * 100, 2),
                    "total_countries": int(len(df_country)),
                    "total_revenue": total_revenue,
                    "total_customers": int(total_customers)
                }

        self.results["geographic_analysis"] = geo_metrics
        print("[SUCCESS] Geographic analysis completed!")
        return geo_metrics

    # ---------------------------------------------------------------------
    # REVENUE ANALYSIS
    # ---------------------------------------------------------------------

    def analyze_revenue(self):
        print("\n" + "=" * 80)
        print("REVENUE ANALYSIS")
        print("=" * 80)

        revenue_metrics = {}

        print("[INFO] Calculating overall revenue statistics...")
        query_revenue_stats = f"""
            SELECT
                SUM({self.num("quantity")} * {self.num("price")}) AS total_revenue,
                AVG({self.num("quantity")} * {self.num("price")}) AS avg_transaction_value,
                MIN({self.num("quantity")} * {self.num("price")}) AS min_transaction_value,
                MAX({self.num("quantity")} * {self.num("price")}) AS max_transaction_value,
                COUNT(*) AS total_transactions
            FROM {self.table_ref}
            {self.sales_where_clause()};
        """
        result = self.execute_query(query_revenue_stats)
        if result and result[0]:
            total_rev, avg_value, min_value, max_value, total_trans = result[0]
            revenue_metrics["overall_statistics"] = {
                "total_revenue": float(total_rev or 0),
                "average_transaction_value": float(avg_value or 0),
                "minimum_transaction_value": float(min_value or 0),
                "maximum_transaction_value": float(max_value or 0),
                "total_transactions": int(total_trans or 0)
            }

        print("[INFO] Analyzing revenue by customer segment...")
        query_revenue_segments = f"""
            WITH customer_revenue AS (
                SELECT
                    customer_id,
                    SUM({self.num("quantity")} * {self.num("price")}) AS total_spent,
                    COUNT(DISTINCT invoice) AS invoice_count
                FROM {self.table_ref}
                {self.sales_where_clause()}
                  AND {self.txt("customer_id")} IS NOT NULL
                GROUP BY customer_id
            )
            SELECT
                CASE
                    WHEN total_spent >= 10000 THEN 'VIP (>10K)'
                    WHEN total_spent >= 5000 THEN 'High Value (5K-10K)'
                    WHEN total_spent >= 1000 THEN 'Mid Value (1K-5K)'
                    WHEN total_spent >= 250 THEN 'Low Value (250-1K)'
                    ELSE 'Small Value (<250)'
                END AS revenue_segment,
                COUNT(*) AS customer_count,
                SUM(total_spent) AS segment_revenue,
                AVG(total_spent) AS avg_customer_revenue,
                AVG(invoice_count) AS avg_invoice_count
            FROM customer_revenue
            GROUP BY revenue_segment
            ORDER BY segment_revenue DESC;
        """
        df_segments = self.query_to_dataframe(query_revenue_segments)
        if not df_segments.empty:
            revenue_metrics["customer_revenue_segments"] = [
                {
                    "revenue_segment": row["revenue_segment"],
                    "customer_count": int(row["customer_count"]),
                    "segment_revenue": float(row["segment_revenue"] or 0),
                    "average_customer_revenue": float(row["avg_customer_revenue"] or 0),
                    "average_invoice_count": float(row["avg_invoice_count"] or 0)
                }
                for _, row in df_segments.iterrows()
            ]

        print("[INFO] Identifying highest-value invoices...")
        query_top_invoices = f"""
            SELECT
                invoice,
                COUNT(*) AS line_count,
                SUM({self.num("quantity")} * {self.num("price")}) AS invoice_value
            FROM {self.table_ref}
            {self.sales_where_clause()}
            GROUP BY invoice
            ORDER BY invoice_value DESC
            LIMIT 20;
        """
        df_top_invoices = self.query_to_dataframe(query_top_invoices)
        if not df_top_invoices.empty:
            revenue_metrics["top_invoices"] = [
                {
                    "invoice": row["invoice"],
                    "line_count": int(row["line_count"]),
                    "invoice_value": float(row["invoice_value"] or 0)
                }
                for _, row in df_top_invoices.iterrows()
            ]

        print("[INFO] Computing revenue concentration (Pareto-style)...")
        query_customer_revenue = f"""
            SELECT
                customer_id,
                SUM({self.num("quantity")} * {self.num("price")}) AS revenue
            FROM {self.table_ref}
            {self.sales_where_clause()}
              AND {self.txt("customer_id")} IS NOT NULL
            GROUP BY customer_id
            ORDER BY revenue DESC;
        """
        df_cust_rev = self.query_to_dataframe(query_customer_revenue)
        if not df_cust_rev.empty:
            df_cust_rev = df_cust_rev.sort_values("revenue", ascending=False).reset_index(drop=True)
            total_rev = float(df_cust_rev["revenue"].sum())
            top_10pct_count = max(1, int(np.ceil(len(df_cust_rev) * 0.10)))
            top_20pct_count = max(1, int(np.ceil(len(df_cust_rev) * 0.20)))
            revenue_metrics["revenue_concentration"] = {
                "top_10pct_customer_revenue_share": round((df_cust_rev.head(top_10pct_count)["revenue"].sum() / total_rev) * 100, 2),
                "top_20pct_customer_revenue_share": round((df_cust_rev.head(top_20pct_count)["revenue"].sum() / total_rev) * 100, 2),
                "total_customers_ranked": int(len(df_cust_rev))
            }

        self.results["revenue_analysis"] = revenue_metrics
        print("[SUCCESS] Revenue analysis completed!")
        return revenue_metrics

    # ---------------------------------------------------------------------
    # CUSTOMER SEGMENTATION (RFM)
    # ---------------------------------------------------------------------

    def analyze_segmentation(self):
        print("\n" + "=" * 80)
        print("CUSTOMER SEGMENTATION")
        print("=" * 80)

        segmentation_metrics = {}

        print("[INFO] Building RFM table...")
        query_rfm = f"""
            WITH base_sales AS (
                SELECT
                    customer_id,
                    invoice,
                    {self.ts("invoicedate")} AS invoice_ts,
                    ({self.num("quantity")} * {self.num("price")}) AS line_revenue
                FROM {self.table_ref}
                {self.sales_where_clause()}
                  AND {self.txt("customer_id")} IS NOT NULL
                  AND {self.ts("invoicedate")} IS NOT NULL
            ),
            snapshot AS (
                SELECT MAX(invoice_ts) AS snapshot_date
                FROM base_sales
            ),
            customer_rfm AS (
                SELECT
                    b.customer_id,
                    EXTRACT(DAY FROM (s.snapshot_date - MAX(b.invoice_ts))) AS recency,
                    COUNT(DISTINCT b.invoice) AS frequency,
                    SUM(b.line_revenue) AS monetary
                FROM base_sales b
                CROSS JOIN snapshot s
                GROUP BY b.customer_id, s.snapshot_date
            ),
            scored AS (
                SELECT
                    customer_id,
                    recency,
                    frequency,
                    monetary,
                    6 - NTILE(5) OVER (ORDER BY recency ASC) AS r_score,
                    NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
                    NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
                FROM customer_rfm
            )
            SELECT
                customer_id,
                recency,
                frequency,
                monetary,
                r_score,
                f_score,
                m_score,
                CONCAT(r_score, f_score, m_score) AS rfm_score
            FROM scored
            ORDER BY monetary DESC;
        """
        df_rfm = self.query_to_dataframe(query_rfm)
        if df_rfm.empty:
            self.results["segmentation"] = segmentation_metrics
            print("[WARNING] Segmentation analysis returned no rows")
            return segmentation_metrics

        def label_segment(row):
            r, f, m = int(row["r_score"]), int(row["f_score"]), int(row["m_score"])
            if r >= 4 and f >= 4 and m >= 4:
                return "Champions"
            if r >= 4 and f >= 3 and m >= 3:
                return "Loyal Customers"
            if r >= 4 and f <= 2:
                return "Recent Customers"
            if r == 3 and f >= 3 and m >= 3:
                return "Potential Loyalists"
            if r <= 2 and f >= 4 and m >= 3:
                return "At Risk"
            if r <= 2 and f <= 2 and m <= 2:
                return "Hibernating"
            if m >= 4 and f <= 2:
                return "Big Spenders"
            return "Others"

        df_rfm["segment"] = df_rfm.apply(label_segment, axis=1)

        segmentation_metrics["rfm_summary"] = {
            "total_customers_segmented": int(len(df_rfm)),
            "average_recency": float(df_rfm["recency"].mean()),
            "average_frequency": float(df_rfm["frequency"].mean()),
            "average_monetary": float(df_rfm["monetary"].mean())
        }

        segment_summary = (
            df_rfm.groupby("segment", dropna=False)
            .agg(
                customer_count=("customer_id", "count"),
                avg_recency=("recency", "mean"),
                avg_frequency=("frequency", "mean"),
                avg_monetary=("monetary", "mean"),
                total_revenue=("monetary", "sum")
            )
            .reset_index()
            .sort_values("total_revenue", ascending=False)
        )

        segmentation_metrics["segment_distribution"] = [
            {
                "segment": row["segment"],
                "customer_count": int(row["customer_count"]),
                "avg_recency": float(row["avg_recency"]),
                "avg_frequency": float(row["avg_frequency"]),
                "avg_monetary": float(row["avg_monetary"]),
                "total_revenue": float(row["total_revenue"])
            }
            for _, row in segment_summary.iterrows()
        ]

        top_segment_customers = (
            df_rfm.sort_values("monetary", ascending=False)
            .groupby("segment", as_index=False)
            .head(5)
            .sort_values(["segment", "monetary"], ascending=[True, False])
        )

        segmentation_metrics["top_segment_customers"] = [
            {
                "customer_id": str(row["customer_id"]),
                "segment": row["segment"],
                "recency": float(row["recency"]),
                "frequency": int(row["frequency"]),
                "monetary": float(row["monetary"]),
                "rfm_score": row["rfm_score"]
            }
            for _, row in top_segment_customers.iterrows()
        ]

        self.results["segmentation"] = segmentation_metrics
        print("[SUCCESS] Customer segmentation completed!")
        return segmentation_metrics

    # ---------------------------------------------------------------------
    # SAVE RESULTS
    # ---------------------------------------------------------------------

    def _json_converter(self, obj):
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return str(obj)

    def save_results_to_json(self, output_file=JSON_FILE):
        print("[INFO] Saving EDA results to JSON...")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=4, default=self._json_converter, ensure_ascii=False)
        print(f"[SUCCESS] Results saved to: {output_file}")

    def export_csvs(self):
        print("[INFO] Exporting key result tables to CSV...")
        exported = 0
        for section_name, section_data in self.results.items():
            if not isinstance(section_data, dict):
                continue
            for key, value in section_data.items():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    df = pd.DataFrame(value)
                    csv_path = os.path.join(DATA_DIR, f"{section_name}__{key}.csv")
                    df.to_csv(csv_path, index=False)
                    exported += 1
        print(f"[SUCCESS] Exported {exported} CSV files")

    def create_summary_report(self, summary_file=SUMMARY_FILE):
        print("[INFO] Writing summary report...")
        lines = []
        lines.append("=" * 100)
        lines.append("UCI ONLINE RETAIL II - MAXIMUM EDA SUMMARY")
        lines.append("=" * 100)
        lines.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Database: {self.db_config['database']}")
        lines.append(f"Schema.Table: {self.schema_name}.{self.table_name}")
        lines.append("")

        dq = self.results.get("data_quality", {})
        tx = self.results.get("transaction_analysis", {})
        ca = self.results.get("customer_analysis", {})
        pa = self.results.get("product_analysis", {})
        ta = self.results.get("time_analysis", {})
        ga = self.results.get("geographic_analysis", {})
        ra = self.results.get("revenue_analysis", {})
        sg = self.results.get("segmentation", {})

        if dq:
            lines.append("[1] DATA QUALITY")
            dup = dq.get("duplicate_analysis", {})
            an = dq.get("anomaly_checks", {})
            lines.append(f"- Duplicate rows: {dup.get('duplicate_count', 'N/A')} ({dup.get('duplicate_percentage', 'N/A')}%)")
            lines.append(f"- Missing customer IDs: {an.get('missing_customer_ids', 'N/A')}")
            lines.append(f"- Missing descriptions: {an.get('missing_descriptions', 'N/A')}")
            lines.append(f"- Cancelled invoice rows: {an.get('cancelled_invoice_rows', 'N/A')}")
            lines.append("")

        if tx:
            lines.append("[2] TRANSACTION ANALYSIS")
            inv = tx.get("invoice_statistics", {})
            size = tx.get("size_statistics", {})
            lines.append(f"- Total invoices: {inv.get('total_invoices', 'N/A')}")
            lines.append(f"- Total transactions: {inv.get('total_transactions', 'N/A')}")
            lines.append(f"- Avg items/invoice: {inv.get('average_items_per_invoice', 'N/A')}")
            lines.append(f"- Avg invoice value: {size.get('avg_value', 'N/A')}")
            lines.append("")

        if ca:
            lines.append("[3] CUSTOMER ANALYSIS")
            cs = ca.get("customer_statistics", {})
            cvs = ca.get("customer_value_summary", {})
            lines.append(f"- Total customers: {cs.get('total_customers', 'N/A')}")
            lines.append(f"- Missing customer ID rows: {cs.get('missing_customer_ids', 'N/A')}")
            lines.append(f"- Average customer revenue: {cvs.get('average_customer_revenue', 'N/A')}")
            lines.append(f"- Median customer revenue: {cvs.get('median_customer_revenue', 'N/A')}")
            if ca.get("top_customers"):
                top = ca["top_customers"][0]
                lines.append(f"- Top customer: {top.get('customer_id')} with revenue {round(top.get('total_spent', 0), 2)}")
            lines.append("")

        if pa:
            lines.append("[4] PRODUCT ANALYSIS")
            ps = pa.get("product_statistics", {})
            lines.append(f"- Total products: {ps.get('total_products', 'N/A')}")
            lines.append(f"- Unique descriptions: {ps.get('unique_descriptions', 'N/A')}")
            if pa.get("top_products"):
                top = pa["top_products"][0]
                lines.append(f"- Top product by revenue: {top.get('stockcode')} | {top.get('description')} | revenue={round(top.get('total_revenue', 0), 2)}")
            lines.append("")

        if ta:
            lines.append("[5] TIME ANALYSIS")
            tr = ta.get("time_range", {})
            lines.append(f"- Earliest transaction: {tr.get('earliest_date', 'N/A')}")
            lines.append(f"- Latest transaction: {tr.get('latest_date', 'N/A')}")
            lines.append(f"- Covered days: {tr.get('total_days', 'N/A')}")
            if ta.get("monthly_trends"):
                monthly_sorted = sorted(ta["monthly_trends"], key=lambda x: (x["year"], x["month"]))
                best_month = max(monthly_sorted, key=lambda x: x["monthly_revenue"])
                lines.append(f"- Best month: {best_month['year']}-{best_month['month']:02d} revenue={round(best_month['monthly_revenue'], 2)}")
            lines.append("")

        if ga:
            lines.append("[6] GEOGRAPHIC ANALYSIS")
            if ga.get("top_countries"):
                top_country = ga["top_countries"][0]
                lines.append(f"- Top country by revenue: {top_country.get('country')} revenue={round(top_country.get('total_revenue', 0), 2)}")
            conc = ga.get("concentration_analysis", {})
            if conc:
                lines.append(f"- UK revenue share: {conc.get('uk_revenue_share', 'N/A')}%")
                lines.append(f"- UK customer share: {conc.get('uk_customer_share', 'N/A')}%")
            lines.append("")

        if ra:
            lines.append("[7] REVENUE ANALYSIS")
            overall = ra.get("overall_statistics", {})
            lines.append(f"- Total revenue: {overall.get('total_revenue', 'N/A')}")
            lines.append(f"- Average transaction value: {overall.get('average_transaction_value', 'N/A')}")
            lines.append(f"- Maximum transaction value: {overall.get('maximum_transaction_value', 'N/A')}")
            conc = ra.get("revenue_concentration", {})
            if conc:
                lines.append(f"- Top 10% customer revenue share: {conc.get('top_10pct_customer_revenue_share', 'N/A')}%")
                lines.append(f"- Top 20% customer revenue share: {conc.get('top_20pct_customer_revenue_share', 'N/A')}%")
            lines.append("")

        if sg:
            lines.append("[8] CUSTOMER SEGMENTATION")
            rfm = sg.get("rfm_summary", {})
            lines.append(f"- Total customers segmented: {rfm.get('total_customers_segmented', 'N/A')}")
            lines.append(f"- Average recency: {rfm.get('average_recency', 'N/A')}")
            lines.append(f"- Average frequency: {rfm.get('average_frequency', 'N/A')}")
            lines.append(f"- Average monetary: {rfm.get('average_monetary', 'N/A')}")
            if sg.get("segment_distribution"):
                top_seg = sg["segment_distribution"][0]
                lines.append(f"- Highest-revenue segment: {top_seg.get('segment')} revenue={round(top_seg.get('total_revenue', 0), 2)}")
            lines.append("")

        lines.append("=" * 100)

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"[SUCCESS] Summary report written to: {summary_file}")

    # ---------------------------------------------------------------------
    # PLOTTING
    # ---------------------------------------------------------------------

    def _save_plot(self, file_path, title):
        plt.title(title, fontsize=13, fontweight="bold")
        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"[PLOT] Saved: {file_path}")

    def generate_plots(self):
        print("\n" + "=" * 80)
        print("GENERATING PLOTS")
        print("=" * 80)

        # 1. Data quality - null percentages
        dq = self.results.get("data_quality", {})
        null_analysis = dq.get("null_analysis", {})
        if null_analysis:
            df = (
                pd.DataFrame.from_dict(null_analysis, orient="index")
                .reset_index()
                .rename(columns={"index": "column"})
                .sort_values("null_percentage", ascending=False)
            )
            plt.figure(figsize=(10, 6))
            sns.barplot(data=df, x="null_percentage", y="column")
            plt.xlabel("Null / Empty Percentage")
            plt.ylabel("Column")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["data_quality"], "null_percentages.png"),
                "Null / Empty Values by Column"
            )

        range_analysis = dq.get("range_analysis", {})
        if range_analysis:
            df = pd.DataFrame(range_analysis).T.reset_index().rename(columns={"index": "metric"})
            metrics_to_plot = ["negative_count", "zero_count"]
            melted = df.melt(id_vars="metric", value_vars=metrics_to_plot, var_name="count_type", value_name="count")
            plt.figure(figsize=(8, 5))
            sns.barplot(data=melted, x="metric", y="count", hue="count_type")
            plt.xlabel("Numeric Column")
            plt.ylabel("Count")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["data_quality"], "numeric_anomalies.png"),
                "Numeric Anomalies (Negative / Zero Counts)"
            )

        # 2. Transactions
        tx = self.results.get("transaction_analysis", {})
        invoice_sizes = tx.get("invoice_sizes", [])
        if invoice_sizes:
            df = pd.DataFrame(invoice_sizes)
            plt.figure(figsize=(9, 5))
            sns.histplot(df["item_count"], bins=40, kde=True)
            plt.xlabel("Items per Invoice")
            plt.ylabel("Frequency")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["transaction_analysis"], "invoice_size_distribution.png"),
                "Invoice Size Distribution"
            )

            top = df.nlargest(15, "total_value").copy()
            plt.figure(figsize=(12, 6))
            sns.barplot(data=top, x="invoice", y="total_value")
            plt.xticks(rotation=45, ha="right")
            plt.xlabel("Invoice")
            plt.ylabel("Total Value")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["transaction_analysis"], "top_invoice_values.png"),
                "Top 15 Invoices by Value"
            )

        # 3. Customers
        ca = self.results.get("customer_analysis", {})
        top_customers = ca.get("top_customers", [])
        if top_customers:
            df = pd.DataFrame(top_customers)
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x="customer_id", y="total_spent")
            plt.xticks(rotation=45, ha="right")
            plt.xlabel("Customer ID")
            plt.ylabel("Total Spent")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["customer_analysis"], "top_customers_by_revenue.png"),
                "Top 20 Customers by Revenue"
            )

        purchase_frequency = ca.get("purchase_frequency", [])
        if purchase_frequency:
            df = pd.DataFrame(purchase_frequency)
            plt.figure(figsize=(10, 5))
            sns.lineplot(data=df, x="invoice_count", y="customer_count", marker="o")
            plt.xlabel("Invoice Count")
            plt.ylabel("Number of Customers")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["customer_analysis"], "purchase_frequency.png"),
                "Customer Purchase Frequency"
            )

        # 4. Products
        pa = self.results.get("product_analysis", {})
        top_products = pa.get("top_products", [])
        if top_products:
            df = pd.DataFrame(top_products)
            plt.figure(figsize=(12, 7))
            sns.barplot(data=df, x="total_revenue", y="description")
            plt.xlabel("Total Revenue")
            plt.ylabel("Product")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["product_analysis"], "top_products_by_revenue.png"),
                "Top 20 Products by Revenue"
            )

        categories = pa.get("product_categories", [])
        if categories:
            df = pd.DataFrame(categories)
            plt.figure(figsize=(10, 6))
            sns.barplot(data=df, x="total_revenue", y="category")
            plt.xlabel("Total Revenue")
            plt.ylabel("Category Prefix")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["product_analysis"], "product_categories.png"),
                "Top Product Categories by Revenue"
            )

        # 5. Time analysis
        ta = self.results.get("time_analysis", {})
        daily = ta.get("daily_patterns", [])
        if daily:
            df = pd.DataFrame(daily)
            df["date"] = pd.to_datetime(df["date"])
            plt.figure(figsize=(14, 6))
            sns.lineplot(data=df, x="date", y="daily_revenue")
            plt.xlabel("Date")
            plt.ylabel("Daily Revenue")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["time_analysis"], "daily_revenue_trend.png"),
                "Daily Revenue Trend"
            )

        monthly = ta.get("monthly_trends", [])
        if monthly:
            df = pd.DataFrame(monthly)
            df["period"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
            plt.figure(figsize=(12, 6))
            sns.lineplot(data=df, x="period", y="monthly_revenue", marker="o")
            plt.xlabel("Month")
            plt.ylabel("Monthly Revenue")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["time_analysis"], "monthly_revenue_trend.png"),
                "Monthly Revenue Trend"
            )

        hourly = ta.get("hourly_patterns", [])
        if hourly:
            df = pd.DataFrame(hourly)
            plt.figure(figsize=(10, 5))
            sns.barplot(data=df, x="hour", y="transaction_count")
            plt.xlabel("Hour of Day")
            plt.ylabel("Transaction Count")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["time_analysis"], "hourly_transactions.png"),
                "Hourly Transaction Pattern"
            )

        dow = ta.get("day_of_week_patterns", [])
        if dow:
            df = pd.DataFrame(dow)
            plt.figure(figsize=(10, 5))
            sns.barplot(data=df, x="day_name", y="daily_revenue")
            plt.xticks(rotation=30, ha="right")
            plt.xlabel("Day of Week")
            plt.ylabel("Revenue")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["time_analysis"], "dow_revenue.png"),
                "Revenue by Day of Week"
            )

        # 6. Geography
        ga = self.results.get("geographic_analysis", {})
        countries = ga.get("top_countries", [])
        if countries:
            df = pd.DataFrame(countries)
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x="total_revenue", y="country")
            plt.xlabel("Total Revenue")
            plt.ylabel("Country")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["geographic_analysis"], "top_countries_revenue.png"),
                "Top 10 Countries by Revenue"
            )

        # 7. Revenue
        ra = self.results.get("revenue_analysis", {})
        segments = ra.get("customer_revenue_segments", [])
        if segments:
            df = pd.DataFrame(segments)
            plt.figure(figsize=(10, 6))
            sns.barplot(data=df, x="revenue_segment", y="segment_revenue")
            plt.xticks(rotation=25, ha="right")
            plt.xlabel("Revenue Segment")
            plt.ylabel("Segment Revenue")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["revenue_analysis"], "revenue_segments.png"),
                "Revenue by Customer Segment"
            )

        top_invoices = ra.get("top_invoices", [])
        if top_invoices:
            df = pd.DataFrame(top_invoices)
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x="invoice", y="invoice_value")
            plt.xticks(rotation=45, ha="right")
            plt.xlabel("Invoice")
            plt.ylabel("Invoice Value")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["revenue_analysis"], "top_invoices.png"),
                "Top 20 Invoices by Revenue"
            )

        # 8. Segmentation
        sg = self.results.get("segmentation", {})
        segment_dist = sg.get("segment_distribution", [])
        if segment_dist:
            df = pd.DataFrame(segment_dist)
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x="segment", y="customer_count")
            plt.xticks(rotation=30, ha="right")
            plt.xlabel("Segment")
            plt.ylabel("Customer Count")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["segmentation"], "segment_distribution.png"),
                "Customer Segment Distribution"
            )

            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x="segment", y="total_revenue")
            plt.xticks(rotation=30, ha="right")
            plt.xlabel("Segment")
            plt.ylabel("Total Revenue")
            self._save_plot(
                os.path.join(PLOT_SUBDIRS["segmentation"], "segment_revenue.png"),
                "Revenue by Customer Segment (RFM)"
            )

        print("[SUCCESS] Plot generation completed!")

    # ---------------------------------------------------------------------
    # RUN ALL
    # ---------------------------------------------------------------------

    def run_full_eda(self):
        print("\n" + "=" * 100)
        print("STARTING MAXIMUM EDA")
        print("=" * 100)

        self.analyze_data_quality()
        self.analyze_transactions()
        self.analyze_customers()
        self.analyze_products()
        self.analyze_time_series()
        self.analyze_geography()
        self.analyze_revenue()
        self.analyze_segmentation()

        self.save_results_to_json()
        self.export_csvs()
        self.create_summary_report()
        self.generate_plots()

        print("\n" + "=" * 100)
        print("EDA COMPLETED SUCCESSFULLY")
        print("=" * 100)
        print(f"[INFO] Output directory: {OUTPUT_DIR}")
        print(f"[INFO] Summary file: {SUMMARY_FILE}")
        print(f"[INFO] JSON file: {JSON_FILE}")
        print(f"[INFO] Plot directory: {PLOT_DIR}")


def main():
    print("\n" + "=" * 100)
    print("UCI ONLINE RETAIL II - MAXIMUM EDA SCRIPT")
    print("=" * 100)
    print(f"Target database: {DATABASE_CONFIG['database']}")
    print(f"Target table: {RAW_DATA_SCHEMA}.{TABLE_NAME}")

    analyzer = OnlineRetailEDA(DATABASE_CONFIG, RAW_DATA_SCHEMA, TABLE_NAME)

    if not analyzer.connect():
        print("[FATAL] Cannot continue without a database connection")
        sys.exit(1)

    try:
        analyzer.run_full_eda()
    except KeyboardInterrupt:
        print("\n[WARNING] Execution interrupted by user")
    except Exception as e:
        print(f"[FATAL] Unexpected error during EDA execution: {e}")
        raise
    finally:
        analyzer.disconnect()


if __name__ == "__main__":
    main()
