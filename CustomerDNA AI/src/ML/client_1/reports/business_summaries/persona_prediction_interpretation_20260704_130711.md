# Persona Prediction Interpretation

- Created at: `2026-07-04T13:07:11.621916+00:00`
- Use case: `persona`
- Source training metrics: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\models\model_metadata\persona_classifier_training_metrics_20260704_123649.json`
- Selected model: `gradient_boosting`
- Accuracy: `0.919708`
- Balanced accuracy: `0.732383`
- Macro F1: `0.722738`
- Weighted F1: `0.892697`

## Persona Group Summary

### Dormant Customer

- Customers in holdout set: `1304`
- Share of holdout set: `50.10%`
- Dominant lifecycle stage: `Dormant`
- Dominant digital affinity: `Low Digital Affinity`
- Dominant price sensitivity: `Low Price Sensitivity`
- Persona precision within group: `86.50%`
- Description: This predicted persona group is dominated by customers labeled as 'Dormant Customer'. They are most commonly in the 'Dormant' lifecycle stage, show 'Low Digital Affinity' behavior, and tend toward 'Low Price Sensitivity'. The dominant value tier is 'Unclassified', and the holdout precision for this predicted persona is 86.50%.
- Recommended action: Launch reactivation journeys with simple incentives and reminder messaging.

### Premium Loyalist

- Customers in holdout set: `557`
- Share of holdout set: `21.40%`
- Dominant lifecycle stage: `Dormant`
- Dominant digital affinity: `Low Digital Affinity`
- Dominant price sensitivity: `Low Price Sensitivity`
- Persona precision within group: `99.46%`
- Description: This predicted persona group is dominated by customers labeled as 'Premium Loyalist'. They are most commonly in the 'Dormant' lifecycle stage, show 'Low Digital Affinity' behavior, and tend toward 'Low Price Sensitivity'. The dominant value tier is 'High Value', and the holdout precision for this predicted persona is 99.46%.
- Recommended action: Protect loyalty with premium offers, recognition, and high-touch personalized journeys.

### At-Risk High Spender

- Customers in holdout set: `443`
- Share of holdout set: `17.02%`
- Dominant lifecycle stage: `Dormant`
- Dominant digital affinity: `Low Digital Affinity`
- Dominant price sensitivity: `Low Price Sensitivity`
- Persona precision within group: `99.77%`
- Description: This predicted persona group is dominated by customers labeled as 'At-Risk High Spender'. They are most commonly in the 'Dormant' lifecycle stage, show 'Low Digital Affinity' behavior, and tend toward 'Low Price Sensitivity'. The dominant value tier is 'Upper Mid Value', and the holdout precision for this predicted persona is 99.77%.
- Recommended action: Prioritize retention recovery with curated offers and urgent engagement follow-up.

### Core Relationship Customer

- Customers in holdout set: `145`
- Share of holdout set: `5.57%`
- Dominant lifecycle stage: `New`
- Dominant digital affinity: `Low Digital Affinity`
- Dominant price sensitivity: `Low Price Sensitivity`
- Persona precision within group: `86.21%`
- Description: This predicted persona group is dominated by customers labeled as 'Core Relationship Customer'. They are most commonly in the 'New' lifecycle stage, show 'Low Digital Affinity' behavior, and tend toward 'Low Price Sensitivity'. The dominant value tier is 'Upper Mid Value', and the holdout precision for this predicted persona is 86.21%.
- Recommended action: Maintain personalized lifecycle communication and monitor behavior shifts.

### Growth Challenger

- Customers in holdout set: `144`
- Share of holdout set: `5.53%`
- Dominant lifecycle stage: `New`
- Dominant digital affinity: `Low Digital Affinity`
- Dominant price sensitivity: `Moderate Price Sensitivity`
- Persona precision within group: `98.61%`
- Description: This predicted persona group is dominated by customers labeled as 'Growth Challenger'. They are most commonly in the 'New' lifecycle stage, show 'Low Digital Affinity' behavior, and tend toward 'Moderate Price Sensitivity'. The dominant value tier is 'Mid Value', and the holdout precision for this predicted persona is 98.61%.
- Recommended action: Use conversion-acceleration campaigns, bundles, and progressive upsell strategies.

### Promo-Driven Regular

- Customers in holdout set: `10`
- Share of holdout set: `0.38%`
- Dominant lifecycle stage: `New`
- Dominant digital affinity: `Low Digital Affinity`
- Dominant price sensitivity: `Moderate Price Sensitivity`
- Persona precision within group: `30.00%`
- Description: This predicted persona group is dominated by customers labeled as 'Promo-Driven Regular'. They are most commonly in the 'New' lifecycle stage, show 'Low Digital Affinity' behavior, and tend toward 'Moderate Price Sensitivity'. The dominant value tier is 'Upper Mid Value', and the holdout precision for this predicted persona is 30.00%.
- Recommended action: Lead with promotion-sensitive campaigns and savings-oriented product messaging.

## Top Model Drivers

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | numeric__effective_spend | 0.543588 |
| 2 | numeric__web_visits_last_month | 0.195145 |
| 3 | numeric__total_valid_orders | 0.170196 |
| 4 | numeric__annual_income | 0.034000 |
| 5 | numeric__customer_age | 0.028185 |
| 6 | numeric__churn_risk_score | 0.027499 |
| 7 | categorical__customer_360_record_source_segments_sales_profile | 0.000761 |
| 8 | categorical__customer_360_record_source_segments_and_sales | 0.000625 |
