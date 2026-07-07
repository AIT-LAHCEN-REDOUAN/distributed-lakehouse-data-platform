# Marketing Recommendation Prediction Interpretation

- Created at: `2026-07-04T13:16:42.006921+00:00`
- Use case: `marketing_recommendation`
- Source training metrics: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\models\model_metadata\marketing_recommendation_classifier_training_metrics_20260704_131443.json`
- Selected model: `gradient_boosting`
- Accuracy: `0.534768`
- Balanced accuracy: `0.271037`
- Macro F1: `0.213795`
- Weighted F1: `0.422660`

## Offer Group Summary

### Personalized Content

- Customers in holdout set: `1431`
- Share of holdout set: `54.97%`
- Precision within predicted group: `58.07%`
- Confidence band: `Moderate Confidence`
- Dominant objective: `Reactivation`
- Dominant channel: `Email`
- Dominant timing: `This Month`
- Dominant next best action: `Maintain regular personalized engagement`
- Description: The model predicts the 'Personalized Content' offer type for this customer group. The dominant linked campaign objective is 'Reactivation', the usual outbound channel is 'Email', and the dominant timing is 'This Month'. Prediction precision within this predicted group is 58.07%, which corresponds to a 'Moderate Confidence' quality level.
- Reliability note: This predicted offer class is directionally useful but should still be reviewed with business rules.

### Bundle Recommendation

- Customers in holdout set: `1172`
- Share of holdout set: `45.02%`
- Precision within predicted group: `47.87%`
- Confidence band: `Low Confidence`
- Dominant objective: `Loyalty Expansion`
- Dominant channel: `Email`
- Dominant timing: `This Month`
- Dominant next best action: `Maintain regular personalized engagement`
- Description: The model predicts the 'Bundle Recommendation' offer type for this customer group. The dominant linked campaign objective is 'Loyalty Expansion', the usual outbound channel is 'Email', and the dominant timing is 'This Month'. Prediction precision within this predicted group is 47.87%, which corresponds to a 'Low Confidence' quality level.
- Reliability note: This predicted offer class should be treated as weak guidance and combined with stronger rule filters.

## Top Model Drivers

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | categorical__customer_360_record_source_segments_sales_profile | 0.539837 |
| 2 | categorical__customer_360_record_source_segments_and_sales | 0.460163 |
