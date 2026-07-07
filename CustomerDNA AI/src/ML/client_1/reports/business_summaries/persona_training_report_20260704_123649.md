# Persona Classification Training Report

- Created at: `2026-07-04T12:36:49.798381+00:00`
- Use case: `persona`
- Processed matrix path: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\datasets\processed\persona_base_processed_20260704_123219.csv`
- Row count: `13013`
- Feature count: `8`
- Persona class count: `7`

## Selected Model

- Model name: `gradient_boosting`
- Train rows: `10410`
- Test rows: `2603`
- Accuracy: `0.919708`
- Balanced accuracy: `0.732383`
- Macro precision: `0.715081`
- Macro recall: `0.732383`
- Macro F1: `0.722738`
- Weighted F1: `0.892697`

## Candidate Results

| Model | Accuracy | Balanced Acc. | Macro F1 | Weighted F1 |
|---|---:|---:|---:|---:|
| logistic_regression | 0.615060 | 0.680371 | 0.549293 | 0.632280 |
| random_forest | 0.721475 | 0.777987 | 0.715210 | 0.754475 |
| gradient_boosting | 0.919708 | 0.732383 | 0.722738 | 0.892697 |
