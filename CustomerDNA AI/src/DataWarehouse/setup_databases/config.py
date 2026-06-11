"""
CustomerDNA AI - Database Configuration
Simple configuration for dual database architecture
"""

import os

# Database names
BASE_DATABASE_NAME = "CustomerDNA_AI_base_DB"
DATA_WAREHOUSE_NAME = "CustomerDNA_AI_DW"

# PostgreSQL connection parameters (update these with your credentials)
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5440,
    'user': 'postgres',
    'password': 'Redouan12.',  # Change this to your PostgreSQL password
    'database': 'postgres'  # Default database for creating new databases
}

# Base Database Configuration
BASE_DB_CONFIG = {
    'name': BASE_DATABASE_NAME,
    'description': 'Raw data storage with automated CSV ingestion',
    'schemas': ['raw_data', 'metadata'],
    'default_schema': 'raw_data'
}

# Data Warehouse Configuration
DW_CONFIG = {
    'name': DATA_WAREHOUSE_NAME,
    'description': 'Main analytical data warehouse',
    'schemas': ['raw_data', 'analytics', 'reports', 'user_tables'],
    'default_schema': 'analytics'
}

# User Configuration - Single superadmin user
USER_CONFIG = {
    'superadmin': {
        'password': 'Redouan12.',
        'description': 'Superadmin user with full access to everything'
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