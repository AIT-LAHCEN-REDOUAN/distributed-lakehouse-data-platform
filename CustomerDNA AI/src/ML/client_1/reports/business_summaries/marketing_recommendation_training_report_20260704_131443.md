# Marketing Recommendation Classification Training Report

- Created at: `2026-07-04T13:14:43.938192+00:00`
- Use case: `marketing_recommendation`
- Processed matrix path: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\datasets\processed\marketing_recommendation_base_processed_20260704_131225.csv`
- Row count: `13013`
- Feature count: `2`
- Recommendation class count: `6`

## Selected Model

- Model name: `gradient_boosting`
- Train rows: `10410`
- Test rows: `2603`
- Accuracy: `0.534768`
- Balanced accuracy: `0.271037`
- Macro precision: `0.176564`
- Macro recall: `0.271037`
- Macro F1: `0.213795`
- Weighted F1: `0.422660`

## Candidate Results

| Model | Accuracy | Balanced Acc. | Macro F1 | Weighted F1 |
|---|---:|---:|---:|---:|
| logistic_regression | 0.319631 | 0.312913 | 0.158750 | 0.171743 |
| random_forest | 0.319631 | 0.312913 | 0.158750 | 0.171743 |
| gradient_boosting | 0.534768 | 0.271037 | 0.213795 | 0.422660 |
