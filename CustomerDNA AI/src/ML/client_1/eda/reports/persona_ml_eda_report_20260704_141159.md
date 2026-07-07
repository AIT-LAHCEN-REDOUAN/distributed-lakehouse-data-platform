# Persona ML EDA Report

- Training metrics source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\models\model_metadata\persona_classifier_training_metrics_20260704_123649.json`
- Holdout predictions source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\reports\business_summaries\persona_holdout_predictions_20260704_123649.csv`
- Feature importance source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\reports\business_summaries\persona_feature_importance_20260704_123649.csv`
- Rows in modeled dataset: `13013`
- Holdout rows: `2603`

## Key Metrics

- Accuracy: `0.919708`
- Balanced accuracy: `0.732383`
- Macro precision: `0.715081`
- Macro recall: `0.732383`
- Macro F1: `0.722738`
- Weighted F1: `0.892697`

## Class Profile

- Persona class count: `7`

### Training Class Distribution

- `Dormant Customer`: `5695`
- `Premium Loyalist`: `2775`
- `At-Risk High Spender`: `2335`
- `Lost Customer`: `765`
- `Growth Challenger`: `717`
- `Core Relationship Customer`: `670`
- `Promo-Driven Regular`: `56`

### Holdout Predicted Distribution

- `Dormant Customer`: `1304`
- `Premium Loyalist`: `557`
- `At-Risk High Spender`: `443`
- `Core Relationship Customer`: `145`
- `Growth Challenger`: `144`
- `Promo-Driven Regular`: `10`

## Best Per-Class F1 Labels

- `Premium Loyalist`
- `Growth Challenger`
- `At-Risk High Spender`

## Top Features

- `numeric__effective_spend`
- `numeric__web_visits_last_month`
- `numeric__total_valid_orders`
- `numeric__annual_income`
- `numeric__customer_age`

## Main Findings

- Accuracy is much higher than balanced accuracy, which means class imbalance is inflating the global score.
- Weighted F1 is much stronger than macro F1, so the model performs better on frequent personas than on rare ones.
- The strongest predicted persona group is 'At-Risk High Spender' with precision 99.77%, while the weakest is 'Promo-Driven Regular' with precision 30.00%.

## Generated Plots

- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\persona\persona_class_distribution_20260704_141159.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\persona\persona_confusion_matrix_20260704_141159.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\persona\persona_per_class_metrics_20260704_141159.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\persona\persona_prediction_distribution_20260704_141159.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\persona\persona_group_precision_20260704_141159.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\persona\persona_feature_importance_top15_20260704_141159.png`
