# Serving Snapshot Audit

- Audit created at: `2026-07-04T12:23:21.966558+00:00`
- Use case: `persona`
- Source: `serving.persona_base`
- Snapshot path: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\datasets\snapshots\persona_base_snapshot_20260704_122312.csv`

## Dataset Overview

- Rows observed: `13013`
- Columns observed: `26`
- Numeric columns: `12`
- Categorical columns: `14`

## Primary Key Checks

- Primary key column: `customer_id`
- Duplicate primary key rows: `0`
- Unique primary key count: `13013`

## Feature Contract

- Candidate feature columns: `13`
- Non-feature columns: `13`
- Reference label columns: `11`

## Data Quality Signals

- Columns with nulls: `0`
- Constant columns: `0`
- Near-constant columns: `0`
- Highly skewed numeric columns: `8`

### Highly Skewed Numeric Columns

- `total_valid_orders` skewness `106.8278`, min `0.0`, max `4964.0`
- `effective_spend` skewness `94.1933`, min `-25111.09`, max `2797634.32`
- `catalog_purchases` skewness `5.0373`, min `0.0`, max `28.0`
- `deals_purchases` skewness `4.7075`, min `0.0`, max `15.0`
- `annual_income` skewness `4.1708`, min `0.0`, max `666666.0`
- `web_purchases` skewness `3.3968`, min `0.0`, max `27.0`
- `store_purchases` skewness `2.8777`, min `0.0`, max `13.0`
- `web_visits_last_month` skewness `2.4897`, min `0.0`, max `20.0`
