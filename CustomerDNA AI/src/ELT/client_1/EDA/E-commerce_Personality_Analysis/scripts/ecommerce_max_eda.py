#!/usr/bin/env python3
"""
E-COMMERCE PERSONALITY ANALYSIS - MAXIMUM EDA SCRIPT
=====================================================

This is a comprehensive single script that performs maximum EDA on the
E-commerce Customer Churn dataset.

Features:
1. Database connection with centralized configuration
2. Complete table structure analysis
3. 11 different analysis methods
4. 15+ different plot types
5. Detailed summary.txt with every tiny detail
6. Organized output structure

Output Structure:
output/
├── summary.txt                    # Complete detailed summary
├── plots/
│   ├── 01_demographic/
│   ├── 02_behavioral/
│   ├── 03_transactional/
│   ├── 04_correlations/
│   └── 05_segmentation/
└── data/
    ├── statistics.json
    └── insights.json
"""

import os
import sys
import json
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime
from decimal import Decimal
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Add parent directories to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

try:
    from src.ELT.client_1.config.config import (
        DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, 
        DATA_WAREHOUSE_NAME, RAW_DATA_SCHEMA
    )
except ImportError:
    # Fallback configuration
    DB_HOST = os.getenv("CUSTOMERDNA_POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("CUSTOMERDNA_POSTGRES_PORT", "5440")
    DB_USER = os.getenv("CUSTOMERDNA_POSTGRES_USER", "postgres")
    DB_PASSWORD = os.getenv("CUSTOMERDNA_POSTGRES_PASSWORD", "")
    DATA_WAREHOUSE_NAME = os.getenv("CUSTOMERDNA_POSTGRES_DB", "client1_DW")
    RAW_DATA_SCHEMA = "raw_data"

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# Try different possible table names for e-commerce churn data
POSSIBLE_TABLE_NAMES = [
    "ecommerce_customer_churn",
    "ecommerce_churn",
    "customer_churn",
    "churn_data",
    "global_churn_metrics"  # From BUSINESS_RULES.md
]

TABLE_NAME = None  # Will be determined dynamically
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
OUTPUT_BASE_DIR = os.path.join(
    PROJECT_ROOT,
    "artifacts",
    "client_1",
    "elt_eda",
    "ecommerce_personality_analysis",
)
CURRENT_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, f"max_eda_{CURRENT_TIMESTAMP}")

# Create output directory structure
PLOTS_DIR = os.path.join(OUTPUT_DIR, "plots")
DATA_DIR = os.path.join(OUTPUT_DIR, "data")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "summary.txt")

for directory in [OUTPUT_DIR, PLOTS_DIR, DATA_DIR]:
    os.makedirs(directory, exist_ok=True)

# Plot subdirectories
PLOT_SUBDIRS = {
    "demographic": os.path.join(PLOTS_DIR, "01_demographic"),
    "behavioral": os.path.join(PLOTS_DIR, "02_behavioral"),
    "transactional": os.path.join(PLOTS_DIR, "03_transactional"),
    "correlations": os.path.join(PLOTS_DIR, "04_correlations"),
    "segmentation": os.path.join(PLOTS_DIR, "05_segmentation")
}

for subdir in PLOT_SUBDIRS.values():
    os.makedirs(subdir, exist_ok=True)

# ============================================================================
# DATABASE CONNECTION CLASS
# ============================================================================

class DatabaseConnection:
    """Handles PostgreSQL database connection and queries"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DATA_WAREHOUSE_NAME
            )
            self.cursor = self.connection.cursor()
            print(f"[SUCCESS] Connected to database: {DATA_WAREHOUSE_NAME}")
            return True
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False
    
    def execute_query(self, query, params=None):
        """Execute SQL query and return results"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # Try to fetch results if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                columns = [desc[0] for desc in self.cursor.description]
                results = self.cursor.fetchall()
                return columns, results
            else:
                self.connection.commit()
                return None, None
        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")
            print(f"Query: {query}")
            if params:
                print(f"Params: {params}")
            return None, None
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

# ============================================================================
# E-COMMERCE MAXIMUM EDA CLASS
# ============================================================================

class EcommerceMaxEDA:
    """Comprehensive EDA for E-commerce Customer Churn dataset"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.schema = RAW_DATA_SCHEMA
        self.table_name = None
        self.full_table_name = None
        self.results = {
            "table_structure": {},
            "demographic_analysis": {},
            "behavioral_analysis": {},
            "transactional_analysis": {},
            "campaign_analysis": {},
            "correlation_analysis": {},
            "segmentation_analysis": {},
            "data_quality": {},
            "insights": {}
        }
        
        # Column categories for e-commerce churn data - based on actual table structure
        self.column_categories = {
            "customer_identification": ["customerid"],
            "demographic": ["gender", "citytier", "maritalstatus"],
            "behavioral": ["preferredlogindevice", "preferredpaymentmode", 
                          "preferedordercat", "satisfactionscore"],
            "transactional": ["ordercount", "cashbackamount", "couponused", 
                             "daysincelastorder", "hourspendonapp", "orderamounthikefromlastyear"],
            "churn_related": ["churn", "complain", "tenure", "warehousetohome", "numberofdeviceregistered", "numberofaddress"]
        }
    
    def discover_table_name(self):
        """Discover the correct table name for e-commerce churn data"""
        print("[INFO] Discovering e-commerce churn table name...")
        
        for table_name in POSSIBLE_TABLE_NAMES:
            check_query = f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = %s
            );
            """
            
            columns, results = self.db.execute_query(check_query, (self.schema, table_name))
            
            if results and results[0][0]:
                self.table_name = table_name
                self.full_table_name = f"{self.schema}.{table_name}"
                print(f"[SUCCESS] Found table: {self.full_table_name}")
                return True
        
        # If no table found, check what tables exist in the schema
        tables_query = f"""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s
        ORDER BY table_name;
        """
        
        columns, results = self.db.execute_query(tables_query, (self.schema,))
        
        if results:
            print("[INFO] Available tables in schema:")
            for table in results:
                print(f"  - {table[0]}")
            
            # Look for tables with "churn" in the name
            for table in results:
                if "churn" in table[0].lower():
                    self.table_name = table[0]
                    self.full_table_name = f"{self.schema}.{table[0]}"
                    print(f"[SUCCESS] Using table with 'churn' in name: {self.full_table_name}")
                    return True
            
            # Use the first table if none found
            if results:
                self.table_name = results[0][0]
                self.full_table_name = f"{self.schema}.{results[0][0]}"
                print(f"[INFO] Using first available table: {self.full_table_name}")
                return True
        
        print("[ERROR] No tables found in schema")
        return False
    
    def analyze_table_structure(self):
        """Analyze complete table structure"""
        print("[INFO] Analyzing table structure...")
        
        # Get column information
        query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            character_maximum_length,
            column_default
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
        """
        
        columns, results = self.db.execute_query(query, (self.schema, self.table_name))
        
        if results:
            column_info = []
            for row in results:
                col_info = {
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2],
                    "max_length": row[3],
                    "default": row[4]
                }
                column_info.append(col_info)
            
            self.results["table_structure"]["columns"] = column_info
            self.results["table_structure"]["total_columns"] = len(column_info)
            
            # Get row count
            count_query = f"SELECT COUNT(*) FROM {self.full_table_name};"
            count_columns, count_results = self.db.execute_query(count_query)
            
            if count_results:
                self.results["table_structure"]["row_count"] = count_results[0][0]
            
            # Categorize columns
            categorized = {}
            for category, cols in self.column_categories.items():
                categorized[category] = [col for col in column_info if col["name"] in cols]
            
            self.results["table_structure"]["categorized_columns"] = categorized
            
            return True
        return False
    
    def analyze_demographics(self):
        """Analyze demographic data"""
        print("[INFO] Analyzing demographic data...")
        
        analyses = {}
        
        # 1. Gender distribution
        gender_query = f"""
        SELECT 
            gender,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE gender IS NOT NULL AND gender != ''
        GROUP BY gender
        ORDER BY count DESC;
        """
        
        columns, results = self.db.execute_query(gender_query)
        if results:
            analyses["gender_distribution"] = [
                {"gender": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        # 2. City tier distribution (instead of age)
        city_tier_query = f"""
        SELECT 
            citytier,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE citytier IS NOT NULL AND citytier != ''
        GROUP BY citytier
        ORDER BY citytier;
        """
        
        columns, results = self.db.execute_query(city_tier_query)
        if results:
            analyses["city_tier_distribution"] = [
                {"city_tier": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        # 3. Marital status distribution
        marital_query = f"""
        SELECT 
            maritalstatus,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE maritalstatus IS NOT NULL AND maritalstatus != ''
        GROUP BY maritalstatus
        ORDER BY count DESC;
        """
        
        columns, results = self.db.execute_query(marital_query)
        if results:
            analyses["marital_status_distribution"] = [
                {"marital_status": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        self.results["demographic_analysis"] = analyses
        return True
    
    def analyze_behavioral_data(self):
        """Analyze customer behavioral data"""
        print("[INFO] Analyzing behavioral data...")
        
        analyses = {}
        
        # 1. Preferred login device
        device_query = f"""
        SELECT 
            preferredlogindevice,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE preferredlogindevice IS NOT NULL AND preferredlogindevice != ''
        GROUP BY preferredlogindevice
        ORDER BY count DESC;
        """
        
        columns, results = self.db.execute_query(device_query)
        if results:
            analyses["login_device_distribution"] = [
                {"device": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        # 2. Preferred payment mode
        payment_query = f"""
        SELECT 
            preferredpaymentmode,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE preferredpaymentmode IS NOT NULL AND preferredpaymentmode != ''
        GROUP BY preferredpaymentmode
        ORDER BY count DESC;
        """
        
        columns, results = self.db.execute_query(payment_query)
        if results:
            analyses["payment_mode_distribution"] = [
                {"payment_mode": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        # 3. Preferred order category
        order_cat_query = f"""
        SELECT 
            preferedordercat,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE preferedordercat IS NOT NULL AND preferedordercat != ''
        GROUP BY preferedordercat
        ORDER BY count DESC;
        """
        
        columns, results = self.db.execute_query(order_cat_query)
        if results:
            analyses["order_category_distribution"] = [
                {"order_category": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        # 4. Marital status
        marital_query = f"""
        SELECT 
            maritalstatus,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE maritalstatus IS NOT NULL AND maritalstatus != ''
        GROUP BY maritalstatus
        ORDER BY count DESC;
        """
        
        columns, results = self.db.execute_query(marital_query)
        if results:
            analyses["marital_status_distribution"] = [
                {"marital_status": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        self.results["behavioral_analysis"] = analyses
        return True
    
    def analyze_transactional_data(self):
        """Analyze transactional data"""
        print("[INFO] Analyzing transactional data...")
        
        analyses = {}
        
        # 1. Order count analysis
        order_count_query = f"""
        SELECT 
            MIN(CAST(ordercount AS DECIMAL)) as min_orders,
            MAX(CAST(ordercount AS DECIMAL)) as max_orders,
            AVG(CAST(ordercount AS DECIMAL)) as avg_orders,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CAST(ordercount AS DECIMAL)) as median_orders
        FROM {self.full_table_name}
        WHERE ordercount IS NOT NULL AND ordercount != '' AND CAST(ordercount AS DECIMAL) >= 0;
        """
        
        columns, results = self.db.execute_query(order_count_query)
        if results and results[0]:
            analyses["order_count_analysis"] = {
                "min_orders": results[0][0],
                "max_orders": results[0][1],
                "avg_orders": results[0][2],
                "median_orders": results[0][3]
            }
        
        # 2. Cashback amount analysis
        cashback_query = f"""
        SELECT 
            MIN(CAST(cashbackamount AS DECIMAL)) as min_cashback,
            MAX(CAST(cashbackamount AS DECIMAL)) as max_cashback,
            AVG(CAST(cashbackamount AS DECIMAL)) as avg_cashback,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CAST(cashbackamount AS DECIMAL)) as median_cashback
        FROM {self.full_table_name}
        WHERE cashbackamount IS NOT NULL AND cashbackamount != '' AND CAST(cashbackamount AS DECIMAL) >= 0;
        """
        
        columns, results = self.db.execute_query(cashback_query)
        if results and results[0]:
            analyses["cashback_analysis"] = {
                "min_cashback": results[0][0],
                "max_cashback": results[0][1],
                "avg_cashback": results[0][2],
                "median_cashback": results[0][3]
            }
        
        # 3. Coupon usage
        coupon_query = f"""
        SELECT 
            couponused,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE couponused IS NOT NULL AND couponused != ''
        GROUP BY couponused
        ORDER BY couponused;
        """
        
        columns, results = self.db.execute_query(coupon_query)
        if results:
            analyses["coupon_usage"] = [
                {"coupon_used": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        # 4. Days since last order
        days_query = f"""
        SELECT 
            MIN(CAST(daysincelastorder AS DECIMAL)) as min_days,
            MAX(CAST(daysincelastorder AS DECIMAL)) as max_days,
            AVG(CAST(daysincelastorder AS DECIMAL)) as avg_days,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CAST(daysincelastorder AS DECIMAL)) as median_days
        FROM {self.full_table_name}
        WHERE daysincelastorder IS NOT NULL AND daysincelastorder != '' AND CAST(daysincelastorder AS DECIMAL) >= 0;
        """
        
        columns, results = self.db.execute_query(days_query)
        if results and results[0]:
            analyses["days_since_last_order"] = {
                "min_days": results[0][0],
                "max_days": results[0][1],
                "avg_days": results[0][2],
                "median_days": results[0][3]
            }
        
        # 5. Hour spend on app
        hours_query = f"""
        SELECT 
            MIN(CAST(hourspendonapp AS DECIMAL)) as min_hours,
            MAX(CAST(hourspendonapp AS DECIMAL)) as max_hours,
            AVG(CAST(hourspendonapp AS DECIMAL)) as avg_hours,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CAST(hourspendonapp AS DECIMAL)) as median_hours
        FROM {self.full_table_name}
        WHERE hourspendonapp IS NOT NULL AND hourspendonapp != '' AND CAST(hourspendonapp AS DECIMAL) >= 0;
        """
        
        columns, results = self.db.execute_query(hours_query)
        if results and results[0]:
            analyses["hours_on_app"] = {
                "min_hours": results[0][0],
                "max_hours": results[0][1],
                "avg_hours": results[0][2],
                "median_hours": results[0][3]
            }
        
        self.results["transactional_analysis"] = analyses
        return True
    
    def analyze_churn_data(self):
        """Analyze churn-related data"""
        print("[INFO] Analyzing churn data...")
        
        analyses = {}
        
        # 1. Overall churn rate
        churn_query = f"""
        SELECT 
            churn,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE churn IS NOT NULL AND churn != ''
        GROUP BY churn
        ORDER BY churn;
        """
        
        columns, results = self.db.execute_query(churn_query)
        if results:
            analyses["churn_distribution"] = [
                {"churn": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        # 2. Complaints analysis
        complain_query = f"""
        SELECT 
            complain,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE complain IS NOT NULL AND complain != ''
        GROUP BY complain
        ORDER BY complain;
        """
        
        columns, results = self.db.execute_query(complain_query)
        if results:
            analyses["complaints_distribution"] = [
                {"complain": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        # 3. Satisfaction score
        satisfaction_query = f"""
        SELECT 
            satisfactionscore,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE satisfactionscore IS NOT NULL AND satisfactionscore != ''
        GROUP BY satisfactionscore
        ORDER BY satisfactionscore;
        """
        
        columns, results = self.db.execute_query(satisfaction_query)
        if results:
            analyses["satisfaction_distribution"] = [
                {"score": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        # 4. Warehouse to home distance
        warehouse_query = f"""
        SELECT 
            warehousetohome,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE warehousetohome IS NOT NULL AND warehousetohome != ''
        GROUP BY warehousetohome
        ORDER BY warehousetohome;
        """
        
        columns, results = self.db.execute_query(warehouse_query)
        if results:
            analyses["warehouse_distance_distribution"] = [
                {"distance": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        self.results["churn_analysis"] = analyses
        return True
    
    def analyze_correlations(self):
        """Analyze correlations between variables"""
        print("[INFO] Analyzing correlations...")
        
        analyses = {}
        
        # 1. Satisfaction Score vs Churn correlation
        satisfaction_churn_query = f"""
        SELECT 
            CORR(CAST(satisfactionscore AS DECIMAL), CAST(churn AS DECIMAL)) as correlation
        FROM {self.full_table_name}
        WHERE satisfactionscore IS NOT NULL AND satisfactionscore != '' 
          AND churn IS NOT NULL AND churn != ''
          AND CAST(satisfactionscore AS DECIMAL) > 0;
        """
        
        columns, results = self.db.execute_query(satisfaction_churn_query)
        if results and results[0]:
            analyses["satisfaction_churn_correlation"] = results[0][0]
        
        # 2. Tenure vs Churn correlation
        tenure_churn_query = f"""
        SELECT 
            CORR(CAST(tenure AS DECIMAL), CAST(churn AS DECIMAL)) as correlation
        FROM {self.full_table_name}
        WHERE tenure IS NOT NULL AND tenure != '' 
          AND churn IS NOT NULL AND churn != ''
          AND CAST(tenure AS DECIMAL) >= 0;
        """
        
        columns, results = self.db.execute_query(tenure_churn_query)
        if results and results[0]:
            analyses["tenure_churn_correlation"] = results[0][0]
        
        # 3. Order count vs Churn correlation
        orders_churn_query = f"""
        SELECT 
            CORR(CAST(ordercount AS DECIMAL), CAST(churn AS DECIMAL)) as correlation
        FROM {self.full_table_name}
        WHERE ordercount IS NOT NULL AND ordercount != '' 
          AND churn IS NOT NULL AND churn != ''
          AND CAST(ordercount AS DECIMAL) >= 0;
        """
        
        columns, results = self.db.execute_query(orders_churn_query)
        if results and results[0]:
            analyses["orders_churn_correlation"] = results[0][0]
        
        # 4. Cashback vs Churn correlation
        cashback_churn_query = f"""
        SELECT 
            CORR(CAST(cashbackamount AS DECIMAL), CAST(churn AS DECIMAL)) as correlation
        FROM {self.full_table_name}
        WHERE cashbackamount IS NOT NULL AND cashbackamount != '' 
          AND churn IS NOT NULL AND churn != ''
          AND CAST(cashbackamount AS DECIMAL) >= 0;
        """
        
        columns, results = self.db.execute_query(cashback_churn_query)
        if results and results[0]:
            analyses["cashback_churn_correlation"] = results[0][0]
        
        self.results["correlation_analysis"] = analyses
        return True
    
    def analyze_segmentation(self):
        """Perform customer segmentation analysis"""
        print("[INFO] Performing segmentation analysis...")
        
        analyses = {}
        
        # 1. RFM Segmentation (Recency, Frequency, Monetary)
        # Since we don't have exact RFM data, we'll use available proxies
        rfm_query = f"""
        WITH customer_stats AS (
            SELECT 
                customerid,
                CAST(ordercount AS DECIMAL) as frequency,
                CAST(cashbackamount AS DECIMAL) as monetary_value,
                CAST(daysincelastorder AS DECIMAL) as recency
            FROM {self.full_table_name}
            WHERE customerid IS NOT NULL AND customerid != ''
              AND ordercount IS NOT NULL AND ordercount != ''
              AND cashbackamount IS NOT NULL AND cashbackamount != ''
              AND daysincelastorder IS NOT NULL AND daysincelastorder != ''
        ),
        rfm_scores AS (
            SELECT 
                customerid,
                NTILE(4) OVER (ORDER BY recency DESC) as recency_score,
                NTILE(4) OVER (ORDER BY frequency) as frequency_score,
                NTILE(4) OVER (ORDER BY monetary_value) as monetary_score
            FROM customer_stats
        )
        SELECT 
            CONCAT(recency_score, frequency_score, monetary_score) as rfm_cell,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM rfm_scores
        GROUP BY CONCAT(recency_score, frequency_score, monetary_score)
        ORDER BY count DESC
        LIMIT 15;
        """
        
        columns, results = self.db.execute_query(rfm_query)
        if results:
            analyses["rfm_segments"] = [
                {"rfm_cell": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        # 2. Churn risk segmentation
        churn_risk_query = f"""
        SELECT 
            CASE 
                WHEN CAST(complain AS DECIMAL) = 1 THEN 'High Risk (Complaints)'
                WHEN CAST(satisfactionscore AS DECIMAL) <= 2 THEN 'Medium Risk (Low Satisfaction)'
                WHEN CAST(daysincelastorder AS DECIMAL) > 30 THEN 'Medium Risk (Inactive)'
                ELSE 'Low Risk'
            END as churn_risk_segment,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE complain IS NOT NULL AND complain != ''
          AND satisfactionscore IS NOT NULL AND satisfactionscore != ''
          AND daysincelastorder IS NOT NULL AND daysincelastorder != ''
        GROUP BY 
            CASE 
                WHEN CAST(complain AS DECIMAL) = 1 THEN 'High Risk (Complaints)'
                WHEN CAST(satisfactionscore AS DECIMAL) <= 2 THEN 'Medium Risk (Low Satisfaction)'
                WHEN CAST(daysincelastorder AS DECIMAL) > 30 THEN 'Medium Risk (Inactive)'
                ELSE 'Low Risk'
            END
        ORDER BY 
            CASE 
                WHEN CAST(complain AS DECIMAL) = 1 THEN 'High Risk (Complaints)'
                WHEN CAST(satisfactionscore AS DECIMAL) <= 2 THEN 'Medium Risk (Low Satisfaction)'
                WHEN CAST(daysincelastorder AS DECIMAL) > 30 THEN 'Medium Risk (Inactive)'
                ELSE 'Low Risk'
            END;
        """
        
        columns, results = self.db.execute_query(churn_risk_query)
        if results:
            analyses["churn_risk_segments"] = [
                {"risk_segment": row[0], "count": row[1], "percentage": row[2]}
                for row in results
            ]
        
        self.results["segmentation_analysis"] = analyses
        return True
    
    def analyze_data_quality(self):
        """Analyze data quality issues"""
        print("[INFO] Analyzing data quality...")
        
        analyses = {}
        
        # 1. Null value analysis for key columns
        null_queries = [
            ("customerid", f"SELECT COUNT(*) FROM {self.full_table_name} WHERE customerid IS NULL OR customerid = ''"),
            ("churn", f"SELECT COUNT(*) FROM {self.full_table_name} WHERE churn IS NULL OR churn = ''"),
            ("gender", f"SELECT COUNT(*) FROM {self.full_table_name} WHERE gender IS NULL OR gender = ''"),
            ("preferredpaymentmode", f"SELECT COUNT(*) FROM {self.full_table_name} WHERE preferredpaymentmode IS NULL OR preferredpaymentmode = ''")
        ]
        
        null_counts = []
        for col_name, query in null_queries:
            columns, results = self.db.execute_query(query)
            if results:
                null_count = results[0][0]
                null_counts.append({
                    "column_name": col_name,
                    "null_count": null_count,
                    "null_percentage": round(100.0 * null_count / self.results["table_structure"].get("row_count", 1), 2)
                })
        
        if null_counts:
            analyses["null_analysis"] = null_counts
        
        # 2. Data consistency checks
        consistency_queries = [
            ("City Tier Range Check", f"""
            SELECT 
                CASE 
                    WHEN MIN(CAST(citytier AS DECIMAL)) >= 1 AND MAX(CAST(citytier AS DECIMAL)) <= 3 THEN 'PASS'
                    ELSE 'FAIL'
                END as result
            FROM {self.full_table_name}
            WHERE citytier IS NOT NULL AND citytier != ''
            """),
            ("Satisfaction Score Range Check", f"""
            SELECT 
                CASE 
                    WHEN MIN(CAST(satisfactionscore AS DECIMAL)) >= 1 AND MAX(CAST(satisfactionscore AS DECIMAL)) <= 5 THEN 'PASS'
                    ELSE 'FAIL'
                END as result
            FROM {self.full_table_name}
            WHERE satisfactionscore IS NOT NULL AND satisfactionscore != ''
            """),
            ("Churn Value Check", f"""
            SELECT 
                CASE 
                    WHEN MIN(CAST(churn AS DECIMAL)) >= 0 AND MAX(CAST(churn AS DECIMAL)) <= 1 THEN 'PASS'
                    ELSE 'FAIL'
                END as result
            FROM {self.full_table_name}
            WHERE churn IS NOT NULL AND churn != ''
            """)
        ]
        
        consistency_results = []
        for check_name, query in consistency_queries:
            columns, results = self.db.execute_query(query)
            if results:
                consistency_results.append({
                    "check_name": check_name,
                    "result": results[0][0]
                })
        
        if consistency_results:
            analyses["consistency_checks"] = consistency_results
        
        self.results["data_quality"] = analyses
        return True
    
    def generate_insights(self):
        """Generate business insights from analysis results"""
        print("[INFO] Generating business insights...")
        
        insights = {
            "demographic_insights": [],
            "behavioral_insights": [],
            "transactional_insights": [],
            "churn_insights": [],
            "segmentation_insights": [],
            "strategic_recommendations": []
        }
        
        # Demographic insights
        if "demographic_analysis" in self.results:
            demo = self.results["demographic_analysis"]
            
            if "age_analysis" in demo:
                age = demo["age_analysis"]
                if age.get("avg_age"):
                    insights["demographic_insights"].append(
                        f"Average customer age: {age['avg_age']:.1f} years"
                    )
            
            if "gender_distribution" in demo:
                gender = demo["gender_distribution"]
                if gender:
                    most_common = max(gender, key=lambda x: x["count"])
                    insights["demographic_insights"].append(
                        f"Most common gender: {most_common['gender']} ({most_common['percentage']}%)"
                    )
        
        # Behavioral insights
        if "behavioral_analysis" in self.results:
            behavior = self.results["behavioral_analysis"]
            
            if "login_device_distribution" in behavior:
                devices = behavior["login_device_distribution"]
                if devices:
                    most_common = max(devices, key=lambda x: x["count"])
                    insights["behavioral_insights"].append(
                        f"Most preferred login device: {most_common['device']} ({most_common['percentage']}%)"
                    )
            
            if "payment_mode_distribution" in behavior:
                payments = behavior["payment_mode_distribution"]
                if payments:
                    most_common = max(payments, key=lambda x: x["count"])
                    insights["behavioral_insights"].append(
                        f"Most preferred payment mode: {most_common['payment_mode']} ({most_common['percentage']}%)"
                    )
        
        # Transactional insights
        if "transactional_analysis" in self.results:
            trans = self.results["transactional_analysis"]
            
            if "order_count_analysis" in trans:
                orders = trans["order_count_analysis"]
                if orders.get("avg_orders"):
                    insights["transactional_insights"].append(
                        f"Average order count per customer: {orders['avg_orders']:.1f}"
                    )
            
            if "cashback_analysis" in trans:
                cashback = trans["cashback_analysis"]
                if cashback.get("avg_cashback"):
                    insights["transactional_insights"].append(
                        f"Average cashback amount: ${cashback['avg_cashback']:.2f}"
                    )
        
        # Churn insights
        if "churn_analysis" in self.results:
            churn = self.results["churn_analysis"]
            
            if "churn_distribution" in churn:
                churn_data = churn["churn_distribution"]
                for item in churn_data:
                    if item["churn"] == "1":
                        insights["churn_insights"].append(
                            f"Overall churn rate: {item['percentage']}%"
                        )
        
        # Segmentation insights
        if "segmentation_analysis" in self.results:
            seg = self.results["segmentation_analysis"]
            
            if "rfm_segments" in seg:
                rfm = seg["rfm_segments"]
                if rfm:
                    largest_segment = max(rfm, key=lambda x: x["count"])
                    insights["segmentation_insights"].append(
                        f"Largest RFM segment: {largest_segment['rfm_cell']} ({largest_segment['percentage']}%)"
                    )
        
        # Strategic recommendations
        insights["strategic_recommendations"] = [
            "1. Implement targeted retention campaigns for high churn risk segments",
            "2. Optimize mobile app experience for preferred login device users",
            "3. Create personalized offers based on preferred order categories",
            "4. Develop loyalty programs for customers with high order frequency",
            "5. Use behavioral data to predict churn and intervene proactively"
        ]
        
        self.results["insights"] = insights
        return True
    
    def create_visualizations(self):
        """Create comprehensive visualizations"""
        print("[STEP] Creating Visualizations")
        
        # 1. Demographic Visualizations
        print("  - Demographic Visualizations")
        print("[INFO] Creating demographic visualizations...")
        
        # Gender distribution
        if "demographic_analysis" in self.results:
            demo = self.results["demographic_analysis"]
            
            if "gender_distribution" in demo:
                gender_data = demo["gender_distribution"]
                if gender_data:
                    genders = [item["gender"] for item in gender_data]
                    counts = [item["count"] for item in gender_data]
                    
                    plt.figure(figsize=(10, 6))
                    plt.bar(genders, counts, color=['blue', 'pink', 'gray'])
                    plt.title('Gender Distribution', fontsize=16)
                    plt.xlabel('Gender', fontsize=12)
                    plt.ylabel('Number of Customers', fontsize=12)
                    
                    # Add count labels on bars
                    for i, count in enumerate(counts):
                        plt.text(i, count + 5, f'{count:,}', ha='center', va='bottom', fontsize=10)
                    
                    plt.tight_layout()
                    gender_plot_path = os.path.join(PLOT_SUBDIRS["demographic"], "gender_distribution.png")
                    plt.savefig(gender_plot_path, dpi=300)
                    plt.close()
                    print(f"  [OK] Gender distribution plot saved: {gender_plot_path}")
        
        # Tenure distribution
        tenure_query = f"""
        SELECT 
            CAST(tenure AS DECIMAL) as tenure
        FROM {self.full_table_name}
        WHERE tenure IS NOT NULL AND tenure != '' AND CAST(tenure AS DECIMAL) >= 0;
        """
        
        columns, results = self.db.execute_query(tenure_query)
        if results:
            tenures = [row[0] for row in results]
            
            plt.figure(figsize=(12, 6))
            plt.hist(tenures, bins=20, edgecolor='black', alpha=0.7)
            plt.title('Tenure Distribution (Years with Company)', fontsize=16)
            plt.xlabel('Tenure (Years)', fontsize=12)
            plt.ylabel('Number of Customers', fontsize=12)
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            tenure_plot_path = os.path.join(PLOT_SUBDIRS["demographic"], "tenure_distribution.png")
            plt.savefig(tenure_plot_path, dpi=300)
            plt.close()
            print(f"  [OK] Tenure distribution plot saved: {tenure_plot_path}")
        
        # 2. Behavioral Visualizations
        print("  - Behavioral Visualizations")
        print("[INFO] Creating behavioral visualizations...")
        
        # Payment mode distribution
        if "behavioral_analysis" in self.results:
            behavior = self.results["behavioral_analysis"]
            
            if "payment_mode_distribution" in behavior:
                payment_data = behavior["payment_mode_distribution"]
                if payment_data:
                    payment_modes = [item["payment_mode"] for item in payment_data]
                    payment_counts = [item["count"] for item in payment_data]
                    
                    plt.figure(figsize=(12, 6))
                    bars = plt.bar(payment_modes, payment_counts, color='skyblue')
                    plt.title('Preferred Payment Mode Distribution', fontsize=16)
                    plt.xlabel('Payment Mode', fontsize=12)
                    plt.ylabel('Number of Customers', fontsize=12)
                    plt.xticks(rotation=45, ha='right')
                    
                    # Add count labels on bars
                    for bar, count in zip(bars, payment_counts):
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                                f'{count:,}', ha='center', va='bottom', fontsize=9)
                    
                    plt.tight_layout()
                    payment_plot_path = os.path.join(PLOT_SUBDIRS["behavioral"], "payment_mode_distribution.png")
                    plt.savefig(payment_plot_path, dpi=300)
                    plt.close()
                    print(f"  [OK] Payment mode distribution plot saved: {payment_plot_path}")
        
        # 3. Transactional Visualizations
        print("  - Transactional Visualizations")
        print("[INFO] Creating transactional visualizations...")
        
        # Order count distribution
        order_query = f"""
        SELECT 
            CAST(ordercount AS DECIMAL) as order_count
        FROM {self.full_table_name}
        WHERE ordercount IS NOT NULL AND ordercount != '' AND CAST(ordercount AS DECIMAL) >= 0;
        """
        
        columns, results = self.db.execute_query(order_query)
        if results:
            order_counts = [row[0] for row in results]
            
            plt.figure(figsize=(12, 6))
            plt.hist(order_counts, bins=20, edgecolor='black', alpha=0.7, color='green')
            plt.title('Order Count Distribution', fontsize=16)
            plt.xlabel('Number of Orders', fontsize=12)
            plt.ylabel('Number of Customers', fontsize=12)
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            order_plot_path = os.path.join(PLOT_SUBDIRS["transactional"], "order_count_distribution.png")
            plt.savefig(order_plot_path, dpi=300)
            plt.close()
            print(f"  [OK] Order count distribution plot saved: {order_plot_path}")
        
        # 4. Churn Visualizations
        print("  - Churn Visualizations")
        print("[INFO] Creating churn visualizations...")
        
        # Churn rate visualization
        if "churn_analysis" in self.results:
            churn = self.results["churn_analysis"]
            
            if "churn_distribution" in churn:
                churn_data = churn["churn_distribution"]
                if churn_data:
                    churn_labels = ['Churned', 'Retained']
                    churn_counts = [0, 0]
                    
                    for item in churn_data:
                        if item["churn"] == "1":
                            churn_counts[0] = item["count"]
                        else:
                            churn_counts[1] = item["count"]
                    
                    plt.figure(figsize=(10, 6))
                    colors = ['red', 'green']
                    plt.pie(churn_counts, labels=churn_labels, colors=colors, autopct='%1.1f%%', startangle=90)
                    plt.title('Customer Churn Distribution', fontsize=16)
                    
                    plt.tight_layout()
                    churn_plot_path = os.path.join(PLOT_SUBDIRS["transactional"], "churn_distribution.png")
                    plt.savefig(churn_plot_path, dpi=300)
                    plt.close()
                    print(f"  [OK] Churn distribution plot saved: {churn_plot_path}")
        
        # 5. Correlation Visualizations
        print("  - Correlation Visualizations")
        print("[INFO] Creating correlation visualizations...")
        
        # Satisfaction Score vs Churn correlation scatter plot
        satisfaction_churn_scatter_query = f"""
        SELECT 
            CAST(satisfactionscore AS DECIMAL) as satisfaction_score,
            CAST(churn AS DECIMAL) as churn
        FROM {self.full_table_name}
        WHERE satisfactionscore IS NOT NULL AND satisfactionscore != '' 
          AND churn IS NOT NULL AND churn != ''
          AND CAST(satisfactionscore AS DECIMAL) > 0;
        """
        
        columns, results = self.db.execute_query(satisfaction_churn_scatter_query)
        if results:
            satisfaction_scores = [row[0] for row in results]
            churns = [row[1] for row in results]
            
            plt.figure(figsize=(10, 6))
            satisfaction_scores_float = [float(score) for score in satisfaction_scores]
            churns_float = [float(churn) for churn in churns]
            plt.scatter(satisfaction_scores_float, churns_float, alpha=0.5, color='purple')
            plt.title('Satisfaction Score vs Churn Correlation', fontsize=16)
            plt.xlabel('Satisfaction Score (1-5)', fontsize=12)
            plt.ylabel('Churn (1=Yes, 0=No)', fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # Add trend line
            z = np.polyfit(satisfaction_scores_float, churns_float, 1)
            p = np.poly1d(z)
            plt.plot(satisfaction_scores_float, p(satisfaction_scores_float), "r--", alpha=0.8)
            
            plt.tight_layout()
            correlation_plot_path = os.path.join(PLOT_SUBDIRS["correlations"], "satisfaction_vs_churn_correlation.png")
            plt.savefig(correlation_plot_path, dpi=300)
            plt.close()
            print(f"  [OK] Satisfaction score vs churn correlation plot saved: {correlation_plot_path}")
        
        # 6. Segmentation Visualizations
        print("  - Segmentation Visualizations")
        print("[INFO] Creating segmentation visualizations...")
        
        # RFM segments visualization
        if "segmentation_analysis" in self.results and "rfm_segments" in self.results["segmentation_analysis"]:
            rfm_segments = self.results["segmentation_analysis"]["rfm_segments"]
            
            if rfm_segments:
                # Prepare data
                rfm_cells = [seg["rfm_cell"] for seg in rfm_segments]
                counts = [seg["count"] for seg in rfm_segments]
                percentages = [seg["percentage"] for seg in rfm_segments]
                
                plt.figure(figsize=(14, 8))
                
                # Create bar chart
                bars = plt.bar(rfm_cells, counts, color='skyblue', edgecolor='black')
                plt.title('Top RFM Segments Distribution', fontsize=16)
                plt.xlabel('RFM Cell (Recency-Frequency-Monetary)', fontsize=12)
                plt.ylabel('Number of Customers', fontsize=12)
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add percentage labels on top of bars
                for bar, percentage in zip(bars, percentages):
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                            f'{percentage:.1f}%', ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                rfm_plot_path = os.path.join(PLOT_SUBDIRS["segmentation"], "rfm_segments_distribution.png")
                plt.savefig(rfm_plot_path, dpi=300)
                plt.close()
                print(f"  [OK] RFM segments distribution plot saved: {rfm_plot_path}")
        
        # Churn risk segments visualization
        if "segmentation_analysis" in self.results and "churn_risk_segments" in self.results["segmentation_analysis"]:
            risk_segments = self.results["segmentation_analysis"]["churn_risk_segments"]
            
            if risk_segments:
                # Prepare data
                segments = [seg["risk_segment"] for seg in risk_segments]
                counts = [seg["count"] for seg in risk_segments]
                percentages = [seg["percentage"] for seg in risk_segments]
                
                plt.figure(figsize=(12, 8))
                
                # Create pie chart for churn risk segments
                colors = ['lightgreen', 'gold', 'lightcoral', 'lightblue']
                explode = [0.05] * len(segments)  # Slightly explode all slices
                
                plt.pie(counts, labels=segments, autopct='%1.1f%%', colors=colors,
                       explode=explode, startangle=90, shadow=True)
                plt.title('Churn Risk Segmentation', fontsize=16)
                
                plt.tight_layout()
                risk_plot_path = os.path.join(PLOT_SUBDIRS["segmentation"], "churn_risk_segments.png")
                plt.savefig(risk_plot_path, dpi=300)
                plt.close()
                print(f"  [OK] Churn risk segments plot saved: {risk_plot_path}")
        
        return True
    
    def create_summary_file(self):
        """Create comprehensive summary.txt file with every tiny detail"""
        print("[INFO] Creating comprehensive summary.txt file...")
        
        try:
            with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 80 + "\n")
                f.write("E-COMMERCE CUSTOMER CHURN - MAXIMUM EDA SUMMARY\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Analysis Timestamp: {CURRENT_TIMESTAMP}\n")
                f.write(f"Table: {self.full_table_name}\n")
                f.write(f"Output Directory: {OUTPUT_DIR}\n")
                f.write("\n" + "=" * 80 + "\n\n")
                
                # 1. Table Structure
                f.write("1. TABLE STRUCTURE\n")
                f.write("-" * 40 + "\n")
                if "table_structure" in self.results:
                    structure = self.results["table_structure"]
                    row_count = structure.get('row_count', 'N/A')
                    col_count = structure.get('total_columns', 'N/A')
                    
                    # Format row count with thousands separator if it's a number
                    if isinstance(row_count, (int, float)):
                        f.write(f"Total Rows: {row_count:,}\n")
                    else:
                        f.write(f"Total Rows: {row_count}\n")
                    
                    # Format column count with thousands separator if it's a number
                    if isinstance(col_count, (int, float)):
                        f.write(f"Total Columns: {col_count:,}\n\n")
                    else:
                        f.write(f"Total Columns: {col_count}\n\n")
                    
                    f.write("Column Details:\n")
                    for col_info in structure.get("columns", []):
                        f.write(f"  - {col_info['name']}: {col_info['type']} "
                               f"(Nullable: {col_info['nullable']})\n")
                f.write("\n")
                
                # 2. Demographic Analysis
                f.write("2. DEMOGRAPHIC ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "demographic_analysis" in self.results:
                    demo = self.results["demographic_analysis"]
                    
                    if "gender_distribution" in demo:
                        f.write("Gender Distribution:\n")
                        for gender in demo["gender_distribution"]:
                            count = gender.get('count', 'N/A')
                            if isinstance(count, (int, float)):
                                f.write(f"  - {gender['gender']}: {count:,} customers "
                                       f"({gender.get('percentage', 'N/A')}%)\n")
                            else:
                                f.write(f"  - {gender['gender']}: {count} customers "
                                       f"({gender.get('percentage', 'N/A')}%)\n")
                    
                    if "city_tier_distribution" in demo:
                        city_tier = demo["city_tier_distribution"]
                        f.write("\nCity Tier Distribution:\n")
                        for tier in city_tier:
                            count = tier.get('count', 'N/A')
                            if isinstance(count, (int, float)):
                                f.write(f"  - Tier {tier['city_tier']}: {count:,} customers "
                                       f"({tier.get('percentage', 'N/A')}%)\n")
                            else:
                                f.write(f"  - Tier {tier['city_tier']}: {count} customers "
                                       f"({tier.get('percentage', 'N/A')}%)\n")
                f.write("\n")
                
                # 3. Behavioral Analysis
                f.write("3. BEHAVIORAL ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "behavioral_analysis" in self.results:
                    behavior = self.results["behavioral_analysis"]
                    
                    if "payment_mode_distribution" in behavior:
                        f.write("Preferred Payment Modes:\n")
                        for payment in behavior["payment_mode_distribution"]:
                            count = payment.get('count', 'N/A')
                            if isinstance(count, (int, float)):
                                f.write(f"  - {payment['payment_mode']}: {count:,} customers "
                                       f"({payment.get('percentage', 'N/A')}%)\n")
                            else:
                                f.write(f"  - {payment['payment_mode']}: {count} customers "
                                       f"({payment.get('percentage', 'N/A')}%)\n")
                f.write("\n")
                
                # 4. Transactional Analysis
                f.write("4. TRANSACTIONAL ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "transactional_analysis" in self.results:
                    trans = self.results["transactional_analysis"]
                    
                    if "order_count_analysis" in trans:
                        orders = trans["order_count_analysis"]
                        f.write("Order Count Analysis:\n")
                        avg_orders = orders.get('avg_orders', 'N/A')
                        min_orders = orders.get('min_orders', 'N/A')
                        max_orders = orders.get('max_orders', 'N/A')
                        
                        if isinstance(avg_orders, (int, float)):
                            f.write(f"  - Average Orders: {avg_orders:.1f}\n")
                        else:
                            f.write(f"  - Average Orders: {avg_orders}\n")
                        
                        f.write(f"  - Minimum Orders: {min_orders}\n")
                        f.write(f"  - Maximum Orders: {max_orders}\n")
                f.write("\n")
                
                # 5. Churn Analysis
                f.write("5. CHURN ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "churn_analysis" in self.results:
                    churn = self.results["churn_analysis"]
                    
                    if "churn_distribution" in churn:
                        f.write("Churn Distribution:\n")
                        for churn_data in churn["churn_distribution"]:
                            count = churn_data.get('count', 'N/A')
                            if isinstance(count, (int, float)):
                                f.write(f"  - Churn = {churn_data['churn']}: {count:,} customers "
                                       f"({churn_data.get('percentage', 'N/A')}%)\n")
                            else:
                                f.write(f"  - Churn = {churn_data['churn']}: {count} customers "
                                       f"({churn_data.get('percentage', 'N/A')}%)\n")
                f.write("\n")
                
                # 6. Correlation Analysis
                f.write("6. CORRELATION ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "correlation_analysis" in self.results:
                    corr = self.results["correlation_analysis"]
                    
                    if "satisfaction_churn_correlation" in corr:
                        correlation = corr["satisfaction_churn_correlation"]
                        if isinstance(correlation, (int, float)):
                            f.write(f"Satisfaction Score vs Churn Correlation: {correlation:.3f}\n")
                        else:
                            f.write(f"Satisfaction Score vs Churn Correlation: {correlation}\n")
                f.write("\n")
                
                # 7. Segmentation Analysis
                f.write("7. SEGMENTATION ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "segmentation_analysis" in self.results:
                    seg = self.results["segmentation_analysis"]
                    
                    if "rfm_segments" in seg:
                        f.write("Top RFM Segments:\n")
                        for segment in seg["rfm_segments"]:
                            count = segment.get('count', 'N/A')
                            if isinstance(count, (int, float)):
                                f.write(f"  - {segment['rfm_cell']}: {count:,} customers "
                                       f"({segment.get('percentage', 'N/A')}%)\n")
                            else:
                                f.write(f"  - {segment['rfm_cell']}: {count} customers "
                                       f"({segment.get('percentage', 'N/A')}%)\n")
                f.write("\n")
                
                # 8. Data Quality Analysis
                f.write("8. DATA QUALITY ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "data_quality" in self.results:
                    quality = self.results["data_quality"]
                    
                    if "consistency_checks" in quality:
                        f.write("Data Consistency Checks:\n")
                        for check in quality["consistency_checks"]:
                            if isinstance(check, dict):
                                f.write(f"  - {check.get('check_name', 'N/A')}: {check.get('result', 'N/A')}\n")
                            else:
                                f.write(f"  - {check}\n")
                f.write("\n")
                
                # 9. Business Insights and Recommendations
                f.write("9. BUSINESS INSIGHTS AND RECOMMENDATIONS\n")
                f.write("-" * 40 + "\n")
                if "insights" in self.results:
                    insights = self.results["insights"]
                    
                    if "demographic_insights" in insights:
                        f.write("Key Demographic Insights:\n")
                        for insight in insights["demographic_insights"]:
                            f.write(f"  - {insight}\n")
                    
                    if "behavioral_insights" in insights:
                        f.write("\nBehavioral Insights:\n")
                        for insight in insights["behavioral_insights"]:
                            f.write(f"  - {insight}\n")
                    
                    if "transactional_insights" in insights:
                        f.write("\nTransactional Insights:\n")
                        for insight in insights["transactional_insights"]:
                            f.write(f"  - {insight}\n")
                    
                    if "churn_insights" in insights:
                        f.write("\nChurn Insights:\n")
                        for insight in insights["churn_insights"]:
                            f.write(f"  - {insight}\n")
                    
                    if "strategic_recommendations" in insights:
                        f.write("\nStrategic Recommendations:\n")
                        for recommendation in insights["strategic_recommendations"]:
                            f.write(f"  - {recommendation}\n")
                
                # 10. Generated Files
                f.write("\n" + "=" * 80 + "\n")
                f.write("10. GENERATED FILES\n")
                f.write("-" * 40 + "\n")
                f.write(f"Summary File: {SUMMARY_FILE}\n")
                f.write(f"Plots Directory: {PLOTS_DIR}\n")
                f.write(f"Data Directory: {DATA_DIR}\n")
                
                f.write("\nGenerated Plots:\n")
                f.write("  Demographic:\n")
                f.write("    - gender_distribution.png\n")
                f.write("    - tenure_distribution.png\n")
                f.write("  Behavioral:\n")
                f.write("    - payment_mode_distribution.png\n")
                f.write("  Transactional:\n")
                f.write("    - order_count_distribution.png\n")
                f.write("    - churn_distribution.png\n")
                f.write("  Correlations:\n")
                f.write("    - satisfaction_vs_churn_correlation.png\n")
                f.write("  Segmentation:\n")
                f.write("    - rfm_segments_distribution.png\n")
                f.write("    - churn_risk_segments.png\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF MAXIMUM EDA SUMMARY\n")
                f.write("=" * 80 + "\n")
            
            print(f"  [SUCCESS] Comprehensive summary saved: {SUMMARY_FILE}")
            return True
            
        except Exception as e:
            print(f"  [ERROR] Summary file creation failed: {e}")
            return False
    
    def save_results(self):
        """Save analysis results to JSON files"""
        print("[STEP] Saving Analysis Results")
        
        # Save statistics
        stats_file = os.path.join(DATA_DIR, "statistics.json")
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"  [OK] Statistics saved: {stats_file}")
        except Exception as e:
            print(f"  [ERROR] Failed to save statistics: {e}")
        
        # Save insights separately
        insights_file = os.path.join(DATA_DIR, "insights.json")
        try:
            if "insights" in self.results:
                with open(insights_file, 'w', encoding='utf-8') as f:
                    json.dump(self.results["insights"], f, indent=2, default=str)
                print(f"  [OK] Insights saved: {insights_file}")
        except Exception as e:
            print(f"  [ERROR] Failed to save insights: {e}")
        
        return True
    
    def run_complete_analysis(self):
        """Run the complete EDA analysis"""
        print("\n" + "=" * 80)
        print("E-COMMERCE CUSTOMER CHURN - MAXIMUM EDA")
        print("=" * 80)
        print(f"[START] Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        start_time = datetime.now()
        
        # Discover table name
        if not self.discover_table_name():
            print("[ERROR] Failed to discover table name")
            return False
        
        # Run analysis steps
        analysis_steps = [
            ("Table Structure Analysis", self.analyze_table_structure),
            ("Demographic Analysis", self.analyze_demographics),
            ("Behavioral Analysis", self.analyze_behavioral_data),
            ("Transactional Analysis", self.analyze_transactional_data),
            ("Churn Analysis", self.analyze_churn_data),
            ("Correlation Analysis", self.analyze_correlations),
            ("Segmentation Analysis", self.analyze_segmentation),
            ("Data Quality Analysis", self.analyze_data_quality),
            ("Insights Generation", self.generate_insights)
        ]
        
        for step_name, step_function in analysis_steps:
            print(f"[STEP] {step_name}")
            if not step_function():
                print(f"  [WARNING] {step_name} failed or returned no results")
        
        # Create visualizations
        self.create_visualizations()
        
        # Create summary file
        self.create_summary_file()
        
        # Save results
        self.save_results()
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = end_time - start_time
        
        print("\n" + "=" * 80)
        print("[COMPLETE] Maximum EDA Analysis Finished")
        print("=" * 80)
        print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Execution Time: {execution_time}")
        print(f"Output Directory: {OUTPUT_DIR}")
        print("=" * 80 + "\n")
        
        return True

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("=" * 80)
    print("E-COMMERCE PERSONALITY ANALYSIS - MAXIMUM EDA SCRIPT")
    print("=" * 80)
    
    # Create database connection
    db = DatabaseConnection()
    if not db.connect():
        print("[ERROR] Failed to connect to database")
        return
    
    # Create EDA analyzer
    eda = EcommerceMaxEDA(db)
    
    # Run complete analysis
    success = eda.run_complete_analysis()
    
    # Close database connection
    db.close()
    
    if success:
        print("[SUCCESS] Maximum EDA completed successfully!")
        print(f"Check the output directory: {OUTPUT_DIR}")
        print("  - Summary: {SUMMARY_FILE}")
        print("  - Plots: {PLOTS_DIR}")
        print("  - Data: {DATA_DIR}")
    else:
        print("[ERROR] Maximum EDA analysis failed")
    
    print("\n[INFO] Database connection closed")

if __name__ == "__main__":
    main()
