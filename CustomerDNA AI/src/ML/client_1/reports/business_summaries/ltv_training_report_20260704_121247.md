# LTV Regression Training Report

- Created at: `2026-07-04T12:12:47.613822+00:00`
- Use case: `ltv`
- Processed matrix path: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\datasets\processed\ltv_feature_base_processed_20260704_121227.csv`
- Row count: `13013`
- Feature count: `62`
- Target mean: `1597.576707`
- Target median: `178.830000`
- Negative target count: `83`

## Selected Model

- Model name: `gradient_boosting_regressor`
- Train rows: `10410`
- Test rows: `2603`
- MAE: `1442.727607`
- RMSE: `46000.094631`
- R²: `0.310273`
- Explained variance: `0.310392`
- Median absolute error: `59.545000`

## Candidate Results

| Model | MAE | RMSE | R² | Explained Variance | MedAE |
|---|---:|---:|---:|---:|---:|
| ridge_regression | 2481.373955 | 54098.389188 | 0.046044 | 0.046482 | 166.807874 |
| random_forest_regressor | 1394.684136 | 47596.354425 | 0.261574 | 0.261752 | 27.582784 |
| gradient_boosting_regressor | 1442.727607 | 46000.094631 | 0.310273 | 0.310392 | 59.545000 |
