"""
CustomerDNA AI - Load Data to Client 1 Base Database
Loads preprocessed CSV files into the client_1 base database (static storage)
"""

import sys
import os
import pandas as pd
import psycopg2
from psycopg2 import sql, errors
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
from config import (
    BASE_DATABASE_NAME, BASE_DB_CONFIG,
    get_connection_params
)

class DataLoader:
    """Loads preprocessed data into the client_1 base database."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.connection = None
    
    def log(self, message, level="INFO"):
        """Log message with simple formatting."""
        if self.verbose:
            if level == "ERROR":
                print(f"[ERROR] {message}")
            elif level == "SUCCESS":
                print(f"[SUCCESS] {message}")
            else:
                print(f"[INFO] {message}")
    
    def connect_to_base_db(self):
        """Connect to the base database."""
        try:
            self.connection = psycopg2.connect(**get_connection_params(BASE_DATABASE_NAME))
            self.connection.autocommit = True
            self.log(f"Connected to base database: {BASE_DATABASE_NAME}")
            return True
        except Exception as e:
            self.log(f"Failed to connect to base database: {str(e)}", "ERROR")
            return False
    
    def create_metadata_table(self):
        """Create metadata table to track loaded files."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata.loaded_files (
                    id SERIAL PRIMARY KEY,
                    file_name VARCHAR(255) NOT NULL,
                    table_name VARCHAR(255) NOT NULL,
                    record_count INTEGER NOT NULL,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(file_name, table_name)
                )
            """)
            
            self.log("Metadata table created/verified")
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to create metadata table: {str(e)}", "ERROR")
            return False
    
    def get_csv_files(self, data_dir):
        """Get all CSV files from a directory."""
        csv_files = []
        
        if not os.path.exists(data_dir):
            self.log(f"Data directory does not exist: {data_dir}", "ERROR")
            return csv_files
        
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(root, file))
        
        return csv_files
    
    def generate_table_name(self, csv_file):
        """Generate a table name from CSV file name."""
        # Extract base name without extension
        base_name = os.path.basename(csv_file).replace('.csv', '')
        
        # Clean the name for PostgreSQL
        # Remove special characters and replace spaces with underscores
        table_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in base_name)
        
        # Ensure it starts with a letter
        if table_name[0].isdigit():
            table_name = 'table_' + table_name
        
        # Convert to lowercase
        table_name = table_name.lower()
        
        return table_name
    
    def load_csv_to_table(self, csv_path, table_name):
        """Load a CSV file into a PostgreSQL table."""
        try:
            self.log(f"Reading CSV file: {os.path.basename(csv_path)}")
            
            # Read CSV file with better error handling
            try:
                # First try reading with default settings
                df = pd.read_csv(csv_path)
            except Exception as e:
                self.log(f"Warning: Standard read failed for {os.path.basename(csv_path)}: {str(e)}", "INFO")
                # Try with low_memory=False to handle mixed types
                df = pd.read_csv(csv_path, low_memory=False)
                self.log(f"Successfully read with low_memory=False", "INFO")
            
            # Get column names and types
            columns = []
            for col in df.columns:
                # Map pandas dtypes to PostgreSQL types
                dtype = str(df[col].dtype)
                
                # Check if this might be RetailRocket data with large integers
                # RetailRocket often has large timestamps or IDs that need BIGINT
                if 'int' in dtype:
                    # For RetailRocket files, use BIGINT to handle large numbers
                    if 'retailrocket' in csv_path.lower():
                        pg_type = 'BIGINT'
                    else:
                        # For other files, check if values might be large
                        try:
                            max_val = df[col].max()
                            min_val = df[col].min()
                            # If values exceed 2 billion, use BIGINT
                            if abs(max_val) > 2000000000 or abs(min_val) > 2000000000:
                                pg_type = 'BIGINT'
                            else:
                                pg_type = 'INTEGER'
                        except:
                            pg_type = 'INTEGER'
                elif 'float' in dtype:
                    pg_type = 'DOUBLE PRECISION'
                elif 'bool' in dtype:
                    pg_type = 'BOOLEAN'
                elif 'datetime' in dtype:
                    pg_type = 'TIMESTAMP'
                else:
                    pg_type = 'TEXT'
                
                # Clean column name
                clean_col = ''.join(c if c.isalnum() or c == '_' else '_' for c in col)
                if clean_col[0].isdigit():
                    clean_col = 'col_' + clean_col
                clean_col = clean_col.lower()
                
                columns.append((clean_col, pg_type))
            
            cursor = self.connection.cursor()
            
            # Drop table if it exists (for fresh reload)
            drop_sql = sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                sql.Identifier(BASE_DB_CONFIG['default_schema']),
                sql.Identifier(table_name)
            )
            cursor.execute(drop_sql)
            
            # Create table
            column_defs = []
            for col_name, col_type in columns:
                column_defs.append(sql.SQL("{} {}").format(
                    sql.Identifier(col_name),
                    sql.SQL(col_type)
                ))
            
            create_sql = sql.SQL("CREATE TABLE {}.{} ({})").format(
                sql.Identifier(BASE_DB_CONFIG['default_schema']),
                sql.Identifier(table_name),
                sql.SQL(", ").join(column_defs)
            )
            cursor.execute(create_sql)
            
            # Insert data
            self.log(f"Inserting {len(df):,} records into {BASE_DB_CONFIG['default_schema']}.{table_name}")
            
            # Convert DataFrame to list of tuples for batch insert
            records = [tuple(row) for row in df.values]
            
            # Create insert statement
            insert_sql = sql.SQL("INSERT INTO {}.{} VALUES ({})").format(
                sql.Identifier(BASE_DB_CONFIG['default_schema']),
                sql.Identifier(table_name),
                sql.SQL(", ").join([sql.Placeholder()] * len(df.columns))
            )
            
            # Batch insert
            cursor.executemany(insert_sql, records)
            
            # Record in metadata
            cursor.execute("""
                INSERT INTO metadata.loaded_files 
                (file_name, table_name, record_count) 
                VALUES (%s, %s, %s)
                ON CONFLICT (file_name, table_name) 
                DO UPDATE SET 
                    record_count = EXCLUDED.record_count,
                    loaded_at = CURRENT_TIMESTAMP
            """, (os.path.basename(csv_path), table_name, len(df)))
            
            cursor.close()
            
            self.log(f"Successfully loaded {len(df):,} records into {BASE_DB_CONFIG['default_schema']}.{table_name}", "SUCCESS")
            return True, len(df)
            
        except errors.NumericValueOutOfRange as e:
            self.log(f"Failed to load file {os.path.basename(csv_path)}: integer out of range", "ERROR")
            self.log(f"  Solution: The CSV contains numbers too large for INTEGER type.", "INFO")
            self.log(f"  Try converting the file or using BIGINT data type.", "INFO")
            return False, 0
        except Exception as e:
            self.log(f"Failed to load file {os.path.basename(csv_path)}: {str(e)}", "ERROR")
            return False, 0
    
    def run_loading(self, data_dir):
        """Run the full data loading process."""
        print("=" * 60)
        print("CUSTOMERDNA AI - LOAD DATA TO CLIENT 1 BASE DATABASE")
        print("=" * 60)
        print(f"Database: {BASE_DATABASE_NAME}")
        print(f"Purpose: {BASE_DB_CONFIG['description']}")
        print(f"Access: {BASE_DB_CONFIG['access']}")
        print("=" * 60)
        
        # Connect to database
        if not self.connect_to_base_db():
            return False
        
        # Create metadata table
        if not self.create_metadata_table():
            return False
        
        # Get CSV files
        csv_files = self.get_csv_files(data_dir)
        
        if not csv_files:
            self.log("No CSV files found in the specified directory", "ERROR")
            return False
        
        self.log(f"Found {len(csv_files)} CSV files to load")
        
        # Load each CSV file
        total_records = 0
        successful_files = 0
        
        for csv_file in csv_files:
            table_name = self.generate_table_name(csv_file)
            
            success, record_count = self.load_csv_to_table(csv_file, table_name)
            
            if success:
                total_records += record_count
                successful_files += 1
        
        # Print summary
        print("\n" + "=" * 60)
        print("LOADING SUMMARY")
        print("=" * 60)
        
        self.log(f"Files processed: {len(csv_files)}")
        self.log(f"Files successfully loaded: {successful_files}")
        self.log(f"Total records loaded: {total_records:,}")
        
        if successful_files == len(csv_files):
            self.log("All files loaded successfully!", "SUCCESS")
            return True
        else:
            self.log(f"{len(csv_files) - successful_files} files failed to load", "ERROR")
            return False

def main():
    """Main function."""
    print("=" * 60)
    print("CUSTOMERDNA AI - LOAD DATA TO CLIENT 1 BASE DATABASE")
    print("=" * 60)
    
    # Get data directory from user
    data_dir = input("\nEnter the path to your preprocessed data directory: ").strip()
    
    if not data_dir:
        print("[ERROR] No directory specified!")
        return 1
    
    # Run loading
    loader = DataLoader(verbose=True)
    success = loader.run_loading(data_dir)
    
    if success:
        print("\n[SUCCESS] Data loading completed successfully!")
        print("\nIMPORTANT: Data is now in the base database (static storage).")
        print("           To use this data for analytics, run sync_base_to_dw.py")
        return 0
    else:
        print("\n[ERROR] Data loading failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())