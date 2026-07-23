select
    customer_id,
    year_birth,
    education,
    marital_status,
    gender,
    income,
    city_tier,
    preferred_payment_mode,
    preferred_order_category,
    satisfaction_score,
    complaint_flag,
    is_churned,
    last_campaign_response_flag,
    retail_invoice_count,
    retail_distinct_product_count,
    retail_total_quantity,
    retail_gross_revenue,
    campaign_total_spend,
    total_campaign_purchase_count,
    case
        when retail_gross_revenue >= 10000 then 'high_value'
        when retail_gross_revenue >= 2500 then 'medium_value'
        else 'emerging_value'
    end as value_segment,
    case
        when coalesce(is_churned, false) then 'at_risk'
        when satisfaction_score >= 4 then 'healthy'
        else 'watchlist'
    end as retention_segment
from {{ ref('int_customer_commercial_360') }}
