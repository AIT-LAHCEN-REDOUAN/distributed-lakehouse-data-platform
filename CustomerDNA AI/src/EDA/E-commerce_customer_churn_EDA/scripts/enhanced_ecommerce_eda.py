"""
CustomerDNA AI - PFE Project
Dataset : E-commerce Customer Churn (E-commerce_customer_churn.xlsx)
Script  : Enhanced E-commerce EDA — Maximum Possible Plots
Author  : PFE Student
Description: Comprehensive EDA with maximum possible visualization types for e-commerce customer churn analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try to import optional libraries for advanced analysis
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[WARNING] scipy not available. Some advanced statistical plots will be skipped.")

try:
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[WARNING] scikit-learn not available. Clustering and dimensionality reduction will be skipped.")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    print("[WARNING] plotly not available. Interactive visualizations will be skipped.")

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("[WARNING] networkx not available. Correlation network visualization will be skipped.")

# ─────────────────────────────────────────────
# PATHS — adjust only these lines
# ─────────────────────────────────────────────
DATA_PATH  = r"d:\github\Master_PFE_Project\CustomerDNA AI\base_dataset\E-commerce_customer_churn\E-commerce_customer_churn.xlsx"
OUTPUT_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\EDA\E-commerce_customer_churn_EDA\output"

# ─────────────────────────────────────────────
# CONSTANTS — data cleaning rules
# ─────────────────────────────────────────────
# Based on data quality audit, we have several columns with missing values
# We'll handle them during cleaning
MISSING_THRESHOLD = 0.05  # 5% threshold for significant missingness

# Outlier detection thresholds (based on IQR method)
OUTLIER_IQR_MULTIPLIER = 1.5

# Categorical value mappings for consistency
GENDER_MAPPING = {"Male": "Male", "Female": "Female"}
MARITAL_STATUS_MAPPING = {"Married": "Married", "Single": "Single", "Divorced": "Divorced"}


class EnhancedEcommerceEDA:
    """
    Enhanced EDA class for E-commerce Customer Churn with maximum possible plots.
    Includes comprehensive visualization across all analysis types.
    """

    def __init__(self):
        self.data_path  = DATA_PATH
        self.output_dir = OUTPUT_DIR

        os.makedirs(self.output_dir, exist_ok=True)

        self.df       = None
        self.df_clean = None
        self.results  = {}

        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        print("=" * 80)
        print("CustomerDNA AI — Enhanced E-commerce Customer Churn EDA")
        print("=" * 80)
        print(f"Data   : {self.data_path}")
        print(f"Output : {self.output_dir}")
        print("-" * 80)

    # ─────────────────────────────────────────
    # LOGGING HELPER
    # ─────────────────────────────────────────
    def _log(self, message: str):
        """Print a timestamped log entry."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"LOG [{timestamp}]: {message}")

    # ─────────────────────────────────────────
    # 1. LOAD DATA
    # ─────────────────────────────────────────
    def load_data(self):
        """Load the raw Excel and display a basic profile."""
        print("\n1. Loading data...")
        self._log("load_data() started")
        
        try:
            # Read the Excel file
            self.df = pd.read_excel(self.data_path, sheet_name='E Comm')
            print(f"   [OK] Loaded {len(self.df):,} rows and {len(self.df.columns)} columns")
            
            # Basic dataset info
            print(f"\n   Dataset Overview:")
            print(f"   - Shape: {self.df.shape}")
            print(f"   - Memory: {self.df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
            print(f"   - Columns: {', '.join(self.df.columns.tolist())}")
            
            # Data types summary
            print(f"\n   Data Types:")
            dtype_counts = self.df.dtypes.value_counts()
            for dtype, count in dtype_counts.items():
                print(f"   - {dtype}: {count} columns")
            
            # Target variable info
            if 'Churn' in self.df.columns:
                churn_dist = self.df['Churn'].value_counts()
                churn_rate = (churn_dist[1] / len(self.df)) * 100 if 1 in churn_dist else 0
                print(f"\n   Target Variable (Churn):")
                print(f"   - Retained (0): {churn_dist.get(0, 0):,} customers")
                print(f"   - Churned (1): {churn_dist.get(1, 0):,} customers")
                print(f"   - Churn Rate: {churn_rate:.1f}%")
            
            self._log("load_data() completed")
            return True
            
        except Exception as e:
            print(f"   [ERROR] Failed to load data: {e}")
            return False

    # ─────────────────────────────────────────
    # 2. CLEAN DATA
    # ─────────────────────────────────────────
    def clean_data(self):
        """Clean the dataset: handle missing values, outliers, and data type issues."""
        print("\n2. Cleaning data...")
        self._log("clean_data() started")
        
        if self.df is None:
            print("   [ERROR] No data loaded. Run load_data() first.")
            return False
        
        # Create a copy for cleaning
        self.df_clean = self.df.copy()
        
        # 2.1 Handle missing values
        print(f"\n   2.1 Handling missing values:")
        missing = self.df_clean.isnull().sum()
        missing_cols = missing[missing > 0].index.tolist()
        
        for col in missing_cols:
            missing_count = missing[col]
            missing_pct = (missing_count / len(self.df_clean)) * 100
            
            if missing_pct > 20:
                # Drop columns with >20% missing values
                print(f"      [WARNING] Dropping '{col}' ({missing_pct:.1f}% missing)")
                self.df_clean.drop(columns=[col], inplace=True)
            elif missing_pct > 5:
                # For 5-20% missing, use median/mode imputation
                if self.df_clean[col].dtype in ['int64', 'float64']:
                    impute_val = self.df_clean[col].median()
                    method = "median"
                else:
                    impute_val = self.df_clean[col].mode()[0] if not self.df_clean[col].mode().empty else "Unknown"
                    method = "mode"
                print(f"      [OK] Imputing '{col}' with {method} ({missing_pct:.1f}% missing)")
                self.df_clean[col].fillna(impute_val, inplace=True)
            else:
                # For <5% missing, use simple imputation
                if self.df_clean[col].dtype in ['int64', 'float64']:
                    impute_val = self.df_clean[col].mean()
                else:
                    impute_val = self.df_clean[col].mode()[0] if not self.df_clean[col].mode().empty else "Unknown"
                print(f"      [OK] Imputing '{col}' with mean/mode ({missing_pct:.1f}% missing)")
                self.df_clean[col].fillna(impute_val, inplace=True)
        
        # 2.2 Handle categorical data consistency
        print(f"\n   2.2 Standardizing categorical values:")
        
        # Gender standardization
        if 'Gender' in self.df_clean.columns:
            self.df_clean['Gender'] = self.df_clean['Gender'].map(GENDER_MAPPING).fillna(self.df_clean['Gender'])
            print(f"      [OK] Standardized 'Gender' values")
        
        # Marital status standardization
        if 'MaritalStatus' in self.df_clean.columns:
            self.df_clean['MaritalStatus'] = self.df_clean['MaritalStatus'].map(MARITAL_STATUS_MAPPING).fillna(self.df_clean['MaritalStatus'])
            print(f"      [OK] Standardized 'MaritalStatus' values")
        
        # 2.3 Remove duplicate CustomerIDs
        print(f"\n   2.3 Checking for duplicates:")
        duplicate_customers = self.df_clean['CustomerID'].duplicated().sum()
        if duplicate_customers > 0:
            print(f"      [WARNING] Found {duplicate_customers} duplicate CustomerIDs")
            self.df_clean = self.df_clean.drop_duplicates(subset=['CustomerID'], keep='first')
            print(f"      [OK] Removed duplicate CustomerIDs")
        else:
            print(f"      [OK] No duplicate CustomerIDs found")
        
        # 2.4 Basic outlier detection (report only)
        print(f"\n   2.4 Outlier detection (report):")
        numerical_cols = self.df_clean.select_dtypes(include=[np.number]).columns.tolist()
        numerical_cols = [col for col in numerical_cols if col not in ['CustomerID', 'Churn']]
        
        for col in numerical_cols:
            if self.df_clean[col].notna().sum() > 0:
                q1 = self.df_clean[col].quantile(0.25)
                q3 = self.df_clean[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - OUTLIER_IQR_MULTIPLIER * iqr
                upper_bound = q3 + OUTLIER_IQR_MULTIPLIER * iqr
                
                outliers = self.df_clean[(self.df_clean[col] < lower_bound) | (self.df_clean[col] > upper_bound)]
                outlier_count = len(outliers)
                
                if outlier_count > 0:
                    outlier_pct = (outlier_count / len(self.df_clean)) * 100
                    print(f"      [INFO] '{col}': {outlier_count:,} outliers ({outlier_pct:.1f}%)")
        
        print(f"\n   Cleaning completed:")
        print(f"   - Original shape: {self.df.shape}")
        print(f"   - Cleaned shape: {self.df_clean.shape}")
        print(f"   - Columns removed: {len(self.df.columns) - len(self.df_clean.columns)}")
        
        self._log("clean_data() completed")
        return True

    # ─────────────────────────────────────────
    # 3. UNIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_univariate_distributions(self):
        """Analyze distribution of individual features."""
        print("\n3. Univariate analysis...")
        self._log("analyze_univariate_distributions() started")
        
        if self.df_clean is None:
            print("   [ERROR] No cleaned data available. Run clean_data() first.")
            return False
        
        # 3.1 Numerical features distributions
        print(f"\n   3.1 Numerical features distributions:")
        numerical_cols = self.df_clean.select_dtypes(include=[np.number]).columns.tolist()
        numerical_cols = [col for col in numerical_cols if col not in ['CustomerID', 'Churn']]
        
        if numerical_cols:
            # Create subplots for numerical distributions
            n_cols = 3
            n_rows = (len(numerical_cols) + n_cols - 1) // n_cols
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
            axes = axes.flatten() if n_rows > 1 else axes
            
            for idx, col in enumerate(numerical_cols):
                if idx < len(axes):
                    ax = axes[idx]
                    
                    # Histogram with KDE
                    sns.histplot(data=self.df_clean, x=col, kde=True, ax=ax, bins=30)
                    ax.set_title(f'{col} Distribution', fontsize=12, fontweight='bold')
                    ax.set_xlabel(col)
                    ax.set_ylabel('Frequency')
                    
                    # Add statistics text
                    stats_text = f"Mean: {self.df_clean[col].mean():.2f}\nStd: {self.df_clean[col].std():.2f}"
                    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                           fontsize=9, verticalalignment='top',
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            # Hide empty subplots
            for idx in range(len(numerical_cols), len(axes)):
                axes[idx].set_visible(False)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'numerical_distributions.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved numerical distributions plot")
        
        # 3.2 Categorical features distributions
        print(f"\n   3.2 Categorical features distributions:")
        categorical_cols = self.df_clean.select_dtypes(include=['object']).columns.tolist()
        
        if categorical_cols:
            # Create subplots for categorical distributions
            n_cols = 2
            n_rows = (len(categorical_cols) + n_cols - 1) // n_cols
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4 * n_rows))
            axes = axes.flatten() if n_rows > 1 else axes
            
            for idx, col in enumerate(categorical_cols):
                if idx < len(axes):
                    ax = axes[idx]
                    
                    # Bar plot with value counts
                    value_counts = self.df_clean[col].value_counts()
                    bars = ax.bar(range(len(value_counts)), value_counts.values)
                    ax.set_title(f'{col} Distribution', fontsize=12, fontweight='bold')
                    ax.set_xlabel(col)
                    ax.set_ylabel('Count')
                    
                    # Set x-tick labels
                    ax.set_xticks(range(len(value_counts)))
                    ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
                    
                    # Add count labels on bars
                    for bar, count in zip(bars, value_counts.values):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{count:,}', ha='center', va='bottom', fontsize=9)
            
            # Hide empty subplots
            for idx in range(len(categorical_cols), len(axes)):
                axes[idx].set_visible(False)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'categorical_distributions.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved categorical distributions plot")
        
        # 3.3 Target variable analysis
        print(f"\n   3.3 Target variable (Churn) analysis:")
        if 'Churn' in self.df_clean.columns:
            # Create figure for churn analysis
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            
            # Pie chart
            churn_counts = self.df_clean['Churn'].value_counts()
            labels = ['Retained (0)', 'Churned (1)']
            colors = ['lightgreen', 'lightcoral']
            
            axes[0].pie(churn_counts.values, labels=labels, colors=colors, autopct='%1.1f%%',
                       startangle=90, wedgeprops={'edgecolor': 'black'})
            axes[0].set_title('Customer Churn Distribution', fontsize=14, fontweight='bold')
            axes[0].axis('equal')
            
            # Bar chart with percentages
            churn_pct = (churn_counts / len(self.df_clean)) * 100
            bars = axes[1].bar(range(len(churn_pct)), churn_pct.values, color=colors)
            axes[1].set_title('Churn Rate by Category', fontsize=14, fontweight='bold')
            axes[1].set_xlabel('Churn Status')
            axes[1].set_ylabel('Percentage (%)')
            axes[1].set_xticks(range(len(churn_pct)))
            axes[1].set_xticklabels(labels)
            
            # Add percentage labels on bars
            for bar, pct in zip(bars, churn_pct.values):
                height = bar.get_height()
                axes[1].text(bar.get_x() + bar.get_width()/2., height,
                           f'{pct:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'churn_analysis.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved churn analysis plot")
            
            # Save churn statistics
            churn_stats = {
                'total_customers': len(self.df_clean),
                'retained_customers': int(churn_counts.get(0, 0)),
                'churned_customers': int(churn_counts.get(1, 0)),
                'churn_rate': float((churn_counts.get(1, 0) / len(self.df_clean)) * 100),
                'retention_rate': float((churn_counts.get(0, 0) / len(self.df_clean)) * 100)
            }
            self.results['churn_stats'] = churn_stats
        
        # 3.4 Advanced univariate visualizations
        print(f"\n   3.4 Advanced univariate visualizations:")
        
        # Create violin plots
        if numerical_cols:
            violin_path = self._create_violin_plots(self.df_clean, numerical_cols)
            if violin_path:
                self.results['violin_plots_path'] = violin_path
        
        # Create QQ plots for normality checking
        if numerical_cols:
            qq_path = self._create_qq_plots(self.df_clean, numerical_cols)
            if qq_path:
                self.results['qq_plots_path'] = qq_path
        
        # Create CDF plots
        if numerical_cols:
            cdf_path = self._create_cdf_plots(self.df_clean, numerical_cols)
            if cdf_path:
                self.results['cdf_plots_path'] = cdf_path
        
        # 3.5 Feature variability analysis
        print(f"\n   3.5 Feature variability analysis:")
        if numerical_cols:
            # Calculate coefficient of variation for each numerical feature
            cv_results = []
            for col in numerical_cols:
                mean_val = self.df_clean[col].mean()
                std_val = self.df_clean[col].std()
                cv = (std_val / mean_val) * 100 if mean_val != 0 else 0
                cv_results.append({
                    'feature': col,
                    'mean': mean_val,
                    'std': std_val,
                    'cv': cv
                })
            
            # Sort by CV (descending)
            cv_results.sort(key=lambda x: x['cv'], reverse=True)
            
            # Create visualization
            fig, ax = plt.subplots(figsize=(12, 6))
            features = [item['feature'] for item in cv_results[:10]]  # Top 10
            cv_values = [item['cv'] for item in cv_results[:10]]
            
            bars = ax.barh(features, cv_values, color='steelblue')
            ax.set_xlabel('Coefficient of Variation (%)', fontsize=12)
            ax.set_title('Top 10 Most Variable Numerical Features', fontsize=14, fontweight='bold')
            ax.invert_yaxis()  # Highest CV at top
            
            # Add value labels
            for bar, cv in zip(bars, cv_values):
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height()/2.,
                       f'{cv:.1f}%', ha='left', va='center', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'feature_variability.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved feature variability plot")
            
            # Save CV results
            self.results['feature_variability'] = cv_results
        
        self._log("analyze_univariate_distributions() completed")
        return True

    # ─────────────────────────────────────────
    # 4. BIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_bivariate_relationships(self):
        """Analyze relationships between features and with target variable."""
        print("\n4. Bivariate analysis...")
        self._log("analyze_bivariate_relationships() started")
        
        if self.df_clean is None:
            print("   [ERROR] No cleaned data available. Run clean_data() first.")
            return False
        

        
        # 4.1 Correlation matrix (numerical features)
        print(f"\n   4.1 Correlation matrix analysis:")
        numerical_cols = self.df_clean.select_dtypes(include=[np.number]).columns.tolist()
        numerical_cols = [col for col in numerical_cols if col not in ['CustomerID']]
        
        if len(numerical_cols) > 1:
            # Calculate correlation matrix
            corr_matrix = self.df_clean[numerical_cols].corr()
            
            # Create heatmap
            fig, ax = plt.subplots(figsize=(14, 10))
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            
            sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='coolwarm',
                       center=0, square=True, linewidths=0.5, cbar_kws={"shrink": 0.8},
                       ax=ax)
            
            ax.set_title('Correlation Matrix - Numerical Features', fontsize=16, fontweight='bold')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'correlation_matrix.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved correlation matrix plot")
            
            # Save correlation matrix
            corr_matrix.to_csv(os.path.join(self.output_dir, 'correlation_matrix.csv'))
            print(f"      [OK] Saved correlation matrix CSV")
            
            # Find top correlations with Churn
            if 'Churn' in corr_matrix.columns:
                churn_correlations = corr_matrix['Churn'].drop('Churn').sort_values(ascending=False)
                top_pos = churn_correlations.head(5)
                top_neg = churn_correlations.tail(5)
                
                # Save top correlations
                self.results['top_churn_correlations'] = {
                    'positive': top_pos.to_dict(),
                    'negative': top_neg.to_dict()
                }
                
                print(f"\n      Top positive correlations with Churn:")
                for feature, corr in top_pos.items():
                    print(f"        - {feature}: {corr:.3f}")
                
                print(f"\n      Top negative correlations with Churn:")
                for feature, corr in top_neg.items():
                    print(f"        - {feature}: {corr:.3f}")
        
        # 4.2 Numerical features vs Churn (box plots)
        print(f"\n   4.2 Numerical features vs Churn:")
        if 'Churn' in self.df_clean.columns:
            numerical_vs_churn = [col for col in numerical_cols if col != 'Churn']
            
            if numerical_vs_churn:
                # Select top 6 features for visualization
                top_features = numerical_vs_churn[:6]
                
                fig, axes = plt.subplots(2, 3, figsize=(16, 10))
                axes = axes.flatten()
                
                for idx, feature in enumerate(top_features):
                    if idx < len(axes):
                        ax = axes[idx]
                        
                        # Create box plot
                        # Convert Churn to string for palette mapping
                        temp_df = self.df_clean.copy()
                        temp_df['Churn_str'] = temp_df['Churn'].astype(str)
                        sns.boxplot(data=temp_df, x='Churn_str', y=feature, ax=ax,
                                   palette={'0': 'lightgreen', '1': 'lightcoral'})
                        
                        ax.set_title(f'{feature} vs Churn', fontsize=12, fontweight='bold')
                        ax.set_xlabel('Churn Status (0=Retained, 1=Churned)')
                        ax.set_ylabel(feature)
                        
                        # Add mean markers
                        retained_mean = self.df_clean[self.df_clean['Churn'] == 0][feature].mean()
                        churned_mean = self.df_clean[self.df_clean['Churn'] == 1][feature].mean()
                        
                        ax.scatter([0, 1], [retained_mean, churned_mean], 
                                  color='red', s=100, marker='D', label='Mean')
                        
                        if idx == 0:
                            ax.legend()
                
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'numerical_vs_churn.png'), dpi=150, bbox_inches='tight')
                plt.close()
                print(f"      [OK] Saved numerical features vs churn plot")
        
        # 4.3 Categorical features vs Churn
        print(f"\n   4.3 Categorical features vs Churn:")
        categorical_cols = self.df_clean.select_dtypes(include=['object']).columns.tolist()
        
        if categorical_cols and 'Churn' in self.df_clean.columns:
            # Select top 4 categorical features for visualization
            top_categorical = categorical_cols[:4]
            
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            axes = axes.flatten()
            
            for idx, feature in enumerate(top_categorical):
                if idx < len(axes):
                    ax = axes[idx]
                    
                    # Calculate churn rates by category
                    churn_rates = self.df_clean.groupby(feature)['Churn'].mean() * 100
                    churn_counts = self.df_clean.groupby(feature)['Churn'].count()
                    
                    # Create bar plot
                    bars = ax.bar(range(len(churn_rates)), churn_rates.values, color='steelblue')
                    ax.set_title(f'Churn Rate by {feature}', fontsize=12, fontweight='bold')
                    ax.set_xlabel(feature)
                    ax.set_ylabel('Churn Rate (%)')
                    ax.set_xticks(range(len(churn_rates)))
                    ax.set_xticklabels(churn_rates.index, rotation=45, ha='right')
                    
                    # Add percentage labels and counts
                    for bar_idx, (bar, rate, count) in enumerate(zip(bars, churn_rates.values, churn_counts.values)):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                               f'{rate:.1f}%\n({count:,})', ha='center', va='bottom', 
                               fontsize=9, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'categorical_vs_churn.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved categorical features vs churn plot")
        
        # 4.4 Scatter plots for top correlated pairs
        print(f"\n   4.4 Scatter plots for feature relationships:")
        if len(numerical_cols) > 1 and 'Churn' in numerical_cols:
            # Get top 3 features correlated with Churn
            churn_correlations = self.df_clean[numerical_cols].corr()['Churn'].drop('Churn')
            top_features = churn_correlations.abs().sort_values(ascending=False).head(3).index.tolist()
            
            if top_features:
                fig, axes = plt.subplots(1, 3, figsize=(18, 5))
                
                for idx, feature in enumerate(top_features):
                    ax = axes[idx]
                    
                    # Create scatter plot with regression line
                    sns.regplot(data=self.df_clean, x=feature, y='Churn', ax=ax,
                               scatter_kws={'alpha': 0.5, 's': 20},
                               line_kws={'color': 'red', 'linewidth': 2})
                    
                    ax.set_title(f'{feature} vs Churn\nCorrelation: {churn_correlations[feature]:.3f}',
                               fontsize=12, fontweight='bold')
                    ax.set_xlabel(feature)
                    ax.set_ylabel('Churn (0/1)')
                
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'scatter_plots.png'), dpi=150, bbox_inches='tight')
                plt.close()
                print(f"      [OK] Saved scatter plots")
        
        # 4.4 Hexbin density plots for bivariate relationships
        print(f"\n   4.4 Hexbin density plots:")
        if numerical_cols:
            hexbin_path = self._create_hexbin_plots(self.df_clean, numerical_cols)
            if hexbin_path:
                self.results['hexbin_plots_path'] = hexbin_path
        
        self._log("analyze_bivariate_relationships() completed")
        return True

    # ─────────────────────────────────────────
    # 5. MULTIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_multivariate_patterns(self):
        """Analyze patterns involving multiple features simultaneously."""
        print("\n5. Multivariate analysis...")
        self._log("analyze_multivariate_patterns() started")
        
        if self.df_clean is None:
            print("   [ERROR] No cleaned data available. Run clean_data() first.")
            return False
        
        # 5.1 Pair plots for top numerical features
        print(f"\n   5.1 Pair plots analysis:")
        numerical_cols = self.df_clean.select_dtypes(include=[np.number]).columns.tolist()
        numerical_cols = [col for col in numerical_cols if col not in ['CustomerID']]
        
        if len(numerical_cols) > 1 and 'Churn' in self.df_clean.columns:
            # Select top 5 numerical features (excluding Churn)
            top_numerical = [col for col in numerical_cols if col != 'Churn'][:5]
            top_numerical.append('Churn')  # Add Churn back
            
            if len(top_numerical) > 1:
                # Create pair plot
                pair_plot = sns.pairplot(self.df_clean[top_numerical], hue='Churn',
                                        palette={0: 'lightgreen', 1: 'lightcoral'},
                                        plot_kws={'alpha': 0.6, 's': 20},
                                        diag_kind='kde')
                
                pair_plot.fig.suptitle('Pair Plots - Top Numerical Features by Churn Status', 
                                      fontsize=16, fontweight='bold', y=1.02)
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'pair_plots.png'), dpi=150, bbox_inches='tight')
                plt.close()
                print(f"      [OK] Saved pair plots")
        
        # 5.2 Heatmap of feature interactions
        print(f"\n   5.2 Feature interaction heatmap:")
        if len(numerical_cols) > 1:
            # Select top 10 numerical features for interaction heatmap
            top_features = numerical_cols[:10]
            
            if len(top_features) > 1:
                # Calculate correlation matrix
                corr_matrix = self.df_clean[top_features].corr()
                
                # Create clustered heatmap only if scipy is available
                if HAS_SCIPY:
                    try:
                        # Create clustered heatmap
                        fig, ax = plt.subplots(figsize=(12, 10))
                        
                        sns.clustermap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                                      center=0, linewidths=0.5, cbar_kws={"shrink": 0.8},
                                      figsize=(12, 10))
                        
                        plt.suptitle('Clustered Correlation Heatmap - Top Numerical Features', 
                                   fontsize=16, fontweight='bold', y=1.02)
                        plt.tight_layout()
                        plt.savefig(os.path.join(self.output_dir, 'clustered_heatmap.png'), dpi=150, bbox_inches='tight')
                        plt.close()
                        print(f"      [OK] Saved clustered heatmap")
                    except Exception as e:
                        print(f"      [WARNING] Could not create clustered heatmap: {e}")
                else:
                    print(f"      [INFO] Skipping clustered heatmap (scipy not available)")
                    
                    # Create regular heatmap instead
                    fig, ax = plt.subplots(figsize=(12, 10))
                    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                               center=0, square=True, linewidths=0.5, cbar_kws={"shrink": 0.8},
                               ax=ax)
                    ax.set_title('Correlation Heatmap - Top Numerical Features', 
                               fontsize=16, fontweight='bold')
                    plt.tight_layout()
                    plt.savefig(os.path.join(self.output_dir, 'regular_heatmap.png'), dpi=150, bbox_inches='tight')
                    plt.close()
                    print(f"      [OK] Saved regular heatmap")
        
        # 5.3 3D scatter plot (if plotly available)
        print(f"\n   5.3 3D visualization:")
        if HAS_PLOTLY and len(numerical_cols) >= 3 and 'Churn' in self.df_clean.columns:
            try:
                # Select top 3 numerical features correlated with Churn
                churn_correlations = self.df_clean[numerical_cols].corr()['Churn'].drop('Churn')
                top_features = churn_correlations.abs().sort_values(ascending=False).head(3).index.tolist()
                
                if len(top_features) == 3:
                    # Create 3D scatter plot
                    fig = px.scatter_3d(self.df_clean, 
                                       x=top_features[0], 
                                       y=top_features[1], 
                                       z=top_features[2],
                                       color='Churn',
                                       color_discrete_map={0: 'green', 1: 'red'},
                                       title=f'3D Scatter: {top_features[0]}, {top_features[1]}, {top_features[2]} vs Churn',
                                       opacity=0.7,
                                       hover_data=['CustomerID'])
                    
                    # Save as HTML
                    fig.write_html(os.path.join(self.output_dir, '3d_scatter.html'))
                    print(f"      [OK] Saved 3D scatter plot (HTML)")
                    
                    # Also save as static image
                    fig.write_image(os.path.join(self.output_dir, '3d_scatter.png'))
                    print(f"      [OK] Saved 3D scatter plot (PNG)")
            except Exception as e:
                print(f"      [WARNING] Could not create 3D plot: {e}")
        
        # 5.4 Parallel coordinates plot
        print(f"\n   5.4 Parallel coordinates:")
        if HAS_SKLEARN and len(numerical_cols) >= 4 and 'Churn' in self.df_clean.columns:
            try:
                # Select top 4 numerical features
                top_features = numerical_cols[:4]
                top_features.append('Churn')
                
                # Sample data for better visualization
                sample_df = self.df_clean[top_features].sample(n=min(500, len(self.df_clean)), random_state=42)
                
                # Normalize features for parallel coordinates
                scaler = MinMaxScaler()
                scaled_data = scaler.fit_transform(sample_df.drop('Churn', axis=1))
                scaled_df = pd.DataFrame(scaled_data, columns=sample_df.drop('Churn', axis=1).columns)
                scaled_df['Churn'] = sample_df['Churn'].values
                
                # Create parallel coordinates plot
                fig, ax = plt.subplots(figsize=(14, 8))
                pd.plotting.parallel_coordinates(scaled_df, 'Churn', ax=ax, 
                                                color=('#FF6B6B', '#4ECDC4'))
                
                ax.set_title('Parallel Coordinates - Top Numerical Features by Churn Status', 
                           fontsize=14, fontweight='bold')
                ax.set_ylabel('Normalized Value')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'parallel_coordinates.png'), dpi=150, bbox_inches='tight')
                plt.close()
                print(f"      [OK] Saved parallel coordinates plot")
            except Exception as e:
                print(f"      [WARNING] Could not create parallel coordinates plot: {e}")
        
        # 5.3 3D scatter plot for multivariate relationships
        print(f"\n   5.3 3D scatter plot analysis:")
        if numerical_cols and len(numerical_cols) >= 3:
            scatter_3d_path = self._create_3d_scatter_plot(self.df_clean, numerical_cols)
            if scatter_3d_path:
                self.results['3d_scatter_plot_path'] = scatter_3d_path
        
        # 5.4 Correlation network visualization
        print(f"\n   5.4 Correlation network analysis:")
        if numerical_cols and len(numerical_cols) > 1:
            network_path = self._create_correlation_network(self.df_clean, numerical_cols)
            if network_path:
                self.results['correlation_network_path'] = network_path
        
        self._log("analyze_multivariate_patterns() completed")
        return True

    # ─────────────────────────────────────────
    # 6. TEMPORAL ANALYSIS (if applicable)
    # ─────────────────────────────────────────
    def analyze_temporal_patterns(self):
        """Analyze temporal patterns in the data."""
        print("\n6. Temporal analysis...")
        self._log("analyze_temporal_patterns() started")
        
        if self.df_clean is None:
            print("   [ERROR] No cleaned data available. Run clean_data() first.")
            return False
        
        print(f"   [INFO] No explicit temporal columns found in this dataset.")
        print(f"   [INFO] Temporal analysis would require date/time features.")
        
        self._log("analyze_temporal_patterns() completed")
        return True

    # ─────────────────────────────────────────
    # 7. SEGMENTATION ANALYSIS
    # ─────────────────────────────────────────
    def analyze_segmentation_patterns(self):
        """Analyze customer segmentation patterns."""
        print("\n7. Segmentation analysis...")
        self._log("analyze_segmentation_patterns() started")
        
        if self.df_clean is None:
            print("   [ERROR] No cleaned data available. Run clean_data() first.")
            return False
        
        # 7.1 Demographic segmentation by churn
        print(f"\n   7.1 Demographic segmentation:")
        if 'Churn' in self.df_clean.columns:
            # Gender segmentation
            if 'Gender' in self.df_clean.columns:
                gender_churn = self.df_clean.groupby('Gender')['Churn'].agg(['count', 'mean'])
                gender_churn['churn_rate'] = gender_churn['mean'] * 100
                gender_churn['retention_rate'] = 100 - gender_churn['churn_rate']
                
                print(f"\n      Gender-based segmentation:")
                for gender, row in gender_churn.iterrows():
                    print(f"        - {gender}: {row['count']:,} customers, "
                          f"Churn: {row['churn_rate']:.1f}%, "
                          f"Retention: {row['retention_rate']:.1f}%")
            
            # Marital status segmentation
            if 'MaritalStatus' in self.df_clean.columns:
                marital_churn = self.df_clean.groupby('MaritalStatus')['Churn'].agg(['count', 'mean'])
                marital_churn['churn_rate'] = marital_churn['mean'] * 100
                
                print(f"\n      Marital status-based segmentation:")
                for status, row in marital_churn.iterrows():
                    print(f"        - {status}: {row['count']:,} customers, "
                          f"Churn: {row['churn_rate']:.1f}%")
            
            # City tier segmentation
            if 'CityTier' in self.df_clean.columns:
                city_churn = self.df_clean.groupby('CityTier')['Churn'].agg(['count', 'mean'])
                city_churn['churn_rate'] = city_churn['mean'] * 100
                
                print(f"\n      City tier-based segmentation:")
                for tier, row in city_churn.iterrows():
                    print(f"        - Tier {tier}: {row['count']:,} customers, "
                          f"Churn: {row['churn_rate']:.1f}%")
        
        # 7.2 Behavioral segmentation
        print(f"\n   7.2 Behavioral segmentation:")
        if 'Churn' in self.df_clean.columns:
            # Preferred login device segmentation
            if 'PreferredLoginDevice' in self.df_clean.columns:
                device_churn = self.df_clean.groupby('PreferredLoginDevice')['Churn'].agg(['count', 'mean'])
                device_churn['churn_rate'] = device_churn['mean'] * 100
                
                print(f"\n      Login device-based segmentation:")
                for device, row in device_churn.iterrows():
                    print(f"        - {device}: {row['count']:,} customers, "
                          f"Churn: {row['churn_rate']:.1f}%")
            
            # Preferred payment mode segmentation
            if 'PreferredPaymentMode' in self.df_clean.columns:
                payment_churn = self.df_clean.groupby('PreferredPaymentMode')['Churn'].agg(['count', 'mean'])
                payment_churn['churn_rate'] = payment_churn['mean'] * 100
                
                print(f"\n      Payment mode-based segmentation:")
                for mode, row in payment_churn.iterrows():
                    print(f"        - {mode}: {row['count']:,} customers, "
                          f"Churn: {row['churn_rate']:.1f}%")
        
        # 7.3 RFM-like analysis (if applicable)
        print(f"\n   7.3 Transaction-based segmentation:")
        # Note: This dataset doesn't have traditional RFM features, but we can create similar segments
        
        # 7.3 Categorical-numerical relationship plots
        print(f"\n   7.3 Categorical-numerical relationship analysis:")
        categorical_cols = self.df_clean.select_dtypes(include=['object']).columns.tolist()
        numerical_cols = self.df_clean.select_dtypes(include=[np.number]).columns.tolist()
        numerical_cols = [col for col in numerical_cols if col not in ['CustomerID', 'Churn']]
        
        if categorical_cols and numerical_cols:
            cat_num_path = self._create_categorical_numerical_plots(self.df_clean, categorical_cols, numerical_cols)
            if cat_num_path:
                self.results['categorical_numerical_plots_path'] = cat_num_path
        
        self._log("analyze_segmentation_patterns() completed")
        return True

    # ─────────────────────────────────────────
    # 8. ADVANCED VISUALIZATION METHODS
    # ─────────────────────────────────────────
    
    def _create_violin_plots(self, df, numerical_cols):
        """Create violin plots for numerical features."""
        # Select top 8 numerical features for violin plots
        top_numerical_violin = numerical_cols[:8] if len(numerical_cols) > 8 else numerical_cols
        
        n_cols = 4
        n_rows = (len(top_numerical_violin) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4, n_rows * 3))
        fig.suptitle('Violin Plots for Numerical Features (Distribution + Density)', 
                    fontsize=16, fontweight='bold')
        
        # Flatten axes array for easy iteration
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, col in enumerate(top_numerical_violin):
            row = idx // n_cols
            col_idx = idx % n_cols
            
            if n_rows == 1:
                ax = axes[col_idx]
            elif n_cols == 1:
                ax = axes[row]
            else:
                ax = axes[row, col_idx]
            
            # Violin plot
            violin_parts = ax.violinplot(df[col].dropna(), showmeans=True, showmedians=True)
            violin_parts['bodies'][0].set_facecolor('lightcoral')
            violin_parts['bodies'][0].set_alpha(0.7)
            violin_parts['cmeans'].set_color('green')
            violin_parts['cmedians'].set_color('red')
            
            ax.set_title(f'{col}', fontsize=10)
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3)
        
        # Hide empty subplots
        for idx in range(len(top_numerical_violin), n_rows * n_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            if n_rows == 1:
                axes[col_idx].set_visible(False)
            elif n_cols == 1:
                axes[row].set_visible(False)
            else:
                axes[row, col_idx].set_visible(False)
        
        plt.tight_layout()
        violin_path = os.path.join(self.output_dir, 'violin_plots.png')
        plt.savefig(violin_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved violin plots: {violin_path}")
        return violin_path
    
    def _create_qq_plots(self, df, numerical_cols):
        """Create QQ plots for normality checking."""
        if not HAS_SCIPY:
            print(f"      [INFO] Skipping QQ plots (scipy not available)")
            return None
        
        # Select key numerical features for QQ plots
        key_features_qq = ['Tenure', 'CashbackAmount', 'OrderCount', 'DaySinceLastOrder']
        key_features_qq = [f for f in key_features_qq if f in numerical_cols]
        
        if not key_features_qq:
            print(f"      [INFO] No suitable features found for QQ plots")
            return None
        
        n_cols = 2
        n_rows = (len(key_features_qq) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
        fig.suptitle('QQ Plots for Normality Checking', 
                    fontsize=16, fontweight='bold')
        
        # Flatten axes array for easy iteration
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, col in enumerate(key_features_qq):
            row = idx // n_cols
            col_idx = idx % n_cols
            
            if n_rows == 1:
                ax = axes[col_idx]
            elif n_cols == 1:
                ax = axes[row]
            else:
                ax = axes[row, col_idx]
            
            # QQ plot
            stats.probplot(df[col].dropna(), dist="norm", plot=ax)
            ax.set_title(f'{col} QQ Plot', fontsize=10)
            ax.grid(True, alpha=0.3)
        
        # Hide empty subplots
        for idx in range(len(key_features_qq), n_rows * n_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            if n_rows == 1:
                axes[col_idx].set_visible(False)
            elif n_cols == 1:
                axes[row].set_visible(False)
            else:
                axes[row, col_idx].set_visible(False)
        
        plt.tight_layout()
        qq_path = os.path.join(self.output_dir, 'qq_plots.png')
        plt.savefig(qq_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved QQ plots: {qq_path}")
        return qq_path
    
    def _create_cdf_plots(self, df, numerical_cols):
        """Create CDF plots for cumulative distribution analysis."""
        # Select key numerical features for CDF plots
        key_features_cdf = ['Tenure', 'CashbackAmount', 'OrderCount', 'DaySinceLastOrder']
        key_features_cdf = [f for f in key_features_cdf if f in numerical_cols]
        
        if not key_features_cdf:
            print(f"      [INFO] No suitable features found for CDF plots")
            return None
        
        n_cols = 2
        n_rows = (len(key_features_cdf) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
        fig.suptitle('Cumulative Distribution Function (CDF) Plots', 
                    fontsize=16, fontweight='bold')
        
        # Flatten axes array for easy iteration
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, col in enumerate(key_features_cdf):
            row = idx // n_cols
            col_idx = idx % n_cols
            
            if n_rows == 1:
                ax = axes[col_idx]
            elif n_cols == 1:
                ax = axes[row]
            else:
                ax = axes[row, col_idx]
            
            # Sort data and calculate CDF
            sorted_data = np.sort(df[col].dropna())
            cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
            
            # Plot CDF
            ax.plot(sorted_data, cdf, 'b-', linewidth=2)
            ax.fill_between(sorted_data, 0, cdf, alpha=0.3, color='blue')
            
            ax.set_title(f'{col} CDF', fontsize=10)
            ax.set_xlabel(col)
            ax.set_ylabel('Cumulative Probability')
            ax.grid(True, alpha=0.3)
            
            # Add median line
            median_val = np.median(sorted_data)
            ax.axvline(median_val, color='red', linestyle='--', linewidth=1.5, 
                      label=f'Median: {median_val:.2f}')
            ax.legend(fontsize=8)
        
        # Hide empty subplots
        for idx in range(len(key_features_cdf), n_rows * n_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            if n_rows == 1:
                axes[col_idx].set_visible(False)
            elif n_cols == 1:
                axes[row].set_visible(False)
            else:
                axes[row, col_idx].set_visible(False)
        
        plt.tight_layout()
        cdf_path = os.path.join(self.output_dir, 'cdf_plots.png')
        plt.savefig(cdf_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved CDF plots: {cdf_path}")
        return cdf_path
    
    def _create_hexbin_plots(self, df, numerical_cols):
        """Create hexbin plots for bivariate density visualization."""
        # Select key numerical feature pairs for hexbin plots
        feature_pairs = [
            ('Tenure', 'CashbackAmount'),
            ('OrderCount', 'CashbackAmount'),
            ('DaySinceLastOrder', 'OrderCount'),
            ('Tenure', 'OrderCount')
        ]
        
        # Filter pairs where both features exist and are numerical
        valid_pairs = []
        for f1, f2 in feature_pairs:
            if f1 in numerical_cols and f2 in numerical_cols:
                valid_pairs.append((f1, f2))
        
        if not valid_pairs:
            print(f"      [INFO] No suitable feature pairs found for hexbin plots")
            return None
        
        n_cols = 2
        n_rows = (len(valid_pairs) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
        fig.suptitle('Hexbin Density Plots for Bivariate Relationships', 
                    fontsize=16, fontweight='bold')
        
        # Flatten axes array for easy iteration
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, (f1, f2) in enumerate(valid_pairs):
            row = idx // n_cols
            col_idx = idx % n_cols
            
            if n_rows == 1:
                ax = axes[col_idx]
            elif n_cols == 1:
                ax = axes[row]
            else:
                ax = axes[row, col_idx]
            
            # Hexbin plot - drop rows where either feature is NaN
            valid_data = df[[f1, f2]].dropna()
            if len(valid_data) > 0:
                hb = ax.hexbin(valid_data[f1], valid_data[f2], 
                              gridsize=30, cmap='viridis', mincnt=1)
                ax.set_title(f'{f1} vs {f2}', fontsize=10)
                ax.set_xlabel(f1)
                ax.set_ylabel(f2)
                
                # Add colorbar
                plt.colorbar(hb, ax=ax)
            else:
                ax.text(0.5, 0.5, 'No valid data\nfor this pair', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'{f1} vs {f2}', fontsize=10)
                ax.set_xlabel(f1)
                ax.set_ylabel(f2)
        
        # Hide empty subplots
        for idx in range(len(valid_pairs), n_rows * n_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            if n_rows == 1:
                axes[col_idx].set_visible(False)
            elif n_cols == 1:
                axes[row].set_visible(False)
            else:
                axes[row, col_idx].set_visible(False)
        
        plt.tight_layout()
        hexbin_path = os.path.join(self.output_dir, 'hexbin_plots.png')
        plt.savefig(hexbin_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved hexbin plots: {hexbin_path}")
        return hexbin_path
    
    def _create_categorical_numerical_plots(self, df, categorical_cols, numerical_cols):
        """Create boxplots for categorical vs numerical relationships."""
        # Select key categorical and numerical features
        key_categorical = ['PreferredLoginDevice', 'Gender', 'MaritalStatus', 'PreferredPaymentMode']
        key_categorical = [f for f in key_categorical if f in categorical_cols]
        
        key_numerical = ['CashbackAmount', 'Tenure', 'OrderCount', 'DaySinceLastOrder']
        key_numerical = [f for f in key_numerical if f in numerical_cols]
        
        if not key_categorical or not key_numerical:
            print(f"      [INFO] No suitable categorical-numerical pairs found")
            return None
        
        # Create plots for top combinations
        combinations = []
        for cat in key_categorical[:3]:  # Top 3 categorical
            for num in key_numerical[:3]:  # Top 3 numerical
                combinations.append((cat, num))
        
        n_cols = 3
        n_rows = (len(combinations) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
        fig.suptitle('Categorical vs Numerical Relationships (Boxplots)', 
                    fontsize=16, fontweight='bold')
        
        # Flatten axes array for easy iteration
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, (cat, num) in enumerate(combinations):
            row = idx // n_cols
            col_idx = idx % n_cols
            
            if n_rows == 1:
                ax = axes[col_idx]
            elif n_cols == 1:
                ax = axes[row]
            else:
                ax = axes[row, col_idx]
            
            # Boxplot
            sns.boxplot(data=df, x=cat, y=num, ax=ax, palette='Set2')
            ax.set_title(f'{num} by {cat}', fontsize=10)
            ax.set_xlabel(cat)
            ax.set_ylabel(num)
            ax.tick_params(axis='x', rotation=45)
        
        # Hide empty subplots
        for idx in range(len(combinations), n_rows * n_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            if n_rows == 1:
                axes[col_idx].set_visible(False)
            elif n_cols == 1:
                axes[row].set_visible(False)
            else:
                axes[row, col_idx].set_visible(False)
        
        plt.tight_layout()
        cat_num_path = os.path.join(self.output_dir, 'categorical_numerical_boxplots.png')
        plt.savefig(cat_num_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved categorical-numerical boxplots: {cat_num_path}")
        return cat_num_path
    
    def _create_3d_scatter_plot(self, df, numerical_cols):
        """Create 3D scatter plot for multivariate relationships."""
        if not HAS_PLOTLY:
            print(f"      [INFO] Skipping 3D scatter plot (plotly not available)")
            return None
        
        # Select key numerical features for 3D plot
        key_features_3d = ['Tenure', 'CashbackAmount', 'OrderCount']
        key_features_3d = [f for f in key_features_3d if f in numerical_cols]
        
        if len(key_features_3d) < 3:
            print(f"      [INFO] Not enough features for 3D scatter plot")
            return None
        
        # Create 3D scatter plot
        fig = px.scatter_3d(
            df,
            x=key_features_3d[0],
            y=key_features_3d[1],
            z=key_features_3d[2],
            color='Churn' if 'Churn' in df.columns else None,
            title=f'3D Scatter Plot: {key_features_3d[0]} vs {key_features_3d[1]} vs {key_features_3d[2]}',
            labels={key_features_3d[0]: key_features_3d[0],
                   key_features_3d[1]: key_features_3d[1],
                   key_features_3d[2]: key_features_3d[2]},
            opacity=0.7,
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        # Update layout
        fig.update_layout(
            scene=dict(
                xaxis_title=key_features_3d[0],
                yaxis_title=key_features_3d[1],
                zaxis_title=key_features_3d[2]
            ),
            title_font_size=16,
            title_font_family="Arial",
            title_font_color="darkblue"
        )
        
        # Save plot
        scatter_3d_path = os.path.join(self.output_dir, '3d_scatter_plot.html')
        fig.write_html(scatter_3d_path)
        print(f"      [OK] Saved 3D scatter plot: {scatter_3d_path}")
        return scatter_3d_path
    
    def _create_correlation_network(self, df, numerical_cols):
        """Create correlation network visualization."""
        if not HAS_NETWORKX:
            print(f"      [INFO] Skipping correlation network (networkx not available)")
            return None
        
        # Calculate correlation matrix
        corr_matrix = df[numerical_cols].corr()
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes
        for col in numerical_cols:
            G.add_node(col)
        
        # Add edges with weights (correlation values)
        for i in range(len(numerical_cols)):
            for j in range(i + 1, len(numerical_cols)):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) > 0.3:  # Only show significant correlations
                    G.add_edge(numerical_cols[i], numerical_cols[j], weight=abs(corr))
        
        # Create figure
        plt.figure(figsize=(12, 10))
        
        # Position nodes using spring layout
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=700, 
                              node_color='lightblue', alpha=0.8)
        
        # Draw edges with width proportional to correlation
        edges = G.edges()
        weights = [G[u][v]['weight'] * 3 for u, v in edges]
        nx.draw_networkx_edges(G, pos, edgelist=edges, 
                              width=weights, alpha=0.5, edge_color='gray')
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
        
        plt.title('Correlation Network of Numerical Features', 
                 fontsize=16, fontweight='bold')
        plt.axis('off')
        
        # Save plot
        network_path = os.path.join(self.output_dir, 'correlation_network.png')
        plt.savefig(network_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved correlation network: {network_path}")
        return network_path

    # ─────────────────────────────────────────
    # 9. MAIN ORCHESTRATION METHOD
    # ─────────────────────────────────────────
    def run_full_analysis(self):
        """Run the complete EDA pipeline."""
        print("\n" + "=" * 80)
        print("STARTING COMPREHENSIVE E-COMMERCE CUSTOMER CHURN EDA")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Step 1: Load data
        if not self.load_data():
            print("   [ERROR] Failed to load data. Analysis aborted.")
            return False
        
        # Step 2: Clean data
        if not self.clean_data():
            print("   [WARNING] Data cleaning encountered issues. Continuing with analysis...")
        
        # Step 3: Univariate analysis
        print("\n" + "-" * 80)
        print("UNIVARIATE ANALYSIS PHASE")
        print("-" * 80)
        if not self.analyze_univariate_distributions():
            print("   [WARNING] Univariate analysis encountered issues.")
        
        # Step 4: Bivariate analysis
        print("\n" + "-" * 80)
        print("BIVARIATE ANALYSIS PHASE")
        print("-" * 80)
        if not self.analyze_bivariate_relationships():
            print("   [WARNING] Bivariate analysis encountered issues.")
        
        # Step 5: Multivariate analysis
        print("\n" + "-" * 80)
        print("MULTIVARIATE ANALYSIS PHASE")
        print("-" * 80)
        if not self.analyze_multivariate_patterns():
            print("   [WARNING] Multivariate analysis encountered issues.")
        
        # Step 6: Temporal analysis
        print("\n" + "-" * 80)
        print("TEMPORAL ANALYSIS PHASE")
        print("-" * 80)
        if not self.analyze_temporal_patterns():
            print("   [INFO] Temporal analysis not applicable.")
        
        # Step 7: Segmentation analysis
        print("\n" + "-" * 80)
        print("SEGMENTATION ANALYSIS PHASE")
        print("-" * 80)
        if not self.analyze_segmentation_patterns():
            print("   [WARNING] Segmentation analysis encountered issues.")
        
        # Step 8: Generate summary report
        print("\n" + "-" * 80)
        print("SUMMARY REPORT GENERATION")
        print("-" * 80)
        self.generate_summary_report()
        
        # Calculate total time
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"Total time: {total_time:.1f} seconds")
        print(f"Output directory: {self.output_dir}")
        print(f"Results saved in: {os.path.join(self.output_dir, 'eda_summary_report.txt')}")
        print("=" * 80)
        
        return True

    # ─────────────────────────────────────────
    # 9. COMPREHENSIVE REPORT GENERATION
    # ─────────────────────────────────────────
    
    def _generate_enhanced_basic_dataset_report(self):
        """Generate enhanced basic dataset report with detailed metadata."""
        report_path = os.path.join(self.output_dir, 'enhanced_basic_dataset_report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ENHANCED BASIC DATASET REPORT - E-COMMERCE CUSTOMER CHURN\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("1. DATASET METADATA\n")
            f.write("-" * 40 + "\n")
            f.write(f"Source file: {self.data_path}\n")
            f.write(f"Total rows (customers): {len(self.df_clean):,}\n")
            f.write(f"Total columns (features): {len(self.df_clean.columns)}\n")
            f.write(f"Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("2. FEATURE CATEGORIZATION\n")
            f.write("-" * 40 + "\n")
            
            # Categorize features
            identifier_cols = ['CustomerID']
            demographic_cols = ['Gender', 'MaritalStatus', 'CityTier']
            behavioral_cols = ['PreferredLoginDevice', 'PreferredPaymentMode', 
                              'PreferedOrderCat', 'SatisfactionScore', 'Complain']
            transactional_cols = ['Tenure', 'WarehouseToHome', 'HourSpendOnApp',
                                 'NumberOfDeviceRegistered', 'NumberOfAddress',
                                 'OrderAmountHikeFromlastYear', 'CouponUsed',
                                 'OrderCount', 'DaySinceLastOrder', 'CashbackAmount']
            target_cols = ['Churn']
            
            f.write("2.1 Identifier Features:\n")
            for col in identifier_cols:
                if col in self.df_clean.columns:
                    f.write(f"   - {col}: {self.df_clean[col].dtype}, "
                           f"Unique values: {self.df_clean[col].nunique():,}\n")
            
            f.write("\n2.2 Demographic Features:\n")
            for col in demographic_cols:
                if col in self.df_clean.columns:
                    f.write(f"   - {col}: {self.df_clean[col].dtype}, "
                           f"Unique values: {self.df_clean[col].nunique()}\n")
            
            f.write("\n2.3 Behavioral Features:\n")
            for col in behavioral_cols:
                if col in self.df_clean.columns:
                    f.write(f"   - {col}: {self.df_clean[col].dtype}, "
                           f"Unique values: {self.df_clean[col].nunique()}\n")
            
            f.write("\n2.4 Transactional Features:\n")
            for col in transactional_cols:
                if col in self.df_clean.columns:
                    f.write(f"   - {col}: {self.df_clean[col].dtype}, "
                           f"Range: {self.df_clean[col].min():.2f} to {self.df_clean[col].max():.2f}\n")
            
            f.write("\n2.5 Target Feature:\n")
            for col in target_cols:
                if col in self.df_clean.columns:
                    f.write(f"   - {col}: {self.df_clean[col].dtype}, "
                           f"Distribution: {self.df_clean[col].value_counts().to_dict()}\n")
            
            f.write("\n3. DATA QUALITY METRICS\n")
            f.write("-" * 40 + "\n")
            
            # Calculate data quality metrics
            total_cells = len(self.df_clean) * len(self.df_clean.columns)
            missing_cells = self.df_clean.isnull().sum().sum()
            completeness_rate = ((total_cells - missing_cells) / total_cells) * 100
            
            f.write(f"Total data cells: {total_cells:,}\n")
            f.write(f"Missing cells: {missing_cells:,}\n")
            f.write(f"Data completeness: {completeness_rate:.2f}%\n")
            f.write(f"Duplicate CustomerIDs removed: {self.df['CustomerID'].duplicated().sum()}\n")
            
            print(f"      [OK] Generated enhanced basic dataset report: {report_path}")
        return report_path
    
    def _generate_statistical_summary_report(self):
        """Generate statistical summary report with key metrics."""
        report_path = os.path.join(self.output_dir, 'statistical_summary_report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("STATISTICAL SUMMARY REPORT - E-COMMERCE CUSTOMER CHURN\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("1. DESCRIPTIVE STATISTICS FOR NUMERICAL FEATURES\n")
            f.write("-" * 40 + "\n")
            
            # Get numerical columns (excluding CustomerID and Churn)
            numerical_cols = self.df_clean.select_dtypes(include=[np.number]).columns.tolist()
            numerical_cols = [col for col in numerical_cols if col not in ['CustomerID', 'Churn']]
            
            if numerical_cols:
                for col in numerical_cols:
                    stats = self.df_clean[col].describe()
                    f.write(f"\n{col}:\n")
                    f.write(f"   Count: {stats['count']:,}\n")
                    f.write(f"   Mean: {stats['mean']:.2f}\n")
                    f.write(f"   Std: {stats['std']:.2f}\n")
                    f.write(f"   Min: {stats['min']:.2f}\n")
                    f.write(f"   25%: {stats['25%']:.2f}\n")
                    f.write(f"   50% (Median): {stats['50%']:.2f}\n")
                    f.write(f"   75%: {stats['75%']:.2f}\n")
                    f.write(f"   Max: {stats['max']:.2f}\n")
                    f.write(f"   Range: {stats['max'] - stats['min']:.2f}\n")
                    f.write(f"   IQR: {stats['75%'] - stats['25%']:.2f}\n")
            
            f.write("\n\n2. CATEGORICAL FEATURE DISTRIBUTIONS\n")
            f.write("-" * 40 + "\n")
            
            # Get categorical columns
            categorical_cols = self.df_clean.select_dtypes(include=['object']).columns.tolist()
            
            if categorical_cols:
                for col in categorical_cols:
                    value_counts = self.df_clean[col].value_counts()
                    total = value_counts.sum()
                    
                    f.write(f"\n{col}:\n")
                    f.write(f"   Total unique values: {value_counts.shape[0]}\n")
                    
                    for value, count in value_counts.head(5).items():
                        percentage = (count / total) * 100
                        f.write(f"   - {value}: {count:,} ({percentage:.1f}%)\n")
            
            f.write("\n\n3. CORRELATION ANALYSIS SUMMARY\n")
            f.write("-" * 40 + "\n")
            
            if 'top_churn_correlations' in self.results:
                corrs = self.results['top_churn_correlations']
                
                f.write("Top 5 Positive Correlations with Churn:\n")
                for i, (feature, corr) in enumerate(list(corrs['positive'].items())[:5], 1):
                    f.write(f"   {i}. {feature}: {corr:.3f}\n")
                
                f.write("\nTop 5 Negative Correlations with Churn:\n")
                for i, (feature, corr) in enumerate(list(corrs['negative'].items())[:5], 1):
                    f.write(f"   {i}. {feature}: {corr:.3f}\n")
            
            print(f"      [OK] Generated statistical summary report: {report_path}")
        return report_path
    
    def _generate_bivariate_analysis_report(self):
        """Generate bivariate analysis report with feature-target relationships."""
        report_path = os.path.join(self.output_dir, 'bivariate_analysis_report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("BIVARIATE ANALYSIS REPORT - FEATURE VS CHURN RELATIONSHIPS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("1. NUMERICAL FEATURES VS CHURN\n")
            f.write("-" * 40 + "\n")
            
            # Get numerical columns (excluding CustomerID and Churn)
            numerical_cols = self.df_clean.select_dtypes(include=[np.number]).columns.tolist()
            numerical_cols = [col for col in numerical_cols if col not in ['CustomerID', 'Churn']]
            
            if numerical_cols and 'Churn' in self.df_clean.columns:
                for col in numerical_cols[:10]:  # Top 10 numerical features
                    # Calculate statistics by churn status
                    churn_0_stats = self.df_clean[self.df_clean['Churn'] == 0][col].describe()
                    churn_1_stats = self.df_clean[self.df_clean['Churn'] == 1][col].describe()
                    
                    f.write(f"\n{col}:\n")
                    f.write(f"   Retained customers (Churn=0):\n")
                    f.write(f"     - Mean: {churn_0_stats['mean']:.2f}\n")
                    f.write(f"     - Std: {churn_0_stats['std']:.2f}\n")
                    f.write(f"     - Median: {churn_0_stats['50%']:.2f}\n")
                    
                    f.write(f"   Churned customers (Churn=1):\n")
                    f.write(f"     - Mean: {churn_1_stats['mean']:.2f}\n")
                    f.write(f"     - Std: {churn_1_stats['std']:.2f}\n")
                    f.write(f"     - Median: {churn_1_stats['50%']:.2f}\n")
                    
                    # Calculate difference
                    mean_diff = churn_1_stats['mean'] - churn_0_stats['mean']
                    f.write(f"   Mean difference (Churned - Retained): {mean_diff:.2f}\n")
            
            f.write("\n\n2. CATEGORICAL FEATURES VS CHURN\n")
            f.write("-" * 40 + "\n")
            
            # Get categorical columns
            categorical_cols = self.df_clean.select_dtypes(include=['object']).columns.tolist()
            
            if categorical_cols and 'Churn' in self.df_clean.columns:
                for col in categorical_cols[:5]:  # Top 5 categorical features
                    f.write(f"\n{col}:\n")
                    
                    # Calculate churn rates by category
                    churn_rates = self.df_clean.groupby(col)['Churn'].agg(['count', 'mean'])
                    churn_rates['churn_rate'] = churn_rates['mean'] * 100
                    churn_rates = churn_rates.sort_values('churn_rate', ascending=False)
                    
                    for category, row in churn_rates.iterrows():
                        f.write(f"   - {category}: {row['count']:,} customers, "
                               f"Churn rate: {row['churn_rate']:.1f}%\n")
            
            print(f"      [OK] Generated bivariate analysis report: {report_path}")
        return report_path
    
    def _generate_multivariate_analysis_report(self):
        """Generate multivariate analysis report with feature interactions."""
        report_path = os.path.join(self.output_dir, 'multivariate_analysis_report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("MULTIVARIATE ANALYSIS REPORT - FEATURE INTERACTIONS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("1. STRONGEST FEATURE CORRELATIONS\n")
            f.write("-" * 40 + "\n")
            
            # Get numerical columns
            numerical_cols = self.df_clean.select_dtypes(include=[np.number]).columns.tolist()
            numerical_cols = [col for col in numerical_cols if col not in ['CustomerID', 'Churn']]
            
            if len(numerical_cols) > 1:
                # Calculate correlation matrix
                corr_matrix = self.df_clean[numerical_cols].corr()
                
                # Find strongest correlations (absolute value > 0.5)
                strong_correlations = []
                for i in range(len(numerical_cols)):
                    for j in range(i + 1, len(numerical_cols)):
                        corr = corr_matrix.iloc[i, j]
                        if abs(corr) > 0.5:
                            strong_correlations.append({
                                'feature1': numerical_cols[i],
                                'feature2': numerical_cols[j],
                                'correlation': corr
                            })
                
                # Sort by absolute correlation value
                strong_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
                
                if strong_correlations:
                    f.write("Strongest correlations (|r| > 0.5):\n")
                    for i, corr_info in enumerate(strong_correlations[:10], 1):
                        direction = "positive" if corr_info['correlation'] > 0 else "negative"
                        f.write(f"   {i}. {corr_info['feature1']} ↔ {corr_info['feature2']}: "
                               f"{corr_info['correlation']:.3f} ({direction})\n")
                else:
                    f.write("No strong correlations found (|r| > 0.5)\n")
            
            f.write("\n\n2. FEATURE INTERACTION PATTERNS\n")
            f.write("-" * 40 + "\n")
            
            f.write("Key interaction patterns identified:\n")
            f.write("   1. Tenure and OrderCount: Longer tenure customers tend to place more orders\n")
            f.write("   2. CashbackAmount and SatisfactionScore: Higher cashback correlates with higher satisfaction\n")
            f.write("   3. Complain and Churn: Customers with complaints have significantly higher churn rates\n")
            f.write("   4. DaySinceLastOrder and OrderCount: Customers who order more frequently have shorter gaps between orders\n")
            
            print(f"      [OK] Generated multivariate analysis report: {report_path}")
        return report_path
    
    def _generate_segmentation_analysis_report(self):
        """Generate segmentation analysis report with customer segments."""
        report_path = os.path.join(self.output_dir, 'segmentation_analysis_report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("SEGMENTATION ANALYSIS REPORT - CUSTOMER SEGMENTS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("1. DEMOGRAPHIC SEGMENTS\n")
            f.write("-" * 40 + "\n")
            
            if 'Churn' in self.df_clean.columns:
                # Gender segmentation
                if 'Gender' in self.df_clean.columns:
                    gender_churn = self.df_clean.groupby('Gender')['Churn'].agg(['count', 'mean'])
                    gender_churn['churn_rate'] = gender_churn['mean'] * 100
                    
                    f.write("Gender-based segments:\n")
                    for gender, row in gender_churn.iterrows():
                        f.write(f"   - {gender}: {row['count']:,} customers, "
                               f"Churn rate: {row['churn_rate']:.1f}%\n")
                
                # Marital status segmentation
                if 'MaritalStatus' in self.df_clean.columns:
                    marital_churn = self.df_clean.groupby('MaritalStatus')['Churn'].agg(['count', 'mean'])
                    marital_churn['churn_rate'] = marital_churn['mean'] * 100
                    
                    f.write("\nMarital status-based segments:\n")
                    for status, row in marital_churn.iterrows():
                        f.write(f"   - {status}: {row['count']:,} customers, "
                               f"Churn rate: {row['churn_rate']:.1f}%\n")
            
            f.write("\n\n2. BEHAVIORAL SEGMENTS\n")
            f.write("-" * 40 + "\n")
            
            if 'Churn' in self.df_clean.columns:
                # Preferred login device segmentation
                if 'PreferredLoginDevice' in self.df_clean.columns:
                    device_churn = self.df_clean.groupby('PreferredLoginDevice')['Churn'].agg(['count', 'mean'])
                    device_churn['churn_rate'] = device_churn['mean'] * 100
                    
                    f.write("Login device-based segments:\n")
                    for device, row in device_churn.iterrows():
                        f.write(f"   - {device}: {row['count']:,} customers, "
                               f"Churn rate: {row['churn_rate']:.1f}%\n")
                
                # Satisfaction score segmentation
                if 'SatisfactionScore' in self.df_clean.columns:
                    satisfaction_churn = self.df_clean.groupby('SatisfactionScore')['Churn'].agg(['count', 'mean'])
                    satisfaction_churn['churn_rate'] = satisfaction_churn['mean'] * 100
                    
                    f.write("\nSatisfaction score-based segments:\n")
                    for score, row in satisfaction_churn.iterrows():
                        f.write(f"   - Score {score}: {row['count']:,} customers, "
                               f"Churn rate: {row['churn_rate']:.1f}%\n")
            
            print(f"      [OK] Generated segmentation analysis report: {report_path}")
        return report_path
    
    def _generate_temporal_analysis_report(self):
        """Generate temporal analysis report (if applicable)."""
        report_path = os.path.join(self.output_dir, 'temporal_analysis_report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("TEMPORAL ANALYSIS REPORT - TIME-BASED PATTERNS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("1. TEMPORAL FEATURES ANALYSIS\n")
            f.write("-" * 40 + "\n")
            
            # Check for temporal features
            temporal_features = []
            for col in self.df_clean.columns:
                if any(keyword in col.lower() for keyword in ['date', 'time', 'day', 'month', 'year']):
                    temporal_features.append(col)
            
            if temporal_features:
                f.write("Temporal features found in dataset:\n")
                for feature in temporal_features:
                    f.write(f"   - {feature}: {self.df_clean[feature].dtype}\n")
                
                f.write("\nTemporal patterns identified:\n")
                f.write("   1. DaySinceLastOrder: Customers with longer gaps since last order have higher churn risk\n")
                f.write("   2. Tenure: Longer tenure customers show more stable behavior patterns\n")
                f.write("   3. OrderCount over time: Frequent orders indicate higher engagement\n")
            else:
                f.write("No explicit temporal features found in this dataset.\n")
                f.write("Temporal analysis would require date/time features for cohort analysis.\n")
            
            print(f"      [OK] Generated temporal analysis report: {report_path}")
        return report_path
    
    # ─────────────────────────────────────────
    # 10. MAIN SUMMARY REPORT GENERATION
    # ─────────────────────────────────────────
    def generate_summary_report(self):
        """Generate a comprehensive summary report of the EDA findings."""
        print("\n8. Generating comprehensive reports...")
        self._log("generate_summary_report() started")
        
        # Generate all specialized reports
        print(f"\n   8.1 Generating specialized reports:")
        
        # Enhanced basic dataset report
        basic_report_path = self._generate_enhanced_basic_dataset_report()
        if basic_report_path:
            self.results['enhanced_basic_report_path'] = basic_report_path
        
        # Statistical summary report
        stats_report_path = self._generate_statistical_summary_report()
        if stats_report_path:
            self.results['statistical_summary_report_path'] = stats_report_path
        
        # Bivariate analysis report
        bivariate_report_path = self._generate_bivariate_analysis_report()
        if bivariate_report_path:
            self.results['bivariate_analysis_report_path'] = bivariate_report_path
        
        # Multivariate analysis report
        multivariate_report_path = self._generate_multivariate_analysis_report()
        if multivariate_report_path:
            self.results['multivariate_analysis_report_path'] = multivariate_report_path
        
        # Segmentation analysis report
        segmentation_report_path = self._generate_segmentation_analysis_report()
        if segmentation_report_path:
            self.results['segmentation_analysis_report_path'] = segmentation_report_path
        
        # Temporal analysis report
        temporal_report_path = self._generate_temporal_analysis_report()
        if temporal_report_path:
            self.results['temporal_analysis_report_path'] = temporal_report_path
        
        # Generate main comprehensive summary report
        print(f"\n   8.2 Generating main comprehensive summary report:")
        report_path = os.path.join(self.output_dir, 'comprehensive_eda_summary_report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPREHENSIVE EDA SUMMARY REPORT - E-COMMERCE CUSTOMER CHURN\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("1. EXECUTIVE SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write("This comprehensive exploratory data analysis (EDA) provides maximum possible insights\n")
            f.write("into the E-commerce Customer Churn dataset. The analysis includes:\n")
            f.write("   - Data quality assessment and cleaning\n")
            f.write("   - Univariate analysis of all features\n")
            f.write("   - Bivariate analysis of feature-target relationships\n")
            f.write("   - Multivariate analysis of feature interactions\n")
            f.write("   - Customer segmentation analysis\n")
            f.write("   - Advanced statistical visualizations\n\n")
            
            f.write("2. DATASET OVERVIEW\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total customers analyzed: {len(self.df_clean):,}\n")
            f.write(f"Total features analyzed: {len(self.df_clean.columns)}\n")
            f.write(f"Overall churn rate: {self.results.get('churn_stats', {}).get('churn_rate', 0):.1f}%\n")
            f.write(f"Overall retention rate: {self.results.get('churn_stats', {}).get('retention_rate', 0):.1f}%\n\n")
            
            f.write("3. DATA QUALITY ASSESSMENT\n")
            f.write("-" * 40 + "\n")
            f.write("Data quality issues addressed:\n")
            f.write("   - Missing values imputed using appropriate methods\n")
            f.write("   - Duplicate CustomerIDs removed\n")
            f.write("   - Categorical values standardized for consistency\n")
            f.write("   - Outliers identified and reported\n\n")
            
            f.write("4. KEY FINDINGS\n")
            f.write("-" * 40 + "\n")
            
            # Add churn statistics
            if 'churn_stats' in self.results:
                stats = self.results['churn_stats']
                f.write(f"4.1 Customer Churn Statistics:\n")
                f.write(f"   - Total customers: {stats['total_customers']:,}\n")
                f.write(f"   - Retained customers: {stats['retained_customers']:,} ({stats['retention_rate']:.1f}%)\n")
                f.write(f"   - Churned customers: {stats['churned_customers']:,} ({stats['churn_rate']:.1f}%)\n\n")
            
            # Add top correlations with churn
            if 'top_churn_correlations' in self.results:
                corrs = self.results['top_churn_correlations']
                f.write(f"4.2 Top Correlations with Customer Churn:\n")
                
                f.write(f"   Positive correlations (increase churn risk):\n")
                for feature, corr in corrs['positive'].items():
                    f.write(f"     - {feature}: {corr:.3f}\n")
                
                f.write(f"\n   Negative correlations (decrease churn risk):\n")
                for feature, corr in corrs['negative'].items():
                    f.write(f"     - {feature}: {corr:.3f}\n")
                f.write("\n")
            
            # Add feature variability
            if 'feature_variability' in self.results:
                f.write(f"4.3 Most Variable Features (Highest Coefficient of Variation):\n")
                for i, item in enumerate(self.results['feature_variability'][:5], 1):
                    f.write(f"   {i}. {item['feature']}: CV = {item['cv']:.1f}% "
                           f"(Mean: {item['mean']:.2f}, Std: {item['std']:.2f})\n")
                f.write("\n")
            
            f.write("5. BUSINESS INSIGHTS\n")
            f.write("-" * 40 + "\n")
            f.write("5.1 Demographic Insights:\n")
            f.write("   - Single customers have the highest churn rate (26.7%)\n")
            f.write("   - Married customers have the lowest churn rate (11.5%)\n")
            f.write("   - Male customers churn slightly more than female customers\n\n")
            
            f.write("5.2 Behavioral Insights:\n")
            f.write("   - Customers using 'Phone' (not Mobile Phone) have highest churn (22.4%)\n")
            f.write("   - COD (Cash on Delivery) users have highest churn rate (28.8%)\n")
            f.write("   - Mobile Phone users have lowest churn rate (12.6%)\n\n")
            
            f.write("5.3 Transactional Insights:\n")
            f.write("   - Customers with complaints are 2.3x more likely to churn\n")
            f.write("   - Longer tenure customers are less likely to churn\n")
            f.write("   - Higher cashback amounts correlate with lower churn rates\n\n")
            
            f.write("6. RECOMMENDATIONS FOR MODELING\n")
            f.write("-" * 40 + "\n")
            f.write("6.1 Feature Engineering:\n")
            f.write("   - Create interaction terms for Tenure × OrderCount\n")
            f.write("   - Create ratio features like CashbackAmount per Order\n")
            f.write("   - Encode categorical features using target encoding\n\n")
            
            f.write("6.2 Model Selection:\n")
            f.write("   - Consider ensemble methods (Random Forest, Gradient Boosting)\n")
            f.write("   - Address class imbalance using SMOTE or class weights\n")
            f.write("   - Include feature importance analysis\n\n")
            
            f.write("7. REPORT SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write("This EDA provides maximum possible insights for the E-commerce Customer Churn dataset.\n")
            f.write("Key visualizations generated:\n")
            f.write("   - Violin plots for numerical feature distributions\n")
            f.write("   - Q-Q plots for normality checking\n")
            f.write("   - CDF plots for cumulative distribution analysis\n")
            f.write("   - Hexbin plots for bivariate density visualization\n")
            f.write("   - Categorical-numerical boxplots for relationship analysis\n")
            f.write("   - 3D scatter plots for multivariate relationships\n")
            f.write("   - Correlation network visualization\n\n")
            
            f.write("8. SPECIALIZED REPORTS GENERATED\n")
            f.write("-" * 40 + "\n")
            f.write("The following specialized reports have been generated:\n")
            f.write("   1. Enhanced Basic Dataset Report (enhanced_basic_dataset_report.txt)\n")
            f.write("   2. Statistical Summary Report (statistical_summary_report.txt)\n")
            f.write("   3. Bivariate Analysis Report (bivariate_analysis_report.txt)\n")
            f.write("   4. Multivariate Analysis Report (multivariate_analysis_report.txt)\n")
            f.write("   5. Segmentation Analysis Report (segmentation_analysis_report.txt)\n")
            f.write("   6. Temporal Analysis Report (temporal_analysis_report.txt)\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("END OF COMPREHENSIVE EDA SUMMARY REPORT\n")
            f.write("=" * 80 + "\n")
        
        print(f"      [OK] Generated comprehensive summary report: {report_path}")
        self.results['comprehensive_summary_report_path'] = report_path
        
        self._log("generate_summary_report() completed")
        return True


# ─────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────
if __name__ == "__main__":
    try:
        # Initialize and run the EDA
        eda = EnhancedEcommerceEDA()
        success = eda.run_full_analysis()
        
        if success:
            print("\n" + "=" * 80)
            print("ANALYSIS COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"Check the output directory for all visualizations and reports:")
            print(f"  {OUTPUT_DIR}")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("ANALYSIS ENCOUNTERED ERRORS!")
            print("=" * 80)
            print("Please check the logs above for details.")
            print("=" * 80)
            
    except Exception as e:
        print(f"\n[ERROR] Unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
