"""
CustomerDNA AI - Client 1 Database Configuration
Description: Configuration for client_1 database and data warehouse setup
             No orchestration logic - Apache Airflow will be integrated later
"""

import os

# ============================================================================
# CLIENT-SPECIFIC CONFIGURATION
# ============================================================================

# Client Identification
CLIENT_ID = "1"
CLIENT_NAME = "Client 1"

# Database Configuration
BASE_DATABASE_NAME = f"client{CLIENT_ID}_DB"
DATA_WAREHOUSE_NAME = f"client{CLIENT_ID}_DW"

# PostgreSQL connection parameters
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5440,
    'user': 'postgres',
    'password': 'Redouan12.',  # Your PostgreSQL password
    'database': 'postgres'  # Default database for creating new databases
}

# Base Database Configuration (static storage)
BASE_DB_CONFIG = {
    'name': BASE_DATABASE_NAME,
    'description': f'Raw data storage for {CLIENT_NAME} - Static',
    'schemas': ['raw_data', 'metadata'],
    'default_schema': 'raw_data',
    'access': 'read_only'  # Data should not be modified here
}

# Client Data Warehouse Configuration (for client-specific analytics)
CLIENT_DW_CONFIG = {
    'name': DATA_WAREHOUSE_NAME,
    'description': f'Client-specific data warehouse for {CLIENT_NAME}',
    'schemas': ['raw_data', 'analytics', 'reports', 'client_specific'],
    'default_schema': 'analytics',
    'access': 'read_write'  # Analytical users can modify data here
}

# User Configuration
USER_CONFIG = {
    'superadmin': {
        'password': 'Redouan12.',  # Your PostgreSQL password
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

def print_config_summary():
    """Print a summary of the configuration."""
    print("=" * 60)
    print("CUSTOMERDNA AI - CLIENT 1 DATABASE CONFIGURATION")
    print("=" * 60)
    
    print(f"\n1. BASE DATABASE (Static Storage):")
    print(f"   Name: {BASE_DATABASE_NAME}")
    print(f"   Description: {BASE_DB_CONFIG['description']}")
    print(f"   Schemas: {', '.join(BASE_DB_CONFIG['schemas'])}")
    print(f"   Access: {BASE_DB_CONFIG['access']}")
    
    print(f"\n2. CLIENT DATA WAREHOUSE (Analytics):")
    print(f"   Name: {DATA_WAREHOUSE_NAME}")
    print(f"   Description: {CLIENT_DW_CONFIG['description']}")
    print(f"   Schemas: {', '.join(CLIENT_DW_CONFIG['schemas'])}")
    print(f"   Access: {CLIENT_DW_CONFIG['access']}")
    
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