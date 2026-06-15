"""
CustomerDNA AI - Data Ingestion Configuration
Client 1: Customer Personality Analysis Dataset
Purpose: Minimal preprocessing for database loading
"""

import os
from datetime import datetime

# ============================================================================
# DATASET CONFIGURATION
# ============================================================================

DATASET_CONFIG = {
    'customer_personality_analysis': {
        'name': 'Customer Personality Analysis',
        'file_name': 'marketing_campaign.csv',
        'delimiter': '\t',  # Tab-separated
        'encoding': 'utf-8',
        'description': 'Demographic and psychographic customer data',
        'columns': {
            'ID': 'int64',
            'Year_Birth': 'int64', 
            'Education': 'str',
            'Marital_Status': 'str',
            'Income': 'float64',
            'Kidhome': 'int64',
            'Teenhome': 'int64',
            'Dt_Customer': 'str',  # Will convert to date
            'Recency': 'int64',
            'MntWines': 'int64',
            'MntFruits': 'int64',
            'MntMeatProducts': 'int64',
            'MntFishProducts': 'int64',
            'MntSweetProducts': 'int64',
            'MntGoldProds': 'int64',
            'NumDealsPurchases': 'int64',
            'NumWebPurchases': 'int64',
            'NumCatalogPurchases': 'int64',
            'NumStorePurchases': 'int64',
            'NumWebVisitsMonth': 'int64',
            'AcceptedCmp3': 'int64',
            'AcceptedCmp4': 'int64',
            'AcceptedCmp5': 'int64',
            'AcceptedCmp1': 'int64',
            'AcceptedCmp2': 'int64',
            'Complain': 'int64',
            'Z_CostContact': 'int64',
            'Z_Revenue': 'int64',
            'Response': 'int64'
        },
        'required_columns': ['ID', 'Year_Birth', 'Education', 'Income'],
        'date_columns': ['Dt_Customer'],
        'numeric_columns': ['Income', 'MntWines', 'MntFruits', 'MntMeatProducts', 
                           'MntFishProducts', 'MntSweetProducts', 'MntGoldProds'],
        'categorical_columns': ['Education', 'Marital_Status'],
        'primary_key': 'ID'
    },
    'ecommerce_customer_churn': {
        'name': 'E-commerce Customer Churn',
        'file_name': 'E-commerce_customer_churn.xlsx',
        'sheet_name': 'E Comm',
        'file_type': 'excel',
        'encoding': 'utf-8',
        'description': 'E-commerce customer behavior and churn prediction data',
        'columns': {
            'CustomerID': 'int64',
            'Churn': 'int64',
            'Tenure': 'float64',
            'PreferredLoginDevice': 'str',
            'CityTier': 'int64',
            'WarehouseToHome': 'int64',
            'PreferredPaymentMode': 'str',
            'Gender': 'str',
            'HourSpendOnApp': 'float64',
            'NumberOfDeviceRegistered': 'int64',
            'PreferedOrderCat': 'str',
            'SatisfactionScore': 'int64',
            'MaritalStatus': 'str',
            'NumberOfAddress': 'int64',
            'Complain': 'int64',
            'OrderAmountHikeFromlastYear': 'int64',
            'CouponUsed': 'int64',
            'OrderCount': 'int64',
            'DaySinceLastOrder': 'int64',
            'CashbackAmount': 'float64'
        },
        'required_columns': ['CustomerID', 'Churn', 'Tenure', 'PreferredLoginDevice'],
        'date_columns': [],  # No date columns in this dataset
        'numeric_columns': ['Tenure', 'HourSpendOnApp', 'NumberOfDeviceRegistered', 
                           'SatisfactionScore', 'NumberOfAddress', 'Complain',
                           'OrderAmountHikeFromlastYear', 'CouponUsed', 'OrderCount',
                           'DaySinceLastOrder', 'CashbackAmount'],
        'categorical_columns': ['PreferredLoginDevice', 'PreferredPaymentMode', 
                               'Gender', 'PreferedOrderCat', 'MaritalStatus'],
        'primary_key': 'CustomerID'
    },
    'retailrocket_category_tree': {
        'name': 'RetailRocket Category Tree',
        'file_name': 'category_tree.csv',
        'delimiter': ',',
        'encoding': 'utf-8',
        'description': 'Category hierarchy for RetailRocket e-commerce dataset',
        'columns': {
            'categoryid': 'int64',
            'parentid': 'int64'
        },
        'required_columns': ['categoryid', 'parentid'],
        'date_columns': [],
        'numeric_columns': ['categoryid', 'parentid'],
        'categorical_columns': [],
        'primary_key': 'categoryid'
    },
    'retailrocket_events': {
        'name': 'RetailRocket Events',
        'file_name': 'events.csv',
        'delimiter': ',',
        'encoding': 'utf-8',
        'description': 'User interaction events (views, add to cart, transactions)',
        'columns': {
            'timestamp': 'int64',
            'visitorid': 'int64',
            'event': 'str',
            'itemid': 'int64',
            'transactionid': 'str'
        },
        'required_columns': ['timestamp', 'visitorid', 'event', 'itemid'],
        'date_columns': [],
        'numeric_columns': ['timestamp', 'visitorid', 'itemid'],
        'categorical_columns': ['event'],
        'primary_key': None  # Composite key: timestamp + visitorid + itemid + event
    },
    'retailrocket_item_properties': {
        'name': 'RetailRocket Item Properties',
        'file_name': 'item_properties_part1.csv',  # Will handle both parts
        'delimiter': ',',
        'encoding': 'utf-8',
        'description': 'Item properties and attributes for RetailRocket dataset',
        'columns': {
            'timestamp': 'int64',
            'itemid': 'int64',
            'property': 'str',
            'value': 'str'
        },
        'required_columns': ['timestamp', 'itemid', 'property', 'value'],
        'date_columns': [],
        'numeric_columns': ['timestamp', 'itemid'],
        'categorical_columns': ['property'],
        'primary_key': None  # Composite key: timestamp + itemid + property
    },
    'uci_online_retail_2': {
        'name': 'UCI Online Retail II',
        'file_name': 'online_retail_2.xlsx',
        'sheet_names': ['Year 2009-2010', 'Year 2010-2011'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'description': 'Online retail transactional data from UCI dataset',
        'columns': {
            'Invoice': 'str',
            'StockCode': 'str',
            'Description': 'str',
            'Quantity': 'int64',
            'InvoiceDate': 'datetime64[ns]',
            'Price': 'float64',
            'Customer ID': 'int64',
            'Country': 'str'
        },
        'required_columns': ['Invoice', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'Price'],
        'date_columns': ['InvoiceDate'],
        'numeric_columns': ['Quantity', 'Price', 'Customer ID'],
        'categorical_columns': ['Invoice', 'StockCode', 'Description', 'Country'],
        'primary_key': None  # Transactional data, no single primary key
    }
}

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE_CONFIG = {
    'client1_DB': {
        'database': 'client1_DB',
        'host': 'localhost',
        'port': 5440,
        'user': 'postgres',
        'password': 'Redouan12.'
    },
    'client1_DW': {
        'database': 'client1_DW',
        'host': 'localhost',
        'port': 5440,
        'user': 'postgres',
        'password': 'Redouan12.'
    }
}

# Schema configuration (separate from connection)
SCHEMA_CONFIG = {
    'client1_DB': 'raw_data',
    'client1_DW': 'analytics'
}

# ============================================================================
# DATA INGESTION RULES
# ============================================================================

INGESTION_RULES = {
    'minimal_preprocessing': {
        'fix_encoding': True,
        'handle_missing_values': True,
        'convert_dates': True,
        'validate_data_types': True,
        'check_required_columns': True,
        'preserve_original_format': True  # Key principle: keep original data
    },
    'data_quality': {
        'allow_missing_income': True,  # 24 records have missing income
        'min_year_birth': 1900,
        'max_year_birth': datetime.now().year,
        'min_income': 0,
        'max_income': 1000000
    }
}

# ============================================================================
# PATHS
# ============================================================================

# Base paths - Go up 5 levels from config.py to reach CustomerDNA AI directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
DATA_DIR = os.path.join(BASE_DIR, 'datasets', 'client_1')

# Dataset paths
DATASET_PATHS = {
    'customer_personality_analysis': os.path.join(
        DATA_DIR, 'Customer_Personality_Analysis', 'marketing_campaign.csv'
    ),
    'ecommerce_customer_churn': os.path.join(
        DATA_DIR, 'E-commerce_customer_churn', 'E-commerce_customer_churn.xlsx'
    ),
    'retailrocket_category_tree': os.path.join(
        DATA_DIR, 'Retailrocket_recommender_system_dataset', 'category_tree.csv'
    ),
    'retailrocket_events': os.path.join(
        DATA_DIR, 'Retailrocket_recommender_system_dataset', 'events.csv'
    ),
    'retailrocket_item_properties': os.path.join(
        DATA_DIR, 'Retailrocket_recommender_system_dataset', 'item_properties_part1.csv'
    ),
    'uci_online_retail_2': os.path.join(
        DATA_DIR, 'UCI_Online_Retail_2', 'online_retail_2.xlsx'
    )
}

# Logging
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_dataset_config(dataset_name):
    """Get configuration for a specific dataset."""
    return DATASET_CONFIG.get(dataset_name, {})

def get_database_config(database_name):
    """Get configuration for a specific database."""
    return DATABASE_CONFIG.get(database_name, {})

def get_dataset_path(dataset_name):
    """Get file path for a specific dataset."""
    return DATASET_PATHS.get(dataset_name, '')

def get_log_file_path():
    """Get path for ingestion log file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join(LOG_DIR, f'data_ingestion_{timestamp}.log')