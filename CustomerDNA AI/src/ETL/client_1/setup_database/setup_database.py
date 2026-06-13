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
            cursor.execute(f"REVOKE ALL ON DATABASE {BASE_DATABASE_NAME} FROM PUBLIC")
            
            # Grant connect to superadmin
            cursor.execute(f"GRANT CONNECT ON DATABASE {BASE_DATABASE_NAME} TO superadmin")
            
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