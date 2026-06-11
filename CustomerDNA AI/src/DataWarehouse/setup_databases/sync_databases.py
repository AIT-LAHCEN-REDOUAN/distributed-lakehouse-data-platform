"""
CustomerDNA AI - Database Synchronization
Synchronizes data from base database to data warehouse
"""

import sys
import psycopg2
from psycopg2 import sql
from datetime import datetime
from config import (
    BASE_DATABASE_NAME, DATA_WAREHOUSE_NAME,
    get_connection_params, USER_CONFIG
)

class DatabaseSynchronizer:
    """Synchronizes data from base database to data warehouse."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.base_connection = None
        self.dw_connection = None
        self.sync_report = {
            'tables_synced': [],
            'errors': [],
            'total_tables': 0,
            'total_records': 0
        }
    
    def log(self, message, level="INFO"):
        """Log message with simple formatting."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            if level == "ERROR":
                print(f"[ERROR] [{timestamp}] {message}")
            elif level == "SUCCESS":
                print(f"[SUCCESS] [{timestamp}] {message}")
            else:
                print(f"[INFO] [{timestamp}] {message}")
    
    def connect_to_databases(self):
        """Connect to both databases."""
        try:
            # Connect to base database as superadmin
            base_params = get_connection_params(BASE_DATABASE_NAME)
            base_params['user'] = 'superadmin'
            base_params['password'] = USER_CONFIG['superadmin']['password']
            self.base_connection = psycopg2.connect(**base_params)
            self.base_connection.autocommit = True
            self.log(f"Connected to base database as superadmin")
            
            # Connect to data warehouse as superadmin
            dw_params = get_connection_params(DATA_WAREHOUSE_NAME)
            dw_params['user'] = 'superadmin'
            dw_params['password'] = USER_CONFIG['superadmin']['password']
            self.dw_connection = psycopg2.connect(**dw_params)
            self.dw_connection.autocommit = True
            self.log(f"Connected to data warehouse as superadmin")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to connect to databases: {str(e)}", "ERROR")
            return False
    
    def disconnect_from_databases(self):
        """Disconnect from both databases."""
        if self.base_connection:
            self.base_connection.close()
        if self.dw_connection:
            self.dw_connection.close()
        self.log("Disconnected from databases")
    
    def get_tables_from_base_db(self):
        """Get list of tables from base database raw_data schema."""
        try:
            cursor = self.base_connection.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'raw_data' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            self.log(f"Found {len(tables)} tables in base database raw_data schema")
            return tables
            
        except Exception as e:
            self.log(f"Failed to get tables from base database: {str(e)}", "ERROR")
            return []
    
    def get_table_structure(self, connection, schema_name, table_name):
        """Get column names and data types for a table."""
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema_name, table_name))
            
            columns = cursor.fetchall()
            cursor.close()
            
            return columns
            
        except Exception as e:
            self.log(f"Failed to get structure for {schema_name}.{table_name}: {str(e)}", "ERROR")
            return []
    
    def sync_table(self, table_name):
        """Synchronize a single table from base DB to data warehouse."""
        self.log(f"Synchronizing table: {table_name}")
        
        try:
            # Get table structure from base database
            base_columns = self.get_table_structure(self.base_connection, 'raw_data', table_name)
            if not base_columns:
                self.log(f"No columns found for table {table_name}", "ERROR")
                return False
            
            # Create table in data warehouse if it doesn't exist
            cursor = self.dw_connection.cursor()
            
            # Check if table exists in data warehouse
            cursor.execute("""
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'raw_data' AND table_name = %s
            """, (table_name,))
            
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create table with same structure
                column_defs = []
                for col_name, data_type in base_columns:
                    column_defs.append(f'"{col_name}" {data_type}')
                
                create_sql = f'CREATE TABLE raw_data.{table_name} ({", ".join(column_defs)})'
                cursor.execute(create_sql)
                self.log(f"Created table raw_data.{table_name} in data warehouse")
            else:
                # Table exists, truncate it first
                truncate_sql = f'TRUNCATE TABLE raw_data.{table_name}'
                cursor.execute(truncate_sql)
                self.log(f"Truncated existing table raw_data.{table_name}")
            
            # Copy data from base database to data warehouse
            # Get column names for INSERT statement
            column_names = [f'"{col[0]}"' for col in base_columns]
            columns_str = ', '.join(column_names)
            
            # Create placeholders for VALUES
            placeholders = ', '.join(['%s'] * len(column_names))
            
            # Read data from base database
            base_cursor = self.base_connection.cursor()
            base_cursor.execute(f'SELECT {columns_str} FROM raw_data.{table_name}')
            
            # Insert data into data warehouse in batches
            batch_size = 1000
            records_processed = 0
            
            while True:
                batch = base_cursor.fetchmany(batch_size)
                if not batch:
                    break
                
                # Build INSERT statement
                insert_sql = f'INSERT INTO raw_data.{table_name} ({columns_str}) VALUES ({placeholders})'
                
                # Insert batch
                cursor.executemany(insert_sql, batch)
                records_processed += len(batch)
                
                if len(batch) < batch_size:
                    break
            
            base_cursor.close()
            cursor.close()
            
            # Update sync report
            self.sync_report['tables_synced'].append({
                'table': table_name,
                'records': records_processed
            })
            self.sync_report['total_tables'] += 1
            self.sync_report['total_records'] += records_processed
            
            self.log(f"Successfully synchronized {records_processed:,} records for table {table_name}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Failed to sync table {table_name}: {str(e)}", "ERROR")
            self.sync_report['errors'].append(f"{table_name}: {str(e)}")
            return False
    
    def run_synchronization(self):
        """Run full synchronization from base database to data warehouse."""
        self.log("\n" + "=" * 60)
        self.log("DATABASE SYNCHRONIZATION")
        self.log("=" * 60)
        
        if not self.connect_to_databases():
            return False
        
        try:
            # Get list of tables from base database
            tables = self.get_tables_from_base_db()
            if not tables:
                self.log("No tables found in base database", "ERROR")
                return False
            
            self.log(f"Found {len(tables)} tables to synchronize")
            
            # Synchronize each table
            for table_name in tables:
                self.sync_table(table_name)
            
            # Print synchronization report
            self.print_sync_report()
            
            return True
            
        except Exception as e:
            self.log(f"Synchronization failed: {str(e)}", "ERROR")
            return False
        
        finally:
            self.disconnect_from_databases()
    
    def print_sync_report(self):
        """Print a summary of the synchronization process."""
        print("\n" + "=" * 60)
        print("SYNCHRONIZATION REPORT")
        print("=" * 60)
        
        print(f"\nTotal tables synchronized: {self.sync_report['total_tables']}")
        print(f"Total records copied: {self.sync_report['total_records']:,}")
        
        if self.sync_report['tables_synced']:
            print(f"\nTables synchronized:")
            for table_info in self.sync_report['tables_synced']:
                print(f"  • {table_info['table']}: {table_info['records']:,} records")
        
        if self.sync_report['errors']:
            print(f"\nErrors ({len(self.sync_report['errors'])}):")
            for error in self.sync_report['errors']:
                print(f"  • {error}")
        
        print("\n" + "=" * 60)

def main():
    """Main function."""
    print("=" * 60)
    print("CUSTOMERDNA AI - DATABASE SYNCHRONIZATION")
    print("=" * 60)
    
    synchronizer = DatabaseSynchronizer(verbose=True)
    success = synchronizer.run_synchronization()
    
    if success:
        print("\n[SUCCESS] Database synchronization completed successfully!")
        return 0
    else:
        print("\n[ERROR] Database synchronization failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())