"""
CustomerDNA AI - PFE Project
Dataset : E-commerce Customer Churn (E-commerce_customer_churn.xlsx)
Script  : Enhanced E-commerce Churn Preprocessing — Comprehensive Pipeline
Author  : PFE Student
Description: Comprehensive preprocessing pipeline for e-commerce customer churn dataset
             including data cleaning, feature engineering, outlier handling, encoding, and scaling
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
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
    from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler, MinMaxScaler
    from sklearn.impute import SimpleImputer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[WARNING] scikit-learn not available. Some advanced preprocessing techniques will be skipped.")

# ─────────────────────────────────────────────
# PATHS — adjust only these lines
# ─────────────────────────────────────────────
DATA_PATH = r"d:\github\Master_PFE_Project\CustomerDNA AI\datasets\client_1\E-commerce_customer_churn\E-commerce_customer_churn.xlsx"
OUTPUT_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\client_1\E-commerce_customer_churn_Preprocessing\cleaned_dataset"
LOG_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\client_1\E-commerce_customer_churn_Preprocessing\logs"
CONFIG_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\client_1\E-commerce_customer_churn_Preprocessing\config"

# ─────────────────────────────────────────────
# CONSTANTS — data preprocessing rules
# ─────────────────────────────────────────────
# Missing value handling thresholds
MISSING_THRESHOLD_DROP = 20.0  # Drop columns with >20% missing
MISSING_THRESHOLD_IMPUTE = 5.0  # Use advanced imputation for 5-20% missing

# Outlier detection thresholds (based on IQR method)
OUTLIER_IQR_MULTIPLIER = 1.5

# Categorical value mappings for consistency
GENDER_MAPPING = {"Male": "Male", "Female": "Female", "M": "Male", "F": "Female"}
MARITAL_STATUS_MAPPING = {
    "Married": "Marired", "Single": "Single", "Divorced": "Divorced",
    "M": "Married", "S": "Single", "D": "Divorced"
}
PREFERRED_LOGIN_DEVICE_MAPPING = {
    "Phone": "Phone", "Mobile Phone": "Mobile Phone", "Computer": "Computer",
    "phone": "Phone", "mobile": "Mobile Phone", "computer": "Computer"
}
PREFERRED_PAYMENT_MODE_MAPPING = {
    "COD": "COD", "Credit Card": "Credit Card", "Debit Card": "Debit Card",
    "E wallet": "E wallet", "UPI": "UPI",
    "cod": "COD", "credit": "Credit Card", "debit": "Debit Card",
    "ewallet": "E wallet", "upi": "UPI"
}
ORDER_CAT_HABIT_MAPPING = {
    "Laptop & Accessory": "Laptop & Accessory", "Mobile": "Mobile",
    "Mobile Phone": "Mobile Phone", "Fashion": "Fashion",
    "Grocery": "Grocery", "Others": "Others"
}

# Business rules for validation
BUSINESS_RULES = {
    'Tenure': {'min': 0, 'max': 50, 'description': 'Customer tenure in months'},
    'OrderCount': {'min': 0, 'max': 50, 'description': 'Number of orders placed'},
    'CashbackAmount': {'min': 0, 'max': 500, 'description': 'Cashback amount received'},
    'DaySinceLastOrder': {'min': 0, 'max': 365, 'description': 'Days since last order'},
    'SatisfactionScore': {'min': 1, 'max': 5, 'description': 'Customer satisfaction score'},
    'NumberOfDeviceRegistered': {'min': 1, 'max': 10, 'description': 'Number of devices registered'},
    'PreferedOrderCat': {'valid_values': ['Laptop & Accessory', 'Mobile', 'Mobile Phone', 'Fashion', 'Grocery', 'Others'], 
                        'description': 'Preferred order category'},
    'Complain': {'valid_values': [0, 1], 'description': 'Whether customer complained'}
}


class EnhancedEcommerceChurnPreprocessing:
    """
    Enhanced preprocessing class for E-commerce Customer Churn dataset.
    Includes comprehensive data cleaning, transformation, and feature engineering.
    """

    def __init__(self, verbose=True):
        self.data_path = DATA_PATH
        self.output_dir = OUTPUT_DIR
        self.log_dir = LOG_DIR
        self.config_dir = CONFIG_DIR
        
        # Create directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.df_raw = None
        self.df_clean = None
        self.df_processed = None
        self.preprocessing_report = {}
        self.verbose = verbose
        
        # Initialize encoders and scalers
        self.label_encoders = {}
        self.onehot_encoders = {}
        self.scaler = None
        
        print("=" * 80)
        print("CUSTOMERDNA AI - E-COMMERCE CUSTOMER CHURN PREPROCESSING")
        print("=" * 80)
        print(f"Data   : {self.data_path}")
        print(f"Output : {self.output_dir}")
        print(f"Logs   : {self.log_dir}")
        print("-" * 80)

    # ─────────────────────────────────────────
    # LOGGING HELPER
    # ─────────────────────────────────────────
    def _log(self, message: str, level: str = "INFO"):
        """Print a timestamped log entry."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        
        if self.verbose:
            print(log_message)
        
        # Save to log file
        log_file = os.path.join(self.log_dir, f"preprocessing_log_{datetime.now().strftime('%Y%m%d')}.txt")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    # ─────────────────────────────────────────
    # 1. LOAD DATA
    # ─────────────────────────────────────────
    def load_data(self):
        """Load the raw Excel data and perform initial inspection."""
        self._log("load_data() started")
        
        try:
            # Read the Excel file
            self.df_raw = pd.read_excel(self.data_path, sheet_name='E Comm')
            self._log(f"Successfully loaded {len(self.df_raw):,} rows and {len(self.df_raw.columns)} columns")
            
            # Basic dataset info
            self.preprocessing_report['dataset_info'] = {
                'original_shape': self.df_raw.shape,
                'columns': self.df_raw.columns.tolist(),
                'data_types': self.df_raw.dtypes.astype(str).to_dict(),
                'memory_usage_mb': self.df_raw.memory_usage(deep=True).sum() / 1024 / 1024
            }
            
            # Display basic info
            if self.verbose:
                print(f"\nDataset Overview:")
                print(f"  - Shape: {self.df_raw.shape}")
                print(f"  - Memory: {self.preprocessing_report['dataset_info']['memory_usage_mb']:.2f} MB")
                print(f"  - Columns: {', '.join(self.df_raw.columns.tolist())}")
                
                # Data types summary
                dtype_counts = self.df_raw.dtypes.value_counts()
                print(f"\n  Data Types:")
                for dtype, count in dtype_counts.items():
                    print(f"    - {dtype}: {count} columns")
                
                # Target variable info
                if 'Churn' in self.df_raw.columns:
                    churn_dist = self.df_raw['Churn'].value_counts()
                    churn_rate = (churn_dist[1] / len(self.df_raw)) * 100 if 1 in churn_dist else 0
                    print(f"\n  Target Variable (Churn):")
                    print(f"    - Retained (0): {churn_dist.get(0, 0):,} customers")
                    print(f"    - Churned (1): {churn_dist.get(1, 0):,} customers")
                    print(f"    - Churn Rate: {churn_rate:.1f}%")
            
            self._log("load_data() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to load data: {e}", "ERROR")
            return False
    
    # ─────────────────────────────────────────
    # 2. CLEAN DATA
    # ─────────────────────────────────────────
    def clean_data(self):
        """Clean the dataset: handle missing values, duplicates, and data type issues."""
        self._log("clean_data() started")
        
        if self.df_raw is None:
            self._log("No raw data available. Run load_data() first.", "ERROR")
            return False
        
        # Create a copy for cleaning
        self.df_clean = self.df_raw.copy()
        
        # 2.1 Handle missing values
        self._log("2.1 Handling missing values...")
        missing = self.df_clean.isnull().sum()
        missing_cols = missing[missing > 0].index.tolist()
        
        missing_report = {}
        for col in missing_cols:
            missing_count = missing[col]
            missing_pct = (missing_count / len(self.df_clean)) * 100
            
            if missing_pct > MISSING_THRESHOLD_DROP:
                # Drop columns with >20% missing values
                self._log(f"Dropping column '{col}' ({missing_pct:.1f}% missing)", "WARNING")
                self.df_clean.drop(columns=[col], inplace=True)
                missing_report[col] = {'action': 'dropped', 'missing_pct': missing_pct}
                
            elif missing_pct > MISSING_THRESHOLD_IMPUTE:
                # For 5-20% missing, use advanced imputation
                if self.df_clean[col].dtype in ['int64', 'float64']:
                    impute_val = self.df_clean[col].median()
                    method = "median"
                else:
                    impute_val = self.df_clean[col].mode()[0] if not self.df_clean[col].mode().empty else "Unknown"
                    method = "mode"
                self._log(f"Imputing '{col}' with {method} ({missing_pct:.1f}% missing)")
                self.df_clean[col].fillna(impute_val, inplace=True)
                missing_report[col] = {'action': 'imputed', 'method': method, 'missing_pct': missing_pct}
                
            else:
                # For <5% missing, use simple imputation
                if self.df_clean[col].dtype in ['int64', 'float64']:
                    impute_val = self.df_clean[col].mean()
                    method = "mean"
                else:
                    impute_val = self.df_clean[col].mode()[0] if not self.df_clean[col].mode().empty else "Unknown"
                    method = "mode"
                self._log(f"Imputing '{col}' with {method} ({missing_pct:.1f}% missing)")
                self.df_clean[col].fillna(impute_val, inplace=True)
                missing_report[col] = {'action': 'imputed', 'method': method, 'missing_pct': missing_pct}
        
        # 2.2 Handle categorical data consistency
        self._log("2.2 Standardizing categorical values...")
        
        categorical_standardization = {}
        
        # Gender standardization
        if 'Gender' in self.df_clean.columns:
            original_values = self.df_clean['Gender'].unique().tolist()
            self.df_clean['Gender'] = self.df_clean['Gender'].map(GENDER_MAPPING).fillna(self.df_clean['Gender'])
            standardized_values = self.df_clean['Gender'].unique().tolist()
            categorical_standardization['Gender'] = {
                'original': original_values,
                'standardized': standardized_values
            }
            self._log(f"Standardized 'Gender' values")
        
        # Marital status standardization
        if 'MaritalStatus' in self.df_clean.columns:
            original_values = self.df_clean['MaritalStatus'].unique().tolist()
            self.df_clean['MaritalStatus'] = self.df_clean['MaritalStatus'].map(MARITAL_STATUS_MAPPING).fillna(self.df_clean['MaritalStatus'])
            standardized_values = self.df_clean['MaritalStatus'].unique().tolist()
            categorical_standardization['MaritalStatus'] = {
                'original': original_values,
                'standardized': standardized_values
            }
            self._log(f"Standardized 'MaritalStatus' values")
        
        # Preferred login device standardization
        if 'PreferedLoginDevice' in self.df_clean.columns:
            original_values = self.df_clean['PreferedLoginDevice'].unique().tolist()
            self.df_clean['PreferedLoginDevice'] = self.df_clean['PreferedLoginDevice'].map(PREFERRED_LOGIN_DEVICE_MAPPING).fillna(self.df_clean['PreferedLoginDevice'])
            standardized_values = self.df_clean['PreferedLoginDevice'].unique().tolist()
            categorical_standardization['PreferedLoginDevice'] = {
                'original': original_values,
                'standardized': standardized_values
            }
            self._log(f"Standardized 'PreferedLoginDevice' values")
        
        # Preferred payment mode standardization
        if 'PreferedPaymentMode' in self.df_clean.columns:
            original_values = self.df_clean['PreferedPaymentMode'].unique().tolist()
            self.df_clean['PreferedPaymentMode'] = self.df_clean['PreferedPaymentMode'].map(PREFERRED_PAYMENT_MODE_MAPPING).fillna(self.df_clean['PreferedPaymentMode'])
            standardized_values = self.df_clean['PreferedPaymentMode'].unique().tolist()
            categorical_standardization['PreferedPaymentMode'] = {
                'original': original_values,
                'standardized': standardized_values
            }
            self._log(f"Standardized 'PreferedPaymentMode' values")
        
        # Order category habit standardization
        if 'PreferedOrderCat' in self.df_clean.columns:
            original_values = self.df_clean['PreferedOrderCat'].unique().tolist()
            self.df_clean['PreferedOrderCat'] = self.df_clean['PreferedOrderCat'].map(ORDER_CAT_HABIT_MAPPING).fillna(self.df_clean['PreferedOrderCat'])
            standardized_values = self.df_clean['PreferedOrderCat'].unique().tolist()
            categorical_standardization['PreferedOrderCat'] = {
                'original': original_values,
                'standardized': standardized_values
            }
            self._log(f"Standardized 'PreferedOrderCat' values")
        
        # 2.3 Remove duplicate CustomerIDs
        self._log("2.3 Checking for duplicates...")
        duplicate_customers = self.df_clean['CustomerID'].duplicated().sum()
        if duplicate_customers > 0:
            self._log(f"Found {duplicate_customers} duplicate CustomerIDs", "WARNING")
            self.df_clean = self.df_clean.drop_duplicates(subset=['CustomerID'], keep='first')
            self._log(f"Removed duplicate CustomerIDs")
        else:
            self._log(f"No duplicate CustomerIDs found")
        
        # 2.4 Data type validation and conversion
        self._log("2.4 Validating data types...")
        
        # Ensure CustomerID is string
        if 'CustomerID' in self.df_clean.columns:
            self.df_clean['CustomerID'] = self.df_clean['CustomerID'].astype(str)
        
        # Ensure Churn is integer (0/1)
        if 'Churn' in self.df_clean.columns:
            self.df_clean['Churn'] = self.df_clean['Churn'].astype(int)
        
        # Ensure Complain is integer (0/1)
        if 'Complain' in self.df_clean.columns:
            self.df_clean['Complain'] = self.df_clean['Complain'].astype(int)
        
        # Update preprocessing report
        self.preprocessing_report['cleaning'] = {
            'missing_values': missing_report,
            'categorical_standardization': categorical_standardization,
            'duplicates_removed': duplicate_customers,
            'cleaned_shape': self.df_clean.shape,
            'columns_removed': len(self.df_raw.columns) - len(self.df_clean.columns)
        }
        
        self._log(f"Cleaning completed: {self.df_clean.shape[0]:,} rows, {self.df_clean.shape[1]:,} columns")
        self._log("clean_data() completed")
        return True
    
    # ─────────────────────────────────────────
    # 3. ENGINEER FEATURES
    # ─────────────────────────────────────────
    def engineer_features(self):
        """Create new features and transform existing ones."""
        self._log("engineer_features() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run clean_data() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            feature_engineering_report = {'new_features': [], 'transformed_features': []}
            
            # 3.1 Behavioral features
            self._log("3.1 Creating behavioral features...")
            
            # Customer activity score (combination of order count and tenure)
            if 'OrderCount' in df.columns and 'Tenure' in df.columns:
                df['Activity_Score'] = df['OrderCount'] / (df['Tenure'] + 1)  # +1 to avoid division by zero
                feature_engineering_report['new_features'].append('Activity_Score')
                self._log(f"Created 'Activity_Score' feature")
            
            # Recency score (inverse of days since last order)
            if 'DaySinceLastOrder' in df.columns:
                df['Recency_Score'] = 1 / (df['DaySinceLastOrder'] + 1)  # +1 to avoid division by zero
                feature_engineering_report['new_features'].append('Recency_Score')
                self._log(f"Created 'Recency_Score' feature")
            
            # Cashback efficiency (cashback per order)
            if 'CashbackAmount' in df.columns and 'OrderCount' in df.columns:
                df['Cashback_Per_Order'] = df['CashbackAmount'] / (df['OrderCount'] + 1)
                feature_engineering_report['new_features'].append('Cashback_Per_Order')
                self._log(f"Created 'Cashback_Per_Order' feature")
            
            # 3.2 Transactional features
            self._log("3.2 Creating transactional features...")
            
            # Order frequency (orders per month of tenure)
            if 'OrderCount' in df.columns and 'Tenure' in df.columns:
                df['Order_Frequency'] = df['OrderCount'] / (df['Tenure'] / 12 + 0.1)  # Convert tenure to years
                feature_engineering_report['new_features'].append('Order_Frequency')
                self._log(f"Created 'Order_Frequency' feature")
            
            # Discount utilization (coupons used vs order count)
            if 'CouponUsed' in df.columns and 'OrderCount' in df.columns:
                df['Discount_Utilization'] = df['CouponUsed'] / (df['OrderCount'] + 1)
                feature_engineering_report['new_features'].append('Discount_Utilization')
                self._log(f"Created 'Discount_Utilization' feature")
            
            # 3.3 Demographic composite features
            self._log("3.3 Creating demographic composite features...")
            
            # Create age groups from tenure (assuming tenure in months)
            if 'Tenure' in df.columns:
                df['Tenure_Group'] = pd.cut(df['Tenure'], 
                                          bins=[0, 6, 12, 24, 36, 100],
                                          labels=['<6m', '6-12m', '1-2y', '2-3y', '3y+'])
                feature_engineering_report['new_features'].append('Tenure_Group')
                self._log(f"Created 'Tenure_Group' feature")
            
            # 3.4 Risk assessment features
            self._log("3.4 Creating risk assessment features...")
            
            # Complaint risk score (combines complain with satisfaction)
            if 'Complain' in df.columns and 'SatisfactionScore' in df.columns:
                df['Complaint_Risk_Score'] = df['Complain'] * (6 - df['SatisfactionScore'])  # Higher score = higher risk
                feature_engineering_report['new_features'].append('Complaint_Risk_Score')
                self._log(f"Created 'Complaint_Risk_Score' feature")
            
            # Device diversity risk (more devices = higher risk?)
            if 'NumberOfDeviceRegistered' in df.columns:
                df['Device_Diversity_Risk'] = pd.cut(df['NumberOfDeviceRegistered'],
                                                   bins=[0, 1, 2, 3, 10],
                                                   labels=['Low', 'Medium', 'High', 'Very High'])
                feature_engineering_report['new_features'].append('Device_Diversity_Risk')
                self._log(f"Created 'Device_Diversity_Risk' feature")
            
            # 3.5 Interaction features
            self._log("3.5 Creating interaction features...")
            
            # Tenure × Satisfaction interaction
            if 'Tenure' in df.columns and 'SatisfactionScore' in df.columns:
                df['Tenure_Satisfaction_Interaction'] = df['Tenure'] * df['SatisfactionScore']
                feature_engineering_report['new_features'].append('Tenure_Satisfaction_Interaction')
                self._log(f"Created 'Tenure_Satisfaction_Interaction' feature")
            
            # OrderCount × Cashback interaction
            if 'OrderCount' in df.columns and 'CashbackAmount' in df.columns:
                df['Order_Cashback_Interaction'] = df['OrderCount'] * df['CashbackAmount']
                feature_engineering_report['new_features'].append('Order_Cashback_Interaction')
                self._log(f"Created 'Order_Cashback_Interaction' feature")
            
            # 3.6 Transform existing features
            self._log("3.6 Transforming existing features...")
            
            # Log transform for highly skewed numerical features
            skewed_features = ['OrderCount', 'CashbackAmount', 'DaySinceLastOrder']
            for feature in skewed_features:
                if feature in df.columns:
                    # Add small constant to avoid log(0)
                    df[f'log_{feature}'] = np.log1p(df[feature])
                    feature_engineering_report['transformed_features'].append(f'log_{feature}')
                    self._log(f"Created 'log_{feature}' transformation")
            
            # Square root transform for moderately skewed features
            sqrt_features = ['Tenure', 'CouponUsed']
            for feature in sqrt_features:
                if feature in df.columns:
                    df[f'sqrt_{feature}'] = np.sqrt(df[feature])
                    feature_engineering_report['transformed_features'].append(f'sqrt_{feature}')
                    self._log(f"Created 'sqrt_{feature}' transformation")
            
            # Update the dataframe
            self.df_clean = df
            
            # Update preprocessing report
            self.preprocessing_report['feature_engineering'] = feature_engineering_report
            self._log(f"Feature engineering completed: Added {len(feature_engineering_report['new_features'])} new features")
            self._log("engineer_features() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to engineer features: {e}", "ERROR")
            return False
    
    # ─────────────────────────────────────────
    # 4. HANDLE OUTLIERS
    # ─────────────────────────────────────────
    def handle_outliers(self):
        """Detect and handle outliers using IQR method with capping."""
        self._log("handle_outliers() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run clean_data() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            outlier_report = {}
            
            # Identify numerical columns (excluding ID, target, and newly created features)
            numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            exclude_cols = ['CustomerID', 'Churn'] + [col for col in df.columns if col.startswith('log_') or col.startswith('sqrt_')]
            numerical_cols = [col for col in numerical_cols if col not in exclude_cols]
            
            self._log(f"Checking {len(numerical_cols)} numerical features for outliers...")
            
            total_outliers = 0
            for col in numerical_cols:
                if df[col].notna().sum() > 0:
                    # Calculate IQR
                    q1 = df[col].quantile(0.25)
                    q3 = df[col].quantile(0.75)
                    iqr = q3 - q1
                    
                    # Define bounds
                    lower_bound = q1 - OUTLIER_IQR_MULTIPLIER * iqr
                    upper_bound = q3 + OUTLIER_IQR_MULTIPLIER * iqr
                    
                    # Identify outliers
                    outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                    outlier_count = len(outliers)
                    
                    if outlier_count > 0:
                        outlier_pct = (outlier_count / len(df)) * 100
                        total_outliers += outlier_count
                        
                        # Cap outliers (winsorization)
                        # Convert bounds to same data type as column
                        if df[col].dtype == np.int64:
                            lower_bound = int(lower_bound)
                            upper_bound = int(upper_bound)
                        
                        df.loc[df[col] < lower_bound, col] = lower_bound
                        df.loc[df[col] > upper_bound, col] = upper_bound
                        
                        # Record in report
                        outlier_report[col] = {
                            'outlier_count': outlier_count,
                            'outlier_pct': outlier_pct,
                            'lower_bound': float(lower_bound),
                            'upper_bound': float(upper_bound),
                            'action': 'capped'
                        }
                        
                        if self.verbose:
                            self._log(f"  '{col}': {outlier_count:,} outliers ({outlier_pct:.1f}%) - capped")
            
            # Update the dataframe
            self.df_clean = df
            
            # Update preprocessing report
            self.preprocessing_report['outlier_handling'] = {
                'total_outliers': total_outliers,
                'outlier_details': outlier_report,
                'features_checked': len(numerical_cols)
            }
            
            self._log(f"Outlier handling completed: {total_outliers:,} outliers capped across {len(outlier_report)} features")
            self._log("handle_outliers() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to handle outliers: {e}", "ERROR")
            return False
    
    # ─────────────────────────────────────────
    # 5. ENCODE AND SCALE
    # ─────────────────────────────────────────
    def encode_and_scale(self):
        """Encode categorical variables and scale numerical features."""
        self._log("encode_and_scale() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run clean_data() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            encoding_report = {'label_encoded': [], 'onehot_encoded': [], 'scaled': []}
            
            # 5.1 Label encoding for ordinal/ binary categorical features
            self._log("5.1 Applying label encoding...")
            
            # Features suitable for label encoding
            label_encode_features = ['Gender', 'MaritalStatus']
            
            for feature in label_encode_features:
                if feature in df.columns:
                    if HAS_SKLEARN:
                        le = LabelEncoder()
                        df[feature] = le.fit_transform(df[feature])
                        self.label_encoders[feature] = le
                        encoding_report['label_encoded'].append(feature)
                        self._log(f"Label encoded '{feature}'")
                    else:
                        # Manual encoding if sklearn not available
                        unique_values = df[feature].unique()
                        mapping = {val: idx for idx, val in enumerate(sorted(unique_values))}
                        df[feature] = df[feature].map(mapping)
                        encoding_report['label_encoded'].append(feature)
                        self._log(f"Manually label encoded '{feature}'")
            
            # 5.2 One-hot encoding for nominal categorical features
            self._log("5.2 Applying one-hot encoding...")
            
            # Features suitable for one-hot encoding
            onehot_features = ['PreferedLoginDevice', 'PreferedPaymentMode', 'PreferedOrderCat']
            
            for feature in onehot_features:
                if feature in df.columns:
                    if HAS_SKLEARN:
                        # Get dummies for now (simpler implementation)
                        dummies = pd.get_dummies(df[feature], prefix=feature, drop_first=True)
                        df = pd.concat([df, dummies], axis=1)
                        df.drop(columns=[feature], inplace=True)
                        encoding_report['onehot_encoded'].append(feature)
                        self._log(f"One-hot encoded '{feature}' (created {len(dummies.columns)} new columns)")
                    else:
                        # Manual one-hot encoding
                        dummies = pd.get_dummies(df[feature], prefix=feature, drop_first=True)
                        df = pd.concat([df, dummies], axis=1)
                        df.drop(columns=[feature], inplace=True)
                        encoding_report['onehot_encoded'].append(feature)
                        self._log(f"Manually one-hot encoded '{feature}' (created {len(dummies.columns)} new columns)")
            
            # 5.3 Scale numerical features
            self._log("5.3 Scaling numerical features...")
            
            # Identify numerical columns to scale (excluding ID, target, and encoded features)
            numerical_to_scale = df.select_dtypes(include=[np.number]).columns.tolist()
            exclude_from_scaling = ['CustomerID', 'Churn'] + encoding_report['label_encoded']
            numerical_to_scale = [col for col in numerical_to_scale if col not in exclude_from_scaling]
            
            if numerical_to_scale:
                if HAS_SKLEARN:
                    self.scaler = StandardScaler()
                    df[numerical_to_scale] = self.scaler.fit_transform(df[numerical_to_scale])
                    encoding_report['scaled'] = numerical_to_scale
                    self._log(f"Scaled {len(numerical_to_scale)} numerical features using StandardScaler")
                else:
                    # Manual standardization
                    for col in numerical_to_scale:
                        mean_val = df[col].mean()
                        std_val = df[col].std()
                        if std_val > 0:
                            df[col] = (df[col] - mean_val) / std_val
                    encoding_report['scaled'] = numerical_to_scale
                    self._log(f"Manually scaled {len(numerical_to_scale)} numerical features")
            
            # Update the processed dataframe
            self.df_processed = df
            
            # Update preprocessing report
            self.preprocessing_report['encoding_scaling'] = encoding_report
            
            self._log(f"Encoding and scaling completed: {len(encoding_report['label_encoded'])} label encoded, "
                     f"{len(encoding_report['onehot_encoded'])} one-hot encoded, "
                     f"{len(encoding_report['scaled'])} scaled")
            self._log("encode_and_scale() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to encode and scale: {e}", "ERROR")
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
            
            # Check 1: No missing values
            missing_check = df.isnull().sum().sum() == 0
            if missing_check:
                validation_report['checks_passed'] += 1
                validation_report['details'].append({'check': 'missing_values', 'status': 'PASS', 'message': 'No missing values found'})
                self._log("  [PASS] No missing values")
            else:
                validation_report['checks_failed'] += 1
                missing_count = df.isnull().sum().sum()
                validation_report['details'].append({'check': 'missing_values', 'status': 'FAIL', 'message': f'{missing_count} missing values found'})
                self._log(f"  [FAIL] Found {missing_count} missing values", "WARNING")
            
            # Check 2: No duplicate CustomerIDs
            duplicate_check = df['CustomerID'].duplicated().sum() == 0
            if duplicate_check:
                validation_report['checks_passed'] += 1
                validation_report['details'].append({'check': 'duplicate_ids', 'status': 'PASS', 'message': 'No duplicate CustomerIDs found'})
                self._log("  [PASS] No duplicate CustomerIDs")
            else:
                validation_report['checks_failed'] += 1
                duplicate_count = df['CustomerID'].duplicated().sum()
                validation_report['details'].append({'check': 'duplicate_ids', 'status': 'FAIL', 'message': f'{duplicate_count} duplicate CustomerIDs found'})
                self._log(f"  [FAIL] Found {duplicate_count} duplicate CustomerIDs", "WARNING")
            
            # Check 3: Target variable exists and has correct values
            if 'Churn' in df.columns:
                churn_values = df['Churn'].unique()
                churn_check = set(churn_values).issubset({0, 1})
                if churn_check:
                    validation_report['checks_passed'] += 1
                    validation_report['details'].append({'check': 'target_variable', 'status': 'PASS', 'message': 'Churn variable has valid values (0/1)'})
                    self._log("  [PASS] Churn variable has valid values")
                else:
                    validation_report['checks_failed'] += 1
                    validation_report['details'].append({'check': 'target_variable', 'status': 'FAIL', 'message': f'Churn has invalid values: {churn_values}'})
                    self._log(f"  [FAIL] Churn has invalid values: {churn_values}", "WARNING")
            
            # Check 4: Business rule validation
            self._log("6.2 Validating business rules...")
            
            for feature, rules in BUSINESS_RULES.items():
                if feature in df.columns:
                    # Check min/max bounds for numerical features
                    if 'min' in rules and 'max' in rules:
                        min_val = rules['min']
                        max_val = rules['max']
                        violations = df[(df[feature] < min_val) | (df[feature] > max_val)]
                        
                        if len(violations) == 0:
                            validation_report['checks_passed'] += 1
                            validation_report['details'].append({
                                'check': f'business_rule_{feature}',
                                'status': 'PASS',
                                'message': f'{feature} within valid range [{min_val}, {max_val}]'
                            })
                            self._log(f"  [PASS] {feature} within valid range")
                        else:
                            validation_report['checks_failed'] += 1
                            validation_report['details'].append({
                                'check': f'business_rule_{feature}',
                                'status': 'FAIL',
                                'message': f'{feature} has {len(violations)} values outside range [{min_val}, {max_val}]'
                            })
                            self._log(f"  [FAIL] {feature} has {len(violations)} values outside valid range", "WARNING")
                    
                    # Check valid values for categorical features
                    if 'valid_values' in rules:
                        valid_values = set(rules['valid_values'])
                        actual_values = set(df[feature].unique())
                        invalid_values = actual_values - valid_values
                        
                        if len(invalid_values) == 0:
                            validation_report['checks_passed'] += 1
                            validation_report['details'].append({
                                'check': f'business_rule_{feature}',
                                'status': 'PASS',
                                'message': f'{feature} has only valid values'
                            })
                            self._log(f"  [PASS] {feature} has only valid values")
                        else:
                            validation_report['checks_failed'] += 1
                            validation_report['details'].append({
                                'check': f'business_rule_{feature}',
                                'status': 'FAIL',
                                'message': f'{feature} has invalid values: {list(invalid_values)}'
                            })
                            self._log(f"  [FAIL] {feature} has invalid values: {list(invalid_values)}", "WARNING")
            
            # 6.3 Export processed data
            self._log("6.3 Exporting processed data...")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Export to CSV
            csv_filename = f"cleaned_ecommerce_churn_{timestamp}.csv"
            csv_path = os.path.join(self.output_dir, csv_filename)
            df.to_csv(csv_path, index=False)
            self._log(f"  [OK] Exported to CSV: {csv_path}")
            
            # Export to Parquet (if supported)
            try:
                parquet_filename = f"cleaned_ecommerce_churn_{timestamp}.parquet"
                parquet_path = os.path.join(self.output_dir, parquet_filename)
                df.to_parquet(parquet_path, index=False)
                self._log(f"  [OK] Exported to Parquet: {parquet_path}")
            except Exception as e:
                self._log(f"  [WARNING] Failed to export to Parquet: {e}", "WARNING")
            
            # 6.4 Save preprocessing report
            self._log("6.4 Saving preprocessing report...")
            
            # Add final statistics to report
            self.preprocessing_report['final_statistics'] = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'numerical_columns': len(df.select_dtypes(include=[np.number]).columns),
                'categorical_columns': len(df.select_dtypes(include=['object']).columns),
                'validation_results': validation_report
            }
            
            # Save report as JSON
            report_filename = f"preprocessing_report_{timestamp}.json"
            report_path = os.path.join(self.log_dir, report_filename)
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.preprocessing_report, f, indent=2, default=str)
            self._log(f"  [OK] Saved JSON report: {report_path}")
            
            # Save summary as text
            summary_filename = f"preprocessing_summary_{timestamp}.txt"
            summary_path = os.path.join(self.log_dir, summary_filename)
            self._save_summary_report(summary_path)
            self._log(f"  [OK] Saved text summary: {summary_path}")
            
            # 6.5 Display final summary
            self._log("\n" + "=" * 80)
            self._log("PREPROCESSING COMPLETED SUCCESSFULLY")
            self._log("=" * 80)
            self._log(f"Original dataset: {self.df_raw.shape[0]:,} rows × {self.df_raw.shape[1]:,} columns")
            self._log(f"Processed dataset: {len(df):,} rows × {len(df.columns):,} columns")
            self._log(f"New features created: {len(self.preprocessing_report.get('feature_engineering', {}).get('new_features', []))}")
            self._log(f"Validation checks: {validation_report['checks_passed']} passed, {validation_report['checks_failed']} failed")
            self._log(f"Output files saved in: {self.output_dir}")
            self._log(f"Logs and reports saved in: {self.log_dir}")
            
            self._log("validate_and_export() completed")
            return True
            
        except Exception as e:
            self._log(f"Failed to validate and export: {e}", "ERROR")
            return False
    
    # ─────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────
    def _save_summary_report(self, filepath: str):
        """Save a human-readable summary of the preprocessing."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("E-COMMERCE CUSTOMER CHURN - PREPROCESSING SUMMARY REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("1. DATASET OVERVIEW\n")
            f.write("-" * 40 + "\n")
            if 'dataset_info' in self.preprocessing_report:
                info = self.preprocessing_report['dataset_info']
                f.write(f"Original shape: {info['original_shape'][0]:,} rows × {info['original_shape'][1]:,} columns\n")
                f.write(f"Memory usage: {info['memory_usage_mb']:.2f} MB\n")
            
            f.write("\n2. DATA CLEANING\n")
            f.write("-" * 40 + "\n")
            if 'cleaning' in self.preprocessing_report:
                cleaning = self.preprocessing_report['cleaning']
                f.write(f"Cleaned shape: {cleaning['cleaned_shape'][0]:,} rows × {cleaning['cleaned_shape'][1]:,} columns\n")
                f.write(f"Columns removed: {cleaning['columns_removed']}\n")
                f.write(f"Duplicates removed: {cleaning['duplicates_removed']}\n")
            
            f.write("\n3. FEATURE ENGINEERING\n")
            f.write("-" * 40 + "\n")
            if 'feature_engineering' in self.preprocessing_report:
                fe = self.preprocessing_report['feature_engineering']
                f.write(f"New features created: {len(fe['new_features'])}\n")
                f.write(f"Features transformed: {len(fe['transformed_features'])}\n")
                
                if fe['new_features']:
                    f.write("\n  New features:\n")
                    for feature in fe['new_features']:
                        f.write(f"    - {feature}\n")
            
            f.write("\n4. OUTLIER HANDLING\n")
            f.write("-" * 40 + "\n")
            if 'outlier_handling' in self.preprocessing_report:
                outliers = self.preprocessing_report['outlier_handling']
                f.write(f"Total outliers capped: {outliers['total_outliers']:,}\n")
                f.write(f"Features checked: {outliers['features_checked']}\n")
            
            f.write("\n5. VALIDATION RESULTS\n")
            f.write("-" * 40 + "\n")
            if 'final_statistics' in self.preprocessing_report:
                stats = self.preprocessing_report['final_statistics']
                validation = stats['validation_results']
                f.write(f"Checks passed: {validation['checks_passed']}\n")
                f.write(f"Checks failed: {validation['checks_failed']}\n")
                
                if validation['details']:
                    f.write("\n  Check details:\n")
                    for detail in validation['details']:
                        status_symbol = "[PASS]" if detail['status'] == 'PASS' else "[FAIL]"
                        f.write(f"    {status_symbol} {detail['check']}: {detail['message']}\n")
            
            f.write("\n6. FINAL DATASET\n")
            f.write("-" * 40 + "\n")
            if 'final_statistics' in self.preprocessing_report:
                stats = self.preprocessing_report['final_statistics']
                f.write(f"Total rows: {stats['total_rows']:,}\n")
                f.write(f"Total columns: {stats['total_columns']:,}\n")
                f.write(f"Numerical columns: {stats['numerical_columns']}\n")
                f.write(f"Categorical columns: {stats['categorical_columns']}\n")
    
    # ─────────────────────────────────────────
    # MAIN EXECUTION PIPELINE
    # ─────────────────────────────────────────
    def run_full_pipeline(self):
        """Execute the complete preprocessing pipeline."""
        self._log("Starting full preprocessing pipeline...")
        
        steps = [
            ("1. Loading data", self.load_data),
            ("2. Cleaning data", self.clean_data),
            ("3. Engineering features", self.engineer_features),
            ("4. Handling outliers", self.handle_outliers),
            ("5. Encoding and scaling", self.encode_and_scale),
            ("6. Validating and exporting", self.validate_and_export)
        ]
        
        successful_steps = 0
        total_steps = len(steps)
        
        for step_name, step_function in steps:
            self._log(f"\n{step_name}...")
            if step_function():
                successful_steps += 1
                self._log(f"{step_name} completed successfully")
            else:
                self._log(f"{step_name} failed", "ERROR")
                break
        
        if successful_steps == total_steps:
            self._log(f"\nAll {total_steps} preprocessing steps completed successfully!")
            return True
        else:
            self._log(f"\nPreprocessing incomplete. {successful_steps}/{total_steps} steps completed.", "WARNING")
            return False


# ─────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CUSTOMERDNA AI - E-COMMERCE CUSTOMER CHURN PREPROCESSING")
    print("=" * 80)
    
    # Initialize and run the preprocessing pipeline
    preprocessor = EnhancedEcommerceChurnPreprocessing(verbose=True)
    
    try:
        success = preprocessor.run_full_pipeline()
        
        if success:
            print("\n" + "=" * 80)
            print("PREPROCESSING COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("\nNext steps:")
            print("1. Check the cleaned dataset in the 'cleaned_dataset' folder")
            print("2. Review the preprocessing report in the 'logs' folder")
            print("3. Proceed with model training using the cleaned data")
        else:
            print("\n" + "=" * 80)
            print("PREPROCESSING FAILED OR INCOMPLETE")
            print("=" * 80)
            print("\nPlease check the error logs and fix the issues.")
    
    except KeyboardInterrupt:
        print("\n\nPreprocessing interrupted by user.")
    
    except Exception as e:
        print(f"\n\nUnexpected error during preprocessing: {e}")
        import traceback
        traceback.print_exc()