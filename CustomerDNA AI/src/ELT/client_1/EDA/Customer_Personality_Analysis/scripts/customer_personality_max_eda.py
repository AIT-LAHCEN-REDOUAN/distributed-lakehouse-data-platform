#!/usr/bin/env python3
"""
CUSTOMER PERSONALITY ANALYSIS - MAXIMUM EDA SCRIPT
==================================================

This is a comprehensive single script that performs maximum EDA on the
Customer Personality Analysis dataset (marketing_campaign table).

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
│   ├── 02_purchase_behavior/
│   ├── 03_campaign_response/
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

TABLE_NAME = "marketing_campaign"
OUTPUT_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
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
    "purchase_behavior": os.path.join(PLOTS_DIR, "02_purchase_behavior"),
    "campaign_response": os.path.join(PLOTS_DIR, "03_campaign_response"),
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
            
            # Check if query returns results
            if self.cursor.description:
                columns = [desc[0] for desc in self.cursor.description]
                results = self.cursor.fetchall()
                return columns, results
            else:
                self.connection.commit()
                return None, None
        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")
            print(f"Query: {query[:200]}...")
            return None, None
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("[INFO] Database connection closed")

# ============================================================================
# EDA ANALYSIS CLASS
# ============================================================================

class CustomerPersonalityMaxEDA:
    """Main class for maximum EDA analysis"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.table_name = TABLE_NAME
        self.schema = RAW_DATA_SCHEMA
        self.full_table_name = f"{self.schema}.{self.table_name}"
        
        # Analysis results storage
        self.results = {
            "table_structure": {},
            "demographic_analysis": {},
            "purchase_analysis": {},
            "campaign_analysis": {},
            "correlation_analysis": {},
            "segmentation_analysis": {},
            "data_quality": {},
            "insights": {}
        }
        
        # Column categories
        self.column_categories = {
            "demographic": ['year_birth', 'education', 'marital_status', 'income'],
            "family": ['kidhome', 'teenhome'],
            "purchase": [
                'mntwines', 'mntfruits', 'mntmeatproducts', 'mntfishproducts',
                'mntsweetproducts', 'mntgoldprods'
            ],
            "purchase_channel": [
                'numdealspurchases', 'numwebpurchases', 'numcatalogpurchases',
                'numstorepurchases'
            ],
            "campaign": [
                'acceptedcmp1', 'acceptedcmp2', 'acceptedcmp3', 'acceptedcmp4',
                'acceptedcmp5', 'response'
            ],
            "other": ['dt_customer', 'recency', 'complain', 'z_costcontact', 'z_revenue']
        }
    
    # ============================================================================
    # CORE ANALYSIS METHODS
    # ============================================================================
    
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
        
        # 1. Age analysis (calculate from year_birth)
        query = f"""
        SELECT 
            COUNT(*) as total_customers,
            MIN(CAST(year_birth AS INTEGER)) as min_birth_year,
            MAX(CAST(year_birth AS INTEGER)) as max_birth_year,
            AVG(CAST(year_birth AS INTEGER)) as avg_birth_year,
            STDDEV(CAST(year_birth AS INTEGER)) as std_birth_year
        FROM {self.full_table_name}
        WHERE year_birth IS NOT NULL AND year_birth != '';
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            analyses["age_analysis"] = {
                "total_customers": results[0][0],
                "min_birth_year": results[0][1],
                "max_birth_year": results[0][2],
                "avg_birth_year": float(results[0][3]) if results[0][3] else None,
                "std_birth_year": float(results[0][4]) if results[0][4] else None
            }
        
        # 2. Income analysis
        query = f"""
        SELECT 
            COUNT(*) as customers_with_income,
            MIN(CAST(income AS DECIMAL)) as min_income,
            MAX(CAST(income AS DECIMAL)) as max_income,
            AVG(CAST(income AS DECIMAL)) as avg_income,
            STDDEV(CAST(income AS DECIMAL)) as std_income,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY CAST(income AS DECIMAL)) as income_q1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY CAST(income AS DECIMAL)) as income_median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY CAST(income AS DECIMAL)) as income_q3
        FROM {self.full_table_name}
        WHERE income IS NOT NULL AND income != '';
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            analyses["income_analysis"] = {
                "customers_with_income": results[0][0],
                "min_income": float(results[0][1]) if results[0][1] else None,
                "max_income": float(results[0][2]) if results[0][2] else None,
                "avg_income": float(results[0][3]) if results[0][3] else None,
                "std_income": float(results[0][4]) if results[0][4] else None,
                "income_q1": float(results[0][5]) if results[0][5] else None,
                "income_median": float(results[0][6]) if results[0][6] else None,
                "income_q3": float(results[0][7]) if results[0][7] else None
            }
        
        # 3. Education distribution
        query = f"""
        SELECT 
            education,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE education IS NOT NULL AND education != ''
        GROUP BY education
        ORDER BY count DESC;
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            education_data = []
            for row in results:
                education_data.append({
                    "education": row[0],
                    "count": row[1],
                    "percentage": float(row[2]) if row[2] else 0
                })
            analyses["education_distribution"] = education_data
        
        # 4. Marital status distribution
        query = f"""
        SELECT 
            marital_status,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE marital_status IS NOT NULL AND marital_status != ''
        GROUP BY marital_status
        ORDER BY count DESC;
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            marital_data = []
            for row in results:
                marital_data.append({
                    "marital_status": row[0],
                    "count": row[1],
                    "percentage": float(row[2]) if row[2] else 0
                })
            analyses["marital_status_distribution"] = marital_data
        
        # 5. Family composition
        query = f"""
        SELECT 
            kidhome,
            teenhome,
            COUNT(*) as customer_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.full_table_name}
        WHERE kidhome IS NOT NULL AND teenhome IS NOT NULL
        GROUP BY kidhome, teenhome
        ORDER BY customer_count DESC;
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            family_data = []
            for row in results:
                family_data.append({
                    "kids": int(row[0]) if row[0] else 0,
                    "teens": int(row[1]) if row[1] else 0,
                    "count": row[2],
                    "percentage": float(row[3]) if row[3] else 0
                })
            analyses["family_composition"] = family_data
        
        self.results["demographic_analysis"] = analyses
        return True
    
    def analyze_purchase_behavior(self):
        """Analyze purchase behavior across categories"""
        print("[INFO] Analyzing purchase behavior...")
        
        analyses = {}
        
        # 1. Total spending by category
        query = f"""
        SELECT 
            SUM(CAST(mntwines AS DECIMAL)) as total_wines,
            SUM(CAST(mntfruits AS DECIMAL)) as total_fruits,
            SUM(CAST(mntmeatproducts AS DECIMAL)) as total_meat,
            SUM(CAST(mntfishproducts AS DECIMAL)) as total_fish,
            SUM(CAST(mntsweetproducts AS DECIMAL)) as total_sweets,
            SUM(CAST(mntgoldprods AS DECIMAL)) as total_gold,
            AVG(CAST(mntwines AS DECIMAL)) as avg_wines,
            AVG(CAST(mntfruits AS DECIMAL)) as avg_fruits,
            AVG(CAST(mntmeatproducts AS DECIMAL)) as avg_meat,
            AVG(CAST(mntfishproducts AS DECIMAL)) as avg_fish,
            AVG(CAST(mntsweetproducts AS DECIMAL)) as avg_sweets,
            AVG(CAST(mntgoldprods AS DECIMAL)) as avg_gold
        FROM {self.full_table_name}
        WHERE mntwines IS NOT NULL AND mntwines != '';
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            purchase_totals = {
                "total_wines": float(results[0][0]) if results[0][0] else 0,
                "total_fruits": float(results[0][1]) if results[0][1] else 0,
                "total_meat": float(results[0][2]) if results[0][2] else 0,
                "total_fish": float(results[0][3]) if results[0][3] else 0,
                "total_sweets": float(results[0][4]) if results[0][4] else 0,
                "total_gold": float(results[0][5]) if results[0][5] else 0,
                "avg_wines": float(results[0][6]) if results[0][6] else 0,
                "avg_fruits": float(results[0][7]) if results[0][7] else 0,
                "avg_meat": float(results[0][8]) if results[0][8] else 0,
                "avg_fish": float(results[0][9]) if results[0][9] else 0,
                "avg_sweets": float(results[0][10]) if results[0][10] else 0,
                "avg_gold": float(results[0][11]) if results[0][11] else 0
            }
            analyses["purchase_totals"] = purchase_totals
        
        # 2. Purchase channel analysis
        query = f"""
        SELECT 
            SUM(CAST(numdealspurchases AS INTEGER)) as total_deal_purchases,
            SUM(CAST(numwebpurchases AS INTEGER)) as total_web_purchases,
            SUM(CAST(numcatalogpurchases AS INTEGER)) as total_catalog_purchases,
            SUM(CAST(numstorepurchases AS INTEGER)) as total_store_purchases,
            AVG(CAST(numdealspurchases AS DECIMAL)) as avg_deal_purchases,
            AVG(CAST(numwebpurchases AS DECIMAL)) as avg_web_purchases,
            AVG(CAST(numcatalogpurchases AS DECIMAL)) as avg_catalog_purchases,
            AVG(CAST(numstorepurchases AS DECIMAL)) as avg_store_purchases
        FROM {self.full_table_name}
        WHERE numdealspurchases IS NOT NULL AND numdealspurchases != '';
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            channel_analysis = {
                "total_deal_purchases": results[0][0],
                "total_web_purchases": results[0][1],
                "total_catalog_purchases": results[0][2],
                "total_store_purchases": results[0][3],
                "avg_deal_purchases": float(results[0][4]) if results[0][4] else 0,
                "avg_web_purchases": float(results[0][5]) if results[0][5] else 0,
                "avg_catalog_purchases": float(results[0][6]) if results[0][6] else 0,
                "avg_store_purchases": float(results[0][7]) if results[0][7] else 0
            }
            analyses["purchase_channels"] = channel_analysis
        
        # 3. Recency analysis
        query = f"""
        SELECT 
            MIN(CAST(recency AS INTEGER)) as min_recency,
            MAX(CAST(recency AS INTEGER)) as max_recency,
            AVG(CAST(recency AS DECIMAL)) as avg_recency,
            STDDEV(CAST(recency AS DECIMAL)) as std_recency,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY CAST(recency AS INTEGER)) as recency_q1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY CAST(recency AS INTEGER)) as recency_median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY CAST(recency AS INTEGER)) as recency_q3
        FROM {self.full_table_name}
        WHERE recency IS NOT NULL AND recency != '';
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            recency_analysis = {
                "min_recency": results[0][0],
                "max_recency": results[0][1],
                "avg_recency": float(results[0][2]) if results[0][2] else 0,
                "std_recency": float(results[0][3]) if results[0][3] else 0,
                "recency_q1": results[0][4],
                "recency_median": results[0][5],
                "recency_q3": results[0][6]
            }
            analyses["recency_analysis"] = recency_analysis
        
        self.results["purchase_analysis"] = analyses
        return True
    
    def analyze_campaign_response(self):
        """Analyze campaign response rates"""
        print("[INFO] Analyzing campaign response rates...")
        
        analyses = {}
        
        # 1. Overall response rate
        query = f"""
        SELECT 
            COUNT(*) as total_customers,
            SUM(CASE WHEN response = '1' THEN 1 ELSE 0 END) as responders,
            ROUND(SUM(CASE WHEN response = '1' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as response_rate
        FROM {self.full_table_name}
        WHERE response IS NOT NULL AND response != '';
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            response_analysis = {
                "total_customers": results[0][0],
                "responders": results[0][1],
                "response_rate": float(results[0][2]) if results[0][2] else 0
            }
            analyses["overall_response"] = response_analysis
        
        # 2. Individual campaign response rates
        campaigns = ['acceptedcmp1', 'acceptedcmp2', 'acceptedcmp3', 'acceptedcmp4', 'acceptedcmp5']
        
        for campaign in campaigns:
            query = f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN {campaign} = '1' THEN 1 ELSE 0 END) as accepted,
                ROUND(SUM(CASE WHEN {campaign} = '1' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as acceptance_rate
            FROM {self.full_table_name}
            WHERE {campaign} IS NOT NULL AND {campaign} != '';
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                analyses[f"{campaign}_response"] = {
                    "total": results[0][0],
                    "accepted": results[0][1],
                    "acceptance_rate": float(results[0][2]) if results[0][2] else 0
                }
        
        # 3. Response by income groups
        query = f"""
        WITH income_groups AS (
            SELECT 
                CASE 
                    WHEN CAST(income AS DECIMAL) < 30000 THEN 'Low (<30k)'
                    WHEN CAST(income AS DECIMAL) BETWEEN 30000 AND 70000 THEN 'Medium (30k-70k)'
                    WHEN CAST(income AS DECIMAL) > 70000 THEN 'High (>70k)'
                    ELSE 'Unknown'
                END as income_group,
                response
            FROM {self.full_table_name}
            WHERE income IS NOT NULL AND income != '' AND response IS NOT NULL AND response != ''
        )
        SELECT 
            income_group,
            COUNT(*) as total_customers,
            SUM(CASE WHEN response = '1' THEN 1 ELSE 0 END) as responders,
            ROUND(SUM(CASE WHEN response = '1' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as response_rate
        FROM income_groups
        GROUP BY income_group
        ORDER BY 
            CASE income_group
                WHEN 'Low (<30k)' THEN 1
                WHEN 'Medium (30k-70k)' THEN 2
                WHEN 'High (>70k)' THEN 3
                ELSE 4
            END;
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            income_response = []
            for row in results:
                income_response.append({
                    "income_group": row[0],
                    "total_customers": row[1],
                    "responders": row[2],
                    "response_rate": float(row[3]) if row[3] else 0
                })
            analyses["response_by_income"] = income_response
        
        self.results["campaign_analysis"] = analyses
        return True
    
    def analyze_correlations(self):
        """Analyze correlations between key variables"""
        print("[INFO] Analyzing correlations between variables...")
        
        analyses = {}
        
        # 1. Correlation matrix of key numeric variables
        query = f"""
        SELECT 
            CAST(income AS DECIMAL) as income,
            CAST(mntwines AS DECIMAL) as wines,
            CAST(mntfruits AS DECIMAL) as fruits,
            CAST(mntmeatproducts AS DECIMAL) as meat,
            CAST(mntfishproducts AS DECIMAL) as fish,
            CAST(mntsweetproducts AS DECIMAL) as sweets,
            CAST(mntgoldprods AS DECIMAL) as gold,
            CAST(numwebpurchases AS INTEGER) as web_purchases,
            CAST(numstorepurchases AS INTEGER) as store_purchases,
            CAST(recency AS INTEGER) as recency
        FROM {self.full_table_name}
        WHERE income IS NOT NULL AND income != ''
          AND mntwines IS NOT NULL AND mntwines != ''
        LIMIT 1000;
        """
        
        columns, results = self.db.execute_query(query)
        if results and len(results) > 10:  # Need enough data for correlation
            # Convert to DataFrame for correlation analysis
            data = []
            for row in results:
                data.append([float(val) if val is not None else 0 for val in row])
            
            df = pd.DataFrame(data, columns=columns)
            correlation_matrix = df.corr()
            
            # Convert to serializable format
            corr_dict = {}
            for i, col1 in enumerate(correlation_matrix.columns):
                corr_dict[col1] = {}
                for j, col2 in enumerate(correlation_matrix.columns):
                    corr_dict[col1][col2] = float(correlation_matrix.iloc[i, j])
            
            analyses["correlation_matrix"] = corr_dict
            
            # 2. Top correlations
            correlations = []
            for i, col1 in enumerate(correlation_matrix.columns):
                for j, col2 in enumerate(correlation_matrix.columns):
                    if i < j:  # Avoid duplicates and diagonal
                        corr_value = correlation_matrix.iloc[i, j]
                        if abs(corr_value) > 0.3:  # Significant correlation
                            correlations.append({
                                "variable1": col1,
                                "variable2": col2,
                                "correlation": float(corr_value),
                                "strength": "Strong" if abs(corr_value) > 0.7 else 
                                          "Moderate" if abs(corr_value) > 0.5 else 
                                          "Weak"
                            })
            
            # Sort by absolute correlation value
            correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            analyses["significant_correlations"] = correlations[:20]  # Top 20
        
        self.results["correlation_analysis"] = analyses
        return True
    
    def analyze_segmentation(self):
        """Perform RFM segmentation analysis"""
        print("[INFO] Performing RFM segmentation analysis...")
        
        analyses = {}
        
        # 1. RFM Segmentation
        query = f"""
        WITH rfm_data AS (
            SELECT 
                CAST(recency AS INTEGER) as recency,
                CAST(numwebpurchases AS INTEGER) + CAST(numstorepurchases AS INTEGER) + 
                CAST(numcatalogpurchases AS INTEGER) + CAST(numdealspurchases AS INTEGER) as frequency,
                CAST(mntwines AS DECIMAL) + CAST(mntfruits AS DECIMAL) + CAST(mntmeatproducts AS DECIMAL) +
                CAST(mntfishproducts AS DECIMAL) + CAST(mntsweetproducts AS DECIMAL) + 
                CAST(mntgoldprods AS DECIMAL) as monetary
            FROM {self.full_table_name}
            WHERE recency IS NOT NULL AND recency != ''
              AND numwebpurchases IS NOT NULL AND numwebpurchases != ''
        ),
        rfm_scores AS (
            SELECT 
                recency,
                frequency,
                monetary,
                NTILE(4) OVER (ORDER BY recency DESC) as r_score,
                NTILE(4) OVER (ORDER BY frequency) as f_score,
                NTILE(4) OVER (ORDER BY monetary) as m_score
            FROM rfm_data
        ),
        rfm_combined AS (
            SELECT 
                CONCAT(r_score, f_score, m_score) as rfm_cell,
                COUNT(*) as customer_count
            FROM rfm_scores
            GROUP BY CONCAT(r_score, f_score, m_score)
        )
        SELECT 
            rfm_cell,
            customer_count,
            ROUND(customer_count * 100.0 / SUM(customer_count) OVER(), 2) as percentage
        FROM rfm_combined
        ORDER BY customer_count DESC
        LIMIT 15;
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            rfm_segments = []
            for row in results:
                rfm_segments.append({
                    "rfm_cell": row[0],
                    "customer_count": row[1],
                    "percentage": float(row[2]) if row[2] else 0
                })
            analyses["rfm_segments"] = rfm_segments
        
        # 2. Customer clusters by spending behavior
        query = f"""
        SELECT 
            CASE 
                WHEN CAST(income AS DECIMAL) < 30000 THEN 'Low Income'
                WHEN CAST(income AS DECIMAL) BETWEEN 30000 AND 70000 THEN 'Middle Income'
                WHEN CAST(income AS DECIMAL) > 70000 THEN 'High Income'
                ELSE 'Unknown'
            END as income_segment,
            CASE 
                WHEN CAST(mntwines AS DECIMAL) > 500 THEN 'High Wine Spender'
                WHEN CAST(mntwines AS DECIMAL) > 100 THEN 'Medium Wine Spender'
                ELSE 'Low Wine Spender'
            END as wine_segment,
            COUNT(*) as customer_count
        FROM {self.full_table_name}
        WHERE income IS NOT NULL AND income != ''
          AND mntwines IS NOT NULL AND mntwines != ''
        GROUP BY 
            CASE 
                WHEN CAST(income AS DECIMAL) < 30000 THEN 'Low Income'
                WHEN CAST(income AS DECIMAL) BETWEEN 30000 AND 70000 THEN 'Middle Income'
                WHEN CAST(income AS DECIMAL) > 70000 THEN 'High Income'
                ELSE 'Unknown'
            END,
            CASE 
                WHEN CAST(mntwines AS DECIMAL) > 500 THEN 'High Wine Spender'
                WHEN CAST(mntwines AS DECIMAL) > 100 THEN 'Medium Wine Spender'
                ELSE 'Low Wine Spender'
            END
        ORDER BY customer_count DESC;
        """
        
        columns, results = self.db.execute_query(query)
        if results:
            spending_clusters = []
            for row in results:
                spending_clusters.append({
                    "income_segment": row[0],
                    "wine_segment": row[1],
                    "customer_count": row[2]
                })
            analyses["spending_clusters"] = spending_clusters
        
        self.results["segmentation_analysis"] = analyses
        return True
    
    def analyze_data_quality(self):
        """Analyze data quality issues"""
        print("[INFO] Analyzing data quality...")
        
        analyses = {}
        
        # 1. Null value analysis
        null_analysis = {}
        for category, columns in self.column_categories.items():
            for column in columns:
                query = f"""
                SELECT 
                    COUNT(*) as total_rows,
                    SUM(CASE WHEN {column} IS NULL OR {column} = '' THEN 1 ELSE 0 END) as null_or_empty,
                    ROUND(SUM(CASE WHEN {column} IS NULL OR {column} = '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as null_percentage
                FROM {self.full_table_name};
                """
                
                columns_result, results = self.db.execute_query(query)
                if results:
                    null_analysis[column] = {
                        "total_rows": results[0][0],
                        "null_or_empty": results[0][1],
                        "null_percentage": float(results[0][2]) if results[0][2] else 0
                    }
        
        analyses["null_analysis"] = null_analysis
        
        # 2. Data consistency checks
        consistency_checks = []
        
        # Check for negative values in numeric columns
        numeric_columns = ['income', 'mntwines', 'mntfruits', 'mntmeatproducts', 
                          'mntfishproducts', 'mntsweetproducts', 'mntgoldprods']
        
        for column in numeric_columns:
            query = f"""
            SELECT COUNT(*) as negative_count
            FROM {self.full_table_name}
            WHERE CAST({column} AS DECIMAL) < 0;
            """
            
            columns_result, results = self.db.execute_query(query)
            if results:
                if results[0][0] > 0:
                    consistency_checks.append({
                        "check": f"Negative values in {column}",
                        "issue": f"Found {results[0][0]} negative values",
                        "severity": "High"
                    })
        
        # Check for unrealistic birth years
        query = f"""
        SELECT COUNT(*) as unrealistic_birth_years
        FROM {self.full_table_name}
        WHERE CAST(year_birth AS INTEGER) < 1900 OR CAST(year_birth AS INTEGER) > 2005;
        """
        
        columns_result, results = self.db.execute_query(query)
        if results and results[0][0] > 0:
            consistency_checks.append({
                "check": "Unrealistic birth years",
                "issue": f"Found {results[0][0]} unrealistic birth years",
                "severity": "Medium"
            })
        
        analyses["consistency_checks"] = consistency_checks
        
        self.results["data_quality"] = analyses
        return True
    
    def generate_insights(self):
        """Generate business insights from analysis"""
        print("[INFO] Generating business insights...")
        
        insights = {
            "demographic_insights": [],
            "purchase_insights": [],
            "campaign_insights": [],
            "segmentation_insights": [],
            "recommendations": []
        }
        
        # Demographic insights
        if "demographic_analysis" in self.results:
            demo = self.results["demographic_analysis"]
            
            if "income_analysis" in demo:
                income = demo["income_analysis"]
                avg_income = income.get("avg_income", 0)
                insights["demographic_insights"].append(
                    f"Average customer income: ${avg_income:,.2f}"
                )
            
            if "education_distribution" in demo:
                edu_data = demo["education_distribution"]
                if edu_data:
                    top_edu = edu_data[0]
                    insights["demographic_insights"].append(
                        f"Most common education level: {top_edu['education']} ({top_edu['percentage']}%)"
                    )
        
        # Purchase insights
        if "purchase_analysis" in self.results:
            purchase = self.results["purchase_analysis"]
            
            if "purchase_totals" in purchase:
                totals = purchase["purchase_totals"]
                max_category = max([
                    ("Wines", totals.get("total_wines", 0)),
                    ("Fruits", totals.get("total_fruits", 0)),
                    ("Meat", totals.get("total_meat", 0)),
                    ("Fish", totals.get("total_fish", 0)),
                    ("Sweets", totals.get("total_sweets", 0)),
                    ("Gold", totals.get("total_gold", 0))
                ], key=lambda x: x[1])
                
                insights["purchase_insights"].append(
                    f"Highest revenue category: {max_category[0]} (${max_category[1]:,.2f})"
                )
        
        # Campaign insights
        if "campaign_analysis" in self.results:
            campaign = self.results["campaign_analysis"]
            
            if "overall_response" in campaign:
                response = campaign["overall_response"]
                insights["campaign_insights"].append(
                    f"Overall campaign response rate: {response.get('response_rate', 0)}%"
                )
        
        # Segmentation insights
        if "segmentation_analysis" in self.results:
            segmentation = self.results["segmentation_analysis"]
            
            if "rfm_segments" in segmentation:
                segments = segmentation["rfm_segments"]
                if segments:
                    top_segment = segments[0]
                    insights["segmentation_insights"].append(
                        f"Largest RFM segment: {top_segment['rfm_cell']} ({top_segment['percentage']}%)"
                    )
        
        # Generate recommendations
        insights["recommendations"].extend([
            "1. Focus marketing efforts on high-income customers (income > $70k) who show higher response rates",
            "2. Develop targeted campaigns for the largest RFM segments to maximize ROI",
            "3. Create bundled offers combining wine with complementary products (meat, sweets)",
            "4. Implement loyalty programs for frequent purchasers across all product categories",
            "5. Use demographic data to personalize marketing messages and improve engagement"
        ])
        
        self.results["insights"] = insights
        return True
    
    # ============================================================================
    # VISUALIZATION METHODS
    # ============================================================================
    
    def create_demographic_visualizations(self):
        """Create demographic visualizations"""
        print("[INFO] Creating demographic visualizations...")
        
        try:
            # 1. Age Distribution Histogram
            query = f"""
            SELECT CAST(year_birth AS INTEGER) as birth_year
            FROM {self.full_table_name}
            WHERE year_birth IS NOT NULL AND year_birth != '';
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                ages = [2026 - int(row[0]) for row in results]  # Calculate age from birth year
                
                plt.figure(figsize=(12, 6))
                plt.hist(ages, bins=20, edgecolor='black', alpha=0.7, color='skyblue')
                plt.title('Customer Age Distribution', fontsize=16, fontweight='bold')
                plt.xlabel('Age', fontsize=12)
                plt.ylabel('Number of Customers', fontsize=12)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                age_plot_path = os.path.join(PLOT_SUBDIRS["demographic"], "age_distribution.png")
                plt.savefig(age_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Age distribution plot saved: {age_plot_path}")
            
            # 2. Income Distribution Box Plot
            query = f"""
            SELECT CAST(income AS DECIMAL) as income
            FROM {self.full_table_name}
            WHERE income IS NOT NULL AND income != '';
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                incomes = [float(row[0]) for row in results]
                
                plt.figure(figsize=(10, 6))
                plt.boxplot(incomes, vert=True, patch_artist=True, 
                           boxprops=dict(facecolor='lightgreen'))
                plt.title('Customer Income Distribution', fontsize=16, fontweight='bold')
                plt.ylabel('Income ($)', fontsize=12)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                income_plot_path = os.path.join(PLOT_SUBDIRS["demographic"], "income_distribution.png")
                plt.savefig(income_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Income distribution plot saved: {income_plot_path}")
            
            # 3. Education Distribution Bar Chart
            query = f"""
            SELECT 
                education,
                COUNT(*) as count
            FROM {self.full_table_name}
            WHERE education IS NOT NULL AND education != ''
            GROUP BY education
            ORDER BY count DESC;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                education_labels = [row[0] for row in results]
                education_counts = [row[1] for row in results]
                
                plt.figure(figsize=(12, 6))
                bars = plt.bar(education_labels, education_counts, color='coral', alpha=0.7)
                plt.title('Education Level Distribution', fontsize=16, fontweight='bold')
                plt.xlabel('Education Level', fontsize=12)
                plt.ylabel('Number of Customers', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add count labels on bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                            f'{int(height)}', ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                
                edu_plot_path = os.path.join(PLOT_SUBDIRS["demographic"], "education_distribution.png")
                plt.savefig(edu_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Education distribution plot saved: {edu_plot_path}")
            
            # 4. Marital Status Pie Chart
            query = f"""
            SELECT 
                marital_status,
                COUNT(*) as count
            FROM {self.full_table_name}
            WHERE marital_status IS NOT NULL AND marital_status != ''
            GROUP BY marital_status
            ORDER BY count DESC;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                marital_labels = [row[0] for row in results]
                marital_counts = [row[1] for row in results]
                
                plt.figure(figsize=(10, 8))
                colors = plt.cm.Set3(np.linspace(0, 1, len(marital_labels)))
                wedges, texts, autotexts = plt.pie(marital_counts, labels=marital_labels, 
                                                  autopct='%1.1f%%', startangle=90,
                                                  colors=colors, textprops={'fontsize': 11})
                
                plt.title('Marital Status Distribution', fontsize=16, fontweight='bold')
                plt.axis('equal')
                plt.tight_layout()
                
                marital_plot_path = os.path.join(PLOT_SUBDIRS["demographic"], "marital_status_distribution.png")
                plt.savefig(marital_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Marital status plot saved: {marital_plot_path}")
            
            return True
            
        except Exception as e:
            print(f"  [ERROR] Demographic visualization failed: {e}")
            return False
    
    def create_purchase_behavior_visualizations(self):
        """Create purchase behavior visualizations"""
        print("[INFO] Creating purchase behavior visualizations...")
        
        try:
            # 1. Purchase Categories Bar Chart
            query = f"""
            SELECT 
                ROUND(AVG(CAST(mntwines AS DECIMAL)), 2) as avg_wines,
                ROUND(AVG(CAST(mntfruits AS DECIMAL)), 2) as avg_fruits,
                ROUND(AVG(CAST(mntmeatproducts AS DECIMAL)), 2) as avg_meat,
                ROUND(AVG(CAST(mntfishproducts AS DECIMAL)), 2) as avg_fish,
                ROUND(AVG(CAST(mntsweetproducts AS DECIMAL)), 2) as avg_sweets,
                ROUND(AVG(CAST(mntgoldprods AS DECIMAL)), 2) as avg_gold
            FROM {self.full_table_name}
            WHERE mntwines IS NOT NULL AND mntwines != '';
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                categories = ['Wines', 'Fruits', 'Meat', 'Fish', 'Sweets', 'Gold']
                values = [float(results[0][i]) for i in range(6)]
                
                plt.figure(figsize=(12, 6))
                bars = plt.bar(categories, values, color='gold', alpha=0.7, edgecolor='darkorange')
                plt.title('Average Spending by Product Category', fontsize=16, fontweight='bold')
                plt.xlabel('Product Category', fontsize=12)
                plt.ylabel('Average Spending ($)', fontsize=12)
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                            f'${height:,.2f}', ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                
                purchase_plot_path = os.path.join(PLOT_SUBDIRS["purchase_behavior"], "purchase_categories.png")
                plt.savefig(purchase_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Purchase categories plot saved: {purchase_plot_path}")
            
            # 2. Purchase Channels Bar Chart
            query = f"""
            SELECT 
                ROUND(AVG(CAST(numdealspurchases AS DECIMAL)), 2) as avg_deals,
                ROUND(AVG(CAST(numwebpurchases AS DECIMAL)), 2) as avg_web,
                ROUND(AVG(CAST(numcatalogpurchases AS DECIMAL)), 2) as avg_catalog,
                ROUND(AVG(CAST(numstorepurchases AS DECIMAL)), 2) as avg_store
            FROM {self.full_table_name}
            WHERE numdealspurchases IS NOT NULL AND numdealspurchases != '';
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                channels = ['Deals', 'Web', 'Catalog', 'Store']
                values = [float(results[0][i]) for i in range(4)]
                
                plt.figure(figsize=(10, 6))
                bars = plt.bar(channels, values, color='lightblue', alpha=0.7, edgecolor='darkblue')
                plt.title('Average Purchases by Channel', fontsize=16, fontweight='bold')
                plt.xlabel('Purchase Channel', fontsize=12)
                plt.ylabel('Average Number of Purchases', fontsize=12)
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{height:.2f}', ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                
                channel_plot_path = os.path.join(PLOT_SUBDIRS["purchase_behavior"], "purchase_channels.png")
                plt.savefig(channel_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Purchase channels plot saved: {channel_plot_path}")
            
            # 3. Total Spending vs Income Scatter Plot
            query = f"""
            SELECT 
                CAST(income AS DECIMAL) as income,
                (CAST(mntwines AS DECIMAL) + CAST(mntfruits AS DECIMAL) + 
                 CAST(mntmeatproducts AS DECIMAL) + CAST(mntfishproducts AS DECIMAL) +
                 CAST(mntsweetproducts AS DECIMAL) + CAST(mntgoldprods AS DECIMAL)) as total_spending
            FROM {self.full_table_name}
            WHERE income IS NOT NULL AND income != '' 
            AND mntwines IS NOT NULL AND mntwines != ''
            LIMIT 500;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                incomes = [float(row[0]) for row in results]
                total_spending = [float(row[1]) for row in results]
                
                plt.figure(figsize=(12, 8))
                plt.scatter(incomes, total_spending, alpha=0.6, color='purple', s=50)
                plt.title('Total Spending vs Income', fontsize=16, fontweight='bold')
                plt.xlabel('Income ($)', fontsize=12)
                plt.ylabel('Total Spending ($)', fontsize=12)
                plt.grid(True, alpha=0.3)
                
                # Add trend line
                if len(incomes) > 1:
                    z = np.polyfit(incomes, total_spending, 1)
                    p = np.poly1d(z)
                    plt.plot(incomes, p(incomes), "r--", alpha=0.8, linewidth=2, 
                            label=f'Trend: y={z[0]:.4f}x + {z[1]:.2f}')
                    plt.legend()
                
                plt.tight_layout()
                
                scatter_plot_path = os.path.join(PLOT_SUBDIRS["purchase_behavior"], "spending_vs_income.png")
                plt.savefig(scatter_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Spending vs income plot saved: {scatter_plot_path}")
            
            # 4. Recency Distribution Histogram
            query = f"""
            SELECT CAST(recency AS INTEGER) as recency
            FROM {self.full_table_name}
            WHERE recency IS NOT NULL AND recency != '';
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                recency_values = [int(row[0]) for row in results]
                
                plt.figure(figsize=(12, 6))
                plt.hist(recency_values, bins=20, edgecolor='black', alpha=0.7, color='lightgreen')
                plt.title('Days Since Last Purchase (Recency)', fontsize=16, fontweight='bold')
                plt.xlabel('Days Since Last Purchase', fontsize=12)
                plt.ylabel('Number of Customers', fontsize=12)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                recency_plot_path = os.path.join(PLOT_SUBDIRS["purchase_behavior"], "recency_distribution.png")
                plt.savefig(recency_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Recency distribution plot saved: {recency_plot_path}")
            
            return True
            
        except Exception as e:
            print(f"  [ERROR] Purchase behavior visualization failed: {e}")
            return False
    
    def create_campaign_response_visualizations(self):
        """Create campaign response visualizations"""
        print("[INFO] Creating campaign response visualizations...")
        
        try:
            # 1. Campaign Response Rates Bar Chart
            query = f"""
            SELECT 
                'Campaign 1' as campaign,
                ROUND(100.0 * SUM(CASE WHEN acceptedcmp1 = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) as response_rate
            FROM {self.full_table_name}
            WHERE acceptedcmp1 IS NOT NULL AND acceptedcmp1 != ''
            UNION ALL
            SELECT 
                'Campaign 2' as campaign,
                ROUND(100.0 * SUM(CASE WHEN acceptedcmp2 = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) as response_rate
            FROM {self.full_table_name}
            WHERE acceptedcmp2 IS NOT NULL AND acceptedcmp2 != ''
            UNION ALL
            SELECT 
                'Campaign 3' as campaign,
                ROUND(100.0 * SUM(CASE WHEN acceptedcmp3 = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) as response_rate
            FROM {self.full_table_name}
            WHERE acceptedcmp3 IS NOT NULL AND acceptedcmp3 != ''
            UNION ALL
            SELECT 
                'Campaign 4' as campaign,
                ROUND(100.0 * SUM(CASE WHEN acceptedcmp4 = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) as response_rate
            FROM {self.full_table_name}
            WHERE acceptedcmp4 IS NOT NULL AND acceptedcmp4 != ''
            UNION ALL
            SELECT 
                'Campaign 5' as campaign,
                ROUND(100.0 * SUM(CASE WHEN acceptedcmp5 = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) as response_rate
            FROM {self.full_table_name}
            WHERE acceptedcmp5 IS NOT NULL AND acceptedcmp5 != ''
            UNION ALL
            SELECT 
                'Last Campaign' as campaign,
                ROUND(100.0 * SUM(CASE WHEN response = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) as response_rate
            FROM {self.full_table_name}
            WHERE response IS NOT NULL AND response != ''
            ORDER BY response_rate DESC;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                campaigns = [row[0] for row in results]
                response_rates = [float(row[1]) for row in results]
                
                plt.figure(figsize=(14, 8))
                bars = plt.bar(campaigns, response_rates, color='salmon', alpha=0.7, edgecolor='darkred')
                plt.title('Campaign Response Rates', fontsize=16, fontweight='bold')
                plt.xlabel('Campaign', fontsize=12)
                plt.ylabel('Response Rate (%)', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{height:.2f}%', ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                
                campaign_plot_path = os.path.join(PLOT_SUBDIRS["campaign_response"], "campaign_response_rates.png")
                plt.savefig(campaign_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Campaign response rates plot saved: {campaign_plot_path}")
            
            # 2. Campaign Response by Income Level
            query = f"""
            WITH income_groups AS (
                SELECT 
                    CASE 
                        WHEN CAST(income AS DECIMAL) < 30000 THEN 'Low (<30k)'
                        WHEN CAST(income AS DECIMAL) BETWEEN 30000 AND 70000 THEN 'Medium (30k-70k)'
                        WHEN CAST(income AS DECIMAL) > 70000 THEN 'High (>70k)'
                        ELSE 'Unknown'
                    END as income_group,
                    CASE WHEN response = '1' THEN 1 ELSE 0 END as responded
                FROM {self.full_table_name}
                WHERE income IS NOT NULL AND income != '' 
                AND response IS NOT NULL AND response != ''
            )
            SELECT 
                income_group,
                COUNT(*) as total_customers,
                SUM(responded) as responders,
                ROUND(100.0 * SUM(responded) / COUNT(*), 2) as response_rate
            FROM income_groups
            WHERE income_group != 'Unknown'
            GROUP BY income_group
            ORDER BY response_rate DESC;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                income_groups = [row[0] for row in results]
                response_rates = [float(row[3]) for row in results]
                
                plt.figure(figsize=(12, 6))
                bars = plt.bar(income_groups, response_rates, color='lightcoral', alpha=0.7, edgecolor='darkred')
                plt.title('Campaign Response Rate by Income Group', fontsize=16, fontweight='bold')
                plt.xlabel('Income Group', fontsize=12)
                plt.ylabel('Response Rate (%)', fontsize=12)
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{height:.2f}%', ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                
                income_response_plot_path = os.path.join(PLOT_SUBDIRS["campaign_response"], "response_by_income.png")
                plt.savefig(income_response_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Response by income plot saved: {income_response_plot_path}")
            
            # 3. Complaints Analysis
            query = f"""
            SELECT 
                complain,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM {self.full_table_name}
            WHERE complain IS NOT NULL AND complain != ''
            GROUP BY complain
            ORDER BY complain;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                complaint_labels = ['No Complaint', 'Complaint'] if len(results) == 2 else [str(row[0]) for row in results]
                complaint_counts = [row[1] for row in results]
                
                plt.figure(figsize=(10, 8))
                colors = ['lightgreen', 'lightcoral']
                wedges, texts, autotexts = plt.pie(complaint_counts, labels=complaint_labels, 
                                                  autopct='%1.1f%%', startangle=90,
                                                  colors=colors[:len(complaint_counts)], 
                                                  textprops={'fontsize': 11})
                
                plt.title('Customer Complaints Distribution', fontsize=16, fontweight='bold')
                plt.axis('equal')
                plt.tight_layout()
                
                complaint_plot_path = os.path.join(PLOT_SUBDIRS["campaign_response"], "complaints_distribution.png")
                plt.savefig(complaint_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Complaints distribution plot saved: {complaint_plot_path}")
            
            return True
            
        except Exception as e:
            print(f"  [ERROR] Campaign response visualization failed: {e}")
            return False
    
    def create_correlation_visualizations(self):
        """Create correlation visualizations"""
        print("[INFO] Creating correlation visualizations...")
        
        try:
            # 1. Correlation Heatmap
            query = f"""
            SELECT 
                CAST(income AS DECIMAL) as income,
                CAST(mntwines AS DECIMAL) as wines,
                CAST(mntfruits AS DECIMAL) as fruits,
                CAST(mntmeatproducts AS DECIMAL) as meat,
                CAST(mntfishproducts AS DECIMAL) as fish,
                CAST(mntsweetproducts AS DECIMAL) as sweets,
                CAST(mntgoldprods AS DECIMAL) as gold,
                CAST(numwebpurchases AS DECIMAL) as web_purchases,
                CAST(numstorepurchases AS DECIMAL) as store_purchases,
                CAST(recency AS INTEGER) as recency
            FROM {self.full_table_name}
            WHERE income IS NOT NULL AND income != ''
            AND mntwines IS NOT NULL AND mntwines != ''
            LIMIT 1000;
            """
            
            columns, results = self.db.execute_query(query)
            if results and len(results) > 10:
                # Convert to DataFrame for correlation calculation
                data = []
                for row in results:
                    data.append([float(val) if val is not None else 0.0 for val in row])
                
                df = pd.DataFrame(data, columns=[
                    'income', 'wines', 'fruits', 'meat', 'fish', 'sweets', 
                    'gold', 'web_purchases', 'store_purchases', 'recency'
                ])
                
                # Calculate correlation matrix
                correlation_matrix = df.corr()
                
                plt.figure(figsize=(14, 10))
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', 
                           center=0, square=True, linewidths=1, 
                           cbar_kws={"shrink": 0.8}, fmt='.2f')
                plt.title('Correlation Heatmap of Key Variables', fontsize=16, fontweight='bold')
                plt.tight_layout()
                
                heatmap_plot_path = os.path.join(PLOT_SUBDIRS["correlations"], "correlation_heatmap.png")
                plt.savefig(heatmap_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Correlation heatmap saved: {heatmap_plot_path}")
            
            # 2. Income vs Wine Spending Scatter Plot
            query = f"""
            SELECT 
                CAST(income AS DECIMAL) as income,
                CAST(mntwines AS DECIMAL) as wine_spending
            FROM {self.full_table_name}
            WHERE income IS NOT NULL AND income != ''
            AND mntwines IS NOT NULL AND mntwines != ''
            LIMIT 500;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                incomes = [float(row[0]) for row in results]
                wine_spending = [float(row[1]) for row in results]
                
                plt.figure(figsize=(12, 8))
                plt.scatter(incomes, wine_spending, alpha=0.6, color='darkred', s=50)
                plt.title('Income vs Wine Spending', fontsize=16, fontweight='bold')
                plt.xlabel('Income ($)', fontsize=12)
                plt.ylabel('Wine Spending ($)', fontsize=12)
                plt.grid(True, alpha=0.3)
                
                # Add trend line
                if len(incomes) > 1:
                    z = np.polyfit(incomes, wine_spending, 1)
                    p = np.poly1d(z)
                    plt.plot(incomes, p(incomes), "b--", alpha=0.8, linewidth=2, 
                            label=f'Trend: y={z[0]:.4f}x + {z[1]:.2f}')
                    plt.legend()
                
                plt.tight_layout()
                
                wine_corr_plot_path = os.path.join(PLOT_SUBDIRS["correlations"], "income_vs_wine_spending.png")
                plt.savefig(wine_corr_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Income vs wine spending plot saved: {wine_corr_plot_path}")
            
            # 3. Family Size vs Total Spending
            query = f"""
            SELECT 
                (CAST(kidhome AS INTEGER) + CAST(teenhome AS INTEGER)) as family_size,
                (CAST(mntwines AS DECIMAL) + CAST(mntfruits AS DECIMAL) + 
                 CAST(mntmeatproducts AS DECIMAL) + CAST(mntfishproducts AS DECIMAL) +
                 CAST(mntsweetproducts AS DECIMAL) + CAST(mntgoldprods AS DECIMAL)) as total_spending
            FROM {self.full_table_name}
            WHERE kidhome IS NOT NULL AND kidhome != ''
            AND teenhome IS NOT NULL AND teenhome != ''
            AND mntwines IS NOT NULL AND mntwines != ''
            LIMIT 500;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                family_sizes = [int(row[0]) for row in results]
                total_spending = [float(row[1]) for row in results]
                
                plt.figure(figsize=(12, 8))
                plt.scatter(family_sizes, total_spending, alpha=0.6, color='darkgreen', s=50)
                plt.title('Family Size vs Total Spending', fontsize=16, fontweight='bold')
                plt.xlabel('Family Size (Kids + Teens)', fontsize=12)
                plt.ylabel('Total Spending ($)', fontsize=12)
                plt.grid(True, alpha=0.3)
                
                # Add trend line
                if len(family_sizes) > 1:
                    z = np.polyfit(family_sizes, total_spending, 1)
                    p = np.poly1d(z)
                    plt.plot(family_sizes, p(family_sizes), "r--", alpha=0.8, linewidth=2, 
                            label=f'Trend: y={z[0]:.4f}x + {z[1]:.2f}')
                    plt.legend()
                
                plt.tight_layout()
                
                family_corr_plot_path = os.path.join(PLOT_SUBDIRS["correlations"], "family_size_vs_spending.png")
                plt.savefig(family_corr_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Family size vs spending plot saved: {family_corr_plot_path}")
            
            return True
            
        except Exception as e:
            print(f"  [ERROR] Correlation visualization failed: {e}")
            return False
    
    def create_segmentation_visualizations(self):
        """Create segmentation visualizations"""
        print("[INFO] Creating segmentation visualizations...")
        
        try:
            # 1. RFM Segmentation Distribution
            query = f"""
            WITH rfm_data AS (
                SELECT 
                    CASE 
                        WHEN CAST(recency AS INTEGER) <= 30 THEN 'High'
                        WHEN CAST(recency AS INTEGER) <= 60 THEN 'Medium'
                        ELSE 'Low'
                    END as recency_score,
                    CASE 
                        WHEN (CAST(numwebpurchases AS INTEGER) + CAST(numstorepurchases AS INTEGER) + 
                              CAST(numcatalogpurchases AS INTEGER) + CAST(numdealspurchases AS INTEGER)) > 10 THEN 'High'
                        WHEN (CAST(numwebpurchases AS INTEGER) + CAST(numstorepurchases AS INTEGER) + 
                              CAST(numcatalogpurchases AS INTEGER) + CAST(numdealspurchases AS INTEGER)) > 5 THEN 'Medium'
                        ELSE 'Low'
                    END as frequency_score,
                    CASE 
                        WHEN (CAST(mntwines AS DECIMAL) + CAST(mntfruits AS DECIMAL) + 
                              CAST(mntmeatproducts AS DECIMAL) + CAST(mntfishproducts AS DECIMAL) +
                              CAST(mntsweetproducts AS DECIMAL) + CAST(mntgoldprods AS DECIMAL)) > 1000 THEN 'High'
                        WHEN (CAST(mntwines AS DECIMAL) + CAST(mntfruits AS DECIMAL) + 
                              CAST(mntmeatproducts AS DECIMAL) + CAST(mntfishproducts AS DECIMAL) +
                              CAST(mntsweetproducts AS DECIMAL) + CAST(mntgoldprods AS DECIMAL)) > 500 THEN 'Medium'
                        ELSE 'Low'
                    END as monetary_score
                FROM {self.full_table_name}
                WHERE recency IS NOT NULL AND recency != ''
                AND mntwines IS NOT NULL AND mntwines != ''
            ),
            rfm_segments AS (
                SELECT 
                    CONCAT(recency_score, '-', frequency_score, '-', monetary_score) as rfm_cell,
                    COUNT(*) as count
                FROM rfm_data
                GROUP BY CONCAT(recency_score, '-', frequency_score, '-', monetary_score)
                ORDER BY count DESC
                LIMIT 10
            )
            SELECT 
                rfm_cell,
                count,
                ROUND(100.0 * count / SUM(count) OVER(), 2) as percentage
            FROM rfm_segments;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                segments = [row[0] for row in results]
                segment_counts = [row[1] for row in results]
                
                plt.figure(figsize=(14, 8))
                bars = plt.bar(segments, segment_counts, color='lightblue', alpha=0.7, edgecolor='darkblue')
                plt.title('Top 10 RFM Segments Distribution', fontsize=16, fontweight='bold')
                plt.xlabel('RFM Segment (Recency-Frequency-Monetary)', fontsize=12)
                plt.ylabel('Number of Customers', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                            f'{int(height)}', ha='center', va='bottom', fontsize=9)
                
                plt.tight_layout()
                
                rfm_plot_path = os.path.join(PLOT_SUBDIRS["segmentation"], "rfm_segments.png")
                plt.savefig(rfm_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] RFM segments plot saved: {rfm_plot_path}")
            
            # 2. Income Segmentation
            query = f"""
            WITH income_data AS (
                SELECT 
                    CASE 
                        WHEN CAST(income AS DECIMAL) < 30000 THEN 'Low (<30k)'
                        WHEN CAST(income AS DECIMAL) BETWEEN 30000 AND 50000 THEN 'Lower-Middle (30k-50k)'
                        WHEN CAST(income AS DECIMAL) BETWEEN 50000 AND 70000 THEN 'Upper-Middle (50k-70k)'
                        WHEN CAST(income AS DECIMAL) BETWEEN 70000 AND 100000 THEN 'High (70k-100k)'
                        WHEN CAST(income AS DECIMAL) > 100000 THEN 'Very High (>100k)'
                        ELSE 'Unknown'
                    END as income_segment
                FROM {self.full_table_name}
                WHERE income IS NOT NULL AND income != ''
            )
            SELECT 
                income_segment,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM income_data
            WHERE income_segment != 'Unknown'
            GROUP BY income_segment
            ORDER BY 
                CASE income_segment
                    WHEN 'Low (<30k)' THEN 1
                    WHEN 'Lower-Middle (30k-50k)' THEN 2
                    WHEN 'Upper-Middle (50k-70k)' THEN 3
                    WHEN 'High (70k-100k)' THEN 4
                    WHEN 'Very High (>100k)' THEN 5
                    ELSE 6
                END;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                income_segments = [row[0] for row in results]
                segment_counts = [row[1] for row in results]
                
                plt.figure(figsize=(12, 8))
                colors = ['lightcoral', 'lightsalmon', 'gold', 'lightgreen', 'lightblue']
                wedges, texts, autotexts = plt.pie(segment_counts, labels=income_segments, 
                                                  autopct='%1.1f%%', startangle=90,
                                                  colors=colors[:len(income_segments)], 
                                                  textprops={'fontsize': 10})
                
                plt.title('Customer Distribution by Income Segment', fontsize=16, fontweight='bold')
                plt.axis('equal')
                plt.tight_layout()
                
                income_seg_plot_path = os.path.join(PLOT_SUBDIRS["segmentation"], "income_segments.png")
                plt.savefig(income_seg_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Income segments plot saved: {income_seg_plot_path}")
            
            # 3. Education Level Segmentation
            query = f"""
            SELECT 
                education,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM {self.full_table_name}
            WHERE education IS NOT NULL AND education != ''
            GROUP BY education
            ORDER BY count DESC;
            """
            
            columns, results = self.db.execute_query(query)
            if results:
                education_levels = [row[0] for row in results]
                education_counts = [row[1] for row in results]
                
                plt.figure(figsize=(12, 6))
                bars = plt.bar(education_levels, education_counts, color='lightpink', alpha=0.7, edgecolor='darkred')
                plt.title('Customer Distribution by Education Level', fontsize=16, fontweight='bold')
                plt.xlabel('Education Level', fontsize=12)
                plt.ylabel('Number of Customers', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                            f'{int(height)}', ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                
                education_seg_plot_path = os.path.join(PLOT_SUBDIRS["segmentation"], "education_segments.png")
                plt.savefig(education_seg_plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] Education segments plot saved: {education_seg_plot_path}")
            
            return True
            
        except Exception as e:
            print(f"  [ERROR] Segmentation visualization failed: {e}")
            return False
    
    def create_summary_file(self):
        """Create comprehensive summary.txt file with every tiny detail"""
        print("[INFO] Creating comprehensive summary.txt file...")
        
        try:
            with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 80 + "\n")
                f.write("CUSTOMER PERSONALITY ANALYSIS - MAXIMUM EDA SUMMARY\n")
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
                    col_count = structure.get('column_count', 'N/A')
                    
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
                    
                    if "age_analysis" in demo:
                        age = demo["age_analysis"]
                        f.write("Age Analysis:\n")
                        avg_age = age.get('avg_age', 'N/A')
                        min_age = age.get('min_age', 'N/A')
                        max_age = age.get('max_age', 'N/A')
                        
                        if isinstance(avg_age, (int, float)):
                            f.write(f"  - Average Age: {avg_age:.1f} years\n")
                        else:
                            f.write(f"  - Average Age: {avg_age} years\n")
                        
                        f.write(f"  - Minimum Age: {min_age} years\n")
                        f.write(f"  - Maximum Age: {max_age} years\n")
                    
                    if "income_analysis" in demo:
                        income = demo["income_analysis"]
                        f.write("\nIncome Analysis:\n")
                        avg_income = income.get('avg_income', 'N/A')
                        min_income = income.get('min_income', 'N/A')
                        max_income = income.get('max_income', 'N/A')
                        
                        if isinstance(avg_income, (int, float)):
                            f.write(f"  - Average Income: ${avg_income:,.2f}\n")
                        else:
                            f.write(f"  - Average Income: ${avg_income}\n")
                        
                        if isinstance(min_income, (int, float)):
                            f.write(f"  - Minimum Income: ${min_income:,.2f}\n")
                        else:
                            f.write(f"  - Minimum Income: ${min_income}\n")
                        
                        if isinstance(max_income, (int, float)):
                            f.write(f"  - Maximum Income: ${max_income:,.2f}\n")
                        else:
                            f.write(f"  - Maximum Income: ${max_income}\n")
                    
                    if "education_distribution" in demo:
                        f.write("\nEducation Distribution:\n")
                        for edu in demo["education_distribution"]:
                            count = edu.get('count', 'N/A')
                            percentage = edu.get('percentage', 'N/A')
                            
                            if isinstance(count, (int, float)):
                                f.write(f"  - {edu['education']}: {count:,} customers ")
                            else:
                                f.write(f"  - {edu['education']}: {count} customers ")
                            
                            f.write(f"({percentage}%)\n")
                    
                    if "marital_status_distribution" in demo:
                        f.write("\nMarital Status Distribution:\n")
                        for marital in demo["marital_status_distribution"]:
                            count = marital.get('count', 'N/A')
                            percentage = marital.get('percentage', 'N/A')
                            
                            if isinstance(count, (int, float)):
                                f.write(f"  - {marital['marital_status']}: {count:,} customers ")
                            else:
                                f.write(f"  - {marital['marital_status']}: {count} customers ")
                            
                            f.write(f"({percentage}%)\n")
                f.write("\n")
                
                # 3. Purchase Behavior Analysis
                f.write("3. PURCHASE BEHAVIOR ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "purchase_analysis" in self.results:
                    purchase = self.results["purchase_analysis"]
                    
                    if "purchase_totals" in purchase:
                        totals = purchase["purchase_totals"]
                        f.write("Total Spending by Category:\n")
                        
                        # Helper function to format currency
                        def format_currency(value, default='N/A'):
                            if isinstance(value, (int, float)):
                                return f"${value:,.2f}"
                            else:
                                return f"${default}"
                        
                        f.write(f"  - Wines: {format_currency(totals.get('total_wines', 'N/A'))}\n")
                        f.write(f"  - Fruits: {format_currency(totals.get('total_fruits', 'N/A'))}\n")
                        f.write(f"  - Meat: {format_currency(totals.get('total_meat', 'N/A'))}\n")
                        f.write(f"  - Fish: {format_currency(totals.get('total_fish', 'N/A'))}\n")
                        f.write(f"  - Sweets: {format_currency(totals.get('total_sweets', 'N/A'))}\n")
                        f.write(f"  - Gold: {format_currency(totals.get('total_gold', 'N/A'))}\n")
                        f.write(f"  - GRAND TOTAL: {format_currency(totals.get('grand_total', 'N/A'))}\n")
                    
                    if "purchase_channels" in purchase:
                        channels = purchase["purchase_channels"]
                        f.write("\nPurchase Channels:\n")
                        
                        # Helper function to format counts
                        def format_count(value, default='N/A'):
                            if isinstance(value, (int, float)):
                                return f"{value:,.0f}"
                            else:
                                return f"{default}"
                        
                        f.write(f"  - Web Purchases: {format_count(channels.get('total_web', 'N/A'))}\n")
                        f.write(f"  - Store Purchases: {format_count(channels.get('total_store', 'N/A'))}\n")
                        f.write(f"  - Catalog Purchases: {format_count(channels.get('total_catalog', 'N/A'))}\n")
                        f.write(f"  - Deal Purchases: {format_count(channels.get('total_deals', 'N/A'))}\n")
                        f.write(f"  - TOTAL PURCHASES: {format_count(channels.get('total_purchases', 'N/A'))}\n")
                f.write("\n")
                
                # 4. Campaign Response Analysis
                f.write("4. CAMPAIGN RESPONSE ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "campaign_analysis" in self.results:
                    campaign = self.results["campaign_analysis"]
                    
                    if "campaign_response_rates" in campaign:
                        f.write("Campaign Response Rates:\n")
                        for cmp in campaign["campaign_response_rates"]:
                            responders = cmp.get('responders', 'N/A')
                            total_customers = cmp.get('total_customers', 'N/A')
                            
                            if isinstance(responders, (int, float)) and isinstance(total_customers, (int, float)):
                                f.write(f"  - {cmp['campaign']}: {cmp['response_rate']}% "
                                       f"({responders:,} out of {total_customers:,})\n")
                            else:
                                f.write(f"  - {cmp['campaign']}: {cmp['response_rate']}% "
                                       f"({responders} out of {total_customers})\n")
                    
                    if "overall_response" in campaign:
                        response = campaign["overall_response"]
                        f.write(f"\nOverall Last Campaign Response: {response.get('response_rate', 'N/A')}%\n")
                        
                        responders = response.get('responders', 'N/A')
                        non_responders = response.get('non_responders', 'N/A')
                        
                        if isinstance(responders, (int, float)):
                            f.write(f"  - Responders: {responders:,}\n")
                        else:
                            f.write(f"  - Responders: {responders}\n")
                        
                        if isinstance(non_responders, (int, float)):
                            f.write(f"  - Non-Responders: {non_responders:,}\n")
                        else:
                            f.write(f"  - Non-Responders: {non_responders}\n")
                f.write("\n")
                
                # 5. Correlation Analysis
                f.write("5. CORRELATION ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "correlation_analysis" in self.results:
                    corr = self.results["correlation_analysis"]
                    
                    if "income_spending_correlation" in corr:
                        income_corr = corr["income_spending_correlation"]
                        f.write("Income vs Spending Correlations:\n")
                        for item in income_corr:
                            f.write(f"  - {item['category']}: Correlation = {item['correlation']:.3f}\n")
                    
                    if "campaign_correlations" in corr:
                        campaign_corr = corr["campaign_correlations"]
                        f.write("\nCampaign Response Correlations:\n")
                        for item in campaign_corr:
                            f.write(f"  - {item['variable']}: Correlation = {item['correlation']:.3f}\n")
                f.write("\n")
                
                # 6. Segmentation Analysis
                f.write("6. SEGMENTATION ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "segmentation_analysis" in self.results:
                    seg = self.results["segmentation_analysis"]
                    
                    if "rfm_segments" in seg:
                        f.write("Top RFM Segments:\n")
                        for segment in seg["rfm_segments"]:
                            count = segment.get('count', 'N/A')
                            
                            if isinstance(count, (int, float)):
                                f.write(f"  - {segment['rfm_cell']}: {count:,} customers ")
                            else:
                                f.write(f"  - {segment['rfm_cell']}: {count} customers ")
                            
                            f.write(f"({segment.get('percentage', 'N/A')}%)\n")
                    
                    if "income_segments" in seg:
                        f.write("\nIncome Segments:\n")
                        for segment in seg["income_segments"]:
                            count = segment.get('count', 'N/A')
                            
                            if isinstance(count, (int, float)):
                                f.write(f"  - {segment['income_segment']}: {count:,} customers ")
                            else:
                                f.write(f"  - {segment['income_segment']}: {count} customers ")
                            
                            f.write(f"({segment.get('percentage', 'N/A')}%)\n")
                f.write("\n")
                
                # 7. Data Quality Analysis
                f.write("7. DATA QUALITY ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if "data_quality" in self.results:
                    quality = self.results["data_quality"]
                    
                    if "null_analysis" in quality:
                        nulls = quality["null_analysis"]
                        f.write("Null Value Analysis:\n")
                        for col in nulls:
                            # Check if col is a dictionary
                            if isinstance(col, dict):
                                null_count = col.get('null_count', 0)
                                if null_count > 0:
                                    if isinstance(null_count, (int, float)):
                                        f.write(f"  - {col.get('column_name', 'N/A')}: {null_count:,} null values ")
                                    else:
                                        f.write(f"  - {col.get('column_name', 'N/A')}: {null_count} null values ")
                                    
                                    f.write(f"({col.get('null_percentage', 'N/A')}%)\n")
                            else:
                                # If col is not a dictionary, just write it as is
                                f.write(f"  - {col}\n")
                    
                    if "consistency_checks" in quality:
                        consistency = quality["consistency_checks"]
                        f.write("\nData Consistency Checks:\n")
                        for check in consistency:
                            # Check if check is a dictionary
                            if isinstance(check, dict):
                                f.write(f"  - {check.get('check_name', 'N/A')}: {check.get('result', 'N/A')}\n")
                            else:
                                # If check is not a dictionary, just write it as is
                                f.write(f"  - {check}\n")
                f.write("\n")
                
                # 8. Business Insights
                f.write("8. BUSINESS INSIGHTS AND RECOMMENDATIONS\n")
                f.write("-" * 40 + "\n")
                if "insights" in self.results:
                    insights = self.results["insights"]
                    
                    f.write("Key Demographic Insights:\n")
                    for insight in insights.get("demographic_insights", []):
                        f.write(f"  - {insight}\n")
                    
                    f.write("\nPurchase Behavior Insights:\n")
                    for insight in insights.get("purchase_insights", []):
                        f.write(f"  - {insight}\n")
                    
                    f.write("\nCampaign Performance Insights:\n")
                    for insight in insights.get("campaign_insights", []):
                        f.write(f"  - {insight}\n")
                    
                    f.write("\nCustomer Segmentation Insights:\n")
                    for insight in insights.get("segmentation_insights", []):
                        f.write(f"  - {insight}\n")
                    
                    f.write("\nStrategic Recommendations:\n")
                    for rec in insights.get("recommendations", []):
                        f.write(f"  {rec}\n")
                
                # 9. Generated Files
                f.write("\n" + "=" * 80 + "\n")
                f.write("9. GENERATED FILES\n")
                f.write("-" * 40 + "\n")
                f.write(f"Summary File: {SUMMARY_FILE}\n")
                f.write(f"Plots Directory: {PLOTS_DIR}\n")
                f.write(f"Data Directory: {DATA_DIR}\n")
                
                # List plot files
                f.write("\nGenerated Plots:\n")
                for category, subdir in PLOT_SUBDIRS.items():
                    if os.path.exists(subdir):
                        plot_files = [f for f in os.listdir(subdir) if f.endswith('.png')]
                        if plot_files:
                            f.write(f"  {category.replace('_', ' ').title()}:\n")
                            for plot_file in plot_files:
                                f.write(f"    - {plot_file}\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF MAXIMUM EDA SUMMARY\n")
                f.write("=" * 80 + "\n")
            
            print(f"  [SUCCESS] Comprehensive summary saved: {SUMMARY_FILE}")
            return True
            
        except Exception as e:
            print(f"  [ERROR] Summary file creation failed: {e}")
            return False
    
    def run_complete_analysis(self):
        """Run the complete maximum EDA analysis"""
        print("\n" + "=" * 80)
        print("CUSTOMER PERSONALITY ANALYSIS - MAXIMUM EDA")
        print("=" * 80)
        
        start_time = datetime.now()
        print(f"[START] Analysis started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all analysis methods
        analysis_steps = [
            ("Table Structure Analysis", self.analyze_table_structure),
            ("Demographic Analysis", self.analyze_demographics),
            ("Purchase Behavior Analysis", self.analyze_purchase_behavior),
            ("Campaign Response Analysis", self.analyze_campaign_response),
            ("Correlation Analysis", self.analyze_correlations),
            ("Segmentation Analysis", self.analyze_segmentation),
            ("Data Quality Analysis", self.analyze_data_quality),
            ("Insights Generation", self.generate_insights)
        ]
        
        # Execute analysis steps
        for step_name, step_method in analysis_steps:
            print(f"\n[STEP] {step_name}")
            if not step_method():
                print(f"  [WARNING] {step_name} failed or returned no results")
        
        # Create visualizations
        print("\n[STEP] Creating Visualizations")
        viz_steps = [
            ("Demographic Visualizations", self.create_demographic_visualizations),
            ("Purchase Behavior Visualizations", self.create_purchase_behavior_visualizations),
            ("Campaign Response Visualizations", self.create_campaign_response_visualizations),
            ("Correlation Visualizations", self.create_correlation_visualizations),
            ("Segmentation Visualizations", self.create_segmentation_visualizations)
        ]
        
        for viz_name, viz_method in viz_steps:
            print(f"  - {viz_name}")
            if not viz_method():
                print(f"    [WARNING] {viz_name} failed")
        
        # Create summary file
        print("\n[STEP] Creating Comprehensive Summary")
        if not self.create_summary_file():
            print("  [WARNING] Summary file creation failed")
        
        # Save results to JSON
        print("\n[STEP] Saving Analysis Results")
        try:
            stats_file = os.path.join(DATA_DIR, "statistics.json")
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"  [OK] Statistics saved: {stats_file}")
            
            insights_file = os.path.join(DATA_DIR, "insights.json")
            with open(insights_file, 'w', encoding='utf-8') as f:
                json.dump(self.results.get("insights", {}), f, indent=2, default=str)
            print(f"  [OK] Insights saved: {insights_file}")
        except Exception as e:
            print(f"  [ERROR] Failed to save JSON files: {e}")
        
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
        print("=" * 80)
        
        return True

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print("CUSTOMER PERSONALITY ANALYSIS - MAXIMUM EDA SCRIPT")
    print("=" * 80)
    
    # Create database connection
    db = DatabaseConnection()
    if not db.connect():
        print("[ERROR] Cannot proceed without database connection")
        return False
    
    try:
        # Create EDA analyzer
        eda = CustomerPersonalityMaxEDA(db)
        
        # Run complete analysis
        success = eda.run_complete_analysis()
        
        if success:
            print("\n[SUCCESS] Maximum EDA completed successfully!")
            print(f"Check the output directory: {OUTPUT_DIR}")
            print(f"  - Summary: {SUMMARY_FILE}")
            print(f"  - Plots: {PLOTS_DIR}")
            print(f"  - Data: {DATA_DIR}")
        else:
            print("\n[WARNING] Analysis completed with some errors")
        
        return success
        
    except Exception as e:
        print(f"[ERROR] Analysis failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Close database connection
        db.close()

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Set matplotlib backend to avoid display issues
    plt.switch_backend('Agg')
    
    # Run main function
    success = main()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
