"""
CustomerDNA AI - Global Data Warehouse Configuration
Description: Basic configuration for the centralized data warehouse
             No orchestration logic - Apache Airflow will be integrated later
"""

import os

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Global Data Warehouse Database
GLOBAL_DW_CONFIG = {
    'database': 'Global_DW',
    'host': 'localhost',
    'port': 5440,  # Changed to match your PostgreSQL port
    'user': 'postgres',
    'password': 'Redouan12.',  # Your PostgreSQL password
    'schema': 'global_dw'
}

# Client Data Warehouse Configuration (for connecting to client DWs)
CLIENT_DW_TEMPLATE = {
    'host': 'localhost',
    'port': 5440,  # Changed to match your PostgreSQL port
    'user': 'postgres',
    'password': 'Redouan12.',  # Your PostgreSQL password
    'schema': 'analytics'  # Default schema in client DW
}

# ============================================================================
# PATHS AND DIRECTORIES
# ============================================================================

# Base project directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Data directories
DATA_DIRECTORIES = {
    'clients_data': os.path.join(PROJECT_ROOT, 'datasets'),
    'preprocessed_data': os.path.join(PROJECT_ROOT, 'src', 'Preprocessing'),
    'etl_logs': os.path.join(PROJECT_ROOT, 'src', 'ETL', 'Global_DW', 'logs'),
    'client_configs': os.path.join(PROJECT_ROOT, 'src', 'ETL', 'client_1')
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_global_dw_connection_params():
    """Get connection parameters for Global_DW."""
    return {
        'host': GLOBAL_DW_CONFIG['host'],
        'port': GLOBAL_DW_CONFIG['port'],
        'user': GLOBAL_DW_CONFIG['user'],
        'password': GLOBAL_DW_CONFIG['password'],
        'database': GLOBAL_DW_CONFIG['database']
    }

def get_client_dw_connection_params(client_db_name):
    """Get connection parameters for a client data warehouse."""
    return {
        'host': CLIENT_DW_TEMPLATE['host'],
        'port': CLIENT_DW_TEMPLATE['port'],
        'user': CLIENT_DW_TEMPLATE['user'],
        'password': CLIENT_DW_TEMPLATE['password'],
        'database': client_db_name
    }

def get_client_base_db_name(client_id):
    """Get base database name for a client."""
    return f"client{client_id}_DB"

def get_client_dw_db_name(client_id):
    """Get data warehouse database name for a client."""
    return f"client{client_id}_DW"

def get_client_database_name(client_id: str) -> str:
    """Generate database name for a specific client."""
    return f"{CLIENT_BASE_DB_TEMPLATE['database_prefix']}_{client_id}_Base_DB"

def get_client_dw_database_name(client_id: str) -> str:
    """Generate data warehouse database name for a specific client."""
    return f"{CLIENT_BASE_DB_TEMPLATE['database_prefix']}_{client_id}_DW"

def get_client_config_path(client_id: str) -> str:
    """Get the configuration file path for a specific client."""
    return os.path.join(
        DATA_DIRECTORIES['client_configs'], 
        client_id, 
        'config.py'
    )

def get_preprocessed_data_path(client_id: str, dataset_name: str) -> str:
    """Get the path to preprocessed data for a specific client and dataset."""
    return os.path.join(
        DATA_DIRECTORIES['preprocessed_data'],
        client_id,
        f"{dataset_name}_Preprocessing",
        "cleaned_dataset"
    )

# ============================================================================
# VERSION INFORMATION
# ============================================================================

VERSION = "1.0.0"
LAST_UPDATED = "2026-06-13"
AUTHOR = "CustomerDNA AI Team"

if __name__ == "__main__":
    print("=" * 80)
    print("CUSTOMERDNA AI - GLOBAL DATA WAREHOUSE CONFIGURATION")
    print("=" * 80)
    print(f"Version: {VERSION}")
    print(f"Last Updated: {LAST_UPDATED}")
    print(f"Author: {AUTHOR}")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Global DW Database: {GLOBAL_DW_CONFIG['database']}")
    print("=" * 80)