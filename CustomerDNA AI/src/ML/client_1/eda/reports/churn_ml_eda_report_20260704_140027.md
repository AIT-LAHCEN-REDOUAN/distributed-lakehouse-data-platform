# Churn ML EDA Report

- Training metrics source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\models\model_metadata\churn_classifier_training_metrics_20260704_114959.json`
- Holdout predictions source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\reports\business_summaries\churn_holdout_predictions_20260704_114959.csv`
- Feature importance source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\reports\business_summaries\churn_feature_importance_20260704_114959.csv`
- Rows in modeled dataset: `13013`
- Holdout rows: `2603`

## Key Metrics

- Accuracy: `0.977718`
- Precision: `0.748691`
- Recall: `0.934641`
- F1 score: `0.831395`
- ROC-AUC: `0.994566`
- PR-AUC: `0.920952`
- Positive churn rate: `5.88%`

## Confusion Matrix

- True negative: `2402`
- False positive: `48`
- False negative: `10`
- True positive: `143`

## Risk Band Counts

- Critical: `71`
- High: `84`
- Medium: `89`
- Low: `2359`

## Top Features

- `numeric__feature_customer_tenure_months`
- `numeric__has_churn_data_flag`
- `numeric__feature_number_of_devices_registered`
- `categorical__customer_loyalty_tier_category_Recent`
- `numeric__feature_churn_risk_score`

## Main Findings

- The churn target is clearly imbalanced, with only 5.88% positive churn cases.
- The ROC-AUC is extremely strong, which indicates excellent separability between churn and non-churn cases.
- Recall is higher than precision, so the model is aggressive in catching churners at the cost of more false positives.

## Generated Plots

- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\churn\churn_class_balance_20260704_140027.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\churn\churn_confusion_matrix_20260704_140027.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\churn\churn_roc_curve_20260704_140027.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\churn\churn_precision_recall_curve_20260704_140027.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\churn\churn_probability_distribution_20260704_140027.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\churn\churn_risk_band_distribution_20260704_140027.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\churn\churn_feature_importance_top15_20260704_140027.png`
