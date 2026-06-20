# Analytical Models

Analytical models create final tables for business intelligence and reporting.

## Purpose

1. **Business Intelligence**: Create tables for dashboards and reports
2. **Performance**: Optimized for query performance
3. **Consistency**: Ensure data consistency across reports
4. **Governance**: Apply data governance rules and access controls

## Naming Convention

- `dim_<dimension_name>.sql` for dimension tables
- `fct_<fact_name>.sql` for fact tables
- Example: `dim_customer.sql`, `fct_sales.sql`

## Best Practices

1. **Star Schema**: Follow dimensional modeling principles
2. **Performance**: Use appropriate indexes and partitioning
3. **Documentation**: Document business metrics and calculations
4. **Testing**: Comprehensive data quality tests

## Example Models

### Dimension Table
```sql
-- models/analytics/dim_customer.sql

{{ config(
    materialized='table',
    schema='analytics'
) }}

SELECT
    customer_id,
    customer_name,
    email,
    phone,
    address,
    city,
    country,
    customer_segment,
    created_date,
    updated_date,
    CURRENT_TIMESTAMP AS loaded_at
    
FROM {{ ref('int_customer_master') }}
```

### Fact Table
```sql
-- models/analytics/fct_sales.sql

{{ config(
    materialized='table',
    schema='analytics'
) }}

SELECT
    -- Surrogate keys
    s.sale_id,
    s.customer_id,
    s.product_id,
    s.date_id,
    
    -- Measures
    s.quantity,
    s.unit_price,
    s.total_amount,
    s.discount_amount,
    s.net_amount,
    
    -- Metadata
    s.transaction_type,
    s.payment_method,
    s.channel,
    
    -- Timestamps
    s.transaction_timestamp,
    CURRENT_TIMESTAMP AS loaded_at
    
FROM {{ ref('int_sales_transactions') }} s
```