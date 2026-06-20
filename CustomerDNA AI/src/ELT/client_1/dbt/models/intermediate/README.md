# Intermediate Models

Intermediate models apply business logic and create reusable transformations.

## Purpose

1. **Business Logic**: Apply calculations, aggregations, and transformations
2. **Reusability**: Create building blocks for multiple analytical models
3. **Complexity Management**: Break down complex transformations
4. **Performance**: Optimize queries before final models

## Naming Convention

- `int_<business_concept>.sql`
- Example: `int_customer_segments.sql`

## Best Practices

1. **Single Responsibility**: Each model should do one thing well
2. **Document Business Rules**: Comment on why transformations are applied
3. **Test Transformations**: Validate calculations and logic
4. **Optimize Performance**: Use appropriate indexes and partitioning

## Example Model

```sql
-- models/intermediate/int_customer_segments.sql

{{ config(
    materialized='table',
    schema='intermediate'
) }}

WITH customer_stats AS (
    SELECT
        customer_id,
        COUNT(*) AS total_purchases,
        SUM(amount) AS total_spent,
        AVG(amount) AS avg_purchase_value,
        MAX(purchase_date) AS last_purchase_date
    FROM {{ ref('stg_transactions') }}
    GROUP BY customer_id
),

customer_segments AS (
    SELECT
        cs.customer_id,
        cs.total_purchases,
        cs.total_spent,
        cs.avg_purchase_value,
        
        -- Business logic: Customer segmentation
        CASE
            WHEN cs.total_spent > 10000 THEN 'VIP'
            WHEN cs.total_spent > 5000 THEN 'Premium'
            WHEN cs.total_spent > 1000 THEN 'Regular'
            ELSE 'New'
        END AS customer_segment,
        
        -- Recency calculation
        DATEDIFF('day', cs.last_purchase_date, CURRENT_DATE) AS days_since_last_purchase
        
    FROM customer_stats cs
)

SELECT * FROM customer_segments
```