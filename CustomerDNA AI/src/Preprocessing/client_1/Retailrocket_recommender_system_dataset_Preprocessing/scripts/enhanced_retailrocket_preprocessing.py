"""
CustomerDNA AI - PFE Project
Dataset: Retailrocket Recommender System Dataset
Script: Enhanced Retailrocket Preprocessing — Comprehensive Pipeline
Author: PFE Student
Description: Comprehensive preprocessing pipeline for Retailrocket recommender system dataset
             including data cleaning, feature engineering, interaction analysis, and session processing
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
    from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
    from sklearn.impute import SimpleImputer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[WARNING] scikit-learn not available. Some advanced preprocessing techniques will be skipped.")

# ─────────────────────────────────────────────
# PATHS — adjust only these lines
# ─────────────────────────────────────────────
DATA_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\datasets\client_1\Retailrocket_recommender_system_dataset"
EVENTS_PATH = os.path.join(DATA_DIR, 'events.csv')
CATEGORY_TREE_PATH = os.path.join(DATA_DIR, 'category_tree.csv')
ITEM_PROPS_PART1_PATH = os.path.join(DATA_DIR, 'item_properties_part1.csv')
ITEM_PROPS_PART2_PATH = os.path.join(DATA_DIR, 'item_properties_part2.csv')

OUTPUT_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\client_1\Retailrocket_recommender_system_dataset_Preprocessing\cleaned_dataset"
LOG_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\client_1\Retailrocket_recommender_system_dataset_Preprocessing\logs"
CONFIG_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\Preprocessing\client_1\Retailrocket_recommender_system_dataset_Preprocessing\config"

# ─────────────────────────────────────────────
# CONSTANTS — data preprocessing rules
# ─────────────────────────────────────────────
# Missing value handling thresholds
MISSING_THRESHOLD_DROP = 30.0  # Drop columns with >30% missing
MISSING_THRESHOLD_IMPUTE = 10.0  # Use advanced imputation for 10-30% missing

# Outlier detection thresholds (based on IQR method)
OUTLIER_IQR_MULTIPLIER = 1.5

# Sampling parameters (for memory management with large datasets)
SAMPLE_SIZE = 100000  # Sample 100,000 records for memory efficiency

# Session analysis parameters
SESSION_TIMEOUT_MINUTES = 30  # Consider events within 30 minutes as same session

# Business rules for validation
BUSINESS_RULES = {
    'timestamp': {'min': 1400000000, 'max': 1500000000, 'description': 'Timestamp should be within 2014-2017 range'},
    'visitorid': {'min': 1, 'max': 10000000, 'description': 'Visitor ID range'},
    'event': {'allowed_values': ['view', 'addtocart', 'transaction'], 'description': 'Valid event types'},
    'itemid': {'min': 1, 'max': 1000000, 'description': 'Item ID range'}
}

# Event type mapping for analysis
EVENT_TYPE_MAPPING = {
    'view': 1,
    'addtocart': 2,
    'transaction': 3
}

# Event type weights for engagement scoring
EVENT_WEIGHTS = {
    'view': 1,
    'addtocart': 3,
    'transaction': 5
}


class EnhancedRetailrocketPreprocessing:
    """
    Enhanced preprocessing class for Retailrocket Recommender System Dataset.
    Includes comprehensive data cleaning, transformation, and feature engineering.
    """

    def __init__(self, verbose=True):
        self.data_dir = DATA_DIR
        self.events_path = EVENTS_PATH
        self.category_tree_path = CATEGORY_TREE_PATH
        self.item_props_part1_path = ITEM_PROPS_PART1_PATH
        self.item_props_part2_path = ITEM_PROPS_PART2_PATH
        
        self.output_dir = OUTPUT_DIR
        self.log_dir = LOG_DIR
        self.config_dir = CONFIG_DIR
        
        # Create directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.df_events = None
        self.df_category_tree = None
        self.df_item_props = None
        self.df_clean = None
        self.preprocessing_report = {}
        self.verbose = verbose
        
        # Initialize preprocessing steps tracking
        self.preprocessing_steps = []
        
        print("=" * 80)
        print("CustomerDNA AI — Enhanced Retailrocket Recommender System Preprocessing")
        print("=" * 80)
        print(f"Data Directory : {self.data_dir}")
        print(f"Output Directory : {self.output_dir}")
        print(f"Log Directory : {self.log_dir}")
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
        """Load all datasets and perform initial assessment."""
        self._log("load_and_assess_data() started")
        
        try:
            # Load events data
            self._log("Loading events data...")
            self.df_events = pd.read_csv(self.events_path)
            
            # Load category tree
            self._log("Loading category tree...")
            self.df_category_tree = pd.read_csv(self.category_tree_path)
            
            # Load item properties (combine both parts)
            self._log("Loading item properties...")
            df_item_props_part1 = pd.read_csv(self.item_props_part1_path)
            df_item_props_part2 = pd.read_csv(self.item_props_part2_path)
            self.df_item_props = pd.concat([df_item_props_part1, df_item_props_part2], ignore_index=True)
            
            # Store initial assessment
            self.preprocessing_report['initial_assessment'] = {
                'events_shape': self.df_events.shape,
                'category_tree_shape': self.df_category_tree.shape,
                'item_props_shape': self.df_item_props.shape,
                'events_columns': list(self.df_events.columns),
                'category_tree_columns': list(self.df_category_tree.columns),
                'item_props_columns': list(self.df_item_props.columns),
                'events_missing_values': self.df_events.isnull().sum().to_dict(),
                'category_tree_missing_values': self.df_category_tree.isnull().sum().to_dict(),
                'item_props_missing_values': self.df_item_props.isnull().sum().to_dict(),
                'events_memory_usage_mb': self.df_events.memory_usage(deep=True).sum() / 1024**2,
                'category_tree_memory_usage_mb': self.df_category_tree.memory_usage(deep=True).sum() / 1024**2,
                'item_props_memory_usage_mb': self.df_item_props.memory_usage(deep=True).sum() / 1024**2
            }
            
            # Log initial findings
            self._log(f"Events data loaded: {self.df_events.shape[0]:,} rows × {self.df_events.shape[1]} columns")
            self._log(f"Category tree loaded: {self.df_category_tree.shape[0]:,} rows × {self.df_category_tree.shape[1]} columns")
            self._log(f"Item properties loaded: {self.df_item_props.shape[0]:,} rows × {self.df_item_props.shape[1]} columns")
            
            # Check for missing values
            total_missing_events = self.df_events.isnull().sum().sum()
            if total_missing_events > 0:
                self._log(f"Total missing values in events: {total_missing_events:,}", "WARNING")
            
            total_missing_category = self.df_category_tree.isnull().sum().sum()
            if total_missing_category > 0:
                self._log(f"Total missing values in category tree: {total_missing_category:,}", "WARNING")
            
            total_missing_item_props = self.df_item_props.isnull().sum().sum()
            if total_missing_item_props > 0:
                self._log(f"Total missing values in item properties: {total_missing_item_props:,}", "WARNING")
            
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
        
        if self.df_events is None:
            self._log("No events data available. Run load_and_assess_data() first.", "ERROR")
            return False
        
        try:
            # Create a copy for cleaning
            df_clean = self.df_events.copy()
            
            # 2.1 Handle missing values
            self._log("2.1 Handling missing values...")
            
            # Calculate missing percentages
            missing_percent = (df_clean.isnull().sum() / len(df_clean)) * 100
            
            # Drop columns with too many missing values
            columns_to_drop = missing_percent[missing_percent > MISSING_THRESHOLD_DROP].index.tolist()
            if columns_to_drop:
                df_clean = df_clean.drop(columns=columns_to_drop)
                self._log(f"  Dropped columns with >{MISSING_THRESHOLD_DROP}% missing: {columns_to_drop}", "WARNING")
            
            # For columns with moderate missing values, use imputation
            columns_to_impute = missing_percent[(missing_percent > MISSING_THRESHOLD_IMPUTE) & 
                                               (missing_percent <= MISSING_THRESHOLD_DROP)].index.tolist()
            
            if columns_to_impute:
                for col in columns_to_impute:
                    if df_clean[col].dtype in ['int64', 'float64']:
                        # Use median for numerical columns
                        imputer = SimpleImputer(strategy='median')
                        df_clean[col] = imputer.fit_transform(df_clean[[col]]).ravel()
                        self._log(f"  Imputed {col} with median: {df_clean[col].median():.2f}", "INFO")
                    else:
                        # Use mode for categorical columns
                        imputer = SimpleImputer(strategy='most_frequent')
                        df_clean[col] = imputer.fit_transform(df_clean[[col]]).ravel()
                        self._log(f"  Imputed {col} with mode: {df_clean[col].mode()[0]}", "INFO")
            
            # 2.2 Handle duplicates
            self._log("2.2 Handling duplicates...")
            initial_rows = len(df_clean)
            df_clean = df_clean.drop_duplicates()
            duplicates_removed = initial_rows - len(df_clean)
            
            if duplicates_removed > 0:
                self._log(f"  Removed {duplicates_removed:,} duplicate rows", "WARNING")
            else:
                self._log("  No duplicate rows found", "INFO")
            
            # 2.3 Data type conversion and validation
            self._log("2.3 Data type conversion and validation...")
            
            # Convert timestamp to datetime
            df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'], unit='s')
            
            # Validate data against business rules
            validation_issues = []
            
            # Check timestamp range
            min_timestamp = df_clean['timestamp'].min()
            max_timestamp = df_clean['timestamp'].max()
            if min_timestamp.year < 2014 or max_timestamp.year > 2017:
                validation_issues.append(f"Timestamp range: {min_timestamp} to {max_timestamp}")
            
            # Check visitor ID range
            min_visitor = df_clean['visitorid'].min()
            max_visitor = df_clean['visitorid'].max()
            if min_visitor < BUSINESS_RULES['visitorid']['min'] or max_visitor > BUSINESS_RULES['visitorid']['max']:
                validation_issues.append(f"Visitor ID range: {min_visitor} to {max_visitor}")
            
            # Check event types
            invalid_events = df_clean[~df_clean['event'].isin(BUSINESS_RULES['event']['allowed_values'])]
            if len(invalid_events) > 0:
                validation_issues.append(f"Invalid event types: {invalid_events['event'].unique().tolist()}")
            
            if validation_issues:
                self._log(f"  Validation issues found: {validation_issues}", "WARNING")
            else:
                self._log("  All data validated successfully", "INFO")
            
            # 2.4 Standardize categorical values
            self._log("2.4 Standardizing categorical values...")
            
            # Standardize event types (lowercase, trim whitespace)
            df_clean['event'] = df_clean['event'].str.lower().str.strip()
            
            # Map event types to numerical codes
            df_clean['event_code'] = df_clean['event'].map(EVENT_TYPE_MAPPING)
            
            self._log(f"  Standardized event types: {df_clean['event'].unique().tolist()}", "INFO")
            
            # Store cleaned data
            self.df_clean = df_clean
            
            # Update preprocessing report
            self.preprocessing_report['cleaning'] = {
                'final_shape': self.df_clean.shape,
                'duplicates_removed': duplicates_removed,
                'columns_dropped': columns_to_drop,
                'columns_imputed': columns_to_impute,
                'validation_issues': validation_issues,
                'event_types': df_clean['event'].value_counts().to_dict()
            }
            
            self._log(f"Data cleaning completed: {self.df_clean.shape[0]:,} rows × {self.df_clean.shape[1]} columns", "INFO")
            return True
            
        except Exception as e:
            self._log(f"Failed to clean data: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────
    # 3. FEATURE ENGINEERING
    # ─────────────────────────────────────────
    def engineer_features(self):
        """Create comprehensive features for recommendation analysis."""
        self._log("engineer_features() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run clean_data() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            
            # 3.1 Create temporal features
            self._log("3.1 Creating temporal features...")
            
            # Extract date components
            df['date'] = df['timestamp'].dt.date
            df['year'] = df['timestamp'].dt.year
            df['month'] = df['timestamp'].dt.month
            df['day'] = df['timestamp'].dt.day
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # 3.2 Create session features
            self._log("3.2 Creating session features...")
            
            # Sort by visitor and timestamp
            df = df.sort_values(['visitorid', 'timestamp'])
            
            # Calculate time difference between consecutive events for same visitor
            df['time_diff'] = df.groupby('visitorid')['timestamp'].diff().dt.total_seconds() / 60
            
            # Identify session boundaries (time difference > SESSION_TIMEOUT_MINUTES)
            df['new_session'] = (df['time_diff'] > SESSION_TIMEOUT_MINUTES) | df['time_diff'].isna()
            
            # Create session IDs
            df['session_id'] = df.groupby('visitorid')['new_session'].cumsum()
            
            # 3.3 Create engagement features
            self._log("3.3 Creating engagement features...")
            
            # Calculate session duration
            session_duration = df.groupby(['visitorid', 'session_id'])['timestamp'].agg(['min', 'max'])
            session_duration['session_duration_minutes'] = (session_duration['max'] - session_duration['min']).dt.total_seconds() / 60
            
            # Merge session duration back
            df = df.merge(session_duration[['session_duration_minutes']], 
                         left_on=['visitorid', 'session_id'], 
                         right_index=True)
            
            # Calculate events per session
            df['events_per_session'] = df.groupby(['visitorid', 'session_id'])['event'].transform('count')
            
            # Calculate unique items per session
            df['unique_items_per_session'] = df.groupby(['visitorid', 'session_id'])['itemid'].transform('nunique')
            
            # 3.4 Create conversion features
            self._log("3.4 Creating conversion features...")
            
            # Check if session contains a transaction
            session_has_transaction = df.groupby(['visitorid', 'session_id'])['event'].transform(
                lambda x: 'transaction' in x.values
            )
            df['session_has_transaction'] = session_has_transaction.astype(int)
            
            # Calculate conversion rate per visitor
            visitor_conversion = df.groupby('visitorid')['session_has_transaction'].max()
            df['visitor_converted'] = df['visitorid'].map(visitor_conversion)
            
            # 3.5 Create interaction features
            self._log("3.5 Creating interaction features...")
            
            # Calculate view-to-cart ratio per session
            session_event_counts = df.groupby(['visitorid', 'session_id', 'event']).size().unstack(fill_value=0)
            session_event_counts['view_to_cart_ratio'] = np.where(
                session_event_counts['view'] > 0,
                session_event_counts['addtocart'] / session_event_counts['view'],
                0
            )
            
            # Merge interaction features back
            df = df.merge(session_event_counts[['view_to_cart_ratio']], 
                         left_on=['visitorid', 'session_id'], 
                         right_index=True)
            
            # 3.6 Create engagement score
            self._log("3.6 Creating engagement score...")
            
            # Calculate weighted engagement score
            df['engagement_weight'] = df['event'].map(EVENT_WEIGHTS)
            visitor_engagement = df.groupby('visitorid')['engagement_weight'].sum()
            df['engagement_score'] = df['visitorid'].map(visitor_engagement)
            
            # Normalize engagement score
            max_engagement = df['engagement_score'].max()
            if max_engagement > 0:
                df['engagement_score_normalized'] = df['engagement_score'] / max_engagement
            
            # Update the cleaned dataframe with new features
            self.df_clean = df
            
            # Update preprocessing report
            self.preprocessing_report['feature_engineering'] = {
                'total_features': len(df.columns),
                'new_features_added': len(df.columns) - len(self.df_events.columns),
                'feature_list': list(df.columns),
                'session_count': df['session_id'].nunique(),
                'conversion_rate': df['visitor_converted'].mean() * 100
            }
            
            self._log(f"Feature engineering completed: {len(df.columns)} total features", "INFO")
            self._log(f"  Sessions created: {df['session_id'].nunique():,}", "INFO")
            self._log(f"  Conversion rate: {df['visitor_converted'].mean() * 100:.2f}%", "INFO")
            
            return True
            
        except Exception as e:
            self._log(f"Failed to engineer features: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────
    # 4. OUTLIER HANDLING
    # ─────────────────────────────────────────
    def handle_outliers(self):
        """Detect and handle outliers in numerical features."""
        self._log("handle_outliers() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run engineer_features() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            
            # Identify numerical columns
            numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Remove non-feature columns
            numerical_cols = [col for col in numerical_cols if col not in ['visitorid', 'itemid', 'event_code', 'session_id']]
            
            outlier_report = {}
            total_outliers = 0
            
            for col in numerical_cols:
                # Calculate IQR
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                # Define outlier boundaries
                lower_bound = Q1 - OUTLIER_IQR_MULTIPLIER * IQR
                upper_bound = Q3 + OUTLIER_IQR_MULTIPLIER * IQR
                
                # Identify outliers
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                outlier_count = len(outliers)
                
                if outlier_count > 0:
                    # Cap outliers at boundaries
                    df[col] = np.where(df[col] < lower_bound, lower_bound, df[col])
                    df[col] = np.where(df[col] > upper_bound, upper_bound, df[col])
                    
                    outlier_report[col] = {
                        'outlier_count': outlier_count,
                        'percentage': (outlier_count / len(df)) * 100,
                        'lower_bound': lower_bound,
                        'upper_bound': upper_bound,
                        'min_before': outliers[col].min(),
                        'max_before': outliers[col].max(),
                        'min_after': df[col].min(),
                        'max_after': df[col].max()
                    }
                    
                    total_outliers += outlier_count
                    
                    self._log(f"  {col}: {outlier_count:,} outliers detected, {outlier_count:,} capped", "INFO")
            
            # Update the cleaned dataframe
            self.df_clean = df
            
            # Update preprocessing report
            self.preprocessing_report['outlier_handling'] = {
                'total_outliers': total_outliers,
                'outlier_details': outlier_report,
                'numerical_features_processed': len(numerical_cols)
            }
            
            self._log(f"Outlier handling completed: {total_outliers:,} total outliers handled", "INFO")
            
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
            self._log("No cleaned data available. Run handle_outliers() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            
            encoding_report = {}
            scaling_report = {}
            
            # 5.1 Encode categorical variables
            self._log("5.1 Encoding categorical variables...")
            
            # Identify categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if HAS_SKLEARN and categorical_cols:
                for col in categorical_cols:
                    if col in df.columns:
                        # Use LabelEncoder for categorical variables
                        le = LabelEncoder()
                        df[col + '_encoded'] = le.fit_transform(df[col].astype(str))
                        
                        encoding_report[col] = {
                            'unique_values': df[col].nunique(),
                            'encoding_mapping': dict(zip(le.classes_, le.transform(le.classes_))),
                            'missing_values': df[col].isnull().sum()
                        }
                        
                        self._log(f"  Encoded {col}: {df[col].nunique():,} unique values", "INFO")
            
            # 5.2 Scale numerical features
            self._log("5.2 Scaling numerical features...")
            
            # Identify numerical columns (excluding IDs and encoded columns)
            numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            numerical_cols = [col for col in numerical_cols 
                            if not col.endswith('_encoded') 
                            and col not in ['visitorid', 'itemid', 'session_id', 'event_code']]
            
            if HAS_SKLEARN and numerical_cols:
                # Use MinMaxScaler for normalization
                scaler = MinMaxScaler()
                scaled_data = scaler.fit_transform(df[numerical_cols])
                df_scaled = pd.DataFrame(scaled_data, columns=[f"{col}_scaled" for col in numerical_cols])
                
                # Combine with original dataframe
                df = pd.concat([df, df_scaled], axis=1)
                
                for col in numerical_cols:
                    scaling_report[col] = {
                        'min_before': df[col].min(),
                        'max_before': df[col].max(),
                        'min_after': df[f"{col}_scaled"].min(),
                        'max_after': df[f"{col}_scaled"].max(),
                        'scaler_type': 'MinMaxScaler'
                    }
                
                self._log(f"  Scaled {len(numerical_cols):,} numerical features", "INFO")
            
            # Update the cleaned dataframe
            self.df_clean = df
            
            # Update preprocessing report
            self.preprocessing_report['encoding_scaling'] = {
                'encoding_details': encoding_report,
                'scaling_details': scaling_report,
                'categorical_features_encoded': len(categorical_cols),
                'numerical_features_scaled': len(numerical_cols)
            }
            
            self._log("Encoding and scaling completed", "INFO")
            return True
            
        except Exception as e:
            self._log(f"Failed to encode and scale: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────
    # 6. VALIDATION AND EXPORT
    # ─────────────────────────────────────────
    def validate_and_export(self):
        """Perform final validation and export cleaned data."""
        self._log("validate_and_export() started")
        
        if self.df_clean is None:
            self._log("No cleaned data available. Run encode_and_scale() first.", "ERROR")
            return False
        
        try:
            df = self.df_clean.copy()
            
            # 6.1 Perform final validation checks
            self._log("6.1 Performing final validation checks...")
            
            validation_checks = []
            
            # Check for missing values
            missing_values = df.isnull().sum().sum()
            if missing_values > 0:
                validation_checks.append(f"Missing values: {missing_values:,}")
            
            # Check for infinite values
            infinite_values = np.isinf(df.select_dtypes(include=[np.number])).sum().sum()
            if infinite_values > 0:
                validation_checks.append(f"Infinite values: {infinite_values:,}")
            
            # Check data types
            invalid_types = []
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Check for mixed types in object columns
                    try:
                        pd.to_numeric(df[col], errors='raise')
                    except:
                        invalid_types.append(col)
            
            if invalid_types:
                validation_checks.append(f"Invalid data types in: {invalid_types}")
            
            if validation_checks:
                self._log(f"  Validation failed for: {validation_checks}", "WARNING")
            else:
                self._log("  All validation checks passed", "INFO")
            
            # 6.2 Export cleaned dataset
            self._log("6.2 Exporting cleaned dataset...")
            
            # Generate timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export to CSV
            csv_path = os.path.join(self.output_dir, f"cleaned_retailrocket_{timestamp}.csv")
            df.to_csv(csv_path, index=False)
            self._log(f"  CSV exported: {csv_path}", "INFO")
            
            # Export to Parquet (if supported)
            try:
                parquet_path = os.path.join(self.output_dir, f"cleaned_retailrocket_{timestamp}.parquet")
                df.to_parquet(parquet_path, index=False)
                self._log(f"  Parquet exported: {parquet_path}", "INFO")
            except Exception as e:
                self._log(f"  Parquet export failed: {e}", "WARNING")
            
            # Export interaction data (simplified version for analysis)
            interaction_data = df[['visitorid', 'itemid', 'event', 'timestamp', 'session_id']].copy()
            interaction_csv_path = os.path.join(self.output_dir, f"interaction_data_{timestamp}.csv")
            interaction_data.to_csv(interaction_csv_path, index=False)
            self._log(f"  Interaction data exported: {interaction_csv_path}", "INFO")
            
            # 6.3 Save preprocessing report
            self._log("6.3 Saving preprocessing report...")
            
            # Add final summary to report
            self.preprocessing_report['summary'] = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'total_visitors': df['visitorid'].nunique(),
                'total_items': df['itemid'].nunique(),
                'total_sessions': df['session_id'].nunique(),
                'total_transactions': df[df['event'] == 'transaction'].shape[0],
                'conversion_rate': df['visitor_converted'].mean() * 100,
                'avg_session_duration': df['session_duration_minutes'].mean(),
                'avg_events_per_session': df['events_per_session'].mean()
            }
            
            # Save report as JSON
            report_path = os.path.join(self.log_dir, f"preprocessing_report_{timestamp}.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.preprocessing_report, f, indent=2, default=str)
            
            # Save summary as text
            summary_path = os.path.join(self.log_dir, f"preprocessing_summary_{timestamp}.txt")
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("RETAILROCKET PREPROCESSING SUMMARY\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Dataset: Retailrocket Recommender System Dataset\n")
                f.write(f"Client: client_1\n")
                f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("FINAL DATASET STATISTICS:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total Rows: {len(df):,}\n")
                f.write(f"Total Columns: {len(df.columns):,}\n")
                f.write(f"Unique Visitors: {df['visitorid'].nunique():,}\n")
                f.write(f"Unique Items: {df['itemid'].nunique():,}\n")
                f.write(f"Total Sessions: {df['session_id'].nunique():,}\n")
                f.write(f"Total Transactions: {df[df['event'] == 'transaction'].shape[0]:,}\n")
                f.write(f"Conversion Rate: {df['visitor_converted'].mean() * 100:.2f}%\n")
                f.write(f"Avg Session Duration: {df['session_duration_minutes'].mean():.2f} minutes\n")
                f.write(f"Avg Events per Session: {df['events_per_session'].mean():.2f}\n\n")
                
                f.write("PREPROCESSING STEPS COMPLETED:\n")
                f.write("-" * 40 + "\n")
                for step in self.preprocessing_steps:
                    f.write(f"✓ {step}\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("PREPROCESSING COMPLETED SUCCESSFULLY!\n")
                f.write("=" * 80 + "\n")
            
            self._log(f"  Report saved: {report_path}", "INFO")
            self._log(f"  Summary saved: {summary_path}", "INFO")
            
            # Update preprocessing steps tracking
            self.preprocessing_steps.append("Data loading and assessment")
            self.preprocessing_steps.append("Data cleaning")
            self.preprocessing_steps.append("Feature engineering")
            self.preprocessing_steps.append("Outlier handling")
            self.preprocessing_steps.append("Encoding and scaling")
            self.preprocessing_steps.append("Validation and export")
            
            return True
            
        except Exception as e:
            self._log(f"Failed to validate and export: {e}", "ERROR")
            return False

    # ─────────────────────────────────────────
    # MAIN PREPROCESSING PIPELINE
    # ─────────────────────────────────────────
    def run_complete_preprocessing(self):
        """Run the complete preprocessing pipeline."""
        self._log("run_complete_preprocessing() started")
        
        print("\n" + "=" * 80)
        print("STARTING COMPREHENSIVE PREPROCESSING PIPELINE")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Step 1: Load and assess data
        if not self.load_and_assess_data():
            self._log("Data loading failed. Stopping preprocessing.", "ERROR")
            return False
        
        # Step 2: Clean data
        if not self.clean_data():
            self._log("Data cleaning failed. Stopping preprocessing.", "ERROR")
            return False
        
        # Step 3: Engineer features
        if not self.engineer_features():
            self._log("Feature engineering failed. Stopping preprocessing.", "ERROR")
            return False
        
        # Step 4: Handle outliers
        if not self.handle_outliers():
            self._log("Outlier handling failed. Stopping preprocessing.", "ERROR")
            return False
        
        # Step 5: Encode and scale
        if not self.encode_and_scale():
            self._log("Encoding and scaling failed. Stopping preprocessing.", "ERROR")
            return False
        
        # Step 6: Validate and export
        if not self.validate_and_export():
            self._log("Validation and export failed. Stopping preprocessing.", "ERROR")
            return False
        
        # Calculate total processing time
        end_time = datetime.now()
        processing_duration = end_time - start_time
        
        # Print final summary
        print("\n" + "=" * 80)
        print("PREPROCESSING COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Total processing time: {processing_duration}")
        print(f"Final dataset shape: {self.df_clean.shape}")
        print(f"Output directory: {self.output_dir}")
        print("=" * 80)
        
        return True


# ─────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 80)
    print("CUSTOMERDNA AI - RETAILROCKET PREPROCESSING SCRIPT")
    print("=" * 80)
    
    try:
        # Initialize preprocessor
        preprocessor = EnhancedRetailrocketPreprocessing(verbose=True)
        
        # Run complete preprocessing pipeline
        success = preprocessor.run_complete_preprocessing()
        
        if success:
            print("\n[SUCCESS] Retailrocket preprocessing completed successfully!")
            print(f"Output files saved in: {OUTPUT_DIR}")
            print(f"Log files saved in: {LOG_DIR}")
            sys.exit(0)
        else:
            print("\n[ERROR] Retailrocket preprocessing failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n[INFO] Preprocessing interrupted by user.")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)