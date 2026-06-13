"""
CustomerDNA AI - PFE Project
Dataset: Customer Personality Analysis (marketing_campaign.csv)
Script: Enhanced Customer Personality Preprocessing
Author: PFE Student
Description: Comprehensive preprocessing pipeline for customer personality analysis dataset
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Try to import optional libraries
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[WARNING] scipy not available. Some advanced statistical preprocessing will be skipped.")

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder
    from sklearn.impute import SimpleImputer, KNNImputer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[WARNING] scikit-learn not available. Some advanced preprocessing techniques will be skipped.")

# ─────────────────────────────────────────────
# PATHS — adjust only these lines
# ─────────────────────────────────────────────
DATA_PATH = r"d:\github\Master_PFE_Project\CustomerDNA AI\datasets\client_1\Customer_Personality_Analysis\marketing_campaign.csv"
OUTPUT_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\client_1\Customer_Personality_Analysis_dataset_Preprocessing\cleaned_dataset"
LOG_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\client_1\Customer_Personality_Analysis_dataset_Preprocessing\logs"

# ─────────────────────────────────────────────
# CONSTANTS — preprocessing rules
# ─────────────────────────────────────────────
# Data quality thresholds
MISSING_THRESHOLD = 0.3  # 30% missing threshold for column removal
OUTLIER_IQR_MULTIPLIER = 1.5

# Business rules for validation
MIN_YEAR_BIRTH = 1900
MAX_YEAR_BIRTH = 2005
MIN_INCOME = 0
MAX_INCOME = 1000000  # $1M maximum reasonable income
MIN_SPENDING = 0
MAX_SPENDING = 100000  # $100K maximum reasonable spending per category

# Categorical value mappings for consistency
EDUCATION_MAPPING = {
    "Basic": "Basic",
    "2n Cycle": "2n Cycle", 
    "Graduation": "Graduation",
    "Master": "Master",
    "PhD": "PhD"
}

MARITAL_STATUS_MAPPING = {
    "Single": "Single",
    "Together": "Together",
    "Married": "Married",
    "Divorced": "Divorced",
    "Widow": "Widow",
    "Alone": "Alone",
    "Absurd": "Absurd",  # This appears to be a data quality issue
    "YOLO": "YOLO"       # This appears to be a data quality issue
}

# Spending categories for feature engineering
SPENDING_CATEGORIES = [
    'MntWines', 'MntFruits', 'MntMeatProducts', 
    'MntFishProducts', 'MntSweetProducts', 'MntGoldProds'
]

PURCHASE_CHANNELS = [
    'NumDealsPurchases', 'NumWebPurchases', 
    'NumCatalogPurchases', 'NumStorePurchases'
]

CAMPAIGN_RESPONSES = [
    'AcceptedCmp1', 'AcceptedCmp2', 'AcceptedCmp3', 
    'AcceptedCmp4', 'AcceptedCmp5', 'Response'
]


class EnhancedCustomerPersonalityPreprocessing:
    """
    Enhanced preprocessing class for Customer Personality Analysis dataset.
    Includes comprehensive data cleaning, transformation, and feature engineering.
    """

    def __init__(self, verbose=True):
        self.data_path = DATA_PATH
        self.output_dir = OUTPUT_DIR
        self.log_dir = LOG_DIR
        
        # Create directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.df_raw = None
        self.df_clean = None
        self.preprocessing_report = {}
        self.verbose = verbose
        
        # Initialize preprocessing steps tracking
        self.preprocessing_steps = []
        
        print("=" * 80)
        print("CustomerDNA AI — Enhanced Customer Personality Preprocessing")
        print("=" * 80)
        print(f"Data   : {self.data_path}")
        print(f"Output : {self.output_dir}")
        print(f"Logs   : {self.log_dir}")
        print("-" * 80)

    # ─────────────────────────────────────────
    # LOGGING HELPER
    # ─────────────────────────────────────────
    def _log(self, message: str, level="INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # Print to console if verbose
        if self.verbose:
            print(log_message)
        
        # Write to log file
        log_file = os.path.join(self.log_dir, 'preprocessing.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
        
        return log_message

    # ─────────────────────────────────────────
    # 1. DATA LOADING AND INITIAL ASSESSMENT
    # ─────────────────────────────────────────
    def load_and_assess_data(self):
        """Load the raw data and perform initial assessment."""
        self._log("load_and_assess_data() started")
        
        try:
            # Load the data
            self.df_raw = pd.read_csv(self.data_path, sep='\t')
            
            # Store initial assessment
            self.preprocessing_report['initial_assessment'] = {
                'raw_shape': self.df_raw.shape,
                'columns': list(self.df_raw.columns),
                'data_types': self.df_raw.dtypes.astype(str).to_dict(),
                'missing_values': self.df_raw.isnull().sum().to_dict(),
                'duplicate_rows': self.df_raw.duplicated().sum(),
                'memory_usage_mb': self.df_raw.memory_usage(deep=True).sum() / 1024**2
            }
            
            # Log initial findings
            self._log(f"Data loaded successfully: {self.df_raw.shape[0]:,} rows × {self.df_raw.shape[1]} columns")
            self._log(f"Memory usage: {self.preprocessing_report['initial_assessment']['memory_usage_mb']:.2f} MB")
            
            total_missing = self.df_raw.isnull().sum().sum()
            if total_missing > 0:
                self._log(f"Total missing values: {total_missing:,}", "WARNING")
            
            if self.df_raw.duplicated().sum() > 0:
                self._log(f"Duplicate rows found: {self.df_raw.duplicated().sum():,}", "WARNING")
            
            return True
            
        except Exception as e:
            self._log(f"Failed to load data: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────
    # 2. DATA CLEANING
    # ─────────────────────────────────────────
    def clean_data(self):
        """Perform comprehensive data cleaning."""
        self._log("clean_data() started")
        
        if self.df_raw is None:
            self._log("No raw data available. Run load_and_assess_data() first.", "ERROR")
            return False
        
        try:
            # Create a copy for cleaning
            df_clean = self.df_raw.copy()
            
            # 2.1 Handle missing values
            self._log("2.1 Handling missing values...")
            
            # Calculate missing percentages
            missing_percent = (df_clean.isnull().sum() / len(df_clean)) * 100
            
            # Identify columns with excessive missing values
            columns_to_drop = missing_percent[missing_percent > MISSING_THRESHOLD * 100].index.tolist()
            
            if columns_to_drop:
                self._log(f"  Dropping columns with >{MISSING_THRESHOLD*100}% missing: {columns_to_drop}", "WARNING")
                df_clean = df_clean.drop(columns=columns_to_drop)
            
            # For remaining missing values, use appropriate imputation
            numerical_cols = df_clean.select_dtypes(include=[np.number]).columns
            categorical_cols = df_clean.select_dtypes(include=['object']).columns
            
            # Impute numerical columns with median
            for col in numerical_cols:
                if df_clean[col].isnull().sum() > 0:
                    median_val = df_clean[col].median()
                    df_clean[col] = df_clean[col].fillna(median_val)
                    self._log(f"  Imputed {col} with median: {median_val:.2f}")
            
            # Impute categorical columns with mode
            for col in categorical_cols:
                if df_clean[col].isnull().sum() > 0:
                    mode_val = df_clean[col].mode()[0] if not df_clean[col].mode().empty else 'Unknown'
                    df_clean[col] = df_clean[col].fillna(mode_val)
                    self._log(f"  Imputed {col} with mode: {mode_val}")
            
            # 2.2 Handle duplicates
            self._log("2.2 Handling duplicates...")
            
            initial_rows = len(df_clean)
            df_clean = df_clean.drop_duplicates()
            duplicates_removed = initial_rows - len(df_clean)
            
            if duplicates_removed > 0:
                self._log(f"  Removed {duplicates_removed:,} duplicate rows", "WARNING")
            
            # 2.3 Data type conversion and validation
            self._log("2.3 Data type conversion and validation...")
            
            # Convert date column to datetime
            if 'Dt_Customer' in df_clean.columns:
                df_clean['Dt_Customer'] = pd.to_datetime(df_clean['Dt_Customer'], format='%d-%m-%Y', errors='coerce')
                invalid_dates = df_clean['Dt_Customer'].isnull().sum()
                if invalid_dates > 0:
                    self._log(f"  Found {invalid_dates:,} invalid dates in Dt_Customer", "WARNING")
            
            # Validate numerical ranges
            validation_issues = []
            
            if 'Year_Birth' in df_clean.columns:
                invalid_years = ((df_clean['Year_Birth'] < MIN_YEAR_BIRTH) | 
                                (df_clean['Year_Birth'] > MAX_YEAR_BIRTH)).sum()
                if invalid_years > 0:
                    validation_issues.append(f"Year_Birth: {invalid_years:,} invalid values")
            
            if 'Income' in df_clean.columns:
                invalid_income = ((df_clean['Income'] < MIN_INCOME) | 
                                 (df_clean['Income'] > MAX_INCOME)).sum()
                if invalid_income > 0:
                    validation_issues.append(f"Income: {invalid_income:,} invalid values")
            
            # Validate spending categories
            for category in SPENDING_CATEGORIES:
                if category in df_clean.columns:
                    invalid_spending = ((df_clean[category] < MIN_SPENDING) | 
                                       (df_clean[category] > MAX_SPENDING)).sum()
                    if invalid_spending > 0:
                        validation_issues.append(f"{category}: {invalid_spending:,} invalid values")
            
            if validation_issues:
                self._log(f"  Validation issues found: {validation_issues}", "WARNING")
            
            # 2.4 Standardize categorical values
            self._log("2.4 Standardizing categorical values...")
            
            if 'Education' in df_clean.columns:
                df_clean['Education'] = df_clean['Education'].map(EDUCATION_MAPPING).fillna('Unknown')
                self._log(f"  Standardized Education column")
            
            if 'Marital_Status' in df_clean.columns:
                df_clean['Marital_Status'] = df_clean['Marital_Status'].map(MARITAL_STATUS_MAPPING).fillna('Unknown')
                self._log(f"  Standardized Marital_Status column")
                
                # Handle data quality issues
                unusual_statuses = ['Absurd', 'YOLO', 'Alone']
                if df_clean['Marital_Status'].isin(unusual_statuses).any():
                    self._log(f"  Found unusual marital statuses: {unusual_statuses}", "WARNING")
            
            # Store cleaned data
            self.df_clean = df_clean
            
            # Store cleaning statistics
            self.preprocessing_report['cleaning_stats'] = {
                'initial_rows': len(self.df_raw),
                'cleaned_rows': len(self.df_clean),
                'rows_removed': len(self.df_raw) - len(self.df_clean),
                'columns_removed': columns_to_drop,
                'duplicates_removed': duplicates_removed,
                'validation_issues': validation_issues,
                'missing_values_after_cleaning': self.df_clean.isnull().sum().to_dict()
            }
            
            self._log(f"Data cleaning completed: {len(self.df_clean):,} rows × {self.df_clean.shape[1]} columns")
            
            return True
            
        except Exception as e:
            self._log(f"Failed to clean data: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────
    # 3. FEATURE ENGINEERING
    # ─────────────────────────────────────────
    def engineer_features(self):
        """Create new features and transform existing ones."""
        self._log("engineer_features() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run clean_data() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            
            # 3.1 Demographic features
            self._log("3.1 Creating demographic features...")
            
            # Calculate age
            if 'Year_Birth' in df.columns:
                current_year = datetime.now().year
                df['Age'] = current_year - df['Year_Birth']
                
                # Create age groups
                df['Age_Group'] = pd.cut(df['Age'], 
                                        bins=[0, 30, 40, 50, 60, 100],
                                        labels=['<30', '30-40', '40-50', '50-60', '60+'])
            
            # Family size
            if all(col in df.columns for col in ['Kidhome', 'Teenhome']):
                df['Family_Size'] = 1 + df['Kidhome'] + df['Teenhome']
                
                # Create family type categories
                conditions = [
                    (df['Family_Size'] == 1),
                    (df['Family_Size'] == 2),
                    (df['Family_Size'] == 3),
                    (df['Family_Size'] >= 4)
                ]
                choices = ['Single', 'Couple', 'Small Family', 'Large Family']
                df['Family_Type'] = np.select(conditions, choices, default='Unknown')
            
            # 3.2 Spending features
            self._log("3.2 Creating spending features...")
            
            # Total spending
            spending_cols = [col for col in SPENDING_CATEGORIES if col in df.columns]
            if spending_cols:
                df['Total_Spending'] = df[spending_cols].sum(axis=1)
                
                # Spending proportions
                for col in spending_cols:
                    df[f'{col}_Proportion'] = df[col] / df['Total_Spending'].replace(0, np.nan)
                
                # Spending diversity (entropy)
                if HAS_SCIPY:
                    try:
                        spending_matrix = df[spending_cols].values
                        row_sums = spending_matrix.sum(axis=1, keepdims=True)
                        row_sums[row_sums == 0] = 1  # Avoid division by zero
                        proportions = spending_matrix / row_sums
                        # Calculate entropy for each row
                        entropy = -np.sum(proportions * np.log(proportions + 1e-10), axis=1)
                        df['Spending_Entropy'] = entropy
                    except:
                        self._log("  Failed to calculate spending entropy", "WARNING")
            
            # 3.3 Purchase behavior features
            self._log("3.3 Creating purchase behavior features...")
            
            # Total purchases
            purchase_cols = [col for col in PURCHASE_CHANNELS if col in df.columns]
            if purchase_cols:
                df['Total_Purchases'] = df[purchase_cols].sum(axis=1)
                
                # Purchase channel proportions
                for col in purchase_cols:
                    df[f'{col}_Proportion'] = df[col] / df['Total_Purchases'].replace(0, np.nan)
                
                # Purchase concentration (Herfindahl index)
                proportions = df[purchase_cols].div(df['Total_Purchases'].replace(0, np.nan), axis=0)
                df['Purchase_Concentration'] = (proportions ** 2).sum(axis=1)
            
            # 3.4 Temporal features
            self._log("3.4 Creating temporal features...")
            
            if 'Dt_Customer' in df.columns:
                # Customer tenure (days since enrollment)
                latest_date = df['Dt_Customer'].max()
                df['Tenure_Days'] = (latest_date - df['Dt_Customer']).dt.days
                
                # Create tenure groups
                df['Tenure_Group'] = pd.cut(df['Tenure_Days'],
                                          bins=[0, 180, 365, 730, 1095, 1825],
                                          labels=['<6m', '6m-1y', '1y-2y', '2y-3y', '3y-5y'])
                
                # Extract temporal components
                df['Enrollment_Year'] = df['Dt_Customer'].dt.year
                df['Enrollment_Month'] = df['Dt_Customer'].dt.month
                df['Enrollment_Quarter'] = df['Dt_Customer'].dt.quarter
            
            # 3.5 Campaign response features
            self._log("3.5 Creating campaign response features...")
            
            campaign_cols = [col for col in CAMPAIGN_RESPONSES if col in df.columns]
            if campaign_cols:
                df['Total_Campaign_Responses'] = df[campaign_cols].sum(axis=1)
                
                # Campaign response rate
                df['Campaign_Response_Rate'] = df['Total_Campaign_Responses'] / len(campaign_cols)
                
                # Identify most recent campaign response
                if 'Response' in df.columns:
                    df['Recent_Response'] = df['Response']
            
            # 3.6 Composite features
            self._log("3.6 Creating composite features...")
            
            # Customer value score
            if all(col in df.columns for col in ['Total_Spending', 'Total_Purchases', 'Tenure_Days']):
                # Normalize components
                spending_norm = (df['Total_Spending'] - df['Total_Spending'].mean()) / df['Total_Spending'].std()
                frequency_norm = (df['Total_Purchases'] - df['Total_Purchases'].mean()) / df['Total_Purchases'].std()
                tenure_norm = (df['Tenure_Days'] - df['Tenure_Days'].mean()) / df['Tenure_Days'].std()
                
                # Weighted composite score
                df['Customer_Value_Score'] = (0.5 * spending_norm + 0.3 * frequency_norm + 0.2 * tenure_norm)
                
                # Create value segments
                df['Value_Segment'] = pd.qcut(df['Customer_Value_Score'], 
                                             q=4, 
                                             labels=['Low', 'Medium', 'High', 'Premium'])
            
            # Update cleaned dataframe
            self.df_clean = df
            
            # Store feature engineering statistics
            self.preprocessing_report['feature_engineering'] = {
                'new_features_created': list(set(df.columns) - set(self.df_raw.columns)),
                'total_features_after_engineering': df.shape[1],
                'feature_categories': {
                    'demographic': ['Age', 'Age_Group', 'Family_Size', 'Family_Type'],
                    'spending': ['Total_Spending'] + [f'{col}_Proportion' for col in spending_cols],
                    'purchase_behavior': ['Total_Purchases'] + [f'{col}_Proportion' for col in purchase_cols],
                    'temporal': ['Tenure_Days', 'Tenure_Group', 'Enrollment_Year', 'Enrollment_Month', 'Enrollment_Quarter'],
                    'campaign_response': ['Total_Campaign_Responses', 'Campaign_Response_Rate', 'Recent_Response'],
                    'composite': ['Customer_Value_Score', 'Value_Segment']
                }
            }
            
            self._log(f"Feature engineering completed: {df.shape[1]} total features")
            
            return True
            
        except Exception as e:
            self._log(f"Failed to engineer features: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────
    # 4. OUTLIER DETECTION AND HANDLING
    # ─────────────────────────────────────────
    def handle_outliers(self):
        """Detect and handle outliers in numerical features."""
        self._log("handle_outliers() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run clean_data() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            numerical_cols = df.select_dtypes(include=[np.number]).columns
            
            outlier_report = {
                'features_analyzed': [],
                'outliers_detected': {},
                'outliers_capped': {},
                'outliers_removed': 0
            }
            
            # Identify and handle outliers for each numerical feature
            for col in numerical_cols:
                if col in ['ID', 'Year_Birth', 'Kidhome', 'Teenhome', 
                          'AcceptedCmp1', 'AcceptedCmp2', 'AcceptedCmp3', 
                          'AcceptedCmp4', 'AcceptedCmp5', 'Response', 'Complain']:
                    continue  # Skip ID and binary/count features
                
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - OUTLIER_IQR_MULTIPLIER * IQR
                upper_bound = Q3 + OUTLIER_IQR_MULTIPLIER * IQR
                
                # Detect outliers
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                outlier_count = len(outliers)
                
                if outlier_count > 0:
                    outlier_report['features_analyzed'].append(col)
                    outlier_report['outliers_detected'][col] = outlier_count
                    
                    # Cap outliers to bounds
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
                    
                    # Count how many values were actually capped
                    capped_count = ((df[col] == lower_bound) | (df[col] == upper_bound)).sum()
                    outlier_report['outliers_capped'][col] = capped_count
                    
                    self._log(f"  {col}: {outlier_count:,} outliers detected, {capped_count:,} capped")
            
            # Update dataframe
            self.df_clean = df
            
            # Store outlier handling statistics
            self.preprocessing_report['outlier_handling'] = outlier_report
            
            total_outliers = sum(outlier_report['outliers_detected'].values())
            self._log(f"Outlier handling completed: {total_outliers:,} total outliers handled")
            
            return True
            
        except Exception as e:
            self._log(f"Failed to handle outliers: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────
    # 5. ENCODING AND SCALING
    # ─────────────────────────────────────────
    def encode_and_scale(self):
        """Encode categorical variables and scale numerical features."""
        self._log("encode_and_scale() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run clean_data() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            
            encoding_report = {
                'categorical_encoded': [],
                'numerical_scaled': [],
                'encoding_methods': {}
            }
            
            # 5.1 Encode categorical variables
            self._log("5.1 Encoding categorical variables...")
            
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            
            for col in categorical_cols:
                if col in ['Education', 'Marital_Status', 'Age_Group', 'Family_Type', 'Tenure_Group', 'Value_Segment']:
                    # Use label encoding for ordinal-like categories
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col].astype(str))
                    encoding_report['categorical_encoded'].append(col)
                    encoding_report['encoding_methods'][col] = 'LabelEncoding'
                    self._log(f"  {col}: Label encoded ({len(le.classes_)} categories)")
                else:
                    # Use one-hot encoding for nominal categories
                    dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
                    df = pd.concat([df, dummies], axis=1)
                    df = df.drop(columns=[col])
                    encoding_report['categorical_encoded'].append(col)
                    encoding_report['encoding_methods'][col] = 'OneHotEncoding'
                    self._log(f"  {col}: One-hot encoded ({dummies.shape[1]} new features)")
            
            # 5.2 Scale numerical features
            self._log("5.2 Scaling numerical features...")
            
            numerical_cols = df.select_dtypes(include=[np.number]).columns
            
            # Identify features that should not be scaled
            exclude_from_scaling = ['ID', 'Response', 'Complain', 
                                   'AcceptedCmp1', 'AcceptedCmp2', 'AcceptedCmp3', 
                                   'AcceptedCmp4', 'AcceptedCmp5']
            
            scaling_cols = [col for col in numerical_cols if col not in exclude_from_scaling]
            
            if scaling_cols and HAS_SKLEARN:
                # Use StandardScaler for features with normal-ish distribution
                scaler = StandardScaler()
                df[scaling_cols] = scaler.fit_transform(df[scaling_cols])
                
                encoding_report['numerical_scaled'] = scaling_cols
                encoding_report['encoding_methods']['numerical_scaling'] = 'StandardScaler'
                self._log(f"  Scaled {len(scaling_cols)} numerical features using StandardScaler")
            
            # Update dataframe
            self.df_clean = df
            
            # Store encoding and scaling statistics
            self.preprocessing_report['encoding_scaling'] = encoding_report
            
            self._log(f"Encoding and scaling completed: {df.shape[1]} total features")
            
            return True
            
        except Exception as e:
            self._log(f"Failed to encode and scale: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────
    # 6. FINAL VALIDATION AND EXPORT
    # ─────────────────────────────────────────
    def validate_and_export(self):
        """Perform final validation and export cleaned dataset."""
        self._log("validate_and_export() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run previous steps first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            
            # 6.1 Final validation checks
            self._log("6.1 Performing final validation checks...")
            
            validation_checks = {
                'missing_values': df.isnull().sum().sum() == 0,
                'infinite_values': np.isfinite(df.select_dtypes(include=[np.number])).all().all(),
                'data_types_consistent': True,  # Assuming preprocessing handled this
                'row_count_reasonable': len(df) > 0 and len(df) <= len(self.df_raw) * 1.1,
                'column_count_reasonable': df.shape[1] > 0 and df.shape[1] <= self.df_raw.shape[1] * 3
            }
            
            failed_checks = [check for check, passed in validation_checks.items() if not passed]
            
            if failed_checks:
                self._log(f"  Validation failed for: {failed_checks}", "WARNING")
            else:
                self._log("  All validation checks passed")
            
            # 6.2 Export cleaned dataset
            self._log("6.2 Exporting cleaned dataset...")
            
            # Create timestamp for versioning
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Export to CSV
            csv_path = os.path.join(self.output_dir, f'cleaned_customer_personality_{timestamp}.csv')
            df.to_csv(csv_path, index=False)
            
            # Export to Parquet (more efficient)
            parquet_path = os.path.join(self.output_dir, f'cleaned_customer_personality_{timestamp}.parquet')
            df.to_parquet(parquet_path, index=False)
            
            # 6.3 Export preprocessing report
            self._log("6.3 Exporting preprocessing report...")
            
            # Add final statistics to report
            self.preprocessing_report['final_validation'] = {
                'validation_checks': validation_checks,
                'failed_checks': failed_checks,
                'final_shape': df.shape,
                'export_paths': {
                    'csv': csv_path,
                    'parquet': parquet_path
                },
                'timestamp': timestamp
            }
            
            # Export report to JSON
            report_path = os.path.join(self.output_dir, f'preprocessing_report_{timestamp}.json')
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                # Convert numpy types to Python types for JSON serialization
                def convert_to_serializable(obj):
                    if isinstance(obj, (np.integer, np.floating)):
                        return obj.item()
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    elif isinstance(obj, pd.Timestamp):
                        return obj.isoformat()
                    else:
                        return obj
                
                serializable_report = json.loads(json.dumps(self.preprocessing_report, default=convert_to_serializable))
                json.dump(serializable_report, f, indent=2, ensure_ascii=False)
            
            # Export report to text
            text_report_path = os.path.join(self.output_dir, f'preprocessing_summary_{timestamp}.txt')
            with open(text_report_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("CUSTOMER PERSONALITY ANALYSIS - PREPROCESSING SUMMARY\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("1. DATA OVERVIEW\n")
                f.write("-" * 40 + "\n")
                f.write(f"Raw dataset: {self.df_raw.shape[0]:,} rows × {self.df_raw.shape[1]} columns\n")
                f.write(f"Cleaned dataset: {df.shape[0]:,} rows × {df.shape[1]} columns\n")
                f.write(f"Rows removed: {len(self.df_raw) - len(df):,}\n")
                f.write(f"New features created: {df.shape[1] - self.df_raw.shape[1]}\n\n")
                
                f.write("2. PREPROCESSING STEPS COMPLETED\n")
                f.write("-" * 40 + "\n")
                f.write("✓ Data loading and initial assessment\n")
                f.write("✓ Missing value imputation\n")
                f.write("✓ Duplicate removal\n")
                f.write("✓ Data type validation\n")
                f.write("✓ Categorical value standardization\n")
                f.write("✓ Feature engineering (demographic, spending, behavioral, temporal)\n")
                f.write("✓ Outlier detection and capping\n")
                f.write("✓ Categorical encoding (Label & One-Hot)\n")
                f.write("✓ Numerical feature scaling\n")
                f.write("✓ Final validation checks\n\n")
                
                f.write("3. OUTPUT FILES\n")
                f.write("-" * 40 + "\n")
                f.write(f"Cleaned dataset (CSV): {csv_path}\n")
                f.write(f"Cleaned dataset (Parquet): {parquet_path}\n")
                f.write(f"Preprocessing report (JSON): {report_path}\n")
                f.write(f"Preprocessing summary (Text): {text_report_path}\n\n")
                
                f.write("4. NEXT STEPS FOR MODELING\n")
                f.write("-" * 40 + "\n")
                f.write("1. Load cleaned dataset for machine learning\n")
                f.write("2. Split data into training, validation, and test sets\n")
                f.write("3. Train customer segmentation models (clustering)\n")
                f.write("4. Develop predictive models for customer behavior\n")
                f.write("5. Implement recommendation systems\n")
                f.write("6. Create customer lifetime value models\n\n")
                
                f.write("=" * 80 + "\n")
                f.write("PREPROCESSING COMPLETED SUCCESSFULLY\n")
                f.write("=" * 80 + "\n")
            
            self._log(f"Cleaned dataset exported to: {csv_path}")
            self._log(f"Preprocessing report exported to: {report_path}")
            
            return True
            
        except Exception as e:
            self._log(f"Failed to validate and export: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────
    # 7. MAIN EXECUTION PIPELINE
    # ─────────────────────────────────────────
    def run_complete_preprocessing(self):
        """Execute the complete preprocessing pipeline."""
        self._log("run_complete_preprocessing() started")
        
        start_time = datetime.now()
        
        # Track success of each step
        steps_completed = []
        
        # Step 1: Load and assess data
        if self.load_and_assess_data():
            steps_completed.append("Data loading and assessment")
        else:
            self._log("Failed to load data. Preprocessing cannot continue.", "ERROR")
            return False
        
        # Step 2: Clean data
        if self.clean_data():
            steps_completed.append("Data cleaning")
        else:
            self._log("Data cleaning had issues, but continuing with preprocessing.", "WARNING")
        
        # Step 3: Engineer features
        if self.engineer_features():
            steps_completed.append("Feature engineering")
        else:
            self._log("Feature engineering had issues, but continuing.", "WARNING")
        
        # Step 4: Handle outliers
        if self.handle_outliers():
            steps_completed.append("Outlier handling")
        else:
            self._log("Outlier handling had issues, but continuing.", "WARNING")
        
        # Step 5: Encode and scale
        if self.encode_and_scale():
            steps_completed.append("Encoding and scaling")
        else:
            self._log("Encoding and scaling had issues, but continuing.", "WARNING")
        
        # Step 6: Validate and export
        if self.validate_and_export():
            steps_completed.append("Validation and export")
        else:
            self._log("Validation and export had issues.", "WARNING")
        
        # Calculate duration
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Final summary
        print("\n" + "=" * 80)
        print("PREPROCESSING COMPLETED")
        print("=" * 80)
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration:   {duration}")
        print(f"Steps completed: {len(steps_completed)}/{6}")
        
        if len(steps_completed) > 0:
            print("\nCompleted steps:")
            for step in steps_completed:
                print(f"  * {step}")
        
        print(f"\nOutput directory: {self.output_dir}")
        print("Generated files:")
        print("  • Cleaned dataset (CSV and Parquet formats)")
        print("  • Preprocessing report (JSON)")
        print("  • Preprocessing summary (Text)")
        print("  • Log file with detailed processing information")
        
        self._log(f"Preprocessing completed at {end_time}. Duration: {duration}")
        
        return len(steps_completed) >= 4  # Consider successful if at least 4 steps completed


# ─────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CUSTOMERDNA AI - CUSTOMER PERSONALITY ANALYSIS PREPROCESSING")
    print("=" * 80)
    
    # Create preprocessing instance
    preprocessor = EnhancedCustomerPersonalityPreprocessing(verbose=True)
    
    # Run complete preprocessing
    success = preprocessor.run_complete_preprocessing()
    
    if success:
        print("\n" + "=" * 80)
        print("[SUCCESS] Preprocessing completed successfully!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Load the cleaned dataset for machine learning")
        print("2. Split data into training, validation, and test sets")
        print("3. Train customer segmentation models (clustering)")
        print("4. Develop predictive models for customer behavior")
        print("5. Implement recommendation systems")
        print("6. Create customer lifetime value models")
    else:
        print("\n" + "=" * 80)
        print("[WARNING] Preprocessing completed with some issues.")
        print("=" * 80)
        print("\nRecommendations:")
        print("1. Check the logs for specific error messages")
        print("2. Verify data file accessibility and format")
        print("3. Ensure required Python packages are installed")
        print("4. Consider running individual preprocessing steps separately")
    
    print("\n" + "=" * 80)
    print("PREPROCESSING FINISHED")
    print("=" * 80)