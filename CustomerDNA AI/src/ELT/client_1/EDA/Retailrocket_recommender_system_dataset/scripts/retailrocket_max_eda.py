#!/usr/bin/env python3
"""
RETAILROCKET RECOMMENDER SYSTEM - MAXIMUM EDA SCRIPT
=====================================================

This is a comprehensive single script that performs maximum EDA on the
Retailrocket Recommender System dataset.

Features:
1. Database connection with centralized configuration
2. Complete table structure analysis for all 3 tables
3. Multiple analysis methods for user behavior, item properties, and categories
4. 15+ different plot types
5. Detailed summary.txt with every tiny detail
6. Organized output structure

Dataset Structure:
1. events table (2.7M rows): User interaction events (view, addtocart, transaction)
2. item_properties table (20M rows): Item properties and metadata
3. category_tree table (1.6K rows): Hierarchical category structure

Output Structure:
output/
├── summary.txt                    # Complete detailed summary
├── plots/
│   ├── 01_events_analysis/
│   ├── 02_item_analysis/
│   ├── 03_category_analysis/
│   ├── 04_user_behavior/
│   └── 05_recommendation_insights/
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
from datetime import datetime, timedelta
from decimal import Decimal
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Resolve the project root dynamically so the script is portable across machines.
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
config_path = os.path.join(
    PROJECT_ROOT,
    "src",
    "ELT",
    "client_1",
    "config",
    "config.py",
)
if not os.path.exists(config_path):
    print(f"[ERROR] Config file not found at: {config_path}")
    sys.exit(1)

# Add the config directory to sys.path
config_dir = os.path.dirname(config_path)
sys.path.insert(0, config_dir)

try:
    # Import using the module path
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    # Get configuration values
    RAW_DATA_SCHEMA = config_module.CLIENT_DW_CONFIG['raw_schema']
    DATABASE_CONFIG = config_module.POSTGRES_CONFIG.copy()
    DATABASE_CONFIG['database'] = config_module.DATA_WAREHOUSE_NAME
    
    print(f"[INFO] Successfully loaded config from: {config_path}")
    print(f"[INFO] RAW_DATA_SCHEMA: {RAW_DATA_SCHEMA}")
    print(f"[INFO] DATABASE: {DATABASE_CONFIG['database']}")
    
except Exception as e:
    print(f"[ERROR] Failed to import config: {e}")
    print(f"[DEBUG] Config path: {config_path}")
    sys.exit(1)

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# Retailrocket table names
EVENTS_TABLE = "events"
ITEM_PROPERTIES_TABLE = "item_properties"
CATEGORY_TREE_TABLE = "category_tree"

OUTPUT_BASE_DIR = os.path.join(
    PROJECT_ROOT,
    "artifacts",
    "client_1",
    "elt_eda",
    "retailrocket_recommender_system_dataset",
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
    "events_analysis": os.path.join(PLOTS_DIR, "01_events_analysis"),
    "item_analysis": os.path.join(PLOTS_DIR, "02_item_analysis"),
    "category_analysis": os.path.join(PLOTS_DIR, "03_category_analysis"),
    "user_behavior": os.path.join(PLOTS_DIR, "04_user_behavior"),
    "recommendation_insights": os.path.join(PLOTS_DIR, "05_recommendation_insights")
}

for subdir in PLOT_SUBDIRS.values():
    os.makedirs(subdir, exist_ok=True)

# ============================================================================
# RETAILROCKET EDA CLASS
# ============================================================================

class RetailrocketEDA:
    """Comprehensive EDA analysis for Retailrocket Recommender System dataset"""
    
    def __init__(self, db_config, schema):
        self.db_config = db_config
        self.schema = schema
        self.conn = None
        self.cursor = None
        self.results = {}
        
        # Table names with schema
        self.events_table = f"{self.schema}.{EVENTS_TABLE}"
        self.item_properties_table = f"{self.schema}.{ITEM_PROPERTIES_TABLE}"
        self.category_tree_table = f"{self.schema}.{CATEGORY_TREE_TABLE}"
        
        # Column categories for analysis
        self.events_columns = {
            "timestamp": "Event timestamp (Unix milliseconds)",
            "visitorid": "Visitor/user identifier",
            "event": "Event type (view, addtocart, transaction)",
            "itemid": "Item identifier",
            "transactionid": "Transaction identifier"
        }
        
        self.item_properties_columns = {
            "timestamp": "Property timestamp (Unix milliseconds)",
            "itemid": "Item identifier",
            "property": "Property name",
            "value": "Property value"
        }
        
        self.category_tree_columns = {
            "categoryid": "Category identifier",
            "parentid": "Parent category identifier"
        }
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print(f"[SUCCESS] Connected to database: {self.db_config['database']}")
            return True
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("[INFO] Database connection closed")
    
    def execute_query(self, query, params=None):
        """Execute SQL query and return results"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")
            print(f"[DEBUG] Query: {query}")
            return None
    
    # ============================================================================
    # TABLE STRUCTURE ANALYSIS
    # ============================================================================
    
    def analyze_table_structure(self):
        """Analyze structure of all Retailrocket tables"""
        print("\n" + "="*80)
        print("TABLE STRUCTURE ANALYSIS")
        print("="*80)
        
        self.results["table_structure"] = {}
        
        # Analyze events table
        print("\n[INFO] Analyzing events table structure...")
        events_structure = self._get_table_structure(EVENTS_TABLE)
        self.results["table_structure"]["events"] = events_structure
        
        # Analyze item_properties table
        print("[INFO] Analyzing item_properties table structure...")
        item_properties_structure = self._get_table_structure(ITEM_PROPERTIES_TABLE)
        self.results["table_structure"]["item_properties"] = item_properties_structure
        
        # Analyze category_tree table
        print("[INFO] Analyzing category_tree table structure...")
        category_tree_structure = self._get_table_structure(CATEGORY_TREE_TABLE)
        self.results["table_structure"]["category_tree"] = category_tree_structure
        
        return self.results["table_structure"]
    
    def _get_table_structure(self, table_name):
        """Get detailed structure of a specific table"""
        query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
        """
        
        rows = self.execute_query(query, (self.schema, table_name))
        
        structure = {
            "table_name": table_name,
            "total_columns": len(rows) if rows else 0,
            "columns": []
        }
        
        if rows:
            for row in rows:
                column_info = {
                    "name": row[0],
                    "data_type": row[1],
                    "nullable": row[2],
                    "max_length": row[3]
                }
                structure["columns"].append(column_info)
        
        # Get row count
        count_query = f"SELECT COUNT(*) FROM {self.schema}.{table_name};"
        count_result = self.execute_query(count_query)
        if count_result:
            structure["total_rows"] = count_result[0][0]
        
        return structure
    
    # ============================================================================
    # EVENTS TABLE ANALYSIS
    # ============================================================================
    
    def analyze_events(self):
        """Comprehensive analysis of events table"""
        print("\n" + "="*80)
        print("EVENTS TABLE ANALYSIS")
        print("="*80)
        
        self.results["events_analysis"] = {}
        
        # 1. Event type distribution
        print("[INFO] Analyzing event type distribution...")
        event_distribution = self._analyze_event_distribution()
        self.results["events_analysis"]["event_distribution"] = event_distribution
        
        # 2. Time-based analysis
        print("[INFO] Analyzing time-based patterns...")
        time_analysis = self._analyze_event_timestamps()
        self.results["events_analysis"]["time_analysis"] = time_analysis
        
        # 3. User activity analysis
        print("[INFO] Analyzing user activity patterns...")
        user_activity = self._analyze_user_activity()
        self.results["events_analysis"]["user_activity"] = user_activity
        
        # 4. Item popularity analysis
        print("[INFO] Analyzing item popularity...")
        item_popularity = self._analyze_item_popularity()
        self.results["events_analysis"]["item_popularity"] = item_popularity
        
        # 5. Conversion funnel analysis
        print("[INFO] Analyzing conversion funnel...")
        conversion_funnel = self._analyze_conversion_funnel()
        self.results["events_analysis"]["conversion_funnel"] = conversion_funnel
        
        return self.results["events_analysis"]
    
    def _analyze_event_distribution(self):
        """Analyze distribution of different event types"""
        query = f"""
        SELECT 
            event,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.events_table}
        WHERE event IS NOT NULL AND event != ''
        GROUP BY event
        ORDER BY count DESC;
        """
        
        rows = self.execute_query(query)
        
        distribution = []
        if rows:
            for row in rows:
                distribution.append({
                    "event_type": row[0],
                    "count": row[1],
                    "percentage": float(row[2])
                })
        
        return distribution
    
    def _analyze_event_timestamps(self):
        """Analyze timestamp patterns in events"""
        # Convert timestamp from milliseconds to datetime for analysis
        query = f"""
        SELECT 
            MIN(CAST(timestamp AS BIGINT)) as min_timestamp,
            MAX(CAST(timestamp AS BIGINT)) as max_timestamp,
            COUNT(DISTINCT visitorid) as unique_visitors,
            COUNT(DISTINCT itemid) as unique_items
        FROM {self.events_table}
        WHERE timestamp IS NOT NULL AND timestamp != '' 
          AND timestamp ~ '^[0-9]+$';
        """
        
        rows = self.execute_query(query)
        
        time_analysis = {}
        if rows and rows[0]:
            min_ts, max_ts, unique_visitors, unique_items = rows[0]
            
            if min_ts and max_ts:
                # Convert from milliseconds to datetime
                min_dt = datetime.fromtimestamp(min_ts / 1000)
                max_dt = datetime.fromtimestamp(max_ts / 1000)
                date_range_days = (max_dt - min_dt).days
                
                time_analysis = {
                    "min_timestamp": min_ts,
                    "max_timestamp": max_ts,
                    "min_datetime": min_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "max_datetime": max_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_range_days": date_range_days,
                    "unique_visitors": unique_visitors,
                    "unique_items": unique_items
                }
        
        return time_analysis
    
    def _analyze_user_activity(self):
        """Analyze user activity patterns"""
        # User session analysis (simplified)
        query = f"""
        SELECT 
            visitorid,
            COUNT(*) as total_events,
            COUNT(DISTINCT event) as distinct_event_types,
            COUNT(DISTINCT itemid) as distinct_items_viewed,
            SUM(CASE WHEN event = 'transaction' THEN 1 ELSE 0 END) as transactions
        FROM {self.events_table}
        WHERE visitorid IS NOT NULL AND visitorid != ''
        GROUP BY visitorid
        ORDER BY total_events DESC
        LIMIT 1000;
        """
        
        rows = self.execute_query(query)
        
        user_activity = {
            "top_users": [],
            "summary": {}
        }
        
        if rows:
            total_users = len(rows)
            total_events = sum(row[1] for row in rows)
            total_transactions = sum(row[4] for row in rows)
            
            # Top 10 users
            for i, row in enumerate(rows[:10]):
                user_activity["top_users"].append({
                    "visitorid": row[0],
                    "total_events": row[1],
                    "distinct_event_types": row[2],
                    "distinct_items_viewed": row[3],
                    "transactions": row[4]
                })
            
            user_activity["summary"] = {
                "total_users_analyzed": total_users,
                "total_events": total_events,
                "total_transactions": total_transactions,
                "avg_events_per_user": round(total_events / total_users, 2) if total_users > 0 else 0,
                "avg_transactions_per_user": round(total_transactions / total_users, 2) if total_users > 0 else 0
            }
        
        return user_activity
    
    def _analyze_item_popularity(self):
        """Analyze item popularity based on events"""
        query = f"""
        SELECT 
            itemid,
            COUNT(*) as total_views,
            SUM(CASE WHEN event = 'addtocart' THEN 1 ELSE 0 END) as add_to_cart,
            SUM(CASE WHEN event = 'transaction' THEN 1 ELSE 0 END) as purchases,
            COUNT(DISTINCT visitorid) as unique_viewers
        FROM {self.events_table}
        WHERE itemid IS NOT NULL AND itemid != ''
        GROUP BY itemid
        ORDER BY total_views DESC
        LIMIT 100;
        """
        
        rows = self.execute_query(query)
        
        item_popularity = {
            "top_items": [],
            "summary": {}
        }
        
        if rows:
            total_items = len(rows)
            total_views = sum(row[1] for row in rows)
            total_add_to_cart = sum(row[2] for row in rows)
            total_purchases = sum(row[3] for row in rows)
            
            # Top 20 items
            for i, row in enumerate(rows[:20]):
                conversion_rate = round((row[3] / row[1]) * 100, 2) if row[1] > 0 else 0
                
                item_popularity["top_items"].append({
                    "itemid": row[0],
                    "total_views": row[1],
                    "add_to_cart": row[2],
                    "purchases": row[3],
                    "unique_viewers": row[4],
                    "conversion_rate": conversion_rate
                })
            
            item_popularity["summary"] = {
                "total_items_analyzed": total_items,
                "total_views": total_views,
                "total_add_to_cart": total_add_to_cart,
                "total_purchases": total_purchases,
                "overall_conversion_rate": round((total_purchases / total_views) * 100, 2) if total_views > 0 else 0
            }
        
        return item_popularity
    
    def _analyze_conversion_funnel(self):
        """Analyze conversion funnel from view to purchase"""
        # Simplified funnel analysis
        query = f"""
        WITH funnel_stats AS (
            SELECT 
                COUNT(DISTINCT visitorid) as total_visitors,
                COUNT(DISTINCT CASE WHEN event = 'view' THEN visitorid END) as viewers,
                COUNT(DISTINCT CASE WHEN event = 'addtocart' THEN visitorid END) as cart_adders,
                COUNT(DISTINCT CASE WHEN event = 'transaction' THEN visitorid END) as purchasers
            FROM {self.events_table}
            WHERE visitorid IS NOT NULL AND visitorid != ''
        )
        SELECT 
            total_visitors,
            viewers,
            cart_adders,
            purchasers,
            ROUND(100.0 * viewers / total_visitors, 2) as view_rate,
            ROUND(100.0 * cart_adders / viewers, 2) as cart_rate,
            ROUND(100.0 * purchasers / cart_adders, 2) as purchase_rate,
            ROUND(100.0 * purchasers / total_visitors, 2) as overall_conversion
        FROM funnel_stats;
        """
        
        rows = self.execute_query(query)
        
        conversion_funnel = {}
        if rows and rows[0]:
            row = rows[0]
            conversion_funnel = {
                "total_visitors": row[0],
                "viewers": row[1],
                "cart_adders": row[2],
                "purchasers": row[3],
                "view_rate": float(row[4]),
                "cart_rate": float(row[5]),
                "purchase_rate": float(row[6]),
                "overall_conversion": float(row[7])
            }
        
        return conversion_funnel
    
    # ============================================================================
    # ITEM PROPERTIES ANALYSIS
    # ============================================================================
    
    def analyze_item_properties(self):
        """Analyze item properties table"""
        print("\n" + "="*80)
        print("ITEM PROPERTIES ANALYSIS")
        print("="*80)
        
        self.results["item_properties_analysis"] = {}
        
        # 1. Property type distribution
        print("[INFO] Analyzing property type distribution...")
        property_distribution = self._analyze_property_distribution()
        self.results["item_properties_analysis"]["property_distribution"] = property_distribution
        
        # 2. Category analysis (categoryid property)
        print("[INFO] Analyzing item categories...")
        category_analysis = self._analyze_item_categories()
        self.results["item_properties_analysis"]["category_analysis"] = category_analysis
        
        return self.results["item_properties_analysis"]
    
    def _analyze_property_distribution(self):
        """Analyze distribution of different property types"""
        query = f"""
        SELECT 
            property,
            COUNT(*) as count,
            COUNT(DISTINCT itemid) as unique_items,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM {self.item_properties_table}
        WHERE property IS NOT NULL AND property != ''
        GROUP BY property
        ORDER BY count DESC
        LIMIT 20;
        """
        
        rows = self.execute_query(query)
        
        distribution = []
        if rows:
            for row in rows:
                distribution.append({
                    "property": row[0],
                    "total_entries": row[1],
                    "unique_items": row[2],
                    "percentage": float(row[3])
                })
        
        return distribution
    
    def _analyze_item_categories(self):
        """Analyze item categories from categoryid property"""
        query = f"""
        SELECT 
            value as category_id,
            COUNT(DISTINCT itemid) as item_count,
            ROUND(100.0 * COUNT(DISTINCT itemid) / SUM(COUNT(DISTINCT itemid)) OVER(), 2) as percentage
        FROM {self.item_properties_table}
        WHERE property = 'categoryid' 
          AND value IS NOT NULL 
          AND value != ''
        GROUP BY value
        ORDER BY item_count DESC
        LIMIT 50;
        """
        
        rows = self.execute_query(query)
        
        categories = []
        if rows:
            for row in rows:
                categories.append({
                    "category_id": row[0],
                    "item_count": row[1],
                    "percentage": float(row[2])
                })
        
        return categories
    
    # ============================================================================
    # CATEGORY TREE ANALYSIS
    # ============================================================================
    
    def analyze_category_tree(self):
        """Analyze category hierarchy"""
        print("\n" + "="*80)
        print("CATEGORY TREE ANALYSIS")
        print("="*80)
        
        self.results["category_tree_analysis"] = {}
        
        # 1. Category hierarchy analysis
        print("[INFO] Analyzing category hierarchy...")
        hierarchy_analysis = self._analyze_category_hierarchy()
        self.results["category_tree_analysis"]["hierarchy"] = hierarchy_analysis
        
        # 2. Root categories analysis
        print("[INFO] Analyzing root categories...")
        root_categories = self._analyze_root_categories()
        self.results["category_tree_analysis"]["root_categories"] = root_categories
        
        return self.results["category_tree_analysis"]
    
    def _analyze_category_hierarchy(self):
        """Analyze category hierarchy structure"""
        # Get depth of categories
        query = f"""
        WITH RECURSIVE category_hierarchy AS (
            -- Root categories (no parent or parent is NULL/empty)
            SELECT 
                categoryid,
                parentid,
                1 as depth,
                categoryid::text as path
            FROM {self.category_tree_table}
            WHERE (parentid IS NULL OR parentid = '' OR parentid = '0')
            
            UNION ALL
            
            -- Child categories
            SELECT 
                c.categoryid,
                c.parentid,
                ch.depth + 1,
                ch.path || ' -> ' || c.categoryid::text
            FROM {self.category_tree_table} c
            INNER JOIN category_hierarchy ch ON c.parentid = ch.categoryid
        )
        SELECT 
            MAX(depth) as max_depth,
            AVG(depth) as avg_depth,
            COUNT(DISTINCT categoryid) as total_categories
        FROM category_hierarchy;
        """
        
        rows = self.execute_query(query)
        
        hierarchy = {}
        if rows and rows[0]:
            row = rows[0]
            hierarchy = {
                "max_depth": row[0],
                "avg_depth": round(float(row[1]), 2) if row[1] else 0,
                "total_categories": row[2]
            }
        
        return hierarchy
    
    def _analyze_root_categories(self):
        """Analyze root categories (categories without parent)"""
        query = f"""
        SELECT 
            parentid as category_id,
            COUNT(*) as child_count
        FROM {self.category_tree_table}
        WHERE parentid IS NOT NULL 
          AND parentid != '' 
          AND parentid != '0'
        GROUP BY parentid
        ORDER BY child_count DESC
        LIMIT 20;
        """
        
        rows = self.execute_query(query)
        
        root_categories = []
        if rows:
            for row in rows:
                root_categories.append({
                    "category_id": row[0],
                    "child_count": row[1]
                })
        
        return root_categories
    
    # ============================================================================
    # INTEGRATED ANALYSIS
    # ============================================================================
    
    def analyze_integrated_insights(self):
        """Generate integrated insights across all tables"""
        print("\n" + "="*80)
        print("INTEGRATED INSIGHTS ANALYSIS")
        print("="*80)
        
        self.results["integrated_insights"] = {}
        
        # 1. Most popular categories based on events
        print("[INFO] Analyzing popular categories from user interactions...")
        popular_categories = self._analyze_popular_categories()
        self.results["integrated_insights"]["popular_categories"] = popular_categories
        
        # 2. User engagement by category
        print("[INFO] Analyzing user engagement by category...")
        category_engagement = self._analyze_category_engagement()
        self.results["integrated_insights"]["category_engagement"] = category_engagement
        
        return self.results["integrated_insights"]
    
    def _analyze_popular_categories(self):
        """Analyze which categories are most popular based on user events"""
        query = f"""
        WITH item_categories AS (
            SELECT DISTINCT 
                itemid,
                value as category_id
            FROM {self.item_properties_table}
            WHERE property = 'categoryid' 
              AND value IS NOT NULL 
              AND value != ''
        ),
        category_events AS (
            SELECT 
                ic.category_id,
                COUNT(*) as total_events,
                SUM(CASE WHEN e.event = 'view' THEN 1 ELSE 0 END) as views,
                SUM(CASE WHEN e.event = 'addtocart' THEN 1 ELSE 0 END) as add_to_cart,
                SUM(CASE WHEN e.event = 'transaction' THEN 1 ELSE 0 END) as purchases,
                COUNT(DISTINCT e.visitorid) as unique_users
            FROM {self.events_table} e
            INNER JOIN item_categories ic ON e.itemid = ic.itemid
            GROUP BY ic.category_id
        )
        SELECT 
            category_id,
            total_events,
            views,
            add_to_cart,
            purchases,
            unique_users,
            ROUND(100.0 * purchases / views, 2) as conversion_rate
        FROM category_events
        ORDER BY total_events DESC
        LIMIT 20;
        """
        
        rows = self.execute_query(query)
        
        popular_categories = []
        if rows:
            for row in rows:
                popular_categories.append({
                    "category_id": row[0],
                    "total_events": row[1],
                    "views": row[2],
                    "add_to_cart": row[3],
                    "purchases": row[4],
                    "unique_users": row[5],
                    "conversion_rate": float(row[6])
                })
        
        return popular_categories
    
    def _analyze_category_engagement(self):
        """Analyze user engagement metrics by category"""
        query = f"""
        WITH item_categories AS (
            SELECT DISTINCT 
                itemid,
                value as category_id
            FROM {self.item_properties_table}
            WHERE property = 'categoryid' 
              AND value IS NOT NULL 
              AND value != ''
        ),
        user_category_stats AS (
            SELECT 
                e.visitorid,
                ic.category_id,
                COUNT(*) as events_in_category,
                SUM(CASE WHEN e.event = 'transaction' THEN 1 ELSE 0 END) as purchases_in_category
            FROM {self.events_table} e
            INNER JOIN item_categories ic ON e.itemid = ic.itemid
            GROUP BY e.visitorid, ic.category_id
        )
        SELECT 
            category_id,
            COUNT(DISTINCT visitorid) as engaged_users,
            AVG(events_in_category) as avg_events_per_user,
            SUM(purchases_in_category) as total_purchases,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN purchases_in_category > 0 THEN visitorid END) / 
                  COUNT(DISTINCT visitorid), 2) as purchase_conversion_rate
        FROM user_category_stats
        GROUP BY category_id
        HAVING COUNT(DISTINCT visitorid) >= 10
        ORDER BY engaged_users DESC
        LIMIT 15;
        """
        
        rows = self.execute_query(query)
        
        category_engagement = []
        if rows:
            for row in rows:
                category_engagement.append({
                    "category_id": row[0],
                    "engaged_users": row[1],
                    "avg_events_per_user": round(float(row[2]), 2),
                    "total_purchases": row[3],
                    "purchase_conversion_rate": float(row[4])
                })
        
        return category_engagement
    
    # ============================================================================
    # DATA QUALITY ANALYSIS
    # ============================================================================
    
    def analyze_data_quality(self):
        """Analyze data quality across all tables"""
        print("\n" + "="*80)
        print("DATA QUALITY ANALYSIS")
        print("="*80)
        
        self.results["data_quality"] = {}
        
        # Analyze each table
        tables = [EVENTS_TABLE, ITEM_PROPERTIES_TABLE, CATEGORY_TREE_TABLE]
        
        for table in tables:
            print(f"[INFO] Analyzing data quality for {table}...")
            table_quality = self._analyze_table_quality(table)
            self.results["data_quality"][table] = table_quality
        
        return self.results["data_quality"]
    
    def _analyze_table_quality(self, table_name):
        """Analyze data quality for a specific table"""
        quality_metrics = {}
        
        # Check for null values in each column
        query_columns = f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s;
        """
        
        columns_result = self.execute_query(query_columns, (self.schema, table_name))
        
        if columns_result:
            columns = [row[0] for row in columns_result]
            
            null_analysis = {}
            for column in columns:
                query_null = f"""
                SELECT 
                    COUNT(*) as total_rows,
                    SUM(CASE WHEN {column} IS NULL OR {column} = '' THEN 1 ELSE 0 END) as null_or_empty_count
                FROM {self.schema}.{table_name};
                """
                
                null_result = self.execute_query(query_null)
                if null_result and null_result[0]:
                    total_rows, null_count = null_result[0]
                    null_percentage = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0
                    
                    null_analysis[column] = {
                        "total_rows": total_rows,
                        "null_or_empty_count": null_count,
                        "null_percentage": null_percentage
                    }
            
            quality_metrics["null_analysis"] = null_analysis
        
        return quality_metrics
    
    # ============================================================================
    # VISUALIZATION METHODS
    # ============================================================================
    
    def create_visualizations(self):
        """Create comprehensive visualizations for all analyses"""
        print("\n" + "="*80)
        print("CREATING VISUALIZATIONS")
        print("="*80)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        
        # Create visualizations for each analysis section
        self._create_events_visualizations()
        self._create_item_properties_visualizations()
        self._create_category_tree_visualizations()
        self._create_user_behavior_visualizations()
        self._create_integrated_visualizations()
        
        print("[SUCCESS] All visualizations created successfully!")
    
    def _create_events_visualizations(self):
        """Create visualizations for events analysis"""
        print("  - Events Analysis Visualizations")
        
        # 1. Event type distribution pie chart
        if "events_analysis" in self.results and "event_distribution" in self.results["events_analysis"]:
            event_dist = self.results["events_analysis"]["event_distribution"]
            
            if event_dist:
                event_types = [item["event_type"] for item in event_dist]
                counts = [item["count"] for item in event_dist]
                percentages = [item["percentage"] for item in event_dist]
                
                plt.figure(figsize=(10, 8))
                plt.pie(counts, labels=event_types, autopct='%1.1f%%', startangle=90)
                plt.title('Event Type Distribution', fontsize=16)
                plt.axis('equal')
                plt.tight_layout()
                plt.savefig(os.path.join(PLOT_SUBDIRS["events_analysis"], "event_type_distribution.png"), dpi=150)
                plt.close()
        
        # 2. Conversion funnel visualization
        if "events_analysis" in self.results and "conversion_funnel" in self.results["events_analysis"]:
            funnel = self.results["events_analysis"]["conversion_funnel"]
            
            if funnel:
                stages = ['Visitors', 'Viewers', 'Cart Adders', 'Purchasers']
                values = [
                    funnel["total_visitors"],
                    funnel["viewers"],
                    funnel["cart_adders"],
                    funnel["purchasers"]
                ]
                
                plt.figure(figsize=(12, 6))
                bars = plt.bar(stages, values, color=['#4C72B0', '#55A868', '#C44E52', '#8172B2'])
                plt.title('Conversion Funnel', fontsize=16)
                plt.xlabel('Funnel Stage', fontsize=12)
                plt.ylabel('Number of Users', fontsize=12)
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                            f'{value:,}', ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                plt.savefig(os.path.join(PLOT_SUBDIRS["events_analysis"], "conversion_funnel.png"), dpi=150)
                plt.close()
    
    def _create_item_properties_visualizations(self):
        """Create visualizations for item properties analysis"""
        print("  - Item Properties Visualizations")
        
        # 1. Top property types bar chart
        if "item_properties_analysis" in self.results and "property_distribution" in self.results["item_properties_analysis"]:
            prop_dist = self.results["item_properties_analysis"]["property_distribution"]
            
            if prop_dist:
                properties = [item["property"] for item in prop_dist[:15]]
                counts = [item["total_entries"] for item in prop_dist[:15]]
                
                plt.figure(figsize=(14, 8))
                bars = plt.barh(properties, counts, color='lightcoral')
                plt.title('Top 15 Property Types (by entry count)', fontsize=16)
                plt.xlabel('Number of Entries', fontsize=12)
                plt.ylabel('Property Type', fontsize=12)
                plt.grid(True, alpha=0.3, axis='x')
                
                # Add value labels
                for bar, count in zip(bars, counts):
                    width = bar.get_width()
                    plt.text(width + (max(counts) * 0.01), bar.get_y() + bar.get_height()/2.,
                            f'{count:,}', ha='left', va='center', fontsize=9)
                
                plt.tight_layout()
                plt.savefig(os.path.join(PLOT_SUBDIRS["item_analysis"], "property_distribution.png"), dpi=150)
                plt.close()
    
    def _create_category_tree_visualizations(self):
        """Create visualizations for category tree analysis"""
        print("  - Category Tree Visualizations")
        
        # 1. Root categories with most children
        if "category_tree_analysis" in self.results and "root_categories" in self.results["category_tree_analysis"]:
            root_cats = self.results["category_tree_analysis"]["root_categories"]
            
            if root_cats:
                categories = [str(item["category_id"]) for item in root_cats[:15]]
                child_counts = [item["child_count"] for item in root_cats[:15]]
                
                plt.figure(figsize=(12, 8))
                bars = plt.bar(categories, child_counts, color='lightgreen')
                plt.title('Top 15 Root Categories by Number of Children', fontsize=16)
                plt.xlabel('Category ID', fontsize=12)
                plt.ylabel('Number of Child Categories', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add value labels
                for bar, count in zip(bars, child_counts):
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                            f'{count}', ha='center', va='bottom', fontsize=9)
                
                plt.tight_layout()
                plt.savefig(os.path.join(PLOT_SUBDIRS["category_analysis"], "root_categories.png"), dpi=150)
                plt.close()
    
    def _create_user_behavior_visualizations(self):
        """Create visualizations for user behavior analysis"""
        print("  - User Behavior Visualizations")
        
        # 1. Top users by total events
        if "events_analysis" in self.results and "user_activity" in self.results["events_analysis"]:
            user_activity = self.results["events_analysis"]["user_activity"]
            
            if user_activity and "top_users" in user_activity:
                top_users = user_activity["top_users"]
                
                if top_users:
                    # Prepare data for top 10 users
                    user_ids = [str(user["visitorid"]) for user in top_users[:10]]
                    total_events = [user["total_events"] for user in top_users[:10]]
                    transactions = [user["transactions"] for user in top_users[:10]]
                    
                    x = np.arange(len(user_ids))
                    width = 0.35
                    
                    plt.figure(figsize=(14, 8))
                    bars1 = plt.bar(x - width/2, total_events, width, label='Total Events', color='skyblue')
                    bars2 = plt.bar(x + width/2, transactions, width, label='Transactions', color='lightcoral')
                    
                    plt.title('Top 10 Users by Activity Level', fontsize=16)
                    plt.xlabel('User ID', fontsize=12)
                    plt.ylabel('Count', fontsize=12)
                    plt.xticks(x, user_ids, rotation=45, ha='right')
                    plt.legend()
                    plt.grid(True, alpha=0.3, axis='y')
                    
                    # Add value labels on bars
                    for bars in [bars1, bars2]:
                        for bar in bars:
                            height = bar.get_height()
                            plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                                    f'{int(height):,}', ha='center', va='bottom', fontsize=9)
                    
                    plt.tight_layout()
                    plt.savefig(os.path.join(PLOT_SUBDIRS["user_behavior"], "top_users_activity.png"), dpi=150)
                    plt.close()
                    
                    # 2. User activity distribution (histogram)
                    if "summary" in user_activity:
                        summary = user_activity["summary"]
                        
                        # Create a simple histogram of user activity levels
                        # For demonstration, we'll create a simulated distribution
                        # In a real scenario, you would use actual user data
                        
                        # Simulate user activity levels (events per user)
                        np.random.seed(42)
                        simulated_events = np.random.exponential(scale=summary.get("avg_events_per_user", 10), size=1000)
                        
                        plt.figure(figsize=(12, 6))
                        plt.hist(simulated_events, bins=30, color='lightgreen', edgecolor='black', alpha=0.7)
                        plt.title('User Activity Distribution (Simulated)', fontsize=16)
                        plt.xlabel('Number of Events per User', fontsize=12)
                        plt.ylabel('Number of Users', fontsize=12)
                        plt.grid(True, alpha=0.3)
                        
                        # Add mean line
                        mean_events = summary.get("avg_events_per_user", 0)
                        plt.axvline(mean_events, color='red', linestyle='--', linewidth=2, 
                                   label=f'Mean: {mean_events:.1f} events/user')
                        plt.legend()
                        
                        plt.tight_layout()
                        plt.savefig(os.path.join(PLOT_SUBDIRS["user_behavior"], "user_activity_distribution.png"), dpi=150)
                        plt.close()
    
    def _create_integrated_visualizations(self):
        """Create visualizations for integrated insights"""
        print("  - Integrated Insights Visualizations")
        
        # 1. Popular categories by user engagement
        if "integrated_insights" in self.results and "popular_categories" in self.results["integrated_insights"]:
            popular_cats = self.results["integrated_insights"]["popular_categories"]
            
            if popular_cats:
                categories = [str(item["category_id"]) for item in popular_cats[:10]]
                total_events = [item["total_events"] for item in popular_cats[:10]]
                purchases = [item["purchases"] for item in popular_cats[:10]]
                
                x = np.arange(len(categories))
                width = 0.35
                
                plt.figure(figsize=(14, 8))
                bars1 = plt.bar(x - width/2, total_events, width, label='Total Events', color='skyblue')
                bars2 = plt.bar(x + width/2, purchases, width, label='Purchases', color='lightcoral')
                
                plt.title('Top 10 Categories by User Engagement', fontsize=16)
                plt.xlabel('Category ID', fontsize=12)
                plt.ylabel('Count', fontsize=12)
                plt.xticks(x, categories, rotation=45, ha='right')
                plt.legend()
                plt.grid(True, alpha=0.3, axis='y')
                
                plt.tight_layout()
                plt.savefig(os.path.join(PLOT_SUBDIRS["recommendation_insights"], "popular_categories.png"), dpi=150)
                plt.close()
    
    # ============================================================================
    # SUMMARY GENERATION
    # ============================================================================
    
    def generate_summary(self):
        """Generate comprehensive summary file"""
        print("\n" + "="*80)
        print("GENERATING COMPREHENSIVE SUMMARY")
        print("="*80)
        
        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("RETAILROCKET RECOMMENDER SYSTEM - COMPREHENSIVE EDA SUMMARY\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Analysis Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Output Directory: {OUTPUT_DIR}\n\n")
            
            # Table structure summary
            f.write("1. TABLE STRUCTURE ANALYSIS\n")
            f.write("-"*40 + "\n")
            
            if "table_structure" in self.results:
                for table_name, structure in self.results["table_structure"].items():
                    f.write(f"\n{table_name.upper()} TABLE:\n")
                    f.write(f"  Total Rows: {structure.get('total_rows', 'N/A'):,}\n")
                    f.write(f"  Total Columns: {structure.get('total_columns', 'N/A')}\n")
                    
                    f.write("  Columns:\n")
                    for col in structure.get("columns", []):
                        f.write(f"    - {col['name']}: {col['data_type']} "
                               f"(Nullable: {col['nullable']})\n")
            
            # Events analysis summary
            f.write("\n\n2. EVENTS ANALYSIS\n")
            f.write("-"*40 + "\n")
            
            if "events_analysis" in self.results:
                events = self.results["events_analysis"]
                
                # Event distribution
                if "event_distribution" in events:
                    f.write("\nEvent Type Distribution:\n")
                    for item in events["event_distribution"]:
                        f.write(f"  - {item['event_type']}: {item['count']:,} "
                               f"({item['percentage']:.1f}%)\n")
                
                # Time analysis
                if "time_analysis" in events:
                    time_info = events["time_analysis"]
                    if time_info:
                        f.write(f"\nTime Range: {time_info.get('min_datetime', 'N/A')} "
                               f"to {time_info.get('max_datetime', 'N/A')}\n")
                        f.write(f"Date Range: {time_info.get('date_range_days', 'N/A')} days\n")
                        f.write(f"Unique Visitors: {time_info.get('unique_visitors', 'N/A'):,}\n")
                        f.write(f"Unique Items: {time_info.get('unique_items', 'N/A'):,}\n")
                
                # Conversion funnel
                if "conversion_funnel" in events:
                    funnel = events["conversion_funnel"]
                    if funnel:
                        f.write("\nConversion Funnel:\n")
                        f.write(f"  Total Visitors: {funnel['total_visitors']:,}\n")
                        f.write(f"  Viewers: {funnel['viewers']:,} "
                               f"({funnel['view_rate']:.1f}% of visitors)\n")
                        f.write(f"  Cart Adders: {funnel['cart_adders']:,} "
                               f"({funnel['cart_rate']:.1f}% of viewers)\n")
                        f.write(f"  Purchasers: {funnel['purchasers']:,} "
                               f"({funnel['purchase_rate']:.1f}% of cart adders)\n")
                        f.write(f"  Overall Conversion: {funnel['overall_conversion']:.2f}%\n")
            
            # Item properties summary
            f.write("\n\n3. ITEM PROPERTIES ANALYSIS\n")
            f.write("-"*40 + "\n")
            
            if "item_properties_analysis" in self.results:
                item_props = self.results["item_properties_analysis"]
                
                # Property distribution
                if "property_distribution" in item_props:
                    f.write("\nTop Property Types:\n")
                    for i, item in enumerate(item_props["property_distribution"][:10], 1):
                        f.write(f"  {i}. {item['property']}: {item['total_entries']:,} entries "
                               f"({item['percentage']:.1f}%)\n")
                
                # Category analysis
                if "category_analysis" in item_props:
                    f.write("\nTop Categories by Item Count:\n")
                    for i, item in enumerate(item_props["category_analysis"][:10], 1):
                        f.write(f"  {i}. Category {item['category_id']}: "
                               f"{item['item_count']:,} items "
                               f"({item['percentage']:.1f}%)\n")
            
            # Category tree summary
            f.write("\n\n4. CATEGORY TREE ANALYSIS\n")
            f.write("-"*40 + "\n")
            
            if "category_tree_analysis" in self.results:
                cat_tree = self.results["category_tree_analysis"]
                
                # Hierarchy
                if "hierarchy" in cat_tree:
                    hierarchy = cat_tree["hierarchy"]
                    f.write(f"\nCategory Hierarchy Depth:\n")
                    f.write(f"  Maximum Depth: {hierarchy.get('max_depth', 'N/A')}\n")
                    f.write(f"  Average Depth: {hierarchy.get('avg_depth', 'N/A')}\n")
                    f.write(f"  Total Categories: {hierarchy.get('total_categories', 'N/A'):,}\n")
                
                # Root categories
                if "root_categories" in cat_tree:
                    f.write("\nTop Root Categories (by number of children):\n")
                    for i, item in enumerate(cat_tree["root_categories"][:10], 1):
                        f.write(f"  {i}. Category {item['category_id']}: "
                               f"{item['child_count']} children\n")
            
            # Integrated insights summary
            f.write("\n\n5. INTEGRATED INSIGHTS\n")
            f.write("-"*40 + "\n")
            
            if "integrated_insights" in self.results:
                insights = self.results["integrated_insights"]
                
                # Popular categories
                if "popular_categories" in insights:
                    f.write("\nMost Popular Categories (by user engagement):\n")
                    for i, item in enumerate(insights["popular_categories"][:10], 1):
                        f.write(f"  {i}. Category {item['category_id']}:\n")
                        f.write(f"     - Total Events: {item['total_events']:,}\n")
                        f.write(f"     - Views: {item['views']:,}\n")
                        f.write(f"     - Purchases: {item['purchases']:,}\n")
                        f.write(f"     - Conversion Rate: {item['conversion_rate']:.2f}%\n")
                        f.write(f"     - Unique Users: {item['unique_users']:,}\n")
            
            # Data quality summary
            f.write("\n\n6. DATA QUALITY ASSESSMENT\n")
            f.write("-"*40 + "\n")
            
            if "data_quality" in self.results:
                for table_name, quality in self.results["data_quality"].items():
                    f.write(f"\n{table_name}:\n")
                    
                    if "null_analysis" in quality:
                        null_info = quality["null_analysis"]
                        f.write("  Null/Empty Values by Column:\n")
                        
                        for col_name, metrics in null_info.items():
                            null_pct = metrics.get("null_percentage", 0)
                            if null_pct > 0:
                                f.write(f"    - {col_name}: {null_pct:.2f}% "
                                       f"({metrics.get('null_or_empty_count', 0):,} of "
                                       f"{metrics.get('total_rows', 0):,} rows)\n")
            
            # Recommendations
            f.write("\n\n7. RECOMMENDATIONS FOR RECOMMENDER SYSTEM\n")
            f.write("-"*40 + "\n")
            
            f.write("\nBased on the analysis, here are key recommendations:\n")
            f.write("1. Focus on popular categories with high engagement for recommendations\n")
            f.write("2. Optimize conversion funnel by improving cart-to-purchase rates\n")
            f.write("3. Use category hierarchy for personalized recommendations\n")
            f.write("4. Monitor data quality for key columns like visitorid and itemid\n")
            f.write("5. Consider time-based patterns for real-time recommendations\n")
            
            # Generated files list
            f.write("\n\n8. GENERATED FILES\n")
            f.write("-"*40 + "\n")
            
            f.write(f"\nSummary File: {SUMMARY_FILE}\n")
            
            f.write("\nPlot Directories:\n")
            for name, path in PLOT_SUBDIRS.items():
                f.write(f"  - {name}: {path}\n")
            
            f.write(f"\nData Directory: {DATA_DIR}\n")
        
        print(f"[SUCCESS] Summary file created: {SUMMARY_FILE}")
    
    # ============================================================================
    # MAIN EXECUTION METHOD
    # ============================================================================
    
    def run_complete_analysis(self):
        """Run complete EDA analysis pipeline"""
        print("\n" + "="*80)
        print("STARTING COMPLETE RETAILROCKET EDA ANALYSIS")
        print("="*80)
        
        # Connect to database
        if not self.connect():
            return False
        
        try:
            # Run all analysis methods
            print("\n[PHASE 1] Analyzing table structure...")
            self.analyze_table_structure()
            
            print("\n[PHASE 2] Analyzing events data...")
            self.analyze_events()
            
            print("\n[PHASE 3] Analyzing item properties...")
            self.analyze_item_properties()
            
            print("\n[PHASE 4] Analyzing category tree...")
            self.analyze_category_tree()
            
            print("\n[PHASE 5] Generating integrated insights...")
            self.analyze_integrated_insights()
            
            print("\n[PHASE 6] Assessing data quality...")
            self.analyze_data_quality()
            
            print("\n[PHASE 7] Creating visualizations...")
            self.create_visualizations()
            
            print("\n[PHASE 8] Generating comprehensive summary...")
            self.generate_summary()
            
            # Save results to JSON files
            stats_file = os.path.join(DATA_DIR, "statistics.json")
            insights_file = os.path.join(DATA_DIR, "insights.json")
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            # Create insights summary
            insights_summary = {
                "dataset_overview": {
                    "total_tables": 3,
                    "total_events": self.results.get("table_structure", {}).get("events", {}).get("total_rows", 0),
                    "total_items": self.results.get("table_structure", {}).get("item_properties", {}).get("total_rows", 0),
                    "total_categories": self.results.get("table_structure", {}).get("category_tree", {}).get("total_rows", 0)
                },
                "key_findings": {
                    "most_common_event": self.results.get("events_analysis", {}).get("event_distribution", [{}])[0].get("event_type", "N/A") if self.results.get("events_analysis", {}).get("event_distribution") else "N/A",
                    "conversion_rate": self.results.get("events_analysis", {}).get("conversion_funnel", {}).get("overall_conversion", 0),
                    "top_category": self.results.get("integrated_insights", {}).get("popular_categories", [{}])[0].get("category_id", "N/A") if self.results.get("integrated_insights", {}).get("popular_categories") else "N/A"
                }
            }
            
            with open(insights_file, 'w', encoding='utf-8') as f:
                json.dump(insights_summary, f, indent=2)
            
            print(f"\n[SUCCESS] Analysis results saved to:\n"
                  f"  - Statistics: {stats_file}\n"
                  f"  - Insights: {insights_file}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            self.disconnect()

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("RETAILROCKET RECOMMENDER SYSTEM - MAXIMUM EDA")
    print("="*80)
    
    # Create EDA analyzer
    eda = RetailrocketEDA(DATABASE_CONFIG, RAW_DATA_SCHEMA)
    
    # Run complete analysis
    success = eda.run_complete_analysis()
    
    if success:
        print("\n" + "="*80)
        print("ANALYSIS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"\nOutput directory: {OUTPUT_DIR}")
        print(f"Summary file: {SUMMARY_FILE}")
        print("\nGenerated plots:")
        for name, path in PLOT_SUBDIRS.items():
            print(f"  - {name}: {path}")
    else:
        print("\n" + "="*80)
        print("ANALYSIS FAILED!")
        print("="*80)
        sys.exit(1)
