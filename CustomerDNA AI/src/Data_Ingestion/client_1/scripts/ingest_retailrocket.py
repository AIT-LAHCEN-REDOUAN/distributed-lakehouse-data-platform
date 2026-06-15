"""
CustomerDNA AI - Data Ingestion Script (Simplified)
Dataset: RetailRocket Recommender System Dataset
Purpose: Process raw data and save SQL-compatible CSV WITHOUT database loading
Handles 4 files: category_tree.csv, events.csv, item_properties_part1.csv, item_properties_part2.csv
"""

import pandas as pd
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import (
    get_dataset_config, 
    get_dataset_path
)

class RetailRocketIngestorSimple:
    """Simplified data ingestion class for RetailRocket dataset - only processes and saves CSV."""
    
    def __init__(self):
        # We'll process 4 datasets
        self.datasets = [
            'retailrocket_category_tree',
            'retailrocket_events', 
            'retailrocket_item_properties'
        ]
        
        # Set up root ingested data folder
        root_dir = os.path.dirname(os.path.dirname(__file__))
        self.ingested_data_root = os.path.join(root_dir, 'ingested_data')
        os.makedirs(self.ingested_data_root, exist_ok=True)
        
        # Set up RetailRocket dataset folder
        self.ingested_data_dir = os.path.join(self.ingested_data_root, 'Retailrocket_recommender_system_dataset')
        os.makedirs(self.ingested_data_dir, exist_ok=True)
        
        # Set up logs folder (at root level)
        self.logs_dir = os.path.join(root_dir, 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        print(f"Initialized simplified ingestor for RetailRocket Recommender System Dataset")
        print(f"Dataset folder: {self.ingested_data_dir}")
        print(f"Logs folder: {self.logs_dir}")
        print(f"Will process: {len(self.datasets)} dataset configurations")
    
    def load_and_prepare_category_tree(self):
        """Load and prepare category_tree.csv."""
        dataset_name = 'retailrocket_category_tree'
        config = get_dataset_config(dataset_name)
        data_path = get_dataset_path(dataset_name)
        
        print(f"\n1. Processing category_tree.csv")
        print(f"   Config: {config['name']}")
        print(f"   File: {data_path}")
        
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"File not found: {data_path}")
        
        try:
            # Load CSV
            df = pd.read_csv(
                data_path,
                delimiter=config['delimiter'],
                encoding=config['encoding']
            )
            
            print(f"   Raw data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Apply ONLY necessary preprocessing for SQL compatibility:
            processed_df = df.copy()
            
            # 1. Fix encoding issues (critical for SQL)
            for col in processed_df.select_dtypes(include=['object']).columns:
                processed_df[col] = processed_df[col].astype(str).str.encode('utf-8', 'ignore').str.decode('utf-8')
            
            # 2. Convert numeric columns to proper types
            for col in config['numeric_columns']:
                if col in processed_df.columns:
                    processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
            
            # 3. Ensure primary key is unique
            pk_col = config['primary_key']
            if pk_col in processed_df.columns:
                duplicates = processed_df[pk_col].duplicated().sum()
                if duplicates > 0:
                    print(f"   [WARNING] Primary key {pk_col} has {duplicates} duplicates")
                else:
                    print(f"   [OK] Primary key {pk_col} is unique - SQL compatible")
            
            # 4. Check for missing values
            missing_counts = processed_df.isnull().sum()
            for col, count in missing_counts.items():
                if count > 0:
                    print(f"   [WARNING] Column {col} has {count} missing values")
            
            print(f"   Processed data shape: {processed_df.shape}")
            return processed_df
            
        except Exception as e:
            print(f"   [ERROR] Failed to process category_tree.csv: {e}")
            raise
    
    def load_and_prepare_events(self):
        """Load and prepare events.csv."""
        dataset_name = 'retailrocket_events'
        config = get_dataset_config(dataset_name)
        data_path = get_dataset_path(dataset_name)
        
        print(f"\n2. Processing events.csv")
        print(f"   Config: {config['name']}")
        print(f"   File: {data_path}")
        
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"File not found: {data_path}")
        
        try:
            # Load CSV - this file is large (94MB), use appropriate settings
            df = pd.read_csv(
                data_path,
                delimiter=config['delimiter'],
                encoding=config['encoding'],
                low_memory=False
            )
            
            print(f"   Raw data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Apply ONLY necessary preprocessing for SQL compatibility:
            processed_df = df.copy()
            
            # 1. Fix encoding issues (critical for SQL)
            for col in processed_df.select_dtypes(include=['object']).columns:
                processed_df[col] = processed_df[col].astype(str).str.encode('utf-8', 'ignore').str.decode('utf-8')
            
            # 2. Convert numeric columns to proper types
            for col in config['numeric_columns']:
                if col in processed_df.columns:
                    processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
            
            # 3. Handle transactionid - empty for non-transaction events
            if 'transactionid' in processed_df.columns:
                # Convert empty strings to None for SQL NULL
                processed_df['transactionid'] = processed_df['transactionid'].replace('', None)
                print(f"   [OK] Processed transactionid column for SQL compatibility")
            
            # 4. Check event types
            if 'event' in processed_df.columns:
                event_counts = processed_df['event'].value_counts()
                print(f"   Event distribution:")
                for event_type, count in event_counts.items():
                    percentage = count / len(processed_df) * 100
                    print(f"     - {event_type}: {count:,} ({percentage:.1f}%)")
            
            # 5. Check for missing values
            missing_counts = processed_df.isnull().sum()
            for col, count in missing_counts.items():
                if count > 0:
                    print(f"   [WARNING] Column {col} has {count} missing values")
            
            print(f"   Processed data shape: {processed_df.shape}")
            return processed_df
            
        except Exception as e:
            print(f"   [ERROR] Failed to process events.csv: {e}")
            raise
    
    def load_and_prepare_item_properties(self):
        """Load and prepare both item_properties files."""
        dataset_name = 'retailrocket_item_properties'
        config = get_dataset_config(dataset_name)
        data_path_part1 = get_dataset_path(dataset_name)
        
        # Get part2 path by replacing part1 with part2
        data_path_part2 = data_path_part1.replace('item_properties_part1.csv', 'item_properties_part2.csv')
        
        print(f"\n3. Processing item_properties files")
        print(f"   Config: {config['name']}")
        print(f"   File 1: {data_path_part1}")
        print(f"   File 2: {data_path_part2}")
        
        if not os.path.exists(data_path_part1):
            raise FileNotFoundError(f"File not found: {data_path_part1}")
        if not os.path.exists(data_path_part2):
            raise FileNotFoundError(f"File not found: {data_path_part2}")
        
        try:
            # Load both files - these are very large (484MB + 409MB)
            print(f"   Loading part1...")
            df_part1 = pd.read_csv(
                data_path_part1,
                delimiter=config['delimiter'],
                encoding=config['encoding'],
                low_memory=False
            )
            
            print(f"   Loading part2...")
            df_part2 = pd.read_csv(
                data_path_part2,
                delimiter=config['delimiter'],
                encoding=config['encoding'],
                low_memory=False
            )
            
            # Combine both parts
            df = pd.concat([df_part1, df_part2], ignore_index=True)
            print(f"   Combined data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Apply ONLY necessary preprocessing for SQL compatibility:
            processed_df = df.copy()
            
            # 1. Fix encoding issues (critical for SQL)
            for col in processed_df.select_dtypes(include=['object']).columns:
                processed_df[col] = processed_df[col].astype(str).str.encode('utf-8', 'ignore').str.decode('utf-8')
            
            # 2. Convert numeric columns to proper types
            for col in config['numeric_columns']:
                if col in processed_df.columns:
                    processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
            
            # 3. Check property distribution
            if 'property' in processed_df.columns:
                top_properties = processed_df['property'].value_counts().head(10)
                print(f"   Top 10 properties:")
                for prop, count in top_properties.items():
                    percentage = count / len(processed_df) * 100
                    print(f"     - {prop}: {count:,} ({percentage:.1f}%)")
            
            # 4. Check for missing values
            missing_counts = processed_df.isnull().sum()
            for col, count in missing_counts.items():
                if count > 0:
                    print(f"   [WARNING] Column {col} has {count} missing values")
            
            print(f"   Processed data shape: {processed_df.shape}")
            return processed_df
            
        except Exception as e:
            print(f"   [ERROR] Failed to process item_properties files: {e}")
            raise
    
    def save_processed_data(self, df, filename):
        """Save processed DataFrame to CSV in the dataset folder."""
        output_path = os.path.join(self.ingested_data_dir, filename)
        
        try:
            # Save with UTF-8 encoding for SQL compatibility
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"   [OK] Saved processed data to: {output_path}")
            print(f"   File size: {os.path.getsize(output_path):,} bytes")
            return output_path
        except Exception as e:
            print(f"   [ERROR] Failed to save CSV: {e}")
            raise
    
    def run_ingestion(self):
        """Main method to run the complete ingestion process."""
        print("\n" + "="*80)
        print("RETAILROCKET DATASET INGESTION - SIMPLIFIED (NO DATABASE LOADING)")
        print("="*80)
        
        start_time = datetime.now()
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Process category_tree.csv
            df_category = self.load_and_prepare_category_tree()
            self.save_processed_data(df_category, 'category_tree_processed.csv')
            
            # Process events.csv
            df_events = self.load_and_prepare_events()
            self.save_processed_data(df_events, 'events_processed.csv')
            
            # Process item_properties files
            df_properties = self.load_and_prepare_item_properties()
            self.save_processed_data(df_properties, 'item_properties_processed.csv')
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "="*80)
            print("INGESTION COMPLETED SUCCESSFULLY")
            print("="*80)
            print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total duration: {duration}")
            print(f"Output files saved to: {self.ingested_data_dir}")
            print("\nFiles created:")
            print("1. category_tree_processed.csv")
            print("2. events_processed.csv")
            print("3. item_properties_processed.csv")
            print("\nNote: These CSV files are SQL-compatible and ready for loading")
            print("      Database loading will be handled in the ELT folder")
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Ingestion failed: {e}")
            return False

def main():
    """Main entry point."""
    try:
        ingestor = RetailRocketIngestorSimple()
        success = ingestor.run_ingestion()
        
        if success:
            print("\n[SUCCESS] RetailRocket dataset processed successfully!")
            print("Next step: Use ELT scripts to load processed CSV files to database")
        else:
            print("\n[FAILURE] RetailRocket dataset processing failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()