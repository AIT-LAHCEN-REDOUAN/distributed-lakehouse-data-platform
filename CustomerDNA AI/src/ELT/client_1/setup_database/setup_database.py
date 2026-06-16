"""
CustomerDNA AI - Client 1 Base Database Setup
Creates the base database for client_1 (static storage)
This database stores raw data and should not be modified
"""

import sys
import psycopg2
from psycopg2 import sql
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from config import (
    BASE_DATABASE_NAME, BASE_DB_CONFIG,
    POSTGRES_CONFIG, get_connection_params
)

class BaseDatabaseSetup:
    """Sets up the base database for client_1 (static storage)."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.postgres_conn = None
        self.base_conn = None
    
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
        """Create the base database."""
        try:
            cursor = self.postgres_conn.cursor()
            
            # Check if database already exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (BASE_DATABASE_NAME,))
            if cursor.fetchone():
                self.log(f"Database '{BASE_DATABASE_NAME}' already exists")
                return True
            
            # Create database
            create_sql = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(BASE_DATABASE_NAME))
            cursor.execute(create_sql)
            self.log(f"Created database: {BASE_DATABASE_NAME} - {BASE_DB_CONFIG['description']}")
            
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to create database '{BASE_DATABASE_NAME}': {str(e)}", "ERROR")
            return False
    
    def connect_to_base_db(self):
        """Connect to the base database."""
        try:
            self.base_conn = psycopg2.connect(**get_connection_params(BASE_DATABASE_NAME))
            self.base_conn.autocommit = True
            self.log(f"Connected to database: {BASE_DATABASE_NAME}")
            return True
        except Exception as e:
            self.log(f"Failed to connect to database '{BASE_DATABASE_NAME}': {str(e)}", "ERROR")
            return False
    
    def create_schemas(self):
        """Create schemas in the base database."""
        try:
            cursor = self.base_conn.cursor()
            
            for schema in BASE_DB_CONFIG['schemas']:
                create_sql = sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema))
                cursor.execute(create_sql)
                self.log(f"Created schema: {schema}")
            
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to create schemas: {str(e)}", "ERROR")
            return False
    
    def set_database_permissions(self):
        """Set read-only permissions on the base database."""
        try:
            cursor = self.postgres_conn.cursor()
            
            # Revoke all privileges from public
            revoke_sql = sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(
                sql.Identifier(BASE_DATABASE_NAME)
            )
            cursor.execute(revoke_sql)
            
            # Grant connect to superadmin
            grant_sql = sql.SQL("GRANT CONNECT ON DATABASE {} TO superadmin").format(
                sql.Identifier(BASE_DATABASE_NAME)
            )
            cursor.execute(grant_sql)
            
            # Connect to base database to set schema permissions
            base_cursor = self.base_conn.cursor()
            
            # Set schema permissions
            for schema in BASE_DB_CONFIG['schemas']:
                # Grant usage on schema
                base_cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO superadmin").format(
                    sql.Identifier(schema)
                ))
                
                # Grant select on all tables in schema (future tables included)
                base_cursor.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO superadmin").format(
                    sql.Identifier(schema)
                ))
                
                # Set default privileges for future tables
                base_cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT SELECT ON TABLES TO superadmin").format(
                    sql.Identifier(schema)
                ))
            
            base_cursor.close()
            cursor.close()
            
            self.log(f"Set read-only permissions on {BASE_DATABASE_NAME}")
            return True
            
        except Exception as e:
            self.log(f"Failed to set permissions: {str(e)}", "ERROR")
            return False
    
    def create_dataset_tables(self):
        """Create empty tables for all datasets in the raw_data schema."""
        try:
            cursor = self.base_conn.cursor()
            
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
                        ('invoice', 'TEXT'),
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
        """Run the full base database setup."""
        print("=" * 60)
        print("CUSTOMERDNA AI - CLIENT 1 BASE DATABASE SETUP")
        print("=" * 60)
        print(f"Database: {BASE_DATABASE_NAME}")
        print(f"Purpose: {BASE_DB_CONFIG['description']}")
        print(f"Access: {BASE_DB_CONFIG['access']}")
        print("=" * 60)
        
        # Connect to PostgreSQL
        if not self.connect_to_postgres():
            return False
        
        try:
            # Create database
            self.log("\nCreating base database...")
            if not self.create_database():
                return False
            
            # Connect to base database
            if not self.connect_to_base_db():
                return False
            
            # Create schemas
            self.log("\nCreating schemas...")
            if not self.create_schemas():
                return False
            
            # Set permissions
            self.log("\nSetting database permissions...")
            if not self.set_database_permissions():
                return False
            
            # Create dataset tables
            self.log("\nCreating dataset tables...")
            if not self.create_dataset_tables():
                self.log("Note: Dataset tables creation failed, but database setup continues", "INFO")
            
            self.log("\n" + "=" * 60)
            self.log("BASE DATABASE SETUP COMPLETED SUCCESSFULLY!", "SUCCESS")
            self.log("=" * 60)
            
            # Print summary
            self.log("\nDATABASE CREATED:")
            self.log(f"  • {BASE_DATABASE_NAME}")
            self.log(f"    Description: {BASE_DB_CONFIG['description']}")
            self.log(f"    Schemas: {', '.join(BASE_DB_CONFIG['schemas'])}")
            self.log(f"    Access: {BASE_DB_CONFIG['access']}")
            
            self.log("\nPERMISSIONS SET:")
            self.log(f"  • superadmin: Connect, Select (read-only)")
            self.log(f"  • PUBLIC: No access")
            
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
            if self.base_conn:
                self.base_conn.close()
            if self.postgres_conn:
                self.postgres_conn.close()
            self.log("Closed database connections")

def main():
    """Main function."""
    setup = BaseDatabaseSetup(verbose=True)
    success = setup.run_setup()
    
    if success:
        print("\n[SUCCESS] Base database setup completed successfully!")
        print("\nIMPORTANT: This database is for static storage only.")
        print("           Data should not be modified here.")
        return 0
    else:
        print("\n[ERROR] Base database setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())