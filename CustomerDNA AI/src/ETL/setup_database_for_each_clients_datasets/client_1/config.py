"""
CustomerDNA AI - Client Database Configuration
Description: Basic configuration for client_1 database setup
             No orchestration logic - Apache Airflow will be integrated later
"""

import os

# ============================================================================
# CLIENT-SPECIFIC CONFIGURATION
# ============================================================================

# Client Identification
CLIENT_ID = "client_1"
CLIENT_NAME = "Client 1"

# Database Configuration
BASE_DATABASE_NAME = f"CustomerDNA_AI_Client_{CLIENT_ID}_Base_DB"
DATA_WAREHOUSE_NAME = f"CustomerDNA_AI_Client_{CLIENT_ID}_DW"

# PostgreSQL connection parameters
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5440,
    'user': 'postgres',
    'password': 'Redouan12.',  # Your PostgreSQL password
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
        'password': 'Redouan12.',  # Your PostgreSQL password
        'description': f'Superadmin user for {CLIENT_NAME}'
    }
}

def get_connection_params(database_name='postgres'):
    """Get connection parameters for a specific database."""
    params = POSTGRES_CONFIG.copy()
    params['database'] = database_name
    return params

def print_config_summary():
    """Print a summary of the configuration."""
    print("=" * 60)
    print("CUSTOMERDNA AI - DATABASE CONFIGURATION SUMMARY")
    print("=" * 60)
    
    print(f"\n1. BASE DATABASE: {BASE_DATABASE_NAME}")
    print(f"   Description: {BASE_DB_CONFIG['description']}")
    print(f"   Schemas: {', '.join(BASE_DB_CONFIG['schemas'])}")
    
    print(f"\n2. DATA WAREHOUSE: {DATA_WAREHOUSE_NAME}")
    print(f"   Description: {DW_CONFIG['description']}")
    print(f"   Schemas: {', '.join(DW_CONFIG['schemas'])}")
    
    print(f"\n3. USER:")
    for user_name, user_config in USER_CONFIG.items():
        print(f"   • {user_name}: {user_config['description']}")
    
    print(f"\n4. POSTGRESQL CONNECTION:")
    print(f"   Host: {POSTGRES_CONFIG['host']}")
    print(f"   Port: {POSTGRES_CONFIG['port']}")
    print(f"   User: {POSTGRES_CONFIG['user']}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print_config_summary()