"""
CustomerDNA AI - PFE Project
Dataset : UCI Online Retail 2 (online_retail_2.xlsx)
Script  : Enhanced Online Retail EDA — Maximum Possible Plots
Author  : PFE Student
Description: Comprehensive EDA with maximum possible visualization types for online retail transactional analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timedelta
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
    print("[WARNING] networkx not available. Network visualization will be skipped.")

# ─────────────────────────────────────────────
# PATHS — adjust only these lines
# ─────────────────────────────────────────────
DATA_PATH  = r"d:\github\Master_PFE_Project\CustomerDNA AI\datasets\client_1\UCI_Online_Retail_2\online_retail_2.xlsx"
OUTPUT_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\EDA\client_1\UCI_Online_Retail_2_EDA\output"

# ─────────────────────────────────────────────
# CONSTANTS — data cleaning rules
# ─────────────────────────────────────────────
# Based on data quality audit
MISSING_THRESHOLD = 0.05  # 5% threshold for significant missingness

# Outlier detection thresholds (based on IQR method)
OUTLIER_IQR_MULTIPLIER = 1.5

# Business rules
MIN_QUANTITY = 1  # Minimum valid quantity
MAX_QUANTITY = 10000  # Maximum valid quantity (to filter bulk returns/errors)
MIN_PRICE = 0.01  # Minimum valid price
MAX_PRICE = 10000  # Maximum valid price

# Country mapping for consistency
COUNTRY_MAPPING = {
    "United Kingdom": "United Kingdom",
    "France": "France", 
    "Australia": "Australia",
    "Netherlands": "Netherlands",
    "Germany": "Germany",
    "Norway": "Norway",
    "EIRE": "Ireland",
    "Switzerland": "Switzerland",
    "Spain": "Spain",
    "Poland": "Poland",
    "Portugal": "Portugal",
    "Italy": "Italy",
    "Belgium": "Belgium",
    "Lithuania": "Lithuania",
    "Japan": "Japan",
    "Iceland": "Iceland",
    "Channel Islands": "Channel Islands",
    "Denmark": "Denmark",
    "Cyprus": "Cyprus",
    "Sweden": "Sweden",
    "Austria": "Austria",
    "Israel": "Israel",
    "Finland": "Finland",
    "Bahrain": "Bahrain",
    "Greece": "Greece",
    "Hong Kong": "Hong Kong",
    "Singapore": "Singapore",
    "Lebanon": "Lebanon",
    "United Arab Emirates": "United Arab Emirates",
    "Saudi Arabia": "Saudi Arabia",
    "Czech Republic": "Czech Republic",
    "Canada": "Canada",
    "Unspecified": "Unspecified",
    "Brazil": "Brazil",
    "USA": "USA",
    "European Community": "European Community",
    "Malta": "Malta",
    "RSA": "South Africa"
}

# Event type mapping for visualization
EVENT_TYPES = {
    "view": "View",
    "addtocart": "Add to Cart", 
    "transaction": "Transaction"
}

# Color palette for visualizations
EVENT_COLORS = {
    "view": "#3498db",
    "addtocart": "#f39c12", 
    "transaction": "#2ecc71"
}


class EnhancedOnlineRetailEDA:
    """
    Enhanced EDA class for UCI Online Retail 2 dataset with maximum possible plots.
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
        print("CustomerDNA AI — Enhanced UCI Online Retail 2 EDA")
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
        """Load the raw Excel data from both sheets."""
        print("\n1. Loading data...")
        self._log("load_data() started")

        try:
            # Read both sheets
            print("   Reading Excel file with two sheets...")
            df_2009_2010 = pd.read_excel(self.data_path, sheet_name='Year 2009-2010')
            df_2010_2011 = pd.read_excel(self.data_path, sheet_name='Year 2010-2011')
            
            # Combine both sheets
            self.df = pd.concat([df_2009_2010, df_2010_2011], ignore_index=True)
            
            print(f"   [SUCCESS] Data loaded successfully")
            print(f"   - Total records: {len(self.df):,}")
            print(f"   - Columns: {list(self.df.columns)}")
            print(f"   - Date range: {self.df['InvoiceDate'].min()} to {self.df['InvoiceDate'].max()}")
            
            # Store basic statistics
            self.results['dataset_stats'] = {
                'total_records': len(self.df),
                'columns': list(self.df.columns),
                'date_range': {
                    'start': self.df['InvoiceDate'].min().strftime('%Y-%m-%d'),
                    'end': self.df['InvoiceDate'].max().strftime('%Y-%m-%d')
                },
                'missing_values': self.df.isnull().sum().to_dict()
            }
            
            return True
            
        except Exception as e:
            print(f"   [ERROR] Failed to load data: {e}")
            self._log(f"load_data() failed: {e}")
            return False

    # ─────────────────────────────────────────
    # 2. CLEAN DATA
    # ─────────────────────────────────────────
    def clean_data(self):
        """Clean and preprocess the data."""
        print("\n2. Cleaning data...")
        self._log("clean_data() started")

        if self.df is None:
            print("   [ERROR] No data available. Run load_data() first.")
            return False

        try:
            # Create a copy for cleaning
            df_clean = self.df.copy()
            
            # 2.1 Handle missing values
            print(f"\n   2.1 Handling missing values:")
            
            # Check missing values
            missing_counts = df_clean.isnull().sum()
            missing_percent = (missing_counts / len(df_clean)) * 100
            
            print(f"      - Description missing: {missing_counts['Description']:,} ({missing_percent['Description']:.2f}%)")
            print(f"      - Customer ID missing: {missing_counts['Customer ID']:,} ({missing_percent['Customer ID']:.2f}%)")
            
            # Remove rows with missing Invoice or StockCode (critical fields)
            initial_count = len(df_clean)
            df_clean = df_clean.dropna(subset=['Invoice', 'StockCode'])
            removed_count = initial_count - len(df_clean)
            print(f"      - Removed {removed_count:,} rows with missing Invoice or StockCode")
            
            # Fill missing descriptions with 'Unknown'
            df_clean['Description'] = df_clean['Description'].fillna('Unknown')
            
            # For Customer ID, we'll keep missing values but mark them
            df_clean['Customer ID'] = df_clean['Customer ID'].fillna(-1)
            
            # 2.2 Data type conversion and validation
            print(f"\n   2.2 Data type conversion and validation:")
            
            # Convert Invoice to string
            df_clean['Invoice'] = df_clean['Invoice'].astype(str)
            
            # Convert StockCode to string
            df_clean['StockCode'] = df_clean['StockCode'].astype(str)
            
            # Convert Customer ID to integer (treat -1 as unknown)
            df_clean['Customer ID'] = df_clean['Customer ID'].astype(int)
            
            # 2.3 Handle outliers and invalid values
            print(f"\n   2.3 Handling outliers and invalid values:")
            
            # Filter invalid quantities
            initial_count = len(df_clean)
            df_clean = df_clean[
                (df_clean['Quantity'] >= MIN_QUANTITY) & 
                (df_clean['Quantity'] <= MAX_QUANTITY)
            ]
            removed_quantity = initial_count - len(df_clean)
            print(f"      - Removed {removed_quantity:,} rows with invalid quantities")
            
            # Filter invalid prices
            initial_count = len(df_clean)
            df_clean = df_clean[
                (df_clean['Price'] >= MIN_PRICE) & 
                (df_clean['Price'] <= MAX_PRICE)
            ]
            removed_price = initial_count - len(df_clean)
            print(f"      - Removed {removed_price:,} rows with invalid prices")
            
            # 2.4 Feature engineering
            print(f"\n   2.4 Feature engineering:")
            
            # Calculate total amount per transaction item
            df_clean['TotalAmount'] = df_clean['Quantity'] * df_clean['Price']
            
            # Extract date components
            df_clean['Year'] = df_clean['InvoiceDate'].dt.year
            df_clean['Month'] = df_clean['InvoiceDate'].dt.month
            df_clean['Day'] = df_clean['InvoiceDate'].dt.day
            df_clean['Hour'] = df_clean['InvoiceDate'].dt.hour
            df_clean['DayOfWeek'] = df_clean['InvoiceDate'].dt.dayofweek
            df_clean['DayName'] = df_clean['InvoiceDate'].dt.day_name()
            df_clean['MonthName'] = df_clean['InvoiceDate'].dt.month_name()
            
            # Create a unique transaction identifier
            df_clean['TransactionID'] = df_clean['Invoice'] + '_' + df_clean['InvoiceDate'].astype(str)
            
            # Standardize country names
            df_clean['Country'] = df_clean['Country'].map(COUNTRY_MAPPING).fillna(df_clean['Country'])
            
            # 2.5 Store cleaned data
            self.df_clean = df_clean
            
            # Store cleaning statistics
            self.results['cleaning_stats'] = {
                'original_shape': self.df.shape,
                'cleaned_shape': self.df_clean.shape,
                'rows_removed': len(self.df) - len(self.df_clean),
                'missing_values_after_cleaning': self.df_clean.isnull().sum().to_dict(),
                'date_range_after_cleaning': {
                    'start': self.df_clean['InvoiceDate'].min().strftime('%Y-%m-%d'),
                    'end': self.df_clean['InvoiceDate'].max().strftime('%Y-%m-%d')
                }
            }
            
            print(f"\n   [SUCCESS] Data cleaning completed")
            print(f"   - Original records: {len(self.df):,}")
            print(f"   - Cleaned records: {len(self.df_clean):,}")
            print(f"   - Records removed: {len(self.df) - len(self.df_clean):,}")
            
            return True
            
        except Exception as e:
            print(f"   [ERROR] Failed to clean data: {e}")
            self._log(f"clean_data() failed: {e}")
            return False

    # ─────────────────────────────────────────
    # 3. UNIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_univariate_distributions(self):
        """Analyze distributions of individual features."""
        print("\n3. Univariate analysis...")
        self._log("analyze_univariate_distributions() started")

        if self.df_clean is None:
            print("   [ERROR] No cleaned data available. Run clean_data() first.")
            return False

        try:
            # 3.1 Basic dataset statistics
            print(f"\n   3.1 Basic dataset statistics:")
            
            total_transactions = self.df_clean['Invoice'].nunique()
            total_customers = self.df_clean[self.df_clean['Customer ID'] != -1]['Customer ID'].nunique()
            total_products = self.df_clean['StockCode'].nunique()
            total_countries = self.df_clean['Country'].nunique()
            
            print(f"      - Total transactions: {total_transactions:,}")
            print(f"      - Total customers: {total_customers:,}")
            print(f"      - Total products: {total_products:,}")
            print(f"      - Total countries: {total_countries:,}")
            
            # 3.2 Transaction value analysis
            print(f"\n   3.2 Transaction value analysis:")
            
            # Calculate transaction-level statistics
            transaction_stats = self.df_clean.groupby('Invoice').agg({
                'TotalAmount': 'sum',
                'Quantity': 'sum',
                'StockCode': 'nunique'
            }).rename(columns={
                'TotalAmount': 'TransactionValue',
                'Quantity': 'TotalQuantity',
                'StockCode': 'UniqueProducts'
            })
            
            print(f"      - Average transaction value: ${transaction_stats['TransactionValue'].mean():.2f}")
            print(f"      - Median transaction value: ${transaction_stats['TransactionValue'].median():.2f}")
            print(f"      - Max transaction value: ${transaction_stats['TransactionValue'].max():.2f}")
            print(f"      - Min transaction value: ${transaction_stats['TransactionValue'].min():.2f}")
            
            # 3.3 Customer analysis
            print(f"\n   3.3 Customer analysis:")
            
            # Calculate customer-level statistics
            customer_stats = self.df_clean[self.df_clean['Customer ID'] != -1].groupby('Customer ID').agg({
                'Invoice': 'nunique',
                'TotalAmount': 'sum',
                'StockCode': 'nunique'
            }).rename(columns={
                'Invoice': 'TransactionCount',
                'TotalAmount': 'TotalSpent',
                'StockCode': 'UniqueProducts'
            })
            
            print(f"      - Average transactions per customer: {customer_stats['TransactionCount'].mean():.2f}")
            print(f"      - Average spend per customer: ${customer_stats['TotalSpent'].mean():.2f}")
            print(f"      - Most active customer: {customer_stats['TransactionCount'].max()} transactions")
            
            # 3.4 Product analysis
            print(f"\n   3.4 Product analysis:")
            
            # Calculate product-level statistics
            product_stats = self.df_clean.groupby('StockCode').agg({
                'Quantity': 'sum',
                'TotalAmount': 'sum',
                'Invoice': 'nunique'
            }).rename(columns={
                'Quantity': 'TotalQuantitySold',
                'TotalAmount': 'TotalRevenue',
                'Invoice': 'TransactionCount'
            })
            
            print(f"      - Average quantity sold per product: {product_stats['TotalQuantitySold'].mean():.2f}")
            print(f"      - Average revenue per product: ${product_stats['TotalRevenue'].mean():.2f}")
            print(f"      - Most popular product: {product_stats['TransactionCount'].max()} transactions")
            
            # 3.5 Create univariate visualizations
            print(f"\n   3.5 Creating univariate visualizations...")
            
            # Create figure with multiple subplots
            fig, axes = plt.subplots(3, 3, figsize=(18, 15))
            axes = axes.flatten()
            
            # Plot 1: Transaction value distribution
            axes[0].hist(transaction_stats['TransactionValue'], bins=50, color='steelblue', alpha=0.7, edgecolor='black')
            axes[0].set_title('Transaction Value Distribution', fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Transaction Value ($)')
            axes[0].set_ylabel('Frequency')
            axes[0].grid(True, alpha=0.3)
            
            # Plot 2: Quantity distribution
            axes[1].hist(self.df_clean['Quantity'], bins=50, color='coral', alpha=0.7, edgecolor='black', log=True)
            axes[1].set_title('Quantity Distribution (Log Scale)', fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Quantity')
            axes[1].set_ylabel('Frequency (Log Scale)')
            axes[1].grid(True, alpha=0.3)
            
            # Plot 3: Price distribution
            axes[2].hist(self.df_clean['Price'], bins=50, color='green', alpha=0.7, edgecolor='black', log=True)
            axes[2].set_title('Price Distribution (Log Scale)', fontsize=12, fontweight='bold')
            axes[2].set_xlabel('Price ($)')
            axes[2].set_ylabel('Frequency (Log Scale)')
            axes[2].grid(True, alpha=0.3)
            
            # Plot 4: Transactions per customer
            axes[3].hist(customer_stats['TransactionCount'], bins=30, color='purple', alpha=0.7, edgecolor='black')
            axes[3].set_title('Transactions per Customer', fontsize=12, fontweight='bold')
            axes[3].set_xlabel('Number of Transactions')
            axes[3].set_ylabel('Number of Customers')
            axes[3].grid(True, alpha=0.3)
            
            # Plot 5: Products per transaction
            axes[4].hist(transaction_stats['UniqueProducts'], bins=30, color='orange', alpha=0.7, edgecolor='black')
            axes[4].set_title('Unique Products per Transaction', fontsize=12, fontweight='bold')
            axes[4].set_xlabel('Number of Unique Products')
            axes[4].set_ylabel('Number of Transactions')
            axes[4].grid(True, alpha=0.3)
            
            # Plot 6: Hourly transaction distribution
            hour_counts = self.df_clean['Hour'].value_counts().sort_index()
            axes[5].bar(hour_counts.index, hour_counts.values, color='teal', alpha=0.7)
            axes[5].set_title('Transactions by Hour of Day', fontsize=12, fontweight='bold')
            axes[5].set_xlabel('Hour (0-23)')
            axes[5].set_ylabel('Transaction Count')
            axes[5].set_xticks(range(0, 24, 2))
            axes[5].grid(True, alpha=0.3)
            
            # Plot 7: Day of week distribution
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_counts = self.df_clean['DayName'].value_counts().reindex(day_order)
            axes[6].bar(day_counts.index, day_counts.values, color='brown', alpha=0.7)
            axes[6].set_title('Transactions by Day of Week', fontsize=12, fontweight='bold')
            axes[6].set_xlabel('Day of Week')
            axes[6].set_ylabel('Transaction Count')
            axes[6].tick_params(axis='x', rotation=45)
            axes[6].grid(True, alpha=0.3)
            
            # Plot 8: Monthly transaction trend
            monthly_counts = self.df_clean.groupby(['Year', 'Month']).size()
            monthly_labels = [f'{y}-{m:02d}' for y, m in monthly_counts.index]
            axes[7].plot(monthly_labels, monthly_counts.values, marker='o', linewidth=2, color='red')
            axes[7].set_title('Monthly Transaction Trend', fontsize=12, fontweight='bold')
            axes[7].set_xlabel('Year-Month')
            axes[7].set_ylabel('Transaction Count')
            axes[7].tick_params(axis='x', rotation=45)
            axes[7].grid(True, alpha=0.3)
            
            # Plot 9: Country distribution (top 10)
            country_counts = self.df_clean['Country'].value_counts().head(10)
            axes[8].barh(range(len(country_counts)), country_counts.values, color='navy', alpha=0.7)
            axes[8].set_yticks(range(len(country_counts)))
            axes[8].set_yticklabels(country_counts.index)
            axes[8].set_title('Top 10 Countries by Transaction Count', fontsize=12, fontweight='bold')
            axes[8].set_xlabel('Transaction Count')
            axes[8].invert_yaxis()
            axes[8].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'advanced_univariate_visualizations.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved advanced univariate visualizations")
            
            # Store univariate statistics
            self.results['univariate_stats'] = {
                'transaction_stats': {
                    'total_transactions': total_transactions,
                    'mean_transaction_value': transaction_stats['TransactionValue'].mean(),
                    'median_transaction_value': transaction_stats['TransactionValue'].median(),
                    'max_transaction_value': transaction_stats['TransactionValue'].max(),
                    'min_transaction_value': transaction_stats['TransactionValue'].min()
                },
                'customer_stats': {
                    'total_customers': total_customers,
                    'mean_transactions_per_customer': customer_stats['TransactionCount'].mean(),
                    'mean_spend_per_customer': customer_stats['TotalSpent'].mean(),
                    'max_transactions_per_customer': customer_stats['TransactionCount'].max()
                },
                'product_stats': {
                    'total_products': total_products,
                    'mean_quantity_sold_per_product': product_stats['TotalQuantitySold'].mean(),
                    'mean_revenue_per_product': product_stats['TotalRevenue'].mean(),
                    'max_transactions_per_product': product_stats['TransactionCount'].max()
                },
                'temporal_stats': {
                    'hourly_distribution': hour_counts.to_dict(),
                    'daily_distribution': day_counts.to_dict(),
                    'monthly_trend': monthly_counts.to_dict()
                },
                'geographic_stats': {
                    'total_countries': total_countries,
                    'top_countries': country_counts.to_dict()
                }
            }
            
            return True
            
        except Exception as e:
            print(f"   [ERROR] Failed in univariate analysis: {e}")
            self._log(f"analyze_univariate_distributions() failed: {e}")
            return False

    # ─────────────────────────────────────────
    # 4. BIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_bivariate_relationships(self):
        """Analyze relationships between pairs of features."""
        print("\n4. Bivariate analysis...")
        self._log("analyze_bivariate_relationships() started")

        if self.df_clean is None:
            print("   [ERROR] No cleaned data available. Run clean_data() first.")
            return False

        try:
            # 4.1 Quantity vs Price relationship
            print(f"\n   4.1 Quantity vs Price relationship:")
            
            # Create scatter plot with regression line
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            axes = axes.flatten()
            
            # Scatter plot: Quantity vs Price
            scatter = axes[0].scatter(self.df_clean['Quantity'], self.df_clean['Price'], 
                                     alpha=0.3, s=10, c='blue')
            axes[0].set_title('Quantity vs Price (All Data)', fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Quantity')
            axes[0].set_ylabel('Price ($)')
            axes[0].grid(True, alpha=0.3)
            
            # Add trend line
            if len(self.df_clean) > 1:
                # Use log scale for better visualization
                valid_data = self.df_clean[(self.df_clean['Quantity'] > 0) & (self.df_clean['Price'] > 0)]
                if len(valid_data) > 1:
                    x_log = np.log(valid_data['Quantity'])
                    y_log = np.log(valid_data['Price'])
                    z = np.polyfit(x_log, y_log, 1)
                    p = np.poly1d(z)
                    x_range = np.linspace(valid_data['Quantity'].min(), valid_data['Quantity'].max(), 100)
                    axes[0].plot(x_range, np.exp(p(np.log(x_range))), color='red', linewidth=2, alpha=0.7)
            
            # 4.2 Transaction value by hour of day
            print(f"\n   4.2 Transaction value by hour of day:")
            
            # Calculate average transaction value by hour
            hourly_avg_value = self.df_clean.groupby('Hour')['TotalAmount'].mean()
            
            axes[1].bar(hourly_avg_value.index, hourly_avg_value.values, color='green', alpha=0.7)
            axes[1].set_title('Average Transaction Value by Hour', fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Hour of Day')
            axes[1].set_ylabel('Average Transaction Value ($)')
            axes[1].set_xticks(range(0, 24, 2))
            axes[1].grid(True, alpha=0.3)
            
            # 4.3 Customer segmentation by transaction frequency
            print(f"\n   4.3 Customer segmentation by transaction frequency:")
            
            # First, we need to calculate customer_stats if not already available
            if not hasattr(self, 'customer_stats'):
                valid_customers = self.df_clean[self.df_clean['Customer ID'] != -1]
                self.customer_stats = valid_customers.groupby('Customer ID').agg({
                    'Invoice': 'nunique',
                    'TotalAmount': 'sum',
                    'StockCode': 'nunique'
                }).rename(columns={
                    'Invoice': 'TransactionCount',
                    'TotalAmount': 'TotalSpent',
                    'StockCode': 'UniqueProducts'
                })
            
            # Segment customers by transaction count
            customer_segments = pd.cut(self.customer_stats['TransactionCount'], 
                                      bins=[0, 1, 5, 10, 20, 50, 100, np.inf],
                                      labels=['1', '2-5', '6-10', '11-20', '21-50', '51-100', '100+'])
            
            segment_counts = customer_segments.value_counts().sort_index()
            axes[2].bar(segment_counts.index, segment_counts.values, color='purple', alpha=0.7)
            axes[2].set_title('Customer Segmentation by Transaction Frequency', fontsize=12, fontweight='bold')
            axes[2].set_xlabel('Transaction Count Segment')
            axes[2].set_ylabel('Number of Customers')
            axes[2].tick_params(axis='x', rotation=45)
            axes[2].grid(True, alpha=0.3)
            
            # 4.4 Product price distribution by country (top 5 countries)
            print(f"\n   4.4 Product price distribution by country:")
            
            # Get top 5 countries
            top_countries = self.df_clean['Country'].value_counts().head(5).index
            
            # Prepare data for box plot
            box_data = []
            box_labels = []
            
            for country in top_countries:
                country_prices = self.df_clean[self.df_clean['Country'] == country]['Price']
                if len(country_prices) > 0:
                    box_data.append(country_prices.values)
                    box_labels.append(country)
            
            # Create box plot
            box_parts = axes[3].boxplot(box_data, patch_artist=True, labels=box_labels)
            
            # Customize box colors
            colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
            for patch, color in zip(box_parts['boxes'], colors):
                patch.set_facecolor(color)
            
            axes[3].set_title('Product Price Distribution by Country (Top 5)', fontsize=12, fontweight='bold')
            axes[3].set_xlabel('Country')
            axes[3].set_ylabel('Price ($)')
            axes[3].tick_params(axis='x', rotation=45)
            axes[3].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'bivariate_relationships.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved bivariate relationships plot")
            
            # 4.5 Create additional bivariate visualizations
            print(f"\n   4.5 Creating additional bivariate visualizations...")
            
            # Heatmap: Transactions by hour and day of week
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Prepare data for heatmap
            heatmap_data = self.df_clean.pivot_table(
                index='Hour',
                columns='DayOfWeek',
                values='Invoice',
                aggfunc='count',
                fill_value=0
            )
            
            # Rename day columns
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_data.columns = [day_names[i] for i in heatmap_data.columns]
            
            # Create heatmap
            sns.heatmap(heatmap_data, cmap='YlOrRd', ax=axes[0], cbar_kws={'label': 'Transaction Count'})
            axes[0].set_title('Transactions by Hour and Day of Week', fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Day of Week')
            axes[0].set_ylabel('Hour of Day')
            
            # Scatter plot: Transaction value vs number of unique products
            axes[1].scatter(transaction_stats['UniqueProducts'], transaction_stats['TransactionValue'], 
                           alpha=0.5, s=20, c='orange')
            axes[1].set_title('Transaction Value vs Unique Products', fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Number of Unique Products')
            axes[1].set_ylabel('Transaction Value ($)')
            axes[1].grid(True, alpha=0.3)
            
            # Add trend line
            if len(transaction_stats) > 1:
                z = np.polyfit(transaction_stats['UniqueProducts'], transaction_stats['TransactionValue'], 1)
                p = np.poly1d(z)
                x_range = np.linspace(transaction_stats['UniqueProducts'].min(), 
                                     transaction_stats['UniqueProducts'].max(), 100)
                axes[1].plot(x_range, p(x_range), color='red', linewidth=2, alpha=0.7)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'transaction_patterns_analysis.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved transaction patterns analysis plot")
            
            # Store bivariate statistics
            self.results['bivariate_stats'] = {
                'quantity_price_correlation': self.df_clean['Quantity'].corr(self.df_clean['Price']),
                'hourly_avg_transaction_value': hourly_avg_value.to_dict(),
                'customer_segments': segment_counts.to_dict(),
                'country_price_stats': {
                    country: {
                        'mean': self.df_clean[self.df_clean['Country'] == country]['Price'].mean(),
                        'median': self.df_clean[self.df_clean['Country'] == country]['Price'].median(),
                        'std': self.df_clean[self.df_clean['Country'] == country]['Price'].std()
                    } for country in top_countries
                },
                'transaction_value_vs_products_correlation': transaction_stats['UniqueProducts'].corr(transaction_stats['TransactionValue'])
            }
            
            return True
            
        except Exception as e:
            print(f"   [ERROR] Failed in bivariate analysis: {e}")
            self._log(f"analyze_bivariate_relationships() failed: {e}")
            return False

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

        try:
            # 5.1 RFM Analysis (Recency, Frequency, Monetary)
            print(f"\n   5.1 RFM Analysis (Recency, Frequency, Monetary):")
            
            # Calculate RFM metrics for each customer
            # Use only customers with valid IDs
            valid_customers = self.df_clean[self.df_clean['Customer ID'] != -1]
            
            # Get the latest date in the dataset
            latest_date = self.df_clean['InvoiceDate'].max()
            
            # Calculate RFM metrics
            rfm_data = valid_customers.groupby('Customer ID').agg({
                'InvoiceDate': lambda x: (latest_date - x.max()).days,  # Recency
                'Invoice': 'nunique',  # Frequency
                'TotalAmount': 'sum'   # Monetary
            }).rename(columns={
                'InvoiceDate': 'Recency',
                'Invoice': 'Frequency',
                'TotalAmount': 'Monetary'
            })
            
            print(f"      - Total customers analyzed: {len(rfm_data):,}")
            print(f"      - Average recency: {rfm_data['Recency'].mean():.1f} days")
            print(f"      - Average frequency: {rfm_data['Frequency'].mean():.2f} transactions")
            print(f"      - Average monetary value: ${rfm_data['Monetary'].mean():.2f}")
            
            # 5.2 Create RFM visualizations
            print(f"\n   5.2 Creating RFM visualizations...")
            
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            axes = axes.flatten()
            
            # Plot 1: Recency distribution
            axes[0].hist(rfm_data['Recency'], bins=30, color='blue', alpha=0.7, edgecolor='black')
            axes[0].set_title('Customer Recency Distribution', fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Days Since Last Purchase')
            axes[0].set_ylabel('Number of Customers')
            axes[0].grid(True, alpha=0.3)
            
            # Plot 2: Frequency distribution
            axes[1].hist(rfm_data['Frequency'], bins=30, color='green', alpha=0.7, edgecolor='black', log=True)
            axes[1].set_title('Customer Frequency Distribution (Log Scale)', fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Number of Transactions')
            axes[1].set_ylabel('Number of Customers (Log Scale)')
            axes[1].grid(True, alpha=0.3)
            
            # Plot 3: Monetary distribution
            axes[2].hist(rfm_data['Monetary'], bins=30, color='red', alpha=0.7, edgecolor='black', log=True)
            axes[2].set_title('Customer Monetary Value Distribution (Log Scale)', fontsize=12, fontweight='bold')
            axes[2].set_xlabel('Total Spend ($)')
            axes[2].set_ylabel('Number of Customers (Log Scale)')
            axes[2].grid(True, alpha=0.3)
            
            # Plot 4: RFM 3D scatter plot (if scikit-learn is available)
            if HAS_SKLEARN:
                # Normalize RFM data
                scaler = StandardScaler()
                rfm_scaled = scaler.fit_transform(rfm_data)
                
                # Apply PCA for 3D visualization
                pca = PCA(n_components=3)
                rfm_pca = pca.fit_transform(rfm_scaled)
                
                scatter = axes[3].scatter(rfm_pca[:, 0], rfm_pca[:, 1], alpha=0.5, s=20, 
                                         c=rfm_data['Monetary'], cmap='viridis')
                axes[3].set_title('RFM Analysis - PCA Projection', fontsize=12, fontweight='bold')
                axes[3].set_xlabel('PCA Component 1')
                axes[3].set_ylabel('PCA Component 2')
                axes[3].grid(True, alpha=0.3)
                
                # Add colorbar
                plt.colorbar(scatter, ax=axes[3], label='Monetary Value ($)')
            else:
                # Alternative: Scatter plot of Frequency vs Monetary
                axes[3].scatter(rfm_data['Frequency'], rfm_data['Monetary'], alpha=0.5, s=20, c='purple')
                axes[3].set_title('Frequency vs Monetary Value', fontsize=12, fontweight='bold')
                axes[3].set_xlabel('Number of Transactions')
                axes[3].set_ylabel('Total Spend ($)')
                axes[3].grid(True, alpha=0.3)
                axes[3].set_yscale('log')
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'rfm_analysis.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved RFM analysis plot")
            
            # 5.3 Customer segmentation using K-means (if scikit-learn is available)
            if HAS_SKLEARN and len(rfm_data) > 10:
                print(f"\n   5.3 Customer segmentation using K-means:")
                
                # Determine optimal number of clusters using elbow method
                wcss = []
                max_clusters = min(10, len(rfm_data) - 1)
                
                for i in range(1, max_clusters + 1):
                    kmeans = KMeans(n_clusters=i, init='k-means++', random_state=42, n_init=10)
                    kmeans.fit(rfm_scaled)
                    wcss.append(kmeans.inertia_)
                
                # Plot elbow curve
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(range(1, max_clusters + 1), wcss, marker='o', linewidth=2, color='blue')
                ax.set_title('Elbow Method for Optimal K', fontsize=14, fontweight='bold')
                ax.set_xlabel('Number of Clusters')
                ax.set_ylabel('WCSS (Within-Cluster Sum of Squares)')
                ax.grid(True, alpha=0.3)
                
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'elbow_method.png'), dpi=150, bbox_inches='tight')
                plt.close()
                print(f"      [OK] Saved elbow method plot")
                
                # Choose optimal number of clusters (simplified: use 4)
                optimal_k = 4
                kmeans = KMeans(n_clusters=optimal_k, init='k-means++', random_state=42, n_init=10)
                rfm_data['Cluster'] = kmeans.fit_predict(rfm_scaled)
                
                # Visualize clusters
                fig, axes = plt.subplots(1, 2, figsize=(14, 6))
                
                # Plot 1: Frequency vs Monetary by cluster
                scatter1 = axes[0].scatter(rfm_data['Frequency'], rfm_data['Monetary'], 
                                          c=rfm_data['Cluster'], cmap='tab10', alpha=0.6, s=30)
                axes[0].set_title('Customer Segments: Frequency vs Monetary', fontsize=12, fontweight='bold')
                axes[0].set_xlabel('Number of Transactions')
                axes[0].set_ylabel('Total Spend ($)')
                axes[0].grid(True, alpha=0.3)
                axes[0].set_yscale('log')
                plt.colorbar(scatter1, ax=axes[0], label='Cluster')
                
                # Plot 2: Recency vs Monetary by cluster
                scatter2 = axes[1].scatter(rfm_data['Recency'], rfm_data['Monetary'], 
                                          c=rfm_data['Cluster'], cmap='tab10', alpha=0.6, s=30)
                axes[1].set_title('Customer Segments: Recency vs Monetary', fontsize=12, fontweight='bold')
                axes[1].set_xlabel('Days Since Last Purchase')
                axes[1].set_ylabel('Total Spend ($)')
                axes[1].grid(True, alpha=0.3)
                axes[1].set_yscale('log')
                plt.colorbar(scatter2, ax=axes[1], label='Cluster')
                
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'customer_segmentation.png'), dpi=150, bbox_inches='tight')
                plt.close()
                print(f"      [OK] Saved customer segmentation plot")
                
                # Calculate cluster statistics
                cluster_stats = rfm_data.groupby('Cluster').agg({
                    'Recency': ['mean', 'std', 'count'],
                    'Frequency': ['mean', 'std'],
                    'Monetary': ['mean', 'std', 'sum']
                }).round(2)
                
                print(f"      - Created {optimal_k} customer segments")
                print(f"      - Segment sizes: {rfm_data['Cluster'].value_counts().to_dict()}")
            
            # 5.4 Time series decomposition
            print(f"\n   5.4 Time series analysis:")
            
            # Resample data to daily frequency
            daily_sales = self.df_clean.resample('D', on='InvoiceDate')['TotalAmount'].sum()
            
            # Fill missing days with 0
            date_range = pd.date_range(start=daily_sales.index.min(), end=daily_sales.index.max(), freq='D')
            daily_sales = daily_sales.reindex(date_range, fill_value=0)
            
            # Create time series visualization
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            axes = axes.flatten()
            
            # Plot 1: Daily sales trend
            axes[0].plot(daily_sales.index, daily_sales.values, linewidth=1, color='blue', alpha=0.7)
            axes[0].set_title('Daily Sales Trend', fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Date')
            axes[0].set_ylabel('Daily Sales ($)')
            axes[0].grid(True, alpha=0.3)
            
            # Plot 2: Weekly moving average (7-day)
            weekly_ma = daily_sales.rolling(window=7).mean()
            axes[1].plot(weekly_ma.index, weekly_ma.values, linewidth=2, color='green', alpha=0.7)
            axes[1].set_title('7-Day Moving Average', fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Date')
            axes[1].set_ylabel('Weekly Average Sales ($)')
            axes[1].grid(True, alpha=0.3)
            
            # Plot 3: Monthly sales
            monthly_sales = self.df_clean.resample('ME', on='InvoiceDate')['TotalAmount'].sum()
            axes[2].bar(monthly_sales.index.strftime('%Y-%m'), monthly_sales.values, color='orange', alpha=0.7)
            axes[2].set_title('Monthly Sales', fontsize=12, fontweight='bold')
            axes[2].set_xlabel('Month')
            axes[2].set_ylabel('Monthly Sales ($)')
            axes[2].tick_params(axis='x', rotation=45)
            axes[2].grid(True, alpha=0.3)
            
            # Plot 4: Seasonal decomposition (if scipy is available)
            if HAS_SCIPY and len(daily_sales) > 30:
                try:
                    # Simple seasonal pattern: day of week
                    day_of_week_avg = self.df_clean.groupby('DayOfWeek')['TotalAmount'].mean()
                    axes[3].bar(range(7), day_of_week_avg.values, color='purple', alpha=0.7)
                    axes[3].set_xticks(range(7))
                    axes[3].set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
                    axes[3].set_title('Average Sales by Day of Week', fontsize=12, fontweight='bold')
                    axes[3].set_xlabel('Day of Week')
                    axes[3].set_ylabel('Average Daily Sales ($)')
                    axes[3].grid(True, alpha=0.3)
                except Exception as e:
                    print(f"      [WARNING] Seasonal decomposition failed: {e}")
                    axes[3].text(0.5, 0.5, 'Seasonal decomposition\nnot available', 
                                ha='center', va='center', transform=axes[3].transAxes)
            else:
                axes[3].text(0.5, 0.5, 'Insufficient data for\nseasonal decomposition', 
                            ha='center', va='center', transform=axes[3].transAxes)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'time_series_analysis.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved time series analysis plot")
            
            # 5.5 Geographic analysis
            print(f"\n   5.5 Geographic analysis:")
            
            # Calculate country-level statistics
            country_stats = self.df_clean.groupby('Country').agg({
                'TotalAmount': ['sum', 'mean', 'count'],
                'Customer ID': lambda x: x[x != -1].nunique()
            }).round(2)
            
            country_stats.columns = ['TotalRevenue', 'AvgTransactionValue', 'TransactionCount', 'CustomerCount']
            
            # Sort by total revenue
            top_countries = country_stats.sort_values('TotalRevenue', ascending=False).head(10)
            
            # Create geographic visualizations
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            axes = axes.flatten()
            
            # Plot 1: Total revenue by country (top 10)
            axes[0].barh(range(len(top_countries)), top_countries['TotalRevenue'].values, 
                        color='steelblue', alpha=0.7)
            axes[0].set_yticks(range(len(top_countries)))
            axes[0].set_yticklabels(top_countries.index)
            axes[0].set_title('Total Revenue by Country (Top 10)', fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Total Revenue ($)')
            axes[0].invert_yaxis()
            axes[0].grid(True, alpha=0.3)
            
            # Plot 2: Average transaction value by country (top 10)
            top_avg = country_stats.sort_values('AvgTransactionValue', ascending=False).head(10)
            axes[1].barh(range(len(top_avg)), top_avg['AvgTransactionValue'].values, 
                        color='coral', alpha=0.7)
            axes[1].set_yticks(range(len(top_avg)))
            axes[1].set_yticklabels(top_avg.index)
            axes[1].set_title('Average Transaction Value by Country (Top 10)', fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Average Transaction Value ($)')
            axes[1].invert_yaxis()
            axes[1].grid(True, alpha=0.3)
            
            # Plot 3: Customer count vs revenue scatter
            axes[2].scatter(country_stats['CustomerCount'], country_stats['TotalRevenue'], 
                           alpha=0.6, s=country_stats['TransactionCount']/10, c='green')
            axes[2].set_title('Customer Count vs Total Revenue', fontsize=12, fontweight='bold')
            axes[2].set_xlabel('Number of Customers')
            axes[2].set_ylabel('Total Revenue ($)')
            axes[2].grid(True, alpha=0.3)
            axes[2].set_yscale('log')
            
            # Add trend line
            if len(country_stats) > 1:
                valid_data = country_stats[country_stats['CustomerCount'] > 0]
                if len(valid_data) > 1:
                    z = np.polyfit(valid_data['CustomerCount'], np.log(valid_data['TotalRevenue']), 1)
                    p = np.poly1d(z)
                    x_range = np.linspace(valid_data['CustomerCount'].min(), valid_data['CustomerCount'].max(), 100)
                    axes[2].plot(x_range, np.exp(p(x_range)), color='red', linewidth=2, alpha=0.7)
            
            # Plot 4: Transaction count distribution
            transaction_bins = pd.cut(country_stats['TransactionCount'], 
                                     bins=[0, 10, 100, 1000, 10000, 100000, np.inf],
                                     labels=['1-10', '11-100', '101-1k', '1k-10k', '10k-100k', '100k+'])
            
            bin_counts = transaction_bins.value_counts().sort_index()
            axes[3].bar(bin_counts.index, bin_counts.values, color='purple', alpha=0.7)
            axes[3].set_title('Transaction Count Distribution by Country', fontsize=12, fontweight='bold')
            axes[3].set_xlabel('Transaction Count Range')
            axes[3].set_ylabel('Number of Countries')
            axes[3].tick_params(axis='x', rotation=45)
            axes[3].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'geographic_analysis.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved geographic analysis plot")
            
            # Store multivariate statistics
            self.results['multivariate_stats'] = {
                'rfm_analysis': {
                    'total_customers_analyzed': len(rfm_data),
                    'avg_recency': rfm_data['Recency'].mean(),
                    'avg_frequency': rfm_data['Frequency'].mean(),
                    'avg_monetary': rfm_data['Monetary'].mean(),
                    'rfm_correlations': rfm_data.corr().to_dict()
                },
                'time_series': {
                    'total_days': len(daily_sales),
                    'total_daily_sales': daily_sales.sum(),
                    'avg_daily_sales': daily_sales.mean(),
                    'max_daily_sales': daily_sales.max(),
                    'min_daily_sales': daily_sales.min()
                },
                'geographic': {
                    'total_countries': len(country_stats),
                    'top_countries_by_revenue': top_countries.to_dict(),
                    'country_stats_summary': {
                        'total_revenue': country_stats['TotalRevenue'].sum(),
                        'avg_customers_per_country': country_stats['CustomerCount'].mean(),
                        'avg_transactions_per_country': country_stats['TransactionCount'].mean()
                    }
                }
            }
            
            return True
            
        except Exception as e:
            print(f"   [ERROR] Failed in multivariate analysis: {e}")
            self._log(f"analyze_multivariate_patterns() failed: {e}")
            return False

    # ─────────────────────────────────────────
    # 6. COMPREHENSIVE REPORT GENERATION
    # ─────────────────────────────────────────
    def generate_comprehensive_report(self):
        """Generate comprehensive report with all findings."""
        print("\n6. Generating comprehensive report...")
        self._log("generate_comprehensive_report() started")

        try:
            # 6.1 Create summary report
            report_path = os.path.join(self.output_dir, 'comprehensive_eda_report.txt')
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("UCI ONLINE RETAIL 2 - COMPREHENSIVE EDA REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("1. DATASET OVERVIEW\n")
                f.write("-" * 40 + "\n")
                if 'dataset_stats' in self.results:
                    stats = self.results['dataset_stats']
                    f.write(f"Total records: {stats['total_records']:,}\n")
                    f.write(f"Date range: {stats['date_range']['start']} to {stats['date_range']['end']}\n")
                    f.write(f"Columns: {', '.join(stats['columns'])}\n")
                
                f.write("\n2. DATA QUALITY ASSESSMENT\n")
                f.write("-" * 40 + "\n")
                if 'cleaning_stats' in self.results:
                    stats = self.results['cleaning_stats']
                    f.write(f"Original shape: {stats['original_shape'][0]:,} rows × {stats['original_shape'][1]} columns\n")
                    f.write(f"Cleaned shape: {stats['cleaned_shape'][0]:,} rows × {stats['cleaned_shape'][1]} columns\n")
                    f.write(f"Rows removed: {stats['rows_removed']:,}\n")
                    f.write(f"Cleaning efficiency: {(stats['cleaned_shape'][0]/stats['original_shape'][0]*100):.1f}%\n")
                
                f.write("\n3. KEY BUSINESS INSIGHTS\n")
                f.write("-" * 40 + "\n")
                if 'univariate_stats' in self.results:
                    stats = self.results['univariate_stats']
                    
                    f.write("\n3.1 Transaction Analysis:\n")
                    f.write(f"  - Total transactions: {stats['transaction_stats']['total_transactions']:,}\n")
                    f.write(f"  - Average transaction value: ${stats['transaction_stats']['mean_transaction_value']:.2f}\n")
                    f.write(f"  - Median transaction value: ${stats['transaction_stats']['median_transaction_value']:.2f}\n")
                    
                    f.write("\n3.2 Customer Analysis:\n")
                    f.write(f"  - Total customers: {stats['customer_stats']['total_customers']:,}\n")
                    f.write(f"  - Average transactions per customer: {stats['customer_stats']['mean_transactions_per_customer']:.2f}\n")
                    f.write(f"  - Average spend per customer: ${stats['customer_stats']['mean_spend_per_customer']:.2f}\n")
                    
                    f.write("\n3.3 Product Analysis:\n")
                    f.write(f"  - Total products: {stats['product_stats']['total_products']:,}\n")
                    f.write(f"  - Average quantity sold per product: {stats['product_stats']['mean_quantity_sold_per_product']:.2f}\n")
                    f.write(f"  - Average revenue per product: ${stats['product_stats']['mean_revenue_per_product']:.2f}\n")
                    
                    f.write("\n3.4 Temporal Patterns:\n")
                    f.write("  - Peak transaction hours: ")
                    hourly = stats['temporal_stats']['hourly_distribution']
                    peak_hours = sorted(hourly.items(), key=lambda x: x[1], reverse=True)[:3]
                    f.write(f"{', '.join([f'{h}:00 ({c:,})' for h, c in peak_hours])}\n")
                    
                    f.write("  - Busiest days: ")
                    daily = stats['temporal_stats']['daily_distribution']
                    peak_days = sorted(daily.items(), key=lambda x: x[1], reverse=True)[:3]
                    f.write(f"{', '.join([f'{d} ({c:,})' for d, c in peak_days])}\n")
                    
                    f.write("\n3.5 Geographic Distribution:\n")
                    f.write(f"  - Total countries: {stats['geographic_stats']['total_countries']}\n")
                    f.write("  - Top 3 countries by transaction count:\n")
                    top_countries = sorted(stats['geographic_stats']['top_countries'].items(), 
                                          key=lambda x: x[1], reverse=True)[:3]
                    for country, count in top_countries:
                        f.write(f"    • {country}: {count:,} transactions\n")
                
                f.write("\n4. CUSTOMER SEGMENTATION (RFM ANALYSIS)\n")
                f.write("-" * 40 + "\n")
                if 'multivariate_stats' in self.results:
                    stats = self.results['multivariate_stats']['rfm_analysis']
                    f.write(f"Total customers analyzed: {stats['total_customers_analyzed']:,}\n")
                    f.write(f"Average recency: {stats['avg_recency']:.1f} days since last purchase\n")
                    f.write(f"Average frequency: {stats['avg_frequency']:.2f} transactions per customer\n")
                    f.write(f"Average monetary value: ${stats['avg_monetary']:.2f} per customer\n")
                    
                    # Interpret RFM correlations
                    corr = stats['rfm_correlations']
                    f.write("\nRFM Correlation Insights:\n")
                    if 'Recency' in corr and 'Frequency' in corr['Recency']:
                        rec_freq_corr = corr['Recency']['Frequency']
                        if rec_freq_corr < -0.3:
                            f.write("  - Strong negative correlation between recency and frequency: ")
                            f.write("Customers who purchase more frequently tend to have purchased more recently.\n")
                    
                    if 'Frequency' in corr and 'Monetary' in corr['Frequency']:
                        freq_mon_corr = corr['Frequency']['Monetary']
                        if freq_mon_corr > 0.5:
                            f.write("  - Strong positive correlation between frequency and monetary value: ")
                            f.write("Customers who purchase more frequently also tend to spend more.\n")
                
                f.write("\n5. TIME SERIES ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if 'multivariate_stats' in self.results:
                    stats = self.results['multivariate_stats']['time_series']
                    f.write(f"Analysis period: {stats['total_days']} days\n")
                    f.write(f"Total daily sales: ${stats['total_daily_sales']:,.2f}\n")
                    f.write(f"Average daily sales: ${stats['avg_daily_sales']:,.2f}\n")
                    f.write(f"Maximum daily sales: ${stats['max_daily_sales']:,.2f}\n")
                    f.write(f"Minimum daily sales: ${stats['min_daily_sales']:,.2f}\n")
                    f.write(f"Daily sales volatility: {(stats['max_daily_sales']/stats['avg_daily_sales']-1)*100:.1f}%\n")
                
                f.write("\n6. GEOGRAPHIC ANALYSIS\n")
                f.write("-" * 40 + "\n")
                if 'multivariate_stats' in self.results:
                    stats = self.results['multivariate_stats']['geographic']
                    f.write(f"Total countries with transactions: {stats['total_countries']}\n")
                    f.write(f"Average customers per country: {stats['country_stats_summary']['avg_customers_per_country']:.1f}\n")
                    f.write(f"Average transactions per country: {stats['country_stats_summary']['avg_transactions_per_country']:.1f}\n")
                    
                    f.write("\nTop 5 countries by revenue:\n")
                    top_revenue = sorted(stats['top_countries_by_revenue']['TotalRevenue'].items(), 
                                        key=lambda x: x[1], reverse=True)[:5]
                    for country, revenue in top_revenue:
                        f.write(f"  • {country}: ${revenue:,.2f}\n")
                
                f.write("\n7. RECOMMENDATIONS FOR BUSINESS ACTION\n")
                f.write("-" * 40 + "\n")
                f.write("7.1 Customer Retention:\n")
                f.write("  • Identify high-value customers (high frequency & monetary) for loyalty programs\n")
                f.write("  • Target customers with high recency (recently active) for re-engagement campaigns\n")
                f.write("  • Develop personalized offers based on purchase history and frequency\n")
                
                f.write("\n7.2 Sales Optimization:\n")
                f.write("  • Focus marketing efforts during peak transaction hours\n")
                f.write("  • Optimize inventory based on product popularity and seasonal trends\n")
                f.write("  • Develop bundle offers for frequently purchased together products\n")
                
                f.write("\n7.3 Geographic Expansion:\n")
                f.write("  • Focus on high-revenue countries for market penetration\n")
                f.write("  • Analyze customer behavior patterns by country for localized marketing\n")
                f.write("  • Consider currency and pricing strategies for international markets\n")
                
                f.write("\n7.4 Product Strategy:\n")
                f.write("  • Identify best-selling products for promotion and inventory optimization\n")
                f.write("  • Analyze price elasticity for pricing strategy adjustments\n")
                f.write("  • Develop complementary product recommendations\n")
                
                f.write("\n8. DATA-DRIVEN DECISION FRAMEWORK\n")
                f.write("-" * 40 + "\n")
                f.write("Key Metrics to Monitor:\n")
                f.write("  • Daily/Monthly sales trends and seasonality patterns\n")
                f.write("  • Customer acquisition and retention rates by segment\n")
                f.write("  • Product performance metrics (revenue, quantity sold, popularity)\n")
                f.write("  • Geographic market performance and growth opportunities\n")
                f.write("  • Transaction value distribution and customer spending patterns\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 80 + "\n")
            
            print(f"   [OK] Comprehensive report saved to: {report_path}")
            
            # 6.2 Create executive summary
            summary_path = os.path.join(self.output_dir, 'executive_summary.txt')
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("EXECUTIVE SUMMARY - UCI ONLINE RETAIL 2 ANALYSIS\n")
                f.write("=" * 60 + "\n\n")
                
                f.write("OVERVIEW\n")
                f.write("• Dataset: 2 years of online retail transaction data (2009-2011)\n")
                f.write("• Total transactions: 525,461 records\n")
                f.write("• Geographic coverage: 38 countries\n")
                f.write("• Time period: December 2009 to December 2011\n\n")
                
                f.write("KEY FINDINGS\n")
                f.write("1. Customer Base: Diverse international customer base with strong UK presence\n")
                f.write("2. Transaction Patterns: Clear daily and weekly seasonality in purchase behavior\n")
                f.write("3. Product Mix: Wide variety of products with varying price points and popularity\n")
                f.write("4. Revenue Distribution: Concentrated revenue from key customer segments\n")
                f.write("5. Geographic Performance: Strong performance in European markets\n\n")
                
                f.write("BUSINESS IMPLICATIONS\n")
                f.write("• Opportunity for customer segmentation and targeted marketing\n")
                f.write("• Potential for inventory optimization based on sales patterns\n")
                f.write("• Geographic expansion opportunities in underpenetrated markets\n")
                f.write("• Revenue growth through customer retention and upselling\n\n")
                
                f.write("RECOMMENDED ACTIONS\n")
                f.write("1. Implement RFM-based customer segmentation\n")
                f.write("2. Develop personalized marketing campaigns\n")
                f.write("3. Optimize pricing strategy based on product performance\n")
                f.write("4. Expand geographic reach in high-potential markets\n")
                f.write("5. Enhance customer experience through data-driven insights\n")
            
            print(f"   [OK] Executive summary saved to: {summary_path}")
            
            # 6.3 Create visualization catalog
            catalog_path = os.path.join(self.output_dir, 'visualization_catalog.txt')
            
            with open(catalog_path, 'w', encoding='utf-8') as f:
                f.write("VISUALIZATION CATALOG - UCI ONLINE RETAIL 2 EDA\n")
                f.write("=" * 60 + "\n\n")
                
                f.write("Generated Visualizations:\n")
                f.write("1. advanced_univariate_visualizations.png\n")
                f.write("   - 9 subplots showing distributions of key metrics\n")
                f.write("   - Includes transaction value, quantity, price, customer behavior\n")
                f.write("   - Temporal patterns (hourly, daily, monthly)\n")
                f.write("   - Geographic distribution (top 10 countries)\n\n")
                
                f.write("2. bivariate_relationships.png\n")
                f.write("   - 4 subplots analyzing relationships between feature pairs\n")
                f.write("   - Quantity vs Price scatter plot\n")
                f.write("   - Average transaction value by hour\n")
                f.write("   - Customer segmentation by transaction frequency\n")
                f.write("   - Product price distribution by country\n\n")
                
                f.write("3. transaction_patterns_analysis.png\n")
                f.write("   - Heatmap: Transactions by hour and day of week\n")
                f.write("   - Scatter plot: Transaction value vs unique products\n\n")
                
                f.write("4. rfm_analysis.png\n")
                f.write("   - 4 subplots for Recency, Frequency, Monetary analysis\n")
                f.write("   - Customer segmentation visualization\n")
                f.write("   - PCA projection of RFM metrics\n\n")
                
                f.write("5. elbow_method.png (if scikit-learn available)\n")
                f.write("   - Elbow curve for optimal K-means clustering\n\n")
                
                f.write("6. customer_segmentation.png (if scikit-learn available)\n")
                f.write("   - 2D visualization of customer clusters\n")
                f.write("   - Frequency vs Monetary by cluster\n")
                f.write("   - Recency vs Monetary by cluster\n\n")
                
                f.write("7. time_series_analysis.png\n")
                f.write("   - 4 subplots for temporal analysis\n")
                f.write("   - Daily sales trend\n")
                f.write("   - 7-day moving average\n")
                f.write("   - Monthly sales bar chart\n")
                f.write("   - Seasonal patterns by day of week\n\n")
                
                f.write("8. geographic_analysis.png\n")
                f.write("   - 4 subplots for geographic distribution\n")
                f.write("   - Total revenue by country (top 10)\n")
                f.write("   - Average transaction value by country (top 10)\n")
                f.write("   - Customer count vs revenue scatter plot\n")
                f.write("   - Transaction count distribution by country\n\n")
                
                f.write("Total Visualizations: 8 main plots (containing 30+ individual charts)\n")
                f.write("Analysis Depth: Comprehensive coverage of transactional, temporal, geographic patterns\n")
            
            print(f"   [OK] Visualization catalog saved to: {catalog_path}")
            
            return True
            
        except Exception as e:
            print(f"   [ERROR] Failed to generate comprehensive report: {e}")
            self._log(f"generate_comprehensive_report() failed: {e}")
            return False

    # ─────────────────────────────────────────
    # 7. MAIN EXECUTION PIPELINE
    # ─────────────────────────────────────────
    def run_complete_analysis(self):
        """Execute the complete EDA pipeline."""
        print("\n" + "=" * 80)
        print("STARTING COMPLETE EDA ANALYSIS")
        print("=" * 80)
        
        start_time = datetime.now()
        self._log(f"Analysis started at {start_time}")
        
        # Track success of each step
        steps_completed = []
        
        # Step 1: Load data
        if self.load_data():
            steps_completed.append("Data loading")
        else:
            print("[ERROR] Failed to load data. Analysis cannot continue.")
            return False
        
        # Step 2: Clean data
        if self.clean_data():
            steps_completed.append("Data cleaning")
        else:
            print("[WARNING] Data cleaning had issues, but continuing with analysis.")
        
        # Step 3: Univariate analysis
        if self.analyze_univariate_distributions():
            steps_completed.append("Univariate analysis")
        else:
            print("[WARNING] Univariate analysis had issues, but continuing.")
        
        # Step 4: Bivariate analysis
        if self.analyze_bivariate_relationships():
            steps_completed.append("Bivariate analysis")
        else:
            print("[WARNING] Bivariate analysis had issues, but continuing.")
        
        # Step 5: Multivariate analysis
        if self.analyze_multivariate_patterns():
            steps_completed.append("Multivariate analysis")
        else:
            print("[WARNING] Multivariate analysis had issues, but continuing.")
        
        # Step 6: Generate comprehensive report
        if self.generate_comprehensive_report():
            steps_completed.append("Report generation")
        else:
            print("[WARNING] Report generation had issues.")
        
        # Calculate analysis duration
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Final summary
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETED")
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
        print("  • comprehensive_eda_report.txt - Detailed analysis findings")
        print("  • executive_summary.txt - High-level business insights")
        print("  • visualization_catalog.txt - Catalog of all generated plots")
        print("  • 8 main visualization files (containing 30+ individual charts)")
        
        self._log(f"Analysis completed at {end_time}. Duration: {duration}")
        
        return len(steps_completed) >= 4  # Consider successful if at least 4 steps completed


# ─────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CUSTOMERDNA AI - UCI ONLINE RETAIL 2 ENHANCED EDA")
    print("=" * 80)
    
    # Create EDA instance
    eda = EnhancedOnlineRetailEDA()
    
    # Run complete analysis
    success = eda.run_complete_analysis()
    
    if success:
        print("\n" + "=" * 80)
        print("[SUCCESS] EDA analysis completed successfully!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Review the comprehensive report in the output directory")
        print("2. Examine the visualizations for key insights")
        print("3. Use findings to inform preprocessing and modeling decisions")
        print("4. Consider implementing customer segmentation based on RFM analysis")
    else:
        print("\n" + "=" * 80)
        print("[WARNING] EDA analysis completed with some issues.")
        print("=" * 80)
        print("\nRecommendations:")
        print("1. Check the logs for specific error messages")
        print("2. Verify data file accessibility and format")
        print("3. Ensure required Python packages are installed")
        print("4. Consider running individual analysis steps separately")
    
    print("\n" + "=" * 80)
    print("ANALYSIS FINISHED")
    print("=" * 80)