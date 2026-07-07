# Marketing Recommendation ML EDA Report

- Training metrics source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\models\model_metadata\marketing_recommendation_classifier_training_metrics_20260704_131443.json`
- Holdout predictions source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\reports\business_summaries\marketing_recommendation_holdout_predictions_20260704_131443.csv`
- Feature importance source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\reports\business_summaries\marketing_recommendation_feature_importance_20260704_131443.csv`
- Interpreted recommendation summary source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\reports\business_summaries\marketing_recommendation_offer_summary_20260704_131642.csv`
- Rows in modeled dataset: `13013`
- Holdout rows: `2603`

## Selected Model

- Selected model: `gradient_boosting`
- Best accuracy among candidates: `gradient_boosting`
- Accuracy: `0.534768`
- Balanced accuracy: `0.271037`
- Macro precision: `0.176564`
- Macro recall: `0.271037`
- Macro F1: `0.213795`
- Weighted F1: `0.422660`

## Training Class Distribution

- `Personalized Content`: `4772`
- `Bundle Recommendation`: `3711`
- `Premium Upsell`: `2775`
- `Win-Back Incentive`: `1725`
- `Digital Cross-Sell`: `26`
- `Discount Offer`: `4`

## Holdout Predicted Distribution

- `Personalized Content`: `1431`
- `Bundle Recommendation`: `1172`

## Strongest Predicted Classes

- `Personalized Content`
- `Bundle Recommendation`

## Recommendation Group Summary

### Personalized Content

- Customer count: `1431`
- Customer share: `54.97%`
- Precision within predicted group: `58.07%`
- Confidence band: `Moderate Confidence`
- Dominant objective: `Reactivation` (`47.59%`)
- Dominant channel: `Email` (`80.01%`)
- Dominant persona: `Dormant Customer` (`60.52%`)
- Reliability note: This predicted offer class is directionally useful but should still be reviewed with business rules.

### Bundle Recommendation

- Customer count: `1172`
- Customer share: `45.02%`
- Precision within predicted group: `47.87%`
- Confidence band: `Low Confidence`
- Dominant objective: `Loyalty Expansion` (`41.55%`)
- Dominant channel: `Email` (`100.00%`)
- Dominant persona: `Premium Loyalist` (`41.55%`)
- Reliability note: This predicted offer class should be treated as weak guidance and combined with stronger rule filters.

## Top Features

- `categorical__customer_360_record_source_segments_sales_profile`
- `categorical__customer_360_record_source_segments_and_sales`

## Main Findings

- Accuracy is noticeably higher than balanced accuracy, which means the model is benefiting from class imbalance.
- Weighted F1 is much stronger than macro F1, so the model mainly performs on frequent offer classes and struggles on rare ones.
- The strongest predicted offer group is 'Personalized Content' with precision 58.07%, while the weakest is 'Bundle Recommendation' with precision 47.87%.
- The model does not actively predict every business offer class in the holdout set, which is a strong signal of limited class separability.

## Generated Plots

- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\marketing_recommendation\marketing_candidate_models_20260704_142742.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\marketing_recommendation\marketing_class_distribution_20260704_142742.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\marketing_recommendation\marketing_confusion_matrix_20260704_142742.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\marketing_recommendation\marketing_per_class_metrics_20260704_142742.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\marketing_recommendation\marketing_prediction_distribution_20260704_142742.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\marketing_recommendation\marketing_group_precision_20260704_142742.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\marketing_recommendation\marketing_feature_importance_20260704_142742.png`
