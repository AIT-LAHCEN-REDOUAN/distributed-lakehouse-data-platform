"""
CustomerDNA AI - Setup Global Data Warehouse
Creates and configures the global data warehouse database
"""

import sys
import psycopg2
from psycopg2 import sql
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
from global_config import (
    GLOBAL_DW_CONFIG, get_global_dw_connection_params,
    get_client_dw_db_name
)

class GlobalDWSetup:
    """Sets up the global data warehouse."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.conn = None
    
    def log(self, message, level="INFO"):
        """Log message with simple formatting."""
        if self.verbose:
            if level == "ERROR":
                print(f"[ERROR] {message}")
            elif level == "SUCCESS":
                print(f"[SUCCESS] {message}")
            else:
                print(f"[INFO] {message}")
    
    def connect_to_postgres(self):
        """Connect to PostgreSQL server."""
        try:
            # Connect to default postgres database
            conn_params = get_global_dw_connection_params()
            conn_params['database'] = 'postgres'  # Connect to default database
            
            self.conn = psycopg2.connect(**conn_params)
            self.conn.autocommit = True
            self.log("Connected to PostgreSQL server")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to connect to PostgreSQL: {str(e)}", "ERROR")
            return False
    
    def database_exists(self, db_name):
        """Check if a database exists."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone() is not None
            cursor.close()
            
            return exists
            
        except Exception as e:
            self.log(f"Failed to check if database exists: {str(e)}", "ERROR")
            return False
    
    def create_database(self):
        """Create the global data warehouse database."""
        try:
            cursor = self.conn.cursor()
            
            # Check if database already exists
            if self.database_exists(GLOBAL_DW_CONFIG['database']):
                self.log(f"Database {GLOBAL_DW_CONFIG['database']} already exists")
                cursor.close()
                return True
            
            # Create database
            create_db_sql = sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(GLOBAL_DW_CONFIG['database'])
            )
            cursor.execute(create_db_sql)
            
            self.log(f"Created database: {GLOBAL_DW_CONFIG['database']}")
            cursor.close()
            
            return True
            
        except Exception as e:
            self.log(f"Failed to create database: {str(e)}", "ERROR")
            return False
    
    def connect_to_global_dw(self):
        """Connect to the global data warehouse database."""
        try:
            self.conn = psycopg2.connect(**get_global_dw_connection_params())
            self.conn.autocommit = True
            self.log(f"Connected to global data warehouse: {GLOBAL_DW_CONFIG['database']}")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to connect to global DW: {str(e)}", "ERROR")
            return False
    
    def create_schema(self):
        """Create the global_dw schema."""
        try:
            cursor = self.conn.cursor()
            
            # Create schema if it doesn't exist
            create_schema_sql = sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                sql.Identifier(GLOBAL_DW_CONFIG['schema'])
            )
            cursor.execute(create_schema_sql)
            
            self.log(f"Created/verified schema: {GLOBAL_DW_CONFIG['schema']}")
            cursor.close()
            
            return True
            
        except Exception as e:
            self.log(f"Failed to create schema: {str(e)}", "ERROR")
            return False
    
    def create_tables(self):
        """Create tables in the global data warehouse."""
        try:
            cursor = self.conn.cursor()
            schema = GLOBAL_DW_CONFIG['schema']
            
            # 1. clients table - metadata about each client
            self.log("Creating clients table...")
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {}.clients (
                    client_id SERIAL PRIMARY KEY,
                    client_name VARCHAR(100) NOT NULL,
                    client_code VARCHAR(50) UNIQUE NOT NULL,
                    industry VARCHAR(100),
                    country VARCHAR(50),
                    onboard_date DATE,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """).format(sql.Identifier(schema)))
            
            # 2. global_customers table - aggregated customer data
            self.log("Creating global_customers table...")
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {}.global_customers (
                    global_customer_id SERIAL PRIMARY KEY,
                    client_id INTEGER REFERENCES {}.clients(client_id),
                    source_customer_id VARCHAR(100),
                    age INTEGER,
                    age_group VARCHAR(50),
                    gender VARCHAR(20),
                    income DECIMAL(15,2),
                    education VARCHAR(100),
                    marital_status VARCHAR(50),
                    country VARCHAR(50),
                    city VARCHAR(100),
                    total_spending DECIMAL(15,2),
                    total_transactions INTEGER,
                    avg_transaction_value DECIMAL(15,2),
                    last_purchase_date DATE,
                    customer_tenure_days INTEGER,
                    customer_segment VARCHAR(50),
                    churn_risk_score DECIMAL(5,2),
                    rfm_segment VARCHAR(50),
                    data_source VARCHAR(100),
                    sync_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(client_id, source_customer_id)
                )
            """).format(sql.Identifier(schema), sql.Identifier(schema)))
            
            # 3. global_transactions table - standardized transaction data
            self.log("Creating global_transactions table...")
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {}.global_transactions (
                    transaction_id SERIAL PRIMARY KEY,
                    global_customer_id INTEGER REFERENCES {}.global_customers(global_customer_id),
                    client_id INTEGER REFERENCES {}.clients(client_id),
                    transaction_date DATE,
                    transaction_time TIME,
                    invoice_number VARCHAR(100),
                    product_id VARCHAR(100),
                    product_category VARCHAR(100),
                    quantity INTEGER,
                    unit_price DECIMAL(15,2),
                    total_amount DECIMAL(15,2),
                    currency VARCHAR(10),
                    payment_method VARCHAR(50),
                    channel VARCHAR(50),
                    country VARCHAR(50),
                    city VARCHAR(100),
                    data_source VARCHAR(100),
                    sync_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """).format(sql.Identifier(schema), sql.Identifier(schema), sql.Identifier(schema)))
            
            # 4. global_interactions table - user interaction data
            self.log("Creating global_interactions table...")
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {}.global_interactions (
                    interaction_id SERIAL PRIMARY KEY,
                    global_customer_id INTEGER REFERENCES {}.global_customers(global_customer_id),
                    client_id INTEGER REFERENCES {}.clients(client_id),
                    interaction_type VARCHAR(50),
                    interaction_date DATE,
                    interaction_time TIME,
                    item_id VARCHAR(100),
                    item_category VARCHAR(100),
                    session_id VARCHAR(100),
                    duration_seconds INTEGER,
                    interaction_score DECIMAL(5,2),
                    platform VARCHAR(50),
                    device_type VARCHAR(50),
                    country VARCHAR(50),
                    data_source VARCHAR(100),
                    sync_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """).format(sql.Identifier(schema), sql.Identifier(schema), sql.Identifier(schema)))
            
            # 5. global_rfm_segments table - customer segmentation
            self.log("Creating global_rfm_segments table...")
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {}.global_rfm_segments (
                    rfm_id SERIAL PRIMARY KEY,
                    global_customer_id INTEGER REFERENCES {}.global_customers(global_customer_id),
                    client_id INTEGER REFERENCES {}.clients(client_id),
                    recency_days INTEGER,
                    frequency_count INTEGER,
                    monetary_value DECIMAL(15,2),
                    r_score INTEGER,
                    f_score INTEGER,
                    m_score INTEGER,
                    rfm_score INTEGER,
                    rfm_segment VARCHAR(50),
                    segment_date DATE,
                    data_source VARCHAR(100),
                    sync_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(global_customer_id, segment_date)
                )
            """).format(sql.Identifier(schema), sql.Identifier(schema), sql.Identifier(schema)))
            
            # 6. global_churn_metrics table - churn analysis
            self.log("Creating global_churn_metrics table...")
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {}.global_churn_metrics (
                    churn_id SERIAL PRIMARY KEY,
                    global_customer_id INTEGER REFERENCES {}.global_customers(global_customer_id),
                    client_id INTEGER REFERENCES {}.clients(client_id),
                    churn_status BOOLEAN,
                    churn_date DATE,
                    tenure_days INTEGER,
                    avg_purchase_frequency DECIMAL(10,2),
                    avg_purchase_value DECIMAL(15,2),
                    last_purchase_days_ago INTEGER,
                    complaint_count INTEGER,
                    campaign_response_rate DECIMAL(5,2),
                    churn_probability DECIMAL(5,2),
                    churn_reason VARCHAR(200),
                    data_source VARCHAR(100),
                    sync_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(global_customer_id)
                )
            """).format(sql.Identifier(schema), sql.Identifier(schema), sql.Identifier(schema)))
            
            # 7. data_sync_log table - synchronization logs
            self.log("Creating data_sync_log table...")
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {}.data_sync_log (
                    log_id SERIAL PRIMARY KEY,
                    client_id INTEGER REFERENCES {}.clients(client_id),
                    sync_type VARCHAR(50),
                    table_name VARCHAR(100),
                    records_processed INTEGER,
                    records_inserted INTEGER,
                    records_updated INTEGER,
                    records_failed INTEGER,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    status VARCHAR(20),
                    error_message TEXT,
                    sync_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """).format(sql.Identifier(schema), sql.Identifier(schema)))
            
            cursor.close()
            self.log("All tables created successfully", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to create tables: {str(e)}", "ERROR")
            return False
    
    def setup_global_dw(self):
        """Run the full setup process."""
        print("=" * 60)
        print("CUSTOMERDNA AI - SETUP GLOBAL DATA WAREHOUSE")
        print("=" * 60)
        
        # Step 1: Connect to PostgreSQL
        if not self.connect_to_postgres():
            return False
        
        # Step 2: Create database
        if not self.create_database():
            return False
        
        # Step 3: Connect to Global DW
        if not self.connect_to_global_dw():
            return False
        
        # Step 4: Create schema
        if not self.create_schema():
            return False
        
        # Step 5: Create tables
        if not self.create_tables():
            return False
        
        print("\n" + "=" * 60)
        print("SETUP COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Global Data Warehouse: {GLOBAL_DW_CONFIG['database']}")
        print(f"Schema: {GLOBAL_DW_CONFIG['schema']}")
        print("\nTables created:")
        print("  • clients")
        print("  • global_customers")
        print("  • global_transactions")
        print("  • global_interactions")
        print("  • global_rfm_segments")
        print("  • global_churn_metrics")
        print("  • data_sync_log")
        
        return True

def main():
    """Main function."""
    setup = GlobalDWSetup(verbose=True)
    success = setup.setup_global_dw()
    
    if success:
        print("\n[SUCCESS] Global Data Warehouse setup completed!")
        print("\nNext steps:")
        print("  1. Add client metadata to the clients table")
        print("  2. Run the data loader to populate Global_DW from client DWs")
        return 0
    else:
        print("\n[ERROR] Global Data Warehouse setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())