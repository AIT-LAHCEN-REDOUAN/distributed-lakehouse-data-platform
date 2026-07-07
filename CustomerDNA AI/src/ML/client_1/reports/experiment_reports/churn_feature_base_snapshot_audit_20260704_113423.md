# Serving Snapshot Audit

- Audit created at: `2026-07-04T11:34:23.084317+00:00`
- Use case: `churn`
- Source: `serving.churn_feature_base`
- Snapshot path: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\datasets\snapshots\churn_feature_base_snapshot_20260704_113407.csv`

## Dataset Overview

- Rows observed: `13013`
- Columns observed: `65`
- Numeric columns: `49`
- Categorical columns: `16`

## Primary Key Checks

- Primary key column: `customer_id`
- Duplicate primary key rows: `0`
- Unique primary key count: `13013`

## Feature Contract

- Candidate feature columns: `59`
- Non-feature columns: `6`
- Reference label columns: `4`

## Data Quality Signals

- Columns with nulls: `0`
- Constant columns: `3`
- Near-constant columns: `3`
- Highly skewed numeric columns: `33`

### Constant Columns

`feature_order_recency_ratio`, `feature_orders_per_month`, `feature_low_satisfaction_flag`

### Near-Constant Columns

- `feature_order_recency_ratio` dominant value `0` with share `1.0000`
- `feature_orders_per_month` dominant value `0` with share `1.0000`
- `feature_low_satisfaction_flag` dominant value `0` with share `1.0000`

### Highly Skewed Numeric Columns

- `feature_total_valid_orders` skewness `106.8278`, min `0.0`, max `4964.0`
- `feature_effective_order_count` skewness `105.2123`, min `0.0`, max `4964.0`
- `feature_gross_sales_amount` skewness `96.9166`, min `0.0`, max `3229538.96`
- `feature_combined_known_spend` skewness `94.1933`, min `-25111.09`, max `2797634.32`
- `feature_effective_spend` skewness `94.1933`, min `-25111.09`, max `2797634.32`
- `feature_net_revenue` skewness `94.1653`, min `-25111.09`, max `2797634.32`
- `feature_avg_order_value` skewness `78.7634`, min `0.0`, max `84236.25`
- `feature_total_quantity_sold` skewness `66.4513`, min `0.0`, max `951644.0`
- `feature_total_cancelled_orders` skewness `62.2606`, min `0.0`, max `391.0`
- `feature_revenue_per_active_day` skewness `60.5311`, min `0.0`, max `84236.25`
- `feature_blended_engagement_score` skewness `28.3356`, min `0.0`, max `553.0`
- `feature_active_purchase_days` skewness `26.6213`, min `0.0`, max `553.0`
- `feature_unique_products_purchased` skewness `16.0831`, min `0.0`, max `5177.0`
- `feature_cancelled_row_ratio` skewness `9.3020`, min `0.0`, max `1.0`
- `feature_total_campaign_responses` skewness `6.8506`, min `0.0`, max `5.0`
- `feature_catalog_purchases` skewness `5.0373`, min `0.0`, max `28.0`
- `feature_deals_purchases` skewness `4.7075`, min `0.0`, max `15.0`
- `feature_annual_income` skewness `4.1708`, min `0.0`, max `666666.0`
- `feature_campaign_dataset_total_spending` skewness `3.8065`, min `0.0`, max `2525.0`
- `target_has_churned_flag` skewness `3.7514`, min `0.0`, max `1.0`
- `feature_kids_at_home` skewness `3.7127`, min `0.0`, max `2.0`
- `feature_teens_at_home` skewness `3.4068`, min `0.0`, max `2.0`
- `feature_web_purchases` skewness `3.3968`, min `0.0`, max `27.0`
- `feature_order_cancellation_share` skewness `3.0899`, min `0.0`, max `1.0`
- `feature_store_purchases` skewness `2.8777`, min `0.0`, max `13.0`
- `feature_purchase_recency_ratio` skewness `2.6922`, min `0.0`, max `0.022556390977443608`
- `feature_days_since_last_purchase` skewness `2.6831`, min `0.0`, max `99.0`
- `feature_campaign_dataset_total_purchases` skewness `2.6282`, min `0.0`, max `44.0`
- `feature_days_since_last_order` skewness `2.6256`, min `0.0`, max `99.0`
- `feature_has_any_complaint_flag` skewness `2.5656`, min `0.0`, max `1.0`
- `feature_web_visits_last_month` skewness `2.4897`, min `0.0`, max `20.0`
- `feature_household_size` skewness `2.3553`, min `0.0`, max `4.0`
- `feature_customer_tenure_months` skewness `2.0784`, min `0.0`, max `61.0`
