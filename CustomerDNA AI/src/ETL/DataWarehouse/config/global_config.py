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
    'database': 'CustomerDNA_AI_Global_DW',
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',  # Change this in production
    'schema': 'global_dw'
}

# Base Database for each client (template)
CLIENT_BASE_DB_TEMPLATE = {
    'database_prefix': 'CustomerDNA_AI_Client',
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',  # Change this in production
    'schema': 'raw_data'
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
    'etl_logs': os.path.join(PROJECT_ROOT, 'src', 'ETL', 'DataWarehouse', 'logs'),
    'client_configs': os.path.join(PROJECT_ROOT, 'src', 'ETL', 'setup_database_for_each_clients_datasets')
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

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