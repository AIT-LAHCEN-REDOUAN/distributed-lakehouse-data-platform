"""
CustomerDNA AI - Client 1 Data Warehouse Configuration

Simplified ELT Architecture:
    Ingested CSV files
        -> client1_DW.raw_data
        -> dbt transformations
        -> client1_DW.analytics

Important:
    This config uses ONLY:
        src/ELT/client_1/.env

It does NOT use:
    src/airflow/.env
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


# ============================================================================
# PATHS
# ============================================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# CURRENT_DIR:
# CustomerDNA AI/src/ELT/client_1/config
CLIENT_ELT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

# CLIENT_ELT_DIR:
# CustomerDNA AI/src/ELT/client_1
CLIENT_ENV_PATH = os.path.join(CLIENT_ELT_DIR, ".env")

# PROJECT_ROOT:
# CustomerDNA AI
PROJECT_ROOT = os.path.abspath(
    os.path.join(CLIENT_ELT_DIR, "..", "..", "..")
)

SRC_DIR = os.path.join(PROJECT_ROOT, "src")

INGESTED_DATA_DIR = os.path.join(
    SRC_DIR,
    "Data_Ingestion",
    "client_1",
    "ingested_data",
)


# ============================================================================
# LOAD CLIENT-SPECIFIC ENVIRONMENT
# ============================================================================

if load_dotenv:
    if os.path.exists(CLIENT_ENV_PATH):
        load_dotenv(CLIENT_ENV_PATH)
    else:
        print(f"[WARNING] Client .env file not found: {CLIENT_ENV_PATH}")
else:
    print("[WARNING] python-dotenv is not installed. Environment variables will not be loaded from .env.")


# ============================================================================
# CLIENT CONFIGURATION
# ============================================================================

CLIENT_ID = os.getenv("CLIENT_ID", "1")
CLIENT_NAME = os.getenv("CLIENT_NAME", "Client 1")

DATA_WAREHOUSE_NAME = f"client{CLIENT_ID}_DW"


# ============================================================================
# POSTGRESQL CONFIGURATION
# ============================================================================

POSTGRES_CONFIG = {
    "host": os.getenv("CUSTOMERDNA_POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("CUSTOMERDNA_POSTGRES_PORT", "5440")),
    "user": os.getenv("CUSTOMERDNA_POSTGRES_USER", "postgres"),
    "password": os.getenv("CUSTOMERDNA_POSTGRES_PASSWORD", ""),
    "database": "postgres",
}


# ============================================================================
# DATA WAREHOUSE CONFIGURATION
# ============================================================================

CLIENT_DW_CONFIG = {
    "name": DATA_WAREHOUSE_NAME,
    "description": f"Client-specific Data Warehouse for {CLIENT_NAME}",
    "schemas": [
        "raw_data",
        "metadata",
        "staging",
        "intermediate",
        "analytics",
        "reports",
        "client_specific",
    ],
    "raw_schema": "raw_data",
    "metadata_schema": "metadata",
    "staging_schema": "staging",
    "intermediate_schema": "intermediate",
    "analytics_schema": "analytics",
    "reports_schema": "reports",
    "client_specific_schema": "client_specific",
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_connection_params(database_name="postgres"):
    """
    Return PostgreSQL connection parameters for a specific database.
    """
    params = POSTGRES_CONFIG.copy()
    params["database"] = database_name
    return params


def validate_config():
    """
    Validate required configuration.
    """
    missing = []

    if not POSTGRES_CONFIG["password"]:
        missing.append("CUSTOMERDNA_POSTGRES_PASSWORD")

    if missing:
        print("[WARNING] Missing required environment variables:")
        for item in missing:
            print(f"  - {item}")

        print(f"\nPlease check this file:")
        print(f"  {CLIENT_ENV_PATH}")

        print("\nExpected example:")
        print("CUSTOMERDNA_POSTGRES_HOST=localhost")
        print("CUSTOMERDNA_POSTGRES_PORT=5440")
        print("CUSTOMERDNA_POSTGRES_USER=postgres")
        print("CUSTOMERDNA_POSTGRES_PASSWORD=your_password")
        print("CLIENT_ID=1")
        print("CLIENT_NAME=Client 1")

        return False

    return True


def print_config_summary():
    """
    Print configuration summary.
    Password is intentionally hidden.
    """
    print("=" * 70)
    print("CUSTOMERDNA AI - CLIENT 1 DW CONFIGURATION")
    print("=" * 70)

    print("\nCLIENT:")
    print(f"  ID: {CLIENT_ID}")
    print(f"  Name: {CLIENT_NAME}")

    print("\nDATA WAREHOUSE:")
    print(f"  Name: {DATA_WAREHOUSE_NAME}")
    print(f"  Schemas: {', '.join(CLIENT_DW_CONFIG['schemas'])}")

    print("\nPOSTGRESQL:")
    print(f"  Host: {POSTGRES_CONFIG['host']}")
    print(f"  Port: {POSTGRES_CONFIG['port']}")
    print(f"  User: {POSTGRES_CONFIG['user']}")
    print("  Password: ********")

    print("\nPATHS:")
    print(f"  Client ELT directory: {CLIENT_ELT_DIR}")
    print(f"  Client .env: {CLIENT_ENV_PATH}")
    print(f"  Project root: {PROJECT_ROOT}")
    print(f"  Ingested data: {INGESTED_DATA_DIR}")

    print("\nFLOW:")
    print("  CSV -> client1_DW.raw_data -> dbt -> client1_DW.analytics")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    validate_config()
    print_config_summary()