#!/usr/bin/env python3
"""
Enhanced EDA for Retailrocket Recommender System Dataset
Comprehensive analysis with maximum possible visualizations and insights.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Optional imports for advanced visualizations
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    print("[WARNING] plotly not available. Interactive visualizations will be skipped.")

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("[WARNING] networkx not available. Network visualizations will be skipped.")

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[WARNING] scipy not available. Statistical tests will be skipped.")

# ─────────────────────────────────────────────
# PATHS — adjust only these lines
# ─────────────────────────────────────────────
BASE_DATA_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\base_dataset\Retailrocket_recommender_system_dataset"
EVENTS_PATH = os.path.join(BASE_DATA_DIR, 'events.csv')
CATEGORY_TREE_PATH = os.path.join(BASE_DATA_DIR, 'category_tree.csv')
ITEM_PROPS_PART1_PATH = os.path.join(BASE_DATA_DIR, 'item_properties_part1.csv')
ITEM_PROPS_PART2_PATH = os.path.join(BASE_DATA_DIR, 'item_properties_part2.csv')

OUTPUT_DIR = r"d:\github\Master_PFE_Project\CustomerDNA AI\src\EDA\Retailrocket_recommender_system_dataset_EDA\output"

# ─────────────────────────────────────────────
# CONSTANTS — analysis parameters
# ─────────────────────────────────────────────
SAMPLE_SIZE = 100000  # For memory management with large datasets
DATE_RANGE_START = '2015-06-01'
DATE_RANGE_END = '2015-09-30'

# Event type mapping
EVENT_TYPES = {
    'view': 'View',
    'addtocart': 'Add to Cart',
    'transaction': 'Transaction'
}

# Color palettes
EVENT_COLORS = {
    'view': '#3498db',
    'addtocart': '#e74c3c',
    'transaction': '#2ecc71'
}

class EnhancedRetailrocketEDA:
    """
    Enhanced EDA class for Retailrocket Recommender System Dataset.
    Comprehensive analysis of e-commerce user interactions, item properties, and category hierarchy.
    """

    def __init__(self):
        self.events_path = EVENTS_PATH
        self.category_tree_path = CATEGORY_TREE_PATH
        self.item_props_part1_path = ITEM_PROPS_PART1_PATH
        self.item_props_part2_path = ITEM_PROPS_PART2_PATH
        self.output_dir = OUTPUT_DIR

        os.makedirs(self.output_dir, exist_ok=True)

        self.df_events = None
        self.df_category_tree = None
        self.df_item_props = None
        self.df_merged = None
        self.results = {}

        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        self._log_dir = os.path.join(os.path.dirname(self.output_dir), 'logs')
        os.makedirs(self._log_dir, exist_ok=True)
        self._log_file = os.path.join(self._log_dir, 'eda_analysis.log')

    def _log(self, message):
        """Log messages to file and console."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"{timestamp} - {message}"
        
        with open(self._log_file, 'a') as f:
            f.write(log_message + '\n')
        
        print(f"LOG [{timestamp}]: {message}")

    # ─────────────────────────────────────────
    # 1. DATA LOADING AND BASIC ASSESSMENT
    # ─────────────────────────────────────────
    def load_data(self):
        """Load all dataset files with memory optimization."""
        print("\n1. Loading data...")
        self._log("load_data() started")

        try:
            # Load events data
            print(f"   Loading events data from: {self.events_path}")
            self.df_events = pd.read_csv(self.events_path)
            print(f"   [OK] Loaded {len(self.df_events):,} events")

            # Load category tree
            print(f"   Loading category tree from: {self.category_tree_path}")
            self.df_category_tree = pd.read_csv(self.category_tree_path)
            print(f"   [OK] Loaded {len(self.df_category_tree):,} category relationships")

            # Load item properties (combine both parts)
            print(f"   Loading item properties...")
            df_props1 = pd.read_csv(self.item_props_part1_path)
            df_props2 = pd.read_csv(self.item_props_part2_path)
            self.df_item_props = pd.concat([df_props1, df_props2], ignore_index=True)
            print(f"   [OK] Loaded {len(self.df_item_props):,} item property records")

            # Basic dataset overview
            print(f"\n   Dataset Overview:")
            print(f"   - Events: {len(self.df_events):,} rows, {self.df_events.shape[1]} columns")
            print(f"   - Category Tree: {len(self.df_category_tree):,} rows, {self.df_category_tree.shape[1]} columns")
            print(f"   - Item Properties: {len(self.df_item_props):,} rows, {self.df_item_props.shape[1]} columns")

            # Events data types
            print(f"\n   Events Data Types:")
            for col, dtype in self.df_events.dtypes.items():
                unique_count = self.df_events[col].nunique()
                print(f"   - {col}: {dtype}, Unique values: {unique_count:,}")

            # Save basic statistics
            self.results['dataset_stats'] = {
                'events_rows': len(self.df_events),
                'events_columns': self.df_events.shape[1],
                'category_tree_rows': len(self.df_category_tree),
                'item_props_rows': len(self.df_item_props),
                'unique_visitors': self.df_events['visitorid'].nunique(),
                'unique_items': self.df_events['itemid'].nunique(),
                'event_types': self.df_events['event'].value_counts().to_dict()
            }

            self._log("load_data() completed")
            return True

        except Exception as e:
            print(f"   [ERROR] Failed to load data: {e}")
            self._log(f"load_data() failed: {e}")
            return False

    # ─────────────────────────────────────────
    # 2. DATA CLEANING AND PREPROCESSING
    # ─────────────────────────────────────────
    def clean_data(self):
        """Clean and preprocess the dataset."""
        print("\n2. Cleaning data...")
        self._log("clean_data() started")

        if self.df_events is None:
            print("   [ERROR] No data loaded. Run load_data() first.")
            return False

        original_shape = self.df_events.shape

        # 2.1 Handle missing values
        print(f"\n   2.1 Handling missing values:")
        missing_counts = self.df_events.isnull().sum()
        for col, count in missing_counts.items():
            if count > 0:
                print(f"      - {col}: {count:,} missing values ({count/len(self.df_events)*100:.1f}%)")

        # Handle transactionid missing values (expected for non-transaction events)
        non_transaction_events = self.df_events[self.df_events['event'] != 'transaction']
        missing_transaction_ids = non_transaction_events['transactionid'].isnull().sum()
        print(f"      - transactionid: {missing_transaction_ids:,} missing (expected for non-transaction events)")

        # 2.2 Convert timestamp to datetime
        print(f"\n   2.2 Converting timestamps:")
        try:
            # Convert milliseconds to datetime
            self.df_events['datetime'] = pd.to_datetime(self.df_events['timestamp'], unit='ms')
            print(f"      [OK] Converted timestamp to datetime")
            
            # Extract date components
            self.df_events['date'] = self.df_events['datetime'].dt.date
            self.df_events['hour'] = self.df_events['datetime'].dt.hour
            self.df_events['day_of_week'] = self.df_events['datetime'].dt.dayofweek
            self.df_events['month'] = self.df_events['datetime'].dt.month
            print(f"      [OK] Extracted date components")
        except Exception as e:
            print(f"      [ERROR] Failed to convert timestamps: {e}")

        # 2.3 Check for duplicates
        print(f"\n   2.3 Checking for duplicates:")
        duplicate_count = self.df_events.duplicated().sum()
        print(f"      - Total duplicates: {duplicate_count:,}")

        if duplicate_count > 0:
            self.df_events = self.df_events.drop_duplicates()
            print(f"      [OK] Removed duplicates")

        # 2.4 Data type optimization
        print(f"\n   2.4 Optimizing data types:")
        # Convert visitorid and itemid to categorical for memory efficiency
        self.df_events['visitorid'] = self.df_events['visitorid'].astype('category')
        self.df_events['itemid'] = self.df_events['itemid'].astype('category')
        print(f"      [OK] Converted IDs to categorical types")

        # 2.5 Event type analysis
        print(f"\n   2.5 Event type distribution:")
        event_counts = self.df_events['event'].value_counts()
        for event_type, count in event_counts.items():
            percentage = count / len(self.df_events) * 100
            print(f"      - {EVENT_TYPES.get(event_type, event_type)}: {count:,} ({percentage:.1f}%)")

        # 2.6 Summary
        print(f"\n   Cleaning completed:")
        print(f"   - Original shape: {original_shape}")
        print(f"   - Cleaned shape: {self.df_events.shape}")
        print(f"   - Rows removed: {original_shape[0] - self.df_events.shape[0]:,}")

        self.results['cleaning_stats'] = {
            'original_shape': original_shape,
            'cleaned_shape': self.df_events.shape,
            'rows_removed': original_shape[0] - self.df_events.shape[0],
            'event_distribution': event_counts.to_dict()
        }

        self._log("clean_data() completed")
        return True

    # ─────────────────────────────────────────
    # 3. UNIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_univariate_distributions(self):
        """Analyze distributions of individual features."""
        print("\n3. Univariate analysis...")
        self._log("analyze_univariate_distributions() started")

        if self.df_events is None:
            print("   [ERROR] No data available. Run load_data() first.")
            return False

        # 3.1 Event type distribution
        print(f"\n   3.1 Event type distribution:")
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Bar chart
        event_counts = self.df_events['event'].value_counts()
        event_labels = [EVENT_TYPES.get(e, e) for e in event_counts.index]
        
        bars = axes[0].bar(event_labels, event_counts.values, color=[EVENT_COLORS.get(e, '#95a5a6') for e in event_counts.index])
        axes[0].set_title('Event Type Distribution', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Event Type')
        axes[0].set_ylabel('Count')
        axes[0].tick_params(axis='x', rotation=45)
        
        # Add count labels on bars
        for bar, count in zip(bars, event_counts.values):
            height = bar.get_height()
            axes[0].text(bar.get_x() + bar.get_width()/2., height + 100,
                       f'{count:,}', ha='center', va='bottom', fontsize=10)

        # Pie chart
        axes[1].pie(event_counts.values, labels=event_labels, 
                   colors=[EVENT_COLORS.get(e, '#95a5a6') for e in event_counts.index],
                   autopct='%1.1f%%', startangle=90)
        axes[1].set_title('Event Type Percentage', fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'event_type_distribution.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved event type distribution plot")

        # 3.2 Temporal distributions
        print(f"\n   3.2 Temporal distributions:")
        
        # Hourly distribution
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()

        # Hour distribution
        hour_counts = self.df_events['hour'].value_counts().sort_index()
        axes[0].bar(hour_counts.index, hour_counts.values, color='steelblue', alpha=0.7)
        axes[0].set_title('Event Distribution by Hour of Day', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Hour (0-23)')
        axes[0].set_ylabel('Event Count')
        axes[0].set_xticks(range(0, 24, 2))
        axes[0].grid(True, alpha=0.3)

        # Day of week distribution
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = self.df_events['day_of_week'].value_counts().sort_index()
        axes[1].bar(day_names, day_counts.values, color='coral', alpha=0.7)
        axes[1].set_title('Event Distribution by Day of Week', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Day of Week')
        axes[1].set_ylabel('Event Count')
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].grid(True, alpha=0.3)

        # Daily trend (if data spans multiple days)
        if self.df_events['date'].nunique() > 1:
            daily_counts = self.df_events.groupby('date').size()
            axes[2].plot(daily_counts.index, daily_counts.values, marker='o', linewidth=2, color='green')
            axes[2].set_title('Daily Event Trend', fontsize=12, fontweight='bold')
            axes[2].set_xlabel('Date')
            axes[2].set_ylabel('Event Count')
            axes[2].tick_params(axis='x', rotation=45)
            axes[2].grid(True, alpha=0.3)

        # Event type by hour heatmap
        event_hour_matrix = pd.crosstab(self.df_events['hour'], self.df_events['event'])
        sns.heatmap(event_hour_matrix, annot=True, fmt='.0f', cmap='YlOrRd', 
                   ax=axes[3], cbar_kws={'label': 'Event Count'})
        axes[3].set_title('Event Type by Hour Heatmap', fontsize=12, fontweight='bold')
        axes[3].set_xlabel('Event Type')
        axes[3].set_ylabel('Hour')

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'temporal_distributions.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved temporal distributions plot")

        # 3.3 Visitor and item statistics
        print(f"\n   3.3 Visitor and item statistics:")
        
        # Visitor engagement
        visitor_stats = self.df_events.groupby('visitorid').agg({
            'event': 'count',
            'itemid': 'nunique'
        }).rename(columns={'event': 'total_events', 'itemid': 'unique_items'})

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()

        # Visitor event count distribution
        axes[0].hist(visitor_stats['total_events'], bins=50, color='purple', alpha=0.7, edgecolor='black')
        axes[0].set_title('Distribution of Events per Visitor', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Number of Events')
        axes[0].set_ylabel('Number of Visitors')
        axes[0].grid(True, alpha=0.3)

        # Visitor unique items distribution
        axes[1].hist(visitor_stats['unique_items'], bins=30, color='orange', alpha=0.7, edgecolor='black')
        axes[1].set_title('Distribution of Unique Items per Visitor', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Number of Unique Items')
        axes[1].set_ylabel('Number of Visitors')
        axes[1].grid(True, alpha=0.3)

        # Item popularity
        item_counts = self.df_events['itemid'].value_counts()
        
        # Top 20 most popular items
        top_items = item_counts.head(20)
        axes[2].barh(range(len(top_items)), top_items.values, color='teal', alpha=0.7)
        axes[2].set_yticks(range(len(top_items)))
        axes[2].set_yticklabels([str(item) for item in top_items.index])
        axes[2].set_title('Top 20 Most Popular Items', fontsize=12, fontweight='bold')
        axes[2].set_xlabel('Event Count')
        axes[2].invert_yaxis()

        # Item popularity distribution (log scale)
        axes[3].hist(item_counts.values, bins=50, color='brown', alpha=0.7, edgecolor='black', log=True)
        axes[3].set_title('Item Popularity Distribution (Log Scale)', fontsize=12, fontweight='bold')
        axes[3].set_xlabel('Event Count per Item')
        axes[3].set_ylabel('Number of Items (Log Scale)')
        axes[3].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'visitor_item_statistics.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved visitor and item statistics plot")

        # 3.4 Advanced univariate visualizations
        print(f"\n   3.4 Advanced univariate visualizations:")
        
        # Violin plots for event counts by hour
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Prepare data for violin plots
        event_hour_data = []
        for event_type in self.df_events['event'].unique():
            event_data = self.df_events[self.df_events['event'] == event_type]['hour'].values
            event_hour_data.append(event_data)
        
        # Create violin plot
        violin_parts = axes[0].violinplot(event_hour_data, showmeans=True, showmedians=True)
        axes[0].set_title('Hour Distribution by Event Type', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Event Type')
        axes[0].set_ylabel('Hour of Day')
        axes[0].set_xticks(range(1, len(event_hour_data) + 1))
        axes[0].set_xticklabels([EVENT_TYPES.get(e, e) for e in self.df_events['event'].unique()])
        
        # Color the violin plots
        for i, pc in enumerate(violin_parts['bodies']):
            pc.set_facecolor(list(EVENT_COLORS.values())[i % len(EVENT_COLORS)])
            pc.set_alpha(0.7)

        # CDF of events per visitor
        sorted_event_counts = np.sort(visitor_stats['total_events'].values)
        cdf = np.arange(1, len(sorted_event_counts) + 1) / len(sorted_event_counts)
        
        axes[1].plot(sorted_event_counts, cdf, linewidth=2, color='darkblue')
        axes[1].set_title('CDF of Events per Visitor', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Number of Events')
        axes[1].set_ylabel('Cumulative Probability')
        axes[1].grid(True, alpha=0.3)
        
        # Add percentile markers
        percentiles = [50, 75, 90, 95, 99]
        for p in percentiles:
            value = np.percentile(sorted_event_counts, p)
            axes[1].axvline(x=value, color='red', linestyle='--', alpha=0.5)
            axes[1].text(value, 0.1, f'{p}%', rotation=90, va='bottom', ha='right')

        # Box plot of events by day of week
        event_data_by_day = []
        for day in range(7):
            day_data = self.df_events[self.df_events['day_of_week'] == day]['hour'].values
            event_data_by_day.append(day_data)
        
        box_parts = axes[2].boxplot(event_data_by_day, patch_artist=True)
        axes[2].set_title('Hour Distribution by Day of Week', fontsize=12, fontweight='bold')
        axes[2].set_xlabel('Day of Week')
        axes[2].set_ylabel('Hour of Day')
        axes[2].set_xticklabels(day_names)
        
        # Color the box plots
        colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink', 'lightgray', 'lightcyan']
        for patch, color in zip(box_parts['boxes'], colors):
            patch.set_facecolor(color)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'advanced_univariate_visualizations.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved advanced univariate visualizations")

        # Save univariate statistics
        self.results['univariate_stats'] = {
            'visitor_stats': {
                'total_visitors': visitor_stats.shape[0],
                'mean_events_per_visitor': visitor_stats['total_events'].mean(),
                'median_events_per_visitor': visitor_stats['total_events'].median(),
                'std_events_per_visitor': visitor_stats['total_events'].std(),
                'max_events_per_visitor': visitor_stats['total_events'].max(),
                'mean_unique_items_per_visitor': visitor_stats['unique_items'].mean()
            },
            'item_stats': {
                'total_items': item_counts.shape[0],
                'mean_events_per_item': item_counts.mean(),
                'median_events_per_item': item_counts.median(),
                'std_events_per_item': item_counts.std(),
                'max_events_per_item': item_counts.max()
            },
            'temporal_stats': {
                'date_range': {
                    'start': self.df_events['date'].min().strftime('%Y-%m-%d'),
                    'end': self.df_events['date'].max().strftime('%Y-%m-%d'),
                    'days': (self.df_events['date'].max() - self.df_events['date'].min()).days
                },
                'hourly_distribution': hour_counts.to_dict(),
                'daily_distribution': day_counts.to_dict() if 'day_counts' in locals() else {}
            }
        }

        self._log("analyze_univariate_distributions() completed")
        return True

    # ─────────────────────────────────────────
    # 4. BIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_bivariate_relationships(self):
        """Analyze relationships between pairs of features."""
        print("\n4. Bivariate analysis...")
        self._log("analyze_bivariate_relationships() started")

        if self.df_events is None:
            print("   [ERROR] No data available. Run load_data() first.")
            return False

        # 4.1 Event type by hour analysis
        print(f"\n   4.1 Event type by hour analysis:")
        
        # Create pivot table for heatmap
        event_hour_pivot = pd.crosstab(self.df_events['hour'], self.df_events['event'])
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # Heatmap
        sns.heatmap(event_hour_pivot, annot=True, fmt='d', cmap='YlOrRd', 
                   ax=axes[0], cbar_kws={'label': 'Event Count'})
        axes[0].set_title('Event Count by Hour and Type', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Event Type')
        axes[0].set_ylabel('Hour of Day')
        
        # Stacked bar chart
        event_hour_pivot.plot(kind='bar', stacked=True, ax=axes[1], 
                             color=[EVENT_COLORS.get(e, '#95a5a6') for e in event_hour_pivot.columns])
        axes[1].set_title('Event Distribution by Hour (Stacked)', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Hour of Day')
        axes[1].set_ylabel('Event Count')
        axes[1].legend(title='Event Type')
        axes[1].tick_params(axis='x', rotation=0)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'event_hour_analysis.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved event hour analysis plot")

        # 4.2 Visitor engagement patterns
        print(f"\n   4.2 Visitor engagement patterns:")
        
        # Calculate visitor metrics
        visitor_metrics = self.df_events.groupby('visitorid').agg({
            'event': lambda x: (x == 'view').sum(),
            'itemid': 'nunique'
        }).rename(columns={'event': 'view_count', 'itemid': 'unique_items'})
        
        # Add addtocart and transaction counts
        visitor_metrics['addtocart_count'] = self.df_events[self.df_events['event'] == 'addtocart'].groupby('visitorid').size()
        visitor_metrics['transaction_count'] = self.df_events[self.df_events['event'] == 'transaction'].groupby('visitorid').size()
        visitor_metrics = visitor_metrics.fillna(0)
        
        # Calculate conversion rates
        visitor_metrics['view_to_cart_rate'] = visitor_metrics['addtocart_count'] / visitor_metrics['view_count']
        visitor_metrics['cart_to_transaction_rate'] = visitor_metrics['transaction_count'] / visitor_metrics['addtocart_count']
        visitor_metrics = visitor_metrics.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()

        # Scatter plot: Views vs Unique Items
        axes[0].scatter(visitor_metrics['view_count'], visitor_metrics['unique_items'], 
                       alpha=0.5, color='blue', s=10)
        axes[0].set_title('Views vs Unique Items per Visitor', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Number of Views')
        axes[0].set_ylabel('Number of Unique Items')
        axes[0].grid(True, alpha=0.3)
        
        # Add trend line
        if len(visitor_metrics) > 1:
            z = np.polyfit(visitor_metrics['view_count'], visitor_metrics['unique_items'], 1)
            p = np.poly1d(z)
            axes[0].plot(visitor_metrics['view_count'], p(visitor_metrics['view_count']), 
                        color='red', linewidth=2, alpha=0.7)

        # Histogram of view-to-cart conversion rate
        valid_rates = visitor_metrics[visitor_metrics['view_count'] > 0]['view_to_cart_rate']
        axes[1].hist(valid_rates, bins=30, color='green', alpha=0.7, edgecolor='black')
        axes[1].set_title('View-to-Cart Conversion Rate Distribution', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Conversion Rate (Add to Cart / Views)')
        axes[1].set_ylabel('Number of Visitors')
        axes[1].grid(True, alpha=0.3)

        # Box plot: Event counts by visitor segment
        # Segment visitors by total events
        visitor_metrics['event_segment'] = pd.cut(visitor_metrics['view_count'], 
                                                 bins=[0, 1, 5, 10, 20, 50, 100, np.inf],
                                                 labels=['1', '2-5', '6-10', '11-20', '21-50', '51-100', '100+'])
        
        segment_data = []
        segment_labels = []
        for segment in visitor_metrics['event_segment'].cat.categories:
            segment_visitors = visitor_metrics[visitor_metrics['event_segment'] == segment]
            if len(segment_visitors) > 0:
                segment_data.append(segment_visitors['unique_items'].values)
                segment_labels.append(str(segment))
        
        box_parts = axes[2].boxplot(segment_data, patch_artist=True)
        axes[2].set_title('Unique Items by Visitor Engagement Segment', fontsize=12, fontweight='bold')
        axes[2].set_xlabel('Visitor Segment (by view count)')
        axes[2].set_ylabel('Number of Unique Items')
        axes[2].set_xticklabels(segment_labels, rotation=45)
        
        # Color the box plots
        colors = plt.cm.Set3(np.linspace(0, 1, len(segment_data)))
        for patch, color in zip(box_parts['boxes'], colors):
            patch.set_facecolor(color)

        # Hexbin plot: Views vs Add to Cart
        axes[3].hexbin(visitor_metrics['view_count'], visitor_metrics['addtocart_count'], 
                      gridsize=30, cmap='YlOrRd', mincnt=1)
        axes[3].set_title('Views vs Add to Cart Density', fontsize=12, fontweight='bold')
        axes[3].set_xlabel('Number of Views')
        axes[3].set_ylabel('Number of Add to Cart')
        plt.colorbar(axes[3].collections[0], ax=axes[3], label='Density')

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'visitor_engagement_patterns.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved visitor engagement patterns plot")

        # 4.3 Temporal patterns by event type
        print(f"\n   4.3 Temporal patterns by event type:")
        
        # Prepare data for temporal analysis
        temporal_data = self.df_events.copy()
        temporal_data['hour_group'] = pd.cut(temporal_data['hour'], 
                                           bins=[0, 6, 12, 18, 24], 
                                           labels=['Night (0-6)', 'Morning (6-12)', 
                                                  'Afternoon (12-18)', 'Evening (18-24)'])
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()

        # Event distribution by hour group
        hour_group_counts = temporal_data.groupby(['hour_group', 'event']).size().unstack(fill_value=0)
        hour_group_counts.plot(kind='bar', stacked=True, ax=axes[0],
                              color=[EVENT_COLORS.get(e, '#95a5a6') for e in hour_group_counts.columns])
        axes[0].set_title('Event Distribution by Time of Day', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Time of Day')
        axes[0].set_ylabel('Event Count')
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].legend(title='Event Type')

        # Conversion funnel by hour group
        funnel_data = temporal_data.groupby(['hour_group', 'event']).size().unstack(fill_value=0)
        funnel_data['view_to_cart_rate'] = funnel_data['addtocart'] / funnel_data['view']
        funnel_data['cart_to_transaction_rate'] = funnel_data['transaction'] / funnel_data['addtocart']
        funnel_data = funnel_data.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        axes[1].bar(range(len(funnel_data)), funnel_data['view_to_cart_rate'], 
                   color='orange', alpha=0.7, label='View to Cart')
        axes[1].bar(range(len(funnel_data)), funnel_data['cart_to_transaction_rate'], 
                   bottom=funnel_data['view_to_cart_rate'],
                   color='green', alpha=0.7, label='Cart to Transaction')
        axes[1].set_title('Conversion Rates by Time of Day', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Time of Day')
        axes[1].set_ylabel('Conversion Rate')
        axes[1].set_xticks(range(len(funnel_data)))
        axes[1].set_xticklabels(funnel_data.index, rotation=45)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        # Event type distribution by day of week
        day_event_counts = temporal_data.groupby(['day_of_week', 'event']).size().unstack(fill_value=0)
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_event_counts.index = day_names
        
        day_event_counts.plot(kind='bar', stacked=True, ax=axes[2],
                             color=[EVENT_COLORS.get(e, '#95a5a6') for e in day_event_counts.columns])
        axes[2].set_title('Event Distribution by Day of Week', fontsize=12, fontweight='bold')
        axes[2].set_xlabel('Day of Week')
        axes[2].set_ylabel('Event Count')
        axes[2].tick_params(axis='x', rotation=45)
        axes[2].legend(title='Event Type')

        # Heatmap: Event type by day of week and hour group
        pivot_table = pd.pivot_table(temporal_data, 
                                    values='timestamp', 
                                    index='day_of_week',
                                    columns='hour_group',
                                    aggfunc='count',
                                    fill_value=0)
        
        sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='YlOrRd', 
                   ax=axes[3], cbar_kws={'label': 'Event Count'})
        axes[3].set_title('Event Heatmap: Day × Time of Day', fontsize=12, fontweight='bold')
        axes[3].set_xlabel('Time of Day')
        axes[3].set_ylabel('Day of Week')
        axes[3].set_yticklabels(day_names, rotation=0)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'temporal_patterns_analysis.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved temporal patterns analysis plot")

        # 4.4 Item popularity by time of day
        print(f"\n   4.4 Item popularity patterns:")
        
        # Sample data for performance
        sample_data = temporal_data.sample(n=min(10000, len(temporal_data)), random_state=42)
        
        # Top items by event type
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()

        # Top viewed items
        top_viewed = sample_data[sample_data['event'] == 'view']['itemid'].value_counts().head(10)
        axes[0].barh(range(len(top_viewed)), top_viewed.values, color=EVENT_COLORS['view'], alpha=0.7)
        axes[0].set_yticks(range(len(top_viewed)))
        axes[0].set_yticklabels([str(item) for item in top_viewed.index])
        axes[0].set_title('Top 10 Most Viewed Items', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('View Count')
        axes[0].invert_yaxis()

        # Top added to cart items
        top_carted = sample_data[sample_data['event'] == 'addtocart']['itemid'].value_counts().head(10)
        axes[1].barh(range(len(top_carted)), top_carted.values, color=EVENT_COLORS['addtocart'], alpha=0.7)
        axes[1].set_yticks(range(len(top_carted)))
        axes[1].set_yticklabels([str(item) for item in top_carted.index])
        axes[1].set_title('Top 10 Most Added to Cart Items', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Add to Cart Count')
        axes[1].invert_yaxis()

        # Top purchased items
        top_purchased = sample_data[sample_data['event'] == 'transaction']['itemid'].value_counts().head(10)
        axes[2].barh(range(len(top_purchased)), top_purchased.values, color=EVENT_COLORS['transaction'], alpha=0.7)
        axes[2].set_yticks(range(len(top_purchased)))
        axes[2].set_yticklabels([str(item) for item in top_purchased.index])
        axes[2].set_title('Top 10 Most Purchased Items', fontsize=12, fontweight='bold')
        axes[2].set_xlabel('Purchase Count')
        axes[2].invert_yaxis()

        # Conversion rate by item (sample)
        item_stats = sample_data.groupby('itemid').agg({
            'event': lambda x: (x == 'view').sum(),
            'timestamp': 'count'
        }).rename(columns={'event': 'view_count', 'timestamp': 'total_events'})
        
        item_stats['addtocart_count'] = sample_data[sample_data['event'] == 'addtocart'].groupby('itemid').size()
        item_stats['transaction_count'] = sample_data[sample_data['event'] == 'transaction'].groupby('itemid').size()
        item_stats = item_stats.fillna(0)
        
        # Calculate conversion rates for items with sufficient views
        item_stats['view_to_cart_rate'] = item_stats['addtocart_count'] / item_stats['view_count']
        item_stats['cart_to_transaction_rate'] = item_stats['transaction_count'] / item_stats['addtocart_count']
        item_stats = item_stats.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Filter for items with at least 5 views
        valid_items = item_stats[item_stats['view_count'] >= 5]
        if len(valid_items) > 0:
            top_conversion = valid_items['view_to_cart_rate'].nlargest(10)
            axes[3].barh(range(len(top_conversion)), top_conversion.values, color='purple', alpha=0.7)
            axes[3].set_yticks(range(len(top_conversion)))
            axes[3].set_yticklabels([str(item) for item in top_conversion.index])
            axes[3].set_title('Top 10 Items by View-to-Cart Conversion', fontsize=12, fontweight='bold')
            axes[3].set_xlabel('Conversion Rate')
            axes[3].invert_yaxis()
        else:
            axes[3].text(0.5, 0.5, 'Insufficient data for conversion analysis', 
                        ha='center', va='center', fontsize=12)
            axes[3].set_title('Conversion Analysis', fontsize=12, fontweight='bold')

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'item_popularity_patterns.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved item popularity patterns plot")

        # Save bivariate statistics
        # Calculate hour_counts for statistics
        hour_counts = self.df_events['hour'].value_counts().sort_index()
        
        self.results['bivariate_stats'] = {
            'event_hour_correlation': {
                'total_events_by_hour': hour_counts.to_dict(),
                'event_distribution_by_hour': event_hour_pivot.to_dict()
            },
            'visitor_engagement': {
                'total_visitors': visitor_metrics.shape[0],
                'mean_views_per_visitor': visitor_metrics['view_count'].mean(),
                'mean_unique_items_per_visitor': visitor_metrics['unique_items'].mean(),
                'mean_addtocart_per_visitor': visitor_metrics['addtocart_count'].mean(),
                'mean_transaction_per_visitor': visitor_metrics['transaction_count'].mean()
            },
            'temporal_patterns': {
                'hour_group_distribution': hour_group_counts.to_dict(),
                'conversion_rates_by_time': funnel_data[['view_to_cart_rate', 'cart_to_transaction_rate']].to_dict()
            }
        }

        self._log("analyze_bivariate_relationships() completed")
        return True

    # ─────────────────────────────────────────
    # 5. MULTIVARIATE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_multivariate_patterns(self):
        """Analyze patterns involving multiple features simultaneously."""
        print("\n5. Multivariate analysis...")
        self._log("analyze_multivariate_patterns() started")

        if self.df_events is None:
            print("   [ERROR] No data available. Run load_data() first.")
            return False

        # 5.1 User-item interaction matrix analysis
        print(f"\n   5.1 User-item interaction patterns:")
        
        # Sample data for performance
        sample_size = min(5000, len(self.df_events))
        sample_data = self.df_events.sample(n=sample_size, random_state=42)
        
        # Create user-item matrix for top users and items
        top_users = sample_data['visitorid'].value_counts().head(50).index
        top_items = sample_data['itemid'].value_counts().head(50).index
        
        filtered_data = sample_data[
            sample_data['visitorid'].isin(top_users) & 
            sample_data['itemid'].isin(top_items)
        ]
        
        if len(filtered_data) > 0:
            # Create pivot table
            user_item_matrix = pd.pivot_table(
                filtered_data,
                values='timestamp',
                index='visitorid',
                columns='itemid',
                aggfunc='count',
                fill_value=0
            )
            
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Heatmap of user-item interactions
            sns.heatmap(user_item_matrix, cmap='YlOrRd', ax=axes[0], 
                       cbar_kws={'label': 'Interaction Count'})
            axes[0].set_title('User-Item Interaction Matrix (Top 50×50)', fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Item ID')
            axes[0].set_ylabel('Visitor ID')
            axes[0].tick_params(axis='x', rotation=90)
            axes[0].tick_params(axis='y', rotation=0)
            
            # Sparsity visualization
            sparsity = (user_item_matrix == 0).sum().sum() / (user_item_matrix.shape[0] * user_item_matrix.shape[1])
            axes[1].bar(['Non-zero', 'Zero'], 
                       [1 - sparsity, sparsity], 
                       color=['green', 'gray'])
            axes[1].set_title(f'Matrix Sparsity: {sparsity:.1%}', fontsize=12, fontweight='bold')
            axes[1].set_ylabel('Percentage')
            axes[1].text(0, 1 - sparsity + 0.01, f'{(1-sparsity)*100:.1f}%', 
                        ha='center', va='bottom', fontsize=10)
            axes[1].text(1, sparsity + 0.01, f'{sparsity*100:.1f}%', 
                        ha='center', va='bottom', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'user_item_interaction_matrix.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved user-item interaction matrix plot")
        
        # 5.2 Session analysis
        print(f"\n   5.2 Session analysis:")
        
        # Define sessions (30-minute inactivity threshold)
        sample_users = sample_data['visitorid'].unique()[:10]  # Analyze first 10 users
        session_data = []
        
        for user_id in sample_users:
            user_events = sample_data[sample_data['visitorid'] == user_id].sort_values('datetime')
            
            if len(user_events) > 1:
                # Calculate time differences
                user_events['time_diff'] = user_events['datetime'].diff().dt.total_seconds() / 60
                
                # Start new session if gap > 30 minutes
                user_events['session_id'] = (user_events['time_diff'] > 30).cumsum()
                
                # Calculate session metrics
                session_metrics = user_events.groupby('session_id').agg({
                    'event': 'count',
                    'itemid': 'nunique',
                    'datetime': lambda x: (x.max() - x.min()).total_seconds() / 60
                }).rename(columns={
                    'event': 'events_per_session',
                    'itemid': 'unique_items_per_session',
                    'datetime': 'session_duration_minutes'
                })
                
                session_data.append(session_metrics)
        
        if session_data:
            session_df = pd.concat(session_data)
            
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            
            # Events per session distribution
            axes[0].hist(session_df['events_per_session'], bins=20, color='blue', alpha=0.7, edgecolor='black')
            axes[0].set_title('Events per Session Distribution', fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Number of Events')
            axes[0].set_ylabel('Frequency')
            axes[0].grid(True, alpha=0.3)
            
            # Unique items per session distribution
            axes[1].hist(session_df['unique_items_per_session'], bins=20, color='green', alpha=0.7, edgecolor='black')
            axes[1].set_title('Unique Items per Session Distribution', fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Number of Unique Items')
            axes[1].set_ylabel('Frequency')
            axes[1].grid(True, alpha=0.3)
            
            # Session duration distribution
            axes[2].hist(session_df['session_duration_minutes'], bins=20, color='red', alpha=0.7, edgecolor='black')
            axes[2].set_title('Session Duration Distribution', fontsize=12, fontweight='bold')
            axes[2].set_xlabel('Duration (minutes)')
            axes[2].set_ylabel('Frequency')
            axes[2].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'session_analysis.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print(f"      [OK] Saved session analysis plot")
        
        # 5.3 Conversion funnel analysis
        print(f"\n   5.3 Conversion funnel analysis:")
        
        # Calculate overall conversion funnel
        total_views = len(self.df_events[self.df_events['event'] == 'view'])
        total_addtocart = len(self.df_events[self.df_events['event'] == 'addtocart'])
        total_transactions = len(self.df_events[self.df_events['event'] == 'transaction'])
        
        funnel_data = pd.DataFrame({
            'Stage': ['Views', 'Add to Cart', 'Transactions'],
            'Count': [total_views, total_addtocart, total_transactions],
            'Conversion Rate': [
                1.0,
                total_addtocart / total_views if total_views > 0 else 0,
                total_transactions / total_addtocart if total_addtocart > 0 else 0
            ]
        })
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # Funnel bar chart
        bars = axes[0].bar(funnel_data['Stage'], funnel_data['Count'], 
                          color=['#3498db', '#e74c3c', '#2ecc71'])
        axes[0].set_title('Overall Conversion Funnel', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Funnel Stage')
        axes[0].set_ylabel('Count')
        axes[0].tick_params(axis='x', rotation=45)
        
        # Add count labels
        for bar, count in zip(bars, funnel_data['Count']):
            height = bar.get_height()
            axes[0].text(bar.get_x() + bar.get_width()/2., height + 100,
                       f'{count:,}', ha='center', va='bottom', fontsize=10)
        
        # Conversion rate line chart
        axes[1].plot(funnel_data['Stage'], funnel_data['Conversion Rate'], 
                    marker='o', linewidth=2, color='purple')
        axes[1].set_title('Conversion Rates by Stage', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Funnel Stage')
        axes[1].set_ylabel('Conversion Rate')
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].grid(True, alpha=0.3)
        
        # Add rate labels
        for i, rate in enumerate(funnel_data['Conversion Rate']):
            axes[1].text(i, rate + 0.01, f'{rate:.2%}', 
                        ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'conversion_funnel_analysis.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved conversion funnel analysis plot")
        
        # Save multivariate statistics
        self.results['multivariate_stats'] = {
            'conversion_funnel': funnel_data.to_dict('records'),
            'session_analysis': {
                'total_sessions_analyzed': len(session_df) if 'session_df' in locals() else 0,
                'mean_events_per_session': session_df['events_per_session'].mean() if 'session_df' in locals() else 0,
                'mean_session_duration': session_df['session_duration_minutes'].mean() if 'session_df' in locals() else 0
            } if 'session_df' in locals() else {}
        }
        
        self._log("analyze_multivariate_patterns() completed")
        return True

    # ─────────────────────────────────────────
    # 6. CATEGORY TREE ANALYSIS
    # ─────────────────────────────────────────
    def analyze_category_hierarchy(self):
        """Analyze product category hierarchy and relationships."""
        print("\n6. Category hierarchy analysis...")
        self._log("analyze_category_hierarchy() started")

        if self.df_category_tree is None:
            print("   [ERROR] Category tree not loaded. Run load_data() first.")
            return False

        # 6.1 Basic category tree statistics
        print(f"\n   6.1 Category tree statistics:")
        
        total_categories = self.df_category_tree['categoryid'].nunique()
        total_parents = self.df_category_tree['parentid'].nunique()
        root_categories = self.df_category_tree[self.df_category_tree['parentid'].isna()]['categoryid'].nunique()
        
        print(f"      - Total unique categories: {total_categories:,}")
        print(f"      - Total unique parent categories: {total_parents:,}")
        print(f"      - Root categories (no parent): {root_categories:,}")
        
        # Calculate category depth
        print(f"\n   6.2 Category depth analysis:")
        
        # Build category depth dictionary
        category_depth = {}
        
        # Find root categories (categories that are not children of any other category)
        all_categories = set(self.df_category_tree['categoryid'].unique())
        all_parents = set(self.df_category_tree['parentid'].dropna().unique())
        root_cats = all_categories - all_parents
        
        # Initialize depth for root categories
        for cat in root_cats:
            category_depth[cat] = 0
        
        # Calculate depth for other categories (simplified approach)
        max_iterations = 10
        for iteration in range(max_iterations):
            updated = False
            for _, row in self.df_category_tree.iterrows():
                category = row['categoryid']
                parent = row['parentid']
                
                if pd.isna(parent):
                    continue
                
                if parent in category_depth and category not in category_depth:
                    category_depth[category] = category_depth[parent] + 1
                    updated = True
            
            if not updated:
                break
        
        # Calculate depth statistics
        if category_depth:
            depths = list(category_depth.values())
            max_depth = max(depths)
            mean_depth = np.mean(depths)
            depth_distribution = pd.Series(depths).value_counts().sort_index()
            
            print(f"      - Maximum category depth: {max_depth}")
            print(f"      - Average category depth: {mean_depth:.1f}")
            print(f"      - Depth distribution:")
            for depth, count in depth_distribution.items():
                print(f"        * Depth {depth}: {count:,} categories")
        
        # 6.3 Category tree visualization
        print(f"\n   6.3 Category tree visualization:")
        
        # Sample categories for visualization
        sample_size = min(50, len(self.df_category_tree))
        sample_data = self.df_category_tree.sample(n=sample_size, random_state=42)
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # Bar chart of category relationships
        if 'category_depth' in locals() and category_depth:
            depth_counts = pd.Series(list(category_depth.values())).value_counts().sort_index()
            axes[0].bar(depth_counts.index, depth_counts.values, color='teal', alpha=0.7)
            axes[0].set_title('Category Depth Distribution', fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Category Depth')
            axes[0].set_ylabel('Number of Categories')
            axes[0].grid(True, alpha=0.3)
        
        # Parent-child relationship visualization
        parent_counts = self.df_category_tree['parentid'].value_counts().head(20)
        axes[1].barh(range(len(parent_counts)), parent_counts.values, color='orange', alpha=0.7)
        axes[1].set_yticks(range(len(parent_counts)))
        axes[1].set_yticklabels([str(parent) for parent in parent_counts.index])
        axes[1].set_title('Top 20 Parent Categories by Number of Children', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Number of Child Categories')
        axes[1].invert_yaxis()
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'category_hierarchy_analysis.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved category hierarchy analysis plot")
        
        # Save category statistics
        self.results['category_stats'] = {
            'total_categories': total_categories,
            'total_parents': total_parents,
            'root_categories': root_categories,
            'max_depth': max_depth if 'max_depth' in locals() else 0,
            'mean_depth': mean_depth if 'mean_depth' in locals() else 0,
            'depth_distribution': depth_distribution.to_dict() if 'depth_distribution' in locals() else {}
        }
        
        self._log("analyze_category_hierarchy() completed")
        return True

    # ─────────────────────────────────────────
    # 7. ITEM PROPERTY ANALYSIS
    # ─────────────────────────────────────────
    def analyze_item_properties(self):
        """Analyze dynamic item properties over time."""
        print("\n7. Item property analysis...")
        self._log("analyze_item_properties() started")

        if self.df_item_props is None:
            print("   [ERROR] Item properties not loaded. Run load_data() first.")
            return False

        # 7.1 Basic property statistics
        print(f"\n   7.1 Item property statistics:")
        
        total_properties = len(self.df_item_props)
        unique_items = self.df_item_props['itemid'].nunique()
        unique_properties = self.df_item_props['property'].nunique()
        
        print(f"      - Total property records: {total_properties:,}")
        print(f"      - Unique items with properties: {unique_items:,}")
        print(f"      - Unique property types: {unique_properties:,}")
        
        # Top properties by frequency
        top_properties = self.df_item_props['property'].value_counts().head(10)
        print(f"\n      - Top 10 most common properties:")
        for prop, count in top_properties.items():
            percentage = count / total_properties * 100
            print(f"        * {prop}: {count:,} ({percentage:.1f}%)")
        
        # 7.2 Property value analysis
        print(f"\n   7.2 Property value analysis:")
        
        # Sample properties for detailed analysis
        sample_props = top_properties.index[:3]
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        plot_idx = 0
        
        for prop_name in sample_props:
            if plot_idx >= 4:
                break
                
            prop_data = self.df_item_props[self.df_item_props['property'] == prop_name]
            
            # Top values for this property
            top_values = prop_data['value'].value_counts().head(10)
            
            axes[plot_idx].barh(range(len(top_values)), top_values.values, color='purple', alpha=0.7)
            axes[plot_idx].set_yticks(range(len(top_values)))
            axes[plot_idx].set_yticklabels([str(val)[:20] + '...' if len(str(val)) > 20 else str(val) 
                                          for val in top_values.index])
            axes[plot_idx].set_title(f'Top Values: {prop_name}', fontsize=12, fontweight='bold')
            axes[plot_idx].set_xlabel('Frequency')
            axes[plot_idx].invert_yaxis()
            
            plot_idx += 1
        
        # Property distribution over time
        if plot_idx < 4:
            # Convert timestamp to datetime
            self.df_item_props['prop_datetime'] = pd.to_datetime(self.df_item_props['timestamp'], unit='ms')
            self.df_item_props['prop_date'] = self.df_item_props['prop_datetime'].dt.date
            
            # Daily property updates
            daily_updates = self.df_item_props.groupby('prop_date').size()
            
            axes[plot_idx].plot(daily_updates.index, daily_updates.values, 
                              marker='o', linewidth=2, color='green')
            axes[plot_idx].set_title('Daily Property Updates', fontsize=12, fontweight='bold')
            axes[plot_idx].set_xlabel('Date')
            axes[plot_idx].set_ylabel('Number of Property Updates')
            axes[plot_idx].tick_params(axis='x', rotation=45)
            axes[plot_idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'item_property_analysis.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved item property analysis plot")
        
        # 7.3 Property changes over time
        print(f"\n   7.3 Property change patterns:")
        
        # Analyze property changes for sample items
        sample_items = self.df_item_props['itemid'].value_counts().head(5).index
        
        fig, axes = plt.subplots(len(sample_items), 1, figsize=(12, 3 * len(sample_items)))
        
        if len(sample_items) == 1:
            axes = [axes]
        
        for idx, item_id in enumerate(sample_items):
            item_props = self.df_item_props[self.df_item_props['itemid'] == item_id]
            
            # Get unique properties for this item
            unique_props = item_props['property'].unique()
            
            # Create timeline visualization
            for prop in unique_props[:3]:  # Show first 3 properties
                prop_timeline = item_props[item_props['property'] == prop]
                axes[idx].scatter(prop_timeline['prop_datetime'], 
                                [prop] * len(prop_timeline), 
                                alpha=0.6, s=50)
            
            axes[idx].set_title(f'Property Timeline for Item {item_id}', fontsize=11, fontweight='bold')
            axes[idx].set_xlabel('Date')
            axes[idx].set_ylabel('Property')
            axes[idx].tick_params(axis='x', rotation=45)
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'property_timeline_analysis.png'), 
                   dpi=150, bbox_inches='tight')
        plt.close()
        print(f"      [OK] Saved property timeline analysis plot")
        
        # Save property statistics
        self.results['property_stats'] = {
            'total_properties': total_properties,
            'unique_items': unique_items,
            'unique_properties': unique_properties,
            'top_properties': top_properties.to_dict(),
            'daily_update_trend': daily_updates.to_dict() if 'daily_updates' in locals() else {}
        }
        
        self._log("analyze_item_properties() completed")
        return True

    # ─────────────────────────────────────────
    # 8. COMPREHENSIVE REPORT GENERATION
    # ─────────────────────────────────────────
    def generate_comprehensive_report(self):
        """Generate comprehensive EDA report with all findings."""
        print("\n8. Generating comprehensive report...")
        self._log("generate_comprehensive_report() started")

        report_path = os.path.join(self.output_dir, 'comprehensive_eda_report.txt')
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("RETAILROCKET RECOMMENDER SYSTEM - COMPREHENSIVE EDA REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("Generated on: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
            f.write("Dataset: Retailrocket E-commerce Recommender System\n")
            f.write("\n" + "=" * 80 + "\n\n")
            
            # 1. Dataset Overview
            f.write("1. DATASET OVERVIEW\n")
            f.write("-" * 40 + "\n")
            if 'dataset_stats' in self.results:
                stats = self.results['dataset_stats']
                f.write(f"   Total Events: {stats['events_rows']:,}\n")
                f.write(f"   Unique Visitors: {stats['unique_visitors']:,}\n")
                f.write(f"   Unique Items: {stats['unique_items']:,}\n")
                f.write(f"   Category Relationships: {stats['category_tree_rows']:,}\n")
                f.write(f"   Item Property Records: {stats['item_props_rows']:,}\n")
                f.write("\n   Event Type Distribution:\n")
                for event_type, count in stats['event_types'].items():
                    percentage = count / stats['events_rows'] * 100
                    f.write(f"     - {EVENT_TYPES.get(event_type, event_type)}: {count:,} ({percentage:.1f}%)\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
            
            # 2. Data Quality Assessment
            f.write("2. DATA QUALITY ASSESSMENT\n")
            f.write("-" * 40 + "\n")
            if 'cleaning_stats' in self.results:
                stats = self.results['cleaning_stats']
                f.write(f"   Original Dataset Size: {stats['original_shape'][0]:,} rows × {stats['original_shape'][1]} columns\n")
                f.write(f"   Cleaned Dataset Size: {stats['cleaned_shape'][0]:,} rows × {stats['cleaned_shape'][1]} columns\n")
                f.write(f"   Rows Removed: {stats['rows_removed']:,}\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
            
            # 3. Key Insights
            f.write("3. KEY INSIGHTS AND RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            
            # User Behavior Insights
            f.write("\n   USER BEHAVIOR INSIGHTS:\n")
            if 'univariate_stats' in self.results and 'visitor_stats' in self.results['univariate_stats']:
                stats = self.results['univariate_stats']['visitor_stats']
                f.write(f"   - Average events per visitor: {stats['mean_events_per_visitor']:.1f}\n")
                f.write(f"   - Average unique items per visitor: {stats['mean_unique_items_per_visitor']:.1f}\n")
                f.write(f"   - Most active visitor had {stats['max_events_per_visitor']:,} events\n")
            
            # Temporal Patterns
            f.write("\n   TEMPORAL PATTERNS:\n")
            if 'univariate_stats' in self.results and 'temporal_stats' in self.results['univariate_stats']:
                stats = self.results['univariate_stats']['temporal_stats']
                f.write(f"   - Date Range: {stats['date_range']['start']} to {stats['date_range']['end']} ({stats['date_range']['days']} days)\n")
                
                # Find peak hour
                if 'hourly_distribution' in stats:
                    hourly = stats['hourly_distribution']
                    peak_hour = max(hourly.items(), key=lambda x: x[1])
                    f.write(f"   - Peak activity hour: {peak_hour[0]}:00 with {peak_hour[1]:,} events\n")
            
            # Conversion Insights
            f.write("\n   CONVERSION INSIGHTS:\n")
            if 'multivariate_stats' in self.results and 'conversion_funnel' in self.results['multivariate_stats']:
                funnel = self.results['multivariate_stats']['conversion_funnel']
                if len(funnel) >= 3:
                    view_to_cart = funnel[1]['Conversion Rate']
                    cart_to_transaction = funnel[2]['Conversion Rate']
                    overall_conversion = funnel[2]['Count'] / funnel[0]['Count'] if funnel[0]['Count'] > 0 else 0
                    
                    f.write(f"   - View to Cart conversion: {view_to_cart:.2%}\n")
                    f.write(f"   - Cart to Transaction conversion: {cart_to_transaction:.2%}\n")
                    f.write(f"   - Overall conversion rate: {overall_conversion:.2%}\n")
            
            # Category Insights
            f.write("\n   CATEGORY INSIGHTS:\n")
            if 'category_stats' in self.results:
                stats = self.results['category_stats']
                f.write(f"   - Total categories in hierarchy: {stats['total_categories']:,}\n")
                f.write(f"   - Maximum category depth: {stats['max_depth']}\n")
                f.write(f"   - Average category depth: {stats['mean_depth']:.1f}\n")
            
            # Property Insights
            f.write("\n   ITEM PROPERTY INSIGHTS:\n")
            if 'property_stats' in self.results:
                stats = self.results['property_stats']
                f.write(f"   - Unique property types: {stats['unique_properties']:,}\n")
                f.write(f"   - Items with properties: {stats['unique_items']:,}\n")
                
                if 'top_properties' in stats and stats['top_properties']:
                    top_prop = max(stats['top_properties'].items(), key=lambda x: x[1])
                    f.write(f"   - Most common property: '{top_prop[0]}' with {top_prop[1]:,} occurrences\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
            
            # 4. Recommendations for Recommender System
            f.write("4. RECOMMENDER SYSTEM IMPLEMENTATION RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            
            f.write("\n   DATA PREPARATION:\n")
            f.write("   1. Handle session identification using 30-minute inactivity threshold\n")
            f.write("   2. Create user-item interaction matrix with appropriate sparsity handling\n")
            f.write("   3. Incorporate temporal features (hour of day, day of week) into models\n")
            
            f.write("\n   FEATURE ENGINEERING:\n")
            f.write("   1. Create user engagement features (total views, unique items, conversion rates)\n")
            f.write("   2. Extract item popularity metrics (view count, add-to-cart rate, purchase rate)\n")
            f.write("   3. Incorporate category hierarchy information\n")
            f.write("   4. Use dynamic item properties for freshness and relevance\n")
            
            f.write("\n   MODELING APPROACHES:\n")
            f.write("   1. Collaborative filtering (user-based, item-based)\n")
            f.write("   2. Matrix factorization techniques\n")
            f.write("   3. Session-based recommendations using RNNs or transformers\n")
            f.write("   4. Hybrid approaches combining content and collaborative filtering\n")
            
            f.write("\n   EVALUATION METRICS:\n")
            f.write("   1. Precision@K, Recall@K for top-K recommendations\n")
            f.write("   2. Mean Average Precision (MAP)\n")
            f.write("   3. Normalized Discounted Cumulative Gain (NDCG)\n")
            f.write("   4. Coverage and novelty metrics\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
            
            # 5. Summary Statistics
            f.write("5. SUMMARY STATISTICS\n")
            f.write("-" * 40 + "\n")
            
            f.write("\n   Dataset Statistics:\n")
            f.write(f"   - Total analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"   - Output directory: {self.output_dir}\n")
            f.write(f"   - Generated plots: Check 'output' directory for visualizations\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
        
        print(f"   [OK] Comprehensive report saved to: {report_path}")
        
        # Also save results as JSON for programmatic access
        json_path = os.path.join(self.output_dir, 'eda_results.json')
        import json
        
        # Convert non-serializable objects
        def convert_to_serializable(obj):
            if isinstance(obj, (pd.Timestamp, datetime)):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(obj, pd.Series):
                return obj.to_dict()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {str(k): convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            else:
                return obj
        
        serializable_results = convert_to_serializable(self.results)
        
        with open(json_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"   [OK] Results saved as JSON to: {json_path}")
        
        self._log("generate_comprehensive_report() completed")
        return True

    # ─────────────────────────────────────────
    # 9. MAIN EXECUTION METHOD
    # ─────────────────────────────────────────
    def run_comprehensive_analysis(self):
        """Execute the complete EDA pipeline."""
        print("=" * 80)
        print("RETAILROCKET RECOMMENDER SYSTEM - ENHANCED EDA")
        print("=" * 80)
        
        start_time = datetime.now()
        self._log(f"Analysis started at {start_time}")
        
        try:
            # Step 1: Load data
            if not self.load_data():
                print("[ERROR] Failed to load data. Exiting.")
                return False
            
            # Step 2: Clean data
            if not self.clean_data():
                print("[ERROR] Failed to clean data. Exiting.")
                return False
            
            # Step 3: Univariate analysis
            if not self.analyze_univariate_distributions():
                print("[ERROR] Failed in univariate analysis. Continuing...")
            
            # Step 4: Bivariate analysis
            if not self.analyze_bivariate_relationships():
                print("[ERROR] Failed in bivariate analysis. Continuing...")
            
            # Step 5: Multivariate analysis
            if not self.analyze_multivariate_patterns():
                print("[ERROR] Failed in multivariate analysis. Continuing...")
            
            # Step 6: Category tree analysis
            if not self.analyze_category_hierarchy():
                print("[ERROR] Failed in category hierarchy analysis. Continuing...")
            
            # Step 7: Item property analysis
            if not self.analyze_item_properties():
                print("[ERROR] Failed in item property analysis. Continuing...")
            
            # Step 8: Generate comprehensive report
            if not self.generate_comprehensive_report():
                print("[ERROR] Failed to generate report. Continuing...")
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "=" * 80)
            print("ANALYSIS COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Duration: {duration}")
            print(f"\nOutput directory: {self.output_dir}")
            print("Check the 'output' folder for all visualizations and reports.")
            print("=" * 80)
            
            self._log(f"Analysis completed successfully at {end_time}")
            self._log(f"Total duration: {duration}")
            
            return True
            
        except Exception as e:
            end_time = datetime.now()
            print(f"\n[ERROR] Analysis failed: {e}")
            self._log(f"Analysis failed at {end_time}: {e}")
            import traceback
            self._log(f"Traceback: {traceback.format_exc()}")
            return False


# ─────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("Initializing Retailrocket Recommender System EDA...")
    
    # Create EDA instance
    eda = EnhancedRetailrocketEDA()
    
    # Run comprehensive analysis
    success = eda.run_comprehensive_analysis()
    
    if success:
        print("\n[SUCCESS] EDA completed successfully!")
        sys.exit(0)
    else:
        print("\n[FAILED] EDA failed!")
        sys.exit(1)