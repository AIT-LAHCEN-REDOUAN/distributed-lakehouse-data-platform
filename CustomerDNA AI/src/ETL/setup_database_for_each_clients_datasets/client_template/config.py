"""
CustomerDNA AI - Client Database Configuration Template
Description: Basic configuration for client-specific database setup
             No orchestration logic - Apache Airflow will be integrated later
             Replace CLIENT_ID and other placeholders with actual values
"""

import os

# ============================================================================
# CLIENT-SPECIFIC CONFIGURATION
# ============================================================================

# Client Identification (REPLACE THESE VALUES)
CLIENT_ID = "template"           # Replace with actual client ID (e.g., "client_1")
CLIENT_NAME = "Template Client"  # Replace with actual client name

# Database Configuration
BASE_DATABASE_NAME = f"CustomerDNA_AI_Client_{CLIENT_ID}_Base_DB"
DATA_WAREHOUSE_NAME = f"CustomerDNA_AI_Client_{CLIENT_ID}_DW"

# PostgreSQL connection parameters
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',  # Change this for production
    'database': 'postgres'  # Default database for creating new databases
}

# Base Database Configuration
BASE_DB_CONFIG = {
    'name': BASE_DATABASE_NAME,
    'description': f'Raw data storage for {CLIENT_NAME}',
    'schemas': ['raw_data', 'metadata'],
    'default_schema': 'raw_data'
}

# Data Warehouse Configuration
DW_CONFIG = {
    'name': DATA_WAREHOUSE_NAME,
    'description': f'Analytical data warehouse for {CLIENT_NAME}',
    'schemas': ['raw_data', 'analytics', 'reports'],
    'default_schema': 'analytics'
}

# User Configuration
USER_CONFIG = {
    'superadmin': {
        'password': 'ChangeThisPassword123!',  # MUST change this
        'description': f'Superadmin user for {CLIENT_NAME}'
    }
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_connection_params(database_name='postgres'):
    """Get connection parameters for a specific database."""
    params = POSTGRES_CONFIG.copy()
    params['database'] = database_name
    return params

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print(f"CUSTOMERDNA AI - CLIENT DATABASE CONFIGURATION")
    print("=" * 80)
    print(f"Client ID: {CLIENT_ID}")
    print(f"Client Name: {CLIENT_NAME}")
    print(f"Base Database: {BASE_DATABASE_NAME}")
    print(f"Data Warehouse: {DATA_WAREHOUSE_NAME}")
    print("=" * 80)