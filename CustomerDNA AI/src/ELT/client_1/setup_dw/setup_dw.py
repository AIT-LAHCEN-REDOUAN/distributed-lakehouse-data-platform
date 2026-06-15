"""
CustomerDNA AI - Client 1 Data Warehouse Setup
Creates the client-specific data warehouse for client_1 analytics
This database is for analytical work and can be modified
"""

import sys
import psycopg2
from psycopg2 import sql
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from config import (
    DATA_WAREHOUSE_NAME, CLIENT_DW_CONFIG,
    POSTGRES_CONFIG, get_connection_params
)

class ClientDWSetup:
    """Sets up the client-specific data warehouse for client_1 analytics."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.postgres_conn = None
        self.dw_conn = None
    
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
            self.postgres_conn = psycopg2.connect(**get_connection_params())
            self.postgres_conn.autocommit = True
            self.log(f"Connected to PostgreSQL server")
            return True
        except Exception as e:
            self.log(f"Failed to connect to PostgreSQL: {str(e)}", "ERROR")
            return False
    
    def create_database(self):
        """Create the data warehouse database."""
        try:
            cursor = self.postgres_conn.cursor()
            
            # Check if database already exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DATA_WAREHOUSE_NAME,))
            if cursor.fetchone():
                self.log(f"Database '{DATA_WAREHOUSE_NAME}' already exists")
                return True
            
            # Create database
            create_sql = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DATA_WAREHOUSE_NAME))
            cursor.execute(create_sql)
            self.log(f"Created database: {DATA_WAREHOUSE_NAME} - {CLIENT_DW_CONFIG['description']}")
            
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to create database '{DATA_WAREHOUSE_NAME}': {str(e)}", "ERROR")
            return False
    
    def connect_to_dw(self):
        """Connect to the data warehouse database."""
        try:
            self.dw_conn = psycopg2.connect(**get_connection_params(DATA_WAREHOUSE_NAME))
            self.dw_conn.autocommit = True
            self.log(f"Connected to database: {DATA_WAREHOUSE_NAME}")
            return True
        except Exception as e:
            self.log(f"Failed to connect to database '{DATA_WAREHOUSE_NAME}': {str(e)}", "ERROR")
            return None
    
    def create_schemas(self):
        """Create schemas in the data warehouse."""
        try:
            cursor = self.dw_conn.cursor()
            
            for schema in CLIENT_DW_CONFIG['schemas']:
                create_sql = sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema))
                cursor.execute(create_sql)
                self.log(f"Created schema: {schema}")
            
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to create schemas: {str(e)}", "ERROR")
            return False
    
    def set_database_permissions(self):
        """Set read-write permissions on the data warehouse."""
        try:
            cursor = self.postgres_conn.cursor()
            
            # Revoke all privileges from public
            revoke_sql = sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(
                sql.Identifier(DATA_WAREHOUSE_NAME)
            )
            cursor.execute(revoke_sql)
            
            # Grant all privileges to superadmin
            grant_sql = sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO superadmin").format(
                sql.Identifier(DATA_WAREHOUSE_NAME)
            )
            cursor.execute(grant_sql)
            
            # Connect to DW database to set schema permissions
            dw_cursor = self.dw_conn.cursor()
            
            # Set schema permissions
            for schema in CLIENT_DW_CONFIG['schemas']:
                # Grant all privileges on schema
                dw_cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON SCHEMA {} TO superadmin").format(
                    sql.Identifier(schema)
                ))
                
                # Grant all privileges on all tables in schema (future tables included)
                dw_cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {} TO superadmin").format(
                    sql.Identifier(schema)
                ))
                
                # Grant all privileges on all sequences in schema
                dw_cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {} TO superadmin").format(
                    sql.Identifier(schema)
                ))
                
                # Set default privileges for future objects
                dw_cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT ALL PRIVILEGES ON TABLES TO superadmin").format(
                    sql.Identifier(schema)
                ))
                dw_cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT ALL PRIVILEGES ON SEQUENCES TO superadmin").format(
                    sql.Identifier(schema)
                ))
            
            dw_cursor.close()
            cursor.close()
            
            self.log(f"Set read-write permissions on {DATA_WAREHOUSE_NAME}")
            return True
            
        except Exception as e:
            self.log(f"Failed to set permissions: {str(e)}", "ERROR")
            return False
    
    def create_analytical_tables(self):
        """Create example analytical tables in the analytics schema."""
        try:
            cursor = self.dw_conn.cursor()
            
            # Example: Customer segmentation table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.customer_segments (
                    customer_id TEXT PRIMARY KEY,
                    segment TEXT NOT NULL,
                    recency_score INTEGER,
                    frequency_score INTEGER,
                    monetary_score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.log("Created table: analytics.customer_segments")
            
            # Example: Sales summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.sales_summary (
                    date DATE PRIMARY KEY,
                    total_sales DECIMAL(10,2),
                    total_orders INTEGER,
                    avg_order_value DECIMAL(10,2),
                    unique_customers INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.log("Created table: analytics.sales_summary")
            
            # Example: Product performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.product_performance (
                    product_id TEXT PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    total_quantity_sold INTEGER,
                    total_revenue DECIMAL(10,2),
                    avg_rating DECIMAL(3,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.log("Created table: analytics.product_performance")
            
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to create analytical tables: {str(e)}", "ERROR")
            return False
    
    def create_dataset_tables(self):
        """Create empty tables for all datasets in the raw_data schema."""
        try:
            cursor = self.dw_conn.cursor()
            
            # List of dataset tables to create (based on CSV file names)
            dataset_tables = [
                # Customer Personality Analysis
                {
                    'name': 'processed_marketing_campaign',
                    'description': 'Customer Personality Analysis dataset',
                    'columns': [
                        ('customerid', 'INTEGER'),
                        ('year_birth', 'INTEGER'),
                        ('education', 'TEXT'),
                        ('marital_status', 'TEXT'),
                        ('income', 'DOUBLE PRECISION'),
                        ('kidhome', 'INTEGER'),
                        ('teenhome', 'INTEGER'),
                        ('dt_customer', 'DATE'),
                        ('recency', 'INTEGER'),
                        ('mntwines', 'INTEGER'),
                        ('mntfruits', 'INTEGER'),
                        ('mntmeatproducts', 'INTEGER'),
                        ('mntfishproducts', 'INTEGER'),
                        ('mntsweetproducts', 'INTEGER'),
                        ('mntgoldprods', 'INTEGER'),
                        ('numdealspurchases', 'INTEGER'),
                        ('numwebpurchases', 'INTEGER'),
                        ('numcatalogpurchases', 'INTEGER'),
                        ('numstorepurchases', 'INTEGER'),
                        ('numwebvisitsmonth', 'INTEGER'),
                        ('acceptedcmp3', 'INTEGER'),
                        ('acceptedcmp4', 'INTEGER'),
                        ('acceptedcmp5', 'INTEGER'),
                        ('acceptedcmp1', 'INTEGER'),
                        ('acceptedcmp2', 'INTEGER'),
                        ('complain', 'INTEGER'),
                        ('z_costcontact', 'INTEGER'),
                        ('z_revenue', 'INTEGER'),
                        ('response', 'INTEGER')
                    ]
                },
                # E-commerce Customer Churn
                {
                    'name': 'processed_e_commerce_customer_churn',
                    'description': 'E-commerce Customer Churn dataset',
                    'columns': [
                        ('customerid', 'INTEGER'),
                        ('churn', 'INTEGER'),
                        ('tenure', 'DOUBLE PRECISION'),
                        ('preferredlogindevice', 'TEXT'),
                        ('citytier', 'INTEGER'),
                        ('warehousetohome', 'DOUBLE PRECISION'),
                        ('preferredpaymentmode', 'TEXT'),
                        ('gender', 'TEXT'),
                        ('hourspendonapp', 'DOUBLE PRECISION'),
                        ('numberofdeviceregistered', 'INTEGER'),
                        ('preferredordercat', 'TEXT'),
                        ('satisfactionscore', 'INTEGER'),
                        ('maritalstatus', 'TEXT'),
                        ('numberofaddress', 'INTEGER'),
                        ('complain', 'INTEGER'),
                        ('orderamounthikefromlastyear', 'DOUBLE PRECISION'),
                        ('couponused', 'INTEGER'),
                        ('ordercount', 'INTEGER'),
                        ('daySinceLastOrder', 'DOUBLE PRECISION'),
                        ('cashbackamount', 'DOUBLE PRECISION')
                    ]
                },
                # Retailrocket dataset tables
                {
                    'name': 'category_tree_processed',
                    'description': 'Retailrocket category tree dataset',
                    'columns': [
                        ('categoryid', 'BIGINT'),
                        ('parentid', 'DOUBLE PRECISION')
                    ]
                },
                {
                    'name': 'events_processed',
                    'description': 'Retailrocket events dataset',
                    'columns': [
                        ('timestamp', 'BIGINT'),
                        ('visitorid', 'BIGINT'),
                        ('event', 'TEXT'),
                        ('itemid', 'BIGINT'),
                        ('transactionid', 'DOUBLE PRECISION')
                    ]
                },
                {
                    'name': 'item_properties_processed',
                    'description': 'Retailrocket item properties dataset',
                    'columns': [
                        ('timestamp', 'BIGINT'),
                        ('itemid', 'BIGINT'),
                        ('property', 'TEXT'),
                        ('value', 'TEXT')
                    ]
                },
                # UCI Online Retail II dataset
                {
                    'name': 'online_retail_processed',
                    'description': 'UCI Online Retail II dataset',
                    'columns': [
                        ('invoiceno', 'TEXT'),
                        ('stockcode', 'TEXT'),
                        ('description', 'TEXT'),
                        ('quantity', 'INTEGER'),
                        ('invoicedate', 'TIMESTAMP'),
                        ('unitprice', 'DOUBLE PRECISION'),
                        ('customerid', 'DOUBLE PRECISION'),
                        ('country', 'TEXT')
                    ]
                }
            ]
            
            self.log("\nCreating dataset tables in raw_data schema...")
            
            for table_config in dataset_tables:
                table_name = table_config['name']
                description = table_config['description']
                columns = table_config['columns']
                
                # Build column definitions
                column_defs = []
                for col_name, col_type in columns:
                    column_defs.append(f'"{col_name}" {col_type}')
                
                # Create table SQL
                create_sql = f"""
                    CREATE TABLE IF NOT EXISTS raw_data.{table_name} (
                        {', '.join(column_defs)}
                    )
                """
                
                try:
                    cursor.execute(create_sql)
                    self.log(f"Created table: raw_data.{table_name} - {description}")
                except Exception as e:
                    self.log(f"Failed to create table raw_data.{table_name}: {str(e)}", "ERROR")
                    # Continue with other tables
            
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to create dataset tables: {str(e)}", "ERROR")
            return False
    
    def run_setup(self):
        """Run the full client data warehouse setup."""
        print("=" * 60)
        print("CUSTOMERDNA AI - CLIENT 1 DATA WAREHOUSE SETUP")
        print("=" * 60)
        print(f"Database: {DATA_WAREHOUSE_NAME}")
        print(f"Purpose: {CLIENT_DW_CONFIG['description']}")
        print(f"Access: {CLIENT_DW_CONFIG['access']}")
        print("=" * 60)
        
        # Connect to PostgreSQL
        if not self.connect_to_postgres():
            return False
        
        try:
            # Create database
            self.log("\nCreating data warehouse database...")
            if not self.create_database():
                return False
            
            # Connect to data warehouse
            if not self.connect_to_dw():
                return False
            
            # Create schemas
            self.log("\nCreating schemas...")
            if not self.create_schemas():
                return False
            
            # Set permissions
            self.log("\nSetting database permissions...")
            if not self.set_database_permissions():
                return False
            
            # Create example analytical tables
            self.log("\nCreating example analytical tables...")
            if not self.create_analytical_tables():
                self.log("Note: Analytical tables creation failed, but database setup continues", "INFO")
            
            # Create dataset tables
            self.log("\nCreating dataset tables...")
            if not self.create_dataset_tables():
                self.log("Note: Dataset tables creation failed, but database setup continues", "INFO")
            
            self.log("\n" + "=" * 60)
            self.log("DATA WAREHOUSE SETUP COMPLETED SUCCESSFULLY!", "SUCCESS")
            self.log("=" * 60)
            
            # Print summary
            self.log("\nDATABASE CREATED:")
            self.log(f"  • {DATA_WAREHOUSE_NAME}")
            self.log(f"    Description: {CLIENT_DW_CONFIG['description']}")
            self.log(f"    Schemas: {', '.join(CLIENT_DW_CONFIG['schemas'])}")
            self.log(f"    Access: {CLIENT_DW_CONFIG['access']}")
            
            self.log("\nPERMISSIONS SET:")
            self.log(f"  • superadmin: All privileges (read-write)")
            self.log(f"  • PUBLIC: No access")
            
            self.log("\nEXAMPLE TABLES CREATED:")
            self.log(f"  • analytics.customer_segments")
            self.log(f"  • analytics.sales_summary")
            self.log(f"  • analytics.product_performance")
            
            self.log("\nDATASET TABLES CREATED:")
            self.log(f"  • raw_data.processed_marketing_campaign")
            self.log(f"  • raw_data.processed_e_commerce_customer_churn")
            self.log(f"  • raw_data.category_tree_processed")
            self.log(f"  • raw_data.events_processed")
            self.log(f"  • raw_data.item_properties_processed")
            self.log(f"  • raw_data.online_retail_processed")
            
            return True
            
        except Exception as e:
            self.log(f"Setup failed: {str(e)}", "ERROR")
            return False
        
        finally:
            # Close connections
            if self.dw_conn:
                self.dw_conn.close()
            if self.postgres_conn:
                self.postgres_conn.close()
            self.log("Closed database connections")

def main():
    """Main function."""
    setup = ClientDWSetup(verbose=True)
    success = setup.run_setup()
    
    if success:
        print("\n[SUCCESS] Client data warehouse setup completed successfully!")
        print("\nNOTE: This database is for analytical work.")
        print("      You can add tables, create joins, and perform transformations here.")
        return 0
    else:
        print("\n[ERROR] Client data warehouse setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())