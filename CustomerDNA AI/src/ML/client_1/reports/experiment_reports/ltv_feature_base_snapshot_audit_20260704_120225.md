# Serving Snapshot Audit

- Audit created at: `2026-07-04T12:02:25.144242+00:00`
- Use case: `ltv`
- Source: `serving.ltv_feature_base`
- Snapshot path: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\datasets\snapshots\ltv_feature_base_snapshot_20260704_120215.csv`

## Dataset Overview

- Rows observed: `13013`
- Columns observed: `55`
- Numeric columns: `45`
- Categorical columns: `10`

## Primary Key Checks

- Primary key column: `customer_id`
- Duplicate primary key rows: `0`
- Unique primary key count: `13013`

## Feature Contract

- Candidate feature columns: `48`
- Non-feature columns: `7`
- Reference label columns: `5`

## Data Quality Signals

- Columns with nulls: `0`
- Constant columns: `0`
- Near-constant columns: `1`
- Highly skewed numeric columns: `32`

### Near-Constant Columns

- `feature_cross_border_flag` dominant value `0` with share `0.9989`

### Highly Skewed Numeric Columns

- `feature_total_valid_orders` skewness `106.8278`, min `0.0`, max `4964.0`
- `target_observed_total_valid_orders` skewness `106.8278`, min `0.0`, max `4964.0`
- `feature_effective_order_count` skewness `105.2123`, min `0.0`, max `4964.0`
- `feature_combined_known_spend` skewness `94.1933`, min `-25111.09`, max `2797634.32`
- `feature_effective_spend` skewness `94.1933`, min `-25111.09`, max `2797634.32`
- `target_observed_ltv_proxy` skewness `94.1933`, min `-25111.09`, max `2797634.32`
- `target_observed_net_revenue` skewness `94.1653`, min `-25111.09`, max `2797634.32`
- `feature_avg_order_value` skewness `78.7634`, min `0.0`, max `84236.25`
- `feature_quantity_per_order` skewness `68.6961`, min `0.0`, max `87167.0`
- `feature_total_quantity_sold` skewness `66.4513`, min `0.0`, max `951644.0`
- `feature_revenue_per_active_day` skewness `60.5311`, min `0.0`, max `84236.25`
- `feature_revenue_per_product` skewness `-50.5450`, min `-25111.09`, max `6501.5`
- `feature_cross_border_flag` skewness `30.4385`, min `0.0`, max `1.0`
- `feature_blended_engagement_score` skewness `28.3356`, min `0.0`, max `553.0`
- `feature_active_purchase_days` skewness `26.6213`, min `0.0`, max `553.0`
- `feature_unique_products_purchased` skewness `16.0831`, min `0.0`, max `5177.0`
- `feature_campaign_response_rate` skewness `8.1831`, min `0.0`, max `0.5`
- `feature_revenue_per_order` skewness `7.0084`, min `-10953.5`, max `11880.84`
- `feature_total_campaign_responses` skewness `6.8506`, min `0.0`, max `5.0`
- `feature_catalog_purchases` skewness `5.0373`, min `0.0`, max `28.0`
- `feature_deals_purchases` skewness `4.7075`, min `0.0`, max `15.0`
- `feature_annual_income` skewness `4.1708`, min `0.0`, max `666666.0`
- `feature_campaign_dataset_total_spending` skewness `3.8065`, min `0.0`, max `2525.0`
- `feature_web_purchases` skewness `3.3968`, min `0.0`, max `27.0`
- `feature_product_diversity_per_order` skewness `3.3596`, min `0.0`, max `220.0`
- `feature_store_purchases` skewness `2.8777`, min `0.0`, max `13.0`
- `feature_days_since_last_purchase` skewness `2.6831`, min `0.0`, max `99.0`
- `feature_campaign_dataset_total_purchases` skewness `2.6282`, min `0.0`, max `44.0`
- `feature_has_any_complaint_flag` skewness `2.5656`, min `0.0`, max `1.0`
- `feature_web_visits_last_month` skewness `2.4897`, min `0.0`, max `20.0`
- `feature_household_size` skewness `2.3553`, min `0.0`, max `4.0`
- `feature_customer_tenure_months` skewness `2.0784`, min `0.0`, max `61.0`
