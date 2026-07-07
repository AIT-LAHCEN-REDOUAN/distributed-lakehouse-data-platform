# Churn Classification Training Report

- Created at: `2026-07-04T11:49:59.769701+00:00`
- Use case: `churn`
- Processed matrix path: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\datasets\processed\churn_feature_base_processed_20260704_114004.csv`
- Row count: `13013`
- Feature count: `107`
- Positive churn rate: `0.058787`

## Selected Model

- Model name: `random_forest`
- Train rows: `10410`
- Test rows: `2603`
- Accuracy: `0.977718`
- Precision: `0.748691`
- Recall: `0.934641`
- F1 score: `0.831395`
- ROC-AUC: `0.994566`
- Average precision: `0.921275`

## Candidate Results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|
| logistic_regression | 0.879370 | 0.314088 | 0.888889 | 0.464164 | 0.965752 | 0.744956 |
| random_forest | 0.977718 | 0.748691 | 0.934641 | 0.831395 | 0.994566 | 0.921275 |

## Confusion Matrix

- True negative: `2402`
- False positive: `48`
- False negative: `10`
- True positive: `143`
