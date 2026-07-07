# Serving Snapshot Audit

- Audit created at: `2026-07-03T22:38:03.718701+00:00`
- Use case: `segmentation`
- Source: `serving.segmentation_feature_base`
- Snapshot path: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\datasets\snapshots\segmentation_feature_base_snapshot_20260703_222522.csv`

## Dataset Overview

- Rows observed: `13013`
- Columns observed: `72`
- Numeric columns: `54`
- Categorical columns: `18`

## Primary Key Checks

- Primary key column: `customer_id`
- Duplicate primary key rows: `0`
- Unique primary key count: `13013`

## Feature Contract

- Candidate feature columns: `62`
- Non-feature columns: `10`
- Reference label columns: `9`

## Data Quality Signals

- Columns with nulls: `0`
- Constant columns: `1`
- Near-constant columns: `1`
- Highly skewed numeric columns: `40`

### Constant Columns

`feature_order_frequency_per_month`

### Near-Constant Columns

- `feature_order_frequency_per_month` dominant value `0` with share `1.0000`

### Highly Skewed Numeric Columns

- `feature_total_valid_orders` skewness `106.8278`, min `0.0`, max `4964.0`
- `feature_effective_order_count` skewness `105.2123`, min `0.0`, max `4964.0`
- `feature_gross_sales_amount` skewness `96.9166`, min `0.0`, max `3229538.96`
- `feature_combined_known_spend` skewness `94.1933`, min `-25111.09`, max `2797634.32`
- `feature_effective_spend` skewness `94.1933`, min `-25111.09`, max `2797634.32`
- `feature_net_revenue` skewness `94.1653`, min `-25111.09`, max `2797634.32`
- `feature_avg_order_value` skewness `78.7634`, min `0.0`, max `84236.25`
- `feature_quantity_per_valid_order` skewness `68.6961`, min `0.0`, max `87167.0`
- `feature_total_quantity_sold` skewness `66.4513`, min `0.0`, max `951644.0`
- `feature_total_cancelled_orders` skewness `62.2606`, min `0.0`, max `391.0`
- `feature_revenue_per_active_day` skewness `60.5311`, min `0.0`, max `84236.25`
- `feature_revenue_per_product` skewness `-50.5450`, min `-25111.09`, max `6501.5`
- `feature_blended_engagement_score` skewness `28.3356`, min `0.0`, max `553.0`
- `feature_active_purchase_days` skewness `26.6213`, min `0.0`, max `553.0`
- `feature_unique_products_purchased` skewness `16.0831`, min `0.0`, max `5177.0`
- `feature_cancelled_row_ratio` skewness `9.3020`, min `0.0`, max `1.0`
- `feature_campaign_response_rate` skewness `8.1831`, min `0.0`, max `0.5`
- `feature_spend_per_valid_order` skewness `7.0084`, min `-10953.5`, max `11880.84`
- `feature_total_campaign_responses` skewness `6.8506`, min `0.0`, max `5.0`
- `feature_catalog_purchases` skewness `5.0373`, min `0.0`, max `28.0`
- `feature_deals_purchases` skewness `4.7075`, min `0.0`, max `15.0`
- `feature_annual_income` skewness `4.1708`, min `0.0`, max `666666.0`
- `feature_campaign_dataset_total_spending` skewness `3.8065`, min `0.0`, max `2525.0`
- `feature_has_churned_flag` skewness `3.7514`, min `0.0`, max `1.0`
- `feature_kids_at_home` skewness `3.7127`, min `0.0`, max `2.0`
- `feature_catalog_purchase_share` skewness `3.6491`, min `0.0`, max `1.0`
- `feature_teens_at_home` skewness `3.4068`, min `0.0`, max `2.0`
- `feature_web_purchases` skewness `3.3968`, min `0.0`, max `27.0`
- `feature_product_diversity_per_order` skewness `3.3596`, min `0.0`, max `220.0`
- `feature_deal_purchase_share` skewness `3.0245`, min `0.0`, max `1.0`
- `feature_store_purchases` skewness `2.8777`, min `0.0`, max `13.0`
- `feature_days_since_last_purchase` skewness `2.6831`, min `0.0`, max `99.0`
- `feature_campaign_dataset_total_purchases` skewness `2.6282`, min `0.0`, max `44.0`
- `feature_days_since_last_order` skewness `2.6256`, min `0.0`, max `99.0`
- `feature_has_any_complaint_flag` skewness `2.5656`, min `0.0`, max `1.0`
- `feature_web_visits_last_month` skewness `2.4897`, min `0.0`, max `20.0`
- `feature_household_size` skewness `2.3553`, min `0.0`, max `4.0`
- `feature_web_purchase_share` skewness `2.2913`, min `0.0`, max `1.0`
- `feature_store_purchase_share` skewness `2.1363`, min `0.0`, max `1.0`
- `feature_customer_tenure_months` skewness `2.0784`, min `0.0`, max `61.0`
