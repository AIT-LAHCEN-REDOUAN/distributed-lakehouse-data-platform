"""
CustomerDNA AI - PFE Project
Dataset : UCI Online Retail 2 (online_retail_2.xlsx)
Script  : Enhanced Online Retail Preprocessing — Comprehensive Pipeline
Author  : PFE Student
Description: Comprehensive preprocessing pipeline for UCI Online Retail 2 dataset
             including data cleaning, RFM analysis, customer segmentation, and feature engineering
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Try to import optional libraries for advanced preprocessing
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[WARNING] scipy not available. Some advanced statistical preprocessing will be skipped.")

try:
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[WARNING] scikit-learn not available. Some advanced preprocessing techniques will be skipped.")

# ─────────────────────────────────────────────
# PATHS — adjust only these lines
# ─────────────────────────────────────────────
DATA_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\base_dataset\UCI_Online_Retail_2"
DATA_PATH = os.path.join(DATA_DIR, "online_retail_2.xlsx")

OUTPUT_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\UCI_Online_Retail_2_Preprocessing\cleaned_dataset"
LOG_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\UCI_Online_Retail_2_Preprocessing\logs"
CONFIG_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\UCI_Online_Retail_2_Preprocessing\config"

# ─────────────────────────────────────────────
# CONSTANTS — data preprocessing rules
# ─────────────────────────────────────────────
# Missing value handling thresholds
MISSING_THRESHOLD_DROP = 20.0  # Drop columns with >20% missing
MISSING_THRESHOLD_IMPUTE = 5.0  # Use advanced imputation for 5-20% missing

# Outlier handling thresholds
OUTLIER_THRESHOLD = 3.0  # Z-score threshold for outlier detection

# Sampling parameters (for memory management)
SAMPLE_SIZE = 100000  # Sample 100,000 records for memory efficiency

# Business rules for validation
BUSINESS_RULES = {
    'Quantity': {'min': -10000, 'max': 10000, 'description': 'Quantity should be reasonable'},
    'Price': {'min': 0, 'max': 10000, 'description': 'Price should be positive and reasonable'},
    'Customer ID': {'min': 1000, 'max': 20000, 'description': 'Customer ID range'},
    'InvoiceDate': {'min': '2009-12-01', 'max': '2011-12-09', 'description': 'Date range'},
    'Country': {'valid_countries': 43, 'description': 'Number of countries'}
}

# RFM analysis parameters
RFM_PARAMS = {
    'recency_days': 365,  # Consider purchases within last 365 days
    'frequency_bins': 5,  # Number of frequency bins
    'monetary_bins': 5    # Number of monetary value bins
}

class EnhancedOnlineRetailPreprocessing:
    """
    Enhanced preprocessing class for UCI Online Retail 2 dataset.
    Includes comprehensive data cleaning, RFM analysis, customer segmentation,
    and feature engineering for retail analytics applications.
    """

    def __init__(self, verbose=True):
        self.data_dir = DATA_DIR
        self.data_path = DATA_PATH
        
        self.output_dir = OUTPUT_DIR
        self.log_dir = LOG_DIR
        self.config_dir = CONFIG_DIR
        
        # Create directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.verbose = verbose
        self.preprocessing_report = {
            'dataset_info': {},
            'cleaning_summary': {},
            'feature_engineering_summary': {},
            'rfm_analysis': {},
            'validation_results': {}
        }
        
        # Data storage
        self.df_raw = None
        self.df_clean = None
        self.df_processed = None
        self.rfm_data = None
        
        # Setup logging
        self.log_file = os.path.join(self.log_dir, f"preprocessing_log_{datetime.now().strftime('%Y%m%d')}.txt")
        
    def _log(self, message, level="INFO"):
        """Log message to file and optionally print to console."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
        
        if self.verbose:
            print(log_entry)
    
    # ─────────────────────────────────────────
    # 1. LOAD DATA
    # ─────────────────────────────────────────
    def load_data(self):
        """Load the UCI Online Retail 2 dataset."""
        self._log("load_data() started")
        
        try:
            # 1.1 Load Excel file
            self._log("1.1 Loading Excel data...")
            self.df_raw = pd.read_excel(self.data_path)
            
            # 1.2 Basic dataset info
            self._log(f"  Successfully loaded {len(self.df_raw):,} rows × {len(self.df_raw.columns)} columns")
            
            # 1.3 Display column information
            self._log("  Columns:")
            for col in self.df_raw.columns:
                dtype = self.df_raw[col].dtype
                non_null = self.df_raw[col].notnull().sum()
                null_pct = (self.df_raw[col].isnull().sum() / len(self.df_raw)) * 100
                self._log(f"    - {col}: {dtype}, {non_null:,} non-null ({null_pct:.1f}% missing)")
            
            # 1.4 Store dataset info
            self.preprocessing_report['dataset_info'] = {
                'original_shape': self.df_raw.shape,
                'columns': list(self.df_raw.columns),
                'dtypes': {col: str(dtype) for col, dtype in self.df_raw.dtypes.items()},
                'memory_usage_mb': self.df_raw.memory_usage(deep=True).sum() / 1024 / 1024
            }
            
            # 1.5 Display summary statistics
            self._log("\nDataset Overview:")
            self._log(f"  - Total records: {len(self.df_raw):,}")
            self._log(f"  - Date range: {self.df_raw['InvoiceDate'].min().date()} to {self.df_raw['InvoiceDate'].max().date()}")
            self._log(f"  - Unique customers: {self.df_raw['Customer ID'].nunique():,}")
            self._log(f"  - Unique products: {self.df_raw['StockCode'].nunique():,}")
            self._log(f"  - Unique countries: {self.df_raw['Country'].nunique():,}")
            
            # Calculate total revenue
            self.df_raw['TotalValue'] = self.df_raw['Quantity'] * self.df_raw['Price']
            total_revenue = self.df_raw['TotalValue'].sum()
            self._log(f"  - Total revenue: ${total_revenue:,.2f}")
            
            # Transaction count
            transaction_count = self.df_raw['Invoice'].nunique()
            self._log(f"  - Total transactions: {transaction_count:,}")
            
            self._log("load_data() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to load data: {str(e)}", "ERROR")
            return False
    
    # ─────────────────────────────────────────
    # 2. CLEAN DATA
    # ─────────────────────────────────────────
    def clean_data(self):
        """Clean the raw dataset."""
        self._log("clean_data() started")
        
        if self.df_raw is None:
            self._log("No raw data available. Run load_data() first.", "ERROR")
            return False
        
        try:
            df = self.df_raw.copy()
            cleaning_summary = {
                'rows_removed': 0,
                'columns_removed': 0,
                'missing_values_handled': {},
                'data_type_conversions': {}
            }
            
            # 2.1 Handle missing values
            self._log("2.1 Handling missing values...")
            
            missing_counts = df.isnull().sum()
            missing_pct = (missing_counts / len(df)) * 100
            
            for col in df.columns:
                if missing_pct[col] > 0:
                    self._log(f"  - {col}: {missing_counts[col]:,} missing ({missing_pct[col]:.1f}%)")
                    
                    # Special handling for Customer ID - critical for retail analytics
                    if col == 'Customer ID':
                        # For Customer ID, we'll create a special value for missing customers
                        # This allows us to still analyze anonymous transactions
                        df[col] = df[col].fillna(-1)
                        cleaning_summary['missing_values_handled'][col] = 'special_value_imputation'
                        self._log(f"    Imputed with special value -1 for anonymous customers")
                    elif missing_pct[col] > MISSING_THRESHOLD_DROP:
                        # Drop column if too many missing values (except Customer ID)
                        df = df.drop(columns=[col])
                        cleaning_summary['columns_removed'] += 1
                        self._log(f"    Dropping column (> {MISSING_THRESHOLD_DROP}% missing)")
                    elif missing_pct[col] > MISSING_THRESHOLD_IMPUTE:
                        # Advanced imputation for moderate missing values
                        if df[col].dtype in [np.float64, np.int64]:
                            df[col] = df[col].fillna(df[col].median())
                            cleaning_summary['missing_values_handled'][col] = 'median_imputation'
                            self._log(f"    Imputed with median")
                        else:
                            df[col] = df[col].fillna('Unknown')
                            cleaning_summary['missing_values_handled'][col] = 'constant_imputation'
                            self._log(f"    Imputed with 'Unknown'")
                    else:
                        # Simple imputation for few missing values
                        if df[col].dtype in [np.float64, np.int64]:
                            df[col] = df[col].fillna(0)
                            cleaning_summary['missing_values_handled'][col] = 'zero_imputation'
                            self._log(f"    Imputed with 0")
                        else:
                            df[col] = df[col].fillna('Unknown')
                            cleaning_summary['missing_values_handled'][col] = 'constant_imputation'
                            self._log(f"    Imputed with 'Unknown'")
            
            # 2.2 Standardize text values
            self._log("2.2 Standardizing text values...")
            
            text_cols = df.select_dtypes(include=['object']).columns
            for col in text_cols:
                if col in ['Description', 'Country']:
                    df[col] = df[col].str.strip().str.title()
                    self._log(f"  Standardized '{col}'")
            
            # 2.3 Check for duplicates
            self._log("2.3 Checking for duplicates...")
            
            duplicate_count = df.duplicated().sum()
            if duplicate_count > 0:
                df = df.drop_duplicates()
                cleaning_summary['rows_removed'] += duplicate_count
                self._log(f"  Found {duplicate_count:,} duplicate rows - removing")
            else:
                self._log("  No duplicate rows found")
            
            # 2.4 Validate data types
            self._log("2.4 Validating data types...")
            
            # Ensure InvoiceDate is datetime
            if 'InvoiceDate' in df.columns:
                df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
                cleaning_summary['data_type_conversions']['InvoiceDate'] = 'datetime'
                self._log("  Converted 'InvoiceDate' to datetime")
            
            # Ensure numeric columns are correct type
            numeric_cols = ['Quantity', 'Price', 'Customer ID']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    cleaning_summary['data_type_conversions'][col] = 'numeric'
                    self._log(f"  Converted '{col}' to numeric")
            
            # 2.5 Remove invalid transactions
            self._log("2.5 Removing invalid transactions...")
            
            # Remove cancelled invoices (negative quantities)
            initial_count = len(df)
            df = df[df['Quantity'] > 0]
            cancelled_count = initial_count - len(df)
            cleaning_summary['rows_removed'] += cancelled_count
            
            if cancelled_count > 0:
                self._log(f"  Removed {cancelled_count:,} cancelled invoice records")
            
            # Remove free items (price = 0)
            initial_count = len(df)
            df = df[df['Price'] > 0]
            free_items_count = initial_count - len(df)
            cleaning_summary['rows_removed'] += free_items_count
            
            if free_items_count > 0:
                self._log(f"  Removed {free_items_count:,} free item records")
            
            # Store cleaned data
            self.df_clean = df
            
            # Update preprocessing report
            cleaning_summary['cleaned_shape'] = df.shape
            self.preprocessing_report['cleaning_summary'] = cleaning_summary
            
            self._log(f"Cleaning completed: {len(df):,} rows, {len(df.columns)} columns")
            self._log("clean_data() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to clean data: {str(e)}", "ERROR")
            return False
    
    # ─────────────────────────────────────────
    # 3. ENGINEER FEATURES
    # ─────────────────────────────────────────
    def engineer_features(self):
        """Create comprehensive features for retail analytics."""
        self._log("engineer_features() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run clean_data() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            new_features_count = 0
            
            # 3.1 Create temporal features
            self._log("3.1 Creating temporal features...")
            
            df['InvoiceYear'] = df['InvoiceDate'].dt.year
            df['InvoiceMonth'] = df['InvoiceDate'].dt.month
            df['InvoiceDay'] = df['InvoiceDate'].dt.day
            df['InvoiceHour'] = df['InvoiceDate'].dt.hour
            df['InvoiceDayOfWeek'] = df['InvoiceDate'].dt.dayofweek
            df['InvoiceWeekOfYear'] = df['InvoiceDate'].dt.isocalendar().week
            df['InvoiceQuarter'] = df['InvoiceDate'].dt.quarter
            
            # Day name and month name
            df['DayName'] = df['InvoiceDate'].dt.day_name()
            df['MonthName'] = df['InvoiceDate'].dt.month_name()
            
            # Weekend flag
            df['IsWeekend'] = df['InvoiceDayOfWeek'].isin([5, 6]).astype(int)
            
            # Time of day categories
            def categorize_time_of_day(hour):
                if 5 <= hour < 12:
                    return 'Morning'
                elif 12 <= hour < 17:
                    return 'Afternoon'
                elif 17 <= hour < 21:
                    return 'Evening'
                else:
                    return 'Night'
            
            df['TimeOfDay'] = df['InvoiceHour'].apply(categorize_time_of_day)
            
            new_features_count += 12  # Count all temporal features
            
            # 3.2 Create transaction-level features
            self._log("3.2 Creating transaction-level features...")
            
            # Calculate total value for each line item
            df['LineItemValue'] = df['Quantity'] * df['Price']
            
            # Create transaction summary
            transaction_summary = df.groupby('Invoice').agg({
                'LineItemValue': 'sum',
                'Quantity': 'sum',
                'Customer ID': 'first',
                'InvoiceDate': 'first',
                'Country': 'first'
            }).reset_index()
            
            transaction_summary.columns = ['Invoice', 'TransactionValue', 'TotalQuantity', 
                                          'Customer ID', 'InvoiceDate', 'Country']
            
            # Merge transaction summary back
            df = df.merge(transaction_summary[['Invoice', 'TransactionValue', 'TotalQuantity']], 
                         on='Invoice', how='left')
            
            new_features_count += 3  # LineItemValue, TransactionValue, TotalQuantity
            
            # 3.3 Create customer-level features
            self._log("3.3 Creating customer-level features...")
            
            # Calculate customer tenure (days since first purchase)
            customer_first_purchase = df.groupby('Customer ID')['InvoiceDate'].min().reset_index()
            customer_first_purchase.columns = ['Customer ID', 'FirstPurchaseDate']
            
            # Calculate customer last purchase
            customer_last_purchase = df.groupby('Customer ID')['InvoiceDate'].max().reset_index()
            customer_last_purchase.columns = ['Customer ID', 'LastPurchaseDate']
            
            # Merge customer features
            df = df.merge(customer_first_purchase, on='Customer ID', how='left')
            df = df.merge(customer_last_purchase, on='Customer ID', how='left')
            
            # Calculate customer tenure in days
            df['CustomerTenureDays'] = (df['LastPurchaseDate'] - df['FirstPurchaseDate']).dt.days
            df['DaysSinceLastPurchase'] = (datetime.now() - df['LastPurchaseDate']).dt.days
            
            new_features_count += 4  # FirstPurchaseDate, LastPurchaseDate, CustomerTenureDays, DaysSinceLastPurchase
            
            # 3.4 Create product-level features
            self._log("3.4 Creating product-level features...")
            
            # Product popularity (total quantity sold)
            product_popularity = df.groupby('StockCode').agg({
                'Quantity': 'sum',
                'LineItemValue': 'sum',
                'Invoice': 'nunique'
            }).reset_index()
            
            product_popularity.columns = ['StockCode', 'TotalQuantitySold', 'TotalRevenue', 'TransactionCount']
            
            # Merge product features
            df = df.merge(product_popularity, on='StockCode', how='left')
            
            new_features_count += 3  # TotalQuantitySold, TotalRevenue, TransactionCount
            
            # 3.5 Create derived features
            self._log("3.5 Creating derived features...")
            
            # Average price per unit for the transaction
            df['AvgPricePerUnit'] = df['TransactionValue'] / df['TotalQuantity']
            
            # Price ratio (item price vs transaction average)
            df['PriceRatio'] = df['Price'] / df['AvgPricePerUnit']
            
            # Quantity ratio (item quantity vs transaction total)
            df['QuantityRatio'] = df['Quantity'] / df['TotalQuantity']
            
            # Customer loyalty score (based on purchase frequency)
            customer_purchase_freq = df.groupby('Customer ID')['Invoice'].nunique().reset_index()
            customer_purchase_freq.columns = ['Customer ID', 'PurchaseFrequency']
            
            # Normalize purchase frequency
            max_freq = customer_purchase_freq['PurchaseFrequency'].max()
            customer_purchase_freq['LoyaltyScore'] = customer_purchase_freq['PurchaseFrequency'] / max_freq
            
            df = df.merge(customer_purchase_freq[['Customer ID', 'LoyaltyScore']], 
                         on='Customer ID', how='left')
            
            new_features_count += 4  # AvgPricePerUnit, PriceRatio, QuantityRatio, LoyaltyScore
            
            # 3.6 Create RFM features
            self._log("3.6 Creating RFM features...")
            
            # Calculate RFM metrics
            current_date = df['InvoiceDate'].max() + timedelta(days=1)
            
            rfm = df.groupby('Customer ID').agg({
                'InvoiceDate': lambda x: (current_date - x.max()).days,  # Recency
                'Invoice': 'nunique',  # Frequency
                'LineItemValue': 'sum'  # Monetary
            }).reset_index()
            
            rfm.columns = ['Customer ID', 'Recency', 'Frequency', 'Monetary']
            
            # Create RFM scores (higher is better)
            # Handle potential errors in pd.qcut with try-except
            try:
                rfm['R_Score'] = pd.qcut(rfm['Recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
            except Exception as e:
                self._log(f"  Warning: Recency qcut failed: {str(e)}. Using rank-based scoring.", "WARNING")
                rfm['R_Score'] = pd.qcut(rfm['Recency'].rank(method='first'), q=5, labels=[5, 4, 3, 2, 1])
            
            try:
                rfm['F_Score'] = pd.qcut(rfm['Frequency'], q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
            except Exception as e:
                self._log(f"  Warning: Frequency qcut failed: {str(e)}. Using rank-based scoring.", "WARNING")
                rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])
            
            try:
                rfm['M_Score'] = pd.qcut(rfm['Monetary'], q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
            except Exception as e:
                self._log(f"  Warning: Monetary qcut failed: {str(e)}. Using rank-based scoring.", "WARNING")
                rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])
            
            # Convert scores to numeric
            rfm['R_Score'] = pd.to_numeric(rfm['R_Score'])
            rfm['F_Score'] = pd.to_numeric(rfm['F_Score'])
            rfm['M_Score'] = pd.to_numeric(rfm['M_Score'])
            
            # Calculate RFM total score
            rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']
            
            # Create RFM segments
            def create_rfm_segment(row):
                if row['R_Score'] >= 4 and row['F_Score'] >= 4 and row['M_Score'] >= 4:
                    return 'Champions'
                elif row['R_Score'] >= 4 and row['F_Score'] >= 3:
                    return 'Loyal Customers'
                elif row['R_Score'] >= 3 and row['F_Score'] >= 3:
                    return 'Potential Loyalists'
                elif row['R_Score'] >= 4:
                    return 'Recent Customers'
                elif row['R_Score'] >= 2 and row['F_Score'] >= 2:
                    return 'Customers Needing Attention'
                else:
                    return 'At Risk'
            
            rfm['RFM_Segment'] = rfm.apply(create_rfm_segment, axis=1)
            
            # Store RFM data
            self.rfm_data = rfm
            
            # Merge RFM features
            df = df.merge(rfm, on='Customer ID', how='left')
            
            new_features_count += 8  # Recency, Frequency, Monetary, R_Score, F_Score, M_Score, RFM_Score, RFM_Segment
            
            # 3.7 Create country-level features
            self._log("3.7 Creating country-level features...")
            
            # Country transaction count
            country_stats = df.groupby('Country').agg({
                'Invoice': 'nunique',
                'LineItemValue': 'sum',
                'Customer ID': 'nunique'
            }).reset_index()
            
            country_stats.columns = ['Country', 'CountryTransactionCount', 'CountryTotalRevenue', 'CountryCustomerCount']
            
            # Merge country features
            df = df.merge(country_stats, on='Country', how='left')
            
            new_features_count += 3  # CountryTransactionCount, CountryTotalRevenue, CountryCustomerCount
            
            # Store processed data
            self.df_processed = df
            
            # Update preprocessing report
            self.preprocessing_report['feature_engineering_summary'] = {
                'new_features_created': new_features_count,
                'processed_shape': df.shape,
                'feature_categories': {
                    'temporal': 12,
                    'transaction': 3,
                    'customer': 4,
                    'product': 3,
                    'derived': 4,
                    'rfm': 8,
                    'country': 3
                }
            }
            
            self._log(f"Feature engineering completed: Added {new_features_count} new features")
            self._log(f"Processed dataset: {df.shape[0]:,} rows × {df.shape[1]} columns")
            self._log("engineer_features() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to engineer features: {str(e)}", "ERROR")
            return False
    
    # ─────────────────────────────────────────
    # 4. HANDLE OUTLIERS
    # ─────────────────────────────────────────
    def handle_outliers(self):
        """Detect and handle outliers in numerical features."""
        self._log("handle_outliers() started")
        
        if self.df_processed is None:
            self._log("No processed data available. Run engineer_features() first.", "ERROR")
            return False
        
        try:
            df = self.df_processed.copy()
            outlier_summary = {}
            total_outliers = 0
            
            # 4.1 Identify numerical columns for outlier detection
            self._log("4.1 Checking numerical features for outliers...")
            
            numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Exclude ID columns and scores
            exclude_cols = ['Customer ID', 'R_Score', 'F_Score', 'M_Score', 'RFM_Score']
            numerical_cols = [col for col in numerical_cols if col not in exclude_cols]
            
            self._log(f"  Checking {len(numerical_cols)} numerical features")
            
            # Log column types for debugging
            if self.verbose:
                for col in numerical_cols[:10]:  # Show first 10 columns
                    dtype = df[col].dtype
                    self._log(f"    '{col}': {dtype}")
                if len(numerical_cols) > 10:
                    self._log(f"    ... and {len(numerical_cols) - 10} more columns")
            
            # 4.2 Detect and cap outliers using IQR method
            for col in numerical_cols:
                # Skip if column has too many missing values or constant values
                if df[col].nunique() <= 1:
                    continue
                
                # Calculate IQR
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                # Define outlier bounds
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Identify outliers
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                outlier_count = len(outliers)
                
                if outlier_count > 0:
                    try:
                        # Cap outliers with proper type handling
                        # Check if column is integer type
                        if pd.api.types.is_integer_dtype(df[col]):
                            # For integer columns, round bounds to nearest integer
                            lower_bound_int = int(round(lower_bound))
                            upper_bound_int = int(round(upper_bound))
                            df.loc[df[col] < lower_bound, col] = lower_bound_int
                            df.loc[df[col] > upper_bound, col] = upper_bound_int
                        else:
                            # For float columns, use bounds as-is
                            df.loc[df[col] < lower_bound, col] = lower_bound
                            df.loc[df[col] > upper_bound, col] = upper_bound
                    except Exception as e:
                        self._log(f"    Warning: Failed to cap outliers for '{col}': {str(e)}. Skipping this column.", "WARNING")
                        continue
                    
                    outlier_summary[col] = {
                        'outlier_count': outlier_count,
                        'outlier_pct': (outlier_count / len(df)) * 100,
                        'method': 'iqr_capping',
                        'lower_bound': lower_bound,
                        'upper_bound': upper_bound
                    }
                    
                    total_outliers += outlier_count
                    self._log(f"  '{col}': {outlier_count:,} outliers ({outlier_summary[col]['outlier_pct']:.1f}%) - capped")
            
            # 4.3 Update processed data
            self.df_processed = df
            
            # Update preprocessing report
            self.preprocessing_report['outlier_handling_summary'] = {
                'features_checked': len(numerical_cols),
                'features_with_outliers': len(outlier_summary),
                'total_outliers': total_outliers,
                'outlier_details': outlier_summary
            }
            
            self._log(f"Outlier handling completed: {total_outliers:,} outliers capped across {len(outlier_summary)} features")
            self._log("handle_outliers() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to handle outliers: {str(e)}", "ERROR")
            return False
    
    # ─────────────────────────────────────────
    # 5. ENCODE AND SCALE
    # ─────────────────────────────────────────
    def encode_and_scale(self):
        """Encode categorical variables and scale numerical features."""
        self._log("encode_and_scale() started")
        
        if self.df_processed is None:
            self._log("No processed data available. Run handle_outliers() first.", "ERROR")
            return False
        
        try:
            df = self.df_processed.copy()
            
            # 5.1 Encode categorical variables
            self._log("5.1 Encoding categorical variables...")
            
            # Identify categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            # Remove columns that are already encoded or are IDs
            exclude_cats = ['Invoice', 'StockCode', 'Description', 'DayName', 'MonthName']
            categorical_cols = [col for col in categorical_cols if col not in exclude_cats]
            
            encoding_summary = {}
            
            for col in categorical_cols:
                if col == 'TimeOfDay':
                    # Ordinal encoding for time of day
                    time_order = ['Morning', 'Afternoon', 'Evening', 'Night']
                    df[col] = pd.Categorical(df[col], categories=time_order, ordered=True)
                    df[f'{col}_encoded'] = df[col].cat.codes
                    encoding_summary[col] = {'method': 'ordinal', 'categories': time_order}
                    self._log(f"  Ordinal encoded '{col}'")
                elif col == 'RFM_Segment':
                    # Ordinal encoding for RFM segments (based on value)
                    segment_order = ['Champions', 'Loyal Customers', 'Potential Loyalists', 
                                   'Recent Customers', 'Customers Needing Attention', 'At Risk']
                    df[col] = pd.Categorical(df[col], categories=segment_order, ordered=True)
                    df[f'{col}_encoded'] = df[col].cat.codes
                    encoding_summary[col] = {'method': 'ordinal', 'categories': segment_order}
                    self._log(f"  Ordinal encoded '{col}'")
                else:
                    # Label encoding for other categoricals
                    if HAS_SKLEARN:
                        le = LabelEncoder()
                        df[f'{col}_encoded'] = le.fit_transform(df[col].fillna('Unknown'))
                        encoding_summary[col] = {'method': 'label', 'classes': le.classes_.tolist()}
                    else:
                        # Manual label encoding
                        unique_vals = df[col].fillna('Unknown').unique()
                        val_to_code = {val: i for i, val in enumerate(unique_vals)}
                        df[f'{col}_encoded'] = df[col].fillna('Unknown').map(val_to_code)
                        encoding_summary[col] = {'method': 'label', 'classes': unique_vals.tolist()}
                    self._log(f"  Label encoded '{col}'")
            
            # 5.2 Scale numerical features
            self._log("5.2 Scaling numerical features...")
            
            # Identify numerical columns to scale (excluding IDs and encoded columns)
            numerical_to_scale = df.select_dtypes(include=[np.number]).columns.tolist()
            exclude_numerical = ['Customer ID', 'InvoiceYear', 'InvoiceMonth', 'InvoiceDay', 
                               'InvoiceHour', 'InvoiceDayOfWeek', 'InvoiceWeekOfWeekYear',
                               'InvoiceQuarter', 'IsWeekend'] + \
                               [f'{col}_encoded' for col in categorical_cols]
            
            numerical_to_scale = [col for col in numerical_to_scale if col not in exclude_numerical]
            
            scaling_summary = {}
            
            for col in numerical_to_scale:
                # Skip if column has too many missing values or constant values
                if df[col].nunique() <= 1:
                    continue
                
                # Min-max scaling
                min_val = df[col].min()
                max_val = df[col].max()
                
                if max_val > min_val:  # Avoid division by zero
                    df[f'{col}_scaled'] = (df[col] - min_val) / (max_val - min_val)
                    scaling_summary[col] = {
                        'method': 'min_max',
                        'original_min': min_val,
                        'original_max': max_val
                    }
                    self._log(f"  Scaled '{col}' using min-max")
            
            # Update processed dataframe
            self.df_processed = df
            
            # Update preprocessing report
            self.preprocessing_report['encoding_scaling_summary'] = {
                'categorical_encoded': len(categorical_cols),
                'numerical_scaled': len(scaling_summary),
                'encoding_details': encoding_summary,
                'scaling_details': scaling_summary
            }
            
            self._log(f"Encoding and scaling completed: {len(categorical_cols)} categorical encoded, {len(scaling_summary)} numerical scaled")
            self._log("encode_and_scale() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to encode and scale: {str(e)}", "ERROR")
            return False
    
    # ─────────────────────────────────────────
    # 6. VALIDATE AND EXPORT
    # ─────────────────────────────────────────
    def validate_and_export(self):
        """Validate processed data and export to multiple formats."""
        self._log("validate_and_export() started")
        
        if self.df_processed is None:
            self._log("No processed data available. Run encode_and_scale() first.", "ERROR")
            return False
        
        try:
            df = self.df_processed.copy()
            validation_report = {'checks_passed': 0, 'checks_failed': 0, 'details': []}
            
            # 6.1 Basic validation checks
            self._log("6.1 Performing validation checks...")
            
            # Check 1: No missing values in key columns
            key_cols = ['Invoice', 'StockCode', 'Quantity', 'Price', 'Customer ID', 'InvoiceDate']
            key_cols = [col for col in key_cols if col in df.columns]
            
            missing_check = df[key_cols].isnull().sum().sum() == 0
            if missing_check:
                validation_report['checks_passed'] += 1
                validation_report['details'].append({'check': 'missing_values_key', 'status': 'PASS', 'message': 'No missing values in key columns'})
                self._log("  [PASS] No missing values in key columns")
            else:
                validation_report['checks_failed'] += 1
                missing_count = df[key_cols].isnull().sum().sum()
                validation_report['details'].append({'check': 'missing_values_key', 'status': 'FAIL', 'message': f'{missing_count} missing values in key columns'})
                self._log(f"  [FAIL] Found {missing_count} missing values in key columns", "WARNING")
            
            # Check 2: Valid quantity range (positive values)
            quantity_check = (df['Quantity'] > 0).all()
            if quantity_check:
                validation_report['checks_passed'] += 1
                validation_report['details'].append({'check': 'quantity_range', 'status': 'PASS', 'message': 'All quantities are positive'})
                self._log("  [PASS] All quantities are positive")
            else:
                validation_report['checks_failed'] += 1
                invalid_count = (df['Quantity'] <= 0).sum()
                validation_report['details'].append({'check': 'quantity_range', 'status': 'FAIL', 'message': f'{invalid_count} non-positive quantities found'})
                self._log(f"  [FAIL] Found {invalid_count} non-positive quantities", "WARNING")
            
            # Check 3: Valid price range (positive values)
            price_check = (df['Price'] > 0).all()
            if price_check:
                validation_report['checks_passed'] += 1
                validation_report['details'].append({'check': 'price_range', 'status': 'PASS', 'message': 'All prices are positive'})
                self._log("  [PASS] All prices are positive")
            else:
                validation_report['checks_failed'] += 1
                invalid_count = (df['Price'] <= 0).sum()
                validation_report['details'].append({'check': 'price_range', 'status': 'FAIL', 'message': f'{invalid_count} non-positive prices found'})
                self._log(f"  [FAIL] Found {invalid_count} non-positive prices", "WARNING")
            
            # Check 4: Valid date range
            date_check = df['InvoiceDate'].between(pd.Timestamp(BUSINESS_RULES['InvoiceDate']['min']), 
                                                  pd.Timestamp(BUSINESS_RULES['InvoiceDate']['max'])).all()
            if date_check:
                validation_report['checks_passed'] += 1
                validation_report['details'].append({'check': 'date_range', 'status': 'PASS', 'message': 'All dates within valid range'})
                self._log("  [PASS] All dates within valid range")
            else:
                validation_report['checks_failed'] += 1
                min_date = df['InvoiceDate'].min()
                max_date = df['InvoiceDate'].max()
                validation_report['details'].append({'check': 'date_range', 'status': 'FAIL', 'message': f'Dates outside range: min={min_date}, max={max_date}'})
                self._log(f"  [FAIL] Dates outside valid range: min={min_date}, max={max_date}", "WARNING")
            
            # 6.2 Export processed data
            self._log("6.2 Exporting processed data...")
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Export cleaned dataset
            csv_path = os.path.join(self.output_dir, f"cleaned_online_retail_{timestamp_str}.csv")
            df.to_csv(csv_path, index=False)
            self._log(f"  [OK] Exported to CSV: {csv_path}")
            
            # Export RFM data separately
            if self.rfm_data is not None:
                rfm_path = os.path.join(self.output_dir, f"rfm_data_{timestamp_str}.csv")
                self.rfm_data.to_csv(rfm_path, index=False)
                self._log(f"  [OK] Exported RFM data: {rfm_path}")
            
            # 6.3 Save preprocessing report
            self._log("6.3 Saving preprocessing report...")
            
            # Update validation results
            self.preprocessing_report['validation_results'] = validation_report
            
            # Save JSON report
            json_path = os.path.join(self.log_dir, f"preprocessing_report_{timestamp_str}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.preprocessing_report, f, indent=2, default=str)
            self._log(f"  [OK] Saved JSON report: {json_path}")
            
            # Save text summary
            summary_path = os.path.join(self.log_dir, f"preprocessing_summary_{timestamp_str}.txt")
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("UCI ONLINE RETAIL 2 - PREPROCESSING SUMMARY REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("1. DATASET OVERVIEW\n")
                f.write("-" * 40 + "\n")
                f.write(f"Original records: {self.preprocessing_report['dataset_info'].get('original_shape', (0, 0))[0]:,} rows\n")
                f.write(f"Cleaned records: {self.preprocessing_report['cleaning_summary'].get('cleaned_shape', (0, 0))[0]:,} rows\n")
                f.write(f"Rows removed: {self.preprocessing_report['cleaning_summary'].get('rows_removed', 0):,}\n\n")
                
                f.write("2. FEATURE ENGINEERING\n")
                f.write("-" * 40 + "\n")
                f.write(f"New features created: {self.preprocessing_report['feature_engineering_summary'].get('new_features_created', 0)}\n")
                f.write(f"Processed dataset: {self.preprocessing_report['feature_engineering_summary'].get('processed_shape', (0, 0))[0]:,} rows × {self.preprocessing_report['feature_engineering_summary'].get('processed_shape', (0, 0))[1]} columns\n\n")
                
                f.write("3. VALIDATION RESULTS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Checks passed: {validation_report['checks_passed']}\n")
                f.write(f"Checks failed: {validation_report['checks_failed']}\n\n")
                
                f.write("4. OUTPUT FILES\n")
                f.write("-" * 40 + "\n")
                f.write(f"Cleaned dataset: {csv_path}\n")
                if self.rfm_data is not None:
                    f.write(f"RFM data: {rfm_path}\n")
                f.write(f"JSON report: {json_path}\n")
                f.write(f"Text summary: {summary_path}\n")
            
            self._log(f"  [OK] Saved text summary: {summary_path}")
            
            # 6.4 Display final summary
            self._log("\n" + "=" * 80)
            self._log("PREPROCESSING COMPLETED SUCCESSFULLY")
            self._log("=" * 80)
            self._log(f"Original dataset: {self.preprocessing_report['dataset_info'].get('original_shape', (0, 0))[0]:,} rows × {self.preprocessing_report['dataset_info'].get('original_shape', (0, 0))[1]} columns")
            self._log(f"Processed dataset: {self.preprocessing_report['feature_engineering_summary'].get('processed_shape', (0, 0))[0]:,} rows × {self.preprocessing_report['feature_engineering_summary'].get('processed_shape', (0, 0))[1]} columns")
            self._log(f"New features created: {self.preprocessing_report['feature_engineering_summary'].get('new_features_created', 0)}")
            self._log(f"Validation checks: {validation_report['checks_passed']} passed, {validation_report['checks_failed']} failed")
            self._log(f"Output files saved in: {self.output_dir}")
            self._log(f"Logs and reports saved in: {self.log_dir}")
            
            self._log("validate_and_export() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to validate and export: {str(e)}", "ERROR")
            return False
    
    # ─────────────────────────────────────────
    # MAIN PIPELINE
    # ─────────────────────────────────────────
    def run_full_pipeline(self):
        """Execute the complete preprocessing pipeline."""
        self._log("Starting full preprocessing pipeline...")
        
        steps = [
            ("1. Loading data...", self.load_data),
            ("2. Cleaning data...", self.clean_data),
            ("3. Engineering features...", self.engineer_features),
            ("4. Handling outliers...", self.handle_outliers),
            ("5. Encoding and scaling...", self.encode_and_scale),
            ("6. Validating and exporting...", self.validate_and_export)
        ]
        
        successful_steps = 0
        
        for step_name, step_func in steps:
            self._log(f"\n{step_name}")
            if step_func():
                successful_steps += 1
                self._log(f"{step_name.strip()} completed successfully")
            else:
                self._log(f"{step_name.strip()} failed", "ERROR")
                break
        
        if successful_steps == len(steps):
            self._log("\nAll 6 preprocessing steps completed successfully!")
            return True
        else:
            self._log(f"\nPreprocessing incomplete. {successful_steps}/{len(steps)} steps completed.", "WARNING")
            return False


# ─────────────────────────────────────────
# EXECUTION
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("UCI ONLINE RETAIL 2 - ENHANCED PREPROCESSING")
    print("=" * 80)
    print(f"Data   : {DATA_DIR}")
    print(f"Output : {OUTPUT_DIR}")
    print(f"Logs   : {LOG_DIR}")
    print("-" * 80)
    
    # Initialize and run preprocessing
    preprocessor = EnhancedOnlineRetailPreprocessing(verbose=True)
    
    if preprocessor.run_full_pipeline():
        print("\n" + "=" * 80)
        print("PREPROCESSING COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Check the cleaned dataset in the 'cleaned_dataset' folder")
        print("2. Review the preprocessing report in the 'logs' folder")
        print("3. Proceed with customer segmentation and predictive modeling")
    else:
        print("\n" + "=" * 80)
        print("PREPROCESSING FAILED OR INCOMPLETE")
        print("=" * 80)
        print("\nPlease check the logs for details and fix any issues.")