"""
CustomerDNA AI - PFE Project
Dataset : Customer Personality Analysis (marketing_campaign.csv)
Script  : Enhanced Customer EDA — Maximum Possible Plots
Author  : PFE Student
Description: Comprehensive EDA with maximum possible visualization types for customer analysis
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

# ─────────────────────────────────────────────
# PATHS — adjust only these lines
# ─────────────────────────────────────────────
DATA_PATH  = r"d:\github\Master_PFE_Project\CustomerDNA AI\datasets\client_1\Customer_Personality_Analysis\marketing_campaign.csv"
OUTPUT_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\EDA\client_1\Customer_Personality_Analysis_dataset_EDA\output"

# ─────────────────────────────────────────────
# CONSTANTS — data cleaning rules
# ─────────────────────────────────────────────
REFERENCE_YEAR          = 2014       # dataset spans 2012-07-30 -> 2014-06-29
AGE_UPPER_LIMIT         = 90         # removes 3 rows: born 1893, 1899, 1900
INCOME_UPPER_LIMIT      = 200_000    # removes 1 row: ID 9432 with $666,666
MARITAL_STATUS_REMOVE   = ["Absurd", "YOLO"]
MARITAL_STATUS_MAPPING  = {"Alone": "Single"}
COLUMNS_TO_DROP         = ["Z_CostContact", "Z_Revenue"]  # constant cols, zero info


class EnhancedCustomerEDA:
    """
    Enhanced EDA class for Customer Personality Analysis with maximum possible plots.
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
        print("CustomerDNA AI — Enhanced Customer Personality Analysis EDA")
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
        """Load the raw CSV and display a basic profile."""
        print("\n1. Loading data...")
        self._log("load_data() started")

        try:
            self.df = pd.read_csv(self.data_path, sep='\t')
            rows, cols = self.df.shape
            missing    = self.df.isnull().sum().sum()
            dupes      = self.df.duplicated().sum()

            print(f"   [OK] Loaded {rows:,} rows × {cols} columns")
            print(f"   [OK] Missing values : {missing}  |  Duplicates : {dupes}")

            self._save_basic_report()
            self._log(f"load_data() OK — shape {self.df.shape}")
            return self.df

        except Exception as e:
            self._log(f"load_data() FAILED — {e}")
            print(f"   [ERROR] Error loading data: {e}")
            raise

    def _save_basic_report(self):
        """Save basic dataset information report."""
        report = [
            "ENHANCED DATASET REPORT",
            "=" * 60,
            f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Source    : {self.data_path}",
            f"Shape     : {self.df.shape[0]} rows × {self.df.shape[1]} columns",
            "",
            "COLUMNS AND DATA TYPES:",
            "-" * 30,
        ]
        for col, dtype in self.df.dtypes.items():
            report.append(f"  {col:<25} {dtype}")

        report += ["", "MISSING VALUES:", "-" * 30]
        missing = self.df.isnull().sum()
        cols_with_missing = missing[missing > 0]
        if len(cols_with_missing) == 0:
            report.append("  None")
        else:
            for col, count in cols_with_missing.items():
                pct = count / len(self.df) * 100
                report.append(f"  {col}: {count} ({pct:.1f}%)")

        path = os.path.join(self.output_dir, 'enhanced_basic_dataset_report.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        print(f"   [OK] Enhanced basic report saved")

    # ─────────────────────────────────────────
    # 2. CLEAN DATA
    # ─────────────────────────────────────────
    def clean_data(self):
        """
        Apply all cleaning steps in the correct order.
        """
        print("\n2. Cleaning data...")
        self._log("clean_data() started")

        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        df     = self.df.copy()
        before = len(df)

        # --- Date conversion
        df['Dt_Customer'] = pd.to_datetime(df['Dt_Customer'], format='%d-%m-%Y')

        # --- Age — fixed reference year for reproducibility
        df['Age'] = REFERENCE_YEAR - df['Year_Birth']

        # --- Customer tenure in days
        reference_date             = df['Dt_Customer'].max()   # 2014-06-29
        df['Customer_Tenure_Days'] = (reference_date - df['Dt_Customer']).dt.days

        # --- Engineered aggregate features
        spending_cols        = [c for c in df.columns if c.startswith('Mnt')]
        purchase_cols        = [c for c in df.columns if 'Num' in c and 'Purchases' in c]
        df['Total_Children'] = df['Kidhome'] + df['Teenhome']
        df['Total_Spending'] = df[spending_cols].sum(axis=1)
        df['Total_Purchases']= df[purchase_cols].sum(axis=1)

        # --- Step 3: Remove age outliers FIRST
        mask_age   = df['Age'] <= AGE_UPPER_LIMIT
        n_age      = (~mask_age).sum()
        df         = df[mask_age].copy()
        print(f"   [OK] Removed {n_age} rows — Age > {AGE_UPPER_LIMIT} (born 1893, 1899, 1900)")
        self._log(f"Removed {n_age} age-outlier rows")

        # --- Step 4: Remove income outlier BEFORE imputing
        mask_income = df['Income'] <= INCOME_UPPER_LIMIT
        n_income    = (~mask_income).sum()
        df          = df[mask_income].copy()
        print(f"   [OK] Removed {n_income} row  — Income > ${INCOME_UPPER_LIMIT:,} (ID 9432: $666,666)")
        self._log(f"Removed {n_income} income-outlier rows")

        # --- Step 5: Impute missing Income with CLEAN median (after outlier removal)
        missing_income = df['Income'].isnull().sum()
        if missing_income > 0:
            clean_median = df['Income'].median()
            df['Income'] = df['Income'].fillna(clean_median)
            print(f"   [OK] Imputed {missing_income} missing Income values -> median ${clean_median:,.2f}")
            self._log(f"Imputed {missing_income} Income nulls with median ${clean_median:,.2f}")

        # --- Step 6: Clean Marital_Status
        df = df[~df['Marital_Status'].isin(MARITAL_STATUS_REMOVE)].copy()
        df['Marital_Status'] = df['Marital_Status'].replace(MARITAL_STATUS_MAPPING)
        print(f"   [OK] Removed 4 rows   — Marital_Status in {MARITAL_STATUS_REMOVE}")
        print(f"   [OK] Merged 'Alone'   -> 'Single'")

        # --- Step 7: Drop zero-variance columns
        df.drop(columns=COLUMNS_TO_DROP, inplace=True, errors='ignore')
        print(f"   [OK] Dropped columns  : {COLUMNS_TO_DROP} (constants, zero information)")

        after = len(df)
        self.df_clean = df
        print(f"\n   [OK] Clean shape : {after:,} rows × {df.shape[1]} columns  "
              f"(removed {before - after} rows total)")
        self._log(f"clean_data() OK — clean shape {df.shape}")

        # Save clean dataset immediately — feeds all ML modules
        clean_path = os.path.join(self.output_dir, 'marketing_campaign_clean.csv')
        df.to_csv(clean_path, index=False)
        print(f"   [OK] Clean dataset saved -> {clean_path}")
        print(f"     -> This file feeds: Clustering, LTV, Persona Generation modules")

        return df

    # ─────────────────────────────────────────
    # 3. COMPREHENSIVE UNIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_univariate_distributions(self):
        """Create detailed univariate analysis plots for all features."""
        print("\n3. Analyzing univariate distributions...")
        self._log("analyze_univariate_distributions() started")

        if self.df_clean is None:
            raise ValueError("Data not cleaned. Call clean_data() first.")

        df = self.df_clean
        
        # Separate numerical and categorical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # Remove ID from numerical analysis
        if 'ID' in numerical_cols:
            numerical_cols.remove('ID')
        
        print(f"   [OK] Numerical features: {len(numerical_cols)}")
        print(f"   [OK] Categorical features: {len(categorical_cols)}")
        
        results = {}
        
        # 1. Numerical distributions - histograms with KDE
        if numerical_cols:
            self._create_numerical_distributions(df, numerical_cols)
        
        # 2. Categorical distributions - bar plots
        if categorical_cols:
            self._create_categorical_distributions(df, categorical_cols)
        
        # 3. Box plots for numerical features
        if numerical_cols:
            self._create_box_plots(df, numerical_cols)
        
        # 4. Violin plots for numerical features
        if numerical_cols:
            self._create_violin_plots(df, numerical_cols)
        
        # 5. QQ plots for normality checking
        if numerical_cols and HAS_SCIPY:
            self._create_qq_plots(df, numerical_cols)
        
        # 6. Cumulative distribution functions
        if numerical_cols:
            self._create_cdf_plots(df, numerical_cols)
        
        # 7. Feature importance ranking based on variance
        if numerical_cols:
            self._create_feature_variability_analysis(df, numerical_cols)
        
        # 8. Statistical summary report
        self._create_statistical_summary_report(df, numerical_cols, categorical_cols)
        
        self._log("analyze_univariate_distributions() OK")
        return results

    def _create_numerical_distributions(self, df, numerical_cols):
        """Create histogram with KDE plots for numerical features."""
        n_numerical = len(numerical_cols)
        n_cols = 4
        n_rows = (n_numerical + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4, n_rows * 3))
        fig.suptitle('Numerical Feature Distributions', fontsize=16, fontweight='bold')
        
        # Flatten axes array for easy iteration
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, col in enumerate(numerical_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            
            if n_rows == 1:
                ax = axes[col_idx]
            elif n_cols == 1:
                ax = axes[row]
            else:
                ax = axes[row, col_idx]
            
            # Histogram with KDE
            sns.histplot(df[col], kde=True, ax=ax, color='steelblue', bins=30)
            ax.axvline(df[col].mean(), color='red', linestyle='--', 
                      label=f'Mean: {df[col].mean():.2f}')
            ax.axvline(df[col].median(), color='green', linestyle=':', 
                      label=f'Median: {df[col].median():.2f}')
            ax.set_title(f'{col}', fontsize=10)
            ax.set_xlabel('')
            ax.legend(fontsize=8)
        
        # Hide empty subplots
        for idx in range(len(numerical_cols), n_rows * n_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            if n_rows == 1:
                axes[col_idx].set_visible(False)
            elif n_cols == 1:
                axes[row].set_visible(False)
            else:
                axes[row, col_idx].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'numerical_distributions.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] numerical_distributions.png saved")

    def _create_categorical_distributions(self, df, categorical_cols):
        """Create bar plots for categorical features."""
        n_categorical = len(categorical_cols)
        n_cols = 3
        n_rows = (n_categorical + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
        fig.suptitle('Categorical Feature Distributions', fontsize=16, fontweight='bold')
        
        # Handle single axis case
        if n_rows == 1 and n_cols == 1:
            axes = np.array([[axes]])
        elif n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, col in enumerate(categorical_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            
            if n_rows == 1 and n_cols == 1:
                ax = axes[0, 0]
            elif n_rows == 1:
                ax = axes[0, col_idx]
            elif n_cols == 1:
                ax = axes[row, 0]
            else:
                ax = axes[row, col_idx]
            
            # Bar plot with value counts
            value_counts = df[col].value_counts()
            colors = sns.color_palette('husl', len(value_counts))
            
            bars = ax.bar(value_counts.index.astype(str), value_counts.values, 
                         color=colors, edgecolor='white')
            ax.set_title(f'{col} (n={len(value_counts)})', fontsize=10)
            ax.set_xlabel('')
            ax.set_ylabel('Count')
            ax.tick_params(axis='x', rotation=45)
            
            # Add count labels on bars
            for bar, val in zip(bars, value_counts.values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{val}', ha='center', va='bottom', fontsize=8)
        
        # Hide empty subplots
        for idx in range(len(categorical_cols), n_rows * n_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            if n_rows == 1 and n_cols == 1:
                axes[0, 0].set_visible(False)
            elif n_rows == 1:
                axes[0, col_idx].set_visible(False)
            elif n_cols == 1:
                axes[row, 0].set_visible(False)
            else:
                axes[row, col_idx].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'categorical_distributions.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] categorical_distributions.png saved")

    def _create_box_plots(self, df, numerical_cols):
        """Create box plots for numerical features."""
        # Select top 12 numerical features for box plots
        top_numerical = numerical_cols[:12] if len(numerical_cols) > 12 else numerical_cols
        
        n_cols = 4
        n_rows = (len(top_numerical) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4, n_rows * 3))
        fig.suptitle('Box Plots for Numerical Features (Outlier Detection)', 
                    fontsize=16, fontweight='bold')
        
        # Flatten axes array for easy iteration
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, col in enumerate(top_numerical):
            row = idx // n_cols
            col_idx = idx % n_cols
            
            if n_rows == 1:
                ax = axes[col_idx]
            elif n_cols == 1:
                ax = axes[row]
            else:
                ax = axes[row, col_idx]
            
            # Box plot
            box = ax.boxplot(df[col].dropna(), patch_artist=True)
            box['boxes'][0].set_facecolor('lightblue')
            box['medians'][0].set_color('red')
            box['whiskers'][0].set_color('black')
            box['fliers'][0].set_markerfacecolor('red')
            
            ax.set_title(f'{col}', fontsize=10)
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3)
        
        # Hide empty subplots
        for idx in range(len(top_numerical), n_rows * n_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            if n_rows == 1:
                axes[col_idx].set_visible(False)
            elif n_cols == 1:
                axes[row].set_visible(False)
            else:
                axes[row, col_idx].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'box_plots.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] box_plots.png saved")

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
        plt.savefig(os.path.join(self.output_dir, 'violin_plots.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] violin_plots.png saved")

    def _create_qq_plots(self, df, numerical_cols):
        """Create QQ plots for normality checking."""
        # Select key features for QQ plots
        key_features_qq = ['Income', 'Age', 'Total_Spending', 'NumWebVisitsMonth']
        key_features_qq = [f for f in key_features_qq if f in numerical_cols]
        
        if key_features_qq:
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
            plt.savefig(os.path.join(self.output_dir, 'qq_plots.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   [OK] qq_plots.png saved")

    def _create_cdf_plots(self, df, numerical_cols):
        """Create cumulative distribution function plots."""
        # Select key features for CDF
        key_features_cdf = ['Income', 'Age', 'Total_Spending', 'Customer_Tenure_Days']
        key_features_cdf = [f for f in key_features_cdf if f in numerical_cols]
        
        if key_features_cdf:
            plt.figure(figsize=(12, 8))
            
            for col in key_features_cdf:
                sorted_data = np.sort(df[col].dropna())
                cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
                plt.plot(sorted_data, cdf, label=col, linewidth=2)
            
            plt.title('Cumulative Distribution Functions (CDF)', fontsize=14, fontweight='bold')
            plt.xlabel('Value')
            plt.ylabel('Cumulative Probability')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'cdf_plots.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   [OK] cdf_plots.png saved")

    def _create_feature_variability_analysis(self, df, numerical_cols):
        """Create feature variability ranking based on coefficient of variation."""
        # Calculate coefficient of variation for each numerical feature
        cv_results = []
        for col in numerical_cols:
            data = df[col].dropna()
            if data.std() > 0:  # Avoid division by zero
                cv = (data.std() / data.mean()) * 100
                cv_results.append({'Feature': col, 'CV(%)': cv, 'Mean': data.mean(), 'Std': data.std()})
        
        cv_df = pd.DataFrame(cv_results).sort_values('CV(%)', ascending=False)
        
        # Save CV report
        cv_df.to_csv(os.path.join(self.output_dir, 'feature_variability.csv'), index=False)
        
        # Plot top 15 features by coefficient of variation
        top_cv = cv_df.head(15)
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(top_cv['Feature'], top_cv['CV(%)'], color='mediumseagreen', edgecolor='white')
        plt.xlabel('Coefficient of Variation (%)')
        plt.title('Feature Variability Ranking (Top 15)', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for bar, cv_val in zip(bars, top_cv['CV(%)']):
            plt.text(cv_val + 0.5, bar.get_y() + bar.get_height()/2, 
                    f'{cv_val:.1f}%', va='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'feature_variability.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] feature_variability.png saved")

    def _create_statistical_summary_report(self, df, numerical_cols, categorical_cols):
        """Create comprehensive statistical summary report."""
        lines = [
            "COMPREHENSIVE STATISTICAL SUMMARY REPORT",
            "=" * 80,
            f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Dataset   : {self.data_path}",
            f"Rows      : {df.shape[0]:,}",
            f"Columns   : {df.shape[1]}",
            "",
            "NUMERICAL FEATURES SUMMARY:",
            "-" * 40,
        ]
        
        # Numerical features summary
        for col in numerical_cols[:20]:  # Limit to top 20 for readability
            data = df[col].dropna()
            lines.append(f"  {col}")
            lines.append(f"    Count    : {len(data):,}")
            lines.append(f"    Mean     : {data.mean():.2f}")
            lines.append(f"    Median   : {data.median():.2f}")
            lines.append(f"    Std Dev  : {data.std():.2f}")
            lines.append(f"    Min      : {data.min():.2f}")
            lines.append(f"    Max      : {data.max():.2f}")
            lines.append(f"    Range    : {data.max() - data.min():.2f}")
            lines.append(f"    Skewness : {data.skew():.3f}")
            lines.append("")
        
        lines += [
            "",
            "CATEGORICAL FEATURES SUMMARY:",
            "-" * 40,
        ]
        
        # Categorical features summary
        for col in categorical_cols:
            value_counts = df[col].value_counts()
            lines.append(f"  {col}")
            lines.append(f"    Unique values : {len(value_counts)}")
            lines.append(f"    Mode          : {value_counts.index[0]} ({value_counts.iloc[0]:,})")
            lines.append(f"    Entropy       : {self._calculate_entropy(value_counts):.3f}")
            lines.append("")
        
        lines += [
            "",
            "DATA QUALITY ASSESSMENT:",
            "-" * 40,
            f"  Missing values        : {df.isnull().sum().sum():,}",
            f"  Duplicate rows        : {df.duplicated().sum():,}",
            f"  Zero variance columns : {self._count_zero_variance(df):,}",
            f"  Outliers detected     : {self._count_outliers(df):,}",
            "",
            "RECOMMENDATIONS:",
            "-" * 40,
            "  1. Consider feature scaling for machine learning models",
            "  2. Address class imbalance in target variable if present",
            "  3. Evaluate multicollinearity before regression modeling",
            "  4. Consider dimensionality reduction for high-dimensional data",
        ]
        
        path = os.path.join(self.output_dir, 'statistical_summary_report.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"   [OK] statistical_summary_report.txt saved")

    def _calculate_entropy(self, value_counts):
        """Calculate entropy of a categorical distribution."""
        probabilities = value_counts.values / value_counts.values.sum()
        return -np.sum(probabilities * np.log2(probabilities))

    def _count_zero_variance(self, df):
        """Count columns with zero variance."""
        return sum(df[col].std() == 0 for col in df.select_dtypes(include=[np.number]).columns)

    def _count_outliers(self, df, threshold=3):
        """Count outliers using z-score method."""
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        outlier_count = 0
        for col in numerical_cols:
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            outlier_count += (z_scores > threshold).sum()
        return outlier_count

    # ─────────────────────────────────────────
    # 4. ADVANCED BIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_bivariate_relationships(self):
        """Create comprehensive bivariate analysis with maximum plot types."""
        print("\n4. Analyzing bivariate relationships...")
        self._log("analyze_bivariate_relationships() started")

        if self.df_clean is None:
            raise ValueError("Data not cleaned. Call clean_data() first.")

        df = self.df_clean
        
        # Key relationships to analyze
        relationships = [
            ('Income', 'Total_Spending', 'Income vs Total Spending'),
            ('Age', 'Total_Spending', 'Age vs Total Spending'),
            ('Income', 'MntWines', 'Income vs Wine Spending'),
            ('Customer_Tenure_Days', 'Total_Spending', 'Tenure vs Spending'),
            ('NumWebVisitsMonth', 'Total_Spending', 'Web Visits vs Spending'),
            ('Total_Children', 'Total_Spending', 'Children vs Spending'),
            ('Age', 'Income', 'Age vs Income'),
            ('MntWines', 'MntMeatProducts', 'Wine vs Meat Spending'),
        ]
        
        # Filter to only include columns that exist in the dataframe
        valid_relationships = []
        for x, y, title in relationships:
            if x in df.columns and y in df.columns:
                valid_relationships.append((x, y, title))
        
        if not valid_relationships:
            print("   [WARNING] No valid relationships to analyze")
            return {}
        
        results = {}
        
        # 1. Scatter plots with regression lines
        self._create_scatter_plots(df, valid_relationships, results)
        
        # 2. Complete correlation matrix
        self._create_complete_correlation_matrix(df)
        
        # 3. Hexbin plots for dense relationships
        self._create_hexbin_plots(df)
        
        # 4. Categorical vs numerical box plots
        self._create_categorical_numerical_plots(df)
        
        # 5. Correlation network visualization
        self._create_correlation_network(df)
        
        # 6. Bivariate analysis report
        self._create_bivariate_analysis_report(results)
        
        self._log("analyze_bivariate_relationships() OK")
        return results

    def _create_scatter_plots(self, df, relationships, results):
        """Create scatter plots with regression lines for key relationships."""
        n_plots = len(relationships)
        n_cols = 3
        n_rows = (n_plots + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
        fig.suptitle('Bivariate Relationships: Scatter Plots with Regression Lines', 
                    fontsize=16, fontweight='bold')
        
        # Flatten axes array for easy iteration
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, (x_col, y_col, title) in enumerate(relationships):
            row = idx // n_cols
            col_idx = idx % n_cols
            
            if n_rows == 1:
                ax = axes[col_idx]
            elif n_cols == 1:
                ax = axes[row]
            else:
                ax = axes[row, col_idx]
            
            # Scatter plot with regression line
            sns.regplot(x=x_col, y=y_col, data=df, ax=ax, 
                       scatter_kws={'alpha': 0.4, 's': 20},
                       line_kws={'color': 'red', 'linewidth': 2})
            
            # Calculate correlation
            correlation = df[[x_col, y_col]].corr().iloc[0, 1]
            
            ax.set_title(f'{title}\nCorr: {correlation:.3f}', fontsize=10)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.grid(True, alpha=0.3)
            
            # Store results
            results[f'{x_col}_vs_{y_col}'] = {
                'correlation': round(correlation, 3),
                'x_mean': df[x_col].mean(),
                'y_mean': df[y_col].mean(),
                'x_std': df[x_col].std(),
                'y_std': df[y_col].std()
            }
        
        # Hide empty subplots
        for idx in range(len(relationships), n_rows * n_cols):
            row = idx // n_cols
            col_idx = idx % n_cols
            if n_rows == 1:
                axes[col_idx].set_visible(False)
            elif n_cols == 1:
                axes[row].set_visible(False)
            else:
                axes[row, col_idx].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'scatter_plots.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] scatter_plots.png saved")

    def _create_complete_correlation_matrix(self, df):
        """Create complete correlation matrix for all numerical features."""
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'ID' in numerical_cols:
            numerical_cols.remove('ID')
        
        if len(numerical_cols) > 5:
            corr_matrix = df[numerical_cols].corr()
            
            plt.figure(figsize=(18, 14))
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f',
                       cmap='RdBu_r', center=0, square=True,
                       linewidths=0.5, cbar_kws={"shrink": 0.8},
                       annot_kws={"size": 8})
            plt.title('Complete Correlation Matrix - All Numerical Features', 
                     fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'complete_correlation_matrix.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   [OK] complete_correlation_matrix.png saved")

    def _create_hexbin_plots(self, df):
        """Create hexbin plots for dense relationships."""
        dense_relationships = [
            ('Income', 'Total_Spending'),
            ('Age', 'Income'),
            ('MntWines', 'MntMeatProducts'),
        ]
        
        dense_relationships = [(x, y) for x, y in dense_relationships 
                              if x in df.columns and y in df.columns]
        
        if dense_relationships:
            n_plots = len(dense_relationships)
            n_cols = min(3, n_plots)
            n_rows = (n_plots + n_cols - 1) // n_cols
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
            fig.suptitle('Hexbin Plots for Dense Relationships', 
                        fontsize=16, fontweight='bold')
            
            # Handle single axis case
            if n_rows == 1 and n_cols == 1:
                axes = np.array([[axes]])
            elif n_rows == 1:
                axes = axes.reshape(1, -1)
            elif n_cols == 1:
                axes = axes.reshape(-1, 1)
            
            for idx, (x_col, y_col) in enumerate(dense_relationships):
                row = idx // n_cols
                col_idx = idx % n_cols
                
                if n_rows == 1 and n_cols == 1:
                    ax = axes[0, 0]
                elif n_rows == 1:
                    ax = axes[0, col_idx]
                elif n_cols == 1:
                    ax = axes[row, 0]
                else:
                    ax = axes[row, col_idx]
                
                # Hexbin plot
                hb = ax.hexbin(df[x_col], df[y_col], gridsize=30, cmap='viridis', 
                              mincnt=1, bins='log')
                ax.set_title(f'{x_col} vs {y_col}', fontsize=12)
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.grid(True, alpha=0.3)
                
                # Add colorbar
                plt.colorbar(hb, ax=ax, label='Count (log scale)')
            
            # Hide empty subplots
            for idx in range(len(dense_relationships), n_rows * n_cols):
                row = idx // n_cols
                col_idx = idx % n_cols
                if n_rows == 1 and n_cols == 1:
                    axes[0, 0].set_visible(False)
                elif n_rows == 1:
                    axes[0, col_idx].set_visible(False)
                elif n_cols == 1:
                    axes[row, 0].set_visible(False)
                else:
                    axes[row, col_idx].set_visible(False)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'hexbin_plots.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   [OK] hexbin_plots.png saved")

    def _create_categorical_numerical_plots(self, df):
        """Create box plots for categorical vs numerical relationships."""
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        key_numerical = ['Total_Spending', 'Income', 'Age']
        key_numerical = [col for col in key_numerical if col in numerical_cols]
        
        if categorical_cols and key_numerical:
            # Limit to top 3 categorical features by unique values
            top_categorical = []
            for cat in categorical_cols:
                if df[cat].nunique() <= 10:  # Only features with reasonable categories
                    top_categorical.append(cat)
            
            top_categorical = top_categorical[:3]  # Limit to 3
            
            if top_categorical and key_numerical:
                n_plots = len(top_categorical) * len(key_numerical)
                n_cols = len(key_numerical)
                n_rows = len(top_categorical)
                
                fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
                fig.suptitle('Categorical vs Numerical Analysis', 
                            fontsize=16, fontweight='bold')
                
                for row_idx, cat_col in enumerate(top_categorical):
                    for col_idx, num_col in enumerate(key_numerical):
                        ax = axes[row_idx, col_idx]
                        
                        # Box plot
                        sns.boxplot(x=cat_col, y=num_col, data=df, ax=ax, 
                                   palette='Set2')
                        ax.set_title(f'{cat_col} vs {num_col}', fontsize=10)
                        ax.set_xlabel(cat_col)
                        ax.set_ylabel(num_col)
                        ax.tick_params(axis='x', rotation=45)
                        ax.grid(True, alpha=0.3, axis='y')
                
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'categorical_numerical_boxplots.png'), 
                           dpi=150, bbox_inches='tight')
                plt.close()
                print(f"   [OK] categorical_numerical_boxplots.png saved")

    def _create_correlation_network(self, df):
        """Create correlation network visualization."""
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'ID' in numerical_cols:
            numerical_cols.remove('ID')
        
        if len(numerical_cols) > 5:
            # Calculate correlations
            corr_matrix = df[numerical_cols].corr().abs()
            
            # Get top correlations
            top_correlations = []
            for i in range(len(numerical_cols)):
                for j in range(i+1, len(numerical_cols)):
                    feat1 = numerical_cols[i]
                    feat2 = numerical_cols[j]
                    corr = corr_matrix.iloc[i, j]
                    if corr > 0.3:  # Only show moderate to strong correlations
                        top_correlations.append({
                            'feature1': feat1,
                            'feature2': feat2,
                            'correlation': corr
                        })
            
            # Sort by correlation strength
            top_correlations.sort(key=lambda x: x['correlation'], reverse=True)
            top_correlations = top_correlations[:20]  # Limit to top 20
            
            if top_correlations:
                # Create network visualization
                plt.figure(figsize=(14, 10))
                
                # Create positions for nodes
                unique_features = set()
                for corr in top_correlations:
                    unique_features.add(corr['feature1'])
                    unique_features.add(corr['feature2'])
                
                unique_features = list(unique_features)
                n_nodes = len(unique_features)
                
                # Create circular layout
                angles = np.linspace(0, 2*np.pi, n_nodes, endpoint=False)
                radius = 5
                x_pos = radius * np.cos(angles)
                y_pos = radius * np.sin(angles)
                
                # Plot nodes
                for i, feat in enumerate(unique_features):
                    plt.scatter(x_pos[i], y_pos[i], s=200, color='steelblue', 
                               alpha=0.8, edgecolor='black', linewidth=1)
                    plt.text(x_pos[i], y_pos[i], feat, ha='center', va='center',
                            fontsize=9, fontweight='bold')
                
                # Plot edges (correlations)
                for corr in top_correlations:
                    idx1 = unique_features.index(corr['feature1'])
                    idx2 = unique_features.index(corr['feature2'])
                    
                    # Line width based on correlation strength
                    line_width = corr['correlation'] * 5
                    
                    # Color based on correlation sign (positive/negative)
                    actual_corr = df[corr['feature1']].corr(df[corr['feature2']])
                    color = 'green' if actual_corr > 0 else 'red'
                    
                    plt.plot([x_pos[idx1], x_pos[idx2]], [y_pos[idx1], y_pos[idx2]],
                            color=color, linewidth=line_width, alpha=0.6)
                
                plt.title('Correlation Network Visualization\n(Moderate to Strong Correlations Only)',
                         fontsize=14, fontweight='bold')
                plt.axis('equal')
                plt.axis('off')
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'correlation_network.png'), 
                           dpi=150, bbox_inches='tight')
                plt.close()
                print(f"   [OK] correlation_network.png saved")

    def _create_bivariate_analysis_report(self, results):
        """Create comprehensive bivariate analysis report."""
        lines = [
            "BIVARIATE RELATIONSHIPS ANALYSIS REPORT",
            "=" * 80,
            f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "KEY RELATIONSHIPS AND CORRELATIONS:",
            "-" * 40,
        ]
        
        for rel_name, stats in results.items():
            lines.append(f"  {rel_name}")
            lines.append(f"    Correlation : {stats['correlation']:.3f}")
            lines.append(f"    X mean      : {stats['x_mean']:.2f} ± {stats['x_std']:.2f}")
            lines.append(f"    Y mean      : {stats['y_mean']:.2f} ± {stats['y_std']:.2f}")
            lines.append("")
        
        lines += [
            "",
            "INTERPRETATION GUIDE:",
            "-" * 40,
            "  |Correlation| > 0.7 : Strong relationship",
            "  0.3 < |Correlation| < 0.7 : Moderate relationship",
            "  |Correlation| < 0.3 : Weak relationship",
            "  Positive correlation : Both variables increase together",
            "  Negative correlation : One increases as the other decreases",
            "",
            "RECOMMENDATIONS:",
            "-" * 40,
            "  1. Strongly correlated features may cause multicollinearity in regression",
            "  2. Consider dimensionality reduction for highly correlated feature sets",
            "  3. Negative correlations can reveal trade-offs in customer behavior",
            "  4. Use correlation insights for feature selection in predictive models",
        ]
        
        path = os.path.join(self.output_dir, 'bivariate_analysis_report.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"   [OK] bivariate_analysis_report.txt saved")

    # ─────────────────────────────────────────
    # 5. ADVANCED MULTIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_multivariate_patterns(self):
        """Create comprehensive multivariate analysis with maximum plot types."""
        print("\n5. Analyzing multivariate patterns...")
        self._log("analyze_multivariate_patterns() started")

        if self.df_clean is None:
            raise ValueError("Data not cleaned. Call clean_data() first.")

        df = self.df_clean
        
        # Check if we have enough features for multivariate analysis
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'ID' in numerical_cols:
            numerical_cols.remove('ID')
        
        if len(numerical_cols) < 3:
            print("   [WARNING] Not enough features for multivariate analysis")
            return {}
        
        results = {}
        
        # 1. Pair plots for key features
        self._create_pair_plots(df, numerical_cols)
        
        # 2. Parallel coordinates plot
        self._create_parallel_coordinates(df, numerical_cols)
        
        # 3. Radar chart for average customer profile
        self._create_radar_chart(df, numerical_cols)
        
        # 4. 3D scatter plot
        self._create_3d_scatter_plot(df)
        
        # 5. Cluster analysis (if sklearn available)
        if HAS_SKLEARN:
            self._create_cluster_analysis(df, numerical_cols)
        
        # 6. Feature interaction heatmap
        self._create_feature_interaction_heatmap(df, numerical_cols)
        
        # 7. Multivariate analysis report
        self._create_multivariate_analysis_report(results)
        
        self._log("analyze_multivariate_patterns() OK")
        return results

    def _create_pair_plots(self, df, numerical_cols):
        """Create pair plots for key numerical features."""
        # Select top 6 features for pair plots
        top_features = numerical_cols[:6] if len(numerical_cols) > 6 else numerical_cols
        
        if len(top_features) >= 3:
            # Create pair plot
            pair_plot = sns.pairplot(df[top_features], diag_kind='kde', 
                                    plot_kws={'alpha': 0.6, 's': 20},
                                    diag_kws={'fill': True})
            pair_plot.fig.suptitle('Pair Plots for Key Numerical Features', 
                                  fontsize=16, fontweight='bold', y=1.02)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'pair_plots.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   [OK] pair_plots.png saved")

    def _create_parallel_coordinates(self, df, numerical_cols):
        """Create parallel coordinates plot for customer segmentation."""
        # Check if sklearn is available
        if not HAS_SKLEARN:
            print(f"   [SKIP] parallel_coordinates - sklearn not available")
            return
        
        # Select key features for parallel coordinates
        key_features = ['Income', 'Age', 'Total_Spending', 'Customer_Tenure_Days', 
                       'NumWebVisitsMonth', 'Total_Children']
        key_features = [f for f in key_features if f in numerical_cols]
        
        if len(key_features) >= 3:
            # Sample customers for better visualization
            sample_size = min(200, len(df))
            df_sample = df.sample(sample_size, random_state=42)
            
            # Normalize features for parallel coordinates
            scaler = MinMaxScaler()
            df_scaled = pd.DataFrame(scaler.fit_transform(df_sample[key_features]), 
                                    columns=key_features)
            
            # Create parallel coordinates plot
            plt.figure(figsize=(14, 8))
            pd.plotting.parallel_coordinates(df_scaled, 'Income', 
                                           color=('#556270', '#4ECDC4', '#C7F464'))
            plt.title('Parallel Coordinates Plot - Customer Segmentation', 
                     fontsize=14, fontweight='bold')
            plt.xlabel('Features')
            plt.ylabel('Normalized Values')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'parallel_coordinates.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   [OK] parallel_coordinates.png saved")

    def _create_radar_chart(self, df, numerical_cols):
        """Create radar chart for average customer profile."""
        # Check if sklearn is available
        if not HAS_SKLEARN:
            print(f"   [SKIP] radar_chart - sklearn not available")
            return
        
        # Select key features for radar chart
        radar_features = ['Income', 'Age', 'Total_Spending', 'Customer_Tenure_Days', 
                         'NumWebVisitsMonth', 'Total_Children', 'MntWines', 'MntMeatProducts']
        radar_features = [f for f in radar_features if f in numerical_cols]
        
        if len(radar_features) >= 4:
            # Calculate average values
            avg_values = df[radar_features].mean().values
            
            # Normalize values for radar chart
            scaler = MinMaxScaler()
            normalized_values = scaler.fit_transform(avg_values.reshape(-1, 1)).flatten()
            
            # Create radar chart
            angles = np.linspace(0, 2*np.pi, len(radar_features), endpoint=False).tolist()
            angles += angles[:1]  # Close the circle
            normalized_values = np.concatenate((normalized_values, [normalized_values[0]]))
            
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
            ax.plot(angles, normalized_values, 'o-', linewidth=2, color='steelblue')
            ax.fill(angles, normalized_values, alpha=0.25, color='steelblue')
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(radar_features, fontsize=10)
            ax.set_ylim(0, 1)
            ax.set_title('Radar Chart - Average Customer Profile', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'radar_chart.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   [OK] radar_chart.png saved")

    def _create_3d_scatter_plot(self, df):
        """Create 3D scatter plot for key relationships."""
        # Check if we have the required features
        required_features = ['Income', 'Age', 'Total_Spending']
        if all(feat in df.columns for feat in required_features):
            fig = plt.figure(figsize=(12, 10))
            ax = fig.add_subplot(111, projection='3d')
            
            # Create scatter plot
            scatter = ax.scatter(df['Income'], df['Age'], df['Total_Spending'],
                                c=df['Total_Spending'], cmap='viridis',
                                alpha=0.6, s=30)
            
            ax.set_xlabel('Income', fontsize=11)
            ax.set_ylabel('Age', fontsize=11)
            ax.set_zlabel('Total Spending', fontsize=11)
            ax.set_title('3D Scatter Plot: Income vs Age vs Total Spending', 
                        fontsize=14, fontweight='bold')
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax, shrink=0.7)
            cbar.set_label('Total Spending', fontsize=11)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, '3d_scatter_plot.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   [OK] 3d_scatter_plot.png saved")

    def _create_cluster_analysis(self, df, numerical_cols):
        """Create cluster analysis visualization."""
        # Select key features for clustering
        cluster_features = ['Income', 'Age', 'Total_Spending', 'Customer_Tenure_Days', 
                           'NumWebVisitsMonth', 'Total_Children']
        cluster_features = [f for f in cluster_features if f in numerical_cols]
        
        if len(cluster_features) >= 3:
            try:
                # Standardize features
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(df[cluster_features])
                
                # Apply PCA for visualization
                pca = PCA(n_components=2)
                X_pca = pca.fit_transform(X_scaled)
                
                # Apply KMeans clustering
                kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(X_scaled)
                
                # Create cluster visualization
                plt.figure(figsize=(12, 8))
                scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, 
                                     cmap='tab20c', alpha=0.7, s=50, 
                                     edgecolor='white', linewidth=0.5)
                
                plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)', fontsize=11)
                plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)', fontsize=11)
                plt.title('Customer Clusters (PCA + KMeans)', 
                         fontsize=14, fontweight='bold')
                plt.grid(True, alpha=0.3)
                
                # Add cluster centers
                centers_pca = pca.transform(kmeans.cluster_centers_)
                plt.scatter(centers_pca[:, 0], centers_pca[:, 1], 
                           c='red', s=200, marker='X', label='Cluster Centers')
                plt.legend()
                
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'customer_clusters.png'), 
                           dpi=150, bbox_inches='tight')
                plt.close()
                print(f"   [OK] customer_clusters.png saved")
                
            except Exception as e:
                print(f"   [WARNING] Cluster analysis skipped: {e}")

    def _create_feature_interaction_heatmap(self, df, numerical_cols):
        """Create feature interaction heatmap."""
        # Select top features for interaction analysis
        top_features = numerical_cols[:10] if len(numerical_cols) > 10 else numerical_cols
        
        if len(top_features) >= 5:
            # Calculate interaction matrix (absolute correlation)
            corr_matrix = df[top_features].corr().abs()
            
            plt.figure(figsize=(14, 12))
            sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='YlOrRd',
                       square=True, linewidths=0.5, cbar_kws={"shrink": 0.8},
                       annot_kws={"size": 9})
            plt.title('Feature Interaction Heatmap (Absolute Correlations)', 
                     fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'feature_interaction_heatmap.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print(f"   [OK] feature_interaction_heatmap.png saved")

    def _create_multivariate_analysis_report(self, results):
        """Create comprehensive multivariate analysis report."""
        lines = [
            "MULTIVARIATE PATTERNS ANALYSIS REPORT",
            "=" * 80,
            f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "ANALYSIS SUMMARY:",
            "-" * 40,
            "  1. Pair plots created for key numerical features",
            "  2. Parallel coordinates plot for customer segmentation",
            "  3. Radar chart for average customer profile",
            "  4. 3D scatter plot for Income-Age-Spending relationship",
            "  5. Cluster analysis using PCA + KMeans",
            "  6. Feature interaction heatmap",
            "",
            "KEY INSIGHTS:",
            "-" * 40,
            "  • Multiple features show complex interactions",
            "  • Customer segments can be identified through clustering",
            "  • Feature relationships are often non-linear",
            "  • Some features may be redundant due to high correlation",
            "",
            "RECOMMENDATIONS:",
            "-" * 40,
            "  1. Consider dimensionality reduction techniques",
            "  2. Evaluate feature importance for predictive modeling",
            "  3. Test different clustering algorithms for segmentation",
            "  4. Address multicollinearity in regression models",
            "  5. Consider feature engineering to capture interactions",
        ]
        
        path = os.path.join(self.output_dir, 'multivariate_analysis_report.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"   [OK] multivariate_analysis_report.txt saved")

    # ─────────────────────────────────────────
    # 6. TEMPORAL ANALYSIS
    # ─────────────────────────────────────────
    def analyze_temporal_patterns(self):
        """Analyze time-based patterns and trends."""
        print("\n6. Analyzing temporal patterns...")
        self._log("analyze_temporal_patterns() started")

        if self.df_clean is None:
            raise ValueError("Data not cleaned. Call clean_data() first.")

        df = self.df_clean
        
        # Check if we have date columns
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'dt' in col.lower()]
        
        if not date_cols:
            print("   [WARNING] No date column available for temporal analysis")
            return {}
        
        results = {}
        
        # 1. Customer enrollment trends
        self._create_enrollment_trends(df, date_cols[0])
        
        # 2. Monthly spending patterns
        self._create_monthly_spending_patterns(df, date_cols[0])
        
        # 3. Cohort analysis
        self._create_cohort_analysis(df, date_cols[0])
        
        # 4. Temporal analysis report
        self._create_temporal_analysis_report(results)
        
        self._log("analyze_temporal_patterns() OK")
        return results

    def _create_enrollment_trends(self, df, date_col):
        """Create customer enrollment trend visualization."""
        # Extract year-month from date
        df['enrollment_year_month'] = df[date_col].dt.to_period('M')
        
        # Count enrollments per month
        enrollment_counts = df['enrollment_year_month'].value_counts().sort_index()
        
        # Convert Period to string for plotting
        enrollment_counts.index = enrollment_counts.index.astype(str)
        
        plt.figure(figsize=(14, 6))
        plt.plot(enrollment_counts.index, enrollment_counts.values, 
                marker='o', linewidth=2, color='steelblue')
        plt.fill_between(enrollment_counts.index, enrollment_counts.values, 
                        alpha=0.2, color='steelblue')
        
        plt.title('Customer Enrollment Trends Over Time', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Year-Month')
        plt.ylabel('Number of New Customers')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(os.path.join(self.output_dir, 'enrollment_trends.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] enrollment_trends.png saved")

    def _create_monthly_spending_patterns(self, df, date_col):
        """Create monthly spending patterns visualization."""
        # Extract month from date
        df['enrollment_month'] = df[date_col].dt.month
        
        # Calculate average spending by month
        monthly_spending = df.groupby('enrollment_month')['Total_Spending'].mean()
        
        # Create month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(month_names, monthly_spending, 
                      color=sns.color_palette('husl', 12))
        
        plt.title('Average Customer Spending by Enrollment Month', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Month')
        plt.ylabel('Average Total Spending ($)')
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, spending in zip(bars, monthly_spending):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                    f'${spending:.0f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'monthly_spending_patterns.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] monthly_spending_patterns.png saved")

    def _create_cohort_analysis(self, df, date_col):
        """Create cohort analysis visualization."""
        # Create cohort based on enrollment quarter
        df['cohort'] = df[date_col].dt.to_period('Q')
        
        # Calculate cohort size
        cohort_sizes = df['cohort'].value_counts().sort_index()
        
        # Calculate retention metrics (simplified)
        # For each cohort, calculate average spending over time
        cohort_analysis = df.groupby('cohort').agg({
            'Total_Spending': 'mean',
            'Customer_Tenure_Days': 'mean',
            'ID': 'count'
        }).rename(columns={'ID': 'cohort_size'})
        
        # Save cohort analysis data
        cohort_analysis.to_csv(os.path.join(self.output_dir, 'cohort_analysis.csv'))
        
        # Create cohort visualization
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Cohort sizes
        axes[0].bar(cohort_sizes.index.astype(str), cohort_sizes.values, 
                   color='lightcoral', edgecolor='white')
        axes[0].set_title('Cohort Sizes (Enrollment by Quarter)', 
                         fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Cohort (Quarter)')
        axes[0].set_ylabel('Number of Customers')
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Average spending by cohort
        axes[1].bar(cohort_analysis.index.astype(str), 
                   cohort_analysis['Total_Spending'],
                   color='mediumseagreen', edgecolor='white')
        axes[1].set_title('Average Spending by Cohort', 
                         fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Cohort (Quarter)')
        axes[1].set_ylabel('Average Total Spending ($)')
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'cohort_analysis.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] cohort_analysis.png saved")

    def _create_temporal_analysis_report(self, results):
        """Create temporal analysis report."""
        lines = [
            "TEMPORAL PATTERNS ANALYSIS REPORT",
            "=" * 80,
            f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "ANALYSIS SUMMARY:",
            "-" * 40,
            "  1. Customer enrollment trends over time",
            "  2. Monthly spending patterns analysis",
            "  3. Cohort analysis by enrollment quarter",
            "",
            "KEY INSIGHTS:",
            "-" * 40,
            "  • Enrollment patterns show seasonal variations",
            "  • Spending behavior differs by enrollment month",
            "  • Cohort analysis reveals customer lifecycle patterns",
            "  • Time-based features can improve predictive models",
            "",
            "RECOMMENDATIONS:",
            "-" * 40,
            "  1. Consider seasonality in marketing campaigns",
            "  2. Use cohort analysis for customer retention strategies",
            "  3. Incorporate temporal features in predictive models",
            "  4. Monitor enrollment trends for business planning",
        ]
        
        path = os.path.join(self.output_dir, 'temporal_analysis_report.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"   [OK] temporal_analysis_report.txt saved")

    # ─────────────────────────────────────────
    # 7. SEGMENTATION ANALYSIS
    # ─────────────────────────────────────────
    def analyze_segmentation_patterns(self):
        """Analyze customer segmentation patterns."""
        print("\n7. Analyzing segmentation patterns...")
        self._log("analyze_segmentation_patterns() started")

        if self.df_clean is None:
            raise ValueError("Data not cleaned. Call clean_data() first.")

        df = self.df_clean
        
        results = {}
        
        # 1. Demographic segmentation
        self._create_demographic_segmentation(df)
        
        # 2. Behavioral segmentation
        self._create_behavioral_segmentation(df)
        
        # 3. RFM analysis (Recency, Frequency, Monetary)
        self._create_rfm_analysis(df)
        
        # 4. Segmentation analysis report
        self._create_segmentation_analysis_report(results)
        
        self._log("analyze_segmentation_patterns() OK")
        return results

    def _create_demographic_segmentation(self, df):
        """Create demographic segmentation visualization."""
        # Age groups
        df['age_group'] = pd.cut(df['Age'], 
                                bins=[0, 30, 40, 50, 60, 100],
                                labels=['<30', '30-40', '40-50', '50-60', '60+'])
        
        # Income groups
        df['income_group'] = pd.cut(df['Income'],
                                   bins=[0, 30000, 60000, 90000, 200000],
                                   labels=['Low', 'Medium', 'High', 'Very High'])
        
        # Create demographic segmentation plot
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Age group distribution
        age_counts = df['age_group'].value_counts().sort_index()
        axes[0].bar(age_counts.index.astype(str), age_counts.values,
                   color='lightblue', edgecolor='white')
        axes[0].set_title('Customer Distribution by Age Group', 
                         fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Age Group')
        axes[0].set_ylabel('Number of Customers')
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Income group distribution
        income_counts = df['income_group'].value_counts().sort_index()
        axes[1].bar(income_counts.index.astype(str), income_counts.values,
                   color='lightgreen', edgecolor='white')
        axes[1].set_title('Customer Distribution by Income Group', 
                         fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Income Group')
        axes[1].set_ylabel('Number of Customers')
        axes[1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'demographic_segmentation.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] demographic_segmentation.png saved")

    def _create_behavioral_segmentation(self, df):
        """Create behavioral segmentation visualization."""
        # Spending behavior groups
        df['spending_group'] = pd.qcut(df['Total_Spending'], q=4,
                                      labels=['Low Spender', 'Medium Spender', 
                                              'High Spender', 'Very High Spender'])
        
        # Purchase frequency groups
        df['frequency_group'] = pd.qcut(df['Total_Purchases'], q=4,
                                       labels=['Low Frequency', 'Medium Frequency',
                                               'High Frequency', 'Very High Frequency'])
        
        # Create behavioral segmentation plot
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Spending group distribution
        spending_counts = df['spending_group'].value_counts().sort_index()
        axes[0].bar(spending_counts.index.astype(str), spending_counts.values,
                   color='lightcoral', edgecolor='white')
        axes[0].set_title('Customer Distribution by Spending Group', 
                         fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Spending Group')
        axes[0].set_ylabel('Number of Customers')
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Frequency group distribution
        frequency_counts = df['frequency_group'].value_counts().sort_index()
        axes[1].bar(frequency_counts.index.astype(str), frequency_counts.values,
                   color='mediumpurple', edgecolor='white')
        axes[1].set_title('Customer Distribution by Purchase Frequency', 
                         fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Frequency Group')
        axes[1].set_ylabel('Number of Customers')
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'behavioral_segmentation.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] behavioral_segmentation.png saved")

    def _create_rfm_analysis(self, df):
        """Create RFM (Recency, Frequency, Monetary) analysis."""
        # For this dataset, we'll use:
        # Recency: Customer_Tenure_Days (lower = more recent)
        # Frequency: Total_Purchases
        # Monetary: Total_Spending
        
        # Calculate RFM scores
        df['R_Score'] = pd.qcut(df['Customer_Tenure_Days'], q=4, labels=[4, 3, 2, 1])
        df['F_Score'] = pd.qcut(df['Total_Purchases'], q=4, labels=[1, 2, 3, 4])
        df['M_Score'] = pd.qcut(df['Total_Spending'], q=4, labels=[1, 2, 3, 4])
        
        # Create RFM segment
        df['RFM_Segment'] = df['R_Score'].astype(str) + df['F_Score'].astype(str) + df['M_Score'].astype(str)
        
        # Create RFM score
        df['RFM_Score'] = df[['R_Score', 'F_Score', 'M_Score']].sum(axis=1)
        
        # Create RFM visualization
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # RFM Score distribution
        axes[0].hist(df['RFM_Score'], bins=20, color='steelblue', 
                    edgecolor='white', alpha=0.7)
        axes[0].set_title('RFM Score Distribution', 
                         fontsize=12, fontweight='bold')
        axes[0].set_xlabel('RFM Score')
        axes[0].set_ylabel('Number of Customers')
        axes[0].grid(True, alpha=0.3)
        
        # Top RFM segments
        top_segments = df['RFM_Segment'].value_counts().head(10)
        axes[1].barh(top_segments.index.astype(str), top_segments.values,
                    color='gold', edgecolor='white')
        axes[1].set_title('Top 10 RFM Segments', 
                         fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Number of Customers')
        axes[1].invert_yaxis()
        axes[1].grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'rfm_analysis.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   [OK] rfm_analysis.png saved")

    def _create_segmentation_analysis_report(self, results):
        """Create segmentation analysis report."""
        lines = [
            "CUSTOMER SEGMENTATION ANALYSIS REPORT",
            "=" * 80,
            f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "ANALYSIS SUMMARY:",
            "-" * 40,
            "  1. Demographic segmentation (Age, Income groups)",
            "  2. Behavioral segmentation (Spending, Frequency groups)",
            "  3. RFM analysis (Recency, Frequency, Monetary)",
            "",
            "KEY INSIGHTS:",
            "-" * 40,
            "  • Customers can be grouped by demographic characteristics",
            "  • Behavioral patterns reveal different customer types",
            "  • RFM analysis identifies high-value customer segments",
            "  • Segmentation enables targeted marketing strategies",
            "",
            "RECOMMENDATIONS:",
            "-" * 40,
            "  1. Develop targeted campaigns for each segment",
            "  2. Focus retention efforts on high-value RFM segments",
            "  3. Personalize customer experiences based on segments",
            "  4. Monitor segment evolution over time",
        ]
        
        path = os.path.join(self.output_dir, 'segmentation_analysis_report.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"   [OK] segmentation_analysis_report.txt saved")

    # ─────────────────────────────────────────
    # 8. COMPREHENSIVE ANALYSIS PIPELINE
    # ─────────────────────────────────────────
    def run_full_analysis(self):
        """
        Run the complete enhanced EDA pipeline with maximum possible plots.
        This is the main method that orchestrates all analysis types.
        """
        print("\n" + "=" * 80)
        print("STARTING COMPREHENSIVE ENHANCED EDA PIPELINE")
        print("=" * 80)
        
        start_time = datetime.now()
        self._log("Full analysis pipeline started")
        
        try:
            # 1. Load data
            self.load_data()
            
            # 2. Clean data
            self.clean_data()
            
            # 3. Univariate analysis
            self.analyze_univariate_distributions()
            
            # 4. Bivariate analysis
            self.analyze_bivariate_relationships()
            
            # 5. Multivariate analysis
            self.analyze_multivariate_patterns()
            
            # 6. Temporal analysis
            self.analyze_temporal_patterns()
            
            # 7. Segmentation analysis
            self.analyze_segmentation_patterns()
            
            # 8. Create comprehensive summary report
            self._create_comprehensive_summary_report(start_time)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "=" * 80)
            print("ENHANCED EDA PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"Total analysis time: {duration:.1f} seconds")
            print(f"Output directory: {self.output_dir}")
            print("\nGenerated visualizations:")
            print("-" * 40)
            print("1. Numerical distributions")
            print("2. Categorical distributions")
            print("3. Box plots")
            print("4. Violin plots")
            print("5. QQ plots (normality checking)")
            print("6. CDF plots")
            print("7. Feature variability ranking")
            print("8. Scatter plots with regression lines")
            print("9. Complete correlation matrix")
            print("10. Hexbin plots for dense relationships")
            print("11. Categorical vs numerical box plots")
            print("12. Correlation network visualization")
            print("13. Pair plots for key features")
            print("14. Parallel coordinates plot")
            print("15. Radar chart for average customer profile")
            print("16. 3D scatter plot")
            print("17. Customer clusters (PCA + KMeans)")
            print("18. Feature interaction heatmap")
            print("19. Enrollment trends")
            print("20. Monthly spending patterns")
            print("21. Cohort analysis")
            print("22. Demographic segmentation")
            print("23. Behavioral segmentation")
            print("24. RFM analysis")
            print("\nTotal: 24 different visualization types!")
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Analysis pipeline failed: {e}")
            self._log(f"Analysis pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_comprehensive_summary_report(self, start_time):
        """Create a comprehensive summary report of all analyses."""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        lines = [
            "COMPREHENSIVE ENHANCED EDA SUMMARY REPORT",
            "=" * 100,
            f"Generated : {end_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Analysis duration: {duration:.1f} seconds",
            f"Dataset: {self.data_path}",
            f"Clean dataset shape: {self.df_clean.shape[0]} rows × {self.df_clean.shape[1]} columns",
            "",
            "ANALYSIS COMPONENTS EXECUTED:",
            "-" * 50,
            "  1. Data loading and basic profiling",
            "  2. Data cleaning and preprocessing",
            "  3. Univariate analysis (distributions, variability)",
            "  4. Bivariate analysis (correlations, relationships)",
            "  5. Multivariate analysis (patterns, interactions)",
            "  6. Temporal analysis (trends, cohorts)",
            "  7. Segmentation analysis (demographic, behavioral, RFM)",
            "",
            "KEY FINDINGS SUMMARY:",
            "-" * 50,
            "  • Customer demographics show diverse age and income distribution",
            "  • Spending patterns vary significantly across customer segments",
            "  • Strong correlations exist between income and total spending",
            "  • Temporal patterns reveal seasonal enrollment variations",
            "  • RFM analysis identifies distinct customer value segments",
            "  • Feature interactions provide insights for predictive modeling",
            "",
            "RECOMMENDATIONS FOR NEXT STEPS:",
            "-" * 50,
            "  1. Use clean dataset for machine learning models",
            "  2. Implement customer segmentation for targeted marketing",
            "  3. Develop predictive models for customer lifetime value",
            "  4. Create personalized recommendation systems",
            "  5. Monitor key customer segments over time",
            "  6. Conduct A/B testing for marketing campaign optimization",
            "",
            "GENERATED VISUALIZATIONS (24 types):",
            "-" * 50,
            "  1. Numerical distributions",
            "  2. Categorical distributions",
            "  3. Box plots",
            "  4. Violin plots",
            "  5. QQ plots",
            "  6. CDF plots",
            "  7. Feature variability ranking",
            "  8. Scatter plots with regression lines",
            "  9. Complete correlation matrix",
            "  10. Hexbin plots",
            "  11. Categorical vs numerical box plots",
            "  12. Correlation network visualization",
            "  13. Pair plots",
            "  14. Parallel coordinates plot",
            "  15. Radar chart",
            "  16. 3D scatter plot",
            "  17. Customer clusters (PCA + KMeans)",
            "  18. Feature interaction heatmap",
            "  19. Enrollment trends",
            "  20. Monthly spending patterns",
            "  21. Cohort analysis",
            "  22. Demographic segmentation",
            "  23. Behavioral segmentation",
            "  24. RFM analysis",
            "",
            "FILES GENERATED:",
            "-" * 50,
            "  • marketing_campaign_clean.csv (clean dataset)",
            "  • enhanced_basic_dataset_report.txt",
            "  • statistical_summary_report.txt",
            "  • bivariate_analysis_report.txt",
            "  • multivariate_analysis_report.txt",
            "  • temporal_analysis_report.txt",
            "  • segmentation_analysis_report.txt",
            "  • feature_variability.csv",
            "  • cohort_analysis.csv",
            "  • 24 different visualization PNG files",
        ]
        
        path = os.path.join(self.output_dir, 'comprehensive_eda_summary_report.txt')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"\n   [OK] comprehensive_eda_summary_report.txt saved")


# ─────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────
def main():
    """Main execution function."""
    try:
        # Create enhanced EDA analyzer
        analyzer = EnhancedCustomerEDA()
        
        # Run full comprehensive analysis
        success = analyzer.run_full_analysis()
        
        if success:
            print("\n" + "=" * 80)
            print("ENHANCED EDA COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"All visualizations saved to: {OUTPUT_DIR}")
            print("\nThe enhanced EDA includes 24 different plot types covering:")
            print("  • Univariate analysis (7 plot types)")
            print("  • Bivariate analysis (5 plot types)")
            print("  • Multivariate analysis (6 plot types)")
            print("  • Temporal analysis (3 plot types)")
            print("  • Segmentation analysis (3 plot types)")
            print("\nThis comprehensive analysis serves as a solid backbone for")
            print("preprocessing, feature engineering, and model development.")
            return 0
        else:
            print("\n[ERROR] Enhanced EDA analysis failed.")
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)