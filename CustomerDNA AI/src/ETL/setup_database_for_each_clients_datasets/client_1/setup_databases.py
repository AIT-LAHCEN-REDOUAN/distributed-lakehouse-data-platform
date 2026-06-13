"""
CustomerDNA AI - Database Setup
Creates both databases with proper schemas and roles
"""

import sys
import psycopg2
from psycopg2 import sql
from config import (
    BASE_DATABASE_NAME, DATA_WAREHOUSE_NAME,
    BASE_DB_CONFIG, DW_CONFIG, USER_CONFIG,
    get_connection_params
)

class DatabaseSetup:
    """Sets up both databases for CustomerDNA AI."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.postgres_conn = None
        self.base_conn = None
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
    
    def create_database(self, db_name, description):
        """Create a new database."""
        try:
            cursor = self.postgres_conn.cursor()
            
            # Check if database already exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cursor.fetchone():
                self.log(f"Database '{db_name}' already exists")
                return True
            
            # Create database
            create_sql = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
            cursor.execute(create_sql)
            self.log(f"Created database: {db_name} - {description}")
            
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to create database '{db_name}': {str(e)}", "ERROR")
            return False
    
    def connect_to_database(self, db_name):
        """Connect to a specific database."""
        try:
            conn = psycopg2.connect(**get_connection_params(db_name))
            conn.autocommit = True
            self.log(f"Connected to database: {db_name}")
            return conn
        except Exception as e:
            self.log(f"Failed to connect to database '{db_name}': {str(e)}", "ERROR")
            return None
    
    def create_schemas(self, connection, schemas):
        """Create schemas in a database."""
        try:
            cursor = connection.cursor()
            
            for schema in schemas:
                create_sql = sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema))
                cursor.execute(create_sql)
                self.log(f"Created schema: {schema}")
            
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to create schemas: {str(e)}", "ERROR")
            return False
    
    def create_roles(self):
        """Create superadmin user."""
        try:
            cursor = self.postgres_conn.cursor()
            
            # Create superadmin user
            cursor.execute("""
                CREATE USER superadmin WITH 
                PASSWORD %s 
                SUPERUSER CREATEDB CREATEROLE LOGIN
            """, (USER_CONFIG['superadmin']['password'],))
            
            self.log("Created superadmin user")
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to create superadmin user: {str(e)}", "ERROR")
            return False
    
    def setup_base_database(self):
        """Set up the base database."""
        self.log("\n" + "=" * 60)
        self.log("SETTING UP BASE DATABASE")
        self.log("=" * 60)
        
        # Create base database
        if not self.create_database(BASE_DATABASE_NAME, BASE_DB_CONFIG['description']):
            return False
        
        # Connect to base database
        self.base_conn = self.connect_to_database(BASE_DATABASE_NAME)
        if not self.base_conn:
            return False
        
        # Create schemas
        if not self.create_schemas(self.base_conn, BASE_DB_CONFIG['schemas']):
            return False
        
        self.log("Base database setup completed", "SUCCESS")
        return True
    
    def setup_data_warehouse(self):
        """Set up the data warehouse."""
        self.log("\n" + "=" * 60)
        self.log("SETTING UP DATA WAREHOUSE")
        self.log("=" * 60)
        
        # Create data warehouse database
        if not self.create_database(DATA_WAREHOUSE_NAME, DW_CONFIG['description']):
            return False
        
        # Connect to data warehouse
        self.dw_conn = self.connect_to_database(DATA_WAREHOUSE_NAME)
        if not self.dw_conn:
            return False
        
        # Create schemas
        if not self.create_schemas(self.dw_conn, DW_CONFIG['schemas']):
            return False
        
        self.log("Data warehouse setup completed", "SUCCESS")
        return True
    
    def run_full_setup(self):
        """Run full database setup."""
        print("=" * 60)
        print("CUSTOMERDNA AI - DATABASE SETUP")
        print("=" * 60)
        
        # Connect to PostgreSQL
        if not self.connect_to_postgres():
            return False
        
        try:
            # Create roles
            self.log("\nCreating database roles...")
            if not self.create_roles():
                return False
            
            # Setup base database
            if not self.setup_base_database():
                return False
            
            # Setup data warehouse
            if not self.setup_data_warehouse():
                return False
            
            self.log("\n" + "=" * 60)
            self.log("DATABASE SETUP COMPLETED SUCCESSFULLY!", "SUCCESS")
            self.log("=" * 60)
            
            # Print summary
            self.log("\nDATABASES CREATED:")
            self.log(f"  1. {BASE_DATABASE_NAME} - {BASE_DB_CONFIG['description']}")
            self.log(f"  2. {DATA_WAREHOUSE_NAME} - {DW_CONFIG['description']}")
            
            self.log("\nUSER CREATED:")
            self.log(f"  • superadmin - {USER_CONFIG['superadmin']['description']}")
            
            return True
            
        except Exception as e:
            self.log(f"Setup failed: {str(e)}", "ERROR")
            return False
        
        finally:
            # Close connections
            if self.base_conn:
                self.base_conn.close()
            if self.dw_conn:
                self.dw_conn.close()
            if self.postgres_conn:
                self.postgres_conn.close()
            self.log("Closed database connections")

def main():
    """Main function."""
    setup = DatabaseSetup(verbose=True)
    success = setup.run_full_setup()
    
    if success:
        print("\n[SUCCESS] Database setup completed successfully!")
        return 0
    else:
        print("\n[ERROR] Database setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())