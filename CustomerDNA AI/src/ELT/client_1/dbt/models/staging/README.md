# Staging Models

Staging models clean and standardize raw data from the `raw_data` schema.

## Purpose

1. **Data Cleaning**: Handle missing values, duplicates, and inconsistencies
2. **Standardization**: Convert data types, format dates, normalize text
3. **Validation**: Ensure data quality before transformation
4. **Documentation**: Add column descriptions and business context

## Naming Convention

- `stg_<source_table_name>.sql`
- Example: `stg_marketing_campaign.sql`

## Best Practices

1. **Preserve Raw Data**: Never modify raw tables directly
2. **Add Metadata**: Include load timestamps and source information
3. **Document Changes**: Comment on transformations applied
4. **Test Early**: Add data quality tests in staging

## Example Model

```sql
-- models/staging/stg_marketing_campaign.sql

{{ config(
    materialized='view',
    schema='staging'
) }}

SELECT
    -- Clean and cast columns
    CAST(customer_id AS INTEGER) AS customer_id,
    TRIM(LOWER(education)) AS education_level,
    CAST(income AS DECIMAL(10, 2)) AS annual_income,
    
    -- Handle missing values
    COALESCE(marital_status, 'Unknown') AS marital_status,
    
    -- Add metadata
    CURRENT_TIMESTAMP AS loaded_at,
    'raw_data.marketing_campaign' AS source_table
    
FROM {{ source('raw_data', 'marketing_campaign') }}
WHERE customer_id IS NOT NULL
```