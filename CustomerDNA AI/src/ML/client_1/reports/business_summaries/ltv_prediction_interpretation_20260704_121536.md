# LTV Prediction Interpretation

- Created at: `2026-07-04T12:15:36.337531+00:00`
- Use case: `ltv`
- Source training metrics: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\models\model_metadata\ltv_regressor_training_metrics_20260704_121247.json`
- Selected model: `gradient_boosting_regressor`
- MAE: `1442.727607`
- RMSE: `46000.094631`
- R²: `0.310273`
- Explained variance: `0.310392`

## Value Band Summary

### Premium Value

- Customers in holdout set: `651`
- Share of holdout set: `25.01%`
- Average predicted LTV: `6530.39`
- Average actual LTV: `8996.55`
- Median actual LTV: `1985.87`
- Dominant value tier: `High Value`
- Dominant sales band: `Top Account`
- Dominant segment: `VIP Active`
- Recommended action: Prioritize white-glove retention, personalized upsell, and premium-service treatment to protect future value.

### High Value

- Customers in holdout set: `650`
- Share of holdout set: `24.97%`
- Average predicted LTV: `547.92`
- Average actual LTV: `573.30`
- Median actual LTV: `496.69`
- Dominant value tier: `Upper Mid Value`
- Dominant sales band: `Medium Account`
- Dominant segment: `High Value Low Engagement`
- Recommended action: Use cross-sell and loyalty reinforcement campaigns to grow wallet share while preserving retention.

### Medium Value

- Customers in holdout set: `651`
- Share of holdout set: `25.01%`
- Average predicted LTV: `74.06`
- Average actual LTV: `47.32`
- Median actual LTV: `0.00`
- Dominant value tier: `Unclassified`
- Dominant sales band: `No Sales`
- Dominant segment: `Dormant`
- Recommended action: Target with growth campaigns, product discovery, and engagement journeys to increase future value.

### Low Value

- Customers in holdout set: `651`
- Share of holdout set: `25.01%`
- Average predicted LTV: `-3.40`
- Average actual LTV: `-50.73`
- Median actual LTV: `0.00`
- Dominant value tier: `Unclassified`
- Dominant sales band: `No Sales`
- Dominant segment: `Dormant`
- Recommended action: Apply low-cost reactivation and nurture journeys rather than high-cost premium interventions.

## Top Model Drivers

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | numeric__feature_total_quantity_sold | 0.703226 |
| 2 | numeric__feature_product_diversity_per_order | 0.118713 |
| 3 | numeric__feature_effective_order_count | 0.037813 |
| 4 | numeric__feature_total_valid_orders | 0.037200 |
| 5 | numeric__feature_quantity_per_order | 0.030592 |
| 6 | numeric__feature_active_purchase_days | 0.029476 |
| 7 | numeric__feature_unique_products_purchased | 0.026721 |
| 8 | numeric__feature_blended_engagement_score | 0.015565 |
| 9 | numeric__feature_annual_income | 0.000226 |
| 10 | numeric__feature_catalog_purchases | 0.000190 |
| 11 | categorical__gender_category_Unknown | 0.000169 |
| 12 | numeric__has_churn_data_flag | 0.000052 |
| 13 | numeric__feature_churn_risk_score | 0.000034 |
| 14 | numeric__feature_campaign_response_rate | 0.000012 |
| 15 | numeric__feature_household_size | 0.000004 |
