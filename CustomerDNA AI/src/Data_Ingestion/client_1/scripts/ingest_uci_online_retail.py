"""
CustomerDNA AI - Data Ingestion Script (Simplified)
Dataset: UCI Online Retail II
Purpose: Process raw data and save SQL-compatible CSV WITHOUT database loading
Handles Excel file with 2 sheets: 'Year 2009-2010' and 'Year 2010-2011'
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

class UCIOnlineRetailIngestorSimple:
    """Simplified data ingestion class for UCI Online Retail II dataset - only processes and saves CSV."""
    
    def __init__(self, dataset_name='uci_online_retail_2'):
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
        """Load data from both Excel sheets and apply ONLY necessary preprocessing for SQL compatibility."""
        print(f"\nLoading data from {self.data_path}")
        
        try:
            # Load both sheets from Excel file
            print(f"Reading sheets: {self.config['sheet_names']}")
            
            df_list = []
            for sheet_name in self.config['sheet_names']:
                df_sheet = pd.read_excel(
                    self.data_path,
                    sheet_name=sheet_name,
                    engine='openpyxl'
                )
                print(f"  - Sheet '{sheet_name}': {df_sheet.shape[0]:,} rows, {df_sheet.shape[1]} columns")
                df_list.append(df_sheet)
            
            # Combine both sheets
            df = pd.concat(df_list, ignore_index=True)
            print(f"Combined data: {df.shape[0]:,} rows, {df.shape[1]} columns")
            
            # Apply ONLY necessary preprocessing for SQL compatibility:
            processed_df = df.copy()
            
            # 1. Fix encoding issues (critical for SQL)
            for col in processed_df.select_dtypes(include=['object']).columns:
                processed_df[col] = processed_df[col].astype(str).str.encode('utf-8', 'ignore').str.decode('utf-8')
            
            # 2. Convert date columns to datetime (required for SQL DATE/TIMESTAMP)
            for date_col in self.config.get('date_columns', []):
                if date_col in processed_df.columns:
                    processed_df[date_col] = pd.to_datetime(
                        processed_df[date_col], 
                        errors='coerce'
                    )
                    print(f"Converted {date_col} to datetime for SQL compatibility")
            
            # 3. Convert numeric columns to proper types (for SQL numeric types)
            for col in self.config.get('numeric_columns', []):
                if col in processed_df.columns:
                    processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
            
            # 4. Handle Customer ID missing values (convert to -1 for SQL compatibility)
            if 'Customer ID' in processed_df.columns:
                # Fill NaN with -1 to represent unknown customers
                processed_df['Customer ID'] = processed_df['Customer ID'].fillna(-1)
                processed_df['Customer ID'] = processed_df['Customer ID'].astype(int)
                print(f"Processed Customer ID column for SQL compatibility")
            
            # 5. Handle Description missing values
            if 'Description' in processed_df.columns:
                processed_df['Description'] = processed_df['Description'].fillna('Unknown')
                print(f"Filled missing descriptions with 'Unknown'")
            
            # 6. Check for missing values in critical columns
            print(f"\nMissing values check:")
            missing_counts = processed_df.isnull().sum()
            for col, count in missing_counts.items():
                if count > 0:
                    percentage = count / len(processed_df) * 100
                    print(f"  - {col}: {count:,} missing ({percentage:.2f}%)")
            
            # 7. Basic data quality checks
            print(f"\nData quality checks:")
            
            # Check for negative quantities (returns)
            if 'Quantity' in processed_df.columns:
                negative_qty = (processed_df['Quantity'] < 0).sum()
                if negative_qty > 0:
                    print(f"  - Found {negative_qty:,} negative quantities (returns)")
            
            # Check for zero or negative prices
            if 'Price' in processed_df.columns:
                invalid_prices = (processed_df['Price'] <= 0).sum()
                if invalid_prices > 0:
                    print(f"  - Found {invalid_prices:,} invalid prices (<= 0)")
            
            # Check country distribution
            if 'Country' in processed_df.columns:
                top_countries = processed_df['Country'].value_counts().head(5)
                print(f"  - Top 5 countries:")
                for country, count in top_countries.items():
                    percentage = count / len(processed_df) * 100
                    print(f"    - {country}: {count:,} ({percentage:.1f}%)")
            
            print(f"\nProcessed data shape: {processed_df.shape}")
            return processed_df
            
        except Exception as e:
            print(f"[ERROR] Failed to process data: {e}")
            raise
    
    def save_processed_data(self, df):
        """Save processed DataFrame to CSV in the dataset folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"online_retail_processed_{timestamp}.csv"
        output_path = os.path.join(self.ingested_data_dir, filename)
        
        try:
            # Save with UTF-8 encoding for SQL compatibility
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"[OK] Saved processed data to: {output_path}")
            print(f"File size: {os.path.getsize(output_path):,} bytes")
            return output_path
        except Exception as e:
            print(f"[ERROR] Failed to save CSV: {e}")
            raise
    
    def run_ingestion(self):
        """Main method to run the complete ingestion process."""
        print("\n" + "="*80)
        print("UCI ONLINE RETAIL II DATASET INGESTION - SIMPLIFIED (NO DATABASE LOADING)")
        print("="*80)
        
        start_time = datetime.now()
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Process the data
            df_processed = self.load_and_prepare_data()
            
            # Save the processed data
            output_path = self.save_processed_data(df_processed)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "="*80)
            print("INGESTION COMPLETED SUCCESSFULLY")
            print("="*80)
            print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total duration: {duration}")
            print(f"Output file saved to: {output_path}")
            print(f"Total records processed: {len(df_processed):,}")
            
            # Summary statistics
            print(f"\nDataset summary:")
            print(f"- Columns: {len(df_processed.columns)}")
            print(f"- Date range: {df_processed['InvoiceDate'].min()} to {df_processed['InvoiceDate'].max()}")
            print(f"- Unique invoices: {df_processed['Invoice'].nunique():,}")
            print(f"- Unique customers: {df_processed['Customer ID'].nunique():,}")
            print(f"- Unique products: {df_processed['StockCode'].nunique():,}")
            
            print(f"\nNote: CSV file is SQL-compatible and ready for loading")
            print(f"      Database loading will be handled in the ELT folder")
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Ingestion failed: {e}")
            return False

def main():
    """Main entry point."""
    try:
        ingestor = UCIOnlineRetailIngestorSimple()
        success = ingestor.run_ingestion()
        
        if success:
            print(f"\n[SUCCESS] UCI Online Retail II dataset processed successfully!")
            print(f"Next step: Use ELT scripts to load processed CSV file to database")
        else:
            print(f"\n[FAILURE] UCI Online Retail II dataset processing failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()