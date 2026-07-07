# Churn Prediction Interpretation

- Created at: `2026-07-04T12:00:17.390026+00:00`
- Use case: `churn`
- Source training metrics: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\models\model_metadata\churn_classifier_training_metrics_20260704_114959.json`
- Selected model: `random_forest`
- Accuracy: `0.977718`
- Precision: `0.748691`
- Recall: `0.934641`
- F1 score: `0.831395`
- ROC-AUC: `0.994566`
- Average precision: `0.921275`

## Risk Band Summary

### Critical Risk

- Customers in holdout set: `71`
- Share of holdout set: `2.73%`
- Average predicted churn probability: `0.8838`
- Actual churn rate in band: `100.00%`
- Dominant retention status: `Churned`
- Dominant churn risk band: `Critical`
- Dominant customer segment: `Lost Customer`
- Recommended action: Launch immediate retention intervention with personalized outreach, complaint resolution, and high-priority incentive follow-up.

### High Risk

- Customers in holdout set: `84`
- Share of holdout set: `3.23%`
- Average predicted churn probability: `0.7024`
- Actual churn rate in band: `67.86%`
- Dominant retention status: `Churned`
- Dominant churn risk band: `Critical`
- Dominant customer segment: `Lost Customer`
- Recommended action: Place in proactive churn-prevention campaign with targeted offers and close journey monitoring.

### Medium Risk

- Customers in holdout set: `89`
- Share of holdout set: `3.42%`
- Average predicted churn probability: `0.4705`
- Actual churn rate in band: `24.72%`
- Dominant retention status: `Stable`
- Dominant churn risk band: `Stable`
- Dominant customer segment: `Dormant`
- Recommended action: Use watchlist treatment: reminder messaging, engagement nudges, and satisfaction follow-up.

### Low Risk

- Customers in holdout set: `2359`
- Share of holdout set: `90.63%`
- Average predicted churn probability: `0.0318`
- Actual churn rate in band: `0.13%`
- Dominant retention status: `Unknown`
- Dominant churn risk band: `Unknown`
- Dominant customer segment: `Dormant`
- Recommended action: Continue standard lifecycle communication and monitor for new churn signals.

## Top Model Drivers

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | numeric__feature_customer_tenure_months | 0.087064 |
| 2 | numeric__has_churn_data_flag | 0.075235 |
| 3 | numeric__feature_number_of_devices_registered | 0.064713 |
| 4 | categorical__customer_loyalty_tier_category_Recent | 0.063070 |
| 5 | numeric__feature_churn_risk_score | 0.054727 |
| 6 | categorical__preferred_order_category_Unknown | 0.035112 |
| 7 | categorical__gender_category_Unknown | 0.033459 |
| 8 | categorical__preferred_login_device_category_Unknown | 0.032893 |
| 9 | categorical__customer_activity_level_category_Unknown | 0.031879 |
| 10 | categorical__city_tier_category_Unknown | 0.030755 |
| 11 | numeric__feature_days_since_last_order | 0.026775 |
| 12 | categorical__customer_loyalty_tier_category_Unknown | 0.026770 |
| 13 | categorical__satisfaction_level_category_Unknown | 0.026595 |
| 14 | numeric__feature_combined_known_spend | 0.022731 |
| 15 | categorical__preferred_payment_mode_category_Unknown | 0.022582 |
