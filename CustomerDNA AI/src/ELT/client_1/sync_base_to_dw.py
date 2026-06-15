"""
CustomerDNA AI - Synchronize Base Database to Client Data Warehouse
Synchronizes data from client_1 base database to client_1 data warehouse
"""

import sys
import psycopg2
from psycopg2 import sql
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
from config import (
    BASE_DATABASE_NAME, DATA_WAREHOUSE_NAME,
    BASE_DB_CONFIG, CLIENT_DW_CONFIG,
    get_connection_params
)

class DatabaseSynchronizer:
    """Synchronizes data from base database to client data warehouse."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
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
    
    def connect_to_databases(self):
        """Connect to both databases."""
        try:
            # Connect to base database
            self.base_conn = psycopg2.connect(**get_connection_params(BASE_DATABASE_NAME))
            self.base_conn.autocommit = True
            self.log(f"Connected to base database: {BASE_DATABASE_NAME}")
            
            # Connect to data warehouse
            self.dw_conn = psycopg2.connect(**get_connection_params(DATA_WAREHOUSE_NAME))
            self.dw_conn.autocommit = True
            self.log(f"Connected to data warehouse: {DATA_WAREHOUSE_NAME}")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to connect to databases: {str(e)}", "ERROR")
            return False
    
    def get_base_tables(self):
        """Get list of tables from base database."""
        try:
            cursor = self.base_conn.cursor()
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (BASE_DB_CONFIG['default_schema'],))
            
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            return tables
            
        except Exception as e:
            self.log(f"Failed to get tables from base database: {str(e)}", "ERROR")
            return []
    
    def table_exists_in_dw(self, table_name):
        """Check if a table exists in data warehouse."""
        try:
            cursor = self.dw_conn.cursor()
            
            cursor.execute("""
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = %s
            """, (CLIENT_DW_CONFIG['default_schema'], table_name))
            
            exists = cursor.fetchone() is not None
            cursor.close()
            
            return exists
            
        except Exception as e:
            self.log(f"Failed to check if table exists: {str(e)}", "ERROR")
            return False
    
    def get_table_structure(self, connection, schema, table_name):
        """Get column structure of a table."""
        try:
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns 
                WHERE table_schema = %s 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table_name))
            
            columns = cursor.fetchall()
            cursor.close()
            
            return columns
            
        except Exception as e:
            self.log(f"Failed to get table structure: {str(e)}", "ERROR")
            return []
    
    def create_table_in_dw(self, table_name, columns):
        """Create a table in data warehouse."""
        try:
            cursor = self.dw_conn.cursor()
            
            # Drop table if it exists
            drop_sql = sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                sql.Identifier(CLIENT_DW_CONFIG['default_schema']),
                sql.Identifier(table_name)
            )
            cursor.execute(drop_sql)
            
            # Create column definitions
            column_defs = []
            for col_name, data_type, is_nullable in columns:
                nullable = "" if is_nullable == 'YES' else " NOT NULL"
                column_defs.append(sql.SQL("{} {}{}").format(
                    sql.Identifier(col_name),
                    sql.SQL(data_type),
                    sql.SQL(nullable)
                ))
            
            # Create table
            create_sql = sql.SQL("CREATE TABLE {}.{} ({})").format(
                sql.Identifier(CLIENT_DW_CONFIG['default_schema']),
                sql.Identifier(table_name),
                sql.SQL(", ").join(column_defs)
            )
            
            # Debug: log the SQL being executed
            if self.verbose:
                self.log(f"Creating table with SQL: {create_sql.as_string(self.dw_conn)[:200]}...")
            
            cursor.execute(create_sql)
            
            self.log(f"Created table: {CLIENT_DW_CONFIG['default_schema']}.{table_name}")
            cursor.close()
            
            return True
            
        except Exception as e:
            self.log(f"Failed to create table {table_name}: {str(e)}", "ERROR")
            
            # Additional debug info
            if self.verbose:
                self.log(f"Columns being used: {len(columns)} columns")
                if columns:
                    self.log(f"First few columns: {columns[:3]}")
            
            return False
    
    def copy_table_data(self, table_name):
        """Copy data from base database to data warehouse."""
        try:
            base_cursor = self.base_conn.cursor()
            dw_cursor = self.dw_conn.cursor()
            
            # Get column names
            base_cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = %s 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (BASE_DB_CONFIG['default_schema'], table_name))
            
            columns = [row[0] for row in base_cursor.fetchall()]
            
            if not columns:
                self.log(f"No columns found in table {table_name}", "ERROR")
                return False, 0
            
            # Build column list for SQL
            column_list = sql.SQL(", ").join([sql.Identifier(col) for col in columns])
            
            # Count records in base table
            base_cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                sql.Identifier(BASE_DB_CONFIG['default_schema']),
                sql.Identifier(table_name)
            ))
            base_count = base_cursor.fetchone()[0]
            
            if base_count == 0:
                self.log(f"Table {table_name} is empty in base database")
                return True, 0
            
            # Clear existing data in DW table
            dw_cursor.execute(sql.SQL("TRUNCATE TABLE {}.{}").format(
                sql.Identifier(CLIENT_DW_CONFIG['default_schema']),
                sql.Identifier(table_name)
            ))
            
            # Copy data - fetch from base DB and insert into DW
            self.log(f"Copying {base_count:,} records from {BASE_DB_CONFIG['default_schema']}.{table_name} to {CLIENT_DW_CONFIG['default_schema']}.{table_name}")
            
            # Fetch data from base database
            base_cursor.execute(sql.SQL("SELECT {} FROM {}.{}").format(
                column_list,
                sql.Identifier(BASE_DB_CONFIG['default_schema']),
                sql.Identifier(table_name)
            ))
            
            # Get all data
            data = base_cursor.fetchall()
            
            # Prepare INSERT statement for data warehouse
            placeholders = sql.SQL(", ").join([sql.Placeholder() for _ in columns])
            insert_sql = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
                sql.Identifier(CLIENT_DW_CONFIG['default_schema']),
                sql.Identifier(table_name),
                column_list,
                placeholders
            )
            
            # Insert data in batches to avoid memory issues
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                for row in batch:
                    dw_cursor.execute(insert_sql, row)
                total_inserted += len(batch)
                
                if self.verbose and i % 5000 == 0:
                    self.log(f"  Inserted {total_inserted:,} of {base_count:,} records...")
            
            # Verify count
            dw_cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                sql.Identifier(CLIENT_DW_CONFIG['default_schema']),
                sql.Identifier(table_name)
            ))
            dw_count = dw_cursor.fetchone()[0]
            
            base_cursor.close()
            dw_cursor.close()
            
            if base_count == dw_count:
                self.log(f"Successfully copied {dw_count:,} records", "SUCCESS")
                return True, dw_count
            else:
                self.log(f"Record count mismatch: Base={base_count:,}, DW={dw_count:,}", "ERROR")
                return False, dw_count
            
        except Exception as e:
            self.log(f"Failed to copy data for table {table_name}: {str(e)}", "ERROR")
            return False, 0
    
    def run_synchronization(self):
        """Run the full synchronization process."""
        print("=" * 60)
        print("CUSTOMERDNA AI - SYNCHRONIZE BASE TO DATA WAREHOUSE")
        print("=" * 60)
        print(f"Source: {BASE_DATABASE_NAME}")
        print(f"Target: {DATA_WAREHOUSE_NAME}")
        print("=" * 60)
        
        # Connect to databases
        if not self.connect_to_databases():
            return False
        
        # Get tables from base database
        tables = self.get_base_tables()
        
        if not tables:
            self.log("No tables found in base database", "ERROR")
            return False
        
        self.log(f"Found {len(tables)} table(s) in base database")
        
        # Synchronize each table
        total_tables = len(tables)
        successful_tables = 0
        total_records = 0
        
        for table_name in tables:
            self.log(f"\nProcessing table: {table_name}")
            
            # Get table structure from base database
            columns = self.get_table_structure(
                self.base_conn, 
                BASE_DB_CONFIG['default_schema'], 
                table_name
            )
            
            if not columns:
                self.log(f"Failed to get structure for table {table_name}", "ERROR")
                continue
            
            # Create table in data warehouse
            if not self.create_table_in_dw(table_name, columns):
                self.log(f"Failed to create table {table_name} in data warehouse", "ERROR")
                continue
            
            # Copy data
            success, record_count = self.copy_table_data(table_name)
            
            if success:
                successful_tables += 1
                total_records += record_count
        
        # Print summary
        print("\n" + "=" * 60)
        print("SYNCHRONIZATION SUMMARY")
        print("=" * 60)
        
        self.log(f"Tables processed: {total_tables}")
        self.log(f"Tables successfully synchronized: {successful_tables}")
        self.log(f"Total records synchronized: {total_records:,}")
        
        if successful_tables == total_tables:
            self.log("All tables synchronized successfully!", "SUCCESS")
            return True
        else:
            self.log(f"{total_tables - successful_tables} tables failed to synchronize", "ERROR")
            return False

def main():
    """Main function."""
    synchronizer = DatabaseSynchronizer(verbose=True)
    success = synchronizer.run_synchronization()
    
    if success:
        print("\n[SUCCESS] Database synchronization completed successfully!")
        print("\nNOTE: Data has been copied from base database to data warehouse.")
        print("      You can now perform analytical work in the data warehouse.")
        return 0
    else:
        print("\n[ERROR] Database synchronization failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())