"""
CustomerDNA AI - Data Ingestion Script (Simplified)
Dataset: E-commerce Customer Churn
Purpose: Process raw data and save SQL-compatible CSV WITHOUT database loading
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

class EcommerceChurnIngestorSimple:
    """Simplified data ingestion class - only processes and saves CSV."""
    
    def __init__(self, dataset_name='ecommerce_customer_churn'):
        self.dataset_name = dataset_name
        self.config = get_dataset_config(dataset_name)
        self.data_path = get_dataset_path(dataset_name)
        
        # Set up root ingested data folder
        root_dir = os.path.dirname(os.path.dirname(__file__))
        self.ingested_data_root = os.path.join(root_dir, 'ingested_data')
        os.makedirs(self.ingested_data_root, exist_ok=True)
        
        # Set up dataset-specific folder
        dataset_folder_name = self.config['name'].replace(' ', '_')
        self.ingested_data_dir = os.path.join(self.ingested_data_root, dataset_folder_name)
        os.makedirs(self.ingested_data_dir, exist_ok=True)
        
        # Set up logs folder (at root level)
        self.logs_dir = os.path.join(root_dir, 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        if not self.config:
            raise ValueError(f"Configuration not found for dataset: {dataset_name}")
        
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Dataset file not found: {self.data_path}")
        
        print(f"Initialized simplified ingestor for {self.config['name']}")
        print(f"Data file: {self.data_path}")
        print(f"Dataset-specific folder: {self.ingested_data_dir}")
        print(f"Logs folder: {self.logs_dir}")
    
    def load_and_prepare_data(self):
        """Load data and apply ONLY necessary preprocessing for SQL compatibility."""
        print(f"\nLoading data from {self.data_path}")
        
        try:
            # Load Excel file with specified sheet
            df = pd.read_excel(
                self.data_path,
                sheet_name=self.config.get('sheet_name', 0),
                engine='openpyxl'
            )
            
            print(f"Raw data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Apply ONLY necessary preprocessing for SQL compatibility:
            processed_df = df.copy()
            
            # 1. Fix encoding issues (critical for SQL)
            for col in processed_df.select_dtypes(include=['object']).columns:
                processed_df[col] = processed_df[col].astype(str).str.encode('utf-8', 'ignore').str.decode('utf-8')
            
            # 2. Convert date columns to datetime (if any)
            for date_col in self.config.get('date_columns', []):
                if date_col in processed_df.columns:
                    processed_df[date_col] = pd.to_datetime(
                        processed_df[date_col], 
                        errors='coerce'
                    )
                    print(f"Converted {date_col} to datetime for SQL compatibility")
            
            # 3. Ensure primary key is unique (critical for SQL)
            if 'primary_key' in self.config:
                pk_col = self.config['primary_key']
                if pk_col in processed_df.columns:
                    duplicates = processed_df[pk_col].duplicated().sum()
                    if duplicates > 0:
                        raise ValueError(f"Primary key {pk_col} has {duplicates} duplicates - cannot create SQL-compatible CSV")
                    else:
                        print(f"Primary key {pk_col} is unique - SQL compatible")
            
            # 4. Convert numeric columns to proper types (for SQL numeric types)
            for col, expected_type in self.config['columns'].items():
                if col in processed_df.columns:
                    if expected_type in ['int64', 'float64']:
                        processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
            
            # Save processed CSV to dataset-specific folder
            processed_csv_path = os.path.join(
                self.ingested_data_dir, 
                f"processed_{os.path.splitext(os.path.basename(self.data_path))[0]}.csv"
            )
            processed_df.to_csv(processed_csv_path, index=False, encoding='utf-8')
            print(f"Processed data saved to: {processed_csv_path}")
            
            print(f"Data prepared for SQL loading. Shape: {processed_df.shape}")
            return processed_df
            
        except Exception as e:
            print(f"ERROR: Failed to load/prepare data: {str(e)}")
            raise
    
    def run_ingestion(self):
        """Main method to run the simplified data ingestion process."""
        print("=" * 80)
        print("CUSTOMERDNA AI - SIMPLIFIED DATA INGESTION STARTED")
        print(f"Dataset: {self.config['name']}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        try:
            # Step 1: Load and prepare data
            processed_df = self.load_and_prepare_data()
            
            # Summary
            print("\n" + "=" * 80)
            print("DATA INGESTION COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print(f"Dataset: {self.config['name']}")
            print(f"Records processed: {processed_df.shape[0]:,}")
            print(f"Processed CSV saved to: {self.ingested_data_dir}")
            print("=" * 80)
            print("\nNext steps:")
            print("1. Use ELT scripts in 'd:\\github\\Master_PFE_Project\\CustomerDNA AI\\src\\ELT' to load data to database")
            print("2. Apply dbt transformations in client1_DW")
            
            return {
                'success': True,
                'records_processed': processed_df.shape[0],
                'csv_path': os.path.join(self.ingested_data_dir, f"processed_{os.path.splitext(os.path.basename(self.data_path))[0]}.csv"),
                'dataset_folder': self.ingested_data_dir
            }
            
        except Exception as e:
            print(f"\nERROR: Data ingestion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("=" * 80)
    print("CUSTOMERDNA AI - SIMPLIFIED DATA INGESTION FOR E-COMMERCE CUSTOMER CHURN")
    print("=" * 80)
    print()
    print("Purpose: Process raw e-commerce customer data and save SQL-compatible CSV")
    print("Key Principle: Preserve original data format for audit trail")
    print("NO DATABASE LOADING - This script only creates processed CSV files")
    print("Database loading will be done by ELT scripts separately")
    print()
    
    try:
        # Initialize ingestor
        ingestor = EcommerceChurnIngestorSimple()
        
        # Run ingestion
        result = ingestor.run_ingestion()
        
        if result['success']:
            print("\n" + "=" * 80)
            print("SUCCESS: INGESTION COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print(f"Records processed: {result['records_processed']:,}")
            print(f"CSV saved to: {result['csv_path']}")
            print(f"Dataset folder: {result['dataset_folder']}")
        else:
            print("\n" + "=" * 80)
            print("ERROR: INGESTION FAILED")
            print("=" * 80)
            print(f"Error: {result['error']}")
        
        return result['success']
        
    except Exception as e:
        print(f"\nERROR: Fatal error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)