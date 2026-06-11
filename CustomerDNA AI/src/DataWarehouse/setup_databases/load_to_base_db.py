"""
CustomerDNA AI - Load Data to Base Database
Loads CSV files from preprocessed datasets into base database
"""

import os
import sys
import pandas as pd
import psycopg2
import hashlib
from datetime import datetime
from config import BASE_DATABASE_NAME, get_connection_params

class BaseDatabaseLoader:
    """Loads CSV files into the base database."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.connection = None
        self.loading_report = {
            'success': [],
            'errors': [],
            'total_files': 0,
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
            elif level == "WARNING":
                print(f"[WARNING] [{timestamp}] {message}")
            else:
                print(f"[INFO] [{timestamp}] {message}")
    
    def connect(self):
        """Connect to base database."""
        try:
            self.connection = psycopg2.connect(**get_connection_params(BASE_DATABASE_NAME))
            self.connection.autocommit = True
            self.log(f"Connected to base database: {BASE_DATABASE_NAME}")
            return True
        except Exception as e:
            self.log(f"Failed to connect to base database: {str(e)}", "ERROR")
            return False
    
    def disconnect(self):
        """Disconnect from database."""
        if self.connection:
            self.connection.close()
            self.log("Disconnected from database")
    
    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash of a file for change detection."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_table_metadata(self, schema_name, table_name):
        """Get metadata for a table from metadata.table_history."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT file_hash, record_count, last_modified 
                FROM metadata.table_history 
                WHERE schema_name = %s AND table_name = %s
            """, (schema_name, table_name))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return {
                    'file_hash': result[0],
                    'record_count': result[1],
                    'last_modified': result[2]
                }
            return None
            
        except Exception as e:
            self.log(f"Failed to get metadata for {schema_name}.{table_name}: {str(e)}", "ERROR")
            return None
    
    def update_table_metadata(self, schema_name, table_name, file_name, file_hash, record_count):
        """Update metadata for a table in metadata.table_history."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO metadata.table_history 
                (schema_name, table_name, file_name, file_hash, record_count, ingestion_time)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (schema_name, table_name) 
                DO UPDATE SET 
                    file_name = EXCLUDED.file_name,
                    file_hash = EXCLUDED.file_hash,
                    record_count = EXCLUDED.record_count,
                    last_modified = CURRENT_TIMESTAMP,
                    ingestion_time = EXCLUDED.ingestion_time
            """, (schema_name, table_name, file_name, file_hash, record_count, datetime.now()))
            
            cursor.close()
            return True
            
        except Exception as e:
            self.log(f"Failed to update metadata for {schema_name}.{table_name}: {str(e)}", "ERROR")
            return False
    
    def create_metadata_table(self):
        """Create metadata table if it doesn't exist."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata.table_history (
                    id SERIAL PRIMARY KEY,
                    schema_name TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    record_count INTEGER DEFAULT 0,
                    file_name TEXT,
                    file_hash TEXT,
                    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(schema_name, table_name)
                )
            """)
            cursor.close()
            self.log("Metadata table created/verified")
            return True
        except Exception as e:
            self.log(f"Failed to create metadata table: {str(e)}", "ERROR")
            return False
    
    def load_csv_file(self, csv_path, schema_name, table_name, file_name):
        """Load a single CSV file into base database."""
        self.log(f"Processing file: {file_name}")
        
        # Check if CSV file exists
        if not os.path.exists(csv_path):
            self.log(f"CSV file not found: {csv_path}", "ERROR")
            self.loading_report['errors'].append(f"File not found: {csv_path}")
            return False
        
        try:
            # Calculate file hash for metadata tracking
            file_hash = self.calculate_file_hash(csv_path)
            
            # Read CSV file with better error handling
            self.log(f"Reading CSV file: {file_name}")
            try:
                # Try reading with low_memory=False to avoid mixed type warnings
                df = pd.read_csv(csv_path, low_memory=False)
            except Exception as e:
                self.log(f"Failed to read CSV with low_memory=False: {str(e)}", "WARNING")
                # Fall back to regular read
                df = pd.read_csv(csv_path)
            
            # Try to convert object columns to numeric where possible
            for col in df.select_dtypes(include=['object']).columns:
                try:
                    # Try to convert to numeric
                    converted = pd.to_numeric(df[col], errors='coerce')
                    # If at least 80% of values converted successfully, use the converted column
                    if converted.notna().sum() / len(df) > 0.8:
                        df[col] = converted
                        self.log(f"Converted column '{col}' from object to numeric", "INFO")
                except Exception:
                    # If conversion fails, keep as object
                    pass
            
            record_count = len(df)
            
            # Always drop and recreate table to ensure clean data
            cursor = self.connection.cursor()
            
            # Drop table if exists
            drop_sql = f'DROP TABLE IF EXISTS {schema_name}.{table_name}'
            cursor.execute(drop_sql)
            self.log(f"Dropped existing table {schema_name}.{table_name}")
            
            # Create table with appropriate data types
            # Convert pandas dtypes to PostgreSQL types
            column_defs = []
            for col_name, dtype in df.dtypes.items():
                if dtype == 'int64':
                    # Check if values might exceed INTEGER range
                    if df[col_name].abs().max() > 2147483647:
                        pg_type = 'BIGINT'
                    else:
                        pg_type = 'INTEGER'
                elif dtype == 'float64':
                    pg_type = 'DOUBLE PRECISION'
                elif dtype == 'bool':
                    pg_type = 'BOOLEAN'
                elif 'datetime' in str(dtype):
                    pg_type = 'TIMESTAMP'
                else:
                    pg_type = 'TEXT'
                
                column_defs.append(f'"{col_name}" {pg_type}')
            
            create_sql = f'CREATE TABLE {schema_name}.{table_name} ({", ".join(column_defs)})'
            cursor.execute(create_sql)
            self.log(f"Created table {schema_name}.{table_name}")
            
            # Insert data
            self.log(f"Inserting {record_count:,} records into {schema_name}.{table_name}")
            
            # Convert DataFrame to list of tuples
            records = [tuple(x) for x in df.to_numpy()]
            columns = ', '.join([f'"{col}"' for col in df.columns])
            
            # Create INSERT statement
            placeholders = ', '.join(['%s'] * len(df.columns))
            insert_sql = f'INSERT INTO {schema_name}.{table_name} ({columns}) VALUES ({placeholders})'
            
            # Insert in batches for efficiency
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany(insert_sql, batch)
            
            # Update metadata
            self.update_table_metadata(schema_name, table_name, file_name, file_hash, record_count)
            
            cursor.close()
            
            # Update loading report
            self.loading_report['success'].append({
                'file': file_name,
                'table': f"{schema_name}.{table_name}",
                'records': record_count
            })
            self.loading_report['total_files'] += 1
            self.loading_report['total_records'] += record_count
            
            self.log(f"Successfully loaded {record_count:,} records into {schema_name}.{table_name}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Failed to load file {file_name}: {str(e)}", "ERROR")
            self.loading_report['errors'].append(f"{file_name}: {str(e)}")
            return False
    
    def load_preprocessed_data(self, data_directory):
        """
        Load all preprocessed CSV files from the data directory.
        Expected directory structure:
        data_directory/
          ├── Dataset1/
          │   └── cleaned_dataset/
          │       └── cleaned_data.csv
          ├── Dataset2/
          │   └── cleaned_dataset/
          │       └── cleaned_data.csv
          └── ...
        """
        self.log("\n" + "=" * 60)
        self.log("LOADING PREPROCESSED DATA TO BASE DATABASE")
        self.log("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            # Create metadata table
            if not self.create_metadata_table():
                return False
            
            # Find all cleaned CSV files
            csv_files = []
            for root, dirs, files in os.walk(data_directory):
                for file in files:
                    if file.endswith('.csv') and 'cleaned' in file.lower():
                        csv_files.append(os.path.join(root, file))
            
            if not csv_files:
                self.log(f"No CSV files found in {data_directory}", "ERROR")
                return False
            
            self.log(f"Found {len(csv_files)} CSV files to load")
            
            # Load each CSV file
            for csv_path in csv_files:
                # Extract dataset name from path
                rel_path = os.path.relpath(csv_path, data_directory)
                path_parts = rel_path.split(os.sep)
                
                # Use the dataset folder name as table name
                dataset_name = path_parts[0] if len(path_parts) > 0 else "unknown"
                table_name = dataset_name.lower().replace(' ', '_').replace('-', '_')
                file_name = os.path.basename(csv_path)
                
                # Load the CSV file
                self.load_csv_file(csv_path, 'raw_data', table_name, file_name)
            
            # Print loading report
            self.print_loading_report()
            
            return True
            
        except Exception as e:
            self.log(f"Loading failed: {str(e)}", "ERROR")
            return False
        
        finally:
            self.disconnect()
    
    def print_loading_report(self):
        """Print a summary of the loading process."""
        print("\n" + "=" * 60)
        print("LOADING REPORT")
        print("=" * 60)
        
        print(f"\nTotal files processed: {self.loading_report['total_files']}")
        print(f"Total records loaded: {self.loading_report['total_records']:,}")
        
        if self.loading_report['success']:
            print(f"\nSuccessfully loaded {len(self.loading_report['success'])} files:")
            for success in self.loading_report['success']:
                print(f"  • {success['file']} → {success['table']} ({success['records']:,} records)")
        
        if self.loading_report['errors']:
            print(f"\nErrors ({len(self.loading_report['errors'])}):")
            for error in self.loading_report['errors']:
                print(f"  • {error}")
        
        print("\n" + "=" * 60)

def main():
    """Main function."""
    print("=" * 60)
    print("CUSTOMERDNA AI - LOAD DATA TO BASE DATABASE")
    print("=" * 60)
    
    # Update this path to point to your preprocessed data directory
    # Example: "d:\\github\\Master_PFE_Project\\CustomerDNA AI\\Preprocessing"
    data_directory = input("\nEnter the path to your preprocessed data directory: ").strip()
    
    if not os.path.exists(data_directory):
        print(f"\n[ERROR] Directory not found: {data_directory}")
        print("Please make sure the path is correct.")
        return 1
    
    loader = BaseDatabaseLoader(verbose=True)
    success = loader.load_preprocessed_data(data_directory)
    
    if success:
        print("\n[SUCCESS] Data loading completed successfully!")
        return 0
    else:
        print("\n[ERROR] Data loading failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())